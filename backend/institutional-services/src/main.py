"""
TigerEx Institutional Services
Prime brokerage, OTC trading, custody services, and institutional-grade features
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
from decimal import Decimal
import json
import uuid
import hashlib
import hmac
import secrets
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, DECIMAL, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
import aioredis
import asyncpg
import aiohttp
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="TigerEx Institutional Services",
    description="Prime brokerage, OTC trading, and institutional-grade services",
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
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "institutional-secret-key")
    
    # Institutional limits
    MIN_INSTITUTIONAL_VOLUME = Decimal("1000000")  # $1M minimum
    OTC_MIN_ORDER_SIZE = Decimal("100000")  # $100K minimum for OTC
    PRIME_BROKERAGE_MIN_AUM = Decimal("10000000")  # $10M minimum AUM
    
    # Custody settings
    COLD_STORAGE_THRESHOLD = Decimal("1000000")  # Move to cold storage above $1M
    MULTI_SIG_THRESHOLD = Decimal("500000")  # Require multi-sig above $500K
    
    # Compliance
    LARGE_TRADE_THRESHOLD = Decimal("250000")  # Report trades above $250K
    SUSPICIOUS_ACTIVITY_THRESHOLD = Decimal("1000000")  # Flag activity above $1M

config = Config()

# Database setup
engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Security
security = HTTPBearer()

# Enums
class InstitutionType(str, Enum):
    HEDGE_FUND = "hedge_fund"
    FAMILY_OFFICE = "family_office"
    ASSET_MANAGER = "asset_manager"
    PENSION_FUND = "pension_fund"
    INSURANCE_COMPANY = "insurance_company"
    BANK = "bank"
    BROKER_DEALER = "broker_dealer"
    PROPRIETARY_TRADING = "proprietary_trading"
    MARKET_MAKER = "market_maker"
    CORPORATE_TREASURY = "corporate_treasury"

class ServiceTier(str, Enum):
    BASIC = "basic"
    PREMIUM = "premium"
    ELITE = "elite"
    WHITE_GLOVE = "white_glove"

class OTCOrderStatus(str, Enum):
    PENDING = "pending"
    QUOTED = "quoted"
    NEGOTIATING = "negotiating"
    AGREED = "agreed"
    SETTLING = "settling"
    SETTLED = "settled"
    CANCELLED = "cancelled"
    EXPIRED = "expired"

class CustodyType(str, Enum):
    HOT_WALLET = "hot_wallet"
    WARM_WALLET = "warm_wallet"
    COLD_STORAGE = "cold_storage"
    MULTI_SIG = "multi_sig"
    HARDWARE_SECURITY_MODULE = "hsm"
    INSTITUTIONAL_CUSTODY = "institutional_custody"

class ReportType(str, Enum):
    DAILY_POSITIONS = "daily_positions"
    TRADE_CONFIRMATION = "trade_confirmation"
    MONTHLY_STATEMENT = "monthly_statement"
    REGULATORY_FILING = "regulatory_filing"
    RISK_REPORT = "risk_report"
    COMPLIANCE_REPORT = "compliance_report"
    TAX_REPORT = "tax_report"

# Database Models
class InstitutionalClient(Base):
    __tablename__ = "institutional_clients"
    
    id = Column(Integer, primary_key=True, index=True)
    client_code = Column(String(20), unique=True, nullable=False, index=True)
    legal_name = Column(String(255), nullable=False)
    institution_type = Column(SQLEnum(InstitutionType), nullable=False)
    service_tier = Column(SQLEnum(ServiceTier), default=ServiceTier.BASIC)
    
    # Contact Information
    primary_contact_name = Column(String(255), nullable=False)
    primary_contact_email = Column(String(255), nullable=False)
    primary_contact_phone = Column(String(20))
    
    # Address
    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255))
    city = Column(String(100), nullable=False)
    state_province = Column(String(100))
    postal_code = Column(String(20))
    country = Column(String(50), nullable=False)
    
    # Financial Information
    aum = Column(DECIMAL(20, 2))  # Assets Under Management
    annual_trading_volume = Column(DECIMAL(20, 2))
    credit_limit = Column(DECIMAL(20, 2), default=0)
    margin_limit = Column(DECIMAL(20, 2), default=0)
    
    # Service Configuration
    services_enabled = Column(JSON)  # List of enabled services
    trading_permissions = Column(JSON)  # Trading permissions
    custody_preferences = Column(JSON)  # Custody preferences
    reporting_preferences = Column(JSON)  # Reporting preferences
    
    # Compliance
    kyc_status = Column(String(20), default='pending')
    aml_status = Column(String(20), default='pending')
    regulatory_status = Column(String(20), default='pending')
    compliance_notes = Column(Text)
    
    # Account Management
    account_manager_id = Column(Integer, ForeignKey("admin_users.id"))
    relationship_manager_id = Column(Integer, ForeignKey("admin_users.id"))
    
    # Status
    is_active = Column(Boolean, default=True)
    onboarding_completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class OTCOrder(Base):
    __tablename__ = "otc_orders"
    
    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(String(50), unique=True, nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("institutional_clients.id"), nullable=False)
    
    # Order Details
    base_asset = Column(String(20), nullable=False)
    quote_asset = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)  # BUY or SELL
    quantity = Column(DECIMAL(30, 8), nullable=False)
    
    # Pricing
    requested_price = Column(DECIMAL(20, 8))
    quoted_price = Column(DECIMAL(20, 8))
    agreed_price = Column(DECIMAL(20, 8))
    market_price_at_request = Column(DECIMAL(20, 8))
    
    # Status and Timing
    status = Column(SQLEnum(OTCOrderStatus), default=OTCOrderStatus.PENDING)
    quote_expires_at = Column(DateTime)
    settlement_date = Column(DateTime)
    
    # Execution Details
    executed_quantity = Column(DECIMAL(30, 8), default=0)
    executed_price = Column(DECIMAL(20, 8))
    execution_venue = Column(String(100))
    
    # Risk and Compliance
    risk_score = Column(Integer, default=0)
    compliance_checked = Column(Boolean, default=False)
    requires_approval = Column(Boolean, default=False)
    approved_by = Column(Integer, ForeignKey("admin_users.id"))
    
    # Metadata
    notes = Column(Text)
    external_order_id = Column(String(100))  # Client's order ID
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class CustodyAccount(Base):
    __tablename__ = "custody_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(String(50), unique=True, nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("institutional_clients.id"), nullable=False)
    
    # Account Details
    account_name = Column(String(255), nullable=False)
    custody_type = Column(SQLEnum(CustodyType), nullable=False)
    
    # Security Configuration
    multi_sig_required = Column(Boolean, default=False)
    required_signatures = Column(Integer, default=1)
    authorized_signers = Column(JSON)  # List of authorized signer IDs
    
    # Wallet Information
    wallet_addresses = Column(JSON)  # Blockchain addresses
    public_keys = Column(JSON)  # Public keys for verification
    
    # Insurance and Security
    insurance_coverage = Column(DECIMAL(20, 2))
    security_audit_date = Column(DateTime)
    security_rating = Column(String(10))
    
    # Access Control
    withdrawal_limits = Column(JSON)  # Daily/monthly limits per asset
    ip_whitelist = Column(JSON)  # Allowed IP addresses
    time_restrictions = Column(JSON)  # Time-based access restrictions
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class PrimeBrokerageAccount(Base):
    __tablename__ = "prime_brokerage_accounts"
    
    id = Column(Integer, primary_key=True, index=True)
    account_id = Column(String(50), unique=True, nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("institutional_clients.id"), nullable=False)
    
    # Account Configuration
    base_currency = Column(String(10), default='USD')
    leverage_limit = Column(DECIMAL(10, 2), default=1.0)
    margin_requirement = Column(DECIMAL(5, 4), default=0.1)  # 10% default
    
    # Balances
    cash_balance = Column(DECIMAL(20, 2), default=0)
    margin_balance = Column(DECIMAL(20, 2), default=0)
    available_balance = Column(DECIMAL(20, 2), default=0)
    
    # Risk Management
    var_limit = Column(DECIMAL(20, 2))  # Value at Risk limit
    concentration_limits = Column(JSON)  # Per-asset concentration limits
    sector_limits = Column(JSON)  # Per-sector limits
    
    # Fees and Pricing
    commission_schedule = Column(JSON)  # Custom commission rates
    financing_rates = Column(JSON)  # Margin financing rates
    
    # Services
    securities_lending_enabled = Column(Boolean, default=False)
    repo_services_enabled = Column(Boolean, default=False)
    fx_services_enabled = Column(Boolean, default=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class InstitutionalReport(Base):
    __tablename__ = "institutional_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(50), unique=True, nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("institutional_clients.id"), nullable=False)
    
    # Report Details
    report_type = Column(SQLEnum(ReportType), nullable=False)
    report_period_start = Column(DateTime, nullable=False)
    report_period_end = Column(DateTime, nullable=False)
    
    # Content
    report_data = Column(JSON)  # Report content
    file_url = Column(String(500))  # URL to generated file
    file_format = Column(String(10))  # PDF, CSV, XLSX, etc.
    
    # Generation
    generated_at = Column(DateTime)
    generated_by = Column(Integer, ForeignKey("admin_users.id"))
    
    # Delivery
    delivery_method = Column(String(20))  # email, sftp, api, portal
    delivered_at = Column(DateTime)
    delivery_status = Column(String(20), default='pending')
    
    created_at = Column(DateTime, default=func.now())

# Pydantic Models
class InstitutionalClientCreate(BaseModel):
    legal_name: str
    institution_type: InstitutionType
    primary_contact_name: str
    primary_contact_email: EmailStr
    primary_contact_phone: Optional[str] = None
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state_province: Optional[str] = None
    postal_code: str
    country: str
    aum: Optional[Decimal] = None
    annual_trading_volume: Optional[Decimal] = None
    services_enabled: List[str] = []

class OTCOrderRequest(BaseModel):
    base_asset: str
    quote_asset: str
    side: str  # BUY or SELL
    quantity: Decimal
    requested_price: Optional[Decimal] = None
    external_order_id: Optional[str] = None
    notes: Optional[str] = None
    
    @validator('side')
    def validate_side(cls, v):
        if v not in ['BUY', 'SELL']:
            raise ValueError('Side must be BUY or SELL')
        return v
    
    @validator('quantity')
    def validate_quantity(cls, v):
        if v <= 0:
            raise ValueError('Quantity must be positive')
        if v < config.OTC_MIN_ORDER_SIZE:
            raise ValueError(f'Minimum OTC order size is {config.OTC_MIN_ORDER_SIZE}')
        return v

class OTCQuoteResponse(BaseModel):
    order_id: str
    quoted_price: Decimal
    quantity: Decimal
    total_value: Decimal
    quote_expires_at: datetime
    spread: Decimal
    market_impact: Decimal

class CustodyAccountCreate(BaseModel):
    account_name: str
    custody_type: CustodyType
    multi_sig_required: bool = False
    required_signatures: int = 1
    authorized_signers: List[str] = []
    insurance_coverage: Optional[Decimal] = None
    withdrawal_limits: Dict[str, Decimal] = {}

class PrimeBrokerageAccountCreate(BaseModel):
    base_currency: str = 'USD'
    leverage_limit: Decimal = Decimal('1.0')
    margin_requirement: Decimal = Decimal('0.1')
    var_limit: Optional[Decimal] = None
    services_enabled: List[str] = []

class ReportRequest(BaseModel):
    report_type: ReportType
    period_start: datetime
    period_end: datetime
    file_format: str = 'PDF'
    delivery_method: str = 'email'

# Dependency functions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_institutional_client(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    # Validate institutional client token
    # This is a simplified implementation
    client = db.query(InstitutionalClient).filter(
        InstitutionalClient.client_code == "INST001"
    ).first()
    
    if not client:
        raise HTTPException(status_code=401, detail="Invalid institutional client")
    
    return client

# Institutional Services Manager
class InstitutionalServicesManager:
    def __init__(self):
        self.redis_client = None
        self.market_data_cache = {}
        self.risk_engine = RiskEngine()
        self.compliance_engine = ComplianceEngine()
        self.pricing_engine = PricingEngine()
        
    async def initialize(self):
        """Initialize async components"""
        self.redis_client = await aioredis.from_url(config.REDIS_URL)
    
    async def create_institutional_client(
        self, 
        client_data: InstitutionalClientCreate,
        db: Session
    ) -> InstitutionalClient:
        """Create new institutional client"""
        
        # Generate unique client code
        client_code = self.generate_client_code(client_data.institution_type)
        
        # Determine service tier based on AUM
        service_tier = self.determine_service_tier(client_data.aum or Decimal('0'))
        
        client = InstitutionalClient(
            client_code=client_code,
            legal_name=client_data.legal_name,
            institution_type=client_data.institution_type,
            service_tier=service_tier,
            primary_contact_name=client_data.primary_contact_name,
            primary_contact_email=client_data.primary_contact_email,
            primary_contact_phone=client_data.primary_contact_phone,
            address_line1=client_data.address_line1,
            address_line2=client_data.address_line2,
            city=client_data.city,
            state_province=client_data.state_province,
            postal_code=client_data.postal_code,
            country=client_data.country,
            aum=client_data.aum,
            annual_trading_volume=client_data.annual_trading_volume,
            services_enabled=client_data.services_enabled
        )
        
        db.add(client)
        db.commit()
        db.refresh(client)
        
        # Initialize default accounts
        await self.setup_default_accounts(client, db)
        
        # Send welcome email
        await self.send_welcome_email(client)
        
        return client
    
    def generate_client_code(self, institution_type: InstitutionType) -> str:
        """Generate unique client code"""
        prefix_map = {
            InstitutionType.HEDGE_FUND: "HF",
            InstitutionType.FAMILY_OFFICE: "FO",
            InstitutionType.ASSET_MANAGER: "AM",
            InstitutionType.PENSION_FUND: "PF",
            InstitutionType.INSURANCE_COMPANY: "IC",
            InstitutionType.BANK: "BK",
            InstitutionType.BROKER_DEALER: "BD",
            InstitutionType.PROPRIETARY_TRADING: "PT",
            InstitutionType.MARKET_MAKER: "MM",
            InstitutionType.CORPORATE_TREASURY: "CT"
        }
        
        prefix = prefix_map.get(institution_type, "IN")
        timestamp = int(datetime.now().timestamp())
        random_suffix = secrets.token_hex(2).upper()
        
        return f"{prefix}{timestamp % 10000:04d}{random_suffix}"
    
    def determine_service_tier(self, aum: Decimal) -> ServiceTier:
        """Determine service tier based on AUM"""
        if aum >= Decimal('1000000000'):  # $1B+
            return ServiceTier.WHITE_GLOVE
        elif aum >= Decimal('100000000'):  # $100M+
            return ServiceTier.ELITE
        elif aum >= Decimal('10000000'):   # $10M+
            return ServiceTier.PREMIUM
        else:
            return ServiceTier.BASIC
    
    async def setup_default_accounts(self, client: InstitutionalClient, db: Session):
        """Setup default accounts for new institutional client"""
        
        # Create custody account
        custody_account = CustodyAccount(
            account_id=f"{client.client_code}_CUSTODY",
            client_id=client.id,
            account_name=f"{client.legal_name} - Custody Account",
            custody_type=CustodyType.MULTI_SIG,
            multi_sig_required=True,
            required_signatures=2,
            insurance_coverage=Decimal('10000000')  # $10M default coverage
        )
        
        db.add(custody_account)
        
        # Create prime brokerage account if eligible
        if client.aum and client.aum >= config.PRIME_BROKERAGE_MIN_AUM:
            pb_account = PrimeBrokerageAccount(
                account_id=f"{client.client_code}_PB",
                client_id=client.id,
                base_currency='USD',
                leverage_limit=Decimal('5.0'),  # 5x leverage for institutions
                margin_requirement=Decimal('0.2'),  # 20% margin requirement
                var_limit=client.aum * Decimal('0.05')  # 5% of AUM as VaR limit
            )
            
            db.add(pb_account)
        
        db.commit()
    
    async def request_otc_quote(
        self,
        client: InstitutionalClient,
        order_request: OTCOrderRequest,
        db: Session
    ) -> OTCQuoteResponse:
        """Request OTC quote for large order"""
        
        # Validate order size
        if order_request.quantity * (order_request.requested_price or Decimal('1')) < config.OTC_MIN_ORDER_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Minimum OTC order size is ${config.OTC_MIN_ORDER_SIZE}"
            )
        
        # Get current market price
        market_price = await self.get_market_price(
            f"{order_request.base_asset}{order_request.quote_asset}"
        )
        
        # Calculate quote using pricing engine
        quote_price, spread, market_impact = await self.pricing_engine.calculate_otc_quote(
            base_asset=order_request.base_asset,
            quote_asset=order_request.quote_asset,
            side=order_request.side,
            quantity=order_request.quantity,
            market_price=market_price,
            client_tier=client.service_tier
        )
        
        # Create OTC order record
        order_id = f"OTC_{client.client_code}_{int(datetime.now().timestamp())}"
        
        otc_order = OTCOrder(
            order_id=order_id,
            client_id=client.id,
            base_asset=order_request.base_asset,
            quote_asset=order_request.quote_asset,
            side=order_request.side,
            quantity=order_request.quantity,
            requested_price=order_request.requested_price,
            quoted_price=quote_price,
            market_price_at_request=market_price,
            status=OTCOrderStatus.QUOTED,
            quote_expires_at=datetime.now() + timedelta(minutes=15),  # 15-minute quote validity
            external_order_id=order_request.external_order_id,
            notes=order_request.notes
        )
        
        db.add(otc_order)
        db.commit()
        db.refresh(otc_order)
        
        # Cache quote for quick access
        await self.redis_client.setex(
            f"otc_quote:{order_id}",
            900,  # 15 minutes
            json.dumps({
                "order_id": order_id,
                "quoted_price": str(quote_price),
                "expires_at": otc_order.quote_expires_at.isoformat()
            })
        )
        
        return OTCQuoteResponse(
            order_id=order_id,
            quoted_price=quote_price,
            quantity=order_request.quantity,
            total_value=quote_price * order_request.quantity,
            quote_expires_at=otc_order.quote_expires_at,
            spread=spread,
            market_impact=market_impact
        )
    
    async def accept_otc_quote(
        self,
        client: InstitutionalClient,
        order_id: str,
        db: Session
    ) -> Dict[str, Any]:
        """Accept OTC quote and execute trade"""
        
        # Get OTC order
        otc_order = db.query(OTCOrder).filter(
            OTCOrder.order_id == order_id,
            OTCOrder.client_id == client.id,
            OTCOrder.status == OTCOrderStatus.QUOTED
        ).first()
        
        if not otc_order:
            raise HTTPException(status_code=404, detail="OTC order not found or not quotable")
        
        # Check if quote is still valid
        if datetime.now() > otc_order.quote_expires_at:
            otc_order.status = OTCOrderStatus.EXPIRED
            db.commit()
            raise HTTPException(status_code=400, detail="Quote has expired")
        
        # Risk and compliance checks
        risk_check = await self.risk_engine.check_otc_order(otc_order, client)
        compliance_check = await self.compliance_engine.check_otc_order(otc_order, client)
        
        if not risk_check.approved:
            raise HTTPException(status_code=400, detail=f"Risk check failed: {risk_check.reason}")
        
        if not compliance_check.approved:
            otc_order.requires_approval = True
            otc_order.status = OTCOrderStatus.PENDING
            db.commit()
            
            # Notify compliance team
            await self.notify_compliance_team(otc_order, compliance_check.reason)
            
            return {
                "status": "pending_approval",
                "message": "Order requires compliance approval",
                "order_id": order_id
            }
        
        # Execute the trade
        execution_result = await self.execute_otc_trade(otc_order, db)
        
        return execution_result
    
    async def execute_otc_trade(self, otc_order: OTCOrder, db: Session) -> Dict[str, Any]:
        """Execute OTC trade"""
        
        try:
            # Update order status
            otc_order.status = OTCOrderStatus.SETTLING
            otc_order.agreed_price = otc_order.quoted_price
            otc_order.settlement_date = datetime.now() + timedelta(days=1)  # T+1 settlement
            
            # Execute trade through liquidity providers
            execution_venues = await self.find_liquidity_sources(otc_order)
            
            total_executed = Decimal('0')
            weighted_avg_price = Decimal('0')
            
            for venue in execution_venues:
                if total_executed >= otc_order.quantity:
                    break
                
                remaining_qty = otc_order.quantity - total_executed
                venue_qty = min(venue['available_quantity'], remaining_qty)
                
                # Execute portion at this venue
                venue_execution = await self.execute_at_venue(
                    venue=venue,
                    quantity=venue_qty,
                    order=otc_order
                )
                
                if venue_execution['success']:
                    executed_qty = venue_execution['executed_quantity']
                    executed_price = venue_execution['executed_price']
                    
                    # Update weighted average price
                    weighted_avg_price = (
                        (weighted_avg_price * total_executed + executed_price * executed_qty) /
                        (total_executed + executed_qty)
                    )
                    
                    total_executed += executed_qty
            
            # Update order with execution details
            otc_order.executed_quantity = total_executed
            otc_order.executed_price = weighted_avg_price
            otc_order.status = OTCOrderStatus.SETTLED if total_executed == otc_order.quantity else OTCOrderStatus.SETTLING
            
            db.commit()
            
            # Generate trade confirmation
            await self.generate_trade_confirmation(otc_order)
            
            # Update client balances
            await self.update_client_balances(otc_order)
            
            return {
                "status": "executed",
                "order_id": otc_order.order_id,
                "executed_quantity": str(total_executed),
                "executed_price": str(weighted_avg_price),
                "total_value": str(total_executed * weighted_avg_price),
                "settlement_date": otc_order.settlement_date.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error executing OTC trade {otc_order.order_id}: {e}")
            otc_order.status = OTCOrderStatus.CANCELLED
            db.commit()
            
            raise HTTPException(status_code=500, detail="Trade execution failed")
    
    async def get_market_price(self, symbol: str) -> Decimal:
        """Get current market price for symbol"""
        # This would integrate with market data providers
        # Mock implementation
        mock_prices = {
            "BTCUSDT": Decimal("45000.00"),
            "ETHUSDT": Decimal("3000.00"),
            "BNBUSDT": Decimal("300.00")
        }
        
        return mock_prices.get(symbol, Decimal("1.00"))
    
    async def find_liquidity_sources(self, otc_order: OTCOrder) -> List[Dict[str, Any]]:
        """Find liquidity sources for OTC order"""
        # This would integrate with multiple liquidity providers
        # Mock implementation
        return [
            {
                "venue": "LP_BINANCE",
                "available_quantity": otc_order.quantity * Decimal("0.6"),
                "price": otc_order.quoted_price,
                "fee": Decimal("0.001")
            },
            {
                "venue": "LP_COINBASE",
                "available_quantity": otc_order.quantity * Decimal("0.4"),
                "price": otc_order.quoted_price * Decimal("1.001"),
                "fee": Decimal("0.0015")
            }
        ]
    
    async def execute_at_venue(self, venue: Dict[str, Any], quantity: Decimal, order: OTCOrder) -> Dict[str, Any]:
        """Execute trade at specific venue"""
        # Mock execution
        return {
            "success": True,
            "executed_quantity": quantity,
            "executed_price": venue["price"],
            "venue": venue["venue"],
            "fee": venue["fee"] * quantity * venue["price"]
        }
    
    async def generate_trade_confirmation(self, otc_order: OTCOrder):
        """Generate trade confirmation document"""
        # This would generate PDF trade confirmation
        logger.info(f"Generated trade confirmation for order {otc_order.order_id}")
    
    async def update_client_balances(self, otc_order: OTCOrder):
        """Update client balances after trade execution"""
        # This would update the client's balances
        logger.info(f"Updated balances for client {otc_order.client_id} after order {otc_order.order_id}")
    
    async def send_welcome_email(self, client: InstitutionalClient):
        """Send welcome email to new institutional client"""
        # Mock implementation
        logger.info(f"Sent welcome email to {client.primary_contact_email}")
    
    async def notify_compliance_team(self, otc_order: OTCOrder, reason: str):
        """Notify compliance team of order requiring approval"""
        logger.info(f"Notified compliance team about order {otc_order.order_id}: {reason}")

# Risk Engine
class RiskEngine:
    async def check_otc_order(self, otc_order: OTCOrder, client: InstitutionalClient) -> 'RiskCheckResult':
        """Perform risk checks on OTC order"""
        
        # Calculate order value
        order_value = otc_order.quantity * otc_order.quoted_price
        
        # Check position limits
        if order_value > client.credit_limit:
            return RiskCheckResult(
                approved=False,
                reason=f"Order value ${order_value} exceeds credit limit ${client.credit_limit}"
            )
        
        # Check concentration limits
        # This would check against existing positions
        
        # Check VaR limits
        # This would calculate impact on portfolio VaR
        
        return RiskCheckResult(approved=True, reason="All risk checks passed")

@dataclass
class RiskCheckResult:
    approved: bool
    reason: str
    risk_score: Optional[int] = None

# Compliance Engine
class ComplianceEngine:
    async def check_otc_order(self, otc_order: OTCOrder, client: InstitutionalClient) -> 'ComplianceCheckResult':
        """Perform compliance checks on OTC order"""
        
        # Calculate order value
        order_value = otc_order.quantity * otc_order.quoted_price
        
        # Check for large trade reporting requirements
        if order_value > config.LARGE_TRADE_THRESHOLD:
            # Would trigger regulatory reporting
            pass
        
        # Check for suspicious activity
        if order_value > config.SUSPICIOUS_ACTIVITY_THRESHOLD:
            return ComplianceCheckResult(
                approved=False,
                reason=f"Large order value ${order_value} requires manual review"
            )
        
        # Check client KYC status
        if client.kyc_status != 'approved':
            return ComplianceCheckResult(
                approved=False,
                reason="Client KYC not approved"
            )
        
        return ComplianceCheckResult(approved=True, reason="All compliance checks passed")

@dataclass
class ComplianceCheckResult:
    approved: bool
    reason: str
    requires_reporting: bool = False

# Pricing Engine
class PricingEngine:
    async def calculate_otc_quote(
        self,
        base_asset: str,
        quote_asset: str,
        side: str,
        quantity: Decimal,
        market_price: Decimal,
        client_tier: ServiceTier
    ) -> Tuple[Decimal, Decimal, Decimal]:
        """Calculate OTC quote price, spread, and market impact"""
        
        # Base spread based on client tier
        tier_spreads = {
            ServiceTier.WHITE_GLOVE: Decimal("0.0005"),  # 5 bps
            ServiceTier.ELITE: Decimal("0.001"),         # 10 bps
            ServiceTier.PREMIUM: Decimal("0.0015"),      # 15 bps
            ServiceTier.BASIC: Decimal("0.002")          # 20 bps
        }
        
        base_spread = tier_spreads.get(client_tier, Decimal("0.002"))
        
        # Calculate market impact based on order size
        # Larger orders have higher market impact
        order_value = quantity * market_price
        
        if order_value > Decimal("10000000"):  # $10M+
            market_impact = Decimal("0.005")    # 50 bps
        elif order_value > Decimal("1000000"): # $1M+
            market_impact = Decimal("0.002")    # 20 bps
        else:
            market_impact = Decimal("0.001")    # 10 bps
        
        # Total spread
        total_spread = base_spread + market_impact
        
        # Calculate quote price
        if side == "BUY":
            quote_price = market_price * (Decimal("1") + total_spread)
        else:
            quote_price = market_price * (Decimal("1") - total_spread)
        
        return quote_price, base_spread, market_impact

# Initialize services manager
services_manager = InstitutionalServicesManager()

@app.on_event("startup")
async def startup_event():
    await services_manager.initialize()

# API Endpoints
@app.post("/api/v1/institutional/clients")
async def create_institutional_client(
    client_data: InstitutionalClientCreate,
    db: Session = Depends(get_db)
):
    """Create new institutional client"""
    try:
        client = await services_manager.create_institutional_client(client_data, db)
        return {
            "client_id": client.id,
            "client_code": client.client_code,
            "service_tier": client.service_tier,
            "status": "created"
        }
    except Exception as e:
        logger.error(f"Error creating institutional client: {e}")
        raise HTTPException(status_code=500, detail="Failed to create client")

@app.post("/api/v1/otc/quote")
async def request_otc_quote(
    order_request: OTCOrderRequest,
    client: InstitutionalClient = Depends(get_current_institutional_client),
    db: Session = Depends(get_db)
):
    """Request OTC quote"""
    try:
        quote = await services_manager.request_otc_quote(client, order_request, db)
        return quote
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error requesting OTC quote: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate quote")

@app.post("/api/v1/otc/accept/{order_id}")
async def accept_otc_quote(
    order_id: str,
    client: InstitutionalClient = Depends(get_current_institutional_client),
    db: Session = Depends(get_db)
):
    """Accept OTC quote and execute trade"""
    try:
        result = await services_manager.accept_otc_quote(client, order_id, db)
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error accepting OTC quote: {e}")
        raise HTTPException(status_code=500, detail="Failed to execute trade")

@app.get("/api/v1/otc/orders")
async def get_otc_orders(
    client: InstitutionalClient = Depends(get_current_institutional_client),
    db: Session = Depends(get_db),
    status: Optional[str] = None,
    limit: int = 50
):
    """Get OTC orders for client"""
    query = db.query(OTCOrder).filter(OTCOrder.client_id == client.id)
    
    if status:
        query = query.filter(OTCOrder.status == status)
    
    orders = query.order_by(OTCOrder.created_at.desc()).limit(limit).all()
    
    return {
        "orders": [
            {
                "order_id": order.order_id,
                "symbol": f"{order.base_asset}{order.quote_asset}",
                "side": order.side,
                "quantity": str(order.quantity),
                "quoted_price": str(order.quoted_price) if order.quoted_price else None,
                "status": order.status,
                "created_at": order.created_at.isoformat()
            }
            for order in orders
        ]
    }

@app.post("/api/v1/custody/accounts")
async def create_custody_account(
    account_data: CustodyAccountCreate,
    client: InstitutionalClient = Depends(get_current_institutional_client),
    db: Session = Depends(get_db)
):
    """Create custody account"""
    account_id = f"{client.client_code}_CUSTODY_{int(datetime.now().timestamp())}"
    
    custody_account = CustodyAccount(
        account_id=account_id,
        client_id=client.id,
        account_name=account_data.account_name,
        custody_type=account_data.custody_type,
        multi_sig_required=account_data.multi_sig_required,
        required_signatures=account_data.required_signatures,
        authorized_signers=account_data.authorized_signers,
        insurance_coverage=account_data.insurance_coverage,
        withdrawal_limits=account_data.withdrawal_limits
    )
    
    db.add(custody_account)
    db.commit()
    db.refresh(custody_account)
    
    return {
        "account_id": custody_account.account_id,
        "custody_type": custody_account.custody_type,
        "status": "created"
    }

@app.get("/api/v1/custody/accounts")
async def get_custody_accounts(
    client: InstitutionalClient = Depends(get_current_institutional_client),
    db: Session = Depends(get_db)
):
    """Get custody accounts for client"""
    accounts = db.query(CustodyAccount).filter(
        CustodyAccount.client_id == client.id,
        CustodyAccount.is_active == True
    ).all()
    
    return {
        "accounts": [
            {
                "account_id": account.account_id,
                "account_name": account.account_name,
                "custody_type": account.custody_type,
                "multi_sig_required": account.multi_sig_required,
                "insurance_coverage": str(account.insurance_coverage) if account.insurance_coverage else None,
                "created_at": account.created_at.isoformat()
            }
            for account in accounts
        ]
    }

@app.post("/api/v1/prime-brokerage/accounts")
async def create_prime_brokerage_account(
    account_data: PrimeBrokerageAccountCreate,
    client: InstitutionalClient = Depends(get_current_institutional_client),
    db: Session = Depends(get_db)
):
    """Create prime brokerage account"""
    
    # Check eligibility
    if not client.aum or client.aum < config.PRIME_BROKERAGE_MIN_AUM:
        raise HTTPException(
            status_code=400,
            detail=f"Minimum AUM of ${config.PRIME_BROKERAGE_MIN_AUM} required for prime brokerage"
        )
    
    account_id = f"{client.client_code}_PB"
    
    pb_account = PrimeBrokerageAccount(
        account_id=account_id,
        client_id=client.id,
        base_currency=account_data.base_currency,
        leverage_limit=account_data.leverage_limit,
        margin_requirement=account_data.margin_requirement,
        var_limit=account_data.var_limit
    )
    
    db.add(pb_account)
    db.commit()
    db.refresh(pb_account)
    
    return {
        "account_id": pb_account.account_id,
        "base_currency": pb_account.base_currency,
        "leverage_limit": str(pb_account.leverage_limit),
        "status": "created"
    }

@app.post("/api/v1/reports/generate")
async def generate_report(
    report_request: ReportRequest,
    client: InstitutionalClient = Depends(get_current_institutional_client),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Generate institutional report"""
    
    report_id = f"RPT_{client.client_code}_{int(datetime.now().timestamp())}"
    
    report = InstitutionalReport(
        report_id=report_id,
        client_id=client.id,
        report_type=report_request.report_type,
        report_period_start=report_request.period_start,
        report_period_end=report_request.period_end,
        file_format=report_request.file_format,
        delivery_method=report_request.delivery_method
    )
    
    db.add(report)
    db.commit()
    db.refresh(report)
    
    # Generate report in background
    background_tasks.add_task(generate_report_background, report.id, db)
    
    return {
        "report_id": report_id,
        "status": "generating",
        "estimated_completion": (datetime.now() + timedelta(minutes=5)).isoformat()
    }

async def generate_report_background(report_id: int, db: Session):
    """Background task to generate report"""
    # This would generate the actual report
    logger.info(f"Generating report {report_id}")
    
    # Mock report generation
    await asyncio.sleep(30)  # Simulate report generation time
    
    report = db.query(InstitutionalReport).filter(InstitutionalReport.id == report_id).first()
    if report:
        report.generated_at = datetime.now()
        report.file_url = f"https://reports.tigerex.com/{report.report_id}.pdf"
        report.delivery_status = "completed"
        db.commit()

@app.get("/api/v1/reports")
async def get_reports(
    client: InstitutionalClient = Depends(get_current_institutional_client),
    db: Session = Depends(get_db),
    report_type: Optional[str] = None,
    limit: int = 20
):
    """Get reports for client"""
    query = db.query(InstitutionalReport).filter(InstitutionalReport.client_id == client.id)
    
    if report_type:
        query = query.filter(InstitutionalReport.report_type == report_type)
    
    reports = query.order_by(InstitutionalReport.created_at.desc()).limit(limit).all()
    
    return {
        "reports": [
            {
                "report_id": report.report_id,
                "report_type": report.report_type,
                "period_start": report.report_period_start.isoformat(),
                "period_end": report.report_period_end.isoformat(),
                "file_format": report.file_format,
                "delivery_status": report.delivery_status,
                "file_url": report.file_url,
                "created_at": report.created_at.isoformat()
            }
            for report in reports
        ]
    }

@app.get("/api/v1/client/profile")
async def get_client_profile(
    client: InstitutionalClient = Depends(get_current_institutional_client)
):
    """Get institutional client profile"""
    return {
        "client_code": client.client_code,
        "legal_name": client.legal_name,
        "institution_type": client.institution_type,
        "service_tier": client.service_tier,
        "aum": str(client.aum) if client.aum else None,
        "annual_trading_volume": str(client.annual_trading_volume) if client.annual_trading_volume else None,
        "services_enabled": client.services_enabled,
        "kyc_status": client.kyc_status,
        "is_active": client.is_active,
        "created_at": client.created_at.isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
