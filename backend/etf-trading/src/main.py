"""
TigerEx ETF Trading Service
Advanced Exchange-Traded Fund trading platform with portfolio management
"""

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import asyncio
import logging
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
import os
from dataclasses import dataclass
import redis
import httpx
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import structlog
from decimal import Decimal

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
    title="TigerEx ETF Trading Service",
    description="Advanced Exchange-Traded Fund trading platform",
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
class ETFInfo(BaseModel):
    etf_id: str
    symbol: str
    name: str
    description: str
    category: str  # equity, bond, commodity, sector, etc.
    expense_ratio: Decimal
    aum: Decimal  # Assets Under Management
    inception_date: datetime
    benchmark_index: Optional[str]
    dividend_yield: Optional[Decimal]
    is_active: bool = True

class ETFHolding(BaseModel):
    etf_id: str
    asset_symbol: str
    asset_name: str
    weight: Decimal  # Percentage weight in ETF
    shares: int
    market_value: Decimal
    sector: Optional[str]
    country: Optional[str]

class ETFOrder(BaseModel):
    order_id: str
    user_id: str
    etf_symbol: str
    side: str  # BUY, SELL
    order_type: str  # MARKET, LIMIT
    quantity: int  # Number of ETF shares
    price: Optional[Decimal]
    status: str  # NEW, FILLED, CANCELED, REJECTED
    created_at: datetime
    filled_at: Optional[datetime]
    filled_price: Optional[Decimal]

class CreateETFRequest(BaseModel):
    symbol: str = Field(..., min_length=3, max_length=10)
    name: str = Field(..., min_length=1, max_length=200)
    description: str
    category: str
    expense_ratio: Decimal = Field(..., ge=0, le=5)  # 0-5%
    benchmark_index: Optional[str]
    holdings: List[Dict[str, Any]]  # Initial holdings

class PlaceETFOrderRequest(BaseModel):
    etf_symbol: str
    side: str = Field(..., regex="^(BUY|SELL)$")
    order_type: str = Field(..., regex="^(MARKET|LIMIT)$")
    quantity: int = Field(..., gt=0)
    price: Optional[Decimal] = Field(None, gt=0)

class ETFPortfolio(BaseModel):
    user_id: str
    etf_holdings: List[Dict[str, Any]]
    total_value: Decimal
    total_cost: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal
    dividend_income: Decimal

class ETFPerformance(BaseModel):
    etf_symbol: str
    nav: Decimal  # Net Asset Value
    market_price: Decimal
    premium_discount: Decimal
    daily_return: Decimal
    ytd_return: Decimal
    one_year_return: Decimal
    three_year_return: Optional[Decimal]
    five_year_return: Optional[Decimal]
    volatility: Decimal
    sharpe_ratio: Optional[Decimal]
    beta: Optional[Decimal]

@dataclass
class ETFTradingService:
    """Core ETF Trading Service"""
    
    def __init__(self):
        self.etfs: Dict[str, ETFInfo] = {}
        self.holdings: Dict[str, List[ETFHolding]] = {}
        self.load_etf_data()
    
    def load_etf_data(self):
        """Load ETF data and holdings"""
        # In production, this would load from database
        logger.info("Loading ETF data")
        
        # Sample ETFs
        sample_etfs = [
            {
                "etf_id": "SPY_ETF",
                "symbol": "SPY",
                "name": "SPDR S&P 500 ETF Trust",
                "description": "Tracks the S&P 500 Index",
                "category": "equity",
                "expense_ratio": Decimal("0.0945"),
                "aum": Decimal("400000000000"),  # $400B
                "inception_date": datetime(1993, 1, 22),
                "benchmark_index": "S&P 500",
                "dividend_yield": Decimal("1.3"),
                "is_active": True
            },
            {
                "etf_id": "QQQ_ETF", 
                "symbol": "QQQ",
                "name": "Invesco QQQ Trust",
                "description": "Tracks the NASDAQ-100 Index",
                "category": "equity",
                "expense_ratio": Decimal("0.20"),
                "aum": Decimal("200000000000"),  # $200B
                "inception_date": datetime(1999, 3, 10),
                "benchmark_index": "NASDAQ-100",
                "dividend_yield": Decimal("0.6"),
                "is_active": True
            },
            {
                "etf_id": "TLT_ETF",
                "symbol": "TLT", 
                "name": "iShares 20+ Year Treasury Bond ETF",
                "description": "Tracks long-term U.S. Treasury bonds",
                "category": "bond",
                "expense_ratio": Decimal("0.15"),
                "aum": Decimal("50000000000"),  # $50B
                "inception_date": datetime(2002, 7, 22),
                "benchmark_index": "ICE U.S. Treasury 20+ Year Bond Index",
                "dividend_yield": Decimal("2.8"),
                "is_active": True
            },
            {
                "etf_id": "GLD_ETF",
                "symbol": "GLD",
                "name": "SPDR Gold Shares",
                "description": "Tracks the price of gold bullion",
                "category": "commodity",
                "expense_ratio": Decimal("0.40"),
                "aum": Decimal("60000000000"),  # $60B
                "inception_date": datetime(2004, 11, 18),
                "benchmark_index": "Gold Spot Price",
                "dividend_yield": None,
                "is_active": True
            }
        ]
        
        for etf_data in sample_etfs:
            etf = ETFInfo(**etf_data)
            self.etfs[etf.symbol] = etf
    
    async def create_etf(self, etf_request: CreateETFRequest) -> ETFInfo:
        """Create a new ETF"""
        if etf_request.symbol in self.etfs:
            raise ValueError(f"ETF with symbol {etf_request.symbol} already exists")
        
        etf = ETFInfo(
            etf_id=f"{etf_request.symbol}_ETF",
            symbol=etf_request.symbol,
            name=etf_request.name,
            description=etf_request.description,
            category=etf_request.category,
            expense_ratio=etf_request.expense_ratio,
            aum=Decimal("0"),  # Start with 0 AUM
            inception_date=datetime.utcnow(),
            benchmark_index=etf_request.benchmark_index,
            dividend_yield=None,
            is_active=True
        )
        
        self.etfs[etf.symbol] = etf
        
        # Create initial holdings
        holdings = []
        for holding_data in etf_request.holdings:
            holding = ETFHolding(
                etf_id=etf.etf_id,
                asset_symbol=holding_data["symbol"],
                asset_name=holding_data["name"],
                weight=Decimal(str(holding_data["weight"])),
                shares=holding_data["shares"],
                market_value=Decimal(str(holding_data["market_value"])),
                sector=holding_data.get("sector"),
                country=holding_data.get("country")
            )
            holdings.append(holding)
        
        self.holdings[etf.symbol] = holdings
        
        logger.info(f"Created new ETF: {etf.symbol}")
        return etf
    
    async def get_etf_list(self, category: Optional[str] = None) -> List[ETFInfo]:
        """Get list of available ETFs"""
        etfs = list(self.etfs.values())
        
        if category:
            etfs = [etf for etf in etfs if etf.category == category]
        
        return [etf for etf in etfs if etf.is_active]
    
    async def get_etf_info(self, symbol: str) -> Optional[ETFInfo]:
        """Get detailed ETF information"""
        return self.etfs.get(symbol)
    
    async def get_etf_holdings(self, symbol: str) -> List[ETFHolding]:
        """Get ETF holdings breakdown"""
        return self.holdings.get(symbol, [])
    
    async def place_etf_order(self, user_id: str, order_request: PlaceETFOrderRequest) -> ETFOrder:
        """Place an ETF order"""
        if order_request.etf_symbol not in self.etfs:
            raise ValueError(f"ETF {order_request.etf_symbol} not found")
        
        etf = self.etfs[order_request.etf_symbol]
        if not etf.is_active:
            raise ValueError(f"ETF {order_request.etf_symbol} is not active")
        
        # Validate limit order has price
        if order_request.order_type == "LIMIT" and order_request.price is None:
            raise ValueError("Price required for limit orders")
        
        # Generate order ID
        import uuid
        order_id = str(uuid.uuid4())
        
        # Get current market price (simplified)
        current_price = await self.get_etf_nav(order_request.etf_symbol)
        
        # For market orders, use current price
        fill_price = current_price if order_request.order_type == "MARKET" else order_request.price
        
        order = ETFOrder(
            order_id=order_id,
            user_id=user_id,
            etf_symbol=order_request.etf_symbol,
            side=order_request.side,
            order_type=order_request.order_type,
            quantity=order_request.quantity,
            price=order_request.price,
            status="FILLED" if order_request.order_type == "MARKET" else "NEW",
            created_at=datetime.utcnow(),
            filled_at=datetime.utcnow() if order_request.order_type == "MARKET" else None,
            filled_price=fill_price if order_request.order_type == "MARKET" else None
        )
        
        # Store order (in production, save to database)
        redis_client.setex(
            f"etf_order:{order_id}",
            3600,  # 1 hour TTL
            json.dumps(order.dict(), default=str)
        )
        
        logger.info(f"Placed ETF order: {order_id} for {order_request.quantity} shares of {order_request.etf_symbol}")
        return order
    
    async def get_etf_nav(self, symbol: str) -> Decimal:
        """Calculate Net Asset Value for ETF"""
        holdings = self.holdings.get(symbol, [])
        if not holdings:
            return Decimal("100")  # Default NAV
        
        # Simplified NAV calculation
        # In production, this would fetch real-time prices for all holdings
        total_value = sum(holding.market_value for holding in holdings)
        
        # Assume 1M shares outstanding for simplicity
        shares_outstanding = Decimal("1000000")
        nav = total_value / shares_outstanding
        
        return nav
    
    async def get_etf_performance(self, symbol: str) -> ETFPerformance:
        """Get ETF performance metrics"""
        nav = await self.get_etf_nav(symbol)
        
        # Simplified performance calculation
        # In production, this would use historical data
        performance = ETFPerformance(
            etf_symbol=symbol,
            nav=nav,
            market_price=nav * Decimal("1.001"),  # Small premium/discount
            premium_discount=Decimal("0.1"),
            daily_return=Decimal("0.5"),
            ytd_return=Decimal("12.3"),
            one_year_return=Decimal("15.7"),
            three_year_return=Decimal("8.2"),
            five_year_return=Decimal("10.1"),
            volatility=Decimal("18.5"),
            sharpe_ratio=Decimal("0.85"),
            beta=Decimal("1.02")
        )
        
        return performance
    
    async def get_user_etf_portfolio(self, user_id: str) -> ETFPortfolio:
        """Get user's ETF portfolio"""
        # In production, this would query the database for user's ETF holdings
        # For now, return a sample portfolio
        
        sample_holdings = [
            {
                "etf_symbol": "SPY",
                "quantity": 100,
                "avg_cost": Decimal("420.50"),
                "current_price": Decimal("435.20"),
                "market_value": Decimal("43520.00"),
                "unrealized_pnl": Decimal("1470.00")
            },
            {
                "etf_symbol": "QQQ", 
                "quantity": 50,
                "avg_cost": Decimal("380.00"),
                "current_price": Decimal("395.75"),
                "market_value": Decimal("19787.50"),
                "unrealized_pnl": Decimal("787.50")
            }
        ]
        
        total_value = sum(Decimal(str(h["market_value"])) for h in sample_holdings)
        total_cost = sum(Decimal(str(h["avg_cost"])) * h["quantity"] for h in sample_holdings)
        unrealized_pnl = sum(Decimal(str(h["unrealized_pnl"])) for h in sample_holdings)
        
        portfolio = ETFPortfolio(
            user_id=user_id,
            etf_holdings=sample_holdings,
            total_value=total_value,
            total_cost=total_cost,
            unrealized_pnl=unrealized_pnl,
            realized_pnl=Decimal("0"),
            dividend_income=Decimal("125.50")
        )
        
        return portfolio
    
    async def rebalance_etf(self, symbol: str, new_holdings: List[Dict[str, Any]]) -> bool:
        """Rebalance ETF holdings"""
        if symbol not in self.etfs:
            raise ValueError(f"ETF {symbol} not found")
        
        # Validate weights sum to 100%
        total_weight = sum(Decimal(str(h["weight"])) for h in new_holdings)
        if abs(total_weight - Decimal("100")) > Decimal("0.01"):
            raise ValueError("Holdings weights must sum to 100%")
        
        # Update holdings
        holdings = []
        for holding_data in new_holdings:
            holding = ETFHolding(
                etf_id=self.etfs[symbol].etf_id,
                asset_symbol=holding_data["symbol"],
                asset_name=holding_data["name"],
                weight=Decimal(str(holding_data["weight"])),
                shares=holding_data["shares"],
                market_value=Decimal(str(holding_data["market_value"])),
                sector=holding_data.get("sector"),
                country=holding_data.get("country")
            )
            holdings.append(holding)
        
        self.holdings[symbol] = holdings
        
        logger.info(f"Rebalanced ETF {symbol} with {len(holdings)} holdings")
        return True

# Initialize ETF service
etf_service = ETFTradingService()

# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "etf-trading",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@app.get("/api/v1/etf/list")
async def get_etf_list(category: Optional[str] = None) -> List[ETFInfo]:
    """Get list of available ETFs"""
    try:
        etfs = await etf_service.get_etf_list(category)
        logger.info(f"Retrieved {len(etfs)} ETFs", category=category)
        return etfs
    except Exception as e:
        logger.error(f"Error retrieving ETF list: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve ETF list: {str(e)}")

@app.post("/api/v1/etf/create")
async def create_etf(etf_request: CreateETFRequest) -> ETFInfo:
    """Create a new ETF"""
    try:
        etf = await etf_service.create_etf(etf_request)
        logger.info(f"Created new ETF", symbol=etf.symbol, name=etf.name)
        return etf
    except ValueError as e:
        logger.error(f"Error creating ETF: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error creating ETF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create ETF: {str(e)}")

@app.get("/api/v1/etf/{symbol}")
async def get_etf_info(symbol: str) -> ETFInfo:
    """Get detailed ETF information"""
    try:
        etf = await etf_service.get_etf_info(symbol.upper())
        if not etf:
            raise HTTPException(status_code=404, detail=f"ETF {symbol} not found")
        return etf
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving ETF info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve ETF info: {str(e)}")

@app.get("/api/v1/etf/{symbol}/holdings")
async def get_etf_holdings(symbol: str) -> List[ETFHolding]:
    """Get ETF holdings breakdown"""
    try:
        holdings = await etf_service.get_etf_holdings(symbol.upper())
        logger.info(f"Retrieved {len(holdings)} holdings for ETF {symbol}")
        return holdings
    except Exception as e:
        logger.error(f"Error retrieving ETF holdings: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve ETF holdings: {str(e)}")

@app.get("/api/v1/etf/{symbol}/performance")
async def get_etf_performance(symbol: str) -> ETFPerformance:
    """Get ETF performance metrics"""
    try:
        performance = await etf_service.get_etf_performance(symbol.upper())
        return performance
    except Exception as e:
        logger.error(f"Error retrieving ETF performance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve ETF performance: {str(e)}")

@app.post("/api/v1/etf/order")
async def place_etf_order(order_request: PlaceETFOrderRequest) -> ETFOrder:
    """Place an ETF order"""
    try:
        # TODO: Extract user_id from JWT token
        user_id = "user123"
        
        order = await etf_service.place_etf_order(user_id, order_request)
        logger.info(f"Placed ETF order", 
                   order_id=order.order_id, 
                   symbol=order.etf_symbol,
                   side=order.side,
                   quantity=order.quantity)
        return order
    except ValueError as e:
        logger.error(f"Error placing ETF order: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error placing ETF order: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to place ETF order: {str(e)}")

@app.get("/api/v1/etf/portfolio")
async def get_user_etf_portfolio() -> ETFPortfolio:
    """Get user's ETF portfolio"""
    try:
        # TODO: Extract user_id from JWT token
        user_id = "user123"
        
        portfolio = await etf_service.get_user_etf_portfolio(user_id)
        logger.info(f"Retrieved ETF portfolio for user {user_id}")
        return portfolio
    except Exception as e:
        logger.error(f"Error retrieving ETF portfolio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve ETF portfolio: {str(e)}")

@app.put("/api/v1/etf/{symbol}/rebalance")
async def rebalance_etf(symbol: str, new_holdings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Rebalance ETF holdings"""
    try:
        success = await etf_service.rebalance_etf(symbol.upper(), new_holdings)
        if success:
            return {"message": f"ETF {symbol} rebalanced successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to rebalance ETF")
    except ValueError as e:
        logger.error(f"Error rebalancing ETF: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error rebalancing ETF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to rebalance ETF: {str(e)}")

@app.get("/api/v1/etf/categories")
async def get_etf_categories() -> List[str]:
    """Get available ETF categories"""
    categories = ["equity", "bond", "commodity", "sector", "international", "real_estate", "currency"]
    return categories

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8092)
