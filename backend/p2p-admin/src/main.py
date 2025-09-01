"""
TigerEx P2P Admin Dashboard
Comprehensive administrative interface for P2P trading management
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
import io
import base64

import aioredis
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, validator, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, DECIMAL, ForeignKey, JSON, Enum as SQLEnum, func as sql_func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder

# Import P2P models (assuming they're in a shared location)
import sys
sys.path.append('../p2p-trading/src')
from main import (
    P2PUser, P2POrder, P2PTrade, TradeMessage, TradeDispute, P2PFeedback, PaymentMethod,
    OrderType, OrderStatus, TradeStatus, PaymentMethodType, DisputeStatus, UserRole
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="TigerEx P2P Admin Dashboard",
    description="Comprehensive administrative interface for P2P trading management",
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
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "p2p-admin-secret-key")

config = Config()

# Database setup
engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

security = HTTPBearer()

# Additional Admin Models
class P2PAdminAction(Base):
    __tablename__ = "p2p_admin_actions"
    
    id = Column(Integer, primary_key=True, index=True)
    action_id = Column(String(50), unique=True, nullable=False, index=True)
    
    admin_id = Column(String(50), nullable=False, index=True)
    action_type = Column(String(50), nullable=False)
    target_type = Column(String(50), nullable=False)  # user, trade, dispute, order
    target_id = Column(String(50), nullable=False)
    
    description = Column(Text, nullable=False)
    details = Column(JSON)
    
    created_at = Column(DateTime, default=func.now())

class P2PSettings(Base):
    __tablename__ = "p2p_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    setting_key = Column(String(100), unique=True, nullable=False)
    setting_value = Column(JSON, nullable=False)
    description = Column(Text)
    
    updated_by = Column(String(50), nullable=False)
    updated_at = Column(DateTime, default=func.now())

# Pydantic Models
class DisputeResolution(BaseModel):
    resolution: str
    winner: str  # buyer, seller, or split
    admin_notes: Optional[str] = None
    
    @validator('winner')
    def validate_winner(cls, v):
        if v not in ['buyer', 'seller', 'split']:
            raise ValueError('Winner must be buyer, seller, or split')
        return v

class UserAction(BaseModel):
    action: str  # block, unblock, verify, suspend
    reason: Optional[str] = None
    duration_days: Optional[int] = None

class P2PSettingsUpdate(BaseModel):
    setting_key: str
    setting_value: Any
    description: Optional[str] = None

class AdminStats(BaseModel):
    total_users: int
    active_orders: int
    completed_trades: int
    pending_disputes: int
    total_volume_24h: Decimal
    total_fees_24h: Decimal

# Dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Simplified admin authentication - in production, verify JWT and check admin role
    return {"user_id": "admin_123", "role": UserRole.P2P_ADMIN, "username": "p2p_admin"}

# P2P Admin Manager
class P2PAdminManager:
    def __init__(self):
        self.redis_client = None
        
    async def initialize(self):
        self.redis_client = await aioredis.from_url(config.REDIS_URL)
    
    async def get_dashboard_stats(self, db: Session) -> Dict[str, Any]:
        """Get comprehensive dashboard statistics"""
        
        # Basic counts
        total_users = db.query(P2PUser).count()
        active_orders = db.query(P2POrder).filter(P2POrder.status == OrderStatus.ACTIVE).count()
        completed_trades = db.query(P2PTrade).filter(P2PTrade.status == TradeStatus.COMPLETED).count()
        pending_disputes = db.query(TradeDispute).filter(TradeDispute.status == DisputeStatus.OPEN).count()
        
        # 24h statistics
        yesterday = datetime.utcnow() - timedelta(days=1)
        
        trades_24h = db.query(P2PTrade).filter(
            P2PTrade.created_at >= yesterday,
            P2PTrade.status == TradeStatus.COMPLETED
        ).all()
        
        total_volume_24h = sum(trade.fiat_amount for trade in trades_24h)
        total_fees_24h = sum(trade.platform_fee for trade in trades_24h)
        
        # Growth statistics
        users_growth = self._calculate_growth(db, P2PUser, 'created_at')
        trades_growth = self._calculate_growth(db, P2PTrade, 'created_at')
        
        # Top cryptocurrencies
        crypto_stats = db.query(
            P2POrder.cryptocurrency,
            sql_func.count(P2POrder.id).label('order_count'),
            sql_func.sum(P2POrder.total_volume).label('total_volume')
        ).group_by(P2POrder.cryptocurrency).order_by(sql_func.sum(P2POrder.total_volume).desc()).limit(10).all()
        
        # Top countries
        country_stats = db.query(
            P2PUser.country_code,
            sql_func.count(P2PUser.id).label('user_count'),
            sql_func.sum(P2PUser.total_volume).label('total_volume')
        ).group_by(P2PUser.country_code).order_by(sql_func.sum(P2PUser.total_volume).desc()).limit(10).all()
        
        return {
            "overview": {
                "total_users": total_users,
                "active_orders": active_orders,
                "completed_trades": completed_trades,
                "pending_disputes": pending_disputes,
                "total_volume_24h": float(total_volume_24h),
                "total_fees_24h": float(total_fees_24h)
            },
            "growth": {
                "users_growth_7d": users_growth['7d'],
                "users_growth_30d": users_growth['30d'],
                "trades_growth_7d": trades_growth['7d'],
                "trades_growth_30d": trades_growth['30d']
            },
            "top_cryptocurrencies": [
                {
                    "cryptocurrency": stat.cryptocurrency,
                    "order_count": stat.order_count,
                    "total_volume": float(stat.total_volume or 0)
                }
                for stat in crypto_stats
            ],
            "top_countries": [
                {
                    "country_code": stat.country_code,
                    "user_count": stat.user_count,
                    "total_volume": float(stat.total_volume or 0)
                }
                for stat in country_stats
            ]
        }
    
    def _calculate_growth(self, db: Session, model, date_field: str) -> Dict[str, float]:
        """Calculate growth percentages"""
        
        now = datetime.utcnow()
        
        # 7 days
        week_ago = now - timedelta(days=7)
        two_weeks_ago = now - timedelta(days=14)
        
        current_week = db.query(model).filter(getattr(model, date_field) >= week_ago).count()
        previous_week = db.query(model).filter(
            getattr(model, date_field) >= two_weeks_ago,
            getattr(model, date_field) < week_ago
        ).count()
        
        growth_7d = ((current_week - previous_week) / previous_week * 100) if previous_week > 0 else 0
        
        # 30 days
        month_ago = now - timedelta(days=30)
        two_months_ago = now - timedelta(days=60)
        
        current_month = db.query(model).filter(getattr(model, date_field) >= month_ago).count()
        previous_month = db.query(model).filter(
            getattr(model, date_field) >= two_months_ago,
            getattr(model, date_field) < month_ago
        ).count()
        
        growth_30d = ((current_month - previous_month) / previous_month * 100) if previous_month > 0 else 0
        
        return {
            "7d": round(growth_7d, 2),
            "30d": round(growth_30d, 2)
        }
    
    async def resolve_dispute(self, dispute_id: str, resolution_data: DisputeResolution, admin: Dict[str, Any], db: Session):
        """Resolve trade dispute"""
        
        dispute = db.query(TradeDispute).filter(TradeDispute.dispute_id == dispute_id).first()
        if not dispute:
            raise HTTPException(status_code=404, detail="Dispute not found")
        
        if dispute.status != DisputeStatus.OPEN:
            raise HTTPException(status_code=400, detail="Dispute is not open")
        
        # Update dispute
        dispute.status = DisputeStatus.RESOLVED
        dispute.resolution = resolution_data.resolution
        dispute.winner = resolution_data.winner
        dispute.admin_notes = resolution_data.admin_notes
        dispute.assigned_admin = admin["user_id"]
        dispute.resolved_at = datetime.utcnow()
        
        # Update trade status
        trade = dispute.trade
        if resolution_data.winner == "buyer":
            trade.status = TradeStatus.COMPLETED
        elif resolution_data.winner == "seller":
            trade.status = TradeStatus.CANCELLED
        else:  # split
            trade.status = TradeStatus.REFUNDED
        
        # Log admin action
        action = P2PAdminAction(
            action_id=f"ACTION_{secrets.token_hex(8).upper()}",
            admin_id=admin["user_id"],
            action_type="resolve_dispute",
            target_type="dispute",
            target_id=dispute_id,
            description=f"Resolved dispute in favor of {resolution_data.winner}",
            details={
                "resolution": resolution_data.resolution,
                "winner": resolution_data.winner,
                "admin_notes": resolution_data.admin_notes
            }
        )
        
        db.add(action)
        db.commit()
        
        return dispute
    
    async def manage_user(self, user_id: str, action_data: UserAction, admin: Dict[str, Any], db: Session):
        """Manage P2P user (block, verify, etc.)"""
        
        user = db.query(P2PUser).filter(P2PUser.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if action_data.action == "block":
            user.is_blocked = True
            user.is_p2p_enabled = False
        elif action_data.action == "unblock":
            user.is_blocked = False
            user.is_p2p_enabled = True
        elif action_data.action == "verify":
            user.is_verified = True
        elif action_data.action == "suspend":
            user.is_p2p_enabled = False
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
        
        # Log admin action
        action = P2PAdminAction(
            action_id=f"ACTION_{secrets.token_hex(8).upper()}",
            admin_id=admin["user_id"],
            action_type=f"user_{action_data.action}",
            target_type="user",
            target_id=user_id,
            description=f"User {action_data.action}: {action_data.reason or 'No reason provided'}",
            details={
                "action": action_data.action,
                "reason": action_data.reason,
                "duration_days": action_data.duration_days
            }
        )
        
        db.add(action)
        db.commit()
        
        return user
    
    async def generate_analytics_chart(self, chart_type: str, period: str, db: Session) -> str:
        """Generate analytics charts"""
        
        # Calculate date range
        if period == "7d":
            start_date = datetime.utcnow() - timedelta(days=7)
        elif period == "30d":
            start_date = datetime.utcnow() - timedelta(days=30)
        elif period == "90d":
            start_date = datetime.utcnow() - timedelta(days=90)
        else:
            start_date = datetime.utcnow() - timedelta(days=30)
        
        if chart_type == "trade_volume":
            # Trade volume over time
            trades = db.query(P2PTrade).filter(
                P2PTrade.created_at >= start_date,
                P2PTrade.status == TradeStatus.COMPLETED
            ).all()
            
            df = pd.DataFrame([
                {
                    "date": trade.created_at.date(),
                    "volume": float(trade.fiat_amount),
                    "crypto": trade.order.cryptocurrency
                }
                for trade in trades
            ])
            
            if df.empty:
                return self._create_empty_chart("No trade data available")
            
            daily_volume = df.groupby("date")["volume"].sum().reset_index()
            
            fig = px.line(daily_volume, x="date", y="volume", title="Daily Trade Volume")
            fig.update_layout(xaxis_title="Date", yaxis_title="Volume (USD)")
            
            return json.dumps(fig, cls=PlotlyJSONEncoder)
        
        elif chart_type == "user_growth":
            # User registration over time
            users = db.query(P2PUser).filter(P2PUser.created_at >= start_date).all()
            
            df = pd.DataFrame([
                {"date": user.created_at.date()}
                for user in users
            ])
            
            if df.empty:
                return self._create_empty_chart("No user data available")
            
            daily_users = df.groupby("date").size().reset_index(name="new_users")
            daily_users["cumulative_users"] = daily_users["new_users"].cumsum()
            
            fig = px.line(daily_users, x="date", y="cumulative_users", title="User Growth")
            fig.update_layout(xaxis_title="Date", yaxis_title="Total Users")
            
            return json.dumps(fig, cls=PlotlyJSONEncoder)
        
        elif chart_type == "cryptocurrency_distribution":
            # Cryptocurrency distribution
            orders = db.query(P2POrder).filter(P2POrder.created_at >= start_date).all()
            
            crypto_counts = {}
            for order in orders:
                crypto_counts[order.cryptocurrency] = crypto_counts.get(order.cryptocurrency, 0) + 1
            
            if not crypto_counts:
                return self._create_empty_chart("No order data available")
            
            fig = px.pie(
                values=list(crypto_counts.values()),
                names=list(crypto_counts.keys()),
                title="Cryptocurrency Distribution"
            )
            
            return json.dumps(fig, cls=PlotlyJSONEncoder)
        
        elif chart_type == "country_distribution":
            # Country distribution
            users = db.query(P2PUser).all()
            
            country_counts = {}
            for user in users:
                country_counts[user.country_code] = country_counts.get(user.country_code, 0) + 1
            
            if not country_counts:
                return self._create_empty_chart("No user data available")
            
            # Get top 10 countries
            top_countries = sorted(country_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            
            fig = px.bar(
                x=[country[1] for country in top_countries],
                y=[country[0] for country in top_countries],
                orientation='h',
                title="Top Countries by User Count"
            )
            fig.update_layout(xaxis_title="User Count", yaxis_title="Country")
            
            return json.dumps(fig, cls=PlotlyJSONEncoder)
        
        else:
            return self._create_empty_chart("Invalid chart type")
    
    def _create_empty_chart(self, message: str) -> str:
        """Create empty chart with message"""
        fig = go.Figure()
        fig.add_annotation(
            text=message,
            xref="paper", yref="paper",
            x=0.5, y=0.5,
            showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            title=message
        )
        return json.dumps(fig, cls=PlotlyJSONEncoder)
    
    async def update_p2p_settings(self, settings_data: P2PSettingsUpdate, admin: Dict[str, Any], db: Session):
        """Update P2P platform settings"""
        
        setting = db.query(P2PSettings).filter(P2PSettings.setting_key == settings_data.setting_key).first()
        
        if setting:
            setting.setting_value = settings_data.setting_value
            setting.description = settings_data.description
            setting.updated_by = admin["user_id"]
            setting.updated_at = datetime.utcnow()
        else:
            setting = P2PSettings(
                setting_key=settings_data.setting_key,
                setting_value=settings_data.setting_value,
                description=settings_data.description,
                updated_by=admin["user_id"]
            )
            db.add(setting)
        
        # Log admin action
        action = P2PAdminAction(
            action_id=f"ACTION_{secrets.token_hex(8).upper()}",
            admin_id=admin["user_id"],
            action_type="update_settings",
            target_type="settings",
            target_id=settings_data.setting_key,
            description=f"Updated setting: {settings_data.setting_key}",
            details={
                "setting_key": settings_data.setting_key,
                "setting_value": settings_data.setting_value,
                "description": settings_data.description
            }
        )
        
        db.add(action)
        db.commit()
        
        return setting

# Initialize admin manager
admin_manager = P2PAdminManager()

@app.on_event("startup")
async def startup_event():
    await admin_manager.initialize()

# API Endpoints
@app.get("/api/v1/p2p-admin/dashboard")
async def get_dashboard_stats(
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get dashboard statistics"""
    stats = await admin_manager.get_dashboard_stats(db)
    return stats

@app.get("/api/v1/p2p-admin/users")
async def get_p2p_users(
    status: Optional[str] = None,
    country: Optional[str] = None,
    verified: Optional[bool] = None,
    blocked: Optional[bool] = None,
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get P2P users with filtering"""
    query = db.query(P2PUser)
    
    if country:
        query = query.filter(P2PUser.country_code == country)
    
    if verified is not None:
        query = query.filter(P2PUser.is_verified == verified)
    
    if blocked is not None:
        query = query.filter(P2PUser.is_blocked == blocked)
    
    if search:
        query = query.filter(
            (P2PUser.username.ilike(f"%{search}%")) |
            (P2PUser.email.ilike(f"%{search}%"))
        )
    
    users = query.offset(offset).limit(limit).all()
    total = query.count()
    
    return {
        "users": [
            {
                "user_id": user.user_id,
                "username": user.username,
                "email": user.email,
                "country_code": user.country_code,
                "total_trades": user.total_trades,
                "successful_trades": user.successful_trades,
                "total_volume": str(user.total_volume),
                "average_rating": str(user.average_rating),
                "is_verified": user.is_verified,
                "is_p2p_enabled": user.is_p2p_enabled,
                "is_blocked": user.is_blocked,
                "created_at": user.created_at.isoformat(),
                "last_active_at": user.last_active_at.isoformat() if user.last_active_at else None
            }
            for user in users
        ],
        "total": total,
        "limit": limit,
        "offset": offset
    }

@app.get("/api/v1/p2p-admin/trades")
async def get_p2p_trades(
    status: Optional[TradeStatus] = None,
    cryptocurrency: Optional[str] = None,
    fiat_currency: Optional[str] = None,
    min_amount: Optional[Decimal] = None,
    max_amount: Optional[Decimal] = None,
    limit: int = 50,
    offset: int = 0,
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get P2P trades with filtering"""
    query = db.query(P2PTrade)
    
    if status:
        query = query.filter(P2PTrade.status == status)
    
    if cryptocurrency:
        query = query.join(P2POrder).filter(P2POrder.cryptocurrency == cryptocurrency)
    
    if fiat_currency:
        query = query.join(P2POrder).filter(P2POrder.fiat_currency == fiat_currency)
    
    if min_amount:
        query = query.filter(P2PTrade.fiat_amount >= min_amount)
    
    if max_amount:
        query = query.filter(P2PTrade.fiat_amount <= max_amount)
    
    trades = query.order_by(P2PTrade.created_at.desc()).offset(offset).limit(limit).all()
    total = query.count()
    
    return {
        "trades": [
            {
                "trade_id": trade.trade_id,
                "order": {
                    "cryptocurrency": trade.order.cryptocurrency,
                    "fiat_currency": trade.order.fiat_currency,
                    "order_type": trade.order.order_type
                },
                "buyer": {
                    "username": trade.buyer.username,
                    "country_code": trade.buyer.country_code
                },
                "seller": {
                    "username": trade.seller.username,
                    "country_code": trade.seller.country_code
                },
                "crypto_amount": str(trade.crypto_amount),
                "fiat_amount": str(trade.fiat_amount),
                "price_per_unit": str(trade.price_per_unit),
                "platform_fee": str(trade.platform_fee),
                "status": trade.status,
                "payment_deadline": trade.payment_deadline.isoformat(),
                "created_at": trade.created_at.isoformat(),
                "completed_at": trade.completed_at.isoformat() if trade.completed_at else None
            }
            for trade in trades
        ],
        "total": total,
        "limit": limit,
        "offset": offset
    }

@app.get("/api/v1/p2p-admin/disputes")
async def get_disputes(
    status: Optional[DisputeStatus] = None,
    assigned_admin: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get trade disputes"""
    query = db.query(TradeDispute)
    
    if status:
        query = query.filter(TradeDispute.status == status)
    
    if assigned_admin:
        query = query.filter(TradeDispute.assigned_admin == assigned_admin)
    
    disputes = query.order_by(TradeDispute.created_at.desc()).offset(offset).limit(limit).all()
    total = query.count()
    
    return {
        "disputes": [
            {
                "dispute_id": dispute.dispute_id,
                "trade": {
                    "trade_id": dispute.trade.trade_id,
                    "cryptocurrency": dispute.trade.order.cryptocurrency,
                    "fiat_amount": str(dispute.trade.fiat_amount)
                },
                "initiated_by": {
                    "user_id": dispute.initiated_by,
                    "username": next((u.username for u in [dispute.trade.buyer, dispute.trade.seller] if u.id == dispute.initiated_by), "Unknown")
                },
                "dispute_reason": dispute.dispute_reason,
                "description": dispute.description,
                "evidence_urls": dispute.evidence_urls,
                "status": dispute.status,
                "assigned_admin": dispute.assigned_admin,
                "admin_notes": dispute.admin_notes,
                "resolution": dispute.resolution,
                "winner": dispute.winner,
                "created_at": dispute.created_at.isoformat(),
                "resolved_at": dispute.resolved_at.isoformat() if dispute.resolved_at else None
            }
            for dispute in disputes
        ],
        "total": total,
        "limit": limit,
        "offset": offset
    }

@app.post("/api/v1/p2p-admin/disputes/{dispute_id}/resolve")
async def resolve_dispute(
    dispute_id: str,
    resolution_data: DisputeResolution,
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Resolve trade dispute"""
    dispute = await admin_manager.resolve_dispute(dispute_id, resolution_data, current_admin, db)
    return {
        "dispute_id": dispute_id,
        "status": dispute.status,
        "resolution": dispute.resolution,
        "winner": dispute.winner,
        "message": "Dispute resolved successfully"
    }

@app.post("/api/v1/p2p-admin/users/{user_id}/action")
async def manage_user(
    user_id: str,
    action_data: UserAction,
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Manage P2P user"""
    user = await admin_manager.manage_user(user_id, action_data, current_admin, db)
    return {
        "user_id": user_id,
        "action": action_data.action,
        "is_blocked": user.is_blocked,
        "is_verified": user.is_verified,
        "is_p2p_enabled": user.is_p2p_enabled,
        "message": f"User {action_data.action} completed successfully"
    }

@app.get("/api/v1/p2p-admin/orders")
async def get_p2p_orders(
    status: Optional[OrderStatus] = None,
    order_type: Optional[OrderType] = None,
    cryptocurrency: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get P2P orders"""
    query = db.query(P2POrder)
    
    if status:
        query = query.filter(P2POrder.status == status)
    
    if order_type:
        query = query.filter(P2POrder.order_type == order_type)
    
    if cryptocurrency:
        query = query.filter(P2POrder.cryptocurrency == cryptocurrency)
    
    if user_id:
        user = db.query(P2PUser).filter(P2PUser.user_id == user_id).first()
        if user:
            query = query.filter(P2POrder.user_id == user.id)
    
    orders = query.order_by(P2POrder.created_at.desc()).offset(offset).limit(limit).all()
    total = query.count()
    
    return {
        "orders": [
            {
                "order_id": order.order_id,
                "user": {
                    "username": order.user.username,
                    "country_code": order.user.country_code
                },
                "order_type": order.order_type,
                "cryptocurrency": order.cryptocurrency,
                "fiat_currency": order.fiat_currency,
                "crypto_amount": str(order.crypto_amount),
                "price_per_unit": str(order.price_per_unit),
                "total_fiat_amount": str(order.total_fiat_amount),
                "status": order.status,
                "completed_trades": order.completed_trades,
                "total_volume": str(order.total_volume),
                "created_at": order.created_at.isoformat()
            }
            for order in orders
        ],
        "total": total,
        "limit": limit,
        "offset": offset
    }

@app.get("/api/v1/p2p-admin/analytics/chart")
async def get_analytics_chart(
    chart_type: str = Query(..., description="Chart type: trade_volume, user_growth, cryptocurrency_distribution, country_distribution"),
    period: str = Query("30d", description="Time period: 7d, 30d, 90d"),
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get analytics chart data"""
    chart_data = await admin_manager.generate_analytics_chart(chart_type, period, db)
    return {"chart_data": chart_data}

@app.get("/api/v1/p2p-admin/payment-methods")
async def get_payment_methods(
    method_type: Optional[PaymentMethodType] = None,
    verified: Optional[bool] = None,
    active: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get payment methods"""
    query = db.query(PaymentMethod)
    
    if method_type:
        query = query.filter(PaymentMethod.method_type == method_type)
    
    if verified is not None:
        query = query.filter(PaymentMethod.is_verified == verified)
    
    if active is not None:
        query = query.filter(PaymentMethod.is_active == active)
    
    methods = query.offset(offset).limit(limit).all()
    total = query.count()
    
    return {
        "payment_methods": [
            {
                "method_id": method.method_id,
                "user": {
                    "username": method.user.username,
                    "country_code": method.user.country_code
                },
                "method_type": method.method_type,
                "method_name": method.method_name,
                "supported_currencies": method.supported_currencies,
                "supported_countries": method.supported_countries,
                "is_verified": method.is_verified,
                "is_active": method.is_active,
                "created_at": method.created_at.isoformat()
            }
            for method in methods
        ],
        "total": total,
        "limit": limit,
        "offset": offset
    }

@app.get("/api/v1/p2p-admin/settings")
async def get_p2p_settings(
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get P2P platform settings"""
    settings = db.query(P2PSettings).all()
    
    return {
        "settings": [
            {
                "setting_key": setting.setting_key,
                "setting_value": setting.setting_value,
                "description": setting.description,
                "updated_by": setting.updated_by,
                "updated_at": setting.updated_at.isoformat()
            }
            for setting in settings
        ]
    }

@app.post("/api/v1/p2p-admin/settings")
async def update_p2p_settings(
    settings_data: P2PSettingsUpdate,
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update P2P platform settings"""
    setting = await admin_manager.update_p2p_settings(settings_data, current_admin, db)
    return {
        "setting_key": setting.setting_key,
        "setting_value": setting.setting_value,
        "message": "Setting updated successfully"
    }

@app.get("/api/v1/p2p-admin/admin-actions")
async def get_admin_actions(
    admin_id: Optional[str] = None,
    action_type: Optional[str] = None,
    target_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get admin action history"""
    query = db.query(P2PAdminAction)
    
    if admin_id:
        query = query.filter(P2PAdminAction.admin_id == admin_id)
    
    if action_type:
        query = query.filter(P2PAdminAction.action_type == action_type)
    
    if target_type:
        query = query.filter(P2PAdminAction.target_type == target_type)
    
    actions = query.order_by(P2PAdminAction.created_at.desc()).offset(offset).limit(limit).all()
    total = query.count()
    
    return {
        "admin_actions": [
            {
                "action_id": action.action_id,
                "admin_id": action.admin_id,
                "action_type": action.action_type,
                "target_type": action.target_type,
                "target_id": action.target_id,
                "description": action.description,
                "details": action.details,
                "created_at": action.created_at.isoformat()
            }
            for action in actions
        ],
        "total": total,
        "limit": limit,
        "offset": offset
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "p2p-admin-dashboard"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
