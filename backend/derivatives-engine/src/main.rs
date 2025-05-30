/*
TigerEx Derivatives Trading Engine
Advanced derivatives platform supporting perpetual swaps, futures, structured products
All features from Binance, Bybit, OKX, KuCoin, Bitget
*/

use std::collections::HashMap;
use std::sync::{Arc, Mutex, RwLock};
use std::time::{SystemTime, UNIX_EPOCH, Duration};
use tokio::time::{interval, sleep};
use serde::{Deserialize, Serialize};
use rust_decimal::Decimal;
use uuid::Uuid;
use chrono::{DateTime, Utc};

// Derivative Types
#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum DerivativeType {
    PerpetualSwap,
    Futures,
    Options,
    StructuredProduct,
    Warrant,
    CFD,
    Swap,
    Forward,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum SettlementType {
    CashSettled,
    PhysicalDelivery,
    CryptoSettled,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum MarginType {
    Cross,
    Isolated,
    Portfolio,
    SPAN,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum OrderType {
    Market,
    Limit,
    Stop,
    StopLimit,
    TakeProfit,
    TakeProfitLimit,
    TrailingStop,
    Iceberg,
    TWAP,
    VWAP,
    PostOnly,
    ReduceOnly,
    ClosePosition,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub enum PositionSide {
    Long,
    Short,
    Both, // For hedge mode
}

// Funding Rate Structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FundingRate {
    pub symbol: String,
    pub funding_rate: Decimal,
    pub predicted_rate: Decimal,
    pub funding_time: DateTime<Utc>,
    pub next_funding_time: DateTime<Utc>,
    pub funding_interval: Duration,
    pub mark_price: Decimal,
    pub index_price: Decimal,
    pub premium_index: Decimal,
    pub interest_rate: Decimal,
}

// Index Price Structure
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IndexPrice {
    pub symbol: String,
    pub index_price: Decimal,
    pub mark_price: Decimal,
    pub last_funding_rate: Decimal,
    pub next_funding_time: DateTime<Utc>,
    pub constituents: Vec<IndexConstituent>,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IndexConstituent {
    pub exchange: String,
    pub symbol: String,
    pub price: Decimal,
    pub weight: Decimal,
    pub volume_24h: Decimal,
}

// Derivative Contract
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DerivativeContract {
    pub symbol: String,
    pub base_asset: String,
    pub quote_asset: String,
    pub derivative_type: DerivativeType,
    pub settlement_type: SettlementType,
    pub contract_size: Decimal,
    pub tick_size: Decimal,
    pub min_qty: Decimal,
    pub max_qty: Decimal,
    pub max_leverage: u32,
    pub maintenance_margin_rate: Decimal,
    pub initial_margin_rate: Decimal,
    pub maker_fee_rate: Decimal,
    pub taker_fee_rate: Decimal,
    pub funding_interval: Duration,
    pub delivery_date: Option<DateTime<Utc>>,
    pub listing_date: DateTime<Utc>,
    pub is_active: bool,
    pub is_trading_enabled: bool,
    pub risk_limit_base: Decimal,
    pub risk_limit_step: Decimal,
    pub max_risk_limit: Decimal,
}

// Derivative Order
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DerivativeOrder {
    pub order_id: String,
    pub user_id: String,
    pub symbol: String,
    pub side: String, // BUY, SELL
    pub order_type: OrderType,
    pub position_side: PositionSide,
    pub quantity: Decimal,
    pub price: Option<Decimal>,
    pub stop_price: Option<Decimal>,
    pub time_in_force: String, // GTC, IOC, FOK, GTX
    pub reduce_only: bool,
    pub close_on_trigger: bool,
    pub leverage: u32,
    pub margin_type: MarginType,
    pub status: String, // NEW, PARTIALLY_FILLED, FILLED, CANCELLED
    pub filled_quantity: Decimal,
    pub avg_fill_price: Decimal,
    pub commission: Decimal,
    pub commission_asset: String,
    pub created_time: DateTime<Utc>,
    pub updated_time: DateTime<Utc>,
    pub working_type: String, // MARK_PRICE, CONTRACT_PRICE
    pub price_protect: bool,
    pub trigger_price_type: String, // MARK_PRICE, LAST_PRICE, INDEX_PRICE
}

// Derivative Position
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DerivativePosition {
    pub user_id: String,
    pub symbol: String,
    pub position_side: PositionSide,
    pub size: Decimal, // Positive for long, negative for short
    pub entry_price: Decimal,
    pub mark_price: Decimal,
    pub liquidation_price: Decimal,
    pub bankruptcy_price: Decimal,
    pub unrealized_pnl: Decimal,
    pub realized_pnl: Decimal,
    pub margin: Decimal,
    pub initial_margin: Decimal,
    pub maintenance_margin: Decimal,
    pub margin_ratio: Decimal,
    pub leverage: u32,
    pub margin_type: MarginType,
    pub auto_add_margin: bool,
    pub risk_limit: Decimal,
    pub risk_id: u32,
    pub created_time: DateTime<Utc>,
    pub updated_time: DateTime<Utc>,
    pub cum_realized_pnl: Decimal,
    pub position_value: Decimal,
    pub funding_fee: Decimal,
    pub trading_fee: Decimal,
}

// Risk Limit
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RiskLimit {
    pub risk_id: u32,
    pub symbol: String,
    pub limit: Decimal,
    pub initial_margin_rate: Decimal,
    pub maintenance_margin_rate: Decimal,
    pub is_lowest_risk: bool,
    pub max_leverage: u32,
}

// Liquidation Event
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LiquidationEvent {
    pub liquidation_id: String,
    pub user_id: String,
    pub symbol: String,
    pub side: String,
    pub quantity: Decimal,
    pub price: Decimal,
    pub time: DateTime<Utc>,
    pub liquidation_type: String, // ADL, LIQUIDATION, BANKRUPTCY
}

// Auto-Deleveraging (ADL)
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ADLEvent {
    pub adl_id: String,
    pub symbol: String,
    pub affected_users: Vec<String>,
    pub quantity_deleveraged: Decimal,
    pub price: Decimal,
    pub time: DateTime<Utc>,
}

// Insurance Fund
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct InsuranceFund {
    pub asset: String,
    pub balance: Decimal,
    pub daily_change: Decimal,
    pub last_updated: DateTime<Utc>,
}

// Derivatives Trading Engine
pub struct DerivativesTradingEngine {
    contracts: Arc<RwLock<HashMap<String, DerivativeContract>>>,
    positions: Arc<RwLock<HashMap<String, Vec<DerivativePosition>>>>, // user_id -> positions
    orders: Arc<RwLock<HashMap<String, Vec<DerivativeOrder>>>>, // symbol -> orders
    funding_rates: Arc<RwLock<HashMap<String, FundingRate>>>,
    index_prices: Arc<RwLock<HashMap<String, IndexPrice>>>,
    risk_limits: Arc<RwLock<HashMap<String, Vec<RiskLimit>>>>, // symbol -> risk limits
    insurance_fund: Arc<RwLock<HashMap<String, InsuranceFund>>>,
    liquidation_queue: Arc<Mutex<Vec<LiquidationEvent>>>,
    adl_queue: Arc<Mutex<Vec<ADLEvent>>>,
    running: Arc<Mutex<bool>>,
}

impl DerivativesTradingEngine {
    pub fn new() -> Self {
        Self {
            contracts: Arc::new(RwLock::new(HashMap::new())),
            positions: Arc::new(RwLock::new(HashMap::new())),
            orders: Arc::new(RwLock::new(HashMap::new())),
            funding_rates: Arc::new(RwLock::new(HashMap::new())),
            index_prices: Arc::new(RwLock::new(HashMap::new())),
            risk_limits: Arc::new(RwLock::new(HashMap::new())),
            insurance_fund: Arc::new(RwLock::new(HashMap::new())),
            liquidation_queue: Arc::new(Mutex::new(Vec::new())),
            adl_queue: Arc::new(Mutex::new(Vec::new())),
            running: Arc::new(Mutex::new(true)),
        }
    }

    pub async fn start(&self) {
        println!("Starting TigerEx Derivatives Trading Engine...");
        
        // Initialize sample contracts
        self.initialize_contracts().await;
        
        // Start background tasks
        self.start_funding_rate_engine().await;
        self.start_index_price_engine().await;
        self.start_mark_price_engine().await;
        self.start_liquidation_engine().await;
        self.start_risk_engine().await;
        self.start_adl_engine().await;
        
        println!("Derivatives Trading Engine started successfully");
    }

    async fn initialize_contracts(&self) {
        let mut contracts = self.contracts.write().unwrap();
        
        // BTC Perpetual Swap
        let btc_perp = DerivativeContract {
            symbol: "BTCUSDT".to_string(),
            base_asset: "BTC".to_string(),
            quote_asset: "USDT".to_string(),
            derivative_type: DerivativeType::PerpetualSwap,
            settlement_type: SettlementType::CashSettled,
            contract_size: Decimal::new(1, 0),
            tick_size: Decimal::new(1, 1), // 0.1
            min_qty: Decimal::new(1, 3), // 0.001
            max_qty: Decimal::new(1000000, 0),
            max_leverage: 125,
            maintenance_margin_rate: Decimal::new(4, 3), // 0.4%
            initial_margin_rate: Decimal::new(8, 3), // 0.8%
            maker_fee_rate: Decimal::new(2, 4), // 0.02%
            taker_fee_rate: Decimal::new(5, 4), // 0.05%
            funding_interval: Duration::from_secs(8 * 3600), // 8 hours
            delivery_date: None,
            listing_date: Utc::now(),
            is_active: true,
            is_trading_enabled: true,
            risk_limit_base: Decimal::new(200, 0), // 200 BTC
            risk_limit_step: Decimal::new(100, 0), // 100 BTC
            max_risk_limit: Decimal::new(8000, 0), // 8000 BTC
        };
        
        contracts.insert("BTCUSDT".to_string(), btc_perp);
        
        // ETH Perpetual Swap
        let eth_perp = DerivativeContract {
            symbol: "ETHUSDT".to_string(),
            base_asset: "ETH".to_string(),
            quote_asset: "USDT".to_string(),
            derivative_type: DerivativeType::PerpetualSwap,
            settlement_type: SettlementType::CashSettled,
            contract_size: Decimal::new(1, 0),
            tick_size: Decimal::new(1, 2), // 0.01
            min_qty: Decimal::new(1, 3), // 0.001
            max_qty: Decimal::new(1000000, 0),
            max_leverage: 100,
            maintenance_margin_rate: Decimal::new(5, 3), // 0.5%
            initial_margin_rate: Decimal::new(10, 3), // 1.0%
            maker_fee_rate: Decimal::new(2, 4), // 0.02%
            taker_fee_rate: Decimal::new(5, 4), // 0.05%
            funding_interval: Duration::from_secs(8 * 3600), // 8 hours
            delivery_date: None,
            listing_date: Utc::now(),
            is_active: true,
            is_trading_enabled: true,
            risk_limit_base: Decimal::new(2000, 0), // 2000 ETH
            risk_limit_step: Decimal::new(1000, 0), // 1000 ETH
            max_risk_limit: Decimal::new(80000, 0), // 80000 ETH
        };
        
        contracts.insert("ETHUSDT".to_string(), eth_perp);
        
        // Initialize risk limits
        self.initialize_risk_limits().await;
        
        // Initialize insurance fund
        self.initialize_insurance_fund().await;
    }

    async fn initialize_risk_limits(&self) {
        let mut risk_limits = self.risk_limits.write().unwrap();
        
        // BTC Risk Limits
        let btc_limits = vec![
            RiskLimit {
                risk_id: 1,
                symbol: "BTCUSDT".to_string(),
                limit: Decimal::new(200, 0),
                initial_margin_rate: Decimal::new(8, 3), // 0.8%
                maintenance_margin_rate: Decimal::new(4, 3), // 0.4%
                is_lowest_risk: true,
                max_leverage: 125,
            },
            RiskLimit {
                risk_id: 2,
                symbol: "BTCUSDT".to_string(),
                limit: Decimal::new(300, 0),
                initial_margin_rate: Decimal::new(10, 3), // 1.0%
                maintenance_margin_rate: Decimal::new(5, 3), // 0.5%
                is_lowest_risk: false,
                max_leverage: 100,
            },
            // Add more risk limits...
        ];
        
        risk_limits.insert("BTCUSDT".to_string(), btc_limits);
    }

    async fn initialize_insurance_fund(&self) {
        let mut insurance_fund = self.insurance_fund.write().unwrap();
        
        insurance_fund.insert("BTC".to_string(), InsuranceFund {
            asset: "BTC".to_string(),
            balance: Decimal::new(1000, 0), // 1000 BTC
            daily_change: Decimal::new(0, 0),
            last_updated: Utc::now(),
        });
        
        insurance_fund.insert("ETH".to_string(), InsuranceFund {
            asset: "ETH".to_string(),
            balance: Decimal::new(10000, 0), // 10000 ETH
            daily_change: Decimal::new(0, 0),
            last_updated: Utc::now(),
        });
        
        insurance_fund.insert("USDT".to_string(), InsuranceFund {
            asset: "USDT".to_string(),
            balance: Decimal::new(50000000, 0), // 50M USDT
            daily_change: Decimal::new(0, 0),
            last_updated: Utc::now(),
        });
    }

    async fn start_funding_rate_engine(&self) {
        let funding_rates = Arc::clone(&self.funding_rates);
        let contracts = Arc::clone(&self.contracts);
        let running = Arc::clone(&self.running);
        
        tokio::spawn(async move {
            let mut interval = interval(Duration::from_secs(60)); // Update every minute
            
            while *running.lock().unwrap() {
                interval.tick().await;
                
                let contracts_read = contracts.read().unwrap();
                let mut funding_rates_write = funding_rates.write().unwrap();
                
                for (symbol, contract) in contracts_read.iter() {
                    if contract.derivative_type == DerivativeType::PerpetualSwap {
                        // Calculate funding rate
                        let funding_rate = Self::calculate_funding_rate(symbol).await;
                        funding_rates_write.insert(symbol.clone(), funding_rate);
                    }
                }
            }
        });
    }

    async fn calculate_funding_rate(symbol: &str) -> FundingRate {
        // Simplified funding rate calculation
        // In practice, this would use mark price, index price, and premium index
        
        let current_time = Utc::now();
        let next_funding = current_time + chrono::Duration::hours(8);
        
        FundingRate {
            symbol: symbol.to_string(),
            funding_rate: Decimal::new(1, 4), // 0.01%
            predicted_rate: Decimal::new(1, 4),
            funding_time: current_time,
            next_funding_time: next_funding,
            funding_interval: Duration::from_secs(8 * 3600),
            mark_price: Decimal::new(45000, 0), // Sample mark price
            index_price: Decimal::new(44995, 0), // Sample index price
            premium_index: Decimal::new(5, 0), // Sample premium
            interest_rate: Decimal::new(5, 4), // 0.05%
        }
    }

    async fn start_index_price_engine(&self) {
        let index_prices = Arc::clone(&self.index_prices);
        let running = Arc::clone(&self.running);
        
        tokio::spawn(async move {
            let mut interval = interval(Duration::from_secs(1)); // Update every second
            
            while *running.lock().unwrap() {
                interval.tick().await;
                
                // Calculate index prices for all symbols
                let btc_index = Self::calculate_index_price("BTC").await;
                let eth_index = Self::calculate_index_price("ETH").await;
                
                let mut index_prices_write = index_prices.write().unwrap();
                index_prices_write.insert("BTCUSDT".to_string(), btc_index);
                index_prices_write.insert("ETHUSDT".to_string(), eth_index);
            }
        });
    }

    async fn calculate_index_price(base_asset: &str) -> IndexPrice {
        // Simplified index price calculation
        // In practice, this would aggregate prices from multiple exchanges
        
        let constituents = vec![
            IndexConstituent {
                exchange: "Binance".to_string(),
                symbol: format!("{}USDT", base_asset),
                price: Decimal::new(45000, 0),
                weight: Decimal::new(30, 2), // 30%
                volume_24h: Decimal::new(1000000, 0),
            },
            IndexConstituent {
                exchange: "Coinbase".to_string(),
                symbol: format!("{}-USD", base_asset),
                price: Decimal::new(44995, 0),
                weight: Decimal::new(25, 2), // 25%
                volume_24h: Decimal::new(800000, 0),
            },
            IndexConstituent {
                exchange: "Kraken".to_string(),
                symbol: format!("{}USD", base_asset),
                price: Decimal::new(45005, 0),
                weight: Decimal::new(20, 2), // 20%
                volume_24h: Decimal::new(600000, 0),
            },
            IndexConstituent {
                exchange: "Bitstamp".to_string(),
                symbol: format!("{}usd", base_asset),
                price: Decimal::new(44990, 0),
                weight: Decimal::new(15, 2), // 15%
                volume_24h: Decimal::new(400000, 0),
            },
            IndexConstituent {
                exchange: "Gemini".to_string(),
                symbol: format!("{}usd", base_asset),
                price: Decimal::new(45010, 0),
                weight: Decimal::new(10, 2), // 10%
                volume_24h: Decimal::new(200000, 0),
            },
        ];
        
        // Calculate weighted average price
        let mut weighted_sum = Decimal::new(0, 0);
        let mut total_weight = Decimal::new(0, 0);
        
        for constituent in &constituents {
            weighted_sum += constituent.price * constituent.weight;
            total_weight += constituent.weight;
        }
        
        let index_price = weighted_sum / total_weight;
        
        IndexPrice {
            symbol: format!("{}USDT", base_asset),
            index_price,
            mark_price: index_price + Decimal::new(5, 0), // Add small premium
            last_funding_rate: Decimal::new(1, 4), // 0.01%
            next_funding_time: Utc::now() + chrono::Duration::hours(8),
            constituents,
            timestamp: Utc::now(),
        }
    }

    async fn start_mark_price_engine(&self) {
        let contracts = Arc::clone(&self.contracts);
        let index_prices = Arc::clone(&self.index_prices);
        let running = Arc::clone(&self.running);
        
        tokio::spawn(async move {
            let mut interval = interval(Duration::from_secs(1)); // Update every second
            
            while *running.lock().unwrap() {
                interval.tick().await;
                
                // Update mark prices based on index prices and funding rates
                // This is a simplified implementation
                println!("Updating mark prices...");
            }
        });
    }

    async fn start_liquidation_engine(&self) {
        let positions = Arc::clone(&self.positions);
        let liquidation_queue = Arc::clone(&self.liquidation_queue);
        let running = Arc::clone(&self.running);
        
        tokio::spawn(async move {
            let mut interval = interval(Duration::from_secs(1)); // Check every second
            
            while *running.lock().unwrap() {
                interval.tick().await;
                
                // Check for positions that need liquidation
                let positions_read = positions.read().unwrap();
                let mut liquidations = Vec::new();
                
                for (user_id, user_positions) in positions_read.iter() {
                    for position in user_positions {
                        if Self::should_liquidate(position) {
                            let liquidation = LiquidationEvent {
                                liquidation_id: Uuid::new_v4().to_string(),
                                user_id: user_id.clone(),
                                symbol: position.symbol.clone(),
                                side: if position.size > Decimal::new(0, 0) { "SELL" } else { "BUY" }.to_string(),
                                quantity: position.size.abs(),
                                price: position.mark_price,
                                time: Utc::now(),
                                liquidation_type: "LIQUIDATION".to_string(),
                            };
                            liquidations.push(liquidation);
                        }
                    }
                }
                
                // Add liquidations to queue
                if !liquidations.is_empty() {
                    let mut queue = liquidation_queue.lock().unwrap();
                    queue.extend(liquidations);
                }
            }
        });
    }

    fn should_liquidate(position: &DerivativePosition) -> bool {
        // Check if margin ratio is below maintenance margin
        position.margin_ratio <= position.maintenance_margin
    }

    async fn start_risk_engine(&self) {
        let positions = Arc::clone(&self.positions);
        let running = Arc::clone(&self.running);
        
        tokio::spawn(async move {
            let mut interval = interval(Duration::from_secs(5)); // Check every 5 seconds
            
            while *running.lock().unwrap() {
                interval.tick().await;
                
                // Calculate risk metrics for all positions
                let positions_read = positions.read().unwrap();
                
                for (user_id, user_positions) in positions_read.iter() {
                    let total_margin = user_positions.iter()
                        .map(|p| p.margin)
                        .fold(Decimal::new(0, 0), |acc, x| acc + x);
                    
                    let total_unrealized_pnl = user_positions.iter()
                        .map(|p| p.unrealized_pnl)
                        .fold(Decimal::new(0, 0), |acc, x| acc + x);
                    
                    // Check risk limits and margin requirements
                    // Implement risk management logic here
                }
            }
        });
    }

    async fn start_adl_engine(&self) {
        let adl_queue = Arc::clone(&self.adl_queue);
        let running = Arc::clone(&self.running);
        
        tokio::spawn(async move {
            let mut interval = interval(Duration::from_secs(10)); // Check every 10 seconds
            
            while *running.lock().unwrap() {
                interval.tick().await;
                
                // Process ADL queue
                let mut queue = adl_queue.lock().unwrap();
                if !queue.is_empty() {
                    println!("Processing {} ADL events", queue.len());
                    queue.clear(); // Process and clear
                }
            }
        });
    }

    // Public API methods
    pub async fn place_order(&self, order: DerivativeOrder) -> Result<String, String> {
        // Validate order
        if !self.validate_order(&order).await {
            return Err("Invalid order".to_string());
        }
        
        // Add to order book
        let mut orders = self.orders.write().unwrap();
        let symbol_orders = orders.entry(order.symbol.clone()).or_insert_with(Vec::new);
        symbol_orders.push(order.clone());
        
        // Try to match order
        self.match_order(&order).await;
        
        Ok(order.order_id)
    }

    async fn validate_order(&self, order: &DerivativeOrder) -> bool {
        // Check if contract exists
        let contracts = self.contracts.read().unwrap();
        if !contracts.contains_key(&order.symbol) {
            return false;
        }
        
        // Check quantity constraints
        let contract = &contracts[&order.symbol];
        if order.quantity < contract.min_qty || order.quantity > contract.max_qty {
            return false;
        }
        
        // Check leverage constraints
        if order.leverage > contract.max_leverage {
            return false;
        }
        
        true
    }

    async fn match_order(&self, order: &DerivativeOrder) {
        // Simplified order matching
        // In practice, this would be much more sophisticated
        println!("Matching order: {} {} {} @ {:?}", 
                order.side, order.quantity, order.symbol, order.price);
    }

    pub async fn get_position(&self, user_id: &str, symbol: &str) -> Option<DerivativePosition> {
        let positions = self.positions.read().unwrap();
        if let Some(user_positions) = positions.get(user_id) {
            return user_positions.iter()
                .find(|p| p.symbol == symbol)
                .cloned();
        }
        None
    }

    pub async fn get_funding_rate(&self, symbol: &str) -> Option<FundingRate> {
        let funding_rates = self.funding_rates.read().unwrap();
        funding_rates.get(symbol).cloned()
    }

    pub async fn get_index_price(&self, symbol: &str) -> Option<IndexPrice> {
        let index_prices = self.index_prices.read().unwrap();
        index_prices.get(symbol).cloned()
    }

    pub async fn get_insurance_fund(&self, asset: &str) -> Option<InsuranceFund> {
        let insurance_fund = self.insurance_fund.read().unwrap();
        insurance_fund.get(asset).cloned()
    }

    pub async fn stop(&self) {
        let mut running = self.running.lock().unwrap();
        *running = false;
        println!("Derivatives Trading Engine stopped");
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("TigerEx Derivatives Trading Engine");
    
    let engine = DerivativesTradingEngine::new();
    engine.start().await;
    
    // Demo: Create a sample order
    let sample_order = DerivativeOrder {
        order_id: Uuid::new_v4().to_string(),
        user_id: "user123".to_string(),
        symbol: "BTCUSDT".to_string(),
        side: "BUY".to_string(),
        order_type: OrderType::Limit,
        position_side: PositionSide::Long,
        quantity: Decimal::new(1, 1), // 0.1 BTC
        price: Some(Decimal::new(44000, 0)), // $44,000
        stop_price: None,
        time_in_force: "GTC".to_string(),
        reduce_only: false,
        close_on_trigger: false,
        leverage: 10,
        margin_type: MarginType::Cross,
        status: "NEW".to_string(),
        filled_quantity: Decimal::new(0, 0),
        avg_fill_price: Decimal::new(0, 0),
        commission: Decimal::new(0, 0),
        commission_asset: "USDT".to_string(),
        created_time: Utc::now(),
        updated_time: Utc::now(),
        working_type: "MARK_PRICE".to_string(),
        price_protect: false,
        trigger_price_type: "MARK_PRICE".to_string(),
    };
    
    match engine.place_order(sample_order).await {
        Ok(order_id) => println!("Order placed successfully: {}", order_id),
        Err(e) => println!("Failed to place order: {}", e),
    }
    
    // Demo: Get funding rate
    if let Some(funding_rate) = engine.get_funding_rate("BTCUSDT").await {
        println!("BTC Funding Rate: {}", funding_rate.funding_rate);
    }
    
    // Demo: Get index price
    if let Some(index_price) = engine.get_index_price("BTCUSDT").await {
        println!("BTC Index Price: {}", index_price.index_price);
    }
    
    // Demo: Get insurance fund
    if let Some(insurance) = engine.get_insurance_fund("BTC").await {
        println!("BTC Insurance Fund: {}", insurance.balance);
    }
    
    // Keep running for demo
    sleep(Duration::from_secs(10)).await;
    
    engine.stop().await;
    
    Ok(())
}