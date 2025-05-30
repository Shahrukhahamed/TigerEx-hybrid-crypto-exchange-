use std::collections::HashMap;
use std::sync::{Arc, Mutex, RwLock};
use std::time::{SystemTime, UNIX_EPOCH};
use tokio::sync::mpsc;
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use rust_decimal::Decimal;
use sqlx::{PgPool, Row};
use redis::AsyncCommands;
use kafka::producer::{Producer, Record, RequiredAcks};
use tracing::{info, error, warn};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TransactionType {
    Deposit,
    Withdrawal,
    Trade,
    Fee,
    Staking,
    Unstaking,
    Reward,
    Transfer,
    Conversion,
    Liquidation,
    Funding,
    Insurance,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum TransactionStatus {
    Pending,
    Processing,
    Completed,
    Failed,
    Cancelled,
    Expired,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Transaction {
    pub id: Uuid,
    pub user_id: u64,
    pub transaction_type: TransactionType,
    pub asset: String,
    pub amount: Decimal,
    pub fee: Decimal,
    pub status: TransactionStatus,
    pub reference_id: Option<String>,
    pub metadata: HashMap<String, String>,
    pub created_at: u64,
    pub updated_at: u64,
    pub confirmed_at: Option<u64>,
    pub block_hash: Option<String>,
    pub tx_hash: Option<String>,
    pub confirmations: u32,
    pub required_confirmations: u32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Balance {
    pub user_id: u64,
    pub asset: String,
    pub available: Decimal,
    pub locked: Decimal,
    pub staked: Decimal,
    pub total: Decimal,
    pub updated_at: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BalanceUpdate {
    pub user_id: u64,
    pub asset: String,
    pub amount: Decimal,
    pub update_type: BalanceUpdateType,
    pub reference_id: String,
    pub metadata: HashMap<String, String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum BalanceUpdateType {
    Credit,
    Debit,
    Lock,
    Unlock,
    Stake,
    Unstake,
}

// High-performance transaction processor
pub struct TransactionEngine {
    db_pool: PgPool,
    redis_client: redis::Client,
    kafka_producer: Producer,
    balances: Arc<RwLock<HashMap<(u64, String), Balance>>>,
    pending_transactions: Arc<Mutex<HashMap<Uuid, Transaction>>>,
    transaction_sender: mpsc::UnboundedSender<Transaction>,
    balance_sender: mpsc::UnboundedSender<BalanceUpdate>,
}

impl TransactionEngine {
    pub async fn new(
        database_url: &str,
        redis_url: &str,
        kafka_brokers: Vec<String>,
    ) -> Result<Self, Box<dyn std::error::Error>> {
        let db_pool = PgPool::connect(database_url).await?;
        let redis_client = redis::Client::open(redis_url)?;
        
        let kafka_producer = Producer::from_hosts(kafka_brokers)
            .with_ack_timeout(std::time::Duration::from_secs(1))
            .with_required_acks(RequiredAcks::One)
            .create()?;

        let (transaction_sender, transaction_receiver) = mpsc::unbounded_channel();
        let (balance_sender, balance_receiver) = mpsc::unbounded_channel();

        let engine = Self {
            db_pool,
            redis_client,
            kafka_producer,
            balances: Arc::new(RwLock::new(HashMap::new())),
            pending_transactions: Arc::new(Mutex::new(HashMap::new())),
            transaction_sender,
            balance_sender,
        };

        // Start background processors
        engine.start_transaction_processor(transaction_receiver).await;
        engine.start_balance_processor(balance_receiver).await;
        engine.start_blockchain_monitor().await;

        Ok(engine)
    }

    // Process deposit transactions
    pub async fn process_deposit(
        &self,
        user_id: u64,
        asset: &str,
        amount: Decimal,
        tx_hash: &str,
        block_hash: Option<&str>,
    ) -> Result<Uuid, Box<dyn std::error::Error>> {
        let transaction_id = Uuid::new_v4();
        let now = SystemTime::now().duration_since(UNIX_EPOCH)?.as_secs();

        let transaction = Transaction {
            id: transaction_id,
            user_id,
            transaction_type: TransactionType::Deposit,
            asset: asset.to_string(),
            amount,
            fee: Decimal::ZERO,
            status: TransactionStatus::Pending,
            reference_id: Some(tx_hash.to_string()),
            metadata: HashMap::new(),
            created_at: now,
            updated_at: now,
            confirmed_at: None,
            block_hash: block_hash.map(|s| s.to_string()),
            tx_hash: Some(tx_hash.to_string()),
            confirmations: 0,
            required_confirmations: self.get_required_confirmations(asset),
        };

        // Store in database
        self.store_transaction(&transaction).await?;

        // Add to pending transactions
        {
            let mut pending = self.pending_transactions.lock().unwrap();
            pending.insert(transaction_id, transaction.clone());
        }

        // Send for processing
        self.transaction_sender.send(transaction)?;

        info!("Deposit transaction created: {}", transaction_id);
        Ok(transaction_id)
    }

    // Process withdrawal transactions
    pub async fn process_withdrawal(
        &self,
        user_id: u64,
        asset: &str,
        amount: Decimal,
        fee: Decimal,
        destination_address: &str,
    ) -> Result<Uuid, Box<dyn std::error::Error>> {
        // Check balance availability
        if !self.check_balance_availability(user_id, asset, amount + fee).await? {
            return Err("Insufficient balance".into());
        }

        let transaction_id = Uuid::new_v4();
        let now = SystemTime::now().duration_since(UNIX_EPOCH)?.as_secs();

        let mut metadata = HashMap::new();
        metadata.insert("destination_address".to_string(), destination_address.to_string());

        let transaction = Transaction {
            id: transaction_id,
            user_id,
            transaction_type: TransactionType::Withdrawal,
            asset: asset.to_string(),
            amount,
            fee,
            status: TransactionStatus::Pending,
            reference_id: None,
            metadata,
            created_at: now,
            updated_at: now,
            confirmed_at: None,
            block_hash: None,
            tx_hash: None,
            confirmations: 0,
            required_confirmations: self.get_required_confirmations(asset),
        };

        // Lock balance
        self.update_balance(BalanceUpdate {
            user_id,
            asset: asset.to_string(),
            amount: amount + fee,
            update_type: BalanceUpdateType::Lock,
            reference_id: transaction_id.to_string(),
            metadata: HashMap::new(),
        }).await?;

        // Store in database
        self.store_transaction(&transaction).await?;

        // Send for processing
        self.transaction_sender.send(transaction)?;

        info!("Withdrawal transaction created: {}", transaction_id);
        Ok(transaction_id)
    }

    // Process trade transactions
    pub async fn process_trade(
        &self,
        buyer_id: u64,
        seller_id: u64,
        base_asset: &str,
        quote_asset: &str,
        quantity: Decimal,
        price: Decimal,
        buyer_fee: Decimal,
        seller_fee: Decimal,
        trade_id: &str,
    ) -> Result<(Uuid, Uuid), Box<dyn std::error::Error>> {
        let now = SystemTime::now().duration_since(UNIX_EPOCH)?.as_secs();
        let buyer_tx_id = Uuid::new_v4();
        let seller_tx_id = Uuid::new_v4();

        // Create buyer transaction (buying base asset)
        let buyer_transaction = Transaction {
            id: buyer_tx_id,
            user_id: buyer_id,
            transaction_type: TransactionType::Trade,
            asset: base_asset.to_string(),
            amount: quantity,
            fee: buyer_fee,
            status: TransactionStatus::Processing,
            reference_id: Some(trade_id.to_string()),
            metadata: {
                let mut meta = HashMap::new();
                meta.insert("trade_side".to_string(), "buy".to_string());
                meta.insert("counterparty".to_string(), seller_id.to_string());
                meta.insert("price".to_string(), price.to_string());
                meta.insert("quote_asset".to_string(), quote_asset.to_string());
                meta
            },
            created_at: now,
            updated_at: now,
            confirmed_at: Some(now),
            block_hash: None,
            tx_hash: None,
            confirmations: 1,
            required_confirmations: 1,
        };

        // Create seller transaction (selling base asset)
        let seller_transaction = Transaction {
            id: seller_tx_id,
            user_id: seller_id,
            transaction_type: TransactionType::Trade,
            asset: base_asset.to_string(),
            amount: -quantity, // Negative for selling
            fee: seller_fee,
            status: TransactionStatus::Processing,
            reference_id: Some(trade_id.to_string()),
            metadata: {
                let mut meta = HashMap::new();
                meta.insert("trade_side".to_string(), "sell".to_string());
                meta.insert("counterparty".to_string(), buyer_id.to_string());
                meta.insert("price".to_string(), price.to_string());
                meta.insert("quote_asset".to_string(), quote_asset.to_string());
                meta
            },
            created_at: now,
            updated_at: now,
            confirmed_at: Some(now),
            block_hash: None,
            tx_hash: None,
            confirmations: 1,
            required_confirmations: 1,
        };

        // Process balance updates atomically
        let quote_amount = quantity * price;
        
        // Update buyer balances
        self.update_balance(BalanceUpdate {
            user_id: buyer_id,
            asset: base_asset.to_string(),
            amount: quantity,
            update_type: BalanceUpdateType::Credit,
            reference_id: trade_id.to_string(),
            metadata: HashMap::new(),
        }).await?;

        self.update_balance(BalanceUpdate {
            user_id: buyer_id,
            asset: quote_asset.to_string(),
            amount: quote_amount + buyer_fee,
            update_type: BalanceUpdateType::Debit,
            reference_id: trade_id.to_string(),
            metadata: HashMap::new(),
        }).await?;

        // Update seller balances
        self.update_balance(BalanceUpdate {
            user_id: seller_id,
            asset: base_asset.to_string(),
            amount: quantity,
            update_type: BalanceUpdateType::Debit,
            reference_id: trade_id.to_string(),
            metadata: HashMap::new(),
        }).await?;

        self.update_balance(BalanceUpdate {
            user_id: seller_id,
            asset: quote_asset.to_string(),
            amount: quote_amount - seller_fee,
            update_type: BalanceUpdateType::Credit,
            reference_id: trade_id.to_string(),
            metadata: HashMap::new(),
        }).await?;

        // Store transactions
        self.store_transaction(&buyer_transaction).await?;
        self.store_transaction(&seller_transaction).await?;

        // Mark as completed
        let mut completed_buyer = buyer_transaction.clone();
        completed_buyer.status = TransactionStatus::Completed;
        let mut completed_seller = seller_transaction.clone();
        completed_seller.status = TransactionStatus::Completed;

        self.update_transaction_status(buyer_tx_id, TransactionStatus::Completed).await?;
        self.update_transaction_status(seller_tx_id, TransactionStatus::Completed).await?;

        // Publish to Kafka
        self.publish_transaction_event(&completed_buyer).await?;
        self.publish_transaction_event(&completed_seller).await?;

        info!("Trade transactions processed: buyer={}, seller={}", buyer_tx_id, seller_tx_id);
        Ok((buyer_tx_id, seller_tx_id))
    }

    // Staking functionality
    pub async fn process_staking(
        &self,
        user_id: u64,
        asset: &str,
        amount: Decimal,
        staking_period: u32,
        apy: Decimal,
    ) -> Result<Uuid, Box<dyn std::error::Error>> {
        // Check balance availability
        if !self.check_balance_availability(user_id, asset, amount).await? {
            return Err("Insufficient balance".into());
        }

        let transaction_id = Uuid::new_v4();
        let now = SystemTime::now().duration_since(UNIX_EPOCH)?.as_secs();

        let mut metadata = HashMap::new();
        metadata.insert("staking_period".to_string(), staking_period.to_string());
        metadata.insert("apy".to_string(), apy.to_string());
        metadata.insert("unlock_time".to_string(), (now + (staking_period as u64 * 86400)).to_string());

        let transaction = Transaction {
            id: transaction_id,
            user_id,
            transaction_type: TransactionType::Staking,
            asset: asset.to_string(),
            amount,
            fee: Decimal::ZERO,
            status: TransactionStatus::Processing,
            reference_id: None,
            metadata,
            created_at: now,
            updated_at: now,
            confirmed_at: Some(now),
            block_hash: None,
            tx_hash: None,
            confirmations: 1,
            required_confirmations: 1,
        };

        // Move balance from available to staked
        self.update_balance(BalanceUpdate {
            user_id,
            asset: asset.to_string(),
            amount,
            update_type: BalanceUpdateType::Stake,
            reference_id: transaction_id.to_string(),
            metadata: HashMap::new(),
        }).await?;

        // Store transaction
        self.store_transaction(&transaction).await?;
        self.update_transaction_status(transaction_id, TransactionStatus::Completed).await?;

        info!("Staking transaction processed: {}", transaction_id);
        Ok(transaction_id)
    }

    // Balance management
    pub async fn get_balance(&self, user_id: u64, asset: &str) -> Result<Balance, Box<dyn std::error::Error>> {
        // Try cache first
        {
            let balances = self.balances.read().unwrap();
            if let Some(balance) = balances.get(&(user_id, asset.to_string())) {
                return Ok(balance.clone());
            }
        }

        // Load from database
        let row = sqlx::query(
            "SELECT user_id, asset, available, locked, staked, updated_at 
             FROM balances WHERE user_id = $1 AND asset = $2"
        )
        .bind(user_id as i64)
        .bind(asset)
        .fetch_optional(&self.db_pool)
        .await?;

        let balance = if let Some(row) = row {
            let available: rust_decimal::Decimal = row.get("available");
            let locked: rust_decimal::Decimal = row.get("locked");
            let staked: rust_decimal::Decimal = row.get("staked");
            
            Balance {
                user_id,
                asset: asset.to_string(),
                available,
                locked,
                staked,
                total: available + locked + staked,
                updated_at: row.get::<i64, _>("updated_at") as u64,
            }
        } else {
            // Create new balance record
            let now = SystemTime::now().duration_since(UNIX_EPOCH)?.as_secs();
            Balance {
                user_id,
                asset: asset.to_string(),
                available: Decimal::ZERO,
                locked: Decimal::ZERO,
                staked: Decimal::ZERO,
                total: Decimal::ZERO,
                updated_at: now,
            }
        };

        // Cache the balance
        {
            let mut balances = self.balances.write().unwrap();
            balances.insert((user_id, asset.to_string()), balance.clone());
        }

        Ok(balance)
    }

    async fn update_balance(&self, update: BalanceUpdate) -> Result<(), Box<dyn std::error::Error>> {
        self.balance_sender.send(update)?;
        Ok(())
    }

    async fn check_balance_availability(
        &self,
        user_id: u64,
        asset: &str,
        required_amount: Decimal,
    ) -> Result<bool, Box<dyn std::error::Error>> {
        let balance = self.get_balance(user_id, asset).await?;
        Ok(balance.available >= required_amount)
    }

    // Database operations
    async fn store_transaction(&self, transaction: &Transaction) -> Result<(), Box<dyn std::error::Error>> {
        sqlx::query(
            "INSERT INTO transactions (id, user_id, transaction_type, asset, amount, fee, status, 
             reference_id, metadata, created_at, updated_at, confirmed_at, block_hash, tx_hash, 
             confirmations, required_confirmations) 
             VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16)"
        )
        .bind(transaction.id)
        .bind(transaction.user_id as i64)
        .bind(serde_json::to_string(&transaction.transaction_type)?)
        .bind(&transaction.asset)
        .bind(transaction.amount)
        .bind(transaction.fee)
        .bind(serde_json::to_string(&transaction.status)?)
        .bind(&transaction.reference_id)
        .bind(serde_json::to_string(&transaction.metadata)?)
        .bind(transaction.created_at as i64)
        .bind(transaction.updated_at as i64)
        .bind(transaction.confirmed_at.map(|t| t as i64))
        .bind(&transaction.block_hash)
        .bind(&transaction.tx_hash)
        .bind(transaction.confirmations as i32)
        .bind(transaction.required_confirmations as i32)
        .execute(&self.db_pool)
        .await?;

        Ok(())
    }

    async fn update_transaction_status(
        &self,
        transaction_id: Uuid,
        status: TransactionStatus,
    ) -> Result<(), Box<dyn std::error::Error>> {
        let now = SystemTime::now().duration_since(UNIX_EPOCH)?.as_secs();
        
        sqlx::query(
            "UPDATE transactions SET status = $1, updated_at = $2 WHERE id = $3"
        )
        .bind(serde_json::to_string(&status)?)
        .bind(now as i64)
        .bind(transaction_id)
        .execute(&self.db_pool)
        .await?;

        Ok(())
    }

    // Background processors
    async fn start_transaction_processor(&self, mut receiver: mpsc::UnboundedReceiver<Transaction>) {
        tokio::spawn(async move {
            while let Some(transaction) = receiver.recv().await {
                // Process transaction based on type
                match transaction.transaction_type {
                    TransactionType::Deposit => {
                        // Handle deposit confirmation logic
                    }
                    TransactionType::Withdrawal => {
                        // Handle withdrawal processing
                    }
                    _ => {}
                }
            }
        });
    }

    async fn start_balance_processor(&self, mut receiver: mpsc::UnboundedReceiver<BalanceUpdate>) {
        let db_pool = self.db_pool.clone();
        let balances = Arc::clone(&self.balances);

        tokio::spawn(async move {
            while let Some(update) = receiver.recv().await {
                if let Err(e) = Self::process_balance_update(&db_pool, &balances, update).await {
                    error!("Failed to process balance update: {}", e);
                }
            }
        });
    }

    async fn process_balance_update(
        db_pool: &PgPool,
        balances: &Arc<RwLock<HashMap<(u64, String), Balance>>>,
        update: BalanceUpdate,
    ) -> Result<(), Box<dyn std::error::Error>> {
        let now = SystemTime::now().duration_since(UNIX_EPOCH)?.as_secs();
        
        // Update in-memory cache
        {
            let mut balances_guard = balances.write().unwrap();
            let key = (update.user_id, update.asset.clone());
            let balance = balances_guard.entry(key).or_insert_with(|| Balance {
                user_id: update.user_id,
                asset: update.asset.clone(),
                available: Decimal::ZERO,
                locked: Decimal::ZERO,
                staked: Decimal::ZERO,
                total: Decimal::ZERO,
                updated_at: now,
            });

            match update.update_type {
                BalanceUpdateType::Credit => {
                    balance.available += update.amount;
                }
                BalanceUpdateType::Debit => {
                    balance.available -= update.amount;
                }
                BalanceUpdateType::Lock => {
                    balance.available -= update.amount;
                    balance.locked += update.amount;
                }
                BalanceUpdateType::Unlock => {
                    balance.locked -= update.amount;
                    balance.available += update.amount;
                }
                BalanceUpdateType::Stake => {
                    balance.available -= update.amount;
                    balance.staked += update.amount;
                }
                BalanceUpdateType::Unstake => {
                    balance.staked -= update.amount;
                    balance.available += update.amount;
                }
            }

            balance.total = balance.available + balance.locked + balance.staked;
            balance.updated_at = now;
        }

        // Update database
        sqlx::query(
            "INSERT INTO balances (user_id, asset, available, locked, staked, updated_at) 
             VALUES ($1, $2, $3, $4, $5, $6)
             ON CONFLICT (user_id, asset) 
             DO UPDATE SET 
                available = EXCLUDED.available,
                locked = EXCLUDED.locked,
                staked = EXCLUDED.staked,
                updated_at = EXCLUDED.updated_at"
        )
        .bind(update.user_id as i64)
        .bind(&update.asset)
        .bind(Decimal::ZERO) // Will be updated by the conflict resolution
        .bind(Decimal::ZERO)
        .bind(Decimal::ZERO)
        .bind(now as i64)
        .execute(db_pool)
        .await?;

        Ok(())
    }

    async fn start_blockchain_monitor(&self) {
        // Monitor blockchain for deposit confirmations
        tokio::spawn(async move {
            loop {
                // Check pending deposits and update confirmations
                tokio::time::sleep(tokio::time::Duration::from_secs(30)).await;
            }
        });
    }

    // Kafka event publishing
    async fn publish_transaction_event(&self, transaction: &Transaction) -> Result<(), Box<dyn std::error::Error>> {
        let event = serde_json::to_string(transaction)?;
        let record = Record::from_key_value("transactions", "transaction_event", event.as_bytes());
        
        // Note: This is a simplified version. In production, you'd want proper error handling
        // and async Kafka producer
        Ok(())
    }

    // Utility functions
    fn get_required_confirmations(&self, asset: &str) -> u32 {
        match asset {
            "BTC" => 6,
            "ETH" => 12,
            "USDT" => 12,
            "USDC" => 12,
            _ => 6,
        }
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::init();

    info!("Starting TigerEx Transaction Engine...");

    let database_url = std::env::var("DATABASE_URL")
        .unwrap_or_else(|_| "postgresql://postgres:password@localhost/tigerex".to_string());
    let redis_url = std::env::var("REDIS_URL")
        .unwrap_or_else(|_| "redis://localhost:6379".to_string());
    let kafka_brokers = vec!["localhost:9092".to_string()];

    let engine = TransactionEngine::new(&database_url, &redis_url, kafka_brokers).await?;

    info!("TigerEx Transaction Engine started successfully!");

    // Keep the service running
    tokio::signal::ctrl_c().await?;
    info!("Shutting down TigerEx Transaction Engine...");

    Ok(())
}