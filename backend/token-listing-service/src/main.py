"""
TigerEx Token Listing & Management Service
Advanced Python service for CEX/DEX token listings, liquidity management, and custom blockchain integration
"""

import asyncio
import json
import logging
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

import aiohttp
import asyncpg
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator
import web3
from web3 import Web3
from eth_account import Account
import ccxt.async_support as ccxt
from kafka import KafkaProducer
import boto3
from botocore.exceptions import ClientError
import ipfshttpclient
from celery import Celery
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import tensorflow as tf

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="TigerEx Token Listing Service",
    description="Advanced token listing and liquidity management for CEX/DEX",
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
    
    # Blockchain RPC URLs
    ETHEREUM_RPC = os.getenv("ETHEREUM_RPC", "https://mainnet.infura.io/v3/YOUR_KEY")
    BSC_RPC = os.getenv("BSC_RPC", "https://bsc-dataseed.binance.org/")
    POLYGON_RPC = os.getenv("POLYGON_RPC", "https://polygon-rpc.com/")
    AVALANCHE_RPC = os.getenv("AVALANCHE_RPC", "https://api.avax.network/ext/bc/C/rpc")
    ARBITRUM_RPC = os.getenv("ARBITRUM_RPC", "https://arb1.arbitrum.io/rpc")
    OPTIMISM_RPC = os.getenv("OPTIMISM_RPC", "https://mainnet.optimism.io")
    
    # Custom EVM chains
    CUSTOM_EVM_CHAINS = json.loads(os.getenv("CUSTOM_EVM_CHAINS", "{}"))
    
    # Exchange API keys
    BINANCE_API_KEY = os.getenv("BINANCE_API_KEY")
    BINANCE_SECRET = os.getenv("BINANCE_SECRET")
    BYBIT_API_KEY = os.getenv("BYBIT_API_KEY")
    BYBIT_SECRET = os.getenv("BYBIT_SECRET")
    OKX_API_KEY = os.getenv("OKX_API_KEY")
    OKX_SECRET = os.getenv("OKX_SECRET")
    OKX_PASSPHRASE = os.getenv("OKX_PASSPHRASE")
    
    # AWS/IPFS
    AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY")
    AWS_SECRET_KEY = os.getenv("AWS_SECRET_KEY")
    IPFS_NODE = os.getenv("IPFS_NODE", "/ip4/127.0.0.1/tcp/5001")

config = Config()

# Enums
class TokenType(str, Enum):
    ERC20 = "ERC20"
    BEP20 = "BEP20"
    TRC20 = "TRC20"
    SPL = "SPL"
    NATIVE = "NATIVE"
    CUSTOM_EVM = "CUSTOM_EVM"
    CUSTOM_WEB3 = "CUSTOM_WEB3"

class ListingStatus(str, Enum):
    PENDING = "PENDING"
    UNDER_REVIEW = "UNDER_REVIEW"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    LISTED = "LISTED"
    DELISTED = "DELISTED"

class ListingType(str, Enum):
    CEX_ONLY = "CEX_ONLY"
    DEX_ONLY = "DEX_ONLY"
    HYBRID = "HYBRID"

class LiquiditySource(str, Enum):
    BINANCE = "BINANCE"
    BYBIT = "BYBIT"
    OKX = "OKX"
    UNISWAP = "UNISWAP"
    PANCAKESWAP = "PANCAKESWAP"
    SUSHISWAP = "SUSHISWAP"
    INTERNAL = "INTERNAL"

# Data Models
@dataclass
class TokenInfo:
    symbol: str
    name: str
    contract_address: str
    decimals: int
    total_supply: str
    token_type: TokenType
    blockchain: str
    website: str
    whitepaper_url: str
    social_links: Dict[str, str]
    logo_url: str
    description: str
    use_case: str
    team_info: Dict[str, Any]
    tokenomics: Dict[str, Any]
    audit_reports: List[str]
    kyc_verified: bool
    is_mintable: bool
    is_burnable: bool
    is_pausable: bool
    max_supply: Optional[str] = None
    circulating_supply: Optional[str] = None

@dataclass
class ListingApplication:
    id: str
    token_info: TokenInfo
    listing_type: ListingType
    requested_pairs: List[str]
    listing_fee: Decimal
    market_maker_commitment: Optional[Dict[str, Any]]
    compliance_documents: List[str]
    technical_integration: Dict[str, Any]
    marketing_plan: Optional[Dict[str, Any]]
    status: ListingStatus
    submitted_by: str
    submitted_at: datetime
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    listing_date: Optional[datetime] = None
    rejection_reason: Optional[str] = None

@dataclass
class LiquidityPool:
    id: str
    token_a: str
    token_b: str
    pool_address: str
    dex_protocol: str
    blockchain: str
    liquidity_usd: Decimal
    volume_24h: Decimal
    fee_tier: Decimal
    apy: Decimal
    is_active: bool
    created_at: datetime

@dataclass
class LiquidityProvider:
    id: str
    user_id: str
    pool_id: str
    token_a_amount: Decimal
    token_b_amount: Decimal
    lp_tokens: Decimal
    entry_price_a: Decimal
    entry_price_b: Decimal
    rewards_earned: Decimal
    impermanent_loss: Decimal
    created_at: datetime

# Pydantic Models for API
class TokenInfoRequest(BaseModel):
    symbol: str
    name: str
    contract_address: str
    decimals: int
    total_supply: str
    token_type: TokenType
    blockchain: str
    website: str
    whitepaper_url: str
    social_links: Dict[str, str]
    description: str
    use_case: str
    team_info: Dict[str, Any]
    tokenomics: Dict[str, Any]
    kyc_verified: bool = False
    is_mintable: bool = False
    is_burnable: bool = False
    is_pausable: bool = False

class ListingApplicationRequest(BaseModel):
    token_info: TokenInfoRequest
    listing_type: ListingType
    requested_pairs: List[str]
    market_maker_commitment: Optional[Dict[str, Any]] = None
    marketing_plan: Optional[Dict[str, Any]] = None

class LiquidityProvisionRequest(BaseModel):
    token_a: str
    token_b: str
    amount_a: Decimal
    amount_b: Decimal
    dex_protocol: str
    blockchain: str
    slippage_tolerance: Decimal = Decimal("0.5")

class CustomBlockchainRequest(BaseModel):
    name: str
    chain_id: int
    rpc_url: str
    explorer_url: str
    native_currency: Dict[str, str]
    is_testnet: bool = False
    consensus_mechanism: str
    block_time: int
    gas_token: str

# Database connection
async def get_db_connection():
    return await asyncpg.connect(config.DATABASE_URL)

# Redis connection
async def get_redis_connection():
    return await redis.from_url(config.REDIS_URL)

# Blockchain Integration Manager
class BlockchainManager:
    def __init__(self):
        self.web3_instances = {}
        self.custom_chains = {}
        self.initialize_chains()
    
    def initialize_chains(self):
        """Initialize Web3 instances for supported blockchains"""
        chains = {
            "ethereum": config.ETHEREUM_RPC,
            "bsc": config.BSC_RPC,
            "polygon": config.POLYGON_RPC,
            "avalanche": config.AVALANCHE_RPC,
            "arbitrum": config.ARBITRUM_RPC,
            "optimism": config.OPTIMISM_RPC,
        }
        
        for chain, rpc_url in chains.items():
            try:
                self.web3_instances[chain] = Web3(Web3.HTTPProvider(rpc_url))
                logger.info(f"Connected to {chain} blockchain")
            except Exception as e:
                logger.error(f"Failed to connect to {chain}: {e}")
        
        # Initialize custom EVM chains
        for chain_name, chain_config in config.CUSTOM_EVM_CHAINS.items():
            try:
                self.web3_instances[chain_name] = Web3(Web3.HTTPProvider(chain_config["rpc_url"]))
                self.custom_chains[chain_name] = chain_config
                logger.info(f"Connected to custom EVM chain: {chain_name}")
            except Exception as e:
                logger.error(f"Failed to connect to custom chain {chain_name}: {e}")
    
    async def get_token_info(self, contract_address: str, blockchain: str) -> Dict[str, Any]:
        """Get token information from blockchain"""
        if blockchain not in self.web3_instances:
            raise ValueError(f"Blockchain {blockchain} not supported")
        
        w3 = self.web3_instances[blockchain]
        
        # ERC20 ABI (simplified)
        erc20_abi = [
            {"constant": True, "inputs": [], "name": "name", "outputs": [{"name": "", "type": "string"}], "type": "function"},
            {"constant": True, "inputs": [], "name": "symbol", "outputs": [{"name": "", "type": "string"}], "type": "function"},
            {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
            {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
        ]
        
        try:
            contract = w3.eth.contract(address=Web3.toChecksumAddress(contract_address), abi=erc20_abi)
            
            name = contract.functions.name().call()
            symbol = contract.functions.symbol().call()
            decimals = contract.functions.decimals().call()
            total_supply = contract.functions.totalSupply().call()
            
            return {
                "name": name,
                "symbol": symbol,
                "decimals": decimals,
                "total_supply": str(total_supply),
                "contract_address": contract_address,
                "blockchain": blockchain
            }
        except Exception as e:
            logger.error(f"Error getting token info: {e}")
            raise HTTPException(status_code=400, detail=f"Invalid token contract: {e}")
    
    async def validate_contract(self, contract_address: str, blockchain: str) -> bool:
        """Validate if contract exists and is a valid token"""
        try:
            token_info = await self.get_token_info(contract_address, blockchain)
            return bool(token_info.get("symbol"))
        except:
            return False
    
    async def add_custom_evm_chain(self, chain_config: CustomBlockchainRequest) -> bool:
        """Add a custom EVM-compatible blockchain"""
        try:
            w3 = Web3(Web3.HTTPProvider(chain_config.rpc_url))
            
            # Test connection
            chain_id = w3.eth.chain_id
            if chain_id != chain_config.chain_id:
                raise ValueError("Chain ID mismatch")
            
            # Store configuration
            self.web3_instances[chain_config.name] = w3
            self.custom_chains[chain_config.name] = {
                "chain_id": chain_config.chain_id,
                "rpc_url": chain_config.rpc_url,
                "explorer_url": chain_config.explorer_url,
                "native_currency": chain_config.native_currency,
                "is_testnet": chain_config.is_testnet,
                "consensus_mechanism": chain_config.consensus_mechanism,
                "block_time": chain_config.block_time,
                "gas_token": chain_config.gas_token
            }
            
            # Save to database
            db = await get_db_connection()
            await db.execute("""
                INSERT INTO custom_blockchains (name, chain_id, rpc_url, explorer_url, 
                                               native_currency, is_testnet, consensus_mechanism, 
                                               block_time, gas_token, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                ON CONFLICT (name) DO UPDATE SET
                    rpc_url = EXCLUDED.rpc_url,
                    explorer_url = EXCLUDED.explorer_url,
                    updated_at = NOW()
            """, chain_config.name, chain_config.chain_id, chain_config.rpc_url,
                chain_config.explorer_url, json.dumps(chain_config.native_currency),
                chain_config.is_testnet, chain_config.consensus_mechanism,
                chain_config.block_time, chain_config.gas_token, datetime.utcnow())
            
            await db.close()
            
            logger.info(f"Added custom EVM chain: {chain_config.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add custom EVM chain: {e}")
            return False

# Liquidity Manager
class LiquidityManager:
    def __init__(self):
        self.exchanges = {}
        self.initialize_exchanges()
    
    def initialize_exchanges(self):
        """Initialize exchange connections"""
        try:
            if config.BINANCE_API_KEY:
                self.exchanges['binance'] = ccxt.binance({
                    'apiKey': config.BINANCE_API_KEY,
                    'secret': config.BINANCE_SECRET,
                    'sandbox': False,
                    'enableRateLimit': True,
                })
            
            if config.BYBIT_API_KEY:
                self.exchanges['bybit'] = ccxt.bybit({
                    'apiKey': config.BYBIT_API_KEY,
                    'secret': config.BYBIT_SECRET,
                    'sandbox': False,
                    'enableRateLimit': True,
                })
            
            if config.OKX_API_KEY:
                self.exchanges['okx'] = ccxt.okx({
                    'apiKey': config.OKX_API_KEY,
                    'secret': config.OKX_SECRET,
                    'password': config.OKX_PASSPHRASE,
                    'sandbox': False,
                    'enableRateLimit': True,
                })
            
            logger.info(f"Initialized {len(self.exchanges)} exchange connections")
        except Exception as e:
            logger.error(f"Failed to initialize exchanges: {e}")
    
    async def get_shared_liquidity(self, symbol: str) -> Dict[str, Any]:
        """Get aggregated liquidity from multiple exchanges"""
        liquidity_data = {}
        
        for exchange_name, exchange in self.exchanges.items():
            try:
                ticker = await exchange.fetch_ticker(symbol)
                orderbook = await exchange.fetch_order_book(symbol, limit=100)
                
                liquidity_data[exchange_name] = {
                    "price": ticker["last"],
                    "volume_24h": ticker["quoteVolume"],
                    "bid_depth": sum([bid[1] for bid in orderbook["bids"][:10]]),
                    "ask_depth": sum([ask[1] for ask in orderbook["asks"][:10]]),
                    "spread": (orderbook["asks"][0][0] - orderbook["bids"][0][0]) / orderbook["bids"][0][0] * 100,
                    "timestamp": ticker["timestamp"]
                }
            except Exception as e:
                logger.error(f"Error fetching liquidity from {exchange_name}: {e}")
        
        return liquidity_data
    
    async def create_liquidity_pool(self, pool_request: LiquidityProvisionRequest, user_id: str) -> str:
        """Create a new liquidity pool"""
        pool_id = str(uuid.uuid4())
        
        # Calculate optimal amounts and create pool
        db = await get_db_connection()
        
        try:
            await db.execute("""
                INSERT INTO liquidity_pools (id, token_a, token_b, dex_protocol, blockchain,
                                           liquidity_usd, volume_24h, fee_tier, apy, is_active, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """, pool_id, pool_request.token_a, pool_request.token_b, pool_request.dex_protocol,
                pool_request.blockchain, 0, 0, Decimal("0.3"), Decimal("0"), True, datetime.utcnow())
            
            # Record liquidity provision
            await db.execute("""
                INSERT INTO liquidity_providers (id, user_id, pool_id, token_a_amount, token_b_amount,
                                               lp_tokens, entry_price_a, entry_price_b, rewards_earned,
                                               impermanent_loss, created_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """, str(uuid.uuid4()), user_id, pool_id, pool_request.amount_a, pool_request.amount_b,
                Decimal("1000"), Decimal("1"), Decimal("1"), Decimal("0"), Decimal("0"), datetime.utcnow())
            
            await db.close()
            return pool_id
            
        except Exception as e:
            await db.close()
            logger.error(f"Error creating liquidity pool: {e}")
            raise HTTPException(status_code=500, detail="Failed to create liquidity pool")

# Token Listing Manager
class TokenListingManager:
    def __init__(self):
        self.blockchain_manager = BlockchainManager()
        self.liquidity_manager = LiquidityManager()
        self.ml_model = self.load_risk_assessment_model()
    
    def load_risk_assessment_model(self):
        """Load ML model for token risk assessment"""
        try:
            # Simple isolation forest for anomaly detection
            return IsolationForest(contamination=0.1, random_state=42)
        except Exception as e:
            logger.error(f"Failed to load ML model: {e}")
            return None
    
    async def submit_listing_application(self, application: ListingApplicationRequest, user_id: str) -> str:
        """Submit a new token listing application"""
        application_id = str(uuid.uuid4())
        
        # Validate token contract
        if application.token_info.contract_address:
            is_valid = await self.blockchain_manager.validate_contract(
                application.token_info.contract_address,
                application.token_info.blockchain
            )
            if not is_valid:
                raise HTTPException(status_code=400, detail="Invalid token contract")
        
        # Get on-chain token info
        if application.token_info.contract_address:
            on_chain_info = await self.blockchain_manager.get_token_info(
                application.token_info.contract_address,
                application.token_info.blockchain
            )
            
            # Verify provided info matches on-chain data
            if (application.token_info.symbol != on_chain_info["symbol"] or
                application.token_info.decimals != on_chain_info["decimals"]):
                raise HTTPException(status_code=400, detail="Token info mismatch with on-chain data")
        
        # Calculate listing fee
        listing_fee = self.calculate_listing_fee(application)
        
        # Store application
        db = await get_db_connection()
        
        try:
            await db.execute("""
                INSERT INTO listing_applications (id, token_info, listing_type, requested_pairs,
                                                listing_fee, market_maker_commitment, compliance_documents,
                                                technical_integration, marketing_plan, status,
                                                submitted_by, submitted_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12)
            """, application_id, json.dumps(asdict(application.token_info)), application.listing_type.value,
                json.dumps(application.requested_pairs), listing_fee,
                json.dumps(application.market_maker_commitment) if application.market_maker_commitment else None,
                json.dumps([]), json.dumps({}),
                json.dumps(application.marketing_plan) if application.marketing_plan else None,
                ListingStatus.PENDING.value, user_id, datetime.utcnow())
            
            await db.close()
            
            # Trigger automated review
            await self.trigger_automated_review(application_id)
            
            return application_id
            
        except Exception as e:
            await db.close()
            logger.error(f"Error submitting listing application: {e}")
            raise HTTPException(status_code=500, detail="Failed to submit application")
    
    def calculate_listing_fee(self, application: ListingApplicationRequest) -> Decimal:
        """Calculate listing fee based on various factors"""
        base_fee = Decimal("10000")  # $10,000 base fee
        
        # Adjust based on listing type
        if application.listing_type == ListingType.HYBRID:
            base_fee *= Decimal("1.5")
        elif application.listing_type == ListingType.DEX_ONLY:
            base_fee *= Decimal("0.5")
        
        # Adjust based on number of pairs
        pair_multiplier = Decimal(str(len(application.requested_pairs))) * Decimal("0.1")
        base_fee *= (Decimal("1") + pair_multiplier)
        
        # Market maker commitment discount
        if application.market_maker_commitment:
            commitment_amount = Decimal(str(application.market_maker_commitment.get("amount", 0)))
            if commitment_amount >= Decimal("1000000"):  # $1M+
                base_fee *= Decimal("0.7")
            elif commitment_amount >= Decimal("500000"):  # $500K+
                base_fee *= Decimal("0.8")
        
        return base_fee
    
    async def trigger_automated_review(self, application_id: str):
        """Trigger automated review process"""
        try:
            # Get application data
            db = await get_db_connection()
            row = await db.fetchrow("""
                SELECT * FROM listing_applications WHERE id = $1
            """, application_id)
            await db.close()
            
            if not row:
                return
            
            token_info = json.loads(row["token_info"])
            
            # Perform automated checks
            risk_score = await self.assess_token_risk(token_info)
            compliance_score = await self.check_compliance(token_info)
            technical_score = await self.validate_technical_requirements(token_info)
            
            # Calculate overall score
            overall_score = (risk_score + compliance_score + technical_score) / 3
            
            # Auto-approve if score is high enough
            if overall_score >= 0.8:
                await self.update_application_status(application_id, ListingStatus.APPROVED)
            elif overall_score <= 0.3:
                await self.update_application_status(
                    application_id, 
                    ListingStatus.REJECTED,
                    "Failed automated review criteria"
                )
            else:
                await self.update_application_status(application_id, ListingStatus.UNDER_REVIEW)
            
        except Exception as e:
            logger.error(f"Error in automated review: {e}")
    
    async def assess_token_risk(self, token_info: Dict[str, Any]) -> float:
        """Assess token risk using ML model"""
        try:
            # Extract features for risk assessment
            features = [
                len(token_info.get("description", "")),
                len(token_info.get("team_info", {})),
                len(token_info.get("audit_reports", [])),
                1 if token_info.get("kyc_verified") else 0,
                1 if token_info.get("website") else 0,
                1 if token_info.get("whitepaper_url") else 0,
                len(token_info.get("social_links", {})),
            ]
            
            if self.ml_model:
                # Normalize features
                features_array = np.array(features).reshape(1, -1)
                risk_score = self.ml_model.decision_function(features_array)[0]
                # Convert to 0-1 scale (higher is better)
                return max(0, min(1, (risk_score + 1) / 2))
            else:
                # Fallback scoring
                return sum(features) / len(features) if features else 0.5
                
        except Exception as e:
            logger.error(f"Error assessing token risk: {e}")
            return 0.5
    
    async def check_compliance(self, token_info: Dict[str, Any]) -> float:
        """Check compliance requirements"""
        score = 0.0
        total_checks = 6
        
        # KYC verification
        if token_info.get("kyc_verified"):
            score += 1
        
        # Website presence
        if token_info.get("website"):
            score += 1
        
        # Whitepaper
        if token_info.get("whitepaper_url"):
            score += 1
        
        # Team information
        if token_info.get("team_info") and len(token_info["team_info"]) > 0:
            score += 1
        
        # Audit reports
        if token_info.get("audit_reports") and len(token_info["audit_reports"]) > 0:
            score += 1
        
        # Social presence
        if token_info.get("social_links") and len(token_info["social_links"]) >= 2:
            score += 1
        
        return score / total_checks
    
    async def validate_technical_requirements(self, token_info: Dict[str, Any]) -> float:
        """Validate technical requirements"""
        score = 0.0
        total_checks = 4
        
        # Contract address validation
        if token_info.get("contract_address"):
            try:
                is_valid = await self.blockchain_manager.validate_contract(
                    token_info["contract_address"],
                    token_info["blockchain"]
                )
                if is_valid:
                    score += 1
            except:
                pass
        
        # Decimals check (standard is 18)
        if token_info.get("decimals") in [6, 8, 18]:
            score += 1
        
        # Total supply check
        if token_info.get("total_supply") and int(token_info["total_supply"]) > 0:
            score += 1
        
        # Token type validation
        if token_info.get("token_type") in [t.value for t in TokenType]:
            score += 1
        
        return score / total_checks
    
    async def update_application_status(self, application_id: str, status: ListingStatus, reason: str = None):
        """Update application status"""
        db = await get_db_connection()
        
        try:
            await db.execute("""
                UPDATE listing_applications 
                SET status = $1, reviewed_at = $2, rejection_reason = $3
                WHERE id = $4
            """, status.value, datetime.utcnow(), reason, application_id)
            
            await db.close()
            
            # Send notification
            await self.send_status_notification(application_id, status, reason)
            
        except Exception as e:
            await db.close()
            logger.error(f"Error updating application status: {e}")
    
    async def send_status_notification(self, application_id: str, status: ListingStatus, reason: str = None):
        """Send status update notification"""
        # Implementation for sending notifications
        pass
    
    async def list_token(self, application_id: str) -> bool:
        """List approved token on exchange"""
        try:
            db = await get_db_connection()
            
            # Get application details
            row = await db.fetchrow("""
                SELECT * FROM listing_applications WHERE id = $1 AND status = $2
            """, application_id, ListingStatus.APPROVED.value)
            
            if not row:
                return False
            
            token_info = json.loads(row["token_info"])
            requested_pairs = json.loads(row["requested_pairs"])
            listing_type = row["listing_type"]
            
            # Create trading pairs
            for pair in requested_pairs:
                await self.create_trading_pair(token_info, pair, listing_type)
            
            # Update status to listed
            await db.execute("""
                UPDATE listing_applications 
                SET status = $1, listing_date = $2
                WHERE id = $3
            """, ListingStatus.LISTED.value, datetime.utcnow(), application_id)
            
            await db.close()
            
            # Initialize liquidity if needed
            if listing_type in [ListingType.DEX_ONLY.value, ListingType.HYBRID.value]:
                await self.initialize_dex_liquidity(token_info, requested_pairs)
            
            return True
            
        except Exception as e:
            logger.error(f"Error listing token: {e}")
            return False
    
    async def create_trading_pair(self, token_info: Dict[str, Any], pair: str, listing_type: str):
        """Create a new trading pair"""
        db = await get_db_connection()
        
        try:
            base_asset, quote_asset = pair.split("/")
            
            await db.execute("""
                INSERT INTO trading_pairs (symbol, base_asset, quote_asset, status, is_active,
                                         min_quantity, max_quantity, step_size, min_price, max_price,
                                         tick_size, min_notional, maker_fee, taker_fee,
                                         is_spot_enabled, is_margin_enabled, is_futures_enabled,
                                         created_at, updated_at)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)
            """, pair.replace("/", ""), base_asset, quote_asset, "TRADING", True,
                Decimal("0.00000001"), Decimal("1000000000"), Decimal("0.00000001"),
                Decimal("0.00000001"), Decimal("1000000"), Decimal("0.00000001"),
                Decimal("10.00"), Decimal("0.001"), Decimal("0.001"),
                True, False, False, datetime.utcnow(), datetime.utcnow())
            
            await db.close()
            
        except Exception as e:
            await db.close()
            logger.error(f"Error creating trading pair: {e}")
    
    async def initialize_dex_liquidity(self, token_info: Dict[str, Any], pairs: List[str]):
        """Initialize DEX liquidity for new token"""
        try:
            # Create initial liquidity pools on supported DEXs
            for pair in pairs:
                base_asset, quote_asset = pair.split("/")
                
                # Create pools on major DEXs
                dex_protocols = ["uniswap_v3", "pancakeswap_v3", "sushiswap"]
                
                for protocol in dex_protocols:
                    pool_request = LiquidityProvisionRequest(
                        token_a=base_asset,
                        token_b=quote_asset,
                        amount_a=Decimal("10000"),
                        amount_b=Decimal("10000"),
                        dex_protocol=protocol,
                        blockchain=token_info["blockchain"]
                    )
                    
                    await self.liquidity_manager.create_liquidity_pool(pool_request, "system")
                    
        except Exception as e:
            logger.error(f"Error initializing DEX liquidity: {e}")

# Initialize managers
blockchain_manager = BlockchainManager()
liquidity_manager = LiquidityManager()
listing_manager = TokenListingManager()

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Implement JWT token validation
    return {"id": "user123", "role": "user"}  # Placeholder

# API Endpoints

@app.post("/api/v1/tokens/submit-listing")
async def submit_listing_application(
    application: ListingApplicationRequest,
    current_user: dict = Depends(get_current_user)
):
    """Submit a new token listing application"""
    try:
        application_id = await listing_manager.submit_listing_application(
            application, current_user["id"]
        )
        return {"application_id": application_id, "status": "submitted"}
    except Exception as e:
        logger.error(f"Error submitting listing application: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/tokens/applications/{application_id}")
async def get_listing_application(
    application_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get listing application details"""
    try:
        db = await get_db_connection()
        row = await db.fetchrow("""
            SELECT * FROM listing_applications WHERE id = $1
        """, application_id)
        await db.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="Application not found")
        
        return dict(row)
    except Exception as e:
        logger.error(f"Error getting listing application: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/tokens/applications")
async def list_applications(
    status: Optional[ListingStatus] = None,
    current_user: dict = Depends(get_current_user)
):
    """List token listing applications"""
    try:
        db = await get_db_connection()
        
        if status:
            rows = await db.fetch("""
                SELECT * FROM listing_applications WHERE status = $1 ORDER BY submitted_at DESC
            """, status.value)
        else:
            rows = await db.fetch("""
                SELECT * FROM listing_applications ORDER BY submitted_at DESC
            """)
        
        await db.close()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error listing applications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/tokens/validate-contract")
async def validate_token_contract(
    contract_address: str,
    blockchain: str,
    current_user: dict = Depends(get_current_user)
):
    """Validate token contract and get information"""
    try:
        token_info = await blockchain_manager.get_token_info(contract_address, blockchain)
        is_valid = await blockchain_manager.validate_contract(contract_address, blockchain)
        
        return {
            "is_valid": is_valid,
            "token_info": token_info if is_valid else None
        }
    except Exception as e:
        logger.error(f"Error validating contract: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/v1/blockchains/add-custom-evm")
async def add_custom_evm_chain(
    chain_config: CustomBlockchainRequest,
    current_user: dict = Depends(get_current_user)
):
    """Add a custom EVM-compatible blockchain"""
    try:
        success = await blockchain_manager.add_custom_evm_chain(chain_config)
        if success:
            return {"message": "Custom EVM chain added successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to add custom EVM chain")
    except Exception as e:
        logger.error(f"Error adding custom EVM chain: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/blockchains/supported")
async def get_supported_blockchains():
    """Get list of supported blockchains"""
    try:
        supported_chains = list(blockchain_manager.web3_instances.keys())
        custom_chains = blockchain_manager.custom_chains
        
        return {
            "supported_chains": supported_chains,
            "custom_chains": custom_chains
        }
    except Exception as e:
        logger.error(f"Error getting supported blockchains: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/liquidity/provide")
async def provide_liquidity(
    liquidity_request: LiquidityProvisionRequest,
    current_user: dict = Depends(get_current_user)
):
    """Provide liquidity to a pool"""
    try:
        pool_id = await liquidity_manager.create_liquidity_pool(
            liquidity_request, current_user["id"]
        )
        return {"pool_id": pool_id, "status": "liquidity_provided"}
    except Exception as e:
        logger.error(f"Error providing liquidity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/liquidity/shared/{symbol}")
async def get_shared_liquidity(symbol: str):
    """Get shared liquidity data from multiple exchanges"""
    try:
        liquidity_data = await liquidity_manager.get_shared_liquidity(symbol)
        return liquidity_data
    except Exception as e:
        logger.error(f"Error getting shared liquidity: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/liquidity/pools")
async def list_liquidity_pools(
    blockchain: Optional[str] = None,
    dex_protocol: Optional[str] = None
):
    """List available liquidity pools"""
    try:
        db = await get_db_connection()
        
        query = "SELECT * FROM liquidity_pools WHERE is_active = true"
        params = []
        
        if blockchain:
            query += " AND blockchain = $1"
            params.append(blockchain)
        
        if dex_protocol:
            if params:
                query += " AND dex_protocol = $2"
            else:
                query += " AND dex_protocol = $1"
            params.append(dex_protocol)
        
        query += " ORDER BY liquidity_usd DESC"
        
        rows = await db.fetch(query, *params)
        await db.close()
        
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error listing liquidity pools: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/admin/approve-listing/{application_id}")
async def approve_listing(
    application_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Approve a token listing application (admin only)"""
    try:
        # Check admin permissions
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        success = await listing_manager.list_token(application_id)
        if success:
            return {"message": "Token listing approved and activated"}
        else:
            raise HTTPException(status_code=400, detail="Failed to approve listing")
    except Exception as e:
        logger.error(f"Error approving listing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/admin/reject-listing/{application_id}")
async def reject_listing(
    application_id: str,
    reason: str,
    current_user: dict = Depends(get_current_user)
):
    """Reject a token listing application (admin only)"""
    try:
        # Check admin permissions
        if current_user.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        await listing_manager.update_application_status(
            application_id, ListingStatus.REJECTED, reason
        )
        return {"message": "Token listing rejected"}
    except Exception as e:
        logger.error(f"Error rejecting listing: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/tokens/listed")
async def get_listed_tokens():
    """Get all listed tokens"""
    try:
        db = await get_db_connection()
        rows = await db.fetch("""
            SELECT la.*, tp.symbol as trading_symbol
            FROM listing_applications la
            LEFT JOIN trading_pairs tp ON tp.base_asset = JSON_EXTRACT(la.token_info, '$.symbol')
            WHERE la.status = $1
            ORDER BY la.listing_date DESC
        """, ListingStatus.LISTED.value)
        await db.close()
        
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error getting listed tokens: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "blockchain_connections": len(blockchain_manager.web3_instances),
            "exchange_connections": len(liquidity_manager.exchanges),
            "custom_chains": len(blockchain_manager.custom_chains)
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8087)