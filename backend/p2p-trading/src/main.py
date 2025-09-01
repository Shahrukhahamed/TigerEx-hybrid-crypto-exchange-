"""
TigerEx P2P Trading System
Comprehensive peer-to-peer trading platform with escrow, dispute resolution, and multi-country support
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
import hashlib

import aioredis
from fastapi import FastAPI, HTTPException, Depends, WebSocket, WebSocketDisconnect, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, DECIMAL, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="TigerEx P2P Trading System",
    description="Comprehensive peer-to-peer trading platform with escrow, dispute resolution, and multi-country support",
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
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "p2p-secret-key")
    
    # P2P Configuration
    ESCROW_TIMEOUT_HOURS = 24
    DISPUTE_TIMEOUT_HOURS = 72
    MIN_TRADE_AMOUNT = Decimal("10")
    MAX_TRADE_AMOUNT = Decimal("100000")
    P2P_FEE_PERCENTAGE = Decimal("0.5")  # 0.5%
    
    # Payment Providers
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
    PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
    PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")

config = Config()

# Database setup
engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

security = HTTPBearer()

# Enums
class OrderType(str, Enum):
    BUY = "buy"
    SELL = "sell"

class OrderStatus(str, Enum):
    ACTIVE = "active"
    MATCHED = "matched"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"

class TradeStatus(str, Enum):
    PENDING = "pending"
    PAYMENT_PENDING = "payment_pending"
    PAYMENT_CONFIRMED = "payment_confirmed"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    DISPUTED = "disputed"
    REFUNDED = "refunded"

class PaymentMethodType(str, Enum):
    BANK_TRANSFER = "bank_transfer"
    PAYPAL = "paypal"
    WISE = "wise"
    REVOLUT = "revolut"
    CASH_APP = "cash_app"
    VENMO = "venmo"
    ZELLE = "zelle"
    ALIPAY = "alipay"
    WECHAT_PAY = "wechat_pay"
    UPI = "upi"
    PIX = "pix"
    INTERAC = "interac"

class DisputeStatus(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    CLOSED = "closed"

class UserRole(str, Enum):
    USER = "user"
    P2P_ADMIN = "p2p_admin"
    SUPER_ADMIN = "super_admin"

# Database Models
class P2PUser(Base):
    __tablename__ = "p2p_users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Profile Information
    username = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    phone_number = Column(String(20))
    country_code = Column(String(3), nullable=False)  # ISO country code
    
    # P2P Statistics
    total_trades = Column(Integer, default=0)
    successful_trades = Column(Integer, default=0)
    total_volume = Column(DECIMAL(20, 2), default=0)
    average_rating = Column(DECIMAL(3, 2), default=0)
    total_ratings = Column(Integer, default=0)
    
    # Status
    is_verified = Column(Boolean, default=False)
    is_p2p_enabled = Column(Boolean, default=True)
    is_blocked = Column(Boolean, default=False)
    
    # Timestamps
    first_trade_at = Column(DateTime)
    last_active_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    orders = relationship("P2POrder", foreign_keys="P2POrder.user_id", back_populates="user")
    payment_methods = relationship("PaymentMethod", back_populates="user")
    sent_trades = relationship("P2PTrade", foreign_keys="P2PTrade.buyer_id", back_populates="buyer")
    received_trades = relationship("P2PTrade", foreign_keys="P2PTrade.seller_id", back_populates="seller")

class PaymentMethod(Base):
    __tablename__ = "payment_methods"
    
    id = Column(Integer, primary_key=True, index=True)
    method_id = Column(String(50), unique=True, nullable=False, index=True)
    
    user_id = Column(Integer, ForeignKey("p2p_users.id"), nullable=False)
    user = relationship("P2PUser", back_populates="payment_methods")
    
    # Method Details
    method_type = Column(SQLEnum(PaymentMethodType), nullable=False)
    method_name = Column(String(100), nullable=False)
    account_details = Column(JSON, nullable=False)  # Encrypted account details
    
    # Supported Currencies and Countries
    supported_currencies = Column(JSON)  # List of currency codes
    supported_countries = Column(JSON)   # List of country codes
    
    # Limits
    min_amount = Column(DECIMAL(20, 2))
    max_amount = Column(DECIMAL(20, 2))
    daily_limit = Column(DECIMAL(20, 2))
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=func.now())

class P2POrder(Base):
    __tablename__ = "p2p_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(50), unique=True, nullable=False, index=True)
    
    user_id = Column(Integer, ForeignKey("p2p_users.id"), nullable=False)
    user = relationship("P2PUser", foreign_keys=[user_id], back_populates="orders")
    
    # Order Details
    order_type = Column(SQLEnum(OrderType), nullable=False)
    cryptocurrency = Column(String(10), nullable=False)
    fiat_currency = Column(String(3), nullable=False)
    
    # Amounts
    crypto_amount = Column(DECIMAL(30, 8), nullable=False)
    price_per_unit = Column(DECIMAL(20, 8), nullable=False)
    total_fiat_amount = Column(DECIMAL(20, 2), nullable=False)
    min_trade_amount = Column(DECIMAL(20, 2))
    max_trade_amount = Column(DECIMAL(20, 2))
    
    # Payment Methods
    accepted_payment_methods = Column(JSON)  # List of payment method IDs
    
    # Terms and Conditions
    terms = Column(Text)
    auto_reply_message = Column(Text)
    
    # Geographic Restrictions
    allowed_countries = Column(JSON)  # List of country codes, empty = all countries
    blocked_countries = Column(JSON)  # List of blocked country codes
    
    # Status and Timing
    status = Column(SQLEnum(OrderStatus), default=OrderStatus.ACTIVE)
    expires_at = Column(DateTime)
    
    # Statistics
    completed_trades = Column(Integer, default=0)
    total_volume = Column(DECIMAL(20, 2), default=0)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    trades = relationship("P2PTrade", back_populates="order")

class P2PTrade(Base):
    __tablename__ = "p2p_trades"
    
    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Order Reference
    order_id = Column(Integer, ForeignKey("p2p_orders.id"), nullable=False)
    order = relationship("P2POrder", back_populates="trades")
    
    # Participants
    buyer_id = Column(Integer, ForeignKey("p2p_users.id"), nullable=False)
    seller_id = Column(Integer, ForeignKey("p2p_users.id"), nullable=False)
    buyer = relationship("P2PUser", foreign_keys=[buyer_id], back_populates="sent_trades")
    seller = relationship("P2PUser", foreign_keys=[seller_id], back_populates="received_trades")
    
    # Trade Details
    crypto_amount = Column(DECIMAL(30, 8), nullable=False)
    fiat_amount = Column(DECIMAL(20, 2), nullable=False)
    price_per_unit = Column(DECIMAL(20, 8), nullable=False)
    
    # Payment Information
    payment_method_id = Column(Integer, ForeignKey("payment_methods.id"), nullable=False)
    payment_reference = Column(String(100))
    
    # Status and Timing
    status = Column(SQLEnum(TradeStatus), default=TradeStatus.PENDING)
    payment_deadline = Column(DateTime, nullable=False)
    
    # Escrow Information
    escrow_address = Column(String(100))
    escrow_transaction_hash = Column(String(100))
    release_transaction_hash = Column(String(100))
    
    # Communication
    chat_room_id = Column(String(50), nullable=False)
    
    # Fees
    platform_fee = Column(DECIMAL(20, 8), default=0)
    
    created_at = Column(DateTime, default=func.now())
    completed_at = Column(DateTime)
    
    # Relationships
    messages = relationship("TradeMessage", back_populates="trade")
    dispute = relationship("TradeDispute", back_populates="trade", uselist=False)

class TradeMessage(Base):
    __tablename__ = "trade_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String(50), unique=True, nullable=False, index=True)
    
    trade_id = Column(Integer, ForeignKey("p2p_trades.id"), nullable=False)
    trade = relationship("P2PTrade", back_populates="messages")
    
    sender_id = Column(Integer, ForeignKey("p2p_users.id"), nullable=False)
    
    # Message Content
    message_type = Column(String(20), default="text")  # text, image, file, system
    content = Column(Text, nullable=False)
    file_url = Column(String(500))
    
    # Status
    is_read = Column(Boolean, default=False)
    is_system_message = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=func.now())

class TradeDispute(Base):
    __tablename__ = "trade_disputes"
    
    id = Column(Integer, primary_key=True, index=True)
    dispute_id = Column(String(50), unique=True, nullable=False, index=True)
    
    trade_id = Column(Integer, ForeignKey("p2p_trades.id"), nullable=False)
    trade = relationship("P2PTrade", back_populates="dispute")
    
    # Dispute Details
    initiated_by = Column(Integer, ForeignKey("p2p_users.id"), nullable=False)
    dispute_reason = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    evidence_urls = Column(JSON)  # List of evidence file URLs
    
    # Admin Assignment
    assigned_admin = Column(String(50))
    admin_notes = Column(Text)
    
    # Resolution
    status = Column(SQLEnum(DisputeStatus), default=DisputeStatus.OPEN)
    resolution = Column(Text)
    winner = Column(String(10))  # buyer, seller, or split
    
    created_at = Column(DateTime, default=func.now())
    resolved_at = Column(DateTime)

class P2PFeedback(Base):
    __tablename__ = "p2p_feedback"
    
    id = Column(Integer, primary_key=True, index=True)
    feedback_id = Column(String(50), unique=True, nullable=False, index=True)
    
    trade_id = Column(Integer, ForeignKey("p2p_trades.id"), nullable=False)
    
    # Feedback Details
    from_user_id = Column(Integer, ForeignKey("p2p_users.id"), nullable=False)
    to_user_id = Column(Integer, ForeignKey("p2p_users.id"), nullable=False)
    
    rating = Column(Integer, nullable=False)  # 1-5 stars
    comment = Column(Text)
    
    # Categories
    communication_rating = Column(Integer)
    payment_speed_rating = Column(Integer)
    reliability_rating = Column(Integer)
    
    created_at = Column(DateTime, default=func.now())

# Pydantic Models
class P2POrderCreate(BaseModel):
    order_type: OrderType
    cryptocurrency: str
    fiat_currency: str
    crypto_amount: Decimal
    price_per_unit: Decimal
    min_trade_amount: Optional[Decimal] = None
    max_trade_amount: Optional[Decimal] = None
    accepted_payment_methods: List[str]
    terms: Optional[str] = None
    auto_reply_message: Optional[str] = None
    allowed_countries: List[str] = []
    blocked_countries: List[str] = []
    
    @validator('crypto_amount')
    def validate_crypto_amount(cls, v):
        if v <= 0:
            raise ValueError('Crypto amount must be positive')
        return v
    
    @validator('price_per_unit')
    def validate_price(cls, v):
        if v <= 0:
            raise ValueError('Price must be positive')
        return v

class P2PTradeCreate(BaseModel):
    order_id: str
    fiat_amount: Decimal
    payment_method_id: str
    message: Optional[str] = None
    
    @validator('fiat_amount')
    def validate_amount(cls, v):
        if v < config.MIN_TRADE_AMOUNT:
            raise ValueError(f'Amount must be at least {config.MIN_TRADE_AMOUNT}')
        if v > config.MAX_TRADE_AMOUNT:
            raise ValueError(f'Amount cannot exceed {config.MAX_TRADE_AMOUNT}')
        return v

class PaymentMethodCreate(BaseModel):
    method_type: PaymentMethodType
    method_name: str
    account_details: Dict[str, Any]
    supported_currencies: List[str] = []
    supported_countries: List[str] = []
    min_amount: Optional[Decimal] = None
    max_amount: Optional[Decimal] = None
    daily_limit: Optional[Decimal] = None

class TradeMessageCreate(BaseModel):
    content: str
    message_type: str = "text"

class DisputeCreate(BaseModel):
    dispute_reason: str
    description: str
    evidence_urls: List[str] = []

class FeedbackCreate(BaseModel):
    rating: int
    comment: Optional[str] = None
    communication_rating: Optional[int] = None
    payment_speed_rating: Optional[int] = None
    reliability_rating: Optional[int] = None
    
    @validator('rating')
    def validate_rating(cls, v):
        if v < 1 or v > 5:
            raise ValueError('Rating must be between 1 and 5')
        return v

# Dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return {"user_id": "user_123", "username": "testuser", "country_code": "US"}

# P2P Trading Manager
class P2PTradingManager:
    def __init__(self):
        self.redis_client = None
        self.active_connections: Dict[str, WebSocket] = {}
        
    async def initialize(self):
        self.redis_client = await aioredis.from_url(config.REDIS_URL)
    
    async def create_p2p_order(self, order_data: P2POrderCreate, user: Dict[str, Any], db: Session):
        """Create new P2P order"""
        
        # Get or create P2P user
        p2p_user = await self.get_or_create_p2p_user(user, db)
        
        if not p2p_user.is_p2p_enabled:
            raise HTTPException(status_code=403, detail="P2P trading is disabled for this user")
        
        order_id = f"P2P_{secrets.token_hex(8).upper()}"
        
        # Calculate total fiat amount
        total_fiat = order_data.crypto_amount * order_data.price_per_unit
        
        order = P2POrder(
            order_id=order_id,
            user_id=p2p_user.id,
            order_type=order_data.order_type,
            cryptocurrency=order_data.cryptocurrency,
            fiat_currency=order_data.fiat_currency,
            crypto_amount=order_data.crypto_amount,
            price_per_unit=order_data.price_per_unit,
            total_fiat_amount=total_fiat,
            min_trade_amount=order_data.min_trade_amount or total_fiat,
            max_trade_amount=order_data.max_trade_amount or total_fiat,
            accepted_payment_methods=order_data.accepted_payment_methods,
            terms=order_data.terms,
            auto_reply_message=order_data.auto_reply_message,
            allowed_countries=order_data.allowed_countries,
            blocked_countries=order_data.blocked_countries,
            expires_at=datetime.utcnow() + timedelta(days=30)
        )
        
        db.add(order)
        db.commit()
        db.refresh(order)
        
        return order
    
    async def create_p2p_trade(self, trade_data: P2PTradeCreate, user: Dict[str, Any], db: Session):
        """Create new P2P trade"""
        
        # Get P2P user
        p2p_user = await self.get_or_create_p2p_user(user, db)
        
        # Get order
        order = db.query(P2POrder).filter(P2POrder.order_id == trade_data.order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")
        
        if order.status != OrderStatus.ACTIVE:
            raise HTTPException(status_code=400, detail="Order is not active")
        
        if order.user_id == p2p_user.id:
            raise HTTPException(status_code=400, detail="Cannot trade with yourself")
        
        # Validate trade amount
        if trade_data.fiat_amount < order.min_trade_amount:
            raise HTTPException(status_code=400, detail="Trade amount below minimum")
        
        if order.max_trade_amount and trade_data.fiat_amount > order.max_trade_amount:
            raise HTTPException(status_code=400, detail="Trade amount above maximum")
        
        # Calculate crypto amount
        crypto_amount = trade_data.fiat_amount / order.price_per_unit
        
        trade_id = f"TRADE_{secrets.token_hex(8).upper()}"
        chat_room_id = f"CHAT_{secrets.token_hex(8).upper()}"
        
        # Determine buyer and seller
        if order.order_type == OrderType.SELL:
            buyer_id = p2p_user.id
            seller_id = order.user_id
        else:
            buyer_id = order.user_id
            seller_id = p2p_user.id
        
        # Calculate platform fee
        platform_fee = crypto_amount * config.P2P_FEE_PERCENTAGE / 100
        
        trade = P2PTrade(
            trade_id=trade_id,
            order_id=order.id,
            buyer_id=buyer_id,
            seller_id=seller_id,
            crypto_amount=crypto_amount,
            fiat_amount=trade_data.fiat_amount,
            price_per_unit=order.price_per_unit,
            payment_method_id=int(trade_data.payment_method_id),
            payment_deadline=datetime.utcnow() + timedelta(hours=config.ESCROW_TIMEOUT_HOURS),
            chat_room_id=chat_room_id,
            platform_fee=platform_fee
        )
        
        db.add(trade)
        
        # Create initial system message
        if trade_data.message:
            message = TradeMessage(
                message_id=f"MSG_{secrets.token_hex(8).upper()}",
                trade_id=trade.id,
                sender_id=p2p_user.id,
                content=trade_data.message,
                is_system_message=False
            )
            db.add(message)
        
        # Create system message
        system_message = TradeMessage(
            message_id=f"MSG_{secrets.token_hex(8).upper()}",
            trade_id=trade.id,
            sender_id=p2p_user.id,
            content=f"Trade initiated for {crypto_amount} {order.cryptocurrency}",
            is_system_message=True
        )
        db.add(system_message)
        
        db.commit()
        db.refresh(trade)
        
        return trade
    
    async def get_or_create_p2p_user(self, user: Dict[str, Any], db: Session) -> P2PUser:
        """Get or create P2P user profile"""
        
        p2p_user = db.query(P2PUser).filter(P2PUser.user_id == user["user_id"]).first()
        
        if not p2p_user:
            p2p_user = P2PUser(
                user_id=user["user_id"],
                username=user["username"],
                email=user.get("email", ""),
                country_code=user.get("country_code", "US")
            )
            db.add(p2p_user)
            db.commit()
            db.refresh(p2p_user)
        
        return p2p_user
    
    async def confirm_payment(self, trade_id: str, user: Dict[str, Any], db: Session):
        """Confirm payment made"""
        
        trade = db.query(P2PTrade).filter(P2PTrade.trade_id == trade_id).first()
        if not trade:
            raise HTTPException(status_code=404, detail="Trade not found")
        
        p2p_user = await self.get_or_create_p2p_user(user, db)
        
        if trade.buyer_id != p2p_user.id:
            raise HTTPException(status_code=403, detail="Only buyer can confirm payment")
        
        if trade.status != TradeStatus.PENDING:
            raise HTTPException(status_code=400, detail="Trade is not in pending status")
        
        trade.status = TradeStatus.PAYMENT_CONFIRMED
        
        # Create system message
        message = TradeMessage(
            message_id=f"MSG_{secrets.token_hex(8).upper()}",
            trade_id=trade.id,
            sender_id=p2p_user.id,
            content="Payment confirmed by buyer",
            is_system_message=True
        )
        db.add(message)
        
        db.commit()
        
        return trade
    
    async def release_crypto(self, trade_id: str, user: Dict[str, Any], db: Session):
        """Release cryptocurrency to buyer"""
        
        trade = db.query(P2PTrade).filter(P2PTrade.trade_id == trade_id).first()
        if not trade:
            raise HTTPException(status_code=404, detail="Trade not found")
        
        p2p_user = await self.get_or_create_p2p_user(user, db)
        
        if trade.seller_id != p2p_user.id:
            raise HTTPException(status_code=403, detail="Only seller can release crypto")
        
        if trade.status != TradeStatus.PAYMENT_CONFIRMED:
            raise HTTPException(status_code=400, detail="Payment not confirmed yet")
        
        trade.status = TradeStatus.COMPLETED
        trade.completed_at = datetime.utcnow()
        
        # Update statistics
        buyer = db.query(P2PUser).filter(P2PUser.id == trade.buyer_id).first()
        seller = db.query(P2PUser).filter(P2PUser.id == trade.seller_id).first()
        
        for user_obj in [buyer, seller]:
            user_obj.total_trades += 1
            user_obj.successful_trades += 1
            user_obj.total_volume += trade.fiat_amount
        
        # Update order statistics
        order = trade.order
        order.completed_trades += 1
        order.total_volume += trade.fiat_amount
        
        # Create system message
        message = TradeMessage(
            message_id=f"MSG_{secrets.token_hex(8).upper()}",
            trade_id=trade.id,
            sender_id=p2p_user.id,
            content="Cryptocurrency released to buyer. Trade completed!",
            is_system_message=True
        )
        db.add(message)
        
        db.commit()
        
        return trade
    
    async def create_dispute(self, trade_id: str, dispute_data: DisputeCreate, user: Dict[str, Any], db: Session):
        """Create trade dispute"""
        
        trade = db.query(P2PTrade).filter(P2PTrade.trade_id == trade_id).first()
        if not trade:
            raise HTTPException(status_code=404, detail="Trade not found")
        
        p2p_user = await self.get_or_create_p2p_user(user, db)
        
        if trade.buyer_id != p2p_user.id and trade.seller_id != p2p_user.id:
            raise HTTPException(status_code=403, detail="Not authorized to dispute this trade")
        
        if trade.status in [TradeStatus.COMPLETED, TradeStatus.CANCELLED]:
            raise HTTPException(status_code=400, detail="Cannot dispute completed or cancelled trade")
        
        # Check if dispute already exists
        existing_dispute = db.query(TradeDispute).filter(TradeDispute.trade_id == trade.id).first()
        if existing_dispute:
            raise HTTPException(status_code=400, detail="Dispute already exists for this trade")
        
        dispute_id = f"DISPUTE_{secrets.token_hex(8).upper()}"
        
        dispute = TradeDispute(
            dispute_id=dispute_id,
            trade_id=trade.id,
            initiated_by=p2p_user.id,
            dispute_reason=dispute_data.dispute_reason,
            description=dispute_data.description,
            evidence_urls=dispute_data.evidence_urls
        )
        
        db.add(dispute)
        
        # Update trade status
        trade.status = TradeStatus.DISPUTED
        
        # Create system message
        message = TradeMessage(
            message_id=f"MSG_{secrets.token_hex(8).upper()}",
            trade_id=trade.id,
            sender_id=p2p_user.id,
            content=f"Dispute opened: {dispute_data.dispute_reason}",
            is_system_message=True
        )
        db.add(message)
        
        db.commit()
        db.refresh(dispute)
        
        return dispute

# Initialize P2P manager
p2p_manager = P2PTradingManager()

@app.on_event("startup")
async def startup_event():
    await p2p_manager.initialize()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
    
    async def connect(self, websocket: WebSocket, chat_room_id: str):
        await websocket.accept()
        self.active_connections[chat_room_id] = websocket
    
    def disconnect(self, chat_room_id: str):
        if chat_room_id in self.active_connections:
            del self.active_connections[chat_room_id]
    
    async def send_message(self, message: str, chat_room_id: str):
        if chat_room_id in self.active_connections:
            await self.active_connections[chat_room_id].send_text(message)

manager = ConnectionManager()

# API Endpoints
@app.post("/api/v1/p2p/orders")
async def create_p2p_order(
    order_data: P2POrderCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new P2P order"""
    order = await p2p_manager.create_p2p_order(order_data, current_user, db)
    return {
        "order_id": order.order_id,
        "order_type": order.order_type,
        "cryptocurrency": order.cryptocurrency,
        "fiat_currency": order.fiat_currency,
        "crypto_amount": str(order.crypto_amount),
        "price_per_unit": str(order.price_per_unit),
        "total_fiat_amount": str(order.total_fiat_amount),
        "status": order.status
    }

@app.get("/api/v1/p2p/orders")
async def get_p2p_orders(
    order_type: Optional[OrderType] = None,
    cryptocurrency: Optional[str] = None,
    fiat_currency: Optional[str] = None,
    country: Optional[str] = None,
    payment_method: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get P2P orders"""
    query = db.query(P2POrder).filter(P2POrder.status == OrderStatus.ACTIVE)
    
    if order_type:
        query = query.filter(P2POrder.order_type == order_type)
    
    if cryptocurrency:
        query = query.filter(P2POrder.cryptocurrency == cryptocurrency)
    
    if fiat_currency:
        query = query.filter(P2POrder.fiat_currency == fiat_currency)
    
    orders = query.offset(offset).limit(limit).all()
    
    return {
        "orders": [
            {
                "order_id": order.order_id,
                "order_type": order.order_type,
                "cryptocurrency": order.cryptocurrency,
                "fiat_currency": order.fiat_currency,
                "crypto_amount": str(order.crypto_amount),
                "price_per_unit": str(order.price_per_unit),
                "total_fiat_amount": str(order.total_fiat_amount),
                "min_trade_amount": str(order.min_trade_amount) if order.min_trade_amount else None,
                "max_trade_amount": str(order.max_trade_amount) if order.max_trade_amount else None,
                "accepted_payment_methods": order.accepted_payment_methods,
                "terms": order.terms,
                "user": {
                    "username": order.user.username,
                    "total_trades": order.user.total_trades,
                    "successful_trades": order.user.successful_trades,
                    "average_rating": str(order.user.average_rating)
                },
                "created_at": order.created_at.isoformat()
            }
            for order in orders
        ]
    }

@app.post("/api/v1/p2p/trades")
async def create_p2p_trade(
    trade_data: P2PTradeCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new P2P trade"""
    trade = await p2p_manager.create_p2p_trade(trade_data, current_user, db)
    return {
        "trade_id": trade.trade_id,
        "crypto_amount": str(trade.crypto_amount),
        "fiat_amount": str(trade.fiat_amount),
        "price_per_unit": str(trade.price_per_unit),
        "payment_deadline": trade.payment_deadline.isoformat(),
        "chat_room_id": trade.chat_room_id,
        "status": trade.status
    }

@app.get("/api/v1/p2p/trades")
async def get_user_trades(
    status: Optional[TradeStatus] = None,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's P2P trades"""
    p2p_user = await p2p_manager.get_or_create_p2p_user(current_user, db)
    
    query = db.query(P2PTrade).filter(
        (P2PTrade.buyer_id == p2p_user.id) | (P2PTrade.seller_id == p2p_user.id)
    )
    
    if status:
        query = query.filter(P2PTrade.status == status)
    
    trades = query.order_by(P2PTrade.created_at.desc()).all()
    
    return {
        "trades": [
            {
                "trade_id": trade.trade_id,
                "order": {
                    "cryptocurrency": trade.order.cryptocurrency,
                    "fiat_currency": trade.order.fiat_currency
                },
                "crypto_amount": str(trade.crypto_amount),
                "fiat_amount": str(trade.fiat_amount),
                "price_per_unit": str(trade.price_per_unit),
                "status": trade.status,
                "is_buyer": trade.buyer_id == p2p_user.id,
                "counterparty": {
                    "username": trade.seller.username if trade.buyer_id == p2p_user.id else trade.buyer.username,
                    "average_rating": str(trade.seller.average_rating if trade.buyer_id == p2p_user.id else trade.buyer.average_rating)
                },
                "payment_deadline": trade.payment_deadline.isoformat(),
                "chat_room_id": trade.chat_room_id,
                "created_at": trade.created_at.isoformat()
            }
            for trade in trades
        ]
    }

@app.post("/api/v1/p2p/trades/{trade_id}/confirm-payment")
async def confirm_payment(
    trade_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Confirm payment made"""
    trade = await p2p_manager.confirm_payment(trade_id, current_user, db)
    return {
        "trade_id": trade_id,
        "status": trade.status,
        "message": "Payment confirmed"
    }

@app.post("/api/v1/p2p/trades/{trade_id}/release")
async def release_crypto(
    trade_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Release cryptocurrency"""
    trade = await p2p_manager.release_crypto(trade_id, current_user, db)
    return {
        "trade_id": trade_id,
        "status": trade.status,
        "message": "Cryptocurrency released"
    }

@app.post("/api/v1/p2p/trades/{trade_id}/dispute")
async def create_dispute(
    trade_id: str,
    dispute_data: DisputeCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create trade dispute"""
    dispute = await p2p_manager.create_dispute(trade_id, dispute_data, current_user, db)
    return {
        "dispute_id": dispute.dispute_id,
        "trade_id": trade_id,
        "status": dispute.status,
        "message": "Dispute created successfully"
    }

@app.post("/api/v1/p2p/payment-methods")
async def create_payment_method(
    method_data: PaymentMethodCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create payment method"""
    p2p_user = await p2p_manager.get_or_create_p2p_user(current_user, db)
    
    method_id = f"PM_{secrets.token_hex(8).upper()}"
    
    payment_method = PaymentMethod(
        method_id=method_id,
        user_id=p2p_user.id,
        method_type=method_data.method_type,
        method_name=method_data.method_name,
        account_details=method_data.account_details,
        supported_currencies=method_data.supported_currencies,
        supported_countries=method_data.supported_countries,
        min_amount=method_data.min_amount,
        max_amount=method_data.max_amount,
        daily_limit=method_data.daily_limit
    )
    
    db.add(payment_method)
    db.commit()
    db.refresh(payment_method)
    
    return {
        "method_id": payment_method.method_id,
        "method_type": payment_method.method_type,
        "method_name": payment_method.method_name,
        "status": "created"
    }

@app.get("/api/v1/p2p/payment-methods")
async def get_payment_methods(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's payment methods"""
    p2p_user = await p2p_manager.get_or_create_p2p_user(current_user, db)
    
    methods = db.query(PaymentMethod).filter(
        PaymentMethod.user_id == p2p_user.id,
        PaymentMethod.is_active == True
    ).all()
    
    return {
        "payment_methods": [
            {
                "method_id": method.method_id,
                "method_type": method.method_type,
                "method_name": method.method_name,
                "supported_currencies": method.supported_currencies,
                "supported_countries": method.supported_countries,
                "is_verified": method.is_verified,
                "created_at": method.created_at.isoformat()
            }
            for method in methods
        ]
    }

@app.websocket("/ws/chat/{chat_room_id}")
async def websocket_chat(websocket: WebSocket, chat_room_id: str):
    """WebSocket chat for P2P trades"""
    await manager.connect(websocket, chat_room_id)
    try:
        while True:
            data = await websocket.receive_text()
            await manager.send_message(data, chat_room_id)
    except WebSocketDisconnect:
        manager.disconnect(chat_room_id)

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "p2p-trading"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
