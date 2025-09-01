"""
TigerEx NFT Marketplace
Complete NFT trading, creation, and marketplace platform
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
import hashlib
import secrets

import asyncpg
import aioredis
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, DECIMAL, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
import boto3
from PIL import Image
import requests

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="TigerEx NFT Marketplace",
    description="Complete NFT trading, creation, and marketplace platform",
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
    AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET", "tigerex-nft-assets")
    MARKETPLACE_FEE_PERCENTAGE = Decimal("2.5")

config = Config()

# Database setup
engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

security = HTTPBearer()

# Enums
class NFTStatus(str, Enum):
    DRAFT = "draft"
    MINTING = "minting"
    MINTED = "minted"
    LISTED = "listed"
    SOLD = "sold"

class ListingType(str, Enum):
    FIXED_PRICE = "fixed_price"
    AUCTION = "auction"
    DUTCH_AUCTION = "dutch_auction"

class Blockchain(str, Enum):
    ETHEREUM = "ethereum"
    POLYGON = "polygon"
    BSC = "bsc"

# Database Models
class NFTCollection(Base):
    __tablename__ = "nft_collections"
    
    id = Column(Integer, primary_key=True, index=True)
    collection_id = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    symbol = Column(String(20), nullable=False)
    description = Column(Text)
    creator_id = Column(String(50), nullable=False, index=True)
    creator_address = Column(String(42), nullable=False)
    blockchain = Column(SQLEnum(Blockchain), nullable=False)
    contract_address = Column(String(42))
    image_url = Column(String(500))
    royalty_percentage = Column(DECIMAL(5, 2), default=0)
    is_verified = Column(Boolean, default=False)
    total_supply = Column(Integer, default=0)
    floor_price = Column(DECIMAL(20, 8))
    total_volume = Column(DECIMAL(20, 8), default=0)
    created_at = Column(DateTime, default=func.now())
    
    nfts = relationship("NFT", back_populates="collection")

class NFT(Base):
    __tablename__ = "nfts"
    
    id = Column(Integer, primary_key=True, index=True)
    nft_id = Column(String(50), unique=True, nullable=False, index=True)
    token_id = Column(String(50), nullable=False)
    collection_id = Column(Integer, ForeignKey("nft_collections.id"), nullable=False)
    collection = relationship("NFTCollection", back_populates="nfts")
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    image_url = Column(String(500), nullable=False)
    metadata_url = Column(String(500))
    attributes = Column(JSON)
    
    current_owner = Column(String(42), nullable=False, index=True)
    creator = Column(String(42), nullable=False, index=True)
    blockchain = Column(SQLEnum(Blockchain), nullable=False)
    
    status = Column(SQLEnum(NFTStatus), default=NFTStatus.DRAFT)
    mint_transaction_hash = Column(String(66))
    
    rarity_rank = Column(Integer)
    rarity_score = Column(DECIMAL(10, 4))
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    
    created_at = Column(DateTime, default=func.now())
    
    listings = relationship("NFTListing", back_populates="nft")

class NFTListing(Base):
    __tablename__ = "nft_listings"
    
    id = Column(Integer, primary_key=True, index=True)
    listing_id = Column(String(50), unique=True, nullable=False, index=True)
    nft_id = Column(Integer, ForeignKey("nfts.id"), nullable=False)
    nft = relationship("NFT", back_populates="listings")
    
    seller_address = Column(String(42), nullable=False, index=True)
    listing_type = Column(SQLEnum(ListingType), nullable=False)
    price = Column(DECIMAL(20, 8), nullable=False)
    currency = Column(String(10), nullable=False)
    
    status = Column(String(20), default="active")
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())

# Pydantic Models
class NFTCollectionCreate(BaseModel):
    name: str
    symbol: str
    description: Optional[str] = None
    blockchain: Blockchain
    royalty_percentage: Optional[Decimal] = Decimal("0")

class NFTCreate(BaseModel):
    collection_id: str
    name: str
    description: Optional[str] = None
    attributes: Optional[List[Dict[str, Any]]] = []

class NFTListingCreate(BaseModel):
    nft_id: str
    listing_type: ListingType
    price: Decimal
    currency: str = "ETH"

# Dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return {"user_id": "user_123", "address": "0x742d35Cc6634C0532925a3b8D"}

# NFT Marketplace Manager
class NFTMarketplaceManager:
    def __init__(self):
        self.redis_client = None
        self.s3_client = None
        
    async def initialize(self):
        self.redis_client = await aioredis.from_url(config.REDIS_URL)
        if os.getenv("AWS_ACCESS_KEY_ID"):
            self.s3_client = boto3.client('s3')
    
    async def create_collection(self, collection_data: NFTCollectionCreate, creator: Dict[str, Any], db: Session):
        collection_id = f"COL_{secrets.token_hex(8).upper()}"
        
        collection = NFTCollection(
            collection_id=collection_id,
            name=collection_data.name,
            symbol=collection_data.symbol,
            description=collection_data.description,
            creator_id=creator["user_id"],
            creator_address=creator["address"],
            blockchain=collection_data.blockchain,
            royalty_percentage=collection_data.royalty_percentage
        )
        
        db.add(collection)
        db.commit()
        db.refresh(collection)
        return collection
    
    async def create_nft(self, nft_data: NFTCreate, creator: Dict[str, Any], db: Session):
        collection = db.query(NFTCollection).filter(
            NFTCollection.collection_id == nft_data.collection_id,
            NFTCollection.creator_address == creator["address"]
        ).first()
        
        if not collection:
            raise HTTPException(status_code=404, detail="Collection not found")
        
        token_id = str(collection.total_supply + 1)
        nft_id = f"NFT_{collection.collection_id}_{token_id}"
        
        nft = NFT(
            nft_id=nft_id,
            token_id=token_id,
            collection_id=collection.id,
            name=nft_data.name,
            description=nft_data.description,
            image_url="",
            attributes=nft_data.attributes,
            current_owner=creator["address"],
            creator=creator["address"],
            blockchain=collection.blockchain
        )
        
        db.add(nft)
        collection.total_supply += 1
        db.commit()
        db.refresh(nft)
        return nft

marketplace_manager = NFTMarketplaceManager()

@app.on_event("startup")
async def startup_event():
    await marketplace_manager.initialize()

# API Endpoints
@app.post("/api/v1/collections")
async def create_collection(
    collection_data: NFTCollectionCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    collection = await marketplace_manager.create_collection(collection_data, current_user, db)
    return {
        "collection_id": collection.collection_id,
        "name": collection.name,
        "symbol": collection.symbol,
        "blockchain": collection.blockchain,
        "status": "created"
    }

@app.get("/api/v1/collections")
async def get_collections(
    blockchain: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(NFTCollection)
    if blockchain:
        query = query.filter(NFTCollection.blockchain == blockchain)
    
    collections = query.offset(offset).limit(limit).all()
    
    return {
        "collections": [
            {
                "collection_id": col.collection_id,
                "name": col.name,
                "symbol": col.symbol,
                "description": col.description,
                "blockchain": col.blockchain,
                "creator_address": col.creator_address,
                "image_url": col.image_url,
                "is_verified": col.is_verified,
                "floor_price": str(col.floor_price) if col.floor_price else None,
                "total_volume": str(col.total_volume),
                "total_supply": col.total_supply,
                "created_at": col.created_at.isoformat()
            }
            for col in collections
        ]
    }

@app.post("/api/v1/nfts/upload-image")
async def upload_nft_image(
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large")
    
    # Mock upload - in production would upload to S3/IPFS
    image_url = f"https://example.com/images/{uuid.uuid4()}.jpg"
    
    return {
        "image_url": image_url,
        "filename": file.filename,
        "size": len(content)
    }

@app.post("/api/v1/nfts")
async def create_nft(
    nft_data: NFTCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    nft = await marketplace_manager.create_nft(nft_data, current_user, db)
    return {
        "nft_id": nft.nft_id,
        "token_id": nft.token_id,
        "collection_id": nft.collection.collection_id,
        "status": "created"
    }

@app.post("/api/v1/nfts/{nft_id}/mint")
async def mint_nft(
    nft_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    nft = db.query(NFT).filter(
        NFT.nft_id == nft_id,
        NFT.creator == current_user["address"]
    ).first()
    
    if not nft:
        raise HTTPException(status_code=404, detail="NFT not found")
    
    if nft.status != NFTStatus.DRAFT:
        raise HTTPException(status_code=400, detail="NFT already minted")
    
    # Mock minting process
    nft.status = NFTStatus.MINTED
    nft.mint_transaction_hash = f"0x{secrets.token_hex(32)}"
    db.commit()
    
    return {
        "nft_id": nft_id,
        "status": "minted",
        "transaction_hash": nft.mint_transaction_hash
    }

@app.get("/api/v1/nfts")
async def get_nfts(
    collection_id: Optional[str] = None,
    owner: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(NFT)
    
    if collection_id:
        collection = db.query(NFTCollection).filter(
            NFTCollection.collection_id == collection_id
        ).first()
        if collection:
            query = query.filter(NFT.collection_id == collection.id)
    
    if owner:
        query = query.filter(NFT.current_owner == owner)
    
    if status:
        query = query.filter(NFT.status == status)
    
    nfts = query.offset(offset).limit(limit).all()
    
    return {
        "nfts": [
            {
                "nft_id": nft.nft_id,
                "token_id": nft.token_id,
                "name": nft.name,
                "description": nft.description,
                "image_url": nft.image_url,
                "attributes": nft.attributes,
                "current_owner": nft.current_owner,
                "creator": nft.creator,
                "blockchain": nft.blockchain,
                "status": nft.status,
                "rarity_rank": nft.rarity_rank,
                "view_count": nft.view_count,
                "like_count": nft.like_count,
                "created_at": nft.created_at.isoformat()
            }
            for nft in nfts
        ]
    }

@app.post("/api/v1/listings")
async def create_listing(
    listing_data: NFTListingCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    nft = db.query(NFT).filter(
        NFT.nft_id == listing_data.nft_id,
        NFT.current_owner == current_user["address"],
        NFT.status == NFTStatus.MINTED
    ).first()
    
    if not nft:
        raise HTTPException(status_code=404, detail="NFT not found or not owned")
    
    listing_id = f"LIST_{secrets.token_hex(8).upper()}"
    
    listing = NFTListing(
        listing_id=listing_id,
        nft_id=nft.id,
        seller_address=current_user["address"],
        listing_type=listing_data.listing_type,
        price=listing_data.price,
        currency=listing_data.currency
    )
    
    db.add(listing)
    nft.status = NFTStatus.LISTED
    db.commit()
    
    return {
        "listing_id": listing.listing_id,
        "nft_id": nft.nft_id,
        "listing_type": listing.listing_type,
        "price": str(listing.price),
        "currency": listing.currency,
        "status": "active"
    }

@app.get("/api/v1/listings")
async def get_listings(
    collection_id: Optional[str] = None,
    seller: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(NFTListing).join(NFT)
    
    if collection_id:
        collection = db.query(NFTCollection).filter(
            NFTCollection.collection_id == collection_id
        ).first()
        if collection:
            query = query.filter(NFT.collection_id == collection.id)
    
    if seller:
        query = query.filter(NFTListing.seller_address == seller)
    
    listings = query.offset(offset).limit(limit).all()
    
    return {
        "listings": [
            {
                "listing_id": listing.listing_id,
                "nft": {
                    "nft_id": listing.nft.nft_id,
                    "name": listing.nft.name,
                    "image_url": listing.nft.image_url
                },
                "seller_address": listing.seller_address,
                "listing_type": listing.listing_type,
                "price": str(listing.price),
                "currency": listing.currency,
                "status": listing.status,
                "created_at": listing.created_at.isoformat()
            }
            for listing in listings
        ]
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "nft-marketplace"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
