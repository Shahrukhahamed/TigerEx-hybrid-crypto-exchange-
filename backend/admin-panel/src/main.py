"""
TigerEx Advanced Admin Panel
Comprehensive admin system with all features from Binance, Bybit, OKX
Includes user management, trading controls, risk management, compliance, and analytics
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import hmac
import base64
import secrets
import bcrypt
from pathlib import Path

import asyncpg
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, validator, EmailStr
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from kafka import KafkaProducer, KafkaConsumer
import boto3
from celery import Celery
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import twilio
from twilio.rest import Client as TwilioClient
import requests
import aiofiles
import zipfile
import io

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="TigerEx Admin Panel",
    description="Advanced admin panel with comprehensive exchange management",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Configuration
class Config:
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/tigerex")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:9092").split(",")
    
    # Admin Security
    ADMIN_SECRET_KEY = os.getenv("ADMIN_SECRET_KEY", secrets.token_urlsafe(32))
    ADMIN_SESSION_TIMEOUT = int(os.getenv("ADMIN_SESSION_TIMEOUT", "3600"))  # 1 hour
    
    # Email Configuration
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
    
    # SMS Configuration
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
    
    # Cloud Storage
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_BUCKET_NAME = os.getenv("AWS_BUCKET_NAME", "tigerex-admin")
    
    # External APIs
    CHAINALYSIS_API_KEY = os.getenv("CHAINALYSIS_API_KEY")
    ELLIPTIC_API_KEY = os.getenv("ELLIPTIC_API_KEY")
    COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")

config = Config()

# Enums
class AdminRole(str, Enum):
    SUPER_ADMIN = "SUPER_ADMIN"
    ADMIN = "ADMIN"
    COMPLIANCE_OFFICER = "COMPLIANCE_OFFICER"
    RISK_MANAGER = "RISK_MANAGER"
    CUSTOMER_SUPPORT = "CUSTOMER_SUPPORT"
    FINANCE_MANAGER = "FINANCE_MANAGER"
    TRADING_MANAGER = "TRADING_MANAGER"
    SECURITY_OFFICER = "SECURITY_OFFICER"
    AUDIT_MANAGER = "AUDIT_MANAGER"
    OPERATIONS_MANAGER = "OPERATIONS_MANAGER"

class UserStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    BANNED = "BANNED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    LOCKED = "LOCKED"
    DORMANT = "DORMANT"

class KYCStatus(str, Enum):
    NOT_SUBMITTED = "NOT_SUBMITTED"
    PENDING = "PENDING"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"

class TradingStatus(str, Enum):
    ENABLED = "ENABLED"
    DISABLED = "DISABLED"
    RESTRICTED = "RESTRICTED"
    SUSPENDED = "SUSPENDED"

class AlertType(str, Enum):
    SECURITY = "SECURITY"
    COMPLIANCE = "COMPLIANCE"
    TRADING = "TRADING"
    SYSTEM = "SYSTEM"
    RISK = "RISK"
    FRAUD = "FRAUD"

class AlertSeverity(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ActionType(str, Enum):
    USER_SUSPENSION = "USER_SUSPENSION"
    TRADING_HALT = "TRADING_HALT"
    WITHDRAWAL_FREEZE = "WITHDRAWAL_FREEZE"
    KYC_REVIEW = "KYC_REVIEW"
    RISK_ASSESSMENT = "RISK_ASSESSMENT"
    COMPLIANCE_CHECK = "COMPLIANCE_CHECK"

# Data Models
@dataclass
class AdminUser:
    id: str
    username: str
    email: str
    password_hash: str
    role: AdminRole
    permissions: List[str]
    is_active: bool
    last_login: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    two_factor_enabled: bool
    two_factor_secret: Optional[str]
    session_token: Optional[str]
    session_expires: Optional[datetime]

@dataclass
class UserProfile:
    user_id: str
    email: str
    phone: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    date_of_birth: Optional[datetime]
    country: Optional[str]
    address: Optional[Dict[str, str]]
    kyc_status: KYCStatus
    kyc_level: int
    user_status: UserStatus
    trading_status: TradingStatus
    vip_level: int
    referral_code: str
    referred_by: Optional[str]
    created_at: datetime
    last_login: Optional[datetime]
    total_trading_volume: Decimal
    total_fees_paid: Decimal
    risk_score: float

@dataclass
class SystemAlert:
    id: str
    alert_type: AlertType
    severity: AlertSeverity
    title: str
    description: str
    data: Dict[str, Any]
    is_resolved: bool
    created_at: datetime
    resolved_at: Optional[datetime]
    resolved_by: Optional[str]
    actions_taken: List[str]

@dataclass
class TradingPair:
    symbol: str
    base_asset: str
    quote_asset: str
    status: str
    min_qty: Decimal
    max_qty: Decimal
    step_size: Decimal
    min_price: Decimal
    max_price: Decimal
    tick_size: Decimal
    min_notional: Decimal
    maker_fee: Decimal
    taker_fee: Decimal
    is_spot_trading_allowed: bool
    is_margin_trading_allowed: bool
    is_futures_trading_allowed: bool
    created_at: datetime
    updated_at: datetime

# Pydantic Models
class AdminLoginRequest(BaseModel):
    username: str
    password: str
    two_factor_code: Optional[str] = None

class CreateAdminRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: AdminRole
    permissions: List[str]

class UpdateUserStatusRequest(BaseModel):
    user_id: str
    status: UserStatus
    reason: str
    duration_hours: Optional[int] = None

class TradingControlRequest(BaseModel):
    action: str  # HALT, RESUME, RESTRICT
    symbol: Optional[str] = None
    reason: str
    duration_minutes: Optional[int] = None

class RiskParametersRequest(BaseModel):
    max_position_size: Optional[Decimal] = None
    max_daily_volume: Optional[Decimal] = None
    max_withdrawal_amount: Optional[Decimal] = None
    price_deviation_threshold: Optional[float] = None

class ComplianceActionRequest(BaseModel):
    user_id: str
    action_type: ActionType
    reason: str
    additional_data: Optional[Dict[str, Any]] = None

class SystemConfigRequest(BaseModel):
    config_key: str
    config_value: Any
    description: Optional[str] = None

class BulkUserActionRequest(BaseModel):
    user_ids: List[str]
    action: str
    reason: str
    parameters: Optional[Dict[str, Any]] = None

# Database connection
async def get_db_connection():
    return await asyncpg.connect(config.DATABASE_URL)

# Redis connection
async def get_redis_connection():
    return await redis.from_url(config.REDIS_URL)

# Admin Panel Manager
class AdminPanelManager:
    def __init__(self):
        self.fraud_detector = self.load_fraud_detection_model()
        self.kafka_producer = self.initialize_kafka_producer()
        self.s3_client = self.initialize_s3_client()
        self.twilio_client = self.initialize_twilio_client()
    
    def load_fraud_detection_model(self):
        """Load ML model for fraud detection"""
        try:
            return IsolationForest(contamination=0.1, random_state=42)
        except Exception as e:
            logger.error(f"Failed to load fraud detection model: {e}")
            return None
    
    def initialize_kafka_producer(self):
        """Initialize Kafka producer"""
        try:
            return KafkaProducer(
                bootstrap_servers=config.KAFKA_BROKERS,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
        except Exception as e:
            logger.error(f"Failed to initialize Kafka producer: {e}")
            return None
    
    def initialize_s3_client(self):
        """Initialize S3 client"""
        try:
            return boto3.client(
                's3',
                aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY
            )
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            return None
    
    def initialize_twilio_client(self):
        """Initialize Twilio client"""
        try:
            if config.TWILIO_ACCOUNT_SID and config.TWILIO_AUTH_TOKEN:
                return TwilioClient(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
        except Exception as e:
            logger.error(f"Failed to initialize Twilio client: {e}")
            return None
    
    async def authenticate_admin(self, username: str, password: str, two_factor_code: Optional[str] = None) -> Optional[AdminUser]:
        """Authenticate admin user"""
        db = await get_db_connection()
        try:
            row = await db.fetchrow("""
                SELECT * FROM admin_users WHERE username = $1 AND is_active = true
            """, username)
            
            if not row:
                return None
            
            admin = AdminUser(**dict(row))
            
            # Verify password
            if not bcrypt.checkpw(password.encode('utf-8'), admin.password_hash.encode('utf-8')):
                return None
            
            # Check 2FA if enabled
            if admin.two_factor_enabled:
                if not two_factor_code:
                    raise HTTPException(status_code=400, detail="Two-factor authentication required")
                
                if not self.verify_2fa_code(admin.two_factor_secret, two_factor_code):
                    return None
            
            # Generate session token
            session_token = secrets.token_urlsafe(32)
            session_expires = datetime.utcnow() + timedelta(seconds=config.ADMIN_SESSION_TIMEOUT)
            
            await db.execute("""
                UPDATE admin_users 
                SET session_token = $1, session_expires = $2, last_login = $3
                WHERE id = $4
            """, session_token, session_expires, datetime.utcnow(), admin.id)
            
            admin.session_token = session_token
            admin.session_expires = session_expires
            admin.last_login = datetime.utcnow()
            
            return admin
            
        finally:
            await db.close()
    
    def verify_2fa_code(self, secret: str, code: str) -> bool:
        """Verify 2FA code"""
        import pyotp
        totp = pyotp.TOTP(secret)
        return totp.verify(code)
    
    async def get_user_analytics(self, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get comprehensive user analytics"""
        db = await get_db_connection()
        try:
            # Total users
            total_users = await db.fetchval("SELECT COUNT(*) FROM users")
            
            # Active users (logged in last 30 days)
            active_users = await db.fetchval("""
                SELECT COUNT(*) FROM users 
                WHERE last_login >= $1
            """, datetime.utcnow() - timedelta(days=30))
            
            # New users (registered last 30 days)
            new_users = await db.fetchval("""
                SELECT COUNT(*) FROM users 
                WHERE created_at >= $1
            """, datetime.utcnow() - timedelta(days=30))
            
            # KYC statistics
            kyc_stats = await db.fetch("""
                SELECT kyc_status, COUNT(*) as count
                FROM users 
                GROUP BY kyc_status
            """)
            
            # Trading volume by user tier
            volume_stats = await db.fetch("""
                SELECT vip_level, SUM(total_trading_volume) as volume, COUNT(*) as users
                FROM users 
                GROUP BY vip_level
                ORDER BY vip_level
            """)
            
            # Geographic distribution
            geo_stats = await db.fetch("""
                SELECT country, COUNT(*) as count
                FROM users 
                WHERE country IS NOT NULL
                GROUP BY country
                ORDER BY count DESC
                LIMIT 20
            """)
            
            return {
                "total_users": total_users,
                "active_users": active_users,
                "new_users": new_users,
                "kyc_statistics": [dict(row) for row in kyc_stats],
                "volume_statistics": [dict(row) for row in volume_stats],
                "geographic_distribution": [dict(row) for row in geo_stats]
            }
            
        finally:
            await db.close()
    
    async def get_trading_analytics(self) -> Dict[str, Any]:
        """Get comprehensive trading analytics"""
        db = await get_db_connection()
        try:
            # Total trading volume (24h)
            volume_24h = await db.fetchval("""
                SELECT COALESCE(SUM(quantity * price), 0)
                FROM trades 
                WHERE timestamp >= $1
            """, datetime.utcnow() - timedelta(hours=24))
            
            # Total trades (24h)
            trades_24h = await db.fetchval("""
                SELECT COUNT(*)
                FROM trades 
                WHERE timestamp >= $1
            """, datetime.utcnow() - timedelta(hours=24))
            
            # Top trading pairs
            top_pairs = await db.fetch("""
                SELECT symbol, 
                       COUNT(*) as trade_count,
                       SUM(quantity * price) as volume
                FROM trades 
                WHERE timestamp >= $1
                GROUP BY symbol
                ORDER BY volume DESC
                LIMIT 10
            """, datetime.utcnow() - timedelta(hours=24))
            
            # Active orders
            active_orders = await db.fetchval("""
                SELECT COUNT(*) FROM orders 
                WHERE status IN ('NEW', 'PARTIALLY_FILLED')
            """)
            
            # Fee revenue (24h)
            fee_revenue = await db.fetchval("""
                SELECT COALESCE(SUM(commission), 0)
                FROM trades 
                WHERE timestamp >= $1
            """, datetime.utcnow() - timedelta(hours=24))
            
            return {
                "volume_24h": str(volume_24h),
                "trades_24h": trades_24h,
                "top_trading_pairs": [dict(row) for row in top_pairs],
                "active_orders": active_orders,
                "fee_revenue_24h": str(fee_revenue)
            }
            
        finally:
            await db.close()
    
    async def get_risk_metrics(self) -> Dict[str, Any]:
        """Get comprehensive risk metrics"""
        db = await get_db_connection()
        try:
            # High-risk users
            high_risk_users = await db.fetch("""
                SELECT user_id, risk_score, total_trading_volume
                FROM users 
                WHERE risk_score > 0.8
                ORDER BY risk_score DESC
                LIMIT 20
            """)
            
            # Large positions
            large_positions = await db.fetch("""
                SELECT user_id, symbol, size, mark_price, unrealized_pnl
                FROM positions 
                WHERE ABS(size * mark_price) > 100000
                ORDER BY ABS(size * mark_price) DESC
                LIMIT 20
            """)
            
            # Liquidation risks
            liquidation_risks = await db.fetch("""
                SELECT user_id, symbol, ltv, liquidation_threshold
                FROM loans 
                WHERE status = 'ACTIVE' AND ltv > liquidation_threshold * 0.9
                ORDER BY ltv DESC
                LIMIT 20
            """)
            
            # Suspicious activities
            suspicious_activities = await db.fetch("""
                SELECT user_id, activity_type, risk_score, timestamp
                FROM suspicious_activities 
                WHERE timestamp >= $1
                ORDER BY risk_score DESC
                LIMIT 50
            """, datetime.utcnow() - timedelta(hours=24))
            
            return {
                "high_risk_users": [dict(row) for row in high_risk_users],
                "large_positions": [dict(row) for row in large_positions],
                "liquidation_risks": [dict(row) for row in liquidation_risks],
                "suspicious_activities": [dict(row) for row in suspicious_activities]
            }
            
        finally:
            await db.close()
    
    async def update_user_status(self, request: UpdateUserStatusRequest, admin_id: str) -> bool:
        """Update user status with audit trail"""
        db = await get_db_connection()
        try:
            # Update user status
            await db.execute("""
                UPDATE users 
                SET user_status = $1, updated_at = $2
                WHERE user_id = $3
            """, request.status.value, datetime.utcnow(), request.user_id)
            
            # Create audit log
            await db.execute("""
                INSERT INTO admin_actions (id, admin_id, action_type, target_user_id, 
                                         details, reason, timestamp)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, str(uuid.uuid4()), admin_id, "USER_STATUS_UPDATE", request.user_id,
                json.dumps({"new_status": request.status.value}), request.reason, datetime.utcnow())
            
            # Send notification to user
            await self.send_user_notification(request.user_id, "status_update", {
                "new_status": request.status.value,
                "reason": request.reason
            })
            
            # Publish event
            if self.kafka_producer:
                self.kafka_producer.send('admin-actions', {
                    "action": "user_status_update",
                    "user_id": request.user_id,
                    "new_status": request.status.value,
                    "admin_id": admin_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating user status: {e}")
            return False
        finally:
            await db.close()
    
    async def control_trading(self, request: TradingControlRequest, admin_id: str) -> bool:
        """Control trading operations"""
        db = await get_db_connection()
        redis_conn = await get_redis_connection()
        
        try:
            if request.action == "HALT":
                # Halt trading for symbol or globally
                if request.symbol:
                    await redis_conn.set(f"trading_halt:{request.symbol}", "true", ex=request.duration_minutes * 60 if request.duration_minutes else None)
                else:
                    await redis_conn.set("trading_halt:global", "true", ex=request.duration_minutes * 60 if request.duration_minutes else None)
                
                # Cancel all open orders for the symbol
                if request.symbol:
                    await db.execute("""
                        UPDATE orders 
                        SET status = 'CANCELLED', updated_time = $1
                        WHERE symbol = $2 AND status IN ('NEW', 'PARTIALLY_FILLED')
                    """, datetime.utcnow(), request.symbol)
            
            elif request.action == "RESUME":
                # Resume trading
                if request.symbol:
                    await redis_conn.delete(f"trading_halt:{request.symbol}")
                else:
                    await redis_conn.delete("trading_halt:global")
            
            elif request.action == "RESTRICT":
                # Restrict trading (allow only closing positions)
                if request.symbol:
                    await redis_conn.set(f"trading_restrict:{request.symbol}", "true", ex=request.duration_minutes * 60 if request.duration_minutes else None)
                else:
                    await redis_conn.set("trading_restrict:global", "true", ex=request.duration_minutes * 60 if request.duration_minutes else None)
            
            # Create audit log
            await db.execute("""
                INSERT INTO admin_actions (id, admin_id, action_type, details, reason, timestamp)
                VALUES ($1, $2, $3, $4, $5, $6)
            """, str(uuid.uuid4()), admin_id, "TRADING_CONTROL",
                json.dumps({"action": request.action, "symbol": request.symbol}), request.reason, datetime.utcnow())
            
            # Publish event
            if self.kafka_producer:
                self.kafka_producer.send('trading-control', {
                    "action": request.action,
                    "symbol": request.symbol,
                    "reason": request.reason,
                    "admin_id": admin_id,
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            return True
            
        except Exception as e:
            logger.error(f"Error controlling trading: {e}")
            return False
        finally:
            await db.close()
            await redis_conn.close()
    
    async def update_risk_parameters(self, request: RiskParametersRequest, admin_id: str) -> bool:
        """Update system risk parameters"""
        db = await get_db_connection()
        redis_conn = await get_redis_connection()
        
        try:
            # Update risk parameters in Redis
            risk_params = {}
            if request.max_position_size is not None:
                risk_params["max_position_size"] = str(request.max_position_size)
            if request.max_daily_volume is not None:
                risk_params["max_daily_volume"] = str(request.max_daily_volume)
            if request.max_withdrawal_amount is not None:
                risk_params["max_withdrawal_amount"] = str(request.max_withdrawal_amount)
            if request.price_deviation_threshold is not None:
                risk_params["price_deviation_threshold"] = str(request.price_deviation_threshold)
            
            for key, value in risk_params.items():
                await redis_conn.set(f"risk_param:{key}", value)
            
            # Create audit log
            await db.execute("""
                INSERT INTO admin_actions (id, admin_id, action_type, details, timestamp)
                VALUES ($1, $2, $3, $4, $5)
            """, str(uuid.uuid4()), admin_id, "RISK_PARAMETERS_UPDATE",
                json.dumps(risk_params), datetime.utcnow())
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating risk parameters: {e}")
            return False
        finally:
            await db.close()
            await redis_conn.close()
    
    async def perform_compliance_action(self, request: ComplianceActionRequest, admin_id: str) -> bool:
        """Perform compliance action on user"""
        db = await get_db_connection()
        
        try:
            # Execute compliance action based on type
            if request.action_type == ActionType.USER_SUSPENSION:
                await db.execute("""
                    UPDATE users 
                    SET user_status = 'SUSPENDED', updated_at = $1
                    WHERE user_id = $2
                """, datetime.utcnow(), request.user_id)
            
            elif request.action_type == ActionType.WITHDRAWAL_FREEZE:
                await db.execute("""
                    UPDATE users 
                    SET withdrawal_enabled = false, updated_at = $1
                    WHERE user_id = $2
                """, datetime.utcnow(), request.user_id)
            
            elif request.action_type == ActionType.KYC_REVIEW:
                await db.execute("""
                    UPDATE users 
                    SET kyc_status = 'UNDER_REVIEW', updated_at = $1
                    WHERE user_id = $2
                """, datetime.utcnow(), request.user_id)
            
            # Create compliance case
            case_id = str(uuid.uuid4())
            await db.execute("""
                INSERT INTO compliance_cases (id, user_id, case_type, status, 
                                            assigned_to, details, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, case_id, request.user_id, request.action_type.value, "OPEN",
                admin_id, json.dumps(request.additional_data or {}), datetime.utcnow())
            
            # Create audit log
            await db.execute("""
                INSERT INTO admin_actions (id, admin_id, action_type, target_user_id, 
                                         details, reason, timestamp)
                VALUES ($1, $2, $3, $4, $5, $6, $7)
            """, str(uuid.uuid4()), admin_id, request.action_type.value, request.user_id,
                json.dumps(request.additional_data or {}), request.reason, datetime.utcnow())
            
            return True
            
        except Exception as e:
            logger.error(f"Error performing compliance action: {e}")
            return False
        finally:
            await db.close()
    
    async def generate_system_report(self, report_type: str, start_date: datetime, end_date: datetime) -> bytes:
        """Generate comprehensive system reports"""
        db = await get_db_connection()
        
        try:
            if report_type == "trading_summary":
                data = await db.fetch("""
                    SELECT DATE(timestamp) as date,
                           symbol,
                           COUNT(*) as trade_count,
                           SUM(quantity) as total_quantity,
                           SUM(quantity * price) as total_volume,
                           SUM(commission) as total_fees
                    FROM trades 
                    WHERE timestamp BETWEEN $1 AND $2
                    GROUP BY DATE(timestamp), symbol
                    ORDER BY date, total_volume DESC
                """, start_date, end_date)
            
            elif report_type == "user_activity":
                data = await db.fetch("""
                    SELECT DATE(created_at) as date,
                           COUNT(*) as new_users,
                           COUNT(CASE WHEN kyc_status = 'APPROVED' THEN 1 END) as verified_users,
                           COUNT(CASE WHEN last_login >= $1 THEN 1 END) as active_users
                    FROM users 
                    WHERE created_at BETWEEN $1 AND $2
                    GROUP BY DATE(created_at)
                    ORDER BY date
                """, start_date, end_date)
            
            elif report_type == "compliance_summary":
                data = await db.fetch("""
                    SELECT DATE(created_at) as date,
                           case_type,
                           status,
                           COUNT(*) as case_count
                    FROM compliance_cases 
                    WHERE created_at BETWEEN $1 AND $2
                    GROUP BY DATE(created_at), case_type, status
                    ORDER BY date
                """, start_date, end_date)
            
            # Convert to DataFrame and generate Excel report
            df = pd.DataFrame([dict(row) for row in data])
            
            # Create Excel file in memory
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name=report_type, index=False)
                
                # Add charts and formatting
                workbook = writer.book
                worksheet = writer.sheets[report_type]
                
                # Format headers
                header_format = workbook.add_format({
                    'bold': True,
                    'text_wrap': True,
                    'valign': 'top',
                    'fg_color': '#D7E4BC',
                    'border': 1
                })
                
                for col_num, value in enumerate(df.columns.values):
                    worksheet.write(0, col_num, value, header_format)
            
            output.seek(0)
            return output.getvalue()
            
        finally:
            await db.close()
    
    async def send_user_notification(self, user_id: str, notification_type: str, data: Dict[str, Any]):
        """Send notification to user"""
        try:
            # Get user contact info
            db = await get_db_connection()
            user_info = await db.fetchrow("""
                SELECT email, phone FROM users WHERE user_id = $1
            """, user_id)
            await db.close()
            
            if not user_info:
                return
            
            # Send email notification
            if user_info['email'] and config.SMTP_USERNAME:
                await self.send_email_notification(user_info['email'], notification_type, data)
            
            # Send SMS notification for critical alerts
            if user_info['phone'] and notification_type in ['security_alert', 'account_suspended'] and self.twilio_client:
                await self.send_sms_notification(user_info['phone'], notification_type, data)
            
        except Exception as e:
            logger.error(f"Error sending user notification: {e}")
    
    async def send_email_notification(self, email: str, notification_type: str, data: Dict[str, Any]):
        """Send email notification"""
        try:
            msg = MIMEMultipart()
            msg['From'] = config.SMTP_USERNAME
            msg['To'] = email
            msg['Subject'] = f"TigerEx Account Notification - {notification_type.replace('_', ' ').title()}"
            
            # Create email body based on notification type
            if notification_type == "status_update":
                body = f"""
                Dear User,
                
                Your account status has been updated to: {data.get('new_status')}
                Reason: {data.get('reason')}
                
                If you have any questions, please contact our support team.
                
                Best regards,
                TigerEx Team
                """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(config.SMTP_HOST, config.SMTP_PORT)
            server.starttls()
            server.login(config.SMTP_USERNAME, config.SMTP_PASSWORD)
            server.send_message(msg)
            server.quit()
            
        except Exception as e:
            logger.error(f"Error sending email: {e}")
    
    async def send_sms_notification(self, phone: str, notification_type: str, data: Dict[str, Any]):
        """Send SMS notification"""
        try:
            if self.twilio_client:
                message = f"TigerEx Alert: {notification_type.replace('_', ' ').title()}. Check your account for details."
                
                self.twilio_client.messages.create(
                    body=message,
                    from_=config.TWILIO_PHONE_NUMBER,
                    to=phone
                )
                
        except Exception as e:
            logger.error(f"Error sending SMS: {e}")

# Initialize admin panel manager
admin_manager = AdminPanelManager()

# Authentication dependency
async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated admin"""
    token = credentials.credentials
    
    db = await get_db_connection()
    try:
        admin_row = await db.fetchrow("""
            SELECT * FROM admin_users 
            WHERE session_token = $1 AND session_expires > $2 AND is_active = true
        """, token, datetime.utcnow())
        
        if not admin_row:
            raise HTTPException(status_code=401, detail="Invalid or expired session")
        
        return AdminUser(**dict(admin_row))
        
    finally:
        await db.close()

# API Endpoints

@app.post("/api/v1/admin/auth/login")
async def admin_login(request: AdminLoginRequest):
    """Admin login endpoint"""
    try:
        admin = await admin_manager.authenticate_admin(
            request.username, 
            request.password, 
            request.two_factor_code
        )
        
        if not admin:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        return {
            "access_token": admin.session_token,
            "token_type": "bearer",
            "expires_in": config.ADMIN_SESSION_TIMEOUT,
            "admin_info": {
                "id": admin.id,
                "username": admin.username,
                "email": admin.email,
                "role": admin.role.value,
                "permissions": admin.permissions
            }
        }
        
    except Exception as e:
        logger.error(f"Admin login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@app.post("/api/v1/admin/auth/logout")
async def admin_logout(current_admin: AdminUser = Depends(get_current_admin)):
    """Admin logout endpoint"""
    db = await get_db_connection()
    try:
        await db.execute("""
            UPDATE admin_users 
            SET session_token = NULL, session_expires = NULL
            WHERE id = $1
        """, current_admin.id)
        
        return {"message": "Logged out successfully"}
        
    finally:
        await db.close()

@app.get("/api/v1/admin/dashboard/overview")
async def get_dashboard_overview(current_admin: AdminUser = Depends(get_current_admin)):
    """Get dashboard overview data"""
    try:
        user_analytics = await admin_manager.get_user_analytics()
        trading_analytics = await admin_manager.get_trading_analytics()
        risk_metrics = await admin_manager.get_risk_metrics()
        
        return {
            "user_analytics": user_analytics,
            "trading_analytics": trading_analytics,
            "risk_metrics": risk_metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard overview: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard data")

@app.get("/api/v1/admin/users")
async def get_users(
    page: int = 1,
    limit: int = 50,
    status: Optional[UserStatus] = None,
    kyc_status: Optional[KYCStatus] = None,
    search: Optional[str] = None,
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Get users with filtering and pagination"""
    db = await get_db_connection()
    try:
        offset = (page - 1) * limit
        
        # Build query
        query = "SELECT * FROM users WHERE 1=1"
        params = []
        param_count = 0
        
        if status:
            param_count += 1
            query += f" AND user_status = ${param_count}"
            params.append(status.value)
        
        if kyc_status:
            param_count += 1
            query += f" AND kyc_status = ${param_count}"
            params.append(kyc_status.value)
        
        if search:
            param_count += 1
            query += f" AND (email ILIKE ${param_count} OR first_name ILIKE ${param_count} OR last_name ILIKE ${param_count})"
            params.append(f"%{search}%")
        
        query += f" ORDER BY created_at DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
        params.extend([limit, offset])
        
        users = await db.fetch(query, *params)
        
        # Get total count
        count_query = query.split("ORDER BY")[0].replace("SELECT *", "SELECT COUNT(*)")
        total_count = await db.fetchval(count_query, *params[:-2])
        
        return {
            "users": [dict(user) for user in users],
            "total_count": total_count,
            "page": page,
            "limit": limit,
            "total_pages": (total_count + limit - 1) // limit
        }
        
    finally:
        await db.close()

@app.get("/api/v1/admin/users/{user_id}")
async def get_user_details(
    user_id: str,
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Get detailed user information"""
    db = await get_db_connection()
    try:
        # Get user info
        user = await db.fetchrow("SELECT * FROM users WHERE user_id = $1", user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Get user balances
        balances = await db.fetch("""
            SELECT asset, free, locked, total 
            FROM user_balances 
            WHERE user_id = $1
        """, user_id)
        
        # Get recent trades
        trades = await db.fetch("""
            SELECT * FROM trades 
            WHERE buyer_id = $1 OR seller_id = $1
            ORDER BY timestamp DESC 
            LIMIT 20
        """, user_id)
        
        # Get open orders
        orders = await db.fetch("""
            SELECT * FROM orders 
            WHERE user_id = $1 AND status IN ('NEW', 'PARTIALLY_FILLED')
            ORDER BY created_time DESC
        """, user_id)
        
        # Get compliance cases
        compliance_cases = await db.fetch("""
            SELECT * FROM compliance_cases 
            WHERE user_id = $1
            ORDER BY created_at DESC
        """, user_id)
        
        return {
            "user": dict(user),
            "balances": [dict(balance) for balance in balances],
            "recent_trades": [dict(trade) for trade in trades],
            "open_orders": [dict(order) for order in orders],
            "compliance_cases": [dict(case) for case in compliance_cases]
        }
        
    finally:
        await db.close()

@app.put("/api/v1/admin/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    request: UpdateUserStatusRequest,
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Update user status"""
    request.user_id = user_id
    success = await admin_manager.update_user_status(request, current_admin.id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update user status")
    
    return {"message": "User status updated successfully"}

@app.post("/api/v1/admin/trading/control")
async def control_trading(
    request: TradingControlRequest,
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Control trading operations"""
    if "TRADING_MANAGER" not in current_admin.permissions and current_admin.role != AdminRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    success = await admin_manager.control_trading(request, current_admin.id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to control trading")
    
    return {"message": f"Trading {request.action.lower()} executed successfully"}

@app.get("/api/v1/admin/trading/pairs")
async def get_trading_pairs(current_admin: AdminUser = Depends(get_current_admin)):
    """Get all trading pairs"""
    db = await get_db_connection()
    try:
        pairs = await db.fetch("SELECT * FROM trading_pairs ORDER BY symbol")
        return {"trading_pairs": [dict(pair) for pair in pairs]}
    finally:
        await db.close()

@app.post("/api/v1/admin/trading/pairs")
async def create_trading_pair(
    pair_data: dict,
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Create new trading pair"""
    if "TRADING_MANAGER" not in current_admin.permissions and current_admin.role != AdminRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    db = await get_db_connection()
    try:
        await db.execute("""
            INSERT INTO trading_pairs (symbol, base_asset, quote_asset, status, 
                                     min_qty, max_qty, step_size, min_price, max_price, 
                                     tick_size, min_notional, maker_fee, taker_fee,
                                     is_spot_trading_allowed, is_margin_trading_allowed,
                                     is_futures_trading_allowed, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
        """, 
            pair_data['symbol'], pair_data['base_asset'], pair_data['quote_asset'],
            pair_data.get('status', 'ACTIVE'), pair_data['min_qty'], pair_data.get('max_qty'),
            pair_data['step_size'], pair_data['min_price'], pair_data.get('max_price'),
            pair_data['tick_size'], pair_data['min_notional'], pair_data['maker_fee'],
            pair_data['taker_fee'], pair_data.get('is_spot_trading_allowed', True),
            pair_data.get('is_margin_trading_allowed', False), 
            pair_data.get('is_futures_trading_allowed', False),
            datetime.utcnow(), datetime.utcnow()
        )
        
        return {"message": "Trading pair created successfully"}
        
    finally:
        await db.close()

@app.put("/api/v1/admin/risk/parameters")
async def update_risk_parameters(
    request: RiskParametersRequest,
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Update risk management parameters"""
    if "RISK_MANAGER" not in current_admin.permissions and current_admin.role != AdminRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    success = await admin_manager.update_risk_parameters(request, current_admin.id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update risk parameters")
    
    return {"message": "Risk parameters updated successfully"}

@app.post("/api/v1/admin/compliance/action")
async def perform_compliance_action(
    request: ComplianceActionRequest,
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Perform compliance action"""
    if "COMPLIANCE_OFFICER" not in current_admin.permissions and current_admin.role != AdminRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    success = await admin_manager.perform_compliance_action(request, current_admin.id)
    
    if not success:
        raise HTTPException(status_code=500, detail="Failed to perform compliance action")
    
    return {"message": "Compliance action performed successfully"}

@app.get("/api/v1/admin/compliance/cases")
async def get_compliance_cases(
    page: int = 1,
    limit: int = 50,
    status: Optional[str] = None,
    case_type: Optional[str] = None,
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Get compliance cases"""
    db = await get_db_connection()
    try:
        offset = (page - 1) * limit
        
        query = "SELECT * FROM compliance_cases WHERE 1=1"
        params = []
        param_count = 0
        
        if status:
            param_count += 1
            query += f" AND status = ${param_count}"
            params.append(status)
        
        if case_type:
            param_count += 1
            query += f" AND case_type = ${param_count}"
            params.append(case_type)
        
        query += f" ORDER BY created_at DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
        params.extend([limit, offset])
        
        cases = await db.fetch(query, *params)
        
        return {
            "cases": [dict(case) for case in cases],
            "page": page,
            "limit": limit
        }
        
    finally:
        await db.close()

@app.get("/api/v1/admin/reports/generate")
async def generate_report(
    report_type: str,
    start_date: str,
    end_date: str,
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Generate system reports"""
    try:
        start_dt = datetime.fromisoformat(start_date)
        end_dt = datetime.fromisoformat(end_date)
        
        report_data = await admin_manager.generate_system_report(report_type, start_dt, end_dt)
        
        return StreamingResponse(
            io.BytesIO(report_data),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={report_type}_{start_date}_{end_date}.xlsx"}
        )
        
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate report")

@app.get("/api/v1/admin/analytics/charts")
async def get_analytics_charts(
    chart_type: str,
    period: str = "7d",
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Get analytics charts data"""
    db = await get_db_connection()
    try:
        if chart_type == "trading_volume":
            # Get trading volume over time
            if period == "7d":
                data = await db.fetch("""
                    SELECT DATE(timestamp) as date, SUM(quantity * price) as volume
                    FROM trades 
                    WHERE timestamp >= $1
                    GROUP BY DATE(timestamp)
                    ORDER BY date
                """, datetime.utcnow() - timedelta(days=7))
            
        elif chart_type == "user_growth":
            # Get user registration growth
            data = await db.fetch("""
                SELECT DATE(created_at) as date, COUNT(*) as new_users
                FROM users 
                WHERE created_at >= $1
                GROUP BY DATE(created_at)
                ORDER BY date
            """, datetime.utcnow() - timedelta(days=30))
        
        elif chart_type == "fee_revenue":
            # Get fee revenue over time
            data = await db.fetch("""
                SELECT DATE(timestamp) as date, SUM(commission) as revenue
                FROM trades 
                WHERE timestamp >= $1
                GROUP BY DATE(timestamp)
                ORDER BY date
            """, datetime.utcnow() - timedelta(days=30))
        
        return {"chart_data": [dict(row) for row in data]}
        
    finally:
        await db.close()

@app.post("/api/v1/admin/users/bulk-action")
async def bulk_user_action(
    request: BulkUserActionRequest,
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Perform bulk action on multiple users"""
    if current_admin.role != AdminRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Super admin access required")
    
    db = await get_db_connection()
    try:
        success_count = 0
        
        for user_id in request.user_ids:
            try:
                if request.action == "SUSPEND":
                    await db.execute("""
                        UPDATE users 
                        SET user_status = 'SUSPENDED', updated_at = $1
                        WHERE user_id = $2
                    """, datetime.utcnow(), user_id)
                
                elif request.action == "ACTIVATE":
                    await db.execute("""
                        UPDATE users 
                        SET user_status = 'ACTIVE', updated_at = $1
                        WHERE user_id = $2
                    """, datetime.utcnow(), user_id)
                
                # Create audit log
                await db.execute("""
                    INSERT INTO admin_actions (id, admin_id, action_type, target_user_id, 
                                             details, reason, timestamp)
                    VALUES ($1, $2, $3, $4, $5, $6, $7)
                """, str(uuid.uuid4()), current_admin.id, f"BULK_{request.action}", 
                    user_id, json.dumps(request.parameters or {}), request.reason, datetime.utcnow())
                
                success_count += 1
                
            except Exception as e:
                logger.error(f"Error processing user {user_id}: {e}")
        
        return {
            "message": f"Bulk action completed",
            "total_users": len(request.user_ids),
            "successful": success_count,
            "failed": len(request.user_ids) - success_count
        }
        
    finally:
        await db.close()

@app.get("/api/v1/admin/system/alerts")
async def get_system_alerts(
    page: int = 1,
    limit: int = 50,
    severity: Optional[AlertSeverity] = None,
    alert_type: Optional[AlertType] = None,
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Get system alerts"""
    db = await get_db_connection()
    try:
        offset = (page - 1) * limit
        
        query = "SELECT * FROM system_alerts WHERE 1=1"
        params = []
        param_count = 0
        
        if severity:
            param_count += 1
            query += f" AND severity = ${param_count}"
            params.append(severity.value)
        
        if alert_type:
            param_count += 1
            query += f" AND alert_type = ${param_count}"
            params.append(alert_type.value)
        
        query += f" ORDER BY created_at DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
        params.extend([limit, offset])
        
        alerts = await db.fetch(query, *params)
        
        return {
            "alerts": [dict(alert) for alert in alerts],
            "page": page,
            "limit": limit
        }
        
    finally:
        await db.close()

@app.put("/api/v1/admin/system/alerts/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    resolution_notes: str,
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Resolve system alert"""
    db = await get_db_connection()
    try:
        await db.execute("""
            UPDATE system_alerts 
            SET is_resolved = true, resolved_at = $1, resolved_by = $2,
                resolution_notes = $3
            WHERE id = $4
        """, datetime.utcnow(), current_admin.id, resolution_notes, alert_id)
        
        return {"message": "Alert resolved successfully"}
        
    finally:
        await db.close()

@app.get("/api/v1/admin/audit/logs")
async def get_audit_logs(
    page: int = 1,
    limit: int = 50,
    admin_id: Optional[str] = None,
    action_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_admin: AdminUser = Depends(get_current_admin)
):
    """Get audit logs"""
    db = await get_db_connection()
    try:
        offset = (page - 1) * limit
        
        query = "SELECT * FROM admin_actions WHERE 1=1"
        params = []
        param_count = 0
        
        if admin_id:
            param_count += 1
            query += f" AND admin_id = ${param_count}"
            params.append(admin_id)
        
        if action_type:
            param_count += 1
            query += f" AND action_type = ${param_count}"
            params.append(action_type)
        
        if start_date:
            param_count += 1
            query += f" AND timestamp >= ${param_count}"
            params.append(datetime.fromisoformat(start_date))
        
        if end_date:
            param_count += 1
            query += f" AND timestamp <= ${param_count}"
            params.append(datetime.fromisoformat(end_date))
        
        query += f" ORDER BY timestamp DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
        params.extend([limit, offset])
        
        logs = await db.fetch(query, *params)
        
        return {
            "audit_logs": [dict(log) for log in logs],
            "page": page,
            "limit": limit
        }
        
    finally:
        await db.close()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8093)