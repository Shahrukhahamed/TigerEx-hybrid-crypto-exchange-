"""
TigerEx Trading Pair Management Service
Comprehensive trading pair management for all trading types
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
import asyncio
import logging
from datetime import datetime, timedelta
import json
import os
from decimal import Decimal
import redis
import httpx
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import structlog

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Initialize FastAPI app
app = FastAPI(
    title="TigerEx Trading Pair Management Service",
    description="Comprehensive trading pair management for all trading types",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/tigerex")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Initialize connections
redis_client = redis.from_url(REDIS_URL)
engine = create_async_engine(DATABASE_URL)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Pydantic models
class TradingPairBase(BaseModel):
    symbol: str = Field(..., min_length=3, max_length=20)
    base_asset: str = Field(..., min_length=1, max_length=10)
    quote_asset: str = Field(..., min_length=1, max_length=10)
    status: str = Field(default="ACTIVE", regex="^(ACTIVE|INACTIVE|DELISTED)$")
    min_order_size: Decimal = Field(..., gt=0)
    max_order_size: Optional[Decimal] = Field(None, gt=0)
    min_price: Decimal = Field(..., gt=0)
    max_price: Optional[Decimal] = Field(None, gt=0)
    price_precision: int = Field(..., ge=0, le=8)
    quantity_precision: int = Field(..., ge=0, le=8)
    maker_fee: Decimal = Field(..., ge=0, le=1)  # 0-100%
    taker_fee: Decimal = Field(..., ge=0, le=1)  # 0-100%

class SpotTradingPair(TradingPairBase):
    is_spot_enabled: bool = True
    is_margin_enabled: bool = False
    margin_leverage_max: Optional[Decimal] = Field(None, gt=0, le=1000)

class FuturesTradingPair(TradingPairBase):
    is_futures_enabled: bool = True
    contract_type: str = Field(..., regex="^(PERPETUAL|QUARTERLY|MONTHLY)$")
    settlement_asset: str
    leverage_max: Decimal = Field(..., gt=0, le=1000)
    funding_interval: int = Field(default=8)  # hours
    maintenance_margin_rate: Decimal = Field(..., gt=0, le=1)
    initial_margin_rate: Decimal = Field(..., gt=0, le=1)

class OptionsTradingPair(TradingPairBase):
    is_options_enabled: bool = True
    underlying_asset: str
    option_type: str = Field(..., regex="^(CALL|PUT)$")
    strike_price: Decimal = Field(..., gt=0)
    expiry_date: datetime
    exercise_style: str = Field(..., regex="^(EUROPEAN|AMERICAN)$")
    contract_size: Decimal = Field(default=Decimal("1"))

class ETFTradingPair(TradingPairBase):
    is_etf_enabled: bool = True
    etf_type: str = Field(..., regex="^(EQUITY|BOND|COMMODITY|SECTOR|MIXED)$")
    expense_ratio: Decimal = Field(..., ge=0, le=0.05)  # 0-5%
    nav_calculation_frequency: str = Field(default="DAILY")
    creation_unit_size: int = Field(default=50000)

class MarginTradingPair(TradingPairBase):
    is_margin_enabled: bool = True
    max_leverage: Decimal = Field(..., gt=0, le=1000)
    maintenance_margin_rate: Decimal = Field(..., gt=0, le=1)
    initial_margin_rate: Decimal = Field(..., gt=0, le=1)
    liquidation_fee: Decimal = Field(..., ge=0, le=0.1)

class AlphaTradingPair(TradingPairBase):
    is_alpha_enabled: bool = True
    alpha_strategy_type: str = Field(..., regex="^(MOMENTUM|MEAN_REVERSION|ARBITRAGE|MARKET_MAKING)$")
    min_alpha_score: Decimal = Field(default=Decimal("0.1"))
    max_position_size: Decimal = Field(..., gt=0)
    rebalance_frequency: str = Field(default="DAILY")

class CreateTradingPairRequest(BaseModel):
    trading_type: str = Field(..., regex="^(SPOT|FUTURES|OPTIONS|ETF|MARGIN|ALPHA)$")
    pair_data: Dict[str, Any]

class UpdateTradingPairRequest(BaseModel):
    status: Optional[str] = Field(None, regex="^(ACTIVE|INACTIVE|DELISTED)$")
    min_order_size: Optional[Decimal] = Field(None, gt=0)
    max_order_size: Optional[Decimal] = Field(None, gt=0)
    min_price: Optional[Decimal] = Field(None, gt=0)
    max_price: Optional[Decimal] = Field(None, gt=0)
    maker_fee: Optional[Decimal] = Field(None, ge=0, le=1)
    taker_fee: Optional[Decimal] = Field(None, ge=0, le=1)
    additional_params: Optional[Dict[str, Any]] = None

class TradingPairResponse(BaseModel):
    id: int
    symbol: str
    base_asset: str
    quote_asset: str
    trading_type: str
    status: str
    min_order_size: Decimal
    max_order_size: Optional[Decimal]
    min_price: Decimal
    max_price: Optional[Decimal]
    price_precision: int
    quantity_precision: int
    maker_fee: Decimal
    taker_fee: Decimal
    created_at: datetime
    updated_at: datetime
    additional_params: Optional[Dict[str, Any]]

class TradingPairService:
    """Core Trading Pair Management Service"""
    
    def __init__(self):
        self.supported_types = ["SPOT", "FUTURES", "OPTIONS", "ETF", "MARGIN", "ALPHA"]
        self.pair_validators = {
            "SPOT": self._validate_spot_pair,
            "FUTURES": self._validate_futures_pair,
            "OPTIONS": self._validate_options_pair,
            "ETF": self._validate_etf_pair,
            "MARGIN": self._validate_margin_pair,
            "ALPHA": self._validate_alpha_pair,
        }
    
    async def create_trading_pair(self, request: CreateTradingPairRequest) -> TradingPairResponse:
        """Create a new trading pair"""
        if request.trading_type not in self.supported_types:
            raise ValueError(f"Unsupported trading type: {request.trading_type}")
        
        # Validate pair data
        validator = self.pair_validators[request.trading_type]
        validated_data = await validator(request.pair_data)
        
        # Check if pair already exists
        existing_pair = await self._get_pair_by_symbol(validated_data["symbol"])
        if existing_pair:
            raise ValueError(f"Trading pair {validated_data['symbol']} already exists")
        
        # Create pair in database (simplified - in production use proper ORM)
        pair_id = await self._insert_trading_pair(request.trading_type, validated_data)
        
        # Cache the pair
        await self._cache_trading_pair(pair_id, request.trading_type, validated_data)
        
        # Notify other services
        await self._notify_services_pair_created(request.trading_type, validated_data)
        
        response = TradingPairResponse(
            id=pair_id,
            symbol=validated_data["symbol"],
            base_asset=validated_data["base_asset"],
            quote_asset=validated_data["quote_asset"],
            trading_type=request.trading_type,
            status=validated_data.get("status", "ACTIVE"),
            min_order_size=validated_data["min_order_size"],
            max_order_size=validated_data.get("max_order_size"),
            min_price=validated_data["min_price"],
            max_price=validated_data.get("max_price"),
            price_precision=validated_data["price_precision"],
            quantity_precision=validated_data["quantity_precision"],
            maker_fee=validated_data["maker_fee"],
            taker_fee=validated_data["taker_fee"],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            additional_params=validated_data
        )
        
        logger.info(f"Created {request.trading_type} trading pair", symbol=validated_data["symbol"])
        return response
    
    async def get_trading_pairs(self, trading_type: Optional[str] = None, status: Optional[str] = None) -> List[TradingPairResponse]:
        """Get list of trading pairs"""
        # In production, this would query the database
        # For now, return cached pairs
        pairs = []
        
        # Get from cache or database
        cache_key = f"trading_pairs:{trading_type or 'all'}:{status or 'all'}"
        cached_pairs = redis_client.get(cache_key)
        
        if cached_pairs:
            pairs_data = json.loads(cached_pairs)
            pairs = [TradingPairResponse(**pair) for pair in pairs_data]
        else:
            # Query database and cache results
            pairs = await self._query_trading_pairs(trading_type, status)
            redis_client.setex(cache_key, 300, json.dumps([pair.dict() for pair in pairs], default=str))
        
        return pairs
    
    async def get_trading_pair(self, symbol: str) -> Optional[TradingPairResponse]:
        """Get specific trading pair"""
        pair = await self._get_pair_by_symbol(symbol)
        return pair
    
    async def update_trading_pair(self, symbol: str, request: UpdateTradingPairRequest) -> TradingPairResponse:
        """Update existing trading pair"""
        existing_pair = await self._get_pair_by_symbol(symbol)
        if not existing_pair:
            raise ValueError(f"Trading pair {symbol} not found")
        
        # Update pair data
        updated_pair = await self._update_pair_in_db(symbol, request)
        
        # Update cache
        await self._update_cached_pair(symbol, updated_pair)
        
        # Notify other services
        await self._notify_services_pair_updated(symbol, updated_pair)
        
        logger.info(f"Updated trading pair", symbol=symbol)
        return updated_pair
    
    async def delete_trading_pair(self, symbol: str) -> bool:
        """Delete (delist) trading pair"""
        existing_pair = await self._get_pair_by_symbol(symbol)
        if not existing_pair:
            raise ValueError(f"Trading pair {symbol} not found")
        
        # Soft delete - set status to DELISTED
        await self._update_pair_status(symbol, "DELISTED")
        
        # Remove from cache
        await self._remove_from_cache(symbol)
        
        # Notify other services
        await self._notify_services_pair_deleted(symbol)
        
        logger.info(f"Delisted trading pair", symbol=symbol)
        return True
    
    async def get_supported_assets(self) -> Dict[str, List[str]]:
        """Get list of supported assets for each trading type"""
        return {
            "SPOT": ["BTC", "ETH", "BNB", "ADA", "SOL", "MATIC", "AVAX", "DOT", "LINK", "UNI"],
            "FUTURES": ["BTC", "ETH", "BNB", "ADA", "SOL", "MATIC", "AVAX"],
            "OPTIONS": ["BTC", "ETH", "BNB"],
            "ETF": ["SPY", "QQQ", "TLT", "GLD", "VTI", "IWM"],
            "MARGIN": ["BTC", "ETH", "BNB", "ADA", "SOL"],
            "ALPHA": ["BTC", "ETH", "BNB", "ADA"]
        }
    
    # Validation methods for each trading type
    async def _validate_spot_pair(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate spot trading pair data"""
        pair = SpotTradingPair(**data)
        return pair.dict()
    
    async def _validate_futures_pair(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate futures trading pair data"""
        pair = FuturesTradingPair(**data)
        return pair.dict()
    
    async def _validate_options_pair(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate options trading pair data"""
        pair = OptionsTradingPair(**data)
        return pair.dict()
    
    async def _validate_etf_pair(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate ETF trading pair data"""
        pair = ETFTradingPair(**data)
        return pair.dict()
    
    async def _validate_margin_pair(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate margin trading pair data"""
        pair = MarginTradingPair(**data)
        return pair.dict()
    
    async def _validate_alpha_pair(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate alpha trading pair data"""
        pair = AlphaTradingPair(**data)
        return pair.dict()
    
    # Database operations (simplified)
    async def _get_pair_by_symbol(self, symbol: str) -> Optional[TradingPairResponse]:
        """Get trading pair by symbol"""
        # Check cache first
        cached_pair = redis_client.get(f"trading_pair:{symbol}")
        if cached_pair:
            return TradingPairResponse(**json.loads(cached_pair))
        
        # In production, query database here
        return None
    
    async def _insert_trading_pair(self, trading_type: str, data: Dict[str, Any]) -> int:
        """Insert new trading pair into database"""
        # In production, use proper database insertion
        pair_id = hash(data["symbol"]) % 1000000  # Simple ID generation
        return pair_id
    
    async def _query_trading_pairs(self, trading_type: Optional[str], status: Optional[str]) -> List[TradingPairResponse]:
        """Query trading pairs from database"""
        # In production, implement proper database query
        return []
    
    async def _update_pair_in_db(self, symbol: str, request: UpdateTradingPairRequest) -> TradingPairResponse:
        """Update trading pair in database"""
        # In production, implement proper database update
        existing_pair = await self._get_pair_by_symbol(symbol)
        if existing_pair:
            # Update fields
            if request.status:
                existing_pair.status = request.status
            if request.min_order_size:
                existing_pair.min_order_size = request.min_order_size
            # ... update other fields
            existing_pair.updated_at = datetime.utcnow()
        
        return existing_pair
    
    async def _update_pair_status(self, symbol: str, status: str) -> bool:
        """Update trading pair status"""
        # In production, update database
        return True
    
    # Cache operations
    async def _cache_trading_pair(self, pair_id: int, trading_type: str, data: Dict[str, Any]):
        """Cache trading pair data"""
        cache_key = f"trading_pair:{data['symbol']}"
        redis_client.setex(cache_key, 3600, json.dumps(data, default=str))
    
    async def _update_cached_pair(self, symbol: str, pair: TradingPairResponse):
        """Update cached trading pair"""
        cache_key = f"trading_pair:{symbol}"
        redis_client.setex(cache_key, 3600, json.dumps(pair.dict(), default=str))
    
    async def _remove_from_cache(self, symbol: str):
        """Remove trading pair from cache"""
        redis_client.delete(f"trading_pair:{symbol}")
    
    # Service notifications
    async def _notify_services_pair_created(self, trading_type: str, data: Dict[str, Any]):
        """Notify other services about new trading pair"""
        notification = {
            "event": "trading_pair_created",
            "trading_type": trading_type,
            "symbol": data["symbol"],
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Publish to Redis pub/sub
        redis_client.publish("trading_pair_events", json.dumps(notification, default=str))
        
        # Send HTTP notifications to services
        services = {
            "SPOT": "http://spot-trading:8091",
            "FUTURES": "http://futures-trading:8094",
            "OPTIONS": "http://options-trading:8095",
            "ETF": "http://etf-trading:8092",
            "MARGIN": "http://margin-trading:8096",
            "ALPHA": "http://alpha-trading:8097"
        }
        
        if trading_type in services:
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(f"{services[trading_type]}/api/v1/pairs/created", json=notification)
            except Exception as e:
                logger.error(f"Failed to notify {trading_type} service: {str(e)}")
    
    async def _notify_services_pair_updated(self, symbol: str, pair: TradingPairResponse):
        """Notify other services about updated trading pair"""
        notification = {
            "event": "trading_pair_updated",
            "symbol": symbol,
            "data": pair.dict(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        redis_client.publish("trading_pair_events", json.dumps(notification, default=str))
    
    async def _notify_services_pair_deleted(self, symbol: str):
        """Notify other services about deleted trading pair"""
        notification = {
            "event": "trading_pair_deleted",
            "symbol": symbol,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        redis_client.publish("trading_pair_events", json.dumps(notification, default=str))

# Initialize service
trading_pair_service = TradingPairService()

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "trading-pair-management",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.post("/api/v1/trading-pairs")
async def create_trading_pair(request: CreateTradingPairRequest) -> TradingPairResponse:
    """Create a new trading pair"""
    try:
        pair = await trading_pair_service.create_trading_pair(request)
        return pair
    except ValueError as e:
        logger.error(f"Error creating trading pair: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating trading pair: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create trading pair: {str(e)}")

@app.get("/api/v1/trading-pairs")
async def get_trading_pairs(
    trading_type: Optional[str] = None,
    status: Optional[str] = None
) -> List[TradingPairResponse]:
    """Get list of trading pairs"""
    try:
        pairs = await trading_pair_service.get_trading_pairs(trading_type, status)
        logger.info(f"Retrieved {len(pairs)} trading pairs", trading_type=trading_type, status=status)
        return pairs
    except Exception as e:
        logger.error(f"Error retrieving trading pairs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve trading pairs: {str(e)}")

@app.get("/api/v1/trading-pairs/{symbol}")
async def get_trading_pair(symbol: str) -> TradingPairResponse:
    """Get specific trading pair"""
    try:
        pair = await trading_pair_service.get_trading_pair(symbol.upper())
        if not pair:
            raise HTTPException(status_code=404, detail=f"Trading pair {symbol} not found")
        return pair
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving trading pair: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve trading pair: {str(e)}")

@app.put("/api/v1/trading-pairs/{symbol}")
async def update_trading_pair(symbol: str, request: UpdateTradingPairRequest) -> TradingPairResponse:
    """Update existing trading pair"""
    try:
        pair = await trading_pair_service.update_trading_pair(symbol.upper(), request)
        return pair
    except ValueError as e:
        logger.error(f"Error updating trading pair: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error updating trading pair: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update trading pair: {str(e)}")

@app.delete("/api/v1/trading-pairs/{symbol}")
async def delete_trading_pair(symbol: str) -> Dict[str, Any]:
    """Delete (delist) trading pair"""
    try:
        success = await trading_pair_service.delete_trading_pair(symbol.upper())
        if success:
            return {"message": f"Trading pair {symbol} delisted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete trading pair")
    except ValueError as e:
        logger.error(f"Error deleting trading pair: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error deleting trading pair: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete trading pair: {str(e)}")

@app.get("/api/v1/supported-assets")
async def get_supported_assets() -> Dict[str, List[str]]:
    """Get list of supported assets for each trading type"""
    try:
        assets = await trading_pair_service.get_supported_assets()
        return assets
    except Exception as e:
        logger.error(f"Error retrieving supported assets: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve supported assets: {str(e)}")

@app.get("/api/v1/trading-types")
async def get_trading_types() -> List[str]:
    """Get list of supported trading types"""
    return trading_pair_service.supported_types

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8093)
