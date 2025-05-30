#!/usr/bin/env python3
"""
TigerEx Risk Management Service

Advanced risk management system with features inspired by major exchanges:
- Real-time position monitoring
- Dynamic risk limits
- Liquidation engine
- Market risk assessment
- Credit risk management
- Operational risk controls
- Compliance monitoring
"""

import asyncio
import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from decimal import Decimal
import aioredis
import asyncpg
from kafka import KafkaProducer, KafkaConsumer
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import websockets
import aiohttp
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

@dataclass
class RiskLimits:
    """Risk limits for users/accounts"""
    user_id: int
    max_position_size: Decimal
    max_daily_loss: Decimal
    max_leverage: float
    max_open_orders: int
    max_daily_volume: Decimal
    margin_call_threshold: float
    liquidation_threshold: float
    withdrawal_limit_24h: Decimal
    api_rate_limit: int
    max_symbols_per_user: int
    vip_level: int
    is_institutional: bool
    created_at: datetime
    updated_at: datetime

@dataclass
class Position:
    """Trading position"""
    user_id: int
    symbol: str
    side: str  # LONG, SHORT
    size: Decimal
    entry_price: Decimal
    mark_price: Decimal
    unrealized_pnl: Decimal
    margin_used: Decimal
    leverage: float
    liquidation_price: Decimal
    maintenance_margin: Decimal
    created_at: datetime
    updated_at: datetime

@dataclass
class RiskEvent:
    """Risk event for monitoring"""
    event_id: str
    user_id: int
    event_type: str
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    description: str
    data: Dict
    timestamp: datetime
    resolved: bool = False

@dataclass
class MarketData:
    """Market data for risk calculations"""
    symbol: str
    price: Decimal
    volume_24h: Decimal
    volatility: float
    bid: Decimal
    ask: Decimal
    timestamp: datetime

class RiskEngine:
    """Core risk management engine"""
    
    def __init__(self):
        self.redis_client = None
        self.db_pool = None
        self.kafka_producer = None
        self.risk_limits: Dict[int, RiskLimits] = {}
        self.positions: Dict[Tuple[int, str], Position] = {}
        self.market_data: Dict[str, MarketData] = {}
        self.anomaly_detector = IsolationForest(contamination=0.1)
        self.scaler = StandardScaler()
        self.is_trained = False
        
    async def initialize(self):
        """Initialize connections and load data"""
        try:
            # Redis connection
            self.redis_client = await aioredis.from_url("redis://localhost:6379")
            
            # PostgreSQL connection
            self.db_pool = await asyncpg.create_pool(
                "postgresql://postgres:password@localhost/tigerex",
                min_size=10,
                max_size=20
            )
            
            # Kafka producer
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=['localhost:9092'],
                value_serializer=lambda x: json.dumps(x, default=str).encode('utf-8')
            )
            
            # Load risk limits and positions
            await self.load_risk_limits()
            await self.load_positions()
            
            # Start background tasks
            asyncio.create_task(self.monitor_positions())
            asyncio.create_task(self.monitor_market_risk())
            asyncio.create_task(self.train_anomaly_detector())
            
            logger.info("Risk engine initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize risk engine", error=str(e))
            raise

    async def load_risk_limits(self):
        """Load risk limits from database"""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT user_id, max_position_size, max_daily_loss, max_leverage,
                       max_open_orders, max_daily_volume, margin_call_threshold,
                       liquidation_threshold, withdrawal_limit_24h, api_rate_limit,
                       max_symbols_per_user, vip_level, is_institutional,
                       created_at, updated_at
                FROM risk_limits
            """)
            
            for row in rows:
                limits = RiskLimits(**dict(row))
                self.risk_limits[limits.user_id] = limits

    async def load_positions(self):
        """Load active positions from database"""
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT user_id, symbol, side, size, entry_price, mark_price,
                       unrealized_pnl, margin_used, leverage, liquidation_price,
                       maintenance_margin, created_at, updated_at
                FROM positions
                WHERE size > 0
            """)
            
            for row in rows:
                position = Position(**dict(row))
                self.positions[(position.user_id, position.symbol)] = position

    async def validate_order(self, user_id: int, symbol: str, side: str, 
                           quantity: Decimal, price: Decimal, order_type: str) -> Tuple[bool, str]:
        """Validate order against risk limits"""
        try:
            # Get user risk limits
            limits = self.risk_limits.get(user_id)
            if not limits:
                return False, "No risk limits found for user"
            
            # Check position size limits
            current_position = self.positions.get((user_id, symbol))
            new_position_size = quantity
            if current_position:
                if side == current_position.side:
                    new_position_size = current_position.size + quantity
                else:
                    new_position_size = abs(current_position.size - quantity)
            
            if new_position_size > limits.max_position_size:
                return False, f"Position size exceeds limit: {limits.max_position_size}"
            
            # Check daily volume limits
            daily_volume = await self.get_user_daily_volume(user_id)
            order_value = quantity * price
            if daily_volume + order_value > limits.max_daily_volume:
                return False, f"Daily volume limit exceeded: {limits.max_daily_volume}"
            
            # Check open orders limit
            open_orders_count = await self.get_user_open_orders_count(user_id)
            if open_orders_count >= limits.max_open_orders:
                return False, f"Maximum open orders exceeded: {limits.max_open_orders}"
            
            # Check leverage limits for margin/futures orders
            if order_type in ['MARGIN', 'FUTURES']:
                if await self.calculate_leverage(user_id, symbol, quantity, price) > limits.max_leverage:
                    return False, f"Leverage exceeds limit: {limits.max_leverage}"
            
            # Check market conditions
            market_data = self.market_data.get(symbol)
            if market_data:
                # Check for extreme volatility
                if market_data.volatility > 0.5:  # 50% volatility threshold
                    return False, "Market volatility too high"
                
                # Check for price deviation
                if abs(price - market_data.price) / market_data.price > 0.1:  # 10% deviation
                    return False, "Order price deviates significantly from market price"
            
            # Anomaly detection
            if await self.detect_anomaly(user_id, symbol, quantity, price):
                await self.create_risk_event(
                    user_id, "ANOMALY_DETECTED", "HIGH",
                    f"Anomalous trading pattern detected for order {symbol} {side} {quantity}"
                )
                return False, "Anomalous trading pattern detected"
            
            return True, "Order validated successfully"
            
        except Exception as e:
            logger.error("Order validation failed", user_id=user_id, error=str(e))
            return False, f"Validation error: {str(e)}"

    async def monitor_positions(self):
        """Monitor positions for margin calls and liquidations"""
        while True:
            try:
                for (user_id, symbol), position in self.positions.items():
                    limits = self.risk_limits.get(user_id)
                    if not limits:
                        continue
                    
                    # Update mark price
                    market_data = self.market_data.get(symbol)
                    if market_data:
                        position.mark_price = market_data.price
                        position.unrealized_pnl = self.calculate_unrealized_pnl(position)
                    
                    # Calculate margin ratio
                    margin_ratio = self.calculate_margin_ratio(position)
                    
                    # Check for margin call
                    if margin_ratio <= limits.margin_call_threshold:
                        await self.trigger_margin_call(user_id, symbol, position)
                    
                    # Check for liquidation
                    if margin_ratio <= limits.liquidation_threshold:
                        await self.trigger_liquidation(user_id, symbol, position)
                    
                    # Update position in database
                    await self.update_position(position)
                
                await asyncio.sleep(1)  # Check every second
                
            except Exception as e:
                logger.error("Position monitoring error", error=str(e))
                await asyncio.sleep(5)

    async def monitor_market_risk(self):
        """Monitor market-wide risk factors"""
        while True:
            try:
                # Calculate portfolio-wide metrics
                total_exposure = await self.calculate_total_exposure()
                concentration_risk = await self.calculate_concentration_risk()
                correlation_risk = await self.calculate_correlation_risk()
                
                # Check for system-wide risk thresholds
                if total_exposure > Decimal('10000000'):  # $10M threshold
                    await self.create_risk_event(
                        0, "HIGH_EXPOSURE", "HIGH",
                        f"Total system exposure: ${total_exposure}"
                    )
                
                if concentration_risk > 0.3:  # 30% concentration in single asset
                    await self.create_risk_event(
                        0, "CONCENTRATION_RISK", "MEDIUM",
                        f"High concentration risk: {concentration_risk:.2%}"
                    )
                
                # Monitor funding rates and liquidation cascades
                await self.monitor_funding_rates()
                await self.detect_liquidation_cascades()
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error("Market risk monitoring error", error=str(e))
                await asyncio.sleep(60)

    async def train_anomaly_detector(self):
        """Train ML model for anomaly detection"""
        while True:
            try:
                # Get historical trading data
                features = await self.get_trading_features()
                if len(features) > 1000:  # Need sufficient data
                    # Normalize features
                    features_scaled = self.scaler.fit_transform(features)
                    
                    # Train anomaly detector
                    self.anomaly_detector.fit(features_scaled)
                    self.is_trained = True
                    
                    logger.info("Anomaly detector retrained", samples=len(features))
                
                await asyncio.sleep(3600)  # Retrain every hour
                
            except Exception as e:
                logger.error("Anomaly detector training error", error=str(e))
                await asyncio.sleep(1800)

    async def detect_anomaly(self, user_id: int, symbol: str, 
                           quantity: Decimal, price: Decimal) -> bool:
        """Detect anomalous trading patterns"""
        if not self.is_trained:
            return False
        
        try:
            # Get user trading history
            user_features = await self.get_user_features(user_id, symbol)
            
            # Current order features
            current_features = [
                float(quantity),
                float(price),
                time.time() % 86400,  # Time of day
                len(await self.get_user_recent_orders(user_id)),
                float(await self.get_user_daily_volume(user_id))
            ]
            
            # Combine with historical features
            features = np.array([user_features + current_features])
            features_scaled = self.scaler.transform(features)
            
            # Predict anomaly
            anomaly_score = self.anomaly_detector.decision_function(features_scaled)[0]
            is_anomaly = self.anomaly_detector.predict(features_scaled)[0] == -1
            
            if is_anomaly:
                logger.warning("Anomaly detected", 
                             user_id=user_id, symbol=symbol, 
                             score=anomaly_score)
            
            return is_anomaly
            
        except Exception as e:
            logger.error("Anomaly detection error", error=str(e))
            return False

    async def trigger_margin_call(self, user_id: int, symbol: str, position: Position):
        """Trigger margin call for position"""
        try:
            await self.create_risk_event(
                user_id, "MARGIN_CALL", "HIGH",
                f"Margin call triggered for {symbol} position"
            )
            
            # Send notification to user
            await self.send_notification(user_id, "MARGIN_CALL", {
                "symbol": symbol,
                "position_size": str(position.size),
                "margin_ratio": self.calculate_margin_ratio(position),
                "required_margin": str(position.maintenance_margin)
            })
            
            # Publish to Kafka
            self.kafka_producer.send('margin_calls', {
                "user_id": user_id,
                "symbol": symbol,
                "position": asdict(position),
                "timestamp": datetime.utcnow().isoformat()
            })
            
            logger.warning("Margin call triggered", 
                         user_id=user_id, symbol=symbol)
            
        except Exception as e:
            logger.error("Margin call trigger error", error=str(e))

    async def trigger_liquidation(self, user_id: int, symbol: str, position: Position):
        """Trigger position liquidation"""
        try:
            await self.create_risk_event(
                user_id, "LIQUIDATION", "CRITICAL",
                f"Position liquidation triggered for {symbol}"
            )
            
            # Calculate liquidation details
            liquidation_price = position.liquidation_price
            liquidation_size = position.size
            
            # Send liquidation order to matching engine
            liquidation_order = {
                "user_id": user_id,
                "symbol": symbol,
                "side": "SELL" if position.side == "LONG" else "BUY",
                "type": "MARKET",
                "quantity": str(liquidation_size),
                "is_liquidation": True,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Publish to Kafka
            self.kafka_producer.send('liquidations', liquidation_order)
            
            # Update position status
            position.size = Decimal('0')
            await self.update_position(position)
            
            # Remove from active positions
            del self.positions[(user_id, symbol)]
            
            logger.critical("Position liquidated", 
                          user_id=user_id, symbol=symbol, 
                          size=str(liquidation_size))
            
        except Exception as e:
            logger.error("Liquidation trigger error", error=str(e))

    async def calculate_var(self, user_id: int, confidence_level: float = 0.95) -> Decimal:
        """Calculate Value at Risk for user portfolio"""
        try:
            user_positions = [pos for (uid, _), pos in self.positions.items() if uid == user_id]
            if not user_positions:
                return Decimal('0')
            
            # Get historical price data
            portfolio_values = []
            for i in range(252):  # 1 year of daily data
                portfolio_value = Decimal('0')
                for position in user_positions:
                    # Simulate price changes (simplified)
                    price_change = np.random.normal(0, 0.02)  # 2% daily volatility
                    simulated_price = position.mark_price * (1 + Decimal(str(price_change)))
                    position_value = position.size * simulated_price
                    portfolio_value += position_value
                
                portfolio_values.append(float(portfolio_value))
            
            # Calculate VaR
            var_percentile = (1 - confidence_level) * 100
            var = np.percentile(portfolio_values, var_percentile)
            
            return Decimal(str(var))
            
        except Exception as e:
            logger.error("VaR calculation error", error=str(e))
            return Decimal('0')

    async def calculate_total_exposure(self) -> Decimal:
        """Calculate total system exposure"""
        total = Decimal('0')
        for position in self.positions.values():
            total += position.size * position.mark_price
        return total

    async def calculate_concentration_risk(self) -> float:
        """Calculate concentration risk by asset"""
        if not self.positions:
            return 0.0
        
        symbol_exposure = {}
        total_exposure = Decimal('0')
        
        for position in self.positions.values():
            exposure = position.size * position.mark_price
            symbol_exposure[position.symbol] = symbol_exposure.get(position.symbol, Decimal('0')) + exposure
            total_exposure += exposure
        
        if total_exposure == 0:
            return 0.0
        
        max_concentration = max(symbol_exposure.values()) / total_exposure
        return float(max_concentration)

    async def calculate_correlation_risk(self) -> float:
        """Calculate portfolio correlation risk"""
        # Simplified correlation calculation
        # In production, use actual correlation matrices
        symbols = list(set(pos.symbol for pos in self.positions.values()))
        if len(symbols) < 2:
            return 0.0
        
        # Assume high correlation for crypto assets
        return 0.8  # 80% correlation

    def calculate_unrealized_pnl(self, position: Position) -> Decimal:
        """Calculate unrealized PnL for position"""
        if position.side == "LONG":
            return (position.mark_price - position.entry_price) * position.size
        else:
            return (position.entry_price - position.mark_price) * position.size

    def calculate_margin_ratio(self, position: Position) -> float:
        """Calculate margin ratio for position"""
        if position.margin_used == 0:
            return float('inf')
        
        equity = position.margin_used + position.unrealized_pnl
        return float(equity / position.margin_used)

    async def calculate_leverage(self, user_id: int, symbol: str, 
                               quantity: Decimal, price: Decimal) -> float:
        """Calculate effective leverage"""
        # Get user balance
        balance = await self.get_user_balance(user_id)
        if balance == 0:
            return float('inf')
        
        position_value = quantity * price
        return float(position_value / balance)

    # Database operations
    async def update_position(self, position: Position):
        """Update position in database"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE positions 
                SET mark_price = $1, unrealized_pnl = $2, updated_at = $3
                WHERE user_id = $4 AND symbol = $5
            """, position.mark_price, position.unrealized_pnl, 
                datetime.utcnow(), position.user_id, position.symbol)

    async def create_risk_event(self, user_id: int, event_type: str, 
                              severity: str, description: str, data: Dict = None):
        """Create risk event record"""
        event_id = f"{user_id}_{event_type}_{int(time.time())}"
        event = RiskEvent(
            event_id=event_id,
            user_id=user_id,
            event_type=event_type,
            severity=severity,
            description=description,
            data=data or {},
            timestamp=datetime.utcnow()
        )
        
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO risk_events 
                (event_id, user_id, event_type, severity, description, data, timestamp)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, event.event_id, event.user_id, event.event_type, 
                event.severity, event.description, json.dumps(event.data), 
                event.timestamp)

    # Utility methods
    async def get_user_daily_volume(self, user_id: int) -> Decimal:
        """Get user's daily trading volume"""
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchval("""
                SELECT COALESCE(SUM(quantity * price), 0)
                FROM orders 
                WHERE user_id = $1 AND created_at >= $2 AND status = 'FILLED'
            """, user_id, datetime.utcnow() - timedelta(days=1))
            return Decimal(str(result or 0))

    async def get_user_open_orders_count(self, user_id: int) -> int:
        """Get count of user's open orders"""
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchval("""
                SELECT COUNT(*) FROM orders 
                WHERE user_id = $1 AND status IN ('NEW', 'PARTIALLY_FILLED')
            """, user_id)
            return result or 0

    async def get_user_balance(self, user_id: int) -> Decimal:
        """Get user's total balance"""
        async with self.db_pool.acquire() as conn:
            result = await conn.fetchval("""
                SELECT COALESCE(SUM(available + locked), 0)
                FROM balances WHERE user_id = $1
            """, user_id)
            return Decimal(str(result or 0))

    async def send_notification(self, user_id: int, notification_type: str, data: Dict):
        """Send notification to user"""
        notification = {
            "user_id": user_id,
            "type": notification_type,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Publish to notification service
        self.kafka_producer.send('notifications', notification)

# FastAPI application
app = FastAPI(title="TigerEx Risk Management Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global risk engine instance
risk_engine = RiskEngine()

@app.on_event("startup")
async def startup_event():
    await risk_engine.initialize()

# API Models
class OrderValidationRequest(BaseModel):
    user_id: int
    symbol: str
    side: str
    quantity: str
    price: str
    order_type: str

class OrderValidationResponse(BaseModel):
    is_valid: bool
    message: str

# API Endpoints
@app.post("/validate-order", response_model=OrderValidationResponse)
async def validate_order(request: OrderValidationRequest):
    """Validate order against risk limits"""
    is_valid, message = await risk_engine.validate_order(
        request.user_id,
        request.symbol,
        request.side,
        Decimal(request.quantity),
        Decimal(request.price),
        request.order_type
    )
    
    return OrderValidationResponse(is_valid=is_valid, message=message)

@app.get("/risk-limits/{user_id}")
async def get_risk_limits(user_id: int):
    """Get risk limits for user"""
    limits = risk_engine.risk_limits.get(user_id)
    if not limits:
        raise HTTPException(status_code=404, detail="Risk limits not found")
    
    return asdict(limits)

@app.get("/positions/{user_id}")
async def get_user_positions(user_id: int):
    """Get user positions"""
    positions = [
        asdict(pos) for (uid, _), pos in risk_engine.positions.items() 
        if uid == user_id
    ]
    return positions

@app.get("/var/{user_id}")
async def get_user_var(user_id: int, confidence_level: float = 0.95):
    """Get Value at Risk for user"""
    var = await risk_engine.calculate_var(user_id, confidence_level)
    return {"user_id": user_id, "var": str(var), "confidence_level": confidence_level}

@app.get("/system/exposure")
async def get_system_exposure():
    """Get system-wide exposure metrics"""
    total_exposure = await risk_engine.calculate_total_exposure()
    concentration_risk = await risk_engine.calculate_concentration_risk()
    correlation_risk = await risk_engine.calculate_correlation_risk()
    
    return {
        "total_exposure": str(total_exposure),
        "concentration_risk": concentration_risk,
        "correlation_risk": correlation_risk,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "active_positions": len(risk_engine.positions),
        "monitored_users": len(risk_engine.risk_limits)
    }

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8082,
        reload=True,
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "level": "INFO",
                "handlers": ["default"],
            },
        }
    )