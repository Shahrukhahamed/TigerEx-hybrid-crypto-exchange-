/*
TigerEx Liquidity Aggregator Service
High-performance Rust service for aggregating liquidity from multiple CEXs and DEXs
Supports Binance, Bybit, OKX, and major DEX protocols
*/

use std::collections::HashMap;
use std::sync::Arc;
use std::time::{Duration, SystemTime, UNIX_EPOCH};
use tokio::sync::{RwLock, Mutex};
use tokio::time::{interval, sleep};
use serde::{Deserialize, Serialize};
use serde_json::{json, Value};
use reqwest::Client;
use tokio_tungstenite::{connect_async, tungstenite::Message};
use futures_util::{SinkExt, StreamExt};
use redis::AsyncCommands;
use sqlx::{PgPool, Row};
use uuid::Uuid;
use rust_decimal::Decimal;
use chrono::{DateTime, Utc};
use anyhow::{Result, anyhow};
use tracing::{info, error, warn, debug};
use axum::{
    extract::{Path, Query, State},
    http::StatusCode,
    response::Json,
    routing::{get, post},
    Router,
};
use tower::ServiceBuilder;
use tower_http::cors::CorsLayer;
use tower_http::trace::TraceLayer;

// Configuration
#[derive(Debug, Clone)]
pub struct Config {
    pub database_url: String,
    pub redis_url: String,
    pub binance_api_key: Option<String>,
    pub binance_secret: Option<String>,
    pub bybit_api_key: Option<String>,
    pub bybit_secret: Option<String>,
    pub okx_api_key: Option<String>,
    pub okx_secret: Option<String>,
    pub okx_passphrase: Option<String>,
    pub ethereum_rpc: String,
    pub bsc_rpc: String,
    pub polygon_rpc: String,
    pub arbitrum_rpc: String,
    pub optimism_rpc: String,
    pub avalanche_rpc: String,
}

impl Config {
    pub fn from_env() -> Self {
        Self {
            database_url: std::env::var("DATABASE_URL")
                .unwrap_or_else(|_| "postgresql://postgres:password@localhost:5432/tigerex".to_string()),
            redis_url: std::env::var("REDIS_URL")
                .unwrap_or_else(|_| "redis://localhost:6379".to_string()),
            binance_api_key: std::env::var("BINANCE_API_KEY").ok(),
            binance_secret: std::env::var("BINANCE_SECRET").ok(),
            bybit_api_key: std::env::var("BYBIT_API_KEY").ok(),
            bybit_secret: std::env::var("BYBIT_SECRET").ok(),
            okx_api_key: std::env::var("OKX_API_KEY").ok(),
            okx_secret: std::env::var("OKX_SECRET").ok(),
            okx_passphrase: std::env::var("OKX_PASSPHRASE").ok(),
            ethereum_rpc: std::env::var("ETHEREUM_RPC")
                .unwrap_or_else(|_| "https://mainnet.infura.io/v3/YOUR_KEY".to_string()),
            bsc_rpc: std::env::var("BSC_RPC")
                .unwrap_or_else(|_| "https://bsc-dataseed.binance.org/".to_string()),
            polygon_rpc: std::env::var("POLYGON_RPC")
                .unwrap_or_else(|_| "https://polygon-rpc.com/".to_string()),
            arbitrum_rpc: std::env::var("ARBITRUM_RPC")
                .unwrap_or_else(|_| "https://arb1.arbitrum.io/rpc".to_string()),
            optimism_rpc: std::env::var("OPTIMISM_RPC")
                .unwrap_or_else(|_| "https://mainnet.optimism.io".to_string()),
            avalanche_rpc: std::env::var("AVALANCHE_RPC")
                .unwrap_or_else(|_| "https://api.avax.network/ext/bc/C/rpc".to_string()),
        }
    }
}

// Data structures
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrderBookLevel {
    pub price: Decimal,
    pub quantity: Decimal,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrderBook {
    pub symbol: String,
    pub bids: Vec<OrderBookLevel>,
    pub asks: Vec<OrderBookLevel>,
    pub timestamp: DateTime<Utc>,
    pub source: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AggregatedOrderBook {
    pub symbol: String,
    pub bids: Vec<OrderBookLevel>,
    pub asks: Vec<OrderBookLevel>,
    pub best_bid: Option<Decimal>,
    pub best_ask: Option<Decimal>,
    pub spread: Option<Decimal>,
    pub total_bid_volume: Decimal,
    pub total_ask_volume: Decimal,
    pub sources: Vec<String>,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LiquidityMetrics {
    pub symbol: String,
    pub total_liquidity_usd: Decimal,
    pub bid_liquidity_usd: Decimal,
    pub ask_liquidity_usd: Decimal,
    pub spread_bps: Decimal,
    pub depth_1_percent: Decimal,
    pub depth_5_percent: Decimal,
    pub volume_24h: Decimal,
    pub price_impact_1k: Decimal,
    pub price_impact_10k: Decimal,
    pub price_impact_100k: Decimal,
    pub sources: HashMap<String, LiquiditySourceMetrics>,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LiquiditySourceMetrics {
    pub source: String,
    pub liquidity_usd: Decimal,
    pub volume_24h: Decimal,
    pub spread_bps: Decimal,
    pub uptime_percentage: Decimal,
    pub latency_ms: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct DEXPool {
    pub id: String,
    pub dex_protocol: String,
    pub blockchain: String,
    pub token_a: String,
    pub token_b: String,
    pub pool_address: String,
    pub liquidity_usd: Decimal,
    pub volume_24h: Decimal,
    pub fee_tier: Decimal,
    pub apy: Decimal,
    pub price: Decimal,
    pub reserves: (Decimal, Decimal),
    pub is_active: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ArbitrageOpportunity {
    pub id: String,
    pub symbol: String,
    pub buy_exchange: String,
    pub sell_exchange: String,
    pub buy_price: Decimal,
    pub sell_price: Decimal,
    pub profit_percentage: Decimal,
    pub profit_usd: Decimal,
    pub max_quantity: Decimal,
    pub estimated_gas_cost: Option<Decimal>,
    pub net_profit: Decimal,
    pub confidence_score: Decimal,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LiquidityRoute {
    pub symbol: String,
    pub side: String, // BUY or SELL
    pub quantity: Decimal,
    pub routes: Vec<RouteStep>,
    pub total_price: Decimal,
    pub average_price: Decimal,
    pub price_impact: Decimal,
    pub estimated_slippage: Decimal,
    pub gas_cost: Option<Decimal>,
    pub execution_time_ms: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RouteStep {
    pub exchange: String,
    pub quantity: Decimal,
    pub price: Decimal,
    pub fee: Decimal,
    pub is_dex: bool,
    pub pool_address: Option<String>,
}

// Exchange connectors
#[derive(Debug, Clone)]
pub enum ExchangeType {
    Binance,
    Bybit,
    OKX,
    Uniswap,
    PancakeSwap,
    SushiSwap,
    Curve,
    Balancer,
}

pub trait ExchangeConnector: Send + Sync {
    async fn get_order_book(&self, symbol: &str) -> Result<OrderBook>;
    async fn get_24h_volume(&self, symbol: &str) -> Result<Decimal>;
    async fn get_ticker(&self, symbol: &str) -> Result<Value>;
    async fn subscribe_order_book(&self, symbol: &str) -> Result<()>;
}

// Binance connector
pub struct BinanceConnector {
    client: Client,
    api_key: Option<String>,
    secret: Option<String>,
}

impl BinanceConnector {
    pub fn new(api_key: Option<String>, secret: Option<String>) -> Self {
        Self {
            client: Client::new(),
            api_key,
            secret,
        }
    }
}

#[async_trait::async_trait]
impl ExchangeConnector for BinanceConnector {
    async fn get_order_book(&self, symbol: &str) -> Result<OrderBook> {
        let url = format!("https://api.binance.com/api/v3/depth?symbol={}&limit=100", symbol);
        let response = self.client.get(&url).send().await?;
        let data: Value = response.json().await?;
        
        let mut bids = Vec::new();
        let mut asks = Vec::new();
        
        if let Some(bid_array) = data["bids"].as_array() {
            for bid in bid_array {
                if let (Some(price), Some(qty)) = (bid[0].as_str(), bid[1].as_str()) {
                    bids.push(OrderBookLevel {
                        price: price.parse()?,
                        quantity: qty.parse()?,
                        timestamp: Utc::now(),
                    });
                }
            }
        }
        
        if let Some(ask_array) = data["asks"].as_array() {
            for ask in ask_array {
                if let (Some(price), Some(qty)) = (ask[0].as_str(), ask[1].as_str()) {
                    asks.push(OrderBookLevel {
                        price: price.parse()?,
                        quantity: qty.parse()?,
                        timestamp: Utc::now(),
                    });
                }
            }
        }
        
        Ok(OrderBook {
            symbol: symbol.to_string(),
            bids,
            asks,
            timestamp: Utc::now(),
            source: "binance".to_string(),
        })
    }
    
    async fn get_24h_volume(&self, symbol: &str) -> Result<Decimal> {
        let url = format!("https://api.binance.com/api/v3/ticker/24hr?symbol={}", symbol);
        let response = self.client.get(&url).send().await?;
        let data: Value = response.json().await?;
        
        if let Some(volume) = data["quoteVolume"].as_str() {
            Ok(volume.parse()?)
        } else {
            Err(anyhow!("Failed to get volume from Binance"))
        }
    }
    
    async fn get_ticker(&self, symbol: &str) -> Result<Value> {
        let url = format!("https://api.binance.com/api/v3/ticker/24hr?symbol={}", symbol);
        let response = self.client.get(&url).send().await?;
        Ok(response.json().await?)
    }
    
    async fn subscribe_order_book(&self, symbol: &str) -> Result<()> {
        let ws_url = format!("wss://stream.binance.com:9443/ws/{}@depth", symbol.to_lowercase());
        let (ws_stream, _) = connect_async(&ws_url).await?;
        let (mut write, mut read) = ws_stream.split();
        
        // Subscribe to depth stream
        let subscribe_msg = json!({
            "method": "SUBSCRIBE",
            "params": [format!("{}@depth", symbol.to_lowercase())],
            "id": 1
        });
        
        write.send(Message::Text(subscribe_msg.to_string())).await?;
        
        // Handle incoming messages in background
        tokio::spawn(async move {
            while let Some(msg) = read.next().await {
                match msg {
                    Ok(Message::Text(text)) => {
                        if let Ok(data) = serde_json::from_str::<Value>(&text) {
                            // Process order book update
                            debug!("Received order book update: {:?}", data);
                        }
                    }
                    Ok(Message::Close(_)) => break,
                    Err(e) => {
                        error!("WebSocket error: {}", e);
                        break;
                    }
                    _ => {}
                }
            }
        });
        
        Ok(())
    }
}

// Bybit connector
pub struct BybitConnector {
    client: Client,
    api_key: Option<String>,
    secret: Option<String>,
}

impl BybitConnector {
    pub fn new(api_key: Option<String>, secret: Option<String>) -> Self {
        Self {
            client: Client::new(),
            api_key,
            secret,
        }
    }
}

#[async_trait::async_trait]
impl ExchangeConnector for BybitConnector {
    async fn get_order_book(&self, symbol: &str) -> Result<OrderBook> {
        let url = format!("https://api.bybit.com/v5/market/orderbook?category=spot&symbol={}&limit=50", symbol);
        let response = self.client.get(&url).send().await?;
        let data: Value = response.json().await?;
        
        let mut bids = Vec::new();
        let mut asks = Vec::new();
        
        if let Some(result) = data["result"].as_object() {
            if let Some(bid_array) = result["b"].as_array() {
                for bid in bid_array {
                    if let (Some(price), Some(qty)) = (bid[0].as_str(), bid[1].as_str()) {
                        bids.push(OrderBookLevel {
                            price: price.parse()?,
                            quantity: qty.parse()?,
                            timestamp: Utc::now(),
                        });
                    }
                }
            }
            
            if let Some(ask_array) = result["a"].as_array() {
                for ask in ask_array {
                    if let (Some(price), Some(qty)) = (ask[0].as_str(), ask[1].as_str()) {
                        asks.push(OrderBookLevel {
                            price: price.parse()?,
                            quantity: qty.parse()?,
                            timestamp: Utc::now(),
                        });
                    }
                }
            }
        }
        
        Ok(OrderBook {
            symbol: symbol.to_string(),
            bids,
            asks,
            timestamp: Utc::now(),
            source: "bybit".to_string(),
        })
    }
    
    async fn get_24h_volume(&self, symbol: &str) -> Result<Decimal> {
        let url = format!("https://api.bybit.com/v5/market/tickers?category=spot&symbol={}", symbol);
        let response = self.client.get(&url).send().await?;
        let data: Value = response.json().await?;
        
        if let Some(result) = data["result"]["list"].as_array() {
            if let Some(ticker) = result.first() {
                if let Some(volume) = ticker["turnover24h"].as_str() {
                    return Ok(volume.parse()?);
                }
            }
        }
        
        Err(anyhow!("Failed to get volume from Bybit"))
    }
    
    async fn get_ticker(&self, symbol: &str) -> Result<Value> {
        let url = format!("https://api.bybit.com/v5/market/tickers?category=spot&symbol={}", symbol);
        let response = self.client.get(&url).send().await?;
        Ok(response.json().await?)
    }
    
    async fn subscribe_order_book(&self, symbol: &str) -> Result<()> {
        let ws_url = "wss://stream.bybit.com/v5/public/spot";
        let (ws_stream, _) = connect_async(ws_url).await?;
        let (mut write, mut read) = ws_stream.split();
        
        // Subscribe to order book
        let subscribe_msg = json!({
            "op": "subscribe",
            "args": [format!("orderbook.50.{}", symbol)]
        });
        
        write.send(Message::Text(subscribe_msg.to_string())).await?;
        
        tokio::spawn(async move {
            while let Some(msg) = read.next().await {
                match msg {
                    Ok(Message::Text(text)) => {
                        if let Ok(data) = serde_json::from_str::<Value>(&text) {
                            debug!("Received Bybit order book update: {:?}", data);
                        }
                    }
                    Ok(Message::Close(_)) => break,
                    Err(e) => {
                        error!("Bybit WebSocket error: {}", e);
                        break;
                    }
                    _ => {}
                }
            }
        });
        
        Ok(())
    }
}

// OKX connector
pub struct OKXConnector {
    client: Client,
    api_key: Option<String>,
    secret: Option<String>,
    passphrase: Option<String>,
}

impl OKXConnector {
    pub fn new(api_key: Option<String>, secret: Option<String>, passphrase: Option<String>) -> Self {
        Self {
            client: Client::new(),
            api_key,
            secret,
            passphrase,
        }
    }
}

#[async_trait::async_trait]
impl ExchangeConnector for OKXConnector {
    async fn get_order_book(&self, symbol: &str) -> Result<OrderBook> {
        let url = format!("https://www.okx.com/api/v5/market/books?instId={}&sz=100", symbol);
        let response = self.client.get(&url).send().await?;
        let data: Value = response.json().await?;
        
        let mut bids = Vec::new();
        let mut asks = Vec::new();
        
        if let Some(data_array) = data["data"].as_array() {
            if let Some(book) = data_array.first() {
                if let Some(bid_array) = book["bids"].as_array() {
                    for bid in bid_array {
                        if let (Some(price), Some(qty)) = (bid[0].as_str(), bid[1].as_str()) {
                            bids.push(OrderBookLevel {
                                price: price.parse()?,
                                quantity: qty.parse()?,
                                timestamp: Utc::now(),
                            });
                        }
                    }
                }
                
                if let Some(ask_array) = book["asks"].as_array() {
                    for ask in ask_array {
                        if let (Some(price), Some(qty)) = (ask[0].as_str(), ask[1].as_str()) {
                            asks.push(OrderBookLevel {
                                price: price.parse()?,
                                quantity: qty.parse()?,
                                timestamp: Utc::now(),
                            });
                        }
                    }
                }
            }
        }
        
        Ok(OrderBook {
            symbol: symbol.to_string(),
            bids,
            asks,
            timestamp: Utc::now(),
            source: "okx".to_string(),
        })
    }
    
    async fn get_24h_volume(&self, symbol: &str) -> Result<Decimal> {
        let url = format!("https://www.okx.com/api/v5/market/ticker?instId={}", symbol);
        let response = self.client.get(&url).send().await?;
        let data: Value = response.json().await?;
        
        if let Some(data_array) = data["data"].as_array() {
            if let Some(ticker) = data_array.first() {
                if let Some(volume) = ticker["volCcy24h"].as_str() {
                    return Ok(volume.parse()?);
                }
            }
        }
        
        Err(anyhow!("Failed to get volume from OKX"))
    }
    
    async fn get_ticker(&self, symbol: &str) -> Result<Value> {
        let url = format!("https://www.okx.com/api/v5/market/ticker?instId={}", symbol);
        let response = self.client.get(&url).send().await?;
        Ok(response.json().await?)
    }
    
    async fn subscribe_order_book(&self, symbol: &str) -> Result<()> {
        let ws_url = "wss://ws.okx.com:8443/ws/v5/public";
        let (ws_stream, _) = connect_async(ws_url).await?;
        let (mut write, mut read) = ws_stream.split();
        
        // Subscribe to order book
        let subscribe_msg = json!({
            "op": "subscribe",
            "args": [{
                "channel": "books",
                "instId": symbol
            }]
        });
        
        write.send(Message::Text(subscribe_msg.to_string())).await?;
        
        tokio::spawn(async move {
            while let Some(msg) = read.next().await {
                match msg {
                    Ok(Message::Text(text)) => {
                        if let Ok(data) = serde_json::from_str::<Value>(&text) {
                            debug!("Received OKX order book update: {:?}", data);
                        }
                    }
                    Ok(Message::Close(_)) => break,
                    Err(e) => {
                        error!("OKX WebSocket error: {}", e);
                        break;
                    }
                    _ => {}
                }
            }
        });
        
        Ok(())
    }
}

// DEX connector for Uniswap, PancakeSwap, etc.
pub struct DEXConnector {
    client: Client,
    rpc_urls: HashMap<String, String>,
}

impl DEXConnector {
    pub fn new(config: &Config) -> Self {
        let mut rpc_urls = HashMap::new();
        rpc_urls.insert("ethereum".to_string(), config.ethereum_rpc.clone());
        rpc_urls.insert("bsc".to_string(), config.bsc_rpc.clone());
        rpc_urls.insert("polygon".to_string(), config.polygon_rpc.clone());
        rpc_urls.insert("arbitrum".to_string(), config.arbitrum_rpc.clone());
        rpc_urls.insert("optimism".to_string(), config.optimism_rpc.clone());
        rpc_urls.insert("avalanche".to_string(), config.avalanche_rpc.clone());
        
        Self {
            client: Client::new(),
            rpc_urls,
        }
    }
    
    pub async fn get_dex_pools(&self, token_a: &str, token_b: &str, blockchain: &str) -> Result<Vec<DEXPool>> {
        // Implementation for fetching DEX pools from various protocols
        // This would involve calling smart contracts and subgraphs
        let mut pools = Vec::new();
        
        // Placeholder implementation
        pools.push(DEXPool {
            id: Uuid::new_v4().to_string(),
            dex_protocol: "uniswap_v3".to_string(),
            blockchain: blockchain.to_string(),
            token_a: token_a.to_string(),
            token_b: token_b.to_string(),
            pool_address: "0x1234567890123456789012345678901234567890".to_string(),
            liquidity_usd: Decimal::new(1000000, 0),
            volume_24h: Decimal::new(500000, 0),
            fee_tier: Decimal::new(3, 3), // 0.3%
            apy: Decimal::new(15, 2), // 15%
            price: Decimal::new(50000, 0),
            reserves: (Decimal::new(100, 0), Decimal::new(5000000, 0)),
            is_active: true,
        });
        
        Ok(pools)
    }
    
    pub async fn get_dex_price(&self, token_a: &str, token_b: &str, amount: Decimal, blockchain: &str) -> Result<Decimal> {
        // Implementation for getting DEX price quotes
        // This would involve calling router contracts
        Ok(Decimal::new(50000, 0)) // Placeholder
    }
}

// Main liquidity aggregator
pub struct LiquidityAggregator {
    exchanges: HashMap<String, Arc<dyn ExchangeConnector>>,
    dex_connector: DEXConnector,
    order_books: Arc<RwLock<HashMap<String, Vec<OrderBook>>>>,
    liquidity_metrics: Arc<RwLock<HashMap<String, LiquidityMetrics>>>,
    arbitrage_opportunities: Arc<RwLock<Vec<ArbitrageOpportunity>>>,
    db_pool: PgPool,
    redis_client: Arc<Mutex<redis::aio::Connection>>,
}

impl LiquidityAggregator {
    pub async fn new(config: &Config) -> Result<Self> {
        let mut exchanges: HashMap<String, Arc<dyn ExchangeConnector>> = HashMap::new();
        
        // Initialize exchange connectors
        exchanges.insert(
            "binance".to_string(),
            Arc::new(BinanceConnector::new(config.binance_api_key.clone(), config.binance_secret.clone()))
        );
        exchanges.insert(
            "bybit".to_string(),
            Arc::new(BybitConnector::new(config.bybit_api_key.clone(), config.bybit_secret.clone()))
        );
        exchanges.insert(
            "okx".to_string(),
            Arc::new(OKXConnector::new(
                config.okx_api_key.clone(),
                config.okx_secret.clone(),
                config.okx_passphrase.clone()
            ))
        );
        
        // Initialize database connection
        let db_pool = PgPool::connect(&config.database_url).await?;
        
        // Initialize Redis connection
        let redis_client = redis::Client::open(config.redis_url.as_str())?;
        let redis_conn = redis_client.get_async_connection().await?;
        
        Ok(Self {
            exchanges,
            dex_connector: DEXConnector::new(config),
            order_books: Arc::new(RwLock::new(HashMap::new())),
            liquidity_metrics: Arc::new(RwLock::new(HashMap::new())),
            arbitrage_opportunities: Arc::new(RwLock::new(Vec::new())),
            db_pool,
            redis_client: Arc::new(Mutex::new(redis_conn)),
        })
    }
    
    pub async fn start_aggregation(&self, symbols: Vec<String>) -> Result<()> {
        info!("Starting liquidity aggregation for {} symbols", symbols.len());
        
        for symbol in symbols {
            let symbol_clone = symbol.clone();
            let exchanges = self.exchanges.clone();
            let order_books = self.order_books.clone();
            let liquidity_metrics = self.liquidity_metrics.clone();
            
            // Start order book aggregation for each symbol
            tokio::spawn(async move {
                let mut interval = interval(Duration::from_millis(100)); // 100ms updates
                
                loop {
                    interval.tick().await;
                    
                    let mut symbol_order_books = Vec::new();
                    
                    // Fetch order books from all exchanges
                    for (exchange_name, exchange) in &exchanges {
                        match exchange.get_order_book(&symbol_clone).await {
                            Ok(order_book) => {
                                symbol_order_books.push(order_book);
                            }
                            Err(e) => {
                                warn!("Failed to get order book from {}: {}", exchange_name, e);
                            }
                        }
                    }
                    
                    // Update aggregated order books
                    {
                        let mut books = order_books.write().await;
                        books.insert(symbol_clone.clone(), symbol_order_books.clone());
                    }
                    
                    // Calculate liquidity metrics
                    if !symbol_order_books.is_empty() {
                        let metrics = Self::calculate_liquidity_metrics(&symbol_clone, &symbol_order_books);
                        let mut metrics_map = liquidity_metrics.write().await;
                        metrics_map.insert(symbol_clone.clone(), metrics);
                    }
                }
            });
        }
        
        // Start arbitrage detection
        self.start_arbitrage_detection().await?;
        
        Ok(())
    }
    
    pub async fn start_arbitrage_detection(&self) -> Result<()> {
        let order_books = self.order_books.clone();
        let arbitrage_opportunities = self.arbitrage_opportunities.clone();
        
        tokio::spawn(async move {
            let mut interval = interval(Duration::from_secs(1)); // Check every second
            
            loop {
                interval.tick().await;
                
                let books = order_books.read().await;
                let mut opportunities = Vec::new();
                
                for (symbol, symbol_books) in books.iter() {
                    if symbol_books.len() >= 2 {
                        // Find arbitrage opportunities between exchanges
                        for i in 0..symbol_books.len() {
                            for j in (i + 1)..symbol_books.len() {
                                if let Some(opportunity) = Self::detect_arbitrage(
                                    symbol,
                                    &symbol_books[i],
                                    &symbol_books[j]
                                ) {
                                    opportunities.push(opportunity);
                                }
                            }
                        }
                    }
                }
                
                // Update arbitrage opportunities
                {
                    let mut arb_opps = arbitrage_opportunities.write().await;
                    *arb_opps = opportunities;
                }
            }
        });
        
        Ok(())
    }
    
    pub async fn get_aggregated_order_book(&self, symbol: &str) -> Result<AggregatedOrderBook> {
        let books = self.order_books.read().await;
        
        if let Some(symbol_books) = books.get(symbol) {
            Ok(Self::aggregate_order_books(symbol, symbol_books))
        } else {
            Err(anyhow!("No order books found for symbol: {}", symbol))
        }
    }
    
    pub async fn get_best_liquidity_route(&self, symbol: &str, side: &str, quantity: Decimal) -> Result<LiquidityRoute> {
        let books = self.order_books.read().await;
        
        if let Some(symbol_books) = books.get(symbol) {
            Ok(Self::calculate_best_route(symbol, side, quantity, symbol_books))
        } else {
            Err(anyhow!("No liquidity data found for symbol: {}", symbol))
        }
    }
    
    pub async fn get_liquidity_metrics(&self, symbol: &str) -> Result<LiquidityMetrics> {
        let metrics = self.liquidity_metrics.read().await;
        
        if let Some(symbol_metrics) = metrics.get(symbol) {
            Ok(symbol_metrics.clone())
        } else {
            Err(anyhow!("No liquidity metrics found for symbol: {}", symbol))
        }
    }
    
    pub async fn get_arbitrage_opportunities(&self) -> Result<Vec<ArbitrageOpportunity>> {
        let opportunities = self.arbitrage_opportunities.read().await;
        Ok(opportunities.clone())
    }
    
    // Helper methods
    fn aggregate_order_books(symbol: &str, order_books: &[OrderBook]) -> AggregatedOrderBook {
        let mut all_bids = Vec::new();
        let mut all_asks = Vec::new();
        let mut sources = Vec::new();
        
        for book in order_books {
            all_bids.extend(book.bids.clone());
            all_asks.extend(book.asks.clone());
            sources.push(book.source.clone());
        }
        
        // Sort bids (highest price first) and asks (lowest price first)
        all_bids.sort_by(|a, b| b.price.cmp(&a.price));
        all_asks.sort_by(|a, b| a.price.cmp(&b.price));
        
        let best_bid = all_bids.first().map(|b| b.price);
        let best_ask = all_asks.first().map(|a| a.price);
        
        let spread = match (best_bid, best_ask) {
            (Some(bid), Some(ask)) => Some(ask - bid),
            _ => None,
        };
        
        let total_bid_volume = all_bids.iter().map(|b| b.quantity).sum();
        let total_ask_volume = all_asks.iter().map(|a| a.quantity).sum();
        
        AggregatedOrderBook {
            symbol: symbol.to_string(),
            bids: all_bids,
            asks: all_asks,
            best_bid,
            best_ask,
            spread,
            total_bid_volume,
            total_ask_volume,
            sources,
            timestamp: Utc::now(),
        }
    }
    
    fn calculate_liquidity_metrics(symbol: &str, order_books: &[OrderBook]) -> LiquidityMetrics {
        let aggregated = Self::aggregate_order_books(symbol, order_books);
        
        let total_liquidity_usd = (aggregated.total_bid_volume + aggregated.total_ask_volume) * 
            aggregated.best_bid.unwrap_or_default();
        
        let spread_bps = match (aggregated.best_bid, aggregated.best_ask) {
            (Some(bid), Some(ask)) => (ask - bid) / bid * Decimal::new(10000, 0),
            _ => Decimal::ZERO,
        };
        
        // Calculate depth at 1% and 5% price levels
        let depth_1_percent = Self::calculate_depth_at_percentage(&aggregated, Decimal::new(1, 2));
        let depth_5_percent = Self::calculate_depth_at_percentage(&aggregated, Decimal::new(5, 2));
        
        // Calculate price impact for different trade sizes
        let price_impact_1k = Self::calculate_price_impact(&aggregated, Decimal::new(1000, 0));
        let price_impact_10k = Self::calculate_price_impact(&aggregated, Decimal::new(10000, 0));
        let price_impact_100k = Self::calculate_price_impact(&aggregated, Decimal::new(100000, 0));
        
        // Calculate per-source metrics
        let mut source_metrics = HashMap::new();
        for book in order_books {
            let liquidity = (book.bids.iter().map(|b| b.quantity).sum::<Decimal>() +
                           book.asks.iter().map(|a| a.quantity).sum::<Decimal>()) *
                           book.bids.first().map(|b| b.price).unwrap_or_default();
            
            source_metrics.insert(book.source.clone(), LiquiditySourceMetrics {
                source: book.source.clone(),
                liquidity_usd: liquidity,
                volume_24h: Decimal::ZERO, // Would be fetched separately
                spread_bps: Decimal::ZERO, // Would be calculated
                uptime_percentage: Decimal::new(99, 2),
                latency_ms: 50,
            });
        }
        
        LiquidityMetrics {
            symbol: symbol.to_string(),
            total_liquidity_usd,
            bid_liquidity_usd: aggregated.total_bid_volume * aggregated.best_bid.unwrap_or_default(),
            ask_liquidity_usd: aggregated.total_ask_volume * aggregated.best_ask.unwrap_or_default(),
            spread_bps,
            depth_1_percent,
            depth_5_percent,
            volume_24h: Decimal::ZERO, // Would be aggregated from exchanges
            price_impact_1k,
            price_impact_10k,
            price_impact_100k,
            sources: source_metrics,
            timestamp: Utc::now(),
        }
    }
    
    fn calculate_depth_at_percentage(order_book: &AggregatedOrderBook, percentage: Decimal) -> Decimal {
        let mid_price = match (order_book.best_bid, order_book.best_ask) {
            (Some(bid), Some(ask)) => (bid + ask) / Decimal::new(2, 0),
            _ => return Decimal::ZERO,
        };
        
        let price_range = mid_price * percentage / Decimal::new(100, 0);
        let upper_bound = mid_price + price_range;
        let lower_bound = mid_price - price_range;
        
        let bid_depth = order_book.bids.iter()
            .filter(|b| b.price >= lower_bound)
            .map(|b| b.quantity)
            .sum::<Decimal>();
            
        let ask_depth = order_book.asks.iter()
            .filter(|a| a.price <= upper_bound)
            .map(|a| a.quantity)
            .sum::<Decimal>();
        
        bid_depth + ask_depth
    }
    
    fn calculate_price_impact(order_book: &AggregatedOrderBook, trade_size_usd: Decimal) -> Decimal {
        let mid_price = match (order_book.best_bid, order_book.best_ask) {
            (Some(bid), Some(ask)) => (bid + ask) / Decimal::new(2, 0),
            _ => return Decimal::ZERO,
        };
        
        let trade_quantity = trade_size_usd / mid_price;
        let mut remaining_quantity = trade_quantity;
        let mut total_cost = Decimal::ZERO;
        
        // Simulate buying through the order book
        for ask in &order_book.asks {
            if remaining_quantity <= Decimal::ZERO {
                break;
            }
            
            let quantity_to_buy = remaining_quantity.min(ask.quantity);
            total_cost += quantity_to_buy * ask.price;
            remaining_quantity -= quantity_to_buy;
        }
        
        if remaining_quantity > Decimal::ZERO {
            return Decimal::new(100, 0); // 100% impact if not enough liquidity
        }
        
        let average_price = total_cost / trade_quantity;
        (average_price - mid_price) / mid_price * Decimal::new(100, 0)
    }
    
    fn calculate_best_route(symbol: &str, side: &str, quantity: Decimal, order_books: &[OrderBook]) -> LiquidityRoute {
        let mut routes = Vec::new();
        let mut total_cost = Decimal::ZERO;
        let mut remaining_quantity = quantity;
        
        // Simple implementation - would be more sophisticated in practice
        for book in order_books {
            if remaining_quantity <= Decimal::ZERO {
                break;
            }
            
            let levels = if side == "BUY" { &book.asks } else { &book.bids };
            
            for level in levels {
                if remaining_quantity <= Decimal::ZERO {
                    break;
                }
                
                let quantity_to_trade = remaining_quantity.min(level.quantity);
                let cost = quantity_to_trade * level.price;
                
                routes.push(RouteStep {
                    exchange: book.source.clone(),
                    quantity: quantity_to_trade,
                    price: level.price,
                    fee: cost * Decimal::new(1, 3), // 0.1% fee
                    is_dex: false,
                    pool_address: None,
                });
                
                total_cost += cost;
                remaining_quantity -= quantity_to_trade;
            }
        }
        
        let average_price = if quantity > Decimal::ZERO {
            total_cost / quantity
        } else {
            Decimal::ZERO
        };
        
        LiquidityRoute {
            symbol: symbol.to_string(),
            side: side.to_string(),
            quantity,
            routes,
            total_price: total_cost,
            average_price,
            price_impact: Decimal::ZERO, // Would be calculated
            estimated_slippage: Decimal::new(5, 3), // 0.5%
            gas_cost: None,
            execution_time_ms: 100,
        }
    }
    
    fn detect_arbitrage(symbol: &str, book1: &OrderBook, book2: &OrderBook) -> Option<ArbitrageOpportunity> {
        let best_bid1 = book1.bids.first()?.price;
        let best_ask1 = book1.asks.first()?.price;
        let best_bid2 = book2.bids.first()?.price;
        let best_ask2 = book2.asks.first()?.price;
        
        // Check if we can buy on one exchange and sell on another for profit
        let profit_1_to_2 = best_bid2 - best_ask1;
        let profit_2_to_1 = best_bid1 - best_ask2;
        
        let min_profit_threshold = Decimal::new(1, 2); // 1% minimum profit
        
        if profit_1_to_2 > min_profit_threshold {
            let profit_percentage = profit_1_to_2 / best_ask1 * Decimal::new(100, 0);
            let max_quantity = book1.asks.first()?.quantity.min(book2.bids.first()?.quantity);
            
            Some(ArbitrageOpportunity {
                id: Uuid::new_v4().to_string(),
                symbol: symbol.to_string(),
                buy_exchange: book1.source.clone(),
                sell_exchange: book2.source.clone(),
                buy_price: best_ask1,
                sell_price: best_bid2,
                profit_percentage,
                profit_usd: profit_1_to_2 * max_quantity,
                max_quantity,
                estimated_gas_cost: Some(Decimal::new(50, 0)), // $50 gas cost
                net_profit: profit_1_to_2 * max_quantity - Decimal::new(50, 0),
                confidence_score: Decimal::new(85, 2), // 85%
                timestamp: Utc::now(),
            })
        } else if profit_2_to_1 > min_profit_threshold {
            let profit_percentage = profit_2_to_1 / best_ask2 * Decimal::new(100, 0);
            let max_quantity = book2.asks.first()?.quantity.min(book1.bids.first()?.quantity);
            
            Some(ArbitrageOpportunity {
                id: Uuid::new_v4().to_string(),
                symbol: symbol.to_string(),
                buy_exchange: book2.source.clone(),
                sell_exchange: book1.source.clone(),
                buy_price: best_ask2,
                sell_price: best_bid1,
                profit_percentage,
                profit_usd: profit_2_to_1 * max_quantity,
                max_quantity,
                estimated_gas_cost: Some(Decimal::new(50, 0)),
                net_profit: profit_2_to_1 * max_quantity - Decimal::new(50, 0),
                confidence_score: Decimal::new(85, 2),
                timestamp: Utc::now(),
            })
        } else {
            None
        }
    }
}

// Application state
#[derive(Clone)]
pub struct AppState {
    pub aggregator: Arc<LiquidityAggregator>,
}

// API handlers
pub async fn get_aggregated_order_book(
    Path(symbol): Path<String>,
    State(state): State<AppState>,
) -> Result<Json<AggregatedOrderBook>, StatusCode> {
    match state.aggregator.get_aggregated_order_book(&symbol).await {
        Ok(order_book) => Ok(Json(order_book)),
        Err(_) => Err(StatusCode::NOT_FOUND),
    }
}

pub async fn get_liquidity_metrics(
    Path(symbol): Path<String>,
    State(state): State<AppState>,
) -> Result<Json<LiquidityMetrics>, StatusCode> {
    match state.aggregator.get_liquidity_metrics(&symbol).await {
        Ok(metrics) => Ok(Json(metrics)),
        Err(_) => Err(StatusCode::NOT_FOUND),
    }
}

pub async fn get_best_route(
    Path(symbol): Path<String>,
    Query(params): Query<HashMap<String, String>>,
    State(state): State<AppState>,
) -> Result<Json<LiquidityRoute>, StatusCode> {
    let side = params.get("side").unwrap_or(&"BUY".to_string()).clone();
    let quantity = params.get("quantity")
        .and_then(|q| q.parse::<Decimal>().ok())
        .unwrap_or(Decimal::new(1, 0));
    
    match state.aggregator.get_best_liquidity_route(&symbol, &side, quantity).await {
        Ok(route) => Ok(Json(route)),
        Err(_) => Err(StatusCode::NOT_FOUND),
    }
}

pub async fn get_arbitrage_opportunities(
    State(state): State<AppState>,
) -> Result<Json<Vec<ArbitrageOpportunity>>, StatusCode> {
    match state.aggregator.get_arbitrage_opportunities().await {
        Ok(opportunities) => Ok(Json(opportunities)),
        Err(_) => Err(StatusCode::INTERNAL_SERVER_ERROR),
    }
}

pub async fn health_check() -> Json<Value> {
    Json(json!({
        "status": "healthy",
        "timestamp": Utc::now().to_rfc3339(),
        "service": "liquidity-aggregator"
    }))
}

// Main function
#[tokio::main]
async fn main() -> Result<()> {
    tracing_subscriber::init();
    
    let config = Config::from_env();
    let aggregator = Arc::new(LiquidityAggregator::new(&config).await?);
    
    // Start aggregation for popular symbols
    let symbols = vec![
        "BTCUSDT".to_string(),
        "ETHUSDT".to_string(),
        "BNBUSDT".to_string(),
        "ADAUSDT".to_string(),
        "DOTUSDT".to_string(),
        "XRPUSDT".to_string(),
        "LTCUSDT".to_string(),
        "LINKUSDT".to_string(),
        "BCHUSDT".to_string(),
        "XLMUSDT".to_string(),
    ];
    
    aggregator.start_aggregation(symbols).await?;
    
    let app_state = AppState { aggregator };
    
    // Build the router
    let app = Router::new()
        .route("/api/v1/orderbook/:symbol", get(get_aggregated_order_book))
        .route("/api/v1/metrics/:symbol", get(get_liquidity_metrics))
        .route("/api/v1/route/:symbol", get(get_best_route))
        .route("/api/v1/arbitrage", get(get_arbitrage_opportunities))
        .route("/health", get(health_check))
        .layer(
            ServiceBuilder::new()
                .layer(TraceLayer::new_for_http())
                .layer(CorsLayer::permissive())
        )
        .with_state(app_state);
    
    info!("Starting TigerEx Liquidity Aggregator on port 8088");
    
    let listener = tokio::net::TcpListener::bind("0.0.0.0:8088").await?;
    axum::serve(listener, app).await?;
    
    Ok(())
}