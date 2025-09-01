//! TigerEx Spot Trading Service
//! High-performance spot trading engine with real-time order processing

use actix_web::{web, App, HttpServer, middleware::Logger, Result as ActixResult};
use actix_cors::Cors;
use sqlx::{PgPool, Row};
use redis::aio::ConnectionManager;
use std::sync::Arc;
use tracing::{info, error};
use serde::{Deserialize, Serialize};
use uuid::Uuid;
use chrono::{DateTime, Utc};
use rust_decimal::Decimal;
use std::collections::HashMap;

mod models;
mod handlers;
mod services;
mod websocket;

use models::*;
use handlers::*;
use services::*;

#[derive(Clone)]
pub struct AppState {
    pub db: PgPool,
    pub redis: ConnectionManager,
    pub trading_service: Arc<TradingService>,
    pub market_data_service: Arc<MarketDataService>,
    pub order_service: Arc<OrderService>,
}

#[actix_web::main]
async fn main() -> std::io::Result<()> {
    // Initialize tracing
    tracing_subscriber::fmt::init();
    
    // Load environment variables
    dotenv::dotenv().ok();
    
    let database_url = std::env::var("DATABASE_URL")
        .expect("DATABASE_URL must be set");
    let redis_url = std::env::var("REDIS_URL")
        .expect("REDIS_URL must be set");
    
    // Initialize database connection
    let db = PgPool::connect(&database_url)
        .await
        .expect("Failed to connect to database");
    
    // Run migrations
    sqlx::migrate!("./migrations")
        .run(&db)
        .await
        .expect("Failed to run migrations");
    
    // Initialize Redis connection
    let redis_client = redis::Client::open(redis_url)
        .expect("Failed to create Redis client");
    let redis = ConnectionManager::new(redis_client)
        .await
        .expect("Failed to connect to Redis");
    
    // Initialize services
    let trading_service = Arc::new(TradingService::new(db.clone(), redis.clone()));
    let market_data_service = Arc::new(MarketDataService::new(db.clone(), redis.clone()));
    let order_service = Arc::new(OrderService::new(db.clone(), redis.clone()));
    
    // Create app state
    let app_state = AppState {
        db: db.clone(),
        redis: redis.clone(),
        trading_service: trading_service.clone(),
        market_data_service: market_data_service.clone(),
        order_service: order_service.clone(),
    };
    
    info!("Starting TigerEx Spot Trading Service on port 8091");
    
    // Start HTTP server
    HttpServer::new(move || {
        App::new()
            .app_data(web::Data::new(app_state.clone()))
            .wrap(Logger::default())
            .wrap(
                Cors::default()
                    .allow_any_origin()
                    .allow_any_method()
                    .allow_any_header()
            )
            .service(
                web::scope("/api/v1")
                    .service(
                        web::scope("/spot")
                            .route("/health", web::get().to(health_check))
                            .route("/pairs", web::get().to(get_trading_pairs))
                            .route("/pairs", web::post().to(create_trading_pair))
                            .route("/pairs/{symbol}", web::put().to(update_trading_pair))
                            .route("/pairs/{symbol}", web::delete().to(delete_trading_pair))
                            .route("/orders", web::post().to(place_order))
                            .route("/orders", web::get().to(get_orders))
                            .route("/orders/{order_id}", web::get().to(get_order))
                            .route("/orders/{order_id}", web::delete().to(cancel_order))
                            .route("/trades", web::get().to(get_trades))
                            .route("/orderbook/{symbol}", web::get().to(get_orderbook))
                            .route("/ticker/{symbol}", web::get().to(get_ticker))
                            .route("/tickers", web::get().to(get_all_tickers))
                            .route("/klines/{symbol}", web::get().to(get_klines))
                            .route("/depth/{symbol}", web::get().to(get_market_depth))
                    )
            )
            .route("/ws/spot", web::get().to(websocket_handler))
    })
    .bind("0.0.0.0:8091")?
    .run()
    .await
}

// Health check endpoint
async fn health_check() -> ActixResult<web::Json<serde_json::Value>> {
    Ok(web::Json(serde_json::json!({
        "status": "healthy",
        "service": "spot-trading",
        "timestamp": Utc::now(),
        "version": "1.0.0"
    })))
}

// WebSocket handler
async fn websocket_handler(
    req: actix_web::HttpRequest,
    stream: web::Payload,
    data: web::Data<AppState>,
) -> ActixResult<actix_web::HttpResponse> {
    websocket::ws_handler(req, stream, data).await
}
