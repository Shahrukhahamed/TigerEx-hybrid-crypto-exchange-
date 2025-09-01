"""
TigerEx Affiliate & Referral System
Comprehensive affiliate marketing platform with multi-tier commissions and regional partnerships
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
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, DECIMAL, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="TigerEx Affiliate & Referral System",
    description="Comprehensive affiliate marketing platform with multi-tier commissions and regional partnerships",
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
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "affiliate-secret-key")

config = Config()

# Database setup
engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

security = HTTPBearer()

# Enums
class AffiliateType(str, Enum):
    INDIVIDUAL = "individual"
    COMPANY = "company"
    REGIONAL_PARTNER = "regional_partner"
    INFLUENCER = "influencer"
    INSTITUTIONAL = "institutional"

class AffiliateStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"

class CommissionType(str, Enum):
    TRADING_FEE = "trading_fee"
    DEPOSIT_FEE = "deposit_fee"
    WITHDRAWAL_FEE = "withdrawal_fee"
    FUTURES_FEE = "futures_fee"
    OPTIONS_FEE = "options_fee"
    P2P_FEE = "p2p_fee"
    NFT_FEE = "nft_fee"
    COPY_TRADING_FEE = "copy_trading_fee"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ReferralTier(str, Enum):
    TIER_1 = "tier_1"  # Direct referrals
    TIER_2 = "tier_2"  # Referrals of referrals
    TIER_3 = "tier_3"  # Third level
    TIER_4 = "tier_4"  # Fourth level
    TIER_5 = "tier_5"  # Fifth level

# Database Models
class Affiliate(Base):
    __tablename__ = "affiliates"
    
    id = Column(Integer, primary_key=True, index=True)
    affiliate_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Basic Info
    user_id = Column(String(50), nullable=False, index=True)
    affiliate_type = Column(SQLEnum(AffiliateType), nullable=False)
    
    # Personal/Company Info
    first_name = Column(String(100))
    last_name = Column(String(100))
    company_name = Column(String(200))
    email = Column(String(255), nullable=False)
    phone_number = Column(String(20))
    
    # Address
    country = Column(String(3), nullable=False)
    state_province = Column(String(100))
    city = Column(String(100))
    address_line1 = Column(String(200))
    address_line2 = Column(String(200))
    postal_code = Column(String(20))
    
    # Business Info
    business_registration = Column(String(100))
    tax_id = Column(String(50))
    website_url = Column(String(500))
    social_media_links = Column(JSON)
    
    # Referral Code
    referral_code = Column(String(20), unique=True, nullable=False, index=True)
    custom_referral_code = Column(String(50), unique=True)
    
    # Commission Structure
    base_commission_rate = Column(DECIMAL(5, 4), default=0.2)  # 20%
    tier_1_rate = Column(DECIMAL(5, 4), default=0.2)  # 20%
    tier_2_rate = Column(DECIMAL(5, 4), default=0.1)  # 10%
    tier_3_rate = Column(DECIMAL(5, 4), default=0.05)  # 5%
    tier_4_rate = Column(DECIMAL(5, 4), default=0.025)  # 2.5%
    tier_5_rate = Column(DECIMAL(5, 4), default=0.01)  # 1%
    
    # Performance Metrics
    total_referrals = Column(Integer, default=0)
    active_referrals = Column(Integer, default=0)
    total_commission_earned = Column(DECIMAL(20, 2), default=0)
    total_commission_paid = Column(DECIMAL(20, 2), default=0)
    pending_commission = Column(DECIMAL(20, 2), default=0)
    
    # Regional Partner Specific
    assigned_regions = Column(JSON)  # List of country codes
    regional_bonus_rate = Column(DECIMAL(5, 4), default=0)
    
    # Payment Info
    payment_method = Column(String(50))
    payment_details = Column(JSON)  # Encrypted payment details
    minimum_payout = Column(DECIMAL(20, 2), default=100)
    
    # Status and Verification
    status = Column(SQLEnum(AffiliateStatus), default=AffiliateStatus.PENDING)
    is_verified = Column(Boolean, default=False)
    verification_documents = Column(JSON)
    
    # Parent Affiliate (for multi-level)
    parent_affiliate_id = Column(String(50), ForeignKey("affiliates.affiliate_id"))
    parent_affiliate = relationship("Affiliate", remote_side=[affiliate_id])
    
    # Audit
    approved_by = Column(String(50))
    approved_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    referrals = relationship("Referral", foreign_keys="Referral.affiliate_id", back_populates="affiliate")
    commissions = relationship("Commission", back_populates="affiliate")
    payouts = relationship("AffiliatePayout", back_populates="affiliate")

class Referral(Base):
    __tablename__ = "referrals"
    
    id = Column(Integer, primary_key=True, index=True)
    referral_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Referral Info
    affiliate_id = Column(String(50), ForeignKey("affiliates.affiliate_id"), nullable=False)
    affiliate = relationship("Affiliate", foreign_keys=[affiliate_id], back_populates="referrals")
    
    referred_user_id = Column(String(50), nullable=False, index=True)
    referred_user_email = Column(String(255), nullable=False)
    
    # Referral Source
    referral_source = Column(String(100))  # website, social_media, email, etc.
    referral_campaign = Column(String(100))
    utm_source = Column(String(100))
    utm_medium = Column(String(100))
    utm_campaign = Column(String(100))
    
    # Conversion Info
    registration_date = Column(DateTime, default=func.now())
    first_deposit_date = Column(DateTime)
    first_trade_date = Column(DateTime)
    kyc_completion_date = Column(DateTime)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_qualified = Column(Boolean, default=False)  # Met minimum requirements
    qualification_date = Column(DateTime)
    
    # Performance
    total_trading_volume = Column(DECIMAL(30, 8), default=0)
    total_fees_generated = Column(DECIMAL(20, 2), default=0)
    total_commission_generated = Column(DECIMAL(20, 2), default=0)
    
    # Multi-level tracking
    tier_level = Column(SQLEnum(ReferralTier), default=ReferralTier.TIER_1)
    original_affiliate_id = Column(String(50))  # The original affiliate who started the chain
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class Commission(Base):
    __tablename__ = "commissions"
    
    id = Column(Integer, primary_key=True, index=True)
    commission_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Commission Info
    affiliate_id = Column(String(50), ForeignKey("affiliates.affiliate_id"), nullable=False)
    affiliate = relationship("Affiliate", back_populates="commissions")
    
    referral_id = Column(String(50), ForeignKey("referrals.referral_id"), nullable=False)
    referred_user_id = Column(String(50), nullable=False)
    
    # Transaction Info
    transaction_id = Column(String(50), nullable=False)
    transaction_type = Column(String(50), nullable=False)  # trade, deposit, withdrawal, etc.
    commission_type = Column(SQLEnum(CommissionType), nullable=False)
    
    # Amounts
    transaction_amount = Column(DECIMAL(30, 8), nullable=False)
    fee_amount = Column(DECIMAL(20, 8), nullable=False)
    commission_rate = Column(DECIMAL(5, 4), nullable=False)
    commission_amount = Column(DECIMAL(20, 8), nullable=False)
    
    # Multi-level info
    tier_level = Column(SQLEnum(ReferralTier), nullable=False)
    original_affiliate_id = Column(String(50))
    
    # Currency
    currency = Column(String(10), default="USDT")
    usd_value = Column(DECIMAL(20, 2))
    
    # Status
    is_paid = Column(Boolean, default=False)
    paid_at = Column(DateTime)
    payout_id = Column(String(50))
    
    created_at = Column(DateTime, default=func.now())

class AffiliatePayout(Base):
    __tablename__ = "affiliate_payouts"
    
    id = Column(Integer, primary_key=True, index=True)
    payout_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Payout Info
    affiliate_id = Column(String(50), ForeignKey("affiliates.affiliate_id"), nullable=False)
    affiliate = relationship("Affiliate", back_populates="payouts")
    
    # Amount Info
    total_amount = Column(DECIMAL(20, 2), nullable=False)
    currency = Column(String(10), default="USDT")
    commission_count = Column(Integer, nullable=False)
    
    # Period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    # Payment Info
    payment_method = Column(String(50), nullable=False)
    payment_details = Column(JSON)
    payment_reference = Column(String(100))
    
    # Status
    status = Column(SQLEnum(PaymentStatus), default=PaymentStatus.PENDING)
    processed_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Fees
    processing_fee = Column(DECIMAL(20, 2), default=0)
    net_amount = Column(DECIMAL(20, 2))
    
    # Notes
    admin_notes = Column(Text)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class AffiliateLink(Base):
    __tablename__ = "affiliate_links"
    
    id = Column(Integer, primary_key=True, index=True)
    link_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Link Info
    affiliate_id = Column(String(50), ForeignKey("affiliates.affiliate_id"), nullable=False)
    
    # Link Details
    link_name = Column(String(100), nullable=False)
    destination_url = Column(String(500), nullable=False)
    tracking_url = Column(String(500), nullable=False)
    
    # Campaign Info
    campaign_name = Column(String(100))
    utm_source = Column(String(100))
    utm_medium = Column(String(100))
    utm_campaign = Column(String(100))
    utm_content = Column(String(100))
    
    # Performance
    click_count = Column(Integer, default=0)
    conversion_count = Column(Integer, default=0)
    conversion_rate = Column(DECIMAL(5, 4), default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class AffiliatePromotion(Base):
    __tablename__ = "affiliate_promotions"
    
    id = Column(Integer, primary_key=True, index=True)
    promotion_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Promotion Info
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    promotion_type = Column(String(50), nullable=False)  # bonus, contest, special_rate
    
    # Targeting
    target_affiliate_types = Column(JSON)  # List of affiliate types
    target_regions = Column(JSON)  # List of country codes
    minimum_tier = Column(String(20))
    
    # Promotion Details
    bonus_rate = Column(DECIMAL(5, 4))  # Additional commission rate
    bonus_amount = Column(DECIMAL(20, 2))  # Fixed bonus amount
    minimum_volume = Column(DECIMAL(30, 8))  # Minimum volume requirement
    
    # Validity
    start_date = Column(DateTime, nullable=False)
    end_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)
    
    # Terms
    terms_and_conditions = Column(Text)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

# Pydantic Models
class AffiliateCreate(BaseModel):
    affiliate_type: AffiliateType
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    company_name: Optional[str] = None
    email: EmailStr
    phone_number: Optional[str] = None
    country: str
    state_province: Optional[str] = None
    city: Optional[str] = None
    address_line1: Optional[str] = None
    website_url: Optional[str] = None
    social_media_links: Optional[Dict[str, str]] = None
    custom_referral_code: Optional[str] = None
    payment_method: str
    payment_details: Dict[str, Any]

class ReferralCreate(BaseModel):
    referred_user_email: EmailStr
    referral_source: Optional[str] = None
    referral_campaign: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None

class LinkCreate(BaseModel):
    link_name: str
    destination_url: str
    campaign_name: Optional[str] = None
    utm_source: Optional[str] = None
    utm_medium: Optional[str] = None
    utm_campaign: Optional[str] = None
    utm_content: Optional[str] = None
    expires_at: Optional[datetime] = None

class PayoutRequest(BaseModel):
    amount: Decimal
    payment_method: str
    payment_details: Dict[str, Any]

# Dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return {"user_id": "user_123", "username": "testuser"}

# Affiliate System Manager
class AffiliateManager:
    def __init__(self):
        self.redis_client = None
        
    async def initialize(self):
        self.redis_client = await aioredis.from_url(config.REDIS_URL)
    
    def generate_referral_code(self, length: int = 8) -> str:
        """Generate unique referral code"""
        return secrets.token_hex(length // 2).upper()
    
    async def create_affiliate(self, affiliate_data: AffiliateCreate, user: Dict[str, Any], db: Session):
        """Create new affiliate"""
        
        # Check if user is already an affiliate
        existing = db.query(Affiliate).filter(Affiliate.user_id == user["user_id"]).first()
        if existing:
            raise HTTPException(status_code=400, detail="User is already an affiliate")
        
        # Generate unique referral code
        referral_code = affiliate_data.custom_referral_code or self.generate_referral_code()
        
        # Check if referral code is unique
        while db.query(Affiliate).filter(Affiliate.referral_code == referral_code).first():
            referral_code = self.generate_referral_code()
        
        affiliate_id = f"AFF_{secrets.token_hex(8).upper()}"
        
        affiliate = Affiliate(
            affiliate_id=affiliate_id,
            user_id=user["user_id"],
            affiliate_type=affiliate_data.affiliate_type,
            first_name=affiliate_data.first_name,
            last_name=affiliate_data.last_name,
            company_name=affiliate_data.company_name,
            email=affiliate_data.email,
            phone_number=affiliate_data.phone_number,
            country=affiliate_data.country,
            state_province=affiliate_data.state_province,
            city=affiliate_data.city,
            address_line1=affiliate_data.address_line1,
            website_url=affiliate_data.website_url,
            social_media_links=affiliate_data.social_media_links,
            referral_code=referral_code,
            custom_referral_code=affiliate_data.custom_referral_code,
            payment_method=affiliate_data.payment_method,
            payment_details=affiliate_data.payment_details
        )
        
        db.add(affiliate)
        db.commit()
        db.refresh(affiliate)
        
        return affiliate
    
    async def create_referral(self, referral_code: str, referral_data: ReferralCreate, user: Dict[str, Any], db: Session):
        """Create new referral"""
        
        # Find affiliate by referral code
        affiliate = db.query(Affiliate).filter(Affiliate.referral_code == referral_code).first()
        if not affiliate:
            raise HTTPException(status_code=404, detail="Invalid referral code")
        
        if affiliate.status != AffiliateStatus.ACTIVE:
            raise HTTPException(status_code=400, detail="Affiliate is not active")
        
        # Check if user is already referred
        existing = db.query(Referral).filter(Referral.referred_user_id == user["user_id"]).first()
        if existing:
            raise HTTPException(status_code=400, detail="User is already referred")
        
        referral_id = f"REF_{secrets.token_hex(8).upper()}"
        
        referral = Referral(
            referral_id=referral_id,
            affiliate_id=affiliate.affiliate_id,
            referred_user_id=user["user_id"],
            referred_user_email=referral_data.referred_user_email,
            referral_source=referral_data.referral_source,
            referral_campaign=referral_data.referral_campaign,
            utm_source=referral_data.utm_source,
            utm_medium=referral_data.utm_medium,
            utm_campaign=referral_data.utm_campaign,
            tier_level=ReferralTier.TIER_1,
            original_affiliate_id=affiliate.affiliate_id
        )
        
        db.add(referral)
        
        # Update affiliate stats
        affiliate.total_referrals += 1
        
        db.commit()
        db.refresh(referral)
        
        return referral
    
    async def calculate_commission(self, transaction_data: Dict[str, Any], db: Session):
        """Calculate and create commission records"""
        
        user_id = transaction_data["user_id"]
        transaction_id = transaction_data["transaction_id"]
        transaction_type = transaction_data["transaction_type"]
        transaction_amount = Decimal(str(transaction_data["amount"]))
        fee_amount = Decimal(str(transaction_data["fee"]))
        
        # Find referral
        referral = db.query(Referral).filter(Referral.referred_user_id == user_id).first()
        if not referral:
            return  # No referral, no commission
        
        # Create commission for direct affiliate (Tier 1)
        await self._create_commission_record(
            referral.affiliate_id,
            referral.referral_id,
            user_id,
            transaction_id,
            transaction_type,
            transaction_amount,
            fee_amount,
            ReferralTier.TIER_1,
            referral.original_affiliate_id,
            db
        )
        
        # Create multi-level commissions (Tier 2-5)
        current_affiliate = db.query(Affiliate).filter(Affiliate.affiliate_id == referral.affiliate_id).first()
        tier_level = 2
        
        while current_affiliate and current_affiliate.parent_affiliate_id and tier_level <= 5:
            parent_affiliate = db.query(Affiliate).filter(
                Affiliate.affiliate_id == current_affiliate.parent_affiliate_id
            ).first()
            
            if parent_affiliate and parent_affiliate.status == AffiliateStatus.ACTIVE:
                tier_enum = getattr(ReferralTier, f"TIER_{tier_level}")
                
                await self._create_commission_record(
                    parent_affiliate.affiliate_id,
                    referral.referral_id,
                    user_id,
                    transaction_id,
                    transaction_type,
                    transaction_amount,
                    fee_amount,
                    tier_enum,
                    referral.original_affiliate_id,
                    db
                )
            
            current_affiliate = parent_affiliate
            tier_level += 1
        
        db.commit()
    
    async def _create_commission_record(
        self,
        affiliate_id: str,
        referral_id: str,
        user_id: str,
        transaction_id: str,
        transaction_type: str,
        transaction_amount: Decimal,
        fee_amount: Decimal,
        tier_level: ReferralTier,
        original_affiliate_id: str,
        db: Session
    ):
        """Create individual commission record"""
        
        affiliate = db.query(Affiliate).filter(Affiliate.affiliate_id == affiliate_id).first()
        if not affiliate:
            return
        
        # Get commission rate based on tier
        commission_rate = getattr(affiliate, f"{tier_level.value}_rate", Decimal("0"))
        
        if commission_rate <= 0:
            return
        
        commission_amount = fee_amount * commission_rate
        
        commission_id = f"COMM_{secrets.token_hex(8).upper()}"
        
        commission = Commission(
            commission_id=commission_id,
            affiliate_id=affiliate_id,
            referral_id=referral_id,
            referred_user_id=user_id,
            transaction_id=transaction_id,
            transaction_type=transaction_type,
            commission_type=self._get_commission_type(transaction_type),
            transaction_amount=transaction_amount,
            fee_amount=fee_amount,
            commission_rate=commission_rate,
            commission_amount=commission_amount,
            tier_level=tier_level,
            original_affiliate_id=original_affiliate_id,
            usd_value=commission_amount  # Simplified - would convert to USD
        )
        
        db.add(commission)
        
        # Update affiliate pending commission
        affiliate.pending_commission += commission_amount
        affiliate.total_commission_earned += commission_amount
    
    def _get_commission_type(self, transaction_type: str) -> CommissionType:
        """Map transaction type to commission type"""
        mapping = {
            "spot_trade": CommissionType.TRADING_FEE,
            "futures_trade": CommissionType.FUTURES_FEE,
            "options_trade": CommissionType.OPTIONS_FEE,
            "p2p_trade": CommissionType.P2P_FEE,
            "nft_trade": CommissionType.NFT_FEE,
            "deposit": CommissionType.DEPOSIT_FEE,
            "withdrawal": CommissionType.WITHDRAWAL_FEE,
            "copy_trade": CommissionType.COPY_TRADING_FEE
        }
        return mapping.get(transaction_type, CommissionType.TRADING_FEE)
    
    async def create_affiliate_link(self, link_data: LinkCreate, user: Dict[str, Any], db: Session):
        """Create affiliate tracking link"""
        
        affiliate = db.query(Affiliate).filter(Affiliate.user_id == user["user_id"]).first()
        if not affiliate:
            raise HTTPException(status_code=404, detail="User is not an affiliate")
        
        link_id = f"LINK_{secrets.token_hex(8).upper()}"
        
        # Generate tracking URL
        base_url = "https://tigerex.com"
        tracking_params = f"?ref={affiliate.referral_code}"
        
        if link_data.utm_source:
            tracking_params += f"&utm_source={link_data.utm_source}"
        if link_data.utm_medium:
            tracking_params += f"&utm_medium={link_data.utm_medium}"
        if link_data.utm_campaign:
            tracking_params += f"&utm_campaign={link_data.utm_campaign}"
        if link_data.utm_content:
            tracking_params += f"&utm_content={link_data.utm_content}"
        
        tracking_url = f"{base_url}{tracking_params}"
        
        link = AffiliateLink(
            link_id=link_id,
            affiliate_id=affiliate.affiliate_id,
            link_name=link_data.link_name,
            destination_url=link_data.destination_url,
            tracking_url=tracking_url,
            campaign_name=link_data.campaign_name,
            utm_source=link_data.utm_source,
            utm_medium=link_data.utm_medium,
            utm_campaign=link_data.utm_campaign,
            utm_content=link_data.utm_content,
            expires_at=link_data.expires_at
        )
        
        db.add(link)
        db.commit()
        db.refresh(link)
        
        return link
    
    async def process_payout(self, affiliate_id: str, payout_data: PayoutRequest, db: Session):
        """Process affiliate payout"""
        
        affiliate = db.query(Affiliate).filter(Affiliate.affiliate_id == affiliate_id).first()
        if not affiliate:
            raise HTTPException(status_code=404, detail="Affiliate not found")
        
        if affiliate.pending_commission < payout_data.amount:
            raise HTTPException(status_code=400, detail="Insufficient pending commission")
        
        if payout_data.amount < affiliate.minimum_payout:
            raise HTTPException(status_code=400, detail=f"Minimum payout is {affiliate.minimum_payout}")
        
        # Get unpaid commissions
        unpaid_commissions = db.query(Commission).filter(
            Commission.affiliate_id == affiliate_id,
            Commission.is_paid == False
        ).all()
        
        total_unpaid = sum(comm.commission_amount for comm in unpaid_commissions)
        
        if total_unpaid < payout_data.amount:
            raise HTTPException(status_code=400, detail="Insufficient unpaid commissions")
        
        payout_id = f"PAYOUT_{secrets.token_hex(8).upper()}"
        
        # Calculate period
        oldest_commission = min(unpaid_commissions, key=lambda x: x.created_at)
        newest_commission = max(unpaid_commissions, key=lambda x: x.created_at)
        
        payout = AffiliatePayout(
            payout_id=payout_id,
            affiliate_id=affiliate_id,
            total_amount=payout_data.amount,
            commission_count=len(unpaid_commissions),
            period_start=oldest_commission.created_at,
            period_end=newest_commission.created_at,
            payment_method=payout_data.payment_method,
            payment_details=payout_data.payment_details,
            net_amount=payout_data.amount  # Simplified - would deduct fees
        )
        
        db.add(payout)
        
        # Mark commissions as paid
        for commission in unpaid_commissions:
            commission.is_paid = True
            commission.paid_at = datetime.utcnow()
            commission.payout_id = payout_id
        
        # Update affiliate balances
        affiliate.pending_commission -= payout_data.amount
        affiliate.total_commission_paid += payout_data.amount
        
        db.commit()
        db.refresh(payout)
        
        return payout

# Initialize manager
affiliate_manager = AffiliateManager()

@app.on_event("startup")
async def startup_event():
    await affiliate_manager.initialize()

# API Endpoints
@app.post("/api/v1/affiliate/register")
async def register_affiliate(
    affiliate_data: AffiliateCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Register as affiliate"""
    affiliate = await affiliate_manager.create_affiliate(affiliate_data, current_user, db)
    return {
        "affiliate_id": affiliate.affiliate_id,
        "referral_code": affiliate.referral_code,
        "status": affiliate.status,
        "message": "Affiliate registration submitted for review"
    }

@app.post("/api/v1/affiliate/refer/{referral_code}")
async def create_referral(
    referral_code: str,
    referral_data: ReferralCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create referral using referral code"""
    referral = await affiliate_manager.create_referral(referral_code, referral_data, current_user, db)
    return {
        "referral_id": referral.referral_id,
        "affiliate_id": referral.affiliate_id,
        "tier_level": referral.tier_level,
        "message": "Referral created successfully"
    }

@app.get("/api/v1/affiliate/dashboard")
async def get_affiliate_dashboard(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get affiliate dashboard data"""
    affiliate = db.query(Affiliate).filter(Affiliate.user_id == current_user["user_id"]).first()
    if not affiliate:
        raise HTTPException(status_code=404, detail="User is not an affiliate")
    
    # Get recent referrals
    recent_referrals = db.query(Referral).filter(
        Referral.affiliate_id == affiliate.affiliate_id
    ).order_by(Referral.created_at.desc()).limit(10).all()
    
    # Get recent commissions
    recent_commissions = db.query(Commission).filter(
        Commission.affiliate_id == affiliate.affiliate_id
    ).order_by(Commission.created_at.desc()).limit(10).all()
    
    return {
        "affiliate_info": {
            "affiliate_id": affiliate.affiliate_id,
            "referral_code": affiliate.referral_code,
            "status": affiliate.status,
            "total_referrals": affiliate.total_referrals,
            "active_referrals": affiliate.active_referrals,
            "total_commission_earned": float(affiliate.total_commission_earned),
            "pending_commission": float(affiliate.pending_commission),
            "total_commission_paid": float(affiliate.total_commission_paid)
        },
        "recent_referrals": [
            {
                "referral_id": ref.referral_id,
                "referred_user_email": ref.referred_user_email,
                "registration_date": ref.registration_date.isoformat(),
                "is_qualified": ref.is_qualified,
                "total_fees_generated": float(ref.total_fees_generated)
            }
            for ref in recent_referrals
        ],
        "recent_commissions": [
            {
                "commission_id": comm.commission_id,
                "transaction_type": comm.transaction_type,
                "commission_amount": float(comm.commission_amount),
                "tier_level": comm.tier_level,
                "is_paid": comm.is_paid,
                "created_at": comm.created_at.isoformat()
            }
            for comm in recent_commissions
        ]
    }

@app.post("/api/v1/affiliate/links")
async def create_affiliate_link(
    link_data: LinkCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create affiliate tracking link"""
    link = await affiliate_manager.create_affiliate_link(link_data, current_user, db)
    return {
        "link_id": link.link_id,
        "link_name": link.link_name,
        "tracking_url": link.tracking_url,
        "message": "Affiliate link created successfully"
    }

@app.get("/api/v1/affiliate/links")
async def get_affiliate_links(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get affiliate links"""
    affiliate = db.query(Affiliate).filter(Affiliate.user_id == current_user["user_id"]).first()
    if not affiliate:
        raise HTTPException(status_code=404, detail="User is not an affiliate")
    
    links = db.query(AffiliateLink).filter(AffiliateLink.affiliate_id == affiliate.affiliate_id).all()
    
    return {
        "links": [
            {
                "link_id": link.link_id,
                "link_name": link.link_name,
                "tracking_url": link.tracking_url,
                "click_count": link.click_count,
                "conversion_count": link.conversion_count,
                "conversion_rate": float(link.conversion_rate),
                "is_active": link.is_active,
                "created_at": link.created_at.isoformat()
            }
            for link in links
        ]
    }

@app.post("/api/v1/affiliate/payout")
async def request_payout(
    payout_data: PayoutRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Request affiliate payout"""
    affiliate = db.query(Affiliate).filter(Affiliate.user_id == current_user["user_id"]).first()
    if not affiliate:
        raise HTTPException(status_code=404, detail="User is not an affiliate")
    
    payout = await affiliate_manager.process_payout(affiliate.affiliate_id, payout_data, db)
    return {
        "payout_id": payout.payout_id,
        "amount": float(payout.total_amount),
        "status": payout.status,
        "message": "Payout request submitted"
    }

@app.get("/api/v1/affiliate/payouts")
async def get_affiliate_payouts(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get affiliate payout history"""
    affiliate = db.query(Affiliate).filter(Affiliate.user_id == current_user["user_id"]).first()
    if not affiliate:
        raise HTTPException(status_code=404, detail="User is not an affiliate")
    
    payouts = db.query(AffiliatePayout).filter(
        AffiliatePayout.affiliate_id == affiliate.affiliate_id
    ).order_by(AffiliatePayout.created_at.desc()).all()
    
    return {
        "payouts": [
            {
                "payout_id": payout.payout_id,
                "total_amount": float(payout.total_amount),
                "currency": payout.currency,
                "status": payout.status,
                "payment_method": payout.payment_method,
                "created_at": payout.created_at.isoformat(),
                "completed_at": payout.completed_at.isoformat() if payout.completed_at else None
            }
            for payout in payouts
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "affiliate-system"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
