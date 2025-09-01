"""
TigerEx Copy Trading System
Social trading platform with performance tracking and automated copying
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
from enum import Enum
import secrets

import aioredis
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, DECIMAL, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
import numpy as np
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="TigerEx Copy Trading System",
    description="Social trading platform with performance tracking and automated copying",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
class Config:
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost/tigerex")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    MAX_COPY_AMOUNT = Decimal("100000")
    MIN_COPY_AMOUNT = Decimal("10")
    PERFORMANCE_FEE_PERCENTAGE = Decimal("20")

config = Config()

# Database setup
engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

security = HTTPBearer()

# Enums
class TraderStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    VERIFIED = "verified"

class CopyStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    STOPPED = "stopped"

class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"

class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"

class OrderStatus(str, Enum):
    PENDING = "pending"
    FILLED = "filled"
    CANCELLED = "cancelled"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    EXTREME = "extreme"

# Database Models
class Trader(Base):
    __tablename__ = "traders"
    
    id = Column(Integer, primary_key=True, index=True)
    trader_id = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    
    display_name = Column(String(100), nullable=False)
    bio = Column(Text)
    avatar_url = Column(String(500))
    
    trading_since = Column(DateTime, nullable=False)
    total_trades = Column(Integer, default=0)
    winning_trades = Column(Integer, default=0)
    losing_trades = Column(Integer, default=0)
    
    total_return = Column(DECIMAL(10, 4), default=0)
    monthly_return = Column(DECIMAL(10, 4), default=0)
    weekly_return = Column(DECIMAL(10, 4), default=0)
    daily_return = Column(DECIMAL(10, 4), default=0)
    
    max_drawdown = Column(DECIMAL(10, 4), default=0)
    sharpe_ratio = Column(DECIMAL(10, 4), default=0)
    volatility = Column(DECIMAL(10, 4), default=0)
    risk_score = Column(DECIMAL(5, 2), default=0)
    risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.MEDIUM)
    
    followers_count = Column(Integer, default=0)
    total_copied_volume = Column(DECIMAL(20, 2), default=0)
    
    is_public = Column(Boolean, default=True)
    allow_copying = Column(Boolean, default=True)
    min_copy_amount = Column(DECIMAL(20, 2), default=config.MIN_COPY_AMOUNT)
    max_copy_amount = Column(DECIMAL(20, 2), default=config.MAX_COPY_AMOUNT)
    performance_fee = Column(DECIMAL(5, 2), default=config.PERFORMANCE_FEE_PERCENTAGE)
    
    is_verified = Column(Boolean, default=False)
    status = Column(SQLEnum(TraderStatus), default=TraderStatus.ACTIVE)
    created_at = Column(DateTime, default=func.now())
    
    trades = relationship("Trade", back_populates="trader")
    followers = relationship("CopyRelationship", foreign_keys="CopyRelationship.trader_id", back_populates="trader")

class CopyRelationship(Base):
    __tablename__ = "copy_relationships"
    
    id = Column(Integer, primary_key=True, index=True)
    relationship_id = Column(String(50), unique=True, nullable=False, index=True)
    
    follower_id = Column(String(50), nullable=False, index=True)
    trader_id = Column(Integer, ForeignKey("traders.id"), nullable=False)
    trader = relationship("Trader", foreign_keys=[trader_id], back_populates="followers")
    
    copy_amount = Column(DECIMAL(20, 2), nullable=False)
    copy_percentage = Column(DECIMAL(5, 2))
    max_open_positions = Column(Integer, default=10)
    
    stop_loss_percentage = Column(DECIMAL(5, 2))
    take_profit_percentage = Column(DECIMAL(5, 2))
    max_daily_loss = Column(DECIMAL(20, 2))
    
    copy_symbols = Column(JSON)
    exclude_symbols = Column(JSON)
    min_trade_amount = Column(DECIMAL(20, 2))
    max_trade_amount = Column(DECIMAL(20, 2))
    
    total_copied_trades = Column(Integer, default=0)
    total_profit_loss = Column(DECIMAL(20, 2), default=0)
    total_fees_paid = Column(DECIMAL(20, 2), default=0)
    
    status = Column(SQLEnum(CopyStatus), default=CopyStatus.ACTIVE)
    started_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())

class Trade(Base):
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(String(50), unique=True, nullable=False, index=True)
    
    trader_id = Column(Integer, ForeignKey("traders.id"), nullable=False)
    trader = relationship("Trader", back_populates="trades")
    
    symbol = Column(String(20), nullable=False, index=True)
    side = Column(SQLEnum(OrderSide), nullable=False)
    order_type = Column(SQLEnum(OrderType), nullable=False)
    
    quantity = Column(DECIMAL(30, 8), nullable=False)
    price = Column(DECIMAL(20, 8))
    filled_quantity = Column(DECIMAL(30, 8), default=0)
    average_price = Column(DECIMAL(20, 8))
    
    realized_pnl = Column(DECIMAL(20, 2), default=0)
    commission = Column(DECIMAL(20, 8), default=0)
    
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.PENDING)
    opened_at = Column(DateTime, default=func.now())
    closed_at = Column(DateTime)
    
    external_order_id = Column(String(100))
    created_at = Column(DateTime, default=func.now())

class SocialPost(Base):
    __tablename__ = "social_posts"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(String(50), unique=True, nullable=False, index=True)
    
    trader_id = Column(Integer, ForeignKey("traders.id"), nullable=False)
    
    content = Column(Text, nullable=False)
    image_urls = Column(JSON)
    
    likes_count = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    
    is_published = Column(Boolean, default=True)
    is_pinned = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=func.now())

# Pydantic Models
class TraderCreate(BaseModel):
    display_name: str
    bio: Optional[str] = None
    is_public: bool = True
    allow_copying: bool = True
    min_copy_amount: Decimal = config.MIN_COPY_AMOUNT
    max_copy_amount: Decimal = config.MAX_COPY_AMOUNT
    performance_fee: Decimal = config.PERFORMANCE_FEE_PERCENTAGE
    
    @validator('performance_fee')
    def validate_performance_fee(cls, v):
        if v < 0 or v > 50:
            raise ValueError('Performance fee must be between 0% and 50%')
        return v

class CopyRelationshipCreate(BaseModel):
    trader_id: str
    copy_amount: Decimal
    copy_percentage: Optional[Decimal] = None
    max_open_positions: int = 10
    stop_loss_percentage: Optional[Decimal] = None
    take_profit_percentage: Optional[Decimal] = None
    max_daily_loss: Optional[Decimal] = None
    copy_symbols: List[str] = []
    exclude_symbols: List[str] = []
    min_trade_amount: Optional[Decimal] = None
    max_trade_amount: Optional[Decimal] = None

class TradeCreate(BaseModel):
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: Decimal
    price: Optional[Decimal] = None

class SocialPostCreate(BaseModel):
    content: str
    image_urls: List[str] = []
    is_pinned: bool = False
    
    @validator('content')
    def validate_content(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('Content must be at least 10 characters')
        return v

# Dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return {"user_id": "user_123", "username": "testuser"}

# Copy Trading Manager
class CopyTradingManager:
    def __init__(self):
        self.redis_client = None
        self.active_connections: Dict[str, WebSocket] = {}
        
    async def initialize(self):
        self.redis_client = await aioredis.from_url(config.REDIS_URL)
    
    async def create_trader_profile(self, trader_data: TraderCreate, user: Dict[str, Any], db: Session):
        existing_trader = db.query(Trader).filter(Trader.user_id == user["user_id"]).first()
        if existing_trader:
            raise HTTPException(status_code=400, detail="User already has a trader profile")
        
        trader_id = f"TRADER_{secrets.token_hex(8).upper()}"
        
        trader = Trader(
            trader_id=trader_id,
            user_id=user["user_id"],
            display_name=trader_data.display_name,
            bio=trader_data.bio,
            trading_since=datetime.now(),
            is_public=trader_data.is_public,
            allow_copying=trader_data.allow_copying,
            min_copy_amount=trader_data.min_copy_amount,
            max_copy_amount=trader_data.max_copy_amount,
            performance_fee=trader_data.performance_fee
        )
        
        db.add(trader)
        db.commit()
        db.refresh(trader)
        return trader
    
    async def create_copy_relationship(self, copy_data: CopyRelationshipCreate, follower: Dict[str, Any], db: Session):
        trader = db.query(Trader).filter(
            Trader.trader_id == copy_data.trader_id,
            Trader.allow_copying == True,
            Trader.status == TraderStatus.ACTIVE
        ).first()
        
        if not trader:
            raise HTTPException(status_code=404, detail="Trader not found or not available for copying")
        
        if trader.user_id == follower["user_id"]:
            raise HTTPException(status_code=400, detail="Cannot copy your own trades")
        
        relationship_id = f"COPY_{secrets.token_hex(8).upper()}"
        
        relationship = CopyRelationship(
            relationship_id=relationship_id,
            follower_id=follower["user_id"],
            trader_id=trader.id,
            copy_amount=copy_data.copy_amount,
            copy_percentage=copy_data.copy_percentage,
            max_open_positions=copy_data.max_open_positions,
            stop_loss_percentage=copy_data.stop_loss_percentage,
            take_profit_percentage=copy_data.take_profit_percentage,
            max_daily_loss=copy_data.max_daily_loss,
            copy_symbols=copy_data.copy_symbols,
            exclude_symbols=copy_data.exclude_symbols,
            min_trade_amount=copy_data.min_trade_amount,
            max_trade_amount=copy_data.max_trade_amount
        )
        
        db.add(relationship)
        trader.followers_count += 1
        db.commit()
        db.refresh(relationship)
        return relationship
    
    async def process_trade(self, trade_data: TradeCreate, trader: Trader, db: Session):
        trade_id = f"TRADE_{secrets.token_hex(8).upper()}"
        
        trade = Trade(
            trade_id=trade_id,
            trader_id=trader.id,
            symbol=trade_data.symbol,
            side=trade_data.side,
            order_type=trade_data.order_type,
            quantity=trade_data.quantity,
            price=trade_data.price
        )
        
        db.add(trade)
        db.commit()
        db.refresh(trade)
        
        # Mock execution
        trade.status = OrderStatus.FILLED
        trade.filled_quantity = trade.quantity
        trade.average_price = trade.price or Decimal("45000")
        trade.commission = trade.filled_quantity * trade.average_price * Decimal("0.001")
        
        trader.total_trades += 1
        db.commit()
        
        return trade

copy_trading_manager = CopyTradingManager()

@app.on_event("startup")
async def startup_event():
    await copy_trading_manager.initialize()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        self.active_connections[user_id] = websocket
    
    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
    
    async def send_personal_message(self, message: str, user_id: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_text(message)

manager = ConnectionManager()

# API Endpoints
@app.post("/api/v1/traders")
async def create_trader_profile(
    trader_data: TraderCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    trader = await copy_trading_manager.create_trader_profile(trader_data, current_user, db)
    return {
        "trader_id": trader.trader_id,
        "display_name": trader.display_name,
        "status": "created"
    }

@app.get("/api/v1/traders")
async def get_traders(
    sort_by: str = "total_return",
    sort_order: str = "desc",
    risk_level: Optional[str] = None,
    verified_only: bool = False,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(Trader).filter(
        Trader.is_public == True,
        Trader.allow_copying == True,
        Trader.status == TraderStatus.ACTIVE
    )
    
    if risk_level:
        query = query.filter(Trader.risk_level == risk_level)
    
    if verified_only:
        query = query.filter(Trader.is_verified == True)
    
    if sort_by in ['total_return', 'monthly_return', 'followers_count', 'sharpe_ratio']:
        if sort_order == "desc":
            query = query.order_by(getattr(Trader, sort_by).desc())
        else:
            query = query.order_by(getattr(Trader, sort_by).asc())
    
    traders = query.offset(offset).limit(limit).all()
    
    return {
        "traders": [
            {
                "trader_id": trader.trader_id,
                "display_name": trader.display_name,
                "bio": trader.bio,
                "avatar_url": trader.avatar_url,
                "trading_since": trader.trading_since.isoformat(),
                "total_return": str(trader.total_return),
                "monthly_return": str(trader.monthly_return),
                "risk_level": trader.risk_level,
                "followers_count": trader.followers_count,
                "total_trades": trader.total_trades,
                "winning_trades": trader.winning_trades,
                "losing_trades": trader.losing_trades,
                "win_rate": round(trader.winning_trades / trader.total_trades * 100, 2) if trader.total_trades > 0 else 0,
                "is_verified": trader.is_verified,
                "performance_fee": str(trader.performance_fee),
                "min_copy_amount": str(trader.min_copy_amount),
                "max_copy_amount": str(trader.max_copy_amount)
            }
            for trader in traders
        ]
    }

@app.post("/api/v1/copy")
async def create_copy_relationship(
    copy_data: CopyRelationshipCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    relationship = await copy_trading_manager.create_copy_relationship(copy_data, current_user, db)
    return {
        "relationship_id": relationship.relationship_id,
        "trader_id": copy_data.trader_id,
        "copy_amount": str(relationship.copy_amount),
        "status": "active"
    }

@app.get("/api/v1/copy/following")
async def get_following(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    relationships = db.query(CopyRelationship).join(Trader).filter(
        CopyRelationship.follower_id == current_user["user_id"],
        CopyRelationship.status == CopyStatus.ACTIVE
    ).all()
    
    return {
        "following": [
            {
                "relationship_id": rel.relationship_id,
                "trader": {
                    "trader_id": rel.trader.trader_id,
                    "display_name": rel.trader.display_name,
                    "avatar_url": rel.trader.avatar_url,
                    "total_return": str(rel.trader.total_return),
                    "risk_level": rel.trader.risk_level
                },
                "copy_amount": str(rel.copy_amount),
                "total_copied_trades": rel.total_copied_trades,
                "total_profit_loss": str(rel.total_profit_loss),
                "started_at": rel.started_at.isoformat(),
                "status": rel.status
            }
            for rel in relationships
        ]
    }

@app.post("/api/v1/trades")
async def create_trade(
    trade_data: TradeCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    trader = db.query(Trader).filter(
        Trader.user_id == current_user["user_id"],
        Trader.status == TraderStatus.ACTIVE
    ).first()
    
    if not trader:
        raise HTTPException(status_code=404, detail="Trader profile not found")
    
    trade = await copy_trading_manager.process_trade(trade_data, trader, db)
    
    return {
        "trade_id": trade.trade_id,
        "symbol": trade.symbol,
        "side": trade.side,
        "quantity": str(trade.quantity),
        "status": trade.status
    }

@app.get("/api/v1/traders/{trader_id}/performance")
async def get_trader_performance(
    trader_id: str,
    period: str = "30d",
    db: Session = Depends(get_db)
):
    trader = db.query(Trader).filter(Trader.trader_id == trader_id).first()
    
    if not trader:
        raise HTTPException(status_code=404, detail="Trader not found")
    
    return {
        "trader_id": trader_id,
        "period": period,
        "current_metrics": {
            "total_return": str(trader.total_return),
            "monthly_return": str(trader.monthly_return),
            "weekly_return": str(trader.weekly_return),
            "daily_return": str(trader.daily_return),
            "max_drawdown": str(trader.max_drawdown),
            "sharpe_ratio": str(trader.sharpe_ratio),
            "volatility": str(trader.volatility),
            "risk_score": str(trader.risk_score),
            "win_rate": round(trader.winning_trades / trader.total_trades * 100, 2) if trader.total_trades > 0 else 0
        },
        "historical_data": []
    }

@app.post("/api/v1/social/posts")
async def create_social_post(
    post_data: SocialPostCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    trader = db.query(Trader).filter(Trader.user_id == current_user["user_id"]).first()
    
    if not trader:
        raise HTTPException(status_code=404, detail="Trader profile not found")
    
    post_id = f"POST_{secrets.token_hex(8).upper()}"
    
    post = SocialPost(
        post_id=post_id,
        trader_id=trader.id,
        content=post_data.content,
        image_urls=post_data.image_urls,
        is_pinned=post_data.is_pinned
    )
    
    db.add(post)
    db.commit()
    
    return {
        "post_id": post.post_id,
        "content": post.content,
        "created_at": post.created_at.isoformat(),
        "status": "published"
    }

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_personal_message(f"Echo: {data}", user_id)
    except WebSocketDisconnect:
        manager.disconnect(user_id)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "copy-trading"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
