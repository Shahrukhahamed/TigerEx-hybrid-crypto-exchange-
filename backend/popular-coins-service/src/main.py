"""
TigerEx Popular Coins & Tokens Service
Comprehensive cryptocurrency and token management system
Supports all popular coins for spot, futures, margin, and options trading
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import json
import aiohttp
import asyncpg
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator
import requests
from decimal import Decimal
import ccxt
import websockets
from web3 import Web3
from solana.rpc.api import Client as SolanaClient
import base58

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="TigerEx Popular Coins Service",
    description="Comprehensive cryptocurrency and token management",
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
    
    # API Keys
    COINGECKO_API_KEY = os.getenv("COINGECKO_API_KEY")
    COINMARKETCAP_API_KEY = os.getenv("COINMARKETCAP_API_KEY")
    MESSARI_API_KEY = os.getenv("MESSARI_API_KEY")
    
    # Blockchain RPC URLs
    ETHEREUM_RPC = os.getenv("ETHEREUM_RPC", "https://mainnet.infura.io/v3/...")
    BSC_RPC = os.getenv("BSC_RPC", "https://bsc-dataseed.binance.org/")
    POLYGON_RPC = os.getenv("POLYGON_RPC", "https://polygon-rpc.com/")
    SOLANA_RPC = os.getenv("SOLANA_RPC", "https://api.mainnet-beta.solana.com")
    AVALANCHE_RPC = os.getenv("AVALANCHE_RPC", "https://api.avax.network/ext/bc/C/rpc")
    
    # Update intervals
    PRICE_UPDATE_INTERVAL = 10  # seconds
    MARKET_DATA_UPDATE_INTERVAL = 60  # seconds
    TOKEN_INFO_UPDATE_INTERVAL = 3600  # 1 hour

config = Config()

# Enums
class AssetType(str, Enum):
    CRYPTOCURRENCY = "cryptocurrency"
    TOKEN = "token"
    STABLECOIN = "stablecoin"
    DEFI_TOKEN = "defi_token"
    NFT_TOKEN = "nft_token"
    MEME_TOKEN = "meme_token"
    GOVERNANCE_TOKEN = "governance_token"

class Blockchain(str, Enum):
    BITCOIN = "bitcoin"
    ETHEREUM = "ethereum"
    BINANCE_SMART_CHAIN = "binance-smart-chain"
    POLYGON = "polygon"
    SOLANA = "solana"
    AVALANCHE = "avalanche"
    CARDANO = "cardano"
    POLKADOT = "polkadot"
    COSMOS = "cosmos"
    NEAR = "near"
    FANTOM = "fantom"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    TRON = "tron"
    PI_NETWORK = "pi-network"
    TON = "ton"

class TradingType(str, Enum):
    SPOT = "spot"
    FUTURES = "futures"
    MARGIN = "margin"
    OPTIONS = "options"

class MarketStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DELISTED = "delisted"
    MAINTENANCE = "maintenance"

# Data Models
@dataclass
class CoinInfo:
    id: str
    symbol: str
    name: str
    asset_type: AssetType
    blockchain: Blockchain
    contract_address: Optional[str]
    decimals: int
    total_supply: Optional[Decimal]
    circulating_supply: Optional[Decimal]
    max_supply: Optional[Decimal]
    market_cap: Optional[Decimal]
    current_price: Decimal
    price_change_24h: Decimal
    volume_24h: Decimal
    market_cap_rank: Optional[int]
    logo_url: str
    description: str
    website: str
    whitepaper: str
    github: str
    twitter: str
    telegram: str
    discord: str
    reddit: str
    is_verified: bool
    listing_date: datetime
    supported_trading_types: List[TradingType]
    market_status: MarketStatus
    created_at: datetime
    updated_at: datetime

@dataclass
class TradingPair:
    id: str
    base_asset: str
    quote_asset: str
    symbol: str
    trading_type: TradingType
    status: MarketStatus
    min_quantity: Decimal
    max_quantity: Decimal
    step_size: Decimal
    min_price: Decimal
    max_price: Decimal
    tick_size: Decimal
    min_notional: Decimal
    maker_fee: Decimal
    taker_fee: Decimal
    current_price: Decimal
    price_change_24h: Decimal
    volume_24h: Decimal
    high_24h: Decimal
    low_24h: Decimal
    created_at: datetime
    updated_at: datetime

# Pydantic Models
class AddCoinRequest(BaseModel):
    symbol: str
    name: str
    asset_type: AssetType
    blockchain: Blockchain
    contract_address: Optional[str] = None
    decimals: int = 18
    logo_url: Optional[str] = None
    description: Optional[str] = None
    website: Optional[str] = None
    supported_trading_types: List[TradingType] = [TradingType.SPOT]

class CreateTradingPairRequest(BaseModel):
    base_asset: str
    quote_asset: str
    trading_type: TradingType
    min_quantity: Decimal = Decimal("0.001")
    max_quantity: Optional[Decimal] = None
    step_size: Decimal = Decimal("0.001")
    min_price: Decimal = Decimal("0.0001")
    max_price: Optional[Decimal] = None
    tick_size: Decimal = Decimal("0.0001")
    min_notional: Decimal = Decimal("10.0")
    maker_fee: Decimal = Decimal("0.001")
    taker_fee: Decimal = Decimal("0.001")

class PriceUpdateRequest(BaseModel):
    symbol: str
    price: Decimal
    volume_24h: Optional[Decimal] = None
    price_change_24h: Optional[Decimal] = None

# Popular Coins Manager
class PopularCoinsManager:
    def __init__(self):
        self.redis_client = None
        self.db_pool = None
        self.web3_clients = {}
        self.solana_client = None
        self.price_feeds = {}
        self.supported_exchanges = []
        
        # Initialize blockchain clients
        asyncio.create_task(self.initialize_clients())
        
        # Start background tasks
        asyncio.create_task(self.start_background_tasks())
    
    async def initialize_clients(self):
        """Initialize blockchain and external API clients"""
        try:
            # Redis client
            self.redis_client = redis.from_url(config.REDIS_URL)
            
            # Database pool
            self.db_pool = await asyncpg.create_pool(config.DATABASE_URL)
            
            # Web3 clients
            self.web3_clients = {
                Blockchain.ETHEREUM: Web3(Web3.HTTPProvider(config.ETHEREUM_RPC)),
                Blockchain.BINANCE_SMART_CHAIN: Web3(Web3.HTTPProvider(config.BSC_RPC)),
                Blockchain.POLYGON: Web3(Web3.HTTPProvider(config.POLYGON_RPC)),
                Blockchain.AVALANCHE: Web3(Web3.HTTPProvider(config.AVALANCHE_RPC))
            }
            
            # Solana client
            self.solana_client = SolanaClient(config.SOLANA_RPC)
            
            # Initialize supported exchanges
            self.supported_exchanges = [
                ccxt.binance(),
                ccxt.okx(),
                ccxt.bybit(),
                ccxt.kucoin(),
                ccxt.gateio(),
                ccxt.mexc(),
                ccxt.bitget()
            ]
            
            logger.info("Blockchain clients initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing clients: {e}")
    
    async def start_background_tasks(self):
        """Start background monitoring and update tasks"""
        asyncio.create_task(self.price_update_loop())
        asyncio.create_task(self.market_data_update_loop())
        asyncio.create_task(self.token_info_update_loop())
    
    async def price_update_loop(self):
        """Continuously update cryptocurrency prices"""
        while True:
            try:
                await self.update_all_prices()
                await asyncio.sleep(config.PRICE_UPDATE_INTERVAL)
            except Exception as e:
                logger.error(f"Error in price update loop: {e}")
                await asyncio.sleep(30)
    
    async def market_data_update_loop(self):
        """Update market data from external sources"""
        while True:
            try:
                await self.update_market_data()
                await asyncio.sleep(config.MARKET_DATA_UPDATE_INTERVAL)
            except Exception as e:
                logger.error(f"Error in market data update loop: {e}")
                await asyncio.sleep(60)
    
    async def token_info_update_loop(self):
        """Update token information and metadata"""
        while True:
            try:
                await self.update_token_info()
                await asyncio.sleep(config.TOKEN_INFO_UPDATE_INTERVAL)
            except Exception as e:
                logger.error(f"Error in token info update loop: {e}")
                await asyncio.sleep(300)
    
    async def add_popular_coins(self):
        """Add all popular cryptocurrencies and tokens"""
        popular_coins = [
            # Major Cryptocurrencies
            {
                "symbol": "BTC",
                "name": "Bitcoin",
                "asset_type": AssetType.CRYPTOCURRENCY,
                "blockchain": Blockchain.BITCOIN,
                "coingecko_id": "bitcoin",
                "supported_trading_types": [TradingType.SPOT, TradingType.FUTURES, TradingType.MARGIN, TradingType.OPTIONS]
            },
            {
                "symbol": "ETH",
                "name": "Ethereum",
                "asset_type": AssetType.CRYPTOCURRENCY,
                "blockchain": Blockchain.ETHEREUM,
                "coingecko_id": "ethereum",
                "supported_trading_types": [TradingType.SPOT, TradingType.FUTURES, TradingType.MARGIN, TradingType.OPTIONS]
            },
            {
                "symbol": "BNB",
                "name": "BNB",
                "asset_type": AssetType.CRYPTOCURRENCY,
                "blockchain": Blockchain.BINANCE_SMART_CHAIN,
                "coingecko_id": "binancecoin",
                "supported_trading_types": [TradingType.SPOT, TradingType.FUTURES, TradingType.MARGIN]
            },
            {
                "symbol": "SOL",
                "name": "Solana",
                "asset_type": AssetType.CRYPTOCURRENCY,
                "blockchain": Blockchain.SOLANA,
                "coingecko_id": "solana",
                "supported_trading_types": [TradingType.SPOT, TradingType.FUTURES, TradingType.MARGIN]
            },
            {
                "symbol": "ADA",
                "name": "Cardano",
                "asset_type": AssetType.CRYPTOCURRENCY,
                "blockchain": Blockchain.CARDANO,
                "coingecko_id": "cardano",
                "supported_trading_types": [TradingType.SPOT, TradingType.FUTURES, TradingType.MARGIN]
            },
            {
                "symbol": "AVAX",
                "name": "Avalanche",
                "asset_type": AssetType.CRYPTOCURRENCY,
                "blockchain": Blockchain.AVALANCHE,
                "coingecko_id": "avalanche-2",
                "supported_trading_types": [TradingType.SPOT, TradingType.FUTURES, TradingType.MARGIN]
            },
            {
                "symbol": "DOT",
                "name": "Polkadot",
                "asset_type": AssetType.CRYPTOCURRENCY,
                "blockchain": Blockchain.POLKADOT,
                "coingecko_id": "polkadot",
                "supported_trading_types": [TradingType.SPOT, TradingType.FUTURES, TradingType.MARGIN]
            },
            {
                "symbol": "MATIC",
                "name": "Polygon",
                "asset_type": AssetType.CRYPTOCURRENCY,
                "blockchain": Blockchain.POLYGON,
                "coingecko_id": "matic-network",
                "supported_trading_types": [TradingType.SPOT, TradingType.FUTURES, TradingType.MARGIN]
            },
            
            # Stablecoins
            {
                "symbol": "USDT",
                "name": "Tether",
                "asset_type": AssetType.STABLECOIN,
                "blockchain": Blockchain.ETHEREUM,
                "contract_address": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
                "coingecko_id": "tether",
                "supported_trading_types": [TradingType.SPOT, TradingType.MARGIN]
            },
            {
                "symbol": "USDC",
                "name": "USD Coin",
                "asset_type": AssetType.STABLECOIN,
                "blockchain": Blockchain.ETHEREUM,
                "contract_address": "0xA0b86a33E6441E6C7D3E4C",
                "coingecko_id": "usd-coin",
                "supported_trading_types": [TradingType.SPOT, TradingType.MARGIN]
            },
            {
                "symbol": "BUSD",
                "name": "Binance USD",
                "asset_type": AssetType.STABLECOIN,
                "blockchain": Blockchain.BINANCE_SMART_CHAIN,
                "contract_address": "0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56",
                "coingecko_id": "binance-usd",
                "supported_trading_types": [TradingType.SPOT, TradingType.MARGIN]
            },
            
            # DeFi Tokens
            {
                "symbol": "UNI",
                "name": "Uniswap",
                "asset_type": AssetType.DEFI_TOKEN,
                "blockchain": Blockchain.ETHEREUM,
                "contract_address": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
                "coingecko_id": "uniswap",
                "supported_trading_types": [TradingType.SPOT, TradingType.FUTURES, TradingType.MARGIN]
            },
            {
                "symbol": "AAVE",
                "name": "Aave",
                "asset_type": AssetType.DEFI_TOKEN,
                "blockchain": Blockchain.ETHEREUM,
                "contract_address": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9",
                "coingecko_id": "aave",
                "supported_trading_types": [TradingType.SPOT, TradingType.FUTURES, TradingType.MARGIN]
            },
            {
                "symbol": "COMP",
                "name": "Compound",
                "asset_type": AssetType.DEFI_TOKEN,
                "blockchain": Blockchain.ETHEREUM,
                "contract_address": "0xc00e94Cb662C3520282E6f5717214004A7f26888",
                "coingecko_id": "compound-governance-token",
                "supported_trading_types": [TradingType.SPOT, TradingType.FUTURES, TradingType.MARGIN]
            },
            {
                "symbol": "SUSHI",
                "name": "SushiSwap",
                "asset_type": AssetType.DEFI_TOKEN,
                "blockchain": Blockchain.ETHEREUM,
                "contract_address": "0x6B3595068778DD592e39A122f4f5a5cF09C90fE2",
                "coingecko_id": "sushi",
                "supported_trading_types": [TradingType.SPOT, TradingType.FUTURES, TradingType.MARGIN]
            },
            
            # Layer 2 Tokens
            {
                "symbol": "ARB",
                "name": "Arbitrum",
                "asset_type": AssetType.TOKEN,
                "blockchain": Blockchain.ARBITRUM,
                "coingecko_id": "arbitrum",
                "supported_trading_types": [TradingType.SPOT, TradingType.FUTURES]
            },
            {
                "symbol": "OP",
                "name": "Optimism",
                "asset_type": AssetType.TOKEN,
                "blockchain": Blockchain.OPTIMISM,
                "coingecko_id": "optimism",
                "supported_trading_types": [TradingType.SPOT, TradingType.FUTURES]
            },
            
            # Meme Tokens
            {
                "symbol": "DOGE",
                "name": "Dogecoin",
                "asset_type": AssetType.MEME_TOKEN,
                "blockchain": Blockchain.BITCOIN,  # Dogecoin has its own blockchain
                "coingecko_id": "dogecoin",
                "supported_trading_types": [TradingType.SPOT, TradingType.FUTURES, TradingType.MARGIN]
            },
            {
                "symbol": "SHIB",
                "name": "Shiba Inu",
                "asset_type": AssetType.MEME_TOKEN,
                "blockchain": Blockchain.ETHEREUM,
                "contract_address": "0x95aD61b0a150d79219dCF64E1E6Cc01f0B64C4cE",
                "coingecko_id": "shiba-inu",
                "supported_trading_types": [TradingType.SPOT, TradingType.FUTURES]
            },
            
            # Additional Popular Tokens
            {
                "symbol": "LINK",
                "name": "Chainlink",
                "asset_type": AssetType.TOKEN,
                "blockchain": Blockchain.ETHEREUM,
                "contract_address": "0x514910771AF9Ca656af840dff83E8264EcF986CA",
                "coingecko_id": "chainlink",
                "supported_trading_types": [TradingType.SPOT, TradingType.FUTURES, TradingType.MARGIN]
            },
            {
                "symbol": "LTC",
                "name": "Litecoin",
                "asset_type": AssetType.CRYPTOCURRENCY,
                "blockchain": Blockchain.BITCOIN,  # Litecoin has its own blockchain
                "coingecko_id": "litecoin",
                "supported_trading_types": [TradingType.SPOT, TradingType.FUTURES, TradingType.MARGIN]
            },
            {
                "symbol": "BCH",
                "name": "Bitcoin Cash",
                "asset_type": AssetType.CRYPTOCURRENCY,
                "blockchain": Blockchain.BITCOIN,  # Bitcoin Cash has its own blockchain
                "coingecko_id": "bitcoin-cash",
                "supported_trading_types": [TradingType.SPOT, TradingType.FUTURES, TradingType.MARGIN]
            },
            {
                "symbol": "XRP",
                "name": "XRP",
                "asset_type": AssetType.CRYPTOCURRENCY,
                "blockchain": Blockchain.BITCOIN,  # XRP has its own blockchain
                "coingecko_id": "ripple",
                "supported_trading_types": [TradingType.SPOT, TradingType.FUTURES, TradingType.MARGIN]
            },
            {
                "symbol": "TRX",
                "name": "TRON",
                "asset_type": AssetType.CRYPTOCURRENCY,
                "blockchain": Blockchain.TRON,
                "coingecko_id": "tron",
                "supported_trading_types": [TradingType.SPOT, TradingType.FUTURES, TradingType.MARGIN]
            },
            {
                "symbol": "TON",
                "name": "Toncoin",
                "asset_type": AssetType.CRYPTOCURRENCY,
                "blockchain": Blockchain.TON,
                "coingecko_id": "the-open-network",
                "supported_trading_types": [TradingType.SPOT, TradingType.FUTURES]
            },
            {
                "symbol": "PI",
                "name": "Pi Network",
                "asset_type": AssetType.CRYPTOCURRENCY,
                "blockchain": Blockchain.PI_NETWORK,
                "coingecko_id": "pi-network",
                "supported_trading_types": [TradingType.SPOT]
            }
        ]
        
        for coin_data in popular_coins:
            try:
                await self.add_coin_to_database(coin_data)
                await self.create_default_trading_pairs(coin_data)
            except Exception as e:
                logger.error(f"Error adding coin {coin_data['symbol']}: {e}")
    
    async def add_coin_to_database(self, coin_data: Dict[str, Any]):
        """Add coin to database"""
        async with self.db_pool.acquire() as conn:
            # Check if coin already exists
            existing = await conn.fetchrow(
                "SELECT id FROM coins WHERE symbol = $1",
                coin_data["symbol"]
            )
            
            if existing:
                logger.info(f"Coin {coin_data['symbol']} already exists")
                return
            
            # Get additional data from CoinGecko
            coin_info = await self.fetch_coin_info_from_coingecko(coin_data.get("coingecko_id"))
            
            # Insert coin
            await conn.execute("""
                INSERT INTO coins (
                    symbol, name, asset_type, blockchain, contract_address,
                    decimals, total_supply, circulating_supply, max_supply,
                    market_cap, current_price, price_change_24h, volume_24h,
                    market_cap_rank, logo_url, description, website,
                    whitepaper, github, twitter, telegram, discord, reddit,
                    is_verified, listing_date, supported_trading_types,
                    market_status, created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13,
                    $14, $15, $16, $17, $18, $19, $20, $21, $22, $23, $24,
                    $25, $26, $27, $28, $29
                )
            """,
                coin_data["symbol"],
                coin_data["name"],
                coin_data["asset_type"].value,
                coin_data["blockchain"].value,
                coin_data.get("contract_address"),
                coin_data.get("decimals", 18),
                coin_info.get("total_supply"),
                coin_info.get("circulating_supply"),
                coin_info.get("max_supply"),
                coin_info.get("market_cap"),
                coin_info.get("current_price", 0),
                coin_info.get("price_change_24h", 0),
                coin_info.get("volume_24h", 0),
                coin_info.get("market_cap_rank"),
                coin_info.get("logo_url", ""),
                coin_info.get("description", ""),
                coin_info.get("website", ""),
                coin_info.get("whitepaper", ""),
                coin_info.get("github", ""),
                coin_info.get("twitter", ""),
                coin_info.get("telegram", ""),
                coin_info.get("discord", ""),
                coin_info.get("reddit", ""),
                True,  # is_verified
                datetime.now(),  # listing_date
                [t.value for t in coin_data["supported_trading_types"]],
                MarketStatus.ACTIVE.value,
                datetime.now(),
                datetime.now()
            )
            
            logger.info(f"Added coin {coin_data['symbol']} to database")
    
    async def create_default_trading_pairs(self, coin_data: Dict[str, Any]):
        """Create default trading pairs for a coin"""
        base_asset = coin_data["symbol"]
        quote_assets = ["USDT", "USDC", "BTC", "ETH"]
        
        # Don't create pairs for stablecoins against other stablecoins
        if coin_data["asset_type"] == AssetType.STABLECOIN:
            quote_assets = ["BTC", "ETH"]
        
        for quote_asset in quote_assets:
            if base_asset == quote_asset:
                continue
            
            for trading_type in coin_data["supported_trading_types"]:
                try:
                    await self.create_trading_pair(
                        base_asset=base_asset,
                        quote_asset=quote_asset,
                        trading_type=trading_type
                    )
                except Exception as e:
                    logger.error(f"Error creating trading pair {base_asset}{quote_asset}: {e}")
    
    async def create_trading_pair(self, base_asset: str, quote_asset: str, trading_type: TradingType):
        """Create a trading pair"""
        symbol = f"{base_asset}{quote_asset}"
        
        async with self.db_pool.acquire() as conn:
            # Check if pair already exists
            existing = await conn.fetchrow(
                "SELECT id FROM trading_pairs WHERE symbol = $1 AND trading_type = $2",
                symbol, trading_type.value
            )
            
            if existing:
                return
            
            # Insert trading pair
            await conn.execute("""
                INSERT INTO trading_pairs (
                    base_asset, quote_asset, symbol, trading_type, status,
                    min_quantity, max_quantity, step_size, min_price, max_price,
                    tick_size, min_notional, maker_fee, taker_fee,
                    current_price, price_change_24h, volume_24h, high_24h, low_24h,
                    created_at, updated_at
                ) VALUES (
                    $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14,
                    $15, $16, $17, $18, $19, $20, $21
                )
            """,
                base_asset, quote_asset, symbol, trading_type.value, MarketStatus.ACTIVE.value,
                Decimal("0.001"), None, Decimal("0.001"), Decimal("0.0001"), None,
                Decimal("0.0001"), Decimal("10.0"), Decimal("0.001"), Decimal("0.001"),
                Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"), Decimal("0"),
                datetime.now(), datetime.now()
            )
    
    async def fetch_coin_info_from_coingecko(self, coingecko_id: str) -> Dict[str, Any]:
        """Fetch coin information from CoinGecko API"""
        if not coingecko_id:
            return {}
        
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
                            "total_supply": data.get("market_data", {}).get("total_supply"),
                            "circulating_supply": data.get("market_data", {}).get("circulating_supply"),
                            "max_supply": data.get("market_data", {}).get("max_supply"),
                            "market_cap": data.get("market_data", {}).get("market_cap", {}).get("usd"),
                            "current_price": data.get("market_data", {}).get("current_price", {}).get("usd"),
                            "price_change_24h": data.get("market_data", {}).get("price_change_percentage_24h"),
                            "volume_24h": data.get("market_data", {}).get("total_volume", {}).get("usd"),
                            "market_cap_rank": data.get("market_cap_rank"),
                            "logo_url": data.get("image", {}).get("large", ""),
                            "description": data.get("description", {}).get("en", ""),
                            "website": data.get("links", {}).get("homepage", [""])[0],
                            "github": data.get("links", {}).get("repos_url", {}).get("github", [""])[0] if data.get("links", {}).get("repos_url", {}).get("github") else "",
                            "twitter": data.get("links", {}).get("twitter_screen_name", ""),
                            "telegram": data.get("links", {}).get("telegram_channel_identifier", ""),
                            "reddit": data.get("links", {}).get("subreddit_url", "")
                        }
        except Exception as e:
            logger.error(f"Error fetching coin info from CoinGecko: {e}")
            return {}
    
    async def update_all_prices(self):
        """Update prices for all coins"""
        try:
            # Get all coins from database
            async with self.db_pool.acquire() as conn:
                coins = await conn.fetch("SELECT symbol, blockchain, contract_address FROM coins WHERE market_status = 'active'")
            
            # Update prices from multiple sources
            await self.update_prices_from_exchanges(coins)
            await self.update_prices_from_coingecko(coins)
            
        except Exception as e:
            logger.error(f"Error updating all prices: {e}")
    
    async def update_prices_from_exchanges(self, coins: List[Dict]):
        """Update prices from supported exchanges"""
        for exchange in self.supported_exchanges:
            try:
                # Fetch tickers from exchange
                tickers = exchange.fetch_tickers()
                
                for symbol, ticker in tickers.items():
                    # Update price in database and cache
                    await self.update_price_in_cache(symbol, ticker['last'], ticker.get('percentage', 0), ticker.get('quoteVolume', 0))
                
            except Exception as e:
                logger.error(f"Error updating prices from {exchange.name}: {e}")
    
    async def update_prices_from_coingecko(self, coins: List[Dict]):
        """Update prices from CoinGecko"""
        try:
            # Get coin IDs for CoinGecko
            coin_ids = []
            for coin in coins:
                # Map symbol to CoinGecko ID (simplified)
                coingecko_id = self.get_coingecko_id(coin['symbol'])
                if coingecko_id:
                    coin_ids.append(coingecko_id)
            
            if not coin_ids:
                return
            
            # Fetch prices from CoinGecko
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {
                "ids": ",".join(coin_ids),
                "vs_currencies": "usd",
                "include_24hr_change": "true",
                "include_24hr_vol": "true"
            }
            
            headers = {}
            if config.COINGECKO_API_KEY:
                headers["X-CG-Demo-API-Key"] = config.COINGECKO_API_KEY
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        for coin_id, price_data in data.items():
                            symbol = self.get_symbol_from_coingecko_id(coin_id)
                            if symbol:
                                await self.update_price_in_cache(
                                    f"{symbol}USDT",
                                    price_data.get("usd", 0),
                                    price_data.get("usd_24h_change", 0),
                                    price_data.get("usd_24h_vol", 0)
                                )
            
        except Exception as e:
            logger.error(f"Error updating prices from CoinGecko: {e}")
    
    async def update_price_in_cache(self, symbol: str, price: float, change_24h: float, volume_24h: float):
        """Update price in Redis cache and database"""
        try:
            # Update in Redis
            price_data = {
                "symbol": symbol,
                "price": price,
                "change_24h": change_24h,
                "volume_24h": volume_24h,
                "timestamp": datetime.now().isoformat()
            }
            
            await self.redis_client.setex(
                f"price:{symbol}",
                300,  # 5 minutes TTL
                json.dumps(price_data)
            )
            
            # Update in database
            async with self.db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE trading_pairs 
                    SET current_price = $1, price_change_24h = $2, volume_24h = $3, updated_at = $4
                    WHERE symbol = $5
                """, Decimal(str(price)), Decimal(str(change_24h)), Decimal(str(volume_24h)), datetime.now(), symbol)
            
        except Exception as e:
            logger.error(f"Error updating price in cache for {symbol}: {e}")
    
    def get_coingecko_id(self, symbol: str) -> Optional[str]:
        """Map symbol to CoinGecko ID"""
        mapping = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "BNB": "binancecoin",
            "SOL": "solana",
            "ADA": "cardano",
            "AVAX": "avalanche-2",
            "DOT": "polkadot",
            "MATIC": "matic-network",
            "USDT": "tether",
            "USDC": "usd-coin",
            "BUSD": "binance-usd",
            "UNI": "uniswap",
            "AAVE": "aave",
            "COMP": "compound-governance-token",
            "SUSHI": "sushi",
            "LINK": "chainlink",
            "LTC": "litecoin",
            "BCH": "bitcoin-cash",
            "XRP": "ripple",
            "DOGE": "dogecoin",
            "SHIB": "shiba-inu",
            "TRX": "tron",
            "TON": "the-open-network",
            "PI": "pi-network"
        }
        return mapping.get(symbol)
    
    def get_symbol_from_coingecko_id(self, coingecko_id: str) -> Optional[str]:
        """Map CoinGecko ID to symbol"""
        mapping = {
            "bitcoin": "BTC",
            "ethereum": "ETH",
            "binancecoin": "BNB",
            "solana": "SOL",
            "cardano": "ADA",
            "avalanche-2": "AVAX",
            "polkadot": "DOT",
            "matic-network": "MATIC",
            "tether": "USDT",
            "usd-coin": "USDC",
            "binance-usd": "BUSD",
            "uniswap": "UNI",
            "aave": "AAVE",
            "compound-governance-token": "COMP",
            "sushi": "SUSHI",
            "chainlink": "LINK",
            "litecoin": "LTC",
            "bitcoin-cash": "BCH",
            "ripple": "XRP",
            "dogecoin": "DOGE",
            "shiba-inu": "SHIB",
            "tron": "TRX",
            "the-open-network": "TON",
            "pi-network": "PI"
        }
        return mapping.get(coingecko_id)
    
    async def update_market_data(self):
        """Update comprehensive market data"""
        try:
            # Update from CoinMarketCap
            if config.COINMARKETCAP_API_KEY:
                await self.update_from_coinmarketcap()
            
            # Update from Messari
            if config.MESSARI_API_KEY:
                await self.update_from_messari()
            
        except Exception as e:
            logger.error(f"Error updating market data: {e}")
    
    async def update_token_info(self):
        """Update token information and metadata"""
        try:
            # Update token contract information
            await self.update_token_contracts()
            
            # Update social media and project information
            await self.update_project_info()
            
        except Exception as e:
            logger.error(f"Error updating token info: {e}")
    
    async def update_token_contracts(self):
        """Update token contract information from blockchain"""
        try:
            async with self.db_pool.acquire() as conn:
                tokens = await conn.fetch("""
                    SELECT symbol, blockchain, contract_address 
                    FROM coins 
                    WHERE contract_address IS NOT NULL AND asset_type = 'token'
                """)
            
            for token in tokens:
                blockchain = token['blockchain']
                contract_address = token['contract_address']
                
                if blockchain in self.web3_clients:
                    web3 = self.web3_clients[blockchain]
                    
                    # Get token information from contract
                    try:
                        # This is a simplified example - in production, use proper ABI
                        contract = web3.eth.contract(
                            address=contract_address,
                            abi=[
                                {"constant": True, "inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "type": "function"},
                                {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"}
                            ]
                        )
                        
                        total_supply = contract.functions.totalSupply().call()
                        decimals = contract.functions.decimals().call()
                        
                        # Update in database
                        await conn.execute("""
                            UPDATE coins 
                            SET total_supply = $1, decimals = $2, updated_at = $3
                            WHERE symbol = $4
                        """, total_supply, decimals, datetime.now(), token['symbol'])
                        
                    except Exception as e:
                        logger.error(f"Error updating contract info for {token['symbol']}: {e}")
            
        except Exception as e:
            logger.error(f"Error updating token contracts: {e}")

# Initialize manager
coins_manager = PopularCoinsManager()

# API Endpoints
@app.post("/api/v1/coins/add")
async def add_coin(request: AddCoinRequest):
    """Add a new coin or token"""
    try:
        coin_data = {
            "symbol": request.symbol,
            "name": request.name,
            "asset_type": request.asset_type,
            "blockchain": request.blockchain,
            "contract_address": request.contract_address,
            "decimals": request.decimals,
            "supported_trading_types": request.supported_trading_types
        }
        
        await coins_manager.add_coin_to_database(coin_data)
        await coins_manager.create_default_trading_pairs(coin_data)
        
        return {
            "message": f"Coin {request.symbol} added successfully",
            "symbol": request.symbol
        }
        
    except Exception as e:
        logger.error(f"Error adding coin: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/trading-pairs/create")
async def create_trading_pair(request: CreateTradingPairRequest):
    """Create a new trading pair"""
    try:
        await coins_manager.create_trading_pair(
            base_asset=request.base_asset,
            quote_asset=request.quote_asset,
            trading_type=request.trading_type
        )
        
        return {
            "message": f"Trading pair {request.base_asset}{request.quote_asset} created successfully",
            "symbol": f"{request.base_asset}{request.quote_asset}",
            "trading_type": request.trading_type.value
        }
        
    except Exception as e:
        logger.error(f"Error creating trading pair: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/coins")
async def get_all_coins(
    asset_type: Optional[AssetType] = None,
    blockchain: Optional[Blockchain] = None,
    trading_type: Optional[TradingType] = None,
    limit: int = 100,
    offset: int = 0
):
    """Get all coins with optional filtering"""
    try:
        async with coins_manager.db_pool.acquire() as conn:
            query = "SELECT * FROM coins WHERE market_status = 'active'"
            params = []
            param_count = 0
            
            if asset_type:
                param_count += 1
                query += f" AND asset_type = ${param_count}"
                params.append(asset_type.value)
            
            if blockchain:
                param_count += 1
                query += f" AND blockchain = ${param_count}"
                params.append(blockchain.value)
            
            if trading_type:
                param_count += 1
                query += f" AND ${param_count} = ANY(supported_trading_types)"
                params.append(trading_type.value)
            
            query += f" ORDER BY market_cap_rank NULLS LAST, market_cap DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
            params.extend([limit, offset])
            
            coins = await conn.fetch(query, *params)
            
            return {
                "coins": [dict(coin) for coin in coins],
                "total": len(coins)
            }
        
    except Exception as e:
        logger.error(f"Error getting coins: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/trading-pairs")
async def get_trading_pairs(
    trading_type: Optional[TradingType] = None,
    base_asset: Optional[str] = None,
    quote_asset: Optional[str] = None,
    limit: int = 100,
    offset: int = 0
):
    """Get trading pairs with optional filtering"""
    try:
        async with coins_manager.db_pool.acquire() as conn:
            query = "SELECT * FROM trading_pairs WHERE status = 'active'"
            params = []
            param_count = 0
            
            if trading_type:
                param_count += 1
                query += f" AND trading_type = ${param_count}"
                params.append(trading_type.value)
            
            if base_asset:
                param_count += 1
                query += f" AND base_asset = ${param_count}"
                params.append(base_asset)
            
            if quote_asset:
                param_count += 1
                query += f" AND quote_asset = ${param_count}"
                params.append(quote_asset)
            
            query += f" ORDER BY volume_24h DESC LIMIT ${param_count + 1} OFFSET ${param_count + 2}"
            params.extend([limit, offset])
            
            pairs = await conn.fetch(query, *params)
            
            return {
                "trading_pairs": [dict(pair) for pair in pairs],
                "total": len(pairs)
            }
        
    except Exception as e:
        logger.error(f"Error getting trading pairs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/prices/{symbol}")
async def get_price(symbol: str):
    """Get current price for a symbol"""
    try:
        price_data = await coins_manager.redis_client.get(f"price:{symbol}")
        if price_data:
            return json.loads(price_data)
        else:
            raise HTTPException(status_code=404, detail="Price not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting price: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/prices")
async def get_all_prices():
    """Get all current prices"""
    try:
        # Get all price keys from Redis
        keys = await coins_manager.redis_client.keys("price:*")
        prices = {}
        
        for key in keys:
            price_data = await coins_manager.redis_client.get(key)
            if price_data:
                symbol = key.decode().replace("price:", "")
                prices[symbol] = json.loads(price_data)
        
        return {"prices": prices}
        
    except Exception as e:
        logger.error(f"Error getting all prices: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/coins/initialize-popular")
async def initialize_popular_coins():
    """Initialize all popular coins and tokens"""
    try:
        await coins_manager.add_popular_coins()
        
        return {
            "message": "Popular coins initialized successfully",
            "status": "completed"
        }
        
    except Exception as e:
        logger.error(f"Error initializing popular coins: {e}")
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
    uvicorn.run(app, host="0.0.0.0", port=8004)
