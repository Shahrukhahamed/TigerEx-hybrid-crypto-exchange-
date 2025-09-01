//! WebSocket handler for real-time spot trading data

use actix::prelude::*;
use actix_web::{web, HttpRequest, HttpResponse, Result as ActixResult};
use actix_web_actors::ws;
use serde_json::json;
use std::collections::HashSet;
use std::time::{Duration, Instant};
use crate::{AppState, models::*};

const HEARTBEAT_INTERVAL: Duration = Duration::from_secs(5);
const CLIENT_TIMEOUT: Duration = Duration::from_secs(10);

pub struct SpotTradingWebSocket {
    hb: Instant,
    subscriptions: HashSet<String>,
    app_state: web::Data<AppState>,
}

impl SpotTradingWebSocket {
    pub fn new(app_state: web::Data<AppState>) -> Self {
        Self {
            hb: Instant::now(),
            subscriptions: HashSet::new(),
            app_state,
        }
    }
    
    fn hb(&self, ctx: &mut <Self as Actor>::Context) {
        ctx.run_interval(HEARTBEAT_INTERVAL, |act, ctx| {
            if Instant::now().duration_since(act.hb) > CLIENT_TIMEOUT {
                tracing::warn!("WebSocket client heartbeat failed, disconnecting");
                ctx.stop();
                return;
            }
            
            ctx.ping(b"");
        });
    }
    
    fn handle_subscribe(&mut self, params: Vec<String>, ctx: &mut <Self as Actor>::Context) {
        for stream in params {
            if self.subscriptions.insert(stream.clone()) {
                tracing::info!("Client subscribed to stream: {}", stream);
                
                // Send confirmation
                let response = json!({
                    "result": null,
                    "id": 1
                });
                ctx.text(response.to_string());
                
                // Send initial data for the stream
                self.send_initial_data(&stream, ctx);
            }
        }
    }
    
    fn handle_unsubscribe(&mut self, params: Vec<String>, ctx: &mut <Self as Actor>::Context) {
        for stream in params {
            if self.subscriptions.remove(&stream) {
                tracing::info!("Client unsubscribed from stream: {}", stream);
            }
        }
        
        let response = json!({
            "result": null,
            "id": 1
        });
        ctx.text(response.to_string());
    }
    
    fn send_initial_data(&self, stream: &str, ctx: &mut <Self as Actor>::Context) {
        // Parse stream format: symbol@type (e.g., BTCUSDT@ticker, BTCUSDT@depth)
        let parts: Vec<&str> = stream.split('@').collect();
        if parts.len() != 2 {
            return;
        }
        
        let symbol = parts[0];
        let stream_type = parts[1];
        
        match stream_type {
            "ticker" => {
                // Send ticker data
                let ticker_data = json!({
                    "stream": stream,
                    "data": {
                        "s": symbol,
                        "c": "0.0023",
                        "o": "0.0024",
                        "h": "0.0025",
                        "l": "0.0022",
                        "v": "10000",
                        "q": "23.5"
                    }
                });
                ctx.text(ticker_data.to_string());
            },
            "depth" => {
                // Send order book depth
                let depth_data = json!({
                    "stream": stream,
                    "data": {
                        "s": symbol,
                        "b": [["0.0024", "10"], ["0.0023", "20"]],
                        "a": [["0.0025", "15"], ["0.0026", "25"]]
                    }
                });
                ctx.text(depth_data.to_string());
            },
            "trade" => {
                // Send recent trades
                let trade_data = json!({
                    "stream": stream,
                    "data": {
                        "s": symbol,
                        "t": 12345,
                        "p": "0.0024",
                        "q": "10",
                        "T": chrono::Utc::now().timestamp_millis(),
                        "m": true
                    }
                });
                ctx.text(trade_data.to_string());
            },
            _ => {}
        }
    }
}

impl Actor for SpotTradingWebSocket {
    type Context = ws::WebsocketContext<Self>;
    
    fn started(&mut self, ctx: &mut Self::Context) {
        self.hb(ctx);
        tracing::info!("WebSocket connection established");
    }
}

impl StreamHandler<Result<ws::Message, ws::ProtocolError>> for SpotTradingWebSocket {
    fn handle(&mut self, msg: Result<ws::Message, ws::ProtocolError>, ctx: &mut Self::Context) {
        match msg {
            Ok(ws::Message::Ping(msg)) => {
                self.hb = Instant::now();
                ctx.pong(&msg);
            },
            Ok(ws::Message::Pong(_)) => {
                self.hb = Instant::now();
            },
            Ok(ws::Message::Text(text)) => {
                self.hb = Instant::now();
                
                // Parse incoming message
                if let Ok(msg) = serde_json::from_str::<serde_json::Value>(&text) {
                    if let Some(method) = msg.get("method").and_then(|m| m.as_str()) {
                        match method {
                            "SUBSCRIBE" => {
                                if let Some(params) = msg.get("params").and_then(|p| p.as_array()) {
                                    let streams: Vec<String> = params.iter()
                                        .filter_map(|p| p.as_str().map(|s| s.to_string()))
                                        .collect();
                                    self.handle_subscribe(streams, ctx);
                                }
                            },
                            "UNSUBSCRIBE" => {
                                if let Some(params) = msg.get("params").and_then(|p| p.as_array()) {
                                    let streams: Vec<String> = params.iter()
                                        .filter_map(|p| p.as_str().map(|s| s.to_string()))
                                        .collect();
                                    self.handle_unsubscribe(streams, ctx);
                                }
                            },
                            _ => {
                                let error_response = json!({
                                    "error": {
                                        "code": -32601,
                                        "msg": "Method not found"
                                    },
                                    "id": msg.get("id")
                                });
                                ctx.text(error_response.to_string());
                            }
                        }
                    }
                }
            },
            Ok(ws::Message::Binary(_)) => {
                tracing::warn!("Binary messages not supported");
            },
            Ok(ws::Message::Close(reason)) => {
                tracing::info!("WebSocket connection closed: {:?}", reason);
                ctx.stop();
            },
            _ => ctx.stop(),
        }
    }
}

pub async fn ws_handler(
    req: HttpRequest,
    stream: web::Payload,
    data: web::Data<AppState>,
) -> ActixResult<HttpResponse> {
    let resp = ws::start(SpotTradingWebSocket::new(data), &req, stream);
    tracing::info!("WebSocket connection attempt");
    resp
}
