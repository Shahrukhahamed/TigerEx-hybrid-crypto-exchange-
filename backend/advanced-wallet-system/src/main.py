"""
TigerEx Advanced Wallet Management System
Comprehensive wallet creation and management for hot, cold, custodial, and non-custodial wallets
Supports all major blockchains and advanced security features
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import secrets
import hashlib
import hmac
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, ec
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import mnemonic
from bip_utils import Bip39SeedGenerator, Bip44, Bip44Coins, Bip44Changes
from web3 import Web3
from bitcoin import *
from solana.keypair import Keypair
from solana.rpc.api import Client as SolanaClient
import asyncpg
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
import qrcode
import io
import base58
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="TigerEx Advanced Wallet System",
    description="Comprehensive wallet management system",
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
    
    # Encryption keys
    MASTER_KEY = os.getenv("MASTER_KEY", Fernet.generate_key().decode())
    HSM_ENDPOINT = os.getenv("HSM_ENDPOINT")
    
    # Blockchain RPC URLs
    ETHEREUM_RPC = os.getenv("ETHEREUM_RPC", "https://mainnet.infura.io/v3/...")
    BITCOIN_RPC = os.getenv("BITCOIN_RPC", "https://bitcoin-rpc.com")
    BSC_RPC = os.getenv("BSC_RPC", "https://bsc-dataseed.binance.org/")
    POLYGON_RPC = os.getenv("POLYGON_RPC", "https://polygon-rpc.com/")
    SOLANA_RPC = os.getenv("SOLANA_RPC", "https://api.mainnet-beta.solana.com")
    
    # AWS KMS
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    KMS_KEY_ID = os.getenv("KMS_KEY_ID")
    
    # Security settings
    MIN_PASSWORD_LENGTH = 12
    MAX_FAILED_ATTEMPTS = 5
    LOCKOUT_DURATION = 3600  # 1 hour

config = Config()

# Enums
class WalletType(str, Enum):
    HOT = "hot"
    COLD = "cold"
    CUSTODIAL = "custodial"
    NON_CUSTODIAL = "non_custodial"
    HARDWARE = "hardware"
    MULTI_SIG = "multi_sig"
    SMART_CONTRACT = "smart_contract"

class WalletStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    FROZEN = "frozen"
    COMPROMISED = "compromised"
    RECOVERY = "recovery"

class Blockchain(str, Enum):
    BITCOIN = "bitcoin"
    ETHEREUM = "ethereum"
    BINANCE_SMART_CHAIN = "binance_smart_chain"
    POLYGON = "polygon"
    SOLANA = "solana"
    AVALANCHE = "avalanche"
    CARDANO = "cardano"
    POLKADOT = "polkadot"
    COSMOS = "cosmos"
    NEAR = "near"
    TRON = "tron"
    TON = "ton"
    PI_NETWORK = "pi_network"

class SecurityLevel(str, Enum):
    BASIC = "basic"
    STANDARD = "standard"
    HIGH = "high"
    ENTERPRISE = "enterprise"
    MILITARY = "military"

class BackupType(str, Enum):
    MNEMONIC = "mnemonic"
    KEYSTORE = "keystore"
    PRIVATE_KEY = "private_key"
    HARDWARE_BACKUP = "hardware_backup"
    PAPER_WALLET = "paper_wallet"
    SHAMIR_SECRET = "shamir_secret"

# Data Models
@dataclass
class WalletInfo:
    id: str
    user_id: int
    wallet_type: WalletType
    blockchain: Blockchain
    address: str
    public_key: str
    encrypted_private_key: Optional[str]
    mnemonic_encrypted: Optional[str]
    derivation_path: str
    security_level: SecurityLevel
    backup_types: List[BackupType]
    is_multi_sig: bool
    multi_sig_threshold: Optional[int]
    multi_sig_participants: List[str]
    balance: Dict[str, float]
    status: WalletStatus
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime]

@dataclass
class Transaction:
    id: str
    wallet_id: str
    blockchain: Blockchain
    tx_hash: str
    from_address: str
    to_address: str
    amount: float
    token_symbol: str
    gas_fee: float
    status: str
    block_number: Optional[int]
    confirmations: int
    created_at: datetime
    confirmed_at: Optional[datetime]

# Pydantic Models
class CreateWalletRequest(BaseModel):
    wallet_type: WalletType
    blockchain: Blockchain
    security_level: SecurityLevel = SecurityLevel.STANDARD
    backup_types: List[BackupType] = [BackupType.MNEMONIC]
    password: Optional[str] = None
    is_multi_sig: bool = False
    multi_sig_threshold: Optional[int] = None
    multi_sig_participants: List[str] = []

class ImportWalletRequest(BaseModel):
    wallet_type: WalletType
    blockchain: Blockchain
    import_method: str  # mnemonic, private_key, keystore
    import_data: str
    password: Optional[str] = None
    derivation_path: Optional[str] = None

class SendTransactionRequest(BaseModel):
    wallet_id: str
    to_address: str
    amount: float
    token_symbol: str = "native"
    gas_price: Optional[float] = None
    password: Optional[str] = None
    two_factor_code: Optional[str] = None

class WalletBackupRequest(BaseModel):
    wallet_id: str
    backup_type: BackupType
    password: str

# Advanced Wallet Manager
class AdvancedWalletManager:
    def __init__(self):
        self.db_pool = None
        self.redis_client = None
        self.blockchain_clients = {}
        self.encryption_key = Fernet(config.MASTER_KEY.encode())
        self.aws_kms = None
        
        # Initialize components
        asyncio.create_task(self.initialize_components())
    
    async def initialize_components(self):
        """Initialize database, Redis, and blockchain clients"""
        try:
            # Database pool
            self.db_pool = await asyncpg.create_pool(config.DATABASE_URL)
            
            # Redis client
            self.redis_client = redis.from_url(config.REDIS_URL)
            
            # Blockchain clients
            self.blockchain_clients = {
                Blockchain.ETHEREUM: Web3(Web3.HTTPProvider(config.ETHEREUM_RPC)),
                Blockchain.BINANCE_SMART_CHAIN: Web3(Web3.HTTPProvider(config.BSC_RPC)),
                Blockchain.POLYGON: Web3(Web3.HTTPProvider(config.POLYGON_RPC)),
                Blockchain.SOLANA: SolanaClient(config.SOLANA_RPC)
            }
            
            # AWS KMS client
            if config.KMS_KEY_ID:
                self.aws_kms = boto3.client('kms', region_name=config.AWS_REGION)
            
            logger.info("Wallet manager components initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing wallet manager: {e}")
    
    async def create_wallet(self, user_id: int, request: CreateWalletRequest) -> WalletInfo:
        """Create a new wallet"""
        try:
            wallet_id = f"wallet_{secrets.token_hex(16)}"
            
            # Generate wallet based on type and blockchain
            if request.blockchain == Blockchain.BITCOIN:
                wallet_data = await self.create_bitcoin_wallet(request)
            elif request.blockchain in [Blockchain.ETHEREUM, Blockchain.BINANCE_SMART_CHAIN, Blockchain.POLYGON]:
                wallet_data = await self.create_ethereum_wallet(request)
            elif request.blockchain == Blockchain.SOLANA:
                wallet_data = await self.create_solana_wallet(request)
            else:
                raise HTTPException(status_code=400, detail=f"Blockchain {request.blockchain} not supported")
            
            # Encrypt sensitive data
            encrypted_private_key = None
            encrypted_mnemonic = None
            
            if wallet_data.get('private_key'):
                encrypted_private_key = await self.encrypt_sensitive_data(
                    wallet_data['private_key'],
                    request.password,
                    request.security_level
                )
            
            if wallet_data.get('mnemonic'):
                encrypted_mnemonic = await self.encrypt_sensitive_data(
                    wallet_data['mnemonic'],
                    request.password,
                    request.security_level
                )
            
            # Create wallet info
            wallet_info = WalletInfo(
                id=wallet_id,
                user_id=user_id,
                wallet_type=request.wallet_type,
                blockchain=request.blockchain,
                address=wallet_data['address'],
                public_key=wallet_data['public_key'],
                encrypted_private_key=encrypted_private_key,
                mnemonic_encrypted=encrypted_mnemonic,
                derivation_path=wallet_data.get('derivation_path', "m/44'/0'/0'/0/0"),
                security_level=request.security_level,
                backup_types=request.backup_types,
                is_multi_sig=request.is_multi_sig,
                multi_sig_threshold=request.multi_sig_threshold,
                multi_sig_participants=request.multi_sig_participants,
                balance={},
                status=WalletStatus.ACTIVE,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                last_used_at=None
            )
            
            # Save to database
            await self.save_wallet_to_database(wallet_info)
            
            # Initialize balance tracking
            await self.initialize_balance_tracking(wallet_info)
            
            logger.info(f"Created {request.wallet_type} wallet {wallet_id} for user {user_id}")
            return wallet_info
            
        except Exception as e:
            logger.error(f"Error creating wallet: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def create_bitcoin_wallet(self, request: CreateWalletRequest) -> Dict[str, Any]:
        """Create Bitcoin wallet"""
        if request.wallet_type == WalletType.HOT:
            # Generate new private key
            private_key = random_key()
            public_key = privtopub(private_key)
            address = pubtoaddr(public_key)
            
            # Generate mnemonic if requested
            mnemonic_phrase = None
            if BackupType.MNEMONIC in request.backup_types:
                mnemo = mnemonic.Mnemonic("english")
                mnemonic_phrase = mnemo.generate(strength=256)
            
            return {
                'private_key': private_key,
                'public_key': public_key,
                'address': address,
                'mnemonic': mnemonic_phrase,
                'derivation_path': "m/44'/0'/0'/0/0"
            }
        
        elif request.wallet_type == WalletType.COLD:
            # For cold wallets, generate offline
            return await self.create_cold_bitcoin_wallet()
        
        else:
            raise HTTPException(status_code=400, detail=f"Bitcoin wallet type {request.wallet_type} not implemented")
    
    async def create_ethereum_wallet(self, request: CreateWalletRequest) -> Dict[str, Any]:
        """Create Ethereum-compatible wallet"""
        if request.wallet_type == WalletType.HOT:
            # Generate mnemonic
            mnemo = mnemonic.Mnemonic("english")
            mnemonic_phrase = mnemo.generate(strength=256)
            
            # Generate seed
            seed = Bip39SeedGenerator(mnemonic_phrase).Generate()
            
            # Generate wallet from seed
            bip44_mst_ctx = Bip44.FromSeed(seed, Bip44Coins.ETHEREUM)
            bip44_acc_ctx = bip44_mst_ctx.Purpose().Coin().Account(0)
            bip44_chg_ctx = bip44_acc_ctx.Change(Bip44Changes.CHAIN_EXT)
            bip44_addr_ctx = bip44_chg_ctx.AddressIndex(0)
            
            private_key = bip44_addr_ctx.PrivateKey().Raw().ToHex()
            public_key = bip44_addr_ctx.PublicKey().RawCompressed().ToHex()
            address = bip44_addr_ctx.PublicKey().ToAddress()
            
            return {
                'private_key': private_key,
                'public_key': public_key,
                'address': address,
                'mnemonic': mnemonic_phrase,
                'derivation_path': "m/44'/60'/0'/0/0"
            }
        
        elif request.wallet_type == WalletType.SMART_CONTRACT:
            return await self.create_smart_contract_wallet(request)
        
        else:
            raise HTTPException(status_code=400, detail=f"Ethereum wallet type {request.wallet_type} not implemented")
    
    async def create_solana_wallet(self, request: CreateWalletRequest) -> Dict[str, Any]:
        """Create Solana wallet"""
        if request.wallet_type == WalletType.HOT:
            # Generate keypair
            keypair = Keypair()
            
            private_key = base58.b58encode(keypair.secret_key).decode()
            public_key = str(keypair.public_key)
            address = str(keypair.public_key)
            
            # Generate mnemonic if requested
            mnemonic_phrase = None
            if BackupType.MNEMONIC in request.backup_types:
                mnemo = mnemonic.Mnemonic("english")
                mnemonic_phrase = mnemo.generate(strength=256)
            
            return {
                'private_key': private_key,
                'public_key': public_key,
                'address': address,
                'mnemonic': mnemonic_phrase,
                'derivation_path': "m/44'/501'/0'/0'"
            }
        
        else:
            raise HTTPException(status_code=400, detail=f"Solana wallet type {request.wallet_type} not implemented")
    
    async def create_smart_contract_wallet(self, request: CreateWalletRequest) -> Dict[str, Any]:
        """Create smart contract wallet (like Gnosis Safe)"""
        # This would deploy a smart contract wallet
        # Simplified implementation
        web3 = self.blockchain_clients[request.blockchain]
        
        # Generate owner key
        account = web3.eth.account.create()
        
        # In production, deploy actual smart contract wallet
        # For now, return the owner account details
        return {
            'private_key': account.privateKey.hex(),
            'public_key': account.address,
            'address': account.address,
            'mnemonic': None,
            'derivation_path': None
        }
    
    async def encrypt_sensitive_data(self, data: str, password: Optional[str], security_level: SecurityLevel) -> str:
        """Encrypt sensitive data based on security level"""
        if security_level == SecurityLevel.BASIC:
            # Simple Fernet encryption
            return self.encryption_key.encrypt(data.encode()).decode()
        
        elif security_level == SecurityLevel.STANDARD:
            # Password-based encryption
            if not password:
                raise HTTPException(status_code=400, detail="Password required for standard security")
            
            return await self.encrypt_with_password(data, password)
        
        elif security_level in [SecurityLevel.HIGH, SecurityLevel.ENTERPRISE]:
            # AWS KMS encryption
            if self.aws_kms:
                return await self.encrypt_with_kms(data)
            else:
                # Fallback to password-based encryption
                return await self.encrypt_with_password(data, password or "default")
        
        elif security_level == SecurityLevel.MILITARY:
            # Hardware Security Module (HSM) encryption
            if config.HSM_ENDPOINT:
                return await self.encrypt_with_hsm(data)
            else:
                # Fallback to KMS
                return await self.encrypt_with_kms(data)
        
        else:
            raise HTTPException(status_code=400, detail="Invalid security level")
    
    async def encrypt_with_password(self, data: str, password: str) -> str:
        """Encrypt data with password using PBKDF2 + AES"""
        salt = get_random_bytes(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = kdf.derive(password.encode())
        
        cipher = AES.new(key, AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(data.encode())
        
        # Combine salt, nonce, tag, and ciphertext
        encrypted_data = salt + cipher.nonce + tag + ciphertext
        return base64.b64encode(encrypted_data).decode()
    
    async def encrypt_with_kms(self, data: str) -> str:
        """Encrypt data using AWS KMS"""
        try:
            response = self.aws_kms.encrypt(
                KeyId=config.KMS_KEY_ID,
                Plaintext=data.encode()
            )
            return base64.b64encode(response['CiphertextBlob']).decode()
        except Exception as e:
            logger.error(f"KMS encryption error: {e}")
            raise HTTPException(status_code=500, detail="Encryption failed")
    
    async def encrypt_with_hsm(self, data: str) -> str:
        """Encrypt data using Hardware Security Module"""
        # This would integrate with actual HSM
        # For now, return KMS encryption
        return await self.encrypt_with_kms(data)
    
    async def save_wallet_to_database(self, wallet_info: WalletInfo):
        """Save wallet information to database"""
        async with self.db_pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO wallets (
                    id, user_id, wallet_type, blockchain, address, public_key,
                    encrypted_private_key, mnemonic_encrypted, derivation_path,
                    security_level, backup_types, is_multi_sig, multi_sig_threshold,
                    multi_sig_participants, balance, status, created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18
                )
            """,
                wallet_info.id, wallet_info.user_id, wallet_info.wallet_type.value,
                wallet_info.blockchain.value, wallet_info.address, wallet_info.public_key,
                wallet_info.encrypted_private_key, wallet_info.mnemonic_encrypted,
                wallet_info.derivation_path, wallet_info.security_level.value,
                [bt.value for bt in wallet_info.backup_types], wallet_info.is_multi_sig,
                wallet_info.multi_sig_threshold, wallet_info.multi_sig_participants,
                json.dumps(wallet_info.balance), wallet_info.status.value,
                wallet_info.created_at, wallet_info.updated_at
            )
    
    async def initialize_balance_tracking(self, wallet_info: WalletInfo):
        """Initialize balance tracking for wallet"""
        try:
            # Start balance monitoring
            await self.update_wallet_balance(wallet_info.id)
            
            # Set up periodic balance updates
            await self.redis_client.sadd("wallet_balance_tracking", wallet_info.id)
            
        except Exception as e:
            logger.error(f"Error initializing balance tracking: {e}")
    
    async def update_wallet_balance(self, wallet_id: str):
        """Update wallet balance from blockchain"""
        try:
            async with self.db_pool.acquire() as conn:
                wallet = await conn.fetchrow("SELECT * FROM wallets WHERE id = $1", wallet_id)
                
                if not wallet:
                    return
                
                blockchain = Blockchain(wallet['blockchain'])
                address = wallet['address']
                
                if blockchain == Blockchain.BITCOIN:
                    balance = await self.get_bitcoin_balance(address)
                elif blockchain in [Blockchain.ETHEREUM, Blockchain.BINANCE_SMART_CHAIN, Blockchain.POLYGON]:
                    balance = await self.get_ethereum_balance(address, blockchain)
                elif blockchain == Blockchain.SOLANA:
                    balance = await self.get_solana_balance(address)
                else:
                    balance = {}
                
                # Update balance in database
                await conn.execute(
                    "UPDATE wallets SET balance = $1, updated_at = $2 WHERE id = $3",
                    json.dumps(balance), datetime.now(), wallet_id
                )
                
                # Cache balance in Redis
                await self.redis_client.setex(
                    f"wallet_balance:{wallet_id}",
                    300,  # 5 minutes TTL
                    json.dumps(balance)
                )
                
        except Exception as e:
            logger.error(f"Error updating wallet balance: {e}")
    
    async def get_bitcoin_balance(self, address: str) -> Dict[str, float]:
        """Get Bitcoin balance"""
        try:
            # This would integrate with Bitcoin RPC or blockchain API
            # For now, return mock data
            return {"BTC": 0.0}
        except Exception as e:
            logger.error(f"Error getting Bitcoin balance: {e}")
            return {"BTC": 0.0}
    
    async def get_ethereum_balance(self, address: str, blockchain: Blockchain) -> Dict[str, float]:
        """Get Ethereum-compatible blockchain balance"""
        try:
            web3 = self.blockchain_clients[blockchain]
            
            # Get native token balance
            balance_wei = web3.eth.get_balance(address)
            balance_eth = web3.fromWei(balance_wei, 'ether')
            
            native_symbol = {
                Blockchain.ETHEREUM: "ETH",
                Blockchain.BINANCE_SMART_CHAIN: "BNB",
                Blockchain.POLYGON: "MATIC"
            }.get(blockchain, "ETH")
            
            balances = {native_symbol: float(balance_eth)}
            
            # Get token balances (simplified - would need to track user's tokens)
            # This would query ERC-20 token contracts
            
            return balances
            
        except Exception as e:
            logger.error(f"Error getting Ethereum balance: {e}")
            return {"ETH": 0.0}
    
    async def get_solana_balance(self, address: str) -> Dict[str, float]:
        """Get Solana balance"""
        try:
            client = self.blockchain_clients[Blockchain.SOLANA]
            
            # Get SOL balance
            response = client.get_balance(address)
            balance_lamports = response['result']['value']
            balance_sol = balance_lamports / 1e9  # Convert lamports to SOL
            
            return {"SOL": balance_sol}
            
        except Exception as e:
            logger.error(f"Error getting Solana balance: {e}")
            return {"SOL": 0.0}
    
    async def import_wallet(self, user_id: int, request: ImportWalletRequest) -> WalletInfo:
        """Import existing wallet"""
        try:
            wallet_id = f"wallet_{secrets.token_hex(16)}"
            
            # Import wallet based on method
            if request.import_method == "mnemonic":
                wallet_data = await self.import_from_mnemonic(request)
            elif request.import_method == "private_key":
                wallet_data = await self.import_from_private_key(request)
            elif request.import_method == "keystore":
                wallet_data = await self.import_from_keystore(request)
            else:
                raise HTTPException(status_code=400, detail="Invalid import method")
            
            # Create wallet info
            wallet_info = WalletInfo(
                id=wallet_id,
                user_id=user_id,
                wallet_type=request.wallet_type,
                blockchain=request.blockchain,
                address=wallet_data['address'],
                public_key=wallet_data['public_key'],
                encrypted_private_key=await self.encrypt_sensitive_data(
                    wallet_data['private_key'],
                    request.password,
                    SecurityLevel.STANDARD
                ),
                mnemonic_encrypted=None,
                derivation_path=request.derivation_path or "m/44'/60'/0'/0/0",
                security_level=SecurityLevel.STANDARD,
                backup_types=[BackupType.PRIVATE_KEY],
                is_multi_sig=False,
                multi_sig_threshold=None,
                multi_sig_participants=[],
                balance={},
                status=WalletStatus.ACTIVE,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                last_used_at=None
            )
            
            # Save to database
            await self.save_wallet_to_database(wallet_info)
            
            # Initialize balance tracking
            await self.initialize_balance_tracking(wallet_info)
            
            logger.info(f"Imported wallet {wallet_id} for user {user_id}")
            return wallet_info
            
        except Exception as e:
            logger.error(f"Error importing wallet: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def import_from_mnemonic(self, request: ImportWalletRequest) -> Dict[str, Any]:
        """Import wallet from mnemonic phrase"""
        try:
            # Validate mnemonic
            mnemo = mnemonic.Mnemonic("english")
            if not mnemo.check(request.import_data):
                raise HTTPException(status_code=400, detail="Invalid mnemonic phrase")
            
            # Generate seed
            seed = Bip39SeedGenerator(request.import_data).Generate()
            
            if request.blockchain in [Blockchain.ETHEREUM, Blockchain.BINANCE_SMART_CHAIN, Blockchain.POLYGON]:
                # Generate Ethereum wallet
                bip44_mst_ctx = Bip44.FromSeed(seed, Bip44Coins.ETHEREUM)
                bip44_acc_ctx = bip44_mst_ctx.Purpose().Coin().Account(0)
                bip44_chg_ctx = bip44_acc_ctx.Change(Bip44Changes.CHAIN_EXT)
                bip44_addr_ctx = bip44_chg_ctx.AddressIndex(0)
                
                private_key = bip44_addr_ctx.PrivateKey().Raw().ToHex()
                public_key = bip44_addr_ctx.PublicKey().RawCompressed().ToHex()
                address = bip44_addr_ctx.PublicKey().ToAddress()
                
                return {
                    'private_key': private_key,
                    'public_key': public_key,
                    'address': address
                }
            
            else:
                raise HTTPException(status_code=400, detail=f"Mnemonic import not supported for {request.blockchain}")
            
        except Exception as e:
            logger.error(f"Error importing from mnemonic: {e}")
            raise HTTPException(status_code=400, detail="Failed to import from mnemonic")
    
    async def import_from_private_key(self, request: ImportWalletRequest) -> Dict[str, Any]:
        """Import wallet from private key"""
        try:
            private_key = request.import_data
            
            if request.blockchain in [Blockchain.ETHEREUM, Blockchain.BINANCE_SMART_CHAIN, Blockchain.POLYGON]:
                web3 = self.blockchain_clients[request.blockchain]
                account = web3.eth.account.from_key(private_key)
                
                return {
                    'private_key': private_key,
                    'public_key': account.address,
                    'address': account.address
                }
            
            elif request.blockchain == Blockchain.BITCOIN:
                public_key = privtopub(private_key)
                address = pubtoaddr(public_key)
                
                return {
                    'private_key': private_key,
                    'public_key': public_key,
                    'address': address
                }
            
            else:
                raise HTTPException(status_code=400, detail=f"Private key import not supported for {request.blockchain}")
            
        except Exception as e:
            logger.error(f"Error importing from private key: {e}")
            raise HTTPException(status_code=400, detail="Failed to import from private key")
    
    async def import_from_keystore(self, request: ImportWalletRequest) -> Dict[str, Any]:
        """Import wallet from keystore file"""
        try:
            if not request.password:
                raise HTTPException(status_code=400, detail="Password required for keystore import")
            
            # Parse keystore JSON
            keystore_data = json.loads(request.import_data)
            
            if request.blockchain in [Blockchain.ETHEREUM, Blockchain.BINANCE_SMART_CHAIN, Blockchain.POLYGON]:
                web3 = self.blockchain_clients[request.blockchain]
                private_key = web3.eth.account.decrypt(keystore_data, request.password)
                account = web3.eth.account.from_key(private_key)
                
                return {
                    'private_key': private_key.hex(),
                    'public_key': account.address,
                    'address': account.address
                }
            
            else:
                raise HTTPException(status_code=400, detail=f"Keystore import not supported for {request.blockchain}")
            
        except Exception as e:
            logger.error(f"Error importing from keystore: {e}")
            raise HTTPException(status_code=400, detail="Failed to import from keystore")
    
    async def create_wallet_backup(self, wallet_id: str, backup_type: BackupType, password: str) -> Dict[str, Any]:
        """Create wallet backup"""
        try:
            async with self.db_pool.acquire() as conn:
                wallet = await conn.fetchrow("SELECT * FROM wallets WHERE id = $1", wallet_id)
                
                if not wallet:
                    raise HTTPException(status_code=404, detail="Wallet not found")
                
                if backup_type == BackupType.MNEMONIC:
                    if not wallet['mnemonic_encrypted']:
                        raise HTTPException(status_code=400, detail="Mnemonic not available for this wallet")
                    
                    # Decrypt mnemonic
                    mnemonic_phrase = await self.decrypt_sensitive_data(
                        wallet['mnemonic_encrypted'],
                        password,
                        SecurityLevel(wallet['security_level'])
                    )
                    
                    return {
                        'backup_type': backup_type.value,
                        'data': mnemonic_phrase,
                        'instructions': 'Store this mnemonic phrase securely. It can be used to recover your wallet.'
                    }
                
                elif backup_type == BackupType.PRIVATE_KEY:
                    if not wallet['encrypted_private_key']:
                        raise HTTPException(status_code=400, detail="Private key not available for this wallet")
                    
                    # Decrypt private key
                    private_key = await self.decrypt_sensitive_data(
                        wallet['encrypted_private_key'],
                        password,
                        SecurityLevel(wallet['security_level'])
                    )
                    
                    return {
                        'backup_type': backup_type.value,
                        'data': private_key,
                        'instructions': 'Store this private key securely. Never share it with anyone.'
                    }
                
                elif backup_type == BackupType.KEYSTORE:
                    # Generate keystore file
                    if wallet['blockchain'] in ['ethereum', 'binance_smart_chain', 'polygon']:
                        web3 = self.blockchain_clients[Blockchain(wallet['blockchain'])]
                        
                        # Decrypt private key
                        private_key = await self.decrypt_sensitive_data(
                            wallet['encrypted_private_key'],
                            password,
                            SecurityLevel(wallet['security_level'])
                        )
                        
                        # Create keystore
                        keystore = web3.eth.account.encrypt(private_key, password)
                        
                        return {
                            'backup_type': backup_type.value,
                            'data': json.dumps(keystore),
                            'instructions': 'Store this keystore file securely along with your password.'
                        }
                    
                    else:
                        raise HTTPException(status_code=400, detail="Keystore not supported for this blockchain")
                
                elif backup_type == BackupType.PAPER_WALLET:
                    # Generate paper wallet
                    return await self.generate_paper_wallet(wallet)
                
                else:
                    raise HTTPException(status_code=400, detail="Backup type not supported")
            
        except Exception as e:
            logger.error(f"Error creating wallet backup: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    async def decrypt_sensitive_data(self, encrypted_data: str, password: str, security_level: SecurityLevel) -> str:
        """Decrypt sensitive data based on security level"""
        if security_level == SecurityLevel.BASIC:
            return self.encryption_key.decrypt(encrypted_data.encode()).decode()
        
        elif security_level == SecurityLevel.STANDARD:
            return await self.decrypt_with_password(encrypted_data, password)
        
        elif security_level in [SecurityLevel.HIGH, SecurityLevel.ENTERPRISE]:
            if self.aws_kms:
                return await self.decrypt_with_kms(encrypted_data)
            else:
                return await self.decrypt_with_password(encrypted_data, password)
        
        elif security_level == SecurityLevel.MILITARY:
            if config.HSM_ENDPOINT:
                return await self.decrypt_with_hsm(encrypted_data)
            else:
                return await self.decrypt_with_kms(encrypted_data)
        
        else:
            raise HTTPException(status_code=400, detail="Invalid security level")
    
    async def decrypt_with_password(self, encrypted_data: str, password: str) -> str:
        """Decrypt data with password"""
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode())
            
            # Extract components
            salt = encrypted_bytes[:16]
            nonce = encrypted_bytes[16:32]
            tag = encrypted_bytes[32:48]
            ciphertext = encrypted_bytes[48:]
            
            # Derive key
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = kdf.derive(password.encode())
            
            # Decrypt
            cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
            plaintext = cipher.decrypt_and_verify(ciphertext, tag)
            
            return plaintext.decode()
            
        except Exception as e:
            logger.error(f"Password decryption error: {e}")
            raise HTTPException(status_code=400, detail="Decryption failed")
    
    async def decrypt_with_kms(self, encrypted_data: str) -> str:
        """Decrypt data using AWS KMS"""
        try:
            ciphertext_blob = base64.b64decode(encrypted_data.encode())
            response = self.aws_kms.decrypt(CiphertextBlob=ciphertext_blob)
            return response['Plaintext'].decode()
        except Exception as e:
            logger.error(f"KMS decryption error: {e}")
            raise HTTPException(status_code=500, detail="Decryption failed")
    
    async def decrypt_with_hsm(self, encrypted_data: str) -> str:
        """Decrypt data using Hardware Security Module"""
        # This would integrate with actual HSM
        return await self.decrypt_with_kms(encrypted_data)
    
    async def generate_paper_wallet(self, wallet: Dict) -> Dict[str, Any]:
        """Generate paper wallet with QR codes"""
        try:
            # Generate QR codes for address and private key
            address_qr = qrcode.QRCode(version=1, box_size=10, border=5)
            address_qr.add_data(wallet['address'])
            address_qr.make(fit=True)
            
            address_img = address_qr.make_image(fill_color="black", back_color="white")
            address_buffer = io.BytesIO()
            address_img.save(address_buffer, format='PNG')
            address_qr_data = base64.b64encode(address_buffer.getvalue()).decode()
            
            return {
                'backup_type': BackupType.PAPER_WALLET.value,
                'data': {
                    'address': wallet['address'],
                    'address_qr': f"data:image/png;base64,{address_qr_data}",
                    'blockchain': wallet['blockchain']
                },
                'instructions': 'Print this paper wallet and store it securely offline.'
            }
            
        except Exception as e:
            logger.error(f"Error generating paper wallet: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate paper wallet")

# Initialize wallet manager
wallet_manager = AdvancedWalletManager()

# API Endpoints
@app.post("/api/v1/wallets/create")
async def create_wallet(request: CreateWalletRequest, user_id: int = 1):  # In production, get from auth
    """Create a new wallet"""
    try:
        wallet_info = await wallet_manager.create_wallet(user_id, request)
        
        return {
            "wallet_id": wallet_info.id,
            "address": wallet_info.address,
            "blockchain": wallet_info.blockchain.value,
            "wallet_type": wallet_info.wallet_type.value,
            "status": wallet_info.status.value,
            "created_at": wallet_info.created_at
        }
        
    except Exception as e:
        logger.error(f"Error creating wallet: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/wallets/import")
async def import_wallet(request: ImportWalletRequest, user_id: int = 1):
    """Import existing wallet"""
    try:
        wallet_info = await wallet_manager.import_wallet(user_id, request)
        
        return {
            "wallet_id": wallet_info.id,
            "address": wallet_info.address,
            "blockchain": wallet_info.blockchain.value,
            "wallet_type": wallet_info.wallet_type.value,
            "status": wallet_info.status.value,
            "created_at": wallet_info.created_at
        }
        
    except Exception as e:
        logger.error(f"Error importing wallet: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/wallets/{wallet_id}")
async def get_wallet(wallet_id: str):
    """Get wallet information"""
    try:
        async with wallet_manager.db_pool.acquire() as conn:
            wallet = await conn.fetchrow("SELECT * FROM wallets WHERE id = $1", wallet_id)
            
            if not wallet:
                raise HTTPException(status_code=404, detail="Wallet not found")
            
            return {
                "wallet_id": wallet['id'],
                "address": wallet['address'],
                "blockchain": wallet['blockchain'],
                "wallet_type": wallet['wallet_type'],
                "security_level": wallet['security_level'],
                "balance": json.loads(wallet['balance']),
                "status": wallet['status'],
                "created_at": wallet['created_at'],
                "last_used_at": wallet['last_used_at']
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting wallet: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/wallets/{wallet_id}/balance")
async def get_wallet_balance(wallet_id: str):
    """Get wallet balance"""
    try:
        # Try to get from cache first
        cached_balance = await wallet_manager.redis_client.get(f"wallet_balance:{wallet_id}")
        if cached_balance:
            return {"balance": json.loads(cached_balance)}
        
        # Update balance from blockchain
        await wallet_manager.update_wallet_balance(wallet_id)
        
        # Get updated balance
        async with wallet_manager.db_pool.acquire() as conn:
            wallet = await conn.fetchrow("SELECT balance FROM wallets WHERE id = $1", wallet_id)
            
            if not wallet:
                raise HTTPException(status_code=404, detail="Wallet not found")
            
            return {"balance": json.loads(wallet['balance'])}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting wallet balance: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/wallets/{wallet_id}/backup")
async def create_wallet_backup(wallet_id: str, request: WalletBackupRequest):
    """Create wallet backup"""
    try:
        backup_data = await wallet_manager.create_wallet_backup(
            wallet_id,
            request.backup_type,
            request.password
        )
        
        return backup_data
        
    except Exception as e:
        logger.error(f"Error creating wallet backup: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/wallets")
async def get_user_wallets(user_id: int = 1, blockchain: Optional[Blockchain] = None):
    """Get user's wallets"""
    try:
        async with wallet_manager.db_pool.acquire() as conn:
            query = "SELECT * FROM wallets WHERE user_id = $1"
            params = [user_id]
            
            if blockchain:
                query += " AND blockchain = $2"
                params.append(blockchain.value)
            
            query += " ORDER BY created_at DESC"
            
            wallets = await conn.fetch(query, *params)
            
            return {
                "wallets": [
                    {
                        "wallet_id": wallet['id'],
                        "address": wallet['address'],
                        "blockchain": wallet['blockchain'],
                        "wallet_type": wallet['wallet_type'],
                        "balance": json.loads(wallet['balance']),
                        "status": wallet['status'],
                        "created_at": wallet['created_at']
                    }
                    for wallet in wallets
                ]
            }
        
    except Exception as e:
        logger.error(f"Error getting user wallets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)
