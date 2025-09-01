//! Data models for spot trading service

use serde::{Deserialize, Serialize};
use uuid::Uuid;
use chrono::{DateTime, Utc};
use rust_decimal::Decimal;
use sqlx::FromRow;

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct TradingPair {
    pub id: i32,
    pub symbol: String,
    pub base_asset: String,
    pub quote_asset: String,
    pub status: String,
    pub min_order_size: Decimal,
    pub max_order_size: Option<Decimal>,
    pub min_price: Decimal,
    pub max_price: Option<Decimal>,
    pub price_precision: i32,
    pub quantity_precision: i32,
    pub maker_fee: Decimal,
    pub taker_fee: Decimal,
    pub is_spot_enabled: bool,
    pub is_margin_enabled: bool,
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CreateTradingPairRequest {
    pub symbol: String,
    pub base_asset: String,
    pub quote_asset: String,
    pub min_order_size: Decimal,
    pub max_order_size: Option<Decimal>,
    pub min_price: Decimal,
    pub max_price: Option<Decimal>,
    pub price_precision: i32,
    pub quantity_precision: i32,
    pub maker_fee: Decimal,
    pub taker_fee: Decimal,
    pub is_spot_enabled: bool,
    pub is_margin_enabled: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UpdateTradingPairRequest {
    pub status: Option<String>,
    pub min_order_size: Option<Decimal>,
    pub max_order_size: Option<Decimal>,
    pub min_price: Option<Decimal>,
    pub max_price: Option<Decimal>,
    pub maker_fee: Option<Decimal>,
    pub taker_fee: Option<Decimal>,
    pub is_spot_enabled: Option<bool>,
    pub is_margin_enabled: Option<bool>,
}

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct SpotOrder {
    pub id: i32,
    pub order_id: Uuid,
    pub user_id: String,
    pub symbol: String,
    pub side: String, // BUY, SELL
    pub order_type: String, // MARKET, LIMIT, STOP_LOSS, STOP_LOSS_LIMIT, TAKE_PROFIT, TAKE_PROFIT_LIMIT
    pub quantity: Decimal,
    pub price: Option<Decimal>,
    pub stop_price: Option<Decimal>,
    pub filled_quantity: Decimal,
    pub remaining_quantity: Decimal,
    pub status: String, // NEW, PARTIALLY_FILLED, FILLED, CANCELED, REJECTED, EXPIRED
    pub time_in_force: String, // GTC, IOC, FOK
    pub created_at: DateTime<Utc>,
    pub updated_at: DateTime<Utc>,
    pub filled_at: Option<DateTime<Utc>>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PlaceOrderRequest {
    pub symbol: String,
    pub side: String,
    pub order_type: String,
    pub quantity: Decimal,
    pub price: Option<Decimal>,
    pub stop_price: Option<Decimal>,
    pub time_in_force: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize, FromRow)]
pub struct Trade {
    pub id: i32,
    pub trade_id: Uuid,
    pub symbol: String,
    pub buyer_order_id: Uuid,
    pub seller_order_id: Uuid,
    pub buyer_user_id: String,
    pub seller_user_id: String,
    pub price: Decimal,
    pub quantity: Decimal,
    pub buyer_fee: Decimal,
    pub seller_fee: Decimal,
    pub is_buyer_maker: bool,
    pub created_at: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrderBook {
    pub symbol: String,
    pub bids: Vec<OrderBookLevel>,
    pub asks: Vec<OrderBookLevel>,
    pub timestamp: DateTime<Utc>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct OrderBookLevel {
    pub price: Decimal,
    pub quantity: Decimal,
    pub count: i32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Ticker {
    pub symbol: String,
    pub price_change: Decimal,
    pub price_change_percent: Decimal,
    pub weighted_avg_price: Decimal,
    pub prev_close_price: Decimal,
    pub last_price: Decimal,
    pub last_qty: Decimal,
    pub bid_price: Decimal,
    pub bid_qty: Decimal,
    pub ask_price: Decimal,
    pub ask_qty: Decimal,
    pub open_price: Decimal,
    pub high_price: Decimal,
    pub low_price: Decimal,
    pub volume: Decimal,
    pub quote_volume: Decimal,
    pub open_time: DateTime<Utc>,
    pub close_time: DateTime<Utc>,
    pub count: i64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Kline {
    pub open_time: DateTime<Utc>,
    pub close_time: DateTime<Utc>,
    pub symbol: String,
    pub interval: String,
    pub open_price: Decimal,
    pub high_price: Decimal,
    pub low_price: Decimal,
    pub close_price: Decimal,
    pub volume: Decimal,
    pub quote_volume: Decimal,
    pub trade_count: i64,
    pub taker_buy_volume: Decimal,
    pub taker_buy_quote_volume: Decimal,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct MarketDepth {
    pub symbol: String,
    pub bids: Vec<[Decimal; 2]>, // [price, quantity]
    pub asks: Vec<[Decimal; 2]>, // [price, quantity]
    pub timestamp: DateTime<Utc>,
}

// WebSocket message types
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct WebSocketMessage {
    pub stream: String,
    pub data: serde_json::Value,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SubscribeMessage {
    pub method: String,
    pub params: Vec<String>,
    pub id: Option<u64>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct UnsubscribeMessage {
    pub method: String,
    pub params: Vec<String>,
    pub id: Option<u64>,
}
