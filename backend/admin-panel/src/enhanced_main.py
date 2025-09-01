"""
TigerEx Enhanced Admin Panel
Token/Coin Creation, Blockchain Integration, Trading Pair Management
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
import aiohttp
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator, HttpUrl
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, DECIMAL, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
import boto3
from web3 import Web3
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="TigerEx Enhanced Admin Panel",
    description="Token/Coin Creation, Blockchain Integration, Trading Pair Management",
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
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "admin-secret-key")
    
    # Blockchain Configuration
    ETHEREUM_RPC_URL = os.getenv("ETHEREUM_RPC_URL", "https://mainnet.infura.io/v3/your-key")
    POLYGON_RPC_URL = os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com")
    BSC_RPC_URL = os.getenv("BSC_RPC_URL", "https://bsc-dataseed.binance.org")
    ARBITRUM_RPC_URL = os.getenv("ARBITRUM_RPC_URL", "https://arb1.arbitrum.io/rpc")
    OPTIMISM_RPC_URL = os.getenv("OPTIMISM_RPC_URL", "https://mainnet.optimism.io")
    AVALANCHE_RPC_URL = os.getenv("AVALANCHE_RPC_URL", "https://api.avax.network/ext/bc/C/rpc")
    
    # External APIs
    COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")
    COINMARKETCAP_API_KEY = os.getenv("COINMARKETCAP_API_KEY")
    
    # AWS Configuration
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET", "tigerex-assets")

config = Config()

# Database setup
engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

security = HTTPBearer()

# Enums
class BlockchainNetwork(str, Enum):
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    BSC = "bsc"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    AVALANCHE = "avalanche"
    SOLANA = "solana"
    CARDANO = "cardano"
    POLKADOT = "polkadot"

class TokenStandard(str, Enum):
    ERC20 = "ERC20"
    ERC721 = "ERC721"
    ERC1155 = "ERC1155"
    BEP20 = "BEP20"
    SPL = "SPL"
    NATIVE = "NATIVE"

class TokenStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    DELISTED = "delisted"

class TradingPairStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    DELISTED = "delisted"

class AdminRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    ADMIN = "admin"
    MODERATOR = "moderator"
    SUPPORT = "support"

# Database Models
class Blockchain(Base):
    __tablename__ = "blockchains"
    
    id = Column(Integer, primary_key=True, index=True)
    blockchain_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Basic Information
    name = Column(String(100), nullable=False)
    symbol = Column(String(10), nullable=False)
    network = Column(SQLEnum(BlockchainNetwork), nullable=False)
    
    # Technical Details
    rpc_url = Column(String(500), nullable=False)
    chain_id = Column(Integer, nullable=False)
    block_explorer_url = Column(String(500))
    
    # Configuration
    is_testnet = Column(Boolean, default=False)
    supports_smart_contracts = Column(Boolean, default=True)
    native_currency_symbol = Column(String(10), nullable=False)
    native_currency_decimals = Column(Integer, default=18)
    
    # Integration Status
    is_active = Column(Boolean, default=True)
    is_trading_enabled = Column(Boolean, default=True)
    is_deposit_enabled = Column(Boolean, default=True)
    is_withdrawal_enabled = Column(Boolean, default=True)
    
    # Fees
    gas_price_gwei = Column(DECIMAL(20, 8))
    withdrawal_fee = Column(DECIMAL(20, 8))
    min_withdrawal_amount = Column(DECIMAL(20, 8))
    
    # Metadata
    description = Column(Text)
    logo_url = Column(String(500))
    website_url = Column(String(500))
    documentation_url = Column(String(500))
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    tokens = relationship("Token", back_populates="blockchain")

class Token(Base):
    __tablename__ = "tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    token_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Basic Information
    name = Column(String(100), nullable=False)
    symbol = Column(String(20), nullable=False, index=True)
    decimals = Column(Integer, nullable=False, default=18)
    
    # Blockchain Reference
    blockchain_id = Column(Integer, ForeignKey("blockchains.id"), nullable=False)
    blockchain = relationship("Blockchain", back_populates="tokens")
    
    # Contract Information
    contract_address = Column(String(100), index=True)
    token_standard = Column(SQLEnum(TokenStandard), nullable=False)
    
    # Supply Information
    total_supply = Column(DECIMAL(30, 8))
    circulating_supply = Column(DECIMAL(30, 8))
    max_supply = Column(DECIMAL(30, 8))
    
    # Market Data
    current_price_usd = Column(DECIMAL(20, 8))
    market_cap_usd = Column(DECIMAL(20, 2))
    volume_24h_usd = Column(DECIMAL(20, 2))
    price_change_24h = Column(DECIMAL(10, 4))
    
    # External IDs
    coingecko_id = Column(String(100))
    coinmarketcap_id = Column(String(100))
    
    # Metadata
    description = Column(Text)
    logo_url = Column(String(500))
    website_url = Column(String(500))
    whitepaper_url = Column(String(500))
    
    # Social Links
    twitter_url = Column(String(500))
    telegram_url = Column(String(500))
    discord_url = Column(String(500))
    github_url = Column(String(500))
    
    # Trading Configuration
    is_tradable = Column(Boolean, default=True)
    min_trade_amount = Column(DECIMAL(20, 8))
    max_trade_amount = Column(DECIMAL(20, 8))
    
    # Deposit/Withdrawal Configuration
    is_deposit_enabled = Column(Boolean, default=True)
    is_withdrawal_enabled = Column(Boolean, default=True)
    min_deposit_amount = Column(DECIMAL(20, 8))
    min_withdrawal_amount = Column(DECIMAL(20, 8))
    withdrawal_fee = Column(DECIMAL(20, 8))
    
    # Status
    status = Column(SQLEnum(TokenStatus), default=TokenStatus.PENDING)
    listing_date = Column(DateTime)
    delisting_date = Column(DateTime)
    
    # Verification
    is_verified = Column(Boolean, default=False)
    verification_level = Column(Integer, default=0)  # 0-5 verification levels
    
    # Risk Assessment
    risk_score = Column(Integer, default=50)  # 0-100
    risk_factors = Column(JSON)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    base_pairs = relationship("TradingPair", foreign_keys="TradingPair.base_token_id", back_populates="base_token")
    quote_pairs = relationship("TradingPair", foreign_keys="TradingPair.quote_token_id", back_populates="quote_token")

class TradingPair(Base):
    __tablename__ = "trading_pairs"
    
    id = Column(Integer, primary_key=True, index=True)
    pair_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Token References
    base_token_id = Column(Integer, ForeignKey("tokens.id"), nullable=False)
    quote_token_id = Column(Integer, ForeignKey("tokens.id"), nullable=False)
    base_token = relationship("Token", foreign_keys=[base_token_id], back_populates="base_pairs")
    quote_token = relationship("Token", foreign_keys=[quote_token_id], back_populates="quote_pairs")
    
    # Pair Information
    symbol = Column(String(20), nullable=False, unique=True, index=True)  # e.g., BTCUSDT
    
    # Trading Configuration
    min_order_size = Column(DECIMAL(20, 8), nullable=False)
    max_order_size = Column(DECIMAL(20, 8))
    min_price = Column(DECIMAL(20, 8))
    max_price = Column(DECIMAL(20, 8))
    price_precision = Column(Integer, default=8)
    quantity_precision = Column(Integer, default=8)
    
    # Fees
    maker_fee = Column(DECIMAL(5, 4), default=Decimal("0.001"))  # 0.1%
    taker_fee = Column(DECIMAL(5, 4), default=Decimal("0.001"))  # 0.1%
    
    # Market Data
    last_price = Column(DECIMAL(20, 8))
    volume_24h = Column(DECIMAL(30, 8), default=0)
    high_24h = Column(DECIMAL(20, 8))
    low_24h = Column(DECIMAL(20, 8))
    price_change_24h = Column(DECIMAL(10, 4), default=0)
    
    # Status
    status = Column(SQLEnum(TradingPairStatus), default=TradingPairStatus.ACTIVE)
    is_spot_enabled = Column(Boolean, default=True)
    is_margin_enabled = Column(Boolean, default=False)
    is_futures_enabled = Column(Boolean, default=False)
    
    # Listing Information
    listed_at = Column(DateTime, default=func.now())
    delisted_at = Column(DateTime)
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class TokenListing(Base):
    __tablename__ = "token_listings"
    
    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Token Information
    token_name = Column(String(100), nullable=False)
    token_symbol = Column(String(20), nullable=False)
    blockchain_network = Column(SQLEnum(BlockchainNetwork), nullable=False)
    contract_address = Column(String(100))
    
    # Applicant Information
    applicant_name = Column(String(100), nullable=False)
    applicant_email = Column(String(255), nullable=False)
    company_name = Column(String(255))
    
    # Token Details
    total_supply = Column(DECIMAL(30, 8))
    circulating_supply = Column(DECIMAL(30, 8))
    token_description = Column(Text)
    use_case = Column(Text)
    
    # Documentation
    whitepaper_url = Column(String(500))
    audit_report_url = Column(String(500))
    legal_opinion_url = Column(String(500))
    
    # Market Information
    current_exchanges = Column(JSON)  # List of current exchanges
    trading_volume = Column(DECIMAL(20, 2))
    market_cap = Column(DECIMAL(20, 2))
    
    # Application Status
    status = Column(String(20), default="pending")  # pending, under_review, approved, rejected
    review_notes = Column(Text)
    reviewed_by = Column(String(50))
    reviewed_at = Column(DateTime)
    
    # Fees
    listing_fee_paid = Column(Boolean, default=False)
    listing_fee_amount = Column(DECIMAL(20, 2))
    
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

# Pydantic Models
class BlockchainCreate(BaseModel):
    name: str
    symbol: str
    network: BlockchainNetwork
    rpc_url: HttpUrl
    chain_id: int
    block_explorer_url: Optional[HttpUrl] = None
    is_testnet: bool = False
    supports_smart_contracts: bool = True
    native_currency_symbol: str
    native_currency_decimals: int = 18
    description: Optional[str] = None
    logo_url: Optional[HttpUrl] = None
    website_url: Optional[HttpUrl] = None

class TokenCreate(BaseModel):
    name: str
    symbol: str
    decimals: int = 18
    blockchain_id: str
    contract_address: Optional[str] = None
    token_standard: TokenStandard
    total_supply: Optional[Decimal] = None
    description: Optional[str] = None
    logo_url: Optional[HttpUrl] = None
    website_url: Optional[HttpUrl] = None
    coingecko_id: Optional[str] = None
    
    @validator('symbol')
    def validate_symbol(cls, v):
        if len(v) < 2 or len(v) > 10:
            raise ValueError('Symbol must be between 2 and 10 characters')
        return v.upper()

class TradingPairCreate(BaseModel):
    base_token_symbol: str
    quote_token_symbol: str
    min_order_size: Decimal
    max_order_size: Optional[Decimal] = None
    price_precision: int = 8
    quantity_precision: int = 8
    maker_fee: Decimal = Decimal("0.001")
    taker_fee: Decimal = Decimal("0.001")
    is_margin_enabled: bool = False
    is_futures_enabled: bool = False

class TokenListingApplication(BaseModel):
    token_name: str
    token_symbol: str
    blockchain_network: BlockchainNetwork
    contract_address: Optional[str] = None
    applicant_name: str
    applicant_email: EmailStr
    company_name: Optional[str] = None
    total_supply: Decimal
    circulating_supply: Decimal
    token_description: str
    use_case: str
    whitepaper_url: Optional[HttpUrl] = None
    website_url: Optional[HttpUrl] = None

# Dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Simplified admin authentication
    return {"user_id": "admin_123", "role": AdminRole.SUPER_ADMIN}

# Admin Panel Manager
class AdminPanelManager:
    def __init__(self):
        self.redis_client = None
        self.web3_clients = {}
        self.s3_client = None
        
    async def initialize(self):
        """Initialize async components"""
        self.redis_client = await aioredis.from_url(config.REDIS_URL)
        
        # Initialize Web3 clients
        self.web3_clients = {
            BlockchainNetwork.ETHEREUM: Web3(Web3.HTTPProvider(config.ETHEREUM_RPC_URL)),
            BlockchainNetwork.POLYGON: Web3(Web3.HTTPProvider(config.POLYGON_RPC_URL)),
            BlockchainNetwork.BSC: Web3(Web3.HTTPProvider(config.BSC_RPC_URL)),
            BlockchainNetwork.ARBITRUM: Web3(Web3.HTTPProvider(config.ARBITRUM_RPC_URL)),
            BlockchainNetwork.OPTIMISM: Web3(Web3.HTTPProvider(config.OPTIMISM_RPC_URL)),
            BlockchainNetwork.AVALANCHE: Web3(Web3.HTTPProvider(config.AVALANCHE_RPC_URL))
        }
        
        # Initialize S3 client
        if config.AWS_ACCESS_KEY_ID:
            self.s3_client = boto3.client(
                's3',
                aws_access_key_id=config.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=config.AWS_SECRET_ACCESS_KEY
            )
    
    async def create_blockchain(self, blockchain_data: BlockchainCreate, admin: Dict[str, Any], db: Session):
        """Create new blockchain integration"""
        
        # Check if blockchain already exists
        existing = db.query(Blockchain).filter(
            (Blockchain.name == blockchain_data.name) | 
            (Blockchain.chain_id == blockchain_data.chain_id)
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Blockchain already exists")
        
        blockchain_id = f"CHAIN_{secrets.token_hex(8).upper()}"
        
        # Test RPC connection
        try:
            web3 = Web3(Web3.HTTPProvider(str(blockchain_data.rpc_url)))
            if not web3.is_connected():
                raise HTTPException(status_code=400, detail="Cannot connect to RPC URL")
            
            # Verify chain ID
            actual_chain_id = web3.eth.chain_id
            if actual_chain_id != blockchain_data.chain_id:
                raise HTTPException(status_code=400, detail=f"Chain ID mismatch. Expected {blockchain_data.chain_id}, got {actual_chain_id}")
        
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"RPC connection failed: {str(e)}")
        
        blockchain = Blockchain(
            blockchain_id=blockchain_id,
            name=blockchain_data.name,
            symbol=blockchain_data.symbol,
            network=blockchain_data.network,
            rpc_url=str(blockchain_data.rpc_url),
            chain_id=blockchain_data.chain_id,
            block_explorer_url=str(blockchain_data.block_explorer_url) if blockchain_data.block_explorer_url else None,
            is_testnet=blockchain_data.is_testnet,
            supports_smart_contracts=blockchain_data.supports_smart_contracts,
            native_currency_symbol=blockchain_data.native_currency_symbol,
            native_currency_decimals=blockchain_data.native_currency_decimals,
            description=blockchain_data.description,
            logo_url=str(blockchain_data.logo_url) if blockchain_data.logo_url else None,
            website_url=str(blockchain_data.website_url) if blockchain_data.website_url else None
        )
        
        db.add(blockchain)
        db.commit()
        db.refresh(blockchain)
        
        # Add to Web3 clients
        self.web3_clients[blockchain_data.network] = web3
        
        return blockchain
    
    async def create_token(self, token_data: TokenCreate, admin: Dict[str, Any], db: Session):
        """Create new token"""
        
        # Get blockchain
        blockchain = db.query(Blockchain).filter(
            Blockchain.blockchain_id == token_data.blockchain_id
        ).first()
        
        if not blockchain:
            raise HTTPException(status_code=404, detail="Blockchain not found")
        
        # Check if token already exists
        existing = db.query(Token).filter(
            Token.symbol == token_data.symbol,
            Token.blockchain_id == blockchain.id
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Token already exists on this blockchain")
        
        token_id = f"TOKEN_{secrets.token_hex(8).upper()}"
        
        # Validate contract address if provided
        if token_data.contract_address and blockchain.supports_smart_contracts:
            await self.validate_token_contract(token_data.contract_address, blockchain, token_data)
        
        # Fetch market data if external IDs provided
        market_data = {}
        if token_data.coingecko_id:
            market_data = await self.fetch_coingecko_data(token_data.coingecko_id)
        
        token = Token(
            token_id=token_id,
            name=token_data.name,
            symbol=token_data.symbol,
            decimals=token_data.decimals,
            blockchain_id=blockchain.id,
            contract_address=token_data.contract_address,
            token_standard=token_data.token_standard,
            total_supply=token_data.total_supply,
            description=token_data.description,
            logo_url=str(token_data.logo_url) if token_data.logo_url else None,
            website_url=str(token_data.website_url) if token_data.website_url else None,
            coingecko_id=token_data.coingecko_id,
            current_price_usd=market_data.get('current_price'),
            market_cap_usd=market_data.get('market_cap'),
            volume_24h_usd=market_data.get('volume_24h')
        )
        
        db.add(token)
        db.commit()
        db.refresh(token)
        
        return token
    
    async def create_trading_pair(self, pair_data: TradingPairCreate, admin: Dict[str, Any], db: Session):
        """Create new trading pair"""
        
        # Get tokens
        base_token = db.query(Token).filter(Token.symbol == pair_data.base_token_symbol).first()
        quote_token = db.query(Token).filter(Token.symbol == pair_data.quote_token_symbol).first()
        
        if not base_token:
            raise HTTPException(status_code=404, detail=f"Base token {pair_data.base_token_symbol} not found")
        
        if not quote_token:
            raise HTTPException(status_code=404, detail=f"Quote token {pair_data.quote_token_symbol} not found")
        
        # Check if pair already exists
        existing = db.query(TradingPair).filter(
            TradingPair.base_token_id == base_token.id,
            TradingPair.quote_token_id == quote_token.id
        ).first()
        
        if existing:
            raise HTTPException(status_code=400, detail="Trading pair already exists")
        
        pair_id = f"PAIR_{secrets.token_hex(8).upper()}"
        symbol = f"{base_token.symbol}{quote_token.symbol}"
        
        trading_pair = TradingPair(
            pair_id=pair_id,
            base_token_id=base_token.id,
            quote_token_id=quote_token.id,
            symbol=symbol,
            min_order_size=pair_data.min_order_size,
            max_order_size=pair_data.max_order_size,
            price_precision=pair_data.price_precision,
            quantity_precision=pair_data.quantity_precision,
            maker_fee=pair_data.maker_fee,
            taker_fee=pair_data.taker_fee,
            is_margin_enabled=pair_data.is_margin_enabled,
            is_futures_enabled=pair_data.is_futures_enabled
        )
        
        db.add(trading_pair)
        db.commit()
        db.refresh(trading_pair)
        
        return trading_pair
    
    async def validate_token_contract(self, contract_address: str, blockchain: Blockchain, token_data: TokenCreate):
        """Validate token contract on blockchain"""
        
        web3 = self.web3_clients.get(blockchain.network)
        if not web3:
            return
        
        try:
            # Check if address is valid
            if not web3.is_address(contract_address):
                raise HTTPException(status_code=400, detail="Invalid contract address")
            
            # Check if contract exists
            code = web3.eth.get_code(web3.to_checksum_address(contract_address))
            if code == b'':
                raise HTTPException(status_code=400, detail="No contract found at address")
            
            # For ERC20 tokens, validate basic functions
            if token_data.token_standard == TokenStandard.ERC20:
                # This would include more comprehensive contract validation
                # For now, we'll just check that it's a contract
                pass
                
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Contract validation failed: {str(e)}")
    
    async def fetch_coingecko_data(self, coingecko_id: str) -> Dict[str, Any]:
        """Fetch token data from CoinGecko"""
        
        try:
            url = f"https://api.coingecko.com/api/v3/coins/{coingecko_id}"
            headers = {}
            
            if config.COINGECKO_API_KEY:
                headers["X-CG-Demo-API-Key"] = config.COINGECKO_API_KEY
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            'current_price': data.get('market_data', {}).get('current_price', {}).get('usd'),
                            'market_cap': data.get('market_data', {}).get('market_cap', {}).get('usd'),
                            'volume_24h': data.get('market_data', {}).get('total_volume', {}).get('usd')
                        }
        except Exception as e:
            logger.error(f"Error fetching CoinGecko data: {e}")
        
        return {}
    
    async def update_token_market_data(self, db: Session):
        """Update market data for all tokens"""
        
        tokens = db.query(Token).filter(
            Token.coingecko_id.isnot(None),
            Token.status == TokenStatus.ACTIVE
        ).all()
        
        for token in tokens:
            try:
                market_data = await self.fetch_coingecko_data(token.coingecko_id)
                
                if market_data:
                    token.current_price_usd = market_data.get('current_price')
                    token.market_cap_usd = market_data.get('market_cap')
                    token.volume_24h_usd = market_data.get('volume_24h')
                    
                    db.commit()
                    
            except Exception as e:
                logger.error(f"Error updating market data for {token.symbol}: {e}")
    
    async def submit_listing_application(self, application_data: TokenListingApplication, db: Session):
        """Submit token listing application"""
        
        listing_id = f"LISTING_{secrets.token_hex(8).upper()}"
        
        listing = TokenListing(
            listing_id=listing_id,
            token_name=application_data.token_name,
            token_symbol=application_data.token_symbol,
            blockchain_network=application_data.blockchain_network,
            contract_address=application_data.contract_address,
            applicant_name=application_data.applicant_name,
            applicant_email=application_data.applicant_email,
            company_name=application_data.company_name,
            total_supply=application_data.total_supply,
            circulating_supply=application_data.circulating_supply,
            token_description=application_data.token_description,
            use_case=application_data.use_case,
            whitepaper_url=str(application_data.whitepaper_url) if application_data.whitepaper_url else None
        )
        
        db.add(listing)
        db.commit()
        db.refresh(listing)
        
        return listing

# Initialize admin manager
admin_manager = AdminPanelManager()

@app.on_event("startup")
async def startup_event():
    await admin_manager.initialize()

# API Endpoints
@app.post("/api/v1/admin/blockchains")
async def create_blockchain(
    blockchain_data: BlockchainCreate,
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create new blockchain integration"""
    blockchain = await admin_manager.create_blockchain(blockchain_data, current_admin, db)
    return {
        "blockchain_id": blockchain.blockchain_id,
        "name": blockchain.name,
        "network": blockchain.network,
        "chain_id": blockchain.chain_id,
        "status": "created"
    }

@app.get("/api/v1/admin/blockchains")
async def get_blockchains(
    is_active: Optional[bool] = None,
    network: Optional[BlockchainNetwork] = None,
    db: Session = Depends(get_db)
):
    """Get all blockchains"""
    query = db.query(Blockchain)
    
    if is_active is not None:
        query = query.filter(Blockchain.is_active == is_active)
    
    if network:
        query = query.filter(Blockchain.network == network)
    
    blockchains = query.all()
    
    return {
        "blockchains": [
            {
                "blockchain_id": bc.blockchain_id,
                "name": bc.name,
                "symbol": bc.symbol,
                "network": bc.network,
                "chain_id": bc.chain_id,
                "rpc_url": bc.rpc_url,
                "is_active": bc.is_active,
                "is_trading_enabled": bc.is_trading_enabled,
                "native_currency_symbol": bc.native_currency_symbol,
                "created_at": bc.created_at.isoformat()
            }
            for bc in blockchains
        ]
    }

@app.post("/api/v1/admin/tokens")
async def create_token(
    token_data: TokenCreate,
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create new token"""
    token = await admin_manager.create_token(token_data, current_admin, db)
    return {
        "token_id": token.token_id,
        "name": token.name,
        "symbol": token.symbol,
        "blockchain": token.blockchain.name,
        "status": token.status
    }

@app.get("/api/v1/admin/tokens")
async def get_tokens(
    status: Optional[TokenStatus] = None,
    blockchain_id: Optional[str] = None,
    is_tradable: Optional[bool] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get all tokens"""
    query = db.query(Token)
    
    if status:
        query = query.filter(Token.status == status)
    
    if blockchain_id:
        blockchain = db.query(Blockchain).filter(Blockchain.blockchain_id == blockchain_id).first()
        if blockchain:
            query = query.filter(Token.blockchain_id == blockchain.id)
    
    if is_tradable is not None:
        query = query.filter(Token.is_tradable == is_tradable)
    
    tokens = query.offset(offset).limit(limit).all()
    
    return {
        "tokens": [
            {
                "token_id": token.token_id,
                "name": token.name,
                "symbol": token.symbol,
                "blockchain": token.blockchain.name,
                "contract_address": token.contract_address,
                "status": token.status,
                "current_price_usd": str(token.current_price_usd) if token.current_price_usd else None,
                "market_cap_usd": str(token.market_cap_usd) if token.market_cap_usd else None,
                "is_tradable": token.is_tradable,
                "created_at": token.created_at.isoformat()
            }
            for token in tokens
        ]
    }

@app.post("/api/v1/admin/trading-pairs")
async def create_trading_pair(
    pair_data: TradingPairCreate,
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Create new trading pair"""
    pair = await admin_manager.create_trading_pair(pair_data, current_admin, db)
    return {
        "pair_id": pair.pair_id,
        "symbol": pair.symbol,
        "base_token": pair.base_token.symbol,
        "quote_token": pair.quote_token.symbol,
        "status": pair.status
    }

@app.get("/api/v1/admin/trading-pairs")
async def get_trading_pairs(
    status: Optional[TradingPairStatus] = None,
    base_token: Optional[str] = None,
    quote_token: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """Get all trading pairs"""
    query = db.query(TradingPair)
    
    if status:
        query = query.filter(TradingPair.status == status)
    
    if base_token:
        base_token_obj = db.query(Token).filter(Token.symbol == base_token).first()
        if base_token_obj:
            query = query.filter(TradingPair.base_token_id == base_token_obj.id)
    
    if quote_token:
        quote_token_obj = db.query(Token).filter(Token.symbol == quote_token).first()
        if quote_token_obj:
            query = query.filter(TradingPair.quote_token_id == quote_token_obj.id)
    
    pairs = query.offset(offset).limit(limit).all()
    
    return {
        "trading_pairs": [
            {
                "pair_id": pair.pair_id,
                "symbol": pair.symbol,
                "base_token": pair.base_token.symbol,
                "quote_token": pair.quote_token.symbol,
                "status": pair.status,
                "last_price": str(pair.last_price) if pair.last_price else None,
                "volume_24h": str(pair.volume_24h),
                "price_change_24h": str(pair.price_change_24h),
                "is_spot_enabled": pair.is_spot_enabled,
                "is_margin_enabled": pair.is_margin_enabled,
                "is_futures_enabled": pair.is_futures_enabled,
                "created_at": pair.created_at.isoformat()
            }
            for pair in pairs
        ]
    }

@app.put("/api/v1/admin/trading-pairs/{pair_id}/status")
async def update_trading_pair_status(
    pair_id: str,
    status: TradingPairStatus,
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Update trading pair status"""
    pair = db.query(TradingPair).filter(TradingPair.pair_id == pair_id).first()
    
    if not pair:
        raise HTTPException(status_code=404, detail="Trading pair not found")
    
    pair.status = status
    if status == TradingPairStatus.DELISTED:
        pair.delisted_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "pair_id": pair_id,
        "status": status,
        "message": "Trading pair status updated successfully"
    }

@app.delete("/api/v1/admin/trading-pairs/{pair_id}")
async def delete_trading_pair(
    pair_id: str,
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Delete trading pair"""
    pair = db.query(TradingPair).filter(TradingPair.pair_id == pair_id).first()
    
    if not pair:
        raise HTTPException(status_code=404, detail="Trading pair not found")
    
    # Set status to delisted instead of actual deletion
    pair.status = TradingPairStatus.DELISTED
    pair.delisted_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": "Trading pair deleted successfully"}

@app.post("/api/v1/admin/token-listings")
async def submit_token_listing(
    application_data: TokenListingApplication,
    db: Session = Depends(get_db)
):
    """Submit token listing application"""
    listing = await admin_manager.submit_listing_application(application_data, db)
    return {
        "listing_id": listing.listing_id,
        "token_symbol": listing.token_symbol,
        "status": listing.status,
        "message": "Token listing application submitted successfully"
    }

@app.get("/api/v1/admin/token-listings")
async def get_token_listings(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get token listing applications"""
    query = db.query(TokenListing)
    
    if status:
        query = query.filter(TokenListing.status == status)
    
    listings = query.order_by(TokenListing.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "listings": [
            {
                "listing_id": listing.listing_id,
                "token_name": listing.token_name,
                "token_symbol": listing.token_symbol,
                "blockchain_network": listing.blockchain_network,
                "applicant_name": listing.applicant_name,
                "applicant_email": listing.applicant_email,
                "status": listing.status,
                "created_at": listing.created_at.isoformat()
            }
            for listing in listings
        ]
    }

@app.put("/api/v1/admin/token-listings/{listing_id}/review")
async def review_token_listing(
    listing_id: str,
    status: str,
    review_notes: Optional[str] = None,
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Review token listing application"""
    listing = db.query(TokenListing).filter(TokenListing.listing_id == listing_id).first()
    
    if not listing:
        raise HTTPException(status_code=404, detail="Token listing not found")
    
    listing.status = status
    listing.review_notes = review_notes
    listing.reviewed_by = current_admin["user_id"]
    listing.reviewed_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "listing_id": listing_id,
        "status": status,
        "message": "Token listing reviewed successfully"
    }

@app.post("/api/v1/admin/market-data/update")
async def update_market_data(
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """Update market data for all tokens"""
    background_tasks.add_task(admin_manager.update_token_market_data, db)
    return {"message": "Market data update initiated"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "enhanced-admin-panel"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
