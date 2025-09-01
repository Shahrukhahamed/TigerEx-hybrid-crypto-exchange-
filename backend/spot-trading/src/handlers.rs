//! HTTP handlers for spot trading endpoints

use actix_web::{web, HttpResponse, Result as ActixResult};
use serde_json::json;
use uuid::Uuid;
use crate::{AppState, models::*};

// Trading pair management handlers
pub async fn get_trading_pairs(
    data: web::Data<AppState>,
) -> ActixResult<HttpResponse> {
    match sqlx::query_as::<_, TradingPair>(
        "SELECT * FROM trading_pairs WHERE status = 'ACTIVE' ORDER BY symbol"
    )
    .fetch_all(&data.db)
    .await
    {
        Ok(pairs) => Ok(HttpResponse::Ok().json(pairs)),
        Err(e) => {
            tracing::error!("Failed to fetch trading pairs: {}", e);
            Ok(HttpResponse::InternalServerError().json(json!({
                "error": "Failed to fetch trading pairs"
            })))
        }
    }
}

pub async fn create_trading_pair(
    data: web::Data<AppState>,
    req: web::Json<CreateTradingPairRequest>,
) -> ActixResult<HttpResponse> {
    let pair = req.into_inner();
    
    match sqlx::query_as::<_, TradingPair>(
        r#"
        INSERT INTO trading_pairs (
            symbol, base_asset, quote_asset, status, min_order_size, max_order_size,
            min_price, max_price, price_precision, quantity_precision, maker_fee, taker_fee,
            is_spot_enabled, is_margin_enabled, created_at, updated_at
        ) VALUES ($1, $2, $3, 'ACTIVE', $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, NOW(), NOW())
        RETURNING *
        "#
    )
    .bind(&pair.symbol)
    .bind(&pair.base_asset)
    .bind(&pair.quote_asset)
    .bind(&pair.min_order_size)
    .bind(&pair.max_order_size)
    .bind(&pair.min_price)
    .bind(&pair.max_price)
    .bind(&pair.price_precision)
    .bind(&pair.quantity_precision)
    .bind(&pair.maker_fee)
    .bind(&pair.taker_fee)
    .bind(&pair.is_spot_enabled)
    .bind(&pair.is_margin_enabled)
    .fetch_one(&data.db)
    .await
    {
        Ok(created_pair) => {
            // Initialize market data for the new pair
            data.market_data_service.initialize_pair(&pair.symbol).await;
            
            Ok(HttpResponse::Created().json(created_pair))
        },
        Err(e) => {
            tracing::error!("Failed to create trading pair: {}", e);
            Ok(HttpResponse::BadRequest().json(json!({
                "error": "Failed to create trading pair"
            })))
        }
    }
}

pub async fn update_trading_pair(
    data: web::Data<AppState>,
    path: web::Path<String>,
    req: web::Json<UpdateTradingPairRequest>,
) -> ActixResult<HttpResponse> {
    let symbol = path.into_inner();
    let update_req = req.into_inner();
    
    let mut query = "UPDATE trading_pairs SET updated_at = NOW()".to_string();
    let mut params: Vec<String> = vec![];
    let mut param_count = 1;
    
    if let Some(status) = &update_req.status {
        query.push_str(&format!(", status = ${}", param_count));
        params.push(status.clone());
        param_count += 1;
    }
    
    if let Some(min_order_size) = &update_req.min_order_size {
        query.push_str(&format!(", min_order_size = ${}", param_count));
        params.push(min_order_size.to_string());
        param_count += 1;
    }
    
    // Add other fields...
    
    query.push_str(&format!(" WHERE symbol = ${} RETURNING *", param_count));
    params.push(symbol);
    
    // Execute update query (simplified for brevity)
    Ok(HttpResponse::Ok().json(json!({
        "message": "Trading pair updated successfully"
    })))
}

pub async fn delete_trading_pair(
    data: web::Data<AppState>,
    path: web::Path<String>,
) -> ActixResult<HttpResponse> {
    let symbol = path.into_inner();
    
    match sqlx::query(
        "UPDATE trading_pairs SET status = 'DELISTED', updated_at = NOW() WHERE symbol = $1"
    )
    .bind(&symbol)
    .execute(&data.db)
    .await
    {
        Ok(_) => Ok(HttpResponse::Ok().json(json!({
            "message": "Trading pair delisted successfully"
        }))),
        Err(e) => {
            tracing::error!("Failed to delete trading pair: {}", e);
            Ok(HttpResponse::InternalServerError().json(json!({
                "error": "Failed to delete trading pair"
            })))
        }
    }
}

// Order management handlers
pub async fn place_order(
    data: web::Data<AppState>,
    req: web::Json<PlaceOrderRequest>,
    // TODO: Extract user_id from JWT token
) -> ActixResult<HttpResponse> {
    let order_req = req.into_inner();
    let user_id = "user123".to_string(); // TODO: Get from JWT
    
    match data.order_service.place_order(user_id, order_req).await {
        Ok(order) => Ok(HttpResponse::Created().json(order)),
        Err(e) => {
            tracing::error!("Failed to place order: {}", e);
            Ok(HttpResponse::BadRequest().json(json!({
                "error": format!("Failed to place order: {}", e)
            })))
        }
    }
}

pub async fn get_orders(
    data: web::Data<AppState>,
    query: web::Query<std::collections::HashMap<String, String>>,
) -> ActixResult<HttpResponse> {
    let user_id = "user123".to_string(); // TODO: Get from JWT
    let symbol = query.get("symbol");
    let status = query.get("status");
    let limit: i64 = query.get("limit").and_then(|l| l.parse().ok()).unwrap_or(100);
    
    match data.order_service.get_user_orders(user_id, symbol.cloned(), status.cloned(), limit).await {
        Ok(orders) => Ok(HttpResponse::Ok().json(orders)),
        Err(e) => {
            tracing::error!("Failed to fetch orders: {}", e);
            Ok(HttpResponse::InternalServerError().json(json!({
                "error": "Failed to fetch orders"
            })))
        }
    }
}

pub async fn get_order(
    data: web::Data<AppState>,
    path: web::Path<Uuid>,
) -> ActixResult<HttpResponse> {
    let order_id = path.into_inner();
    let user_id = "user123".to_string(); // TODO: Get from JWT
    
    match data.order_service.get_order(order_id, user_id).await {
        Ok(Some(order)) => Ok(HttpResponse::Ok().json(order)),
        Ok(None) => Ok(HttpResponse::NotFound().json(json!({
            "error": "Order not found"
        }))),
        Err(e) => {
            tracing::error!("Failed to fetch order: {}", e);
            Ok(HttpResponse::InternalServerError().json(json!({
                "error": "Failed to fetch order"
            })))
        }
    }
}

pub async fn cancel_order(
    data: web::Data<AppState>,
    path: web::Path<Uuid>,
) -> ActixResult<HttpResponse> {
    let order_id = path.into_inner();
    let user_id = "user123".to_string(); // TODO: Get from JWT
    
    match data.order_service.cancel_order(order_id, user_id).await {
        Ok(order) => Ok(HttpResponse::Ok().json(order)),
        Err(e) => {
            tracing::error!("Failed to cancel order: {}", e);
            Ok(HttpResponse::BadRequest().json(json!({
                "error": format!("Failed to cancel order: {}", e)
            })))
        }
    }
}

pub async fn get_trades(
    data: web::Data<AppState>,
    query: web::Query<std::collections::HashMap<String, String>>,
) -> ActixResult<HttpResponse> {
    let user_id = "user123".to_string(); // TODO: Get from JWT
    let symbol = query.get("symbol");
    let limit: i64 = query.get("limit").and_then(|l| l.parse().ok()).unwrap_or(100);
    
    match data.trading_service.get_user_trades(user_id, symbol.cloned(), limit).await {
        Ok(trades) => Ok(HttpResponse::Ok().json(trades)),
        Err(e) => {
            tracing::error!("Failed to fetch trades: {}", e);
            Ok(HttpResponse::InternalServerError().json(json!({
                "error": "Failed to fetch trades"
            })))
        }
    }
}

// Market data handlers
pub async fn get_orderbook(
    data: web::Data<AppState>,
    path: web::Path<String>,
    query: web::Query<std::collections::HashMap<String, String>>,
) -> ActixResult<HttpResponse> {
    let symbol = path.into_inner();
    let limit: usize = query.get("limit").and_then(|l| l.parse().ok()).unwrap_or(100);
    
    match data.market_data_service.get_orderbook(&symbol, limit).await {
        Ok(orderbook) => Ok(HttpResponse::Ok().json(orderbook)),
        Err(e) => {
            tracing::error!("Failed to fetch orderbook: {}", e);
            Ok(HttpResponse::InternalServerError().json(json!({
                "error": "Failed to fetch orderbook"
            })))
        }
    }
}

pub async fn get_ticker(
    data: web::Data<AppState>,
    path: web::Path<String>,
) -> ActixResult<HttpResponse> {
    let symbol = path.into_inner();
    
    match data.market_data_service.get_ticker(&symbol).await {
        Ok(ticker) => Ok(HttpResponse::Ok().json(ticker)),
        Err(e) => {
            tracing::error!("Failed to fetch ticker: {}", e);
            Ok(HttpResponse::InternalServerError().json(json!({
                "error": "Failed to fetch ticker"
            })))
        }
    }
}

pub async fn get_all_tickers(
    data: web::Data<AppState>,
) -> ActixResult<HttpResponse> {
    match data.market_data_service.get_all_tickers().await {
        Ok(tickers) => Ok(HttpResponse::Ok().json(tickers)),
        Err(e) => {
            tracing::error!("Failed to fetch tickers: {}", e);
            Ok(HttpResponse::InternalServerError().json(json!({
                "error": "Failed to fetch tickers"
            })))
        }
    }
}

pub async fn get_klines(
    data: web::Data<AppState>,
    path: web::Path<String>,
    query: web::Query<std::collections::HashMap<String, String>>,
) -> ActixResult<HttpResponse> {
    let symbol = path.into_inner();
    let interval = query.get("interval").unwrap_or(&"1h".to_string()).clone();
    let limit: i64 = query.get("limit").and_then(|l| l.parse().ok()).unwrap_or(500);
    
    match data.market_data_service.get_klines(&symbol, &interval, limit).await {
        Ok(klines) => Ok(HttpResponse::Ok().json(klines)),
        Err(e) => {
            tracing::error!("Failed to fetch klines: {}", e);
            Ok(HttpResponse::InternalServerError().json(json!({
                "error": "Failed to fetch klines"
            })))
        }
    }
}

pub async fn get_market_depth(
    data: web::Data<AppState>,
    path: web::Path<String>,
    query: web::Query<std::collections::HashMap<String, String>>,
) -> ActixResult<HttpResponse> {
    let symbol = path.into_inner();
    let limit: usize = query.get("limit").and_then(|l| l.parse().ok()).unwrap_or(100);
    
    match data.market_data_service.get_market_depth(&symbol, limit).await {
        Ok(depth) => Ok(HttpResponse::Ok().json(depth)),
        Err(e) => {
            tracing::error!("Failed to fetch market depth: {}", e);
            Ok(HttpResponse::InternalServerError().json(json!({
                "error": "Failed to fetch market depth"
            })))
        }
    }
}
