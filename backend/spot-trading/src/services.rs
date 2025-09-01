//! Business logic services for spot trading

use sqlx::PgPool;
use redis::aio::ConnectionManager;
use anyhow::Result;
use uuid::Uuid;
use rust_decimal::Decimal;
use chrono::Utc;
use std::collections::HashMap;
use crate::models::*;

pub struct TradingService {
    db: PgPool,
    redis: ConnectionManager,
}

impl TradingService {
    pub fn new(db: PgPool, redis: ConnectionManager) -> Self {
        Self { db, redis }
    }
    
    pub async fn get_user_trades(
        &self,
        user_id: String,
        symbol: Option<String>,
        limit: i64,
    ) -> Result<Vec<Trade>> {
        let mut query = "SELECT * FROM trades WHERE (buyer_user_id = $1 OR seller_user_id = $1)".to_string();
        let mut params: Vec<&dyn sqlx::Encode<sqlx::Postgres> + Send + Sync> = vec![&user_id];
        
        if let Some(ref sym) = symbol {
            query.push_str(" AND symbol = $2");
            params.push(sym);
        }
        
        query.push_str(" ORDER BY created_at DESC LIMIT $");
        query.push_str(&(params.len() + 1).to_string());
        
        let trades = sqlx::query_as::<_, Trade>(&query)
            .bind(&user_id)
            .bind(symbol)
            .bind(limit)
            .fetch_all(&self.db)
            .await?;
        
        Ok(trades)
    }
    
    pub async fn execute_trade(
        &self,
        buyer_order: &SpotOrder,
        seller_order: &SpotOrder,
        price: Decimal,
        quantity: Decimal,
    ) -> Result<Trade> {
        let trade_id = Uuid::new_v4();
        
        // Calculate fees
        let buyer_fee = quantity * price * Decimal::from_str_exact("0.001")?; // 0.1% fee
        let seller_fee = quantity * price * Decimal::from_str_exact("0.001")?;
        
        let trade = sqlx::query_as::<_, Trade>(
            r#"
            INSERT INTO trades (
                trade_id, symbol, buyer_order_id, seller_order_id, buyer_user_id, seller_user_id,
                price, quantity, buyer_fee, seller_fee, is_buyer_maker, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, NOW())
            RETURNING *
            "#
        )
        .bind(trade_id)
        .bind(&buyer_order.symbol)
        .bind(buyer_order.order_id)
        .bind(seller_order.order_id)
        .bind(&buyer_order.user_id)
        .bind(&seller_order.user_id)
        .bind(price)
        .bind(quantity)
        .bind(buyer_fee)
        .bind(seller_fee)
        .bind(false) // Assume taker is buyer for now
        .fetch_one(&self.db)
        .await?;
        
        Ok(trade)
    }
}

pub struct MarketDataService {
    db: PgPool,
    redis: ConnectionManager,
}

impl MarketDataService {
    pub fn new(db: PgPool, redis: ConnectionManager) -> Self {
        Self { db, redis }
    }
    
    pub async fn initialize_pair(&self, symbol: &str) {
        // Initialize market data structures for new trading pair
        tracing::info!("Initializing market data for pair: {}", symbol);
    }
    
    pub async fn get_orderbook(&self, symbol: &str, limit: usize) -> Result<OrderBook> {
        // Get bids (buy orders) - highest price first
        let bids = sqlx::query_as::<_, OrderBookLevel>(
            r#"
            SELECT price, SUM(remaining_quantity) as quantity, COUNT(*) as count
            FROM spot_orders 
            WHERE symbol = $1 AND side = 'BUY' AND status = 'NEW'
            GROUP BY price 
            ORDER BY price DESC 
            LIMIT $2
            "#
        )
        .bind(symbol)
        .bind(limit as i64)
        .fetch_all(&self.db)
        .await?;
        
        // Get asks (sell orders) - lowest price first
        let asks = sqlx::query_as::<_, OrderBookLevel>(
            r#"
            SELECT price, SUM(remaining_quantity) as quantity, COUNT(*) as count
            FROM spot_orders 
            WHERE symbol = $1 AND side = 'SELL' AND status = 'NEW'
            GROUP BY price 
            ORDER BY price ASC 
            LIMIT $2
            "#
        )
        .bind(symbol)
        .bind(limit as i64)
        .fetch_all(&self.db)
        .await?;
        
        Ok(OrderBook {
            symbol: symbol.to_string(),
            bids,
            asks,
            timestamp: Utc::now(),
        })
    }
    
    pub async fn get_ticker(&self, symbol: &str) -> Result<Ticker> {
        // This is a simplified implementation
        // In production, you'd calculate these from recent trades and orders
        
        let last_trade = sqlx::query_as::<_, Trade>(
            "SELECT * FROM trades WHERE symbol = $1 ORDER BY created_at DESC LIMIT 1"
        )
        .bind(symbol)
        .fetch_optional(&self.db)
        .await?;
        
        let last_price = last_trade.map(|t| t.price).unwrap_or_default();
        
        // Get 24h stats (simplified)
        let stats = sqlx::query!(
            r#"
            SELECT 
                COUNT(*) as count,
                SUM(quantity) as volume,
                SUM(price * quantity) as quote_volume,
                MIN(price) as low_price,
                MAX(price) as high_price
            FROM trades 
            WHERE symbol = $1 AND created_at > NOW() - INTERVAL '24 hours'
            "#,
            symbol
        )
        .fetch_one(&self.db)
        .await?;
        
        Ok(Ticker {
            symbol: symbol.to_string(),
            price_change: Decimal::ZERO,
            price_change_percent: Decimal::ZERO,
            weighted_avg_price: last_price,
            prev_close_price: last_price,
            last_price,
            last_qty: Decimal::ZERO,
            bid_price: Decimal::ZERO,
            bid_qty: Decimal::ZERO,
            ask_price: Decimal::ZERO,
            ask_qty: Decimal::ZERO,
            open_price: last_price,
            high_price: stats.high_price.unwrap_or_default().into(),
            low_price: stats.low_price.unwrap_or_default().into(),
            volume: stats.volume.unwrap_or_default().into(),
            quote_volume: stats.quote_volume.unwrap_or_default().into(),
            open_time: Utc::now() - chrono::Duration::hours(24),
            close_time: Utc::now(),
            count: stats.count.unwrap_or_default(),
        })
    }
    
    pub async fn get_all_tickers(&self) -> Result<Vec<Ticker>> {
        let symbols = sqlx::query_scalar::<_, String>(
            "SELECT symbol FROM trading_pairs WHERE status = 'ACTIVE'"
        )
        .fetch_all(&self.db)
        .await?;
        
        let mut tickers = Vec::new();
        for symbol in symbols {
            if let Ok(ticker) = self.get_ticker(&symbol).await {
                tickers.push(ticker);
            }
        }
        
        Ok(tickers)
    }
    
    pub async fn get_klines(&self, symbol: &str, interval: &str, limit: i64) -> Result<Vec<Kline>> {
        // Simplified implementation - in production you'd have pre-aggregated kline data
        Ok(vec![])
    }
    
    pub async fn get_market_depth(&self, symbol: &str, limit: usize) -> Result<MarketDepth> {
        let orderbook = self.get_orderbook(symbol, limit).await?;
        
        let bids: Vec<[Decimal; 2]> = orderbook.bids.into_iter()
            .map(|level| [level.price, level.quantity])
            .collect();
            
        let asks: Vec<[Decimal; 2]> = orderbook.asks.into_iter()
            .map(|level| [level.price, level.quantity])
            .collect();
        
        Ok(MarketDepth {
            symbol: symbol.to_string(),
            bids,
            asks,
            timestamp: Utc::now(),
        })
    }
}

pub struct OrderService {
    db: PgPool,
    redis: ConnectionManager,
}

impl OrderService {
    pub fn new(db: PgPool, redis: ConnectionManager) -> Self {
        Self { db, redis }
    }
    
    pub async fn place_order(
        &self,
        user_id: String,
        order_req: PlaceOrderRequest,
    ) -> Result<SpotOrder> {
        let order_id = Uuid::new_v4();
        let time_in_force = order_req.time_in_force.unwrap_or_else(|| "GTC".to_string());
        
        // Validate order
        self.validate_order(&order_req).await?;
        
        let order = sqlx::query_as::<_, SpotOrder>(
            r#"
            INSERT INTO spot_orders (
                order_id, user_id, symbol, side, order_type, quantity, price, stop_price,
                filled_quantity, remaining_quantity, status, time_in_force, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 0, $6, 'NEW', $9, NOW(), NOW())
            RETURNING *
            "#
        )
        .bind(order_id)
        .bind(&user_id)
        .bind(&order_req.symbol)
        .bind(&order_req.side)
        .bind(&order_req.order_type)
        .bind(&order_req.quantity)
        .bind(&order_req.price)
        .bind(&order_req.stop_price)
        .bind(&time_in_force)
        .fetch_one(&self.db)
        .await?;
        
        // Send order to matching engine
        self.send_to_matching_engine(&order).await?;
        
        Ok(order)
    }
    
    pub async fn get_user_orders(
        &self,
        user_id: String,
        symbol: Option<String>,
        status: Option<String>,
        limit: i64,
    ) -> Result<Vec<SpotOrder>> {
        let mut query = "SELECT * FROM spot_orders WHERE user_id = $1".to_string();
        let mut param_count = 2;
        
        if symbol.is_some() {
            query.push_str(&format!(" AND symbol = ${}", param_count));
            param_count += 1;
        }
        
        if status.is_some() {
            query.push_str(&format!(" AND status = ${}", param_count));
            param_count += 1;
        }
        
        query.push_str(&format!(" ORDER BY created_at DESC LIMIT ${}", param_count));
        
        let mut query_builder = sqlx::query_as::<_, SpotOrder>(&query).bind(&user_id);
        
        if let Some(sym) = symbol {
            query_builder = query_builder.bind(sym);
        }
        
        if let Some(stat) = status {
            query_builder = query_builder.bind(stat);
        }
        
        let orders = query_builder.bind(limit).fetch_all(&self.db).await?;
        
        Ok(orders)
    }
    
    pub async fn get_order(&self, order_id: Uuid, user_id: String) -> Result<Option<SpotOrder>> {
        let order = sqlx::query_as::<_, SpotOrder>(
            "SELECT * FROM spot_orders WHERE order_id = $1 AND user_id = $2"
        )
        .bind(order_id)
        .bind(&user_id)
        .fetch_optional(&self.db)
        .await?;
        
        Ok(order)
    }
    
    pub async fn cancel_order(&self, order_id: Uuid, user_id: String) -> Result<SpotOrder> {
        let order = sqlx::query_as::<_, SpotOrder>(
            r#"
            UPDATE spot_orders 
            SET status = 'CANCELED', updated_at = NOW() 
            WHERE order_id = $1 AND user_id = $2 AND status IN ('NEW', 'PARTIALLY_FILLED')
            RETURNING *
            "#
        )
        .bind(order_id)
        .bind(&user_id)
        .fetch_one(&self.db)
        .await?;
        
        // Notify matching engine about cancellation
        self.send_cancellation_to_matching_engine(&order).await?;
        
        Ok(order)
    }
    
    async fn validate_order(&self, order_req: &PlaceOrderRequest) -> Result<()> {
        // Check if trading pair exists and is active
        let pair = sqlx::query_as::<_, TradingPair>(
            "SELECT * FROM trading_pairs WHERE symbol = $1 AND status = 'ACTIVE'"
        )
        .bind(&order_req.symbol)
        .fetch_optional(&self.db)
        .await?;
        
        let pair = pair.ok_or_else(|| anyhow::anyhow!("Trading pair not found or inactive"))?;
        
        // Validate order size
        if order_req.quantity < pair.min_order_size {
            return Err(anyhow::anyhow!("Order quantity below minimum"));
        }
        
        if let Some(max_size) = pair.max_order_size {
            if order_req.quantity > max_size {
                return Err(anyhow::anyhow!("Order quantity above maximum"));
            }
        }
        
        // Validate price for limit orders
        if order_req.order_type == "LIMIT" {
            if let Some(price) = order_req.price {
                if price < pair.min_price {
                    return Err(anyhow::anyhow!("Order price below minimum"));
                }
                
                if let Some(max_price) = pair.max_price {
                    if price > max_price {
                        return Err(anyhow::anyhow!("Order price above maximum"));
                    }
                }
            } else {
                return Err(anyhow::anyhow!("Price required for limit orders"));
            }
        }
        
        Ok(())
    }
    
    async fn send_to_matching_engine(&self, order: &SpotOrder) -> Result<()> {
        // In production, this would send the order to the matching engine via Kafka or direct API call
        tracing::info!("Sending order {} to matching engine", order.order_id);
        Ok(())
    }
    
    async fn send_cancellation_to_matching_engine(&self, order: &SpotOrder) -> Result<()> {
        // In production, this would send the cancellation to the matching engine
        tracing::info!("Sending cancellation for order {} to matching engine", order.order_id);
        Ok(())
    }
}
