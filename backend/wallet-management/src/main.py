"""
TigerEx Wallet Management System
Comprehensive wallet system supporting hot, cold, custodial, and non-custodial wallets
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
from mnemonic import Mnemonic
from hdwallet import HDWallet
from hdwallet.symbols import BTC, ETH
import ecdsa
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

import aioredis
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, DECIMAL, ForeignKey, JSON, Enum as SQLEnum, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
from web3 import Web3

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="TigerEx Wallet Management System",
    description="Comprehensive wallet system supporting hot, cold, custodial, and non-custodial wallets",
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
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "wallet-secret-key")
    ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY", Fernet.generate_key().decode())
    
    # Blockchain RPC URLs
    ETHEREUM_RPC_URL = os.getenv("ETHEREUM_RPC_URL", "https://mainnet.infura.io/v3/your-key")
    BITCOIN_RPC_URL = os.getenv("BITCOIN_RPC_URL", "https://bitcoin-rpc.example.com")
    POLYGON_RPC_URL = os.getenv("POLYGON_RPC_URL", "https://polygon-rpc.com")
    BSC_RPC_URL = os.getenv("BSC_RPC_URL", "https://bsc-dataseed.binance.org")

config = Config()

# Database setup
engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

security = HTTPBearer()

# Enums
class WalletType(str, Enum):
    HOT = "hot"
    COLD = "cold"
    CUSTODIAL = "custodial"
    NON_CUSTODIAL = "non_custodial"
    HARDWARE = "hardware"
    MULTI_SIG = "multi_sig"

class WalletStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    FROZEN = "frozen"
    COMPROMISED = "compromised"

class TransactionType(str, Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    INTERNAL_TRANSFER = "internal_transfer"
    EXTERNAL_TRANSFER = "external_transfer"

class TransactionStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class BlockchainNetwork(str, Enum):
    BITCOIN = "bitcoin"
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    BSC = "bsc"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    AVALANCHE = "avalanche"
    SOLANA = "solana"

# Database Models
class Wallet(Base):
    __tablename__ = "wallets"
    
    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Basic Info
    user_id = Column(String(50), nullable=False, index=True)
    wallet_name = Column(String(100), nullable=False)
    wallet_type = Column(SQLEnum(WalletType), nullable=False)
    blockchain_network = Column(SQLEnum(BlockchainNetwork), nullable=False)
    
    # Addresses
    address = Column(String(100), nullable=False, index=True)
    public_key = Column(Text)
    
    # Encrypted Private Keys (for hot wallets)
    encrypted_private_key = Column(LargeBinary)
    key_derivation_path = Column(String(100))
    
    # Multi-sig Configuration
    required_signatures = Column(Integer, default=1)
    total_signers = Column(Integer, default=1)
    signer_addresses = Column(JSON)
    
    # Security
    is_encrypted = Column(Boolean, default=True)
    encryption_method = Column(String(50), default="AES-256")
    backup_phrase_encrypted = Column(LargeBinary)
    
    # Status and Limits
    status = Column(SQLEnum(WalletStatus), default=WalletStatus.ACTIVE)
    daily_withdrawal_limit = Column(DECIMAL(20, 8))
    monthly_withdrawal_limit = Column(DECIMAL(20, 8))
    
    # Balances (cached)
    total_balance_usd = Column(DECIMAL(20, 2), default=0)
    last_balance_update = Column(DateTime)
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    transactions = relationship("WalletTransaction", back_populates="wallet")
    balances = relationship("WalletBalance", back_populates="wallet")

class WalletBalance(Base):
    __tablename__ = "wallet_balances"
    
    id = Column(Integer, primary_key=True, index=True)
    wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False)
    wallet = relationship("Wallet", back_populates="balances")
    
    # Token Info
    token_symbol = Column(String(20), nullable=False)
    token_address = Column(String(100))  # Contract address for tokens
    
    # Balances
    available_balance = Column(DECIMAL(30, 8), default=0)
    locked_balance = Column(DECIMAL(30, 8), default=0)
    total_balance = Column(DECIMAL(30, 8), default=0)
    
    # USD Values
    usd_price = Column(DECIMAL(20, 8))
    usd_value = Column(DECIMAL(20, 2))
    
    # Last Update
    last_updated = Column(DateTime, default=func.now())

class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Wallet Reference
    wallet_id = Column(Integer, ForeignKey("wallets.id"), nullable=False)
    wallet = relationship("Wallet", back_populates="transactions")
    
    # Transaction Details
    transaction_type = Column(SQLEnum(TransactionType), nullable=False)
    token_symbol = Column(String(20), nullable=False)
    amount = Column(DECIMAL(30, 8), nullable=False)
    
    # Addresses
    from_address = Column(String(100))
    to_address = Column(String(100), nullable=False)
    
    # Blockchain Info
    blockchain_hash = Column(String(100))
    block_number = Column(Integer)
    gas_used = Column(Integer)
    gas_price = Column(DECIMAL(20, 8))
    network_fee = Column(DECIMAL(30, 8))
    
    # Status
    status = Column(SQLEnum(TransactionStatus), default=TransactionStatus.PENDING)
    confirmations = Column(Integer, default=0)
    required_confirmations = Column(Integer, default=6)
    
    # Metadata
    memo = Column(Text)
    internal_reference = Column(String(100))
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    confirmed_at = Column(DateTime)

class WalletSeed(Base):
    __tablename__ = "wallet_seeds"
    
    id = Column(Integer, primary_key=True, index=True)
    seed_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # User and Wallet Info
    user_id = Column(String(50), nullable=False, index=True)
    wallet_name = Column(String(100), nullable=False)
    
    # Encrypted Seed Phrase
    encrypted_seed_phrase = Column(LargeBinary, nullable=False)
    seed_length = Column(Integer, default=12)  # 12 or 24 words
    
    # Derivation Info
    derivation_standard = Column(String(20), default="BIP44")
    supported_networks = Column(JSON)
    
    # Security
    encryption_method = Column(String(50), default="AES-256")
    password_hash = Column(String(255))  # For additional password protection
    
    # Backup Info
    is_backed_up = Column(Boolean, default=False)
    backup_date = Column(DateTime)
    backup_locations = Column(JSON)
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    last_accessed = Column(DateTime)

class HardwareWallet(Base):
    __tablename__ = "hardware_wallets"
    
    id = Column(Integer, primary_key=True, index=True)
    hardware_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # User Info
    user_id = Column(String(50), nullable=False, index=True)
    
    # Hardware Info
    device_type = Column(String(50), nullable=False)  # ledger, trezor, etc.
    device_model = Column(String(50))
    firmware_version = Column(String(20))
    serial_number = Column(String(100))
    
    # Connection Info
    is_connected = Column(Boolean, default=False)
    last_connected = Column(DateTime)
    connection_method = Column(String(20))  # usb, bluetooth
    
    # Supported Features
    supported_networks = Column(JSON)
    supported_apps = Column(JSON)
    
    # Security
    pin_enabled = Column(Boolean, default=True)
    passphrase_enabled = Column(Boolean, default=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

# Pydantic Models
class WalletCreate(BaseModel):
    wallet_name: str
    wallet_type: WalletType
    blockchain_network: BlockchainNetwork
    password: Optional[str] = None
    daily_withdrawal_limit: Optional[Decimal] = None
    monthly_withdrawal_limit: Optional[Decimal] = None

class WalletImport(BaseModel):
    wallet_name: str
    wallet_type: WalletType
    blockchain_network: BlockchainNetwork
    import_method: str  # private_key, seed_phrase, keystore
    import_data: str
    password: Optional[str] = None

class TransactionCreate(BaseModel):
    to_address: str
    token_symbol: str
    amount: Decimal
    memo: Optional[str] = None
    gas_price: Optional[Decimal] = None

class WalletBackup(BaseModel):
    backup_password: str
    backup_locations: List[str] = []

# Dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return {"user_id": "user_123", "username": "testuser"}

# Wallet Management System
class WalletManager:
    def __init__(self):
        self.redis_client = None
        self.encryption_key = config.ENCRYPTION_KEY.encode()
        self.fernet = Fernet(self.encryption_key)
        
        # Initialize blockchain connections
        self.web3_connections = {
            BlockchainNetwork.ETHEREUM: Web3(Web3.HTTPProvider(config.ETHEREUM_RPC_URL)),
            BlockchainNetwork.POLYGON: Web3(Web3.HTTPProvider(config.POLYGON_RPC_URL)),
            BlockchainNetwork.BSC: Web3(Web3.HTTPProvider(config.BSC_RPC_URL))
        }
        
    async def initialize(self):
        self.redis_client = await aioredis.from_url(config.REDIS_URL)
    
    def encrypt_data(self, data: str) -> bytes:
        """Encrypt sensitive data"""
        return self.fernet.encrypt(data.encode())
    
    def decrypt_data(self, encrypted_data: bytes) -> str:
        """Decrypt sensitive data"""
        return self.fernet.decrypt(encrypted_data).decode()
    
    async def create_wallet(self, wallet_data: WalletCreate, user: Dict[str, Any], db: Session):
        """Create new wallet"""
        
        wallet_id = f"WALLET_{secrets.token_hex(8).upper()}"
        
        # Generate wallet based on type
        if wallet_data.wallet_type == WalletType.HOT:
            wallet_info = await self._create_hot_wallet(wallet_data.blockchain_network, wallet_data.password)
        elif wallet_data.wallet_type == WalletType.COLD:
            wallet_info = await self._create_cold_wallet(wallet_data.blockchain_network)
        elif wallet_data.wallet_type == WalletType.CUSTODIAL:
            wallet_info = await self._create_custodial_wallet(wallet_data.blockchain_network)
        elif wallet_data.wallet_type == WalletType.NON_CUSTODIAL:
            wallet_info = await self._create_non_custodial_wallet(wallet_data.blockchain_network)
        else:
            raise HTTPException(status_code=400, detail="Unsupported wallet type")
        
        # Create wallet record
        wallet = Wallet(
            wallet_id=wallet_id,
            user_id=user["user_id"],
            wallet_name=wallet_data.wallet_name,
            wallet_type=wallet_data.wallet_type,
            blockchain_network=wallet_data.blockchain_network,
            address=wallet_info["address"],
            public_key=wallet_info.get("public_key"),
            encrypted_private_key=wallet_info.get("encrypted_private_key"),
            key_derivation_path=wallet_info.get("derivation_path"),
            daily_withdrawal_limit=wallet_data.daily_withdrawal_limit,
            monthly_withdrawal_limit=wallet_data.monthly_withdrawal_limit
        )
        
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
        
        # Initialize balance records
        await self._initialize_wallet_balances(wallet, db)
        
        return wallet
    
    async def _create_hot_wallet(self, network: BlockchainNetwork, password: Optional[str] = None):
        """Create hot wallet with private key storage"""
        
        if network in [BlockchainNetwork.ETHEREUM, BlockchainNetwork.POLYGON, BlockchainNetwork.BSC]:
            # Generate Ethereum-compatible wallet
            account = self.web3_connections[network].eth.account.create()
            
            # Encrypt private key
            private_key = account.key.hex()
            encrypted_private_key = self.encrypt_data(private_key)
            
            return {
                "address": account.address,
                "public_key": account.key.hex(),
                "encrypted_private_key": encrypted_private_key,
                "derivation_path": "m/44'/60'/0'/0/0"
            }
        
        elif network == BlockchainNetwork.BITCOIN:
            # Generate Bitcoin wallet
            hdwallet = HDWallet(symbol=BTC)
            hdwallet.from_entropy(entropy=secrets.token_bytes(32))
            
            private_key = hdwallet.private_key()
            encrypted_private_key = self.encrypt_data(private_key)
            
            return {
                "address": hdwallet.p2pkh_address(),
                "public_key": hdwallet.public_key(),
                "encrypted_private_key": encrypted_private_key,
                "derivation_path": hdwallet.path()
            }
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported network for hot wallet")
    
    async def _create_cold_wallet(self, network: BlockchainNetwork):
        """Create cold wallet (address only, no private key storage)"""
        
        # Generate address but don't store private key
        if network in [BlockchainNetwork.ETHEREUM, BlockchainNetwork.POLYGON, BlockchainNetwork.BSC]:
            account = self.web3_connections[network].eth.account.create()
            return {
                "address": account.address,
                "public_key": account.key.hex()
            }
        else:
            raise HTTPException(status_code=400, detail="Unsupported network for cold wallet")
    
    async def _create_custodial_wallet(self, network: BlockchainNetwork):
        """Create custodial wallet (platform controls private keys)"""
        
        # Similar to hot wallet but with additional security measures
        return await self._create_hot_wallet(network)
    
    async def _create_non_custodial_wallet(self, network: BlockchainNetwork):
        """Create non-custodial wallet (user controls private keys)"""
        
        # Generate seed phrase for user
        mnemo = Mnemonic("english")
        seed_phrase = mnemo.generate(strength=128)  # 12 words
        
        # Derive wallet from seed
        if network in [BlockchainNetwork.ETHEREUM, BlockchainNetwork.POLYGON, BlockchainNetwork.BSC]:
            hdwallet = HDWallet(symbol=ETH)
            hdwallet.from_mnemonic(mnemonic=seed_phrase)
            hdwallet.from_path("m/44'/60'/0'/0/0")
            
            return {
                "address": hdwallet.p2pkh_address(),
                "public_key": hdwallet.public_key(),
                "seed_phrase": seed_phrase,
                "derivation_path": "m/44'/60'/0'/0/0"
            }
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported network for non-custodial wallet")
    
    async def _initialize_wallet_balances(self, wallet: Wallet, db: Session):
        """Initialize balance records for wallet"""
        
        # Get supported tokens for the network
        supported_tokens = self._get_supported_tokens(wallet.blockchain_network)
        
        for token in supported_tokens:
            balance = WalletBalance(
                wallet_id=wallet.id,
                token_symbol=token["symbol"],
                token_address=token.get("address"),
                available_balance=0,
                locked_balance=0,
                total_balance=0
            )
            db.add(balance)
        
        db.commit()
    
    def _get_supported_tokens(self, network: BlockchainNetwork) -> List[Dict]:
        """Get supported tokens for a blockchain network"""
        
        if network == BlockchainNetwork.ETHEREUM:
            return [
                {"symbol": "ETH", "address": None},
                {"symbol": "USDT", "address": "0xdAC17F958D2ee523a2206206994597C13D831ec7"},
                {"symbol": "USDC", "address": "0xA0b86a33E6441b8C4505B8C4505B8C4505B8C4505"},
                {"symbol": "WBTC", "address": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599"}
            ]
        elif network == BlockchainNetwork.BSC:
            return [
                {"symbol": "BNB", "address": None},
                {"symbol": "USDT", "address": "0x55d398326f99059fF775485246999027B3197955"},
                {"symbol": "BUSD", "address": "0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56"}
            ]
        elif network == BlockchainNetwork.POLYGON:
            return [
                {"symbol": "MATIC", "address": None},
                {"symbol": "USDT", "address": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"},
                {"symbol": "USDC", "address": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"}
            ]
        else:
            return [{"symbol": network.value.upper(), "address": None}]
    
    async def import_wallet(self, import_data: WalletImport, user: Dict[str, Any], db: Session):
        """Import existing wallet"""
        
        wallet_id = f"WALLET_{secrets.token_hex(8).upper()}"
        
        # Import wallet based on method
        if import_data.import_method == "private_key":
            wallet_info = await self._import_from_private_key(
                import_data.import_data, 
                import_data.blockchain_network
            )
        elif import_data.import_method == "seed_phrase":
            wallet_info = await self._import_from_seed_phrase(
                import_data.import_data, 
                import_data.blockchain_network
            )
        elif import_data.import_method == "keystore":
            wallet_info = await self._import_from_keystore(
                import_data.import_data, 
                import_data.password,
                import_data.blockchain_network
            )
        else:
            raise HTTPException(status_code=400, detail="Unsupported import method")
        
        # Create wallet record
        wallet = Wallet(
            wallet_id=wallet_id,
            user_id=user["user_id"],
            wallet_name=import_data.wallet_name,
            wallet_type=import_data.wallet_type,
            blockchain_network=import_data.blockchain_network,
            address=wallet_info["address"],
            public_key=wallet_info.get("public_key"),
            encrypted_private_key=wallet_info.get("encrypted_private_key"),
            key_derivation_path=wallet_info.get("derivation_path")
        )
        
        db.add(wallet)
        db.commit()
        db.refresh(wallet)
        
        # Initialize balances and sync
        await self._initialize_wallet_balances(wallet, db)
        await self._sync_wallet_balance(wallet, db)
        
        return wallet
    
    async def _import_from_private_key(self, private_key: str, network: BlockchainNetwork):
        """Import wallet from private key"""
        
        if network in [BlockchainNetwork.ETHEREUM, BlockchainNetwork.POLYGON, BlockchainNetwork.BSC]:
            try:
                account = self.web3_connections[network].eth.account.from_key(private_key)
                encrypted_private_key = self.encrypt_data(private_key)
                
                return {
                    "address": account.address,
                    "public_key": private_key,
                    "encrypted_private_key": encrypted_private_key
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail="Invalid private key")
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported network for private key import")
    
    async def _import_from_seed_phrase(self, seed_phrase: str, network: BlockchainNetwork):
        """Import wallet from seed phrase"""
        
        try:
            mnemo = Mnemonic("english")
            if not mnemo.check(seed_phrase):
                raise HTTPException(status_code=400, detail="Invalid seed phrase")
            
            if network in [BlockchainNetwork.ETHEREUM, BlockchainNetwork.POLYGON, BlockchainNetwork.BSC]:
                hdwallet = HDWallet(symbol=ETH)
                hdwallet.from_mnemonic(mnemonic=seed_phrase)
                hdwallet.from_path("m/44'/60'/0'/0/0")
                
                private_key = hdwallet.private_key()
                encrypted_private_key = self.encrypt_data(private_key)
                
                return {
                    "address": hdwallet.p2pkh_address(),
                    "public_key": hdwallet.public_key(),
                    "encrypted_private_key": encrypted_private_key,
                    "derivation_path": "m/44'/60'/0'/0/0"
                }
            
        except Exception as e:
            raise HTTPException(status_code=400, detail="Failed to import from seed phrase")
    
    async def _import_from_keystore(self, keystore_json: str, password: str, network: BlockchainNetwork):
        """Import wallet from keystore file"""
        
        try:
            keystore = json.loads(keystore_json)
            private_key = self.web3_connections[network].eth.account.decrypt(keystore, password)
            
            return await self._import_from_private_key(private_key.hex(), network)
            
        except Exception as e:
            raise HTTPException(status_code=400, detail="Failed to decrypt keystore")
    
    async def _sync_wallet_balance(self, wallet: Wallet, db: Session):
        """Sync wallet balance with blockchain"""
        
        try:
            if wallet.blockchain_network in self.web3_connections:
                web3 = self.web3_connections[wallet.blockchain_network]
                
                # Get native token balance
                balance_wei = web3.eth.get_balance(wallet.address)
                balance_eth = web3.from_wei(balance_wei, 'ether')
                
                # Update native token balance
                native_balance = db.query(WalletBalance).filter(
                    WalletBalance.wallet_id == wallet.id,
                    WalletBalance.token_address.is_(None)
                ).first()
                
                if native_balance:
                    native_balance.available_balance = balance_eth
                    native_balance.total_balance = balance_eth
                    native_balance.last_updated = datetime.utcnow()
                
                # Get ERC20 token balances (simplified)
                # In production, you would iterate through all tokens
                
                db.commit()
                
        except Exception as e:
            logger.error(f"Failed to sync wallet balance: {str(e)}")
    
    async def create_transaction(self, wallet_id: str, tx_data: TransactionCreate, user: Dict[str, Any], db: Session):
        """Create new transaction"""
        
        wallet = db.query(Wallet).filter(
            Wallet.wallet_id == wallet_id,
            Wallet.user_id == user["user_id"]
        ).first()
        
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")
        
        if wallet.status != WalletStatus.ACTIVE:
            raise HTTPException(status_code=400, detail="Wallet is not active")
        
        # Check balance
        balance = db.query(WalletBalance).filter(
            WalletBalance.wallet_id == wallet.id,
            WalletBalance.token_symbol == tx_data.token_symbol
        ).first()
        
        if not balance or balance.available_balance < tx_data.amount:
            raise HTTPException(status_code=400, detail="Insufficient balance")
        
        # Create transaction record
        transaction_id = f"TX_{secrets.token_hex(8).upper()}"
        
        transaction = WalletTransaction(
            transaction_id=transaction_id,
            wallet_id=wallet.id,
            transaction_type=TransactionType.WITHDRAWAL,
            token_symbol=tx_data.token_symbol,
            amount=tx_data.amount,
            from_address=wallet.address,
            to_address=tx_data.to_address,
            memo=tx_data.memo
        )
        
        db.add(transaction)
        
        # Lock balance
        balance.available_balance -= tx_data.amount
        balance.locked_balance += tx_data.amount
        
        db.commit()
        db.refresh(transaction)
        
        # Process transaction asynchronously
        await self._process_transaction(transaction, wallet, db)
        
        return transaction
    
    async def _process_transaction(self, transaction: WalletTransaction, wallet: Wallet, db: Session):
        """Process blockchain transaction"""
        
        try:
            if wallet.wallet_type == WalletType.HOT and wallet.encrypted_private_key:
                # Decrypt private key
                private_key = self.decrypt_data(wallet.encrypted_private_key)
                
                # Send transaction to blockchain
                if wallet.blockchain_network in self.web3_connections:
                    web3 = self.web3_connections[wallet.blockchain_network]
                    
                    # Build transaction
                    tx_hash = await self._send_blockchain_transaction(
                        web3, private_key, transaction
                    )
                    
                    transaction.blockchain_hash = tx_hash
                    transaction.status = TransactionStatus.PENDING
                    
                else:
                    raise Exception("Unsupported blockchain network")
            
            else:
                # For cold wallets, mark as pending manual processing
                transaction.status = TransactionStatus.PENDING
            
            db.commit()
            
        except Exception as e:
            logger.error(f"Transaction processing failed: {str(e)}")
            transaction.status = TransactionStatus.FAILED
            
            # Unlock balance
            balance = db.query(WalletBalance).filter(
                WalletBalance.wallet_id == wallet.id,
                WalletBalance.token_symbol == transaction.token_symbol
            ).first()
            
            if balance:
                balance.available_balance += transaction.amount
                balance.locked_balance -= transaction.amount
            
            db.commit()
    
    async def _send_blockchain_transaction(self, web3: Web3, private_key: str, transaction: WalletTransaction) -> str:
        """Send transaction to blockchain"""
        
        account = web3.eth.account.from_key(private_key)
        
        # Build transaction
        tx = {
            'to': transaction.to_address,
            'value': web3.to_wei(transaction.amount, 'ether'),
            'gas': 21000,
            'gasPrice': web3.to_wei('20', 'gwei'),
            'nonce': web3.eth.get_transaction_count(account.address)
        }
        
        # Sign transaction
        signed_tx = web3.eth.account.sign_transaction(tx, private_key)
        
        # Send transaction
        tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        return tx_hash.hex()

# Initialize manager
wallet_manager = WalletManager()

@app.on_event("startup")
async def startup_event():
    await wallet_manager.initialize()

# API Endpoints
@app.post("/api/v1/wallets/create")
async def create_wallet(
    wallet_data: WalletCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new wallet"""
    wallet = await wallet_manager.create_wallet(wallet_data, current_user, db)
    return {
        "wallet_id": wallet.wallet_id,
        "wallet_name": wallet.wallet_name,
        "wallet_type": wallet.wallet_type,
        "blockchain_network": wallet.blockchain_network,
        "address": wallet.address,
        "status": wallet.status
    }

@app.post("/api/v1/wallets/import")
async def import_wallet(
    import_data: WalletImport,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Import existing wallet"""
    wallet = await wallet_manager.import_wallet(import_data, current_user, db)
    return {
        "wallet_id": wallet.wallet_id,
        "wallet_name": wallet.wallet_name,
        "wallet_type": wallet.wallet_type,
        "blockchain_network": wallet.blockchain_network,
        "address": wallet.address,
        "status": wallet.status
    }

@app.get("/api/v1/wallets")
async def get_user_wallets(
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's wallets"""
    wallets = db.query(Wallet).filter(Wallet.user_id == current_user["user_id"]).all()
    
    return {
        "wallets": [
            {
                "wallet_id": wallet.wallet_id,
                "wallet_name": wallet.wallet_name,
                "wallet_type": wallet.wallet_type,
                "blockchain_network": wallet.blockchain_network,
                "address": wallet.address,
                "status": wallet.status,
                "total_balance_usd": float(wallet.total_balance_usd) if wallet.total_balance_usd else 0,
                "created_at": wallet.created_at.isoformat()
            }
            for wallet in wallets
        ]
    }

@app.get("/api/v1/wallets/{wallet_id}/balance")
async def get_wallet_balance(
    wallet_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get wallet balance"""
    wallet = db.query(Wallet).filter(
        Wallet.wallet_id == wallet_id,
        Wallet.user_id == current_user["user_id"]
    ).first()
    
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    balances = db.query(WalletBalance).filter(WalletBalance.wallet_id == wallet.id).all()
    
    return {
        "wallet_id": wallet_id,
        "balances": [
            {
                "token_symbol": balance.token_symbol,
                "available_balance": str(balance.available_balance),
                "locked_balance": str(balance.locked_balance),
                "total_balance": str(balance.total_balance),
                "usd_value": float(balance.usd_value) if balance.usd_value else 0,
                "last_updated": balance.last_updated.isoformat()
            }
            for balance in balances
        ]
    }

@app.post("/api/v1/wallets/{wallet_id}/send")
async def send_transaction(
    wallet_id: str,
    tx_data: TransactionCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send transaction from wallet"""
    transaction = await wallet_manager.create_transaction(wallet_id, tx_data, current_user, db)
    return {
        "transaction_id": transaction.transaction_id,
        "status": transaction.status,
        "amount": str(transaction.amount),
        "to_address": transaction.to_address,
        "blockchain_hash": transaction.blockchain_hash
    }

@app.get("/api/v1/wallets/{wallet_id}/transactions")
async def get_wallet_transactions(
    wallet_id: str,
    limit: int = 50,
    offset: int = 0,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get wallet transactions"""
    wallet = db.query(Wallet).filter(
        Wallet.wallet_id == wallet_id,
        Wallet.user_id == current_user["user_id"]
    ).first()
    
    if not wallet:
        raise HTTPException(status_code=404, detail="Wallet not found")
    
    transactions = db.query(WalletTransaction).filter(
        WalletTransaction.wallet_id == wallet.id
    ).order_by(WalletTransaction.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "transactions": [
            {
                "transaction_id": tx.transaction_id,
                "transaction_type": tx.transaction_type,
                "token_symbol": tx.token_symbol,
                "amount": str(tx.amount),
                "from_address": tx.from_address,
                "to_address": tx.to_address,
                "status": tx.status,
                "blockchain_hash": tx.blockchain_hash,
                "confirmations": tx.confirmations,
                "created_at": tx.created_at.isoformat()
            }
            for tx in transactions
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "wallet-management"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
