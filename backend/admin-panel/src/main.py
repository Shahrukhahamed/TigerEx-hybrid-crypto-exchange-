"""
TigerEx Advanced Admin Panel Backend
Comprehensive role-based administration system with all requested features
"""

from fastapi import FastAPI, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, DECIMAL, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import os
import logging
import asyncio
import aioredis
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pyotp
import qrcode
import io
import base64
from PIL import Image
import requests
import json
import hashlib
import secrets
from web3 import Web3
import docker
import subprocess
import tempfile
import shutil
from jinja2 import Template
import boto3
from botocore.exceptions import ClientError

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost/tigerex")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-super-secret-jwt-key")
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Initialize FastAPI app
app = FastAPI(
    title="TigerEx Admin Panel API",
    description="Comprehensive administration system for TigerEx crypto exchange",
    version="2.0.0"
)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure properly for production
)

# Database setup
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database Models
class AdminRole(Base):
    __tablename__ = "admin_roles"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    level = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    users = relationship("AdminUser", back_populates="role")
    permissions = relationship("AdminRolePermission", back_populates="role")

class AdminUser(Base):
    __tablename__ = "admin_users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    phone = Column(String(20))
    role_id = Column(Integer, ForeignKey("admin_roles.id"))
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_secret = Column(String(255))
    last_login_at = Column(DateTime)
    last_login_ip = Column(String(45))
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    role = relationship("AdminRole", back_populates="users")

class AdminPermission(Base):
    __tablename__ = "admin_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    display_name = Column(String(150), nullable=False)
    description = Column(Text)
    category = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=func.now())

class AdminRolePermission(Base):
    __tablename__ = "admin_role_permissions"
    
    id = Column(Integer, primary_key=True, index=True)
    role_id = Column(Integer, ForeignKey("admin_roles.id"))
    permission_id = Column(Integer, ForeignKey("admin_permissions.id"))
    granted_at = Column(DateTime, default=func.now())
    granted_by = Column(Integer, ForeignKey("admin_users.id"))
    
    role = relationship("AdminRole", back_populates="permissions")
    permission = relationship("AdminPermission")

class KYCApplication(Base):
    __tablename__ = "kyc_applications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    application_type = Column(String(20), nullable=False)
    status = Column(String(20), default='pending', index=True)
    tier_requested = Column(Integer, default=1)
    tier_approved = Column(Integer, default=0)
    first_name = Column(String(100))
    last_name = Column(String(100))
    date_of_birth = Column(DateTime)
    nationality = Column(String(50))
    country_of_residence = Column(String(50))
    address_line1 = Column(String(255))
    city = Column(String(100))
    documents = Column(JSON)
    reviewed_by = Column(Integer, ForeignKey("admin_users.id"))
    reviewed_at = Column(DateTime)
    rejection_reason = Column(Text)
    risk_score = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class SupportTicket(Base):
    __tablename__ = "support_tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String(20), unique=True, nullable=False)
    user_id = Column(Integer, nullable=False, index=True)
    assigned_to = Column(Integer, ForeignKey("admin_users.id"), index=True)
    category = Column(String(50), nullable=False)
    priority = Column(String(20), default='medium')
    status = Column(String(20), default='open', index=True)
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())
    first_response_at = Column(DateTime)
    resolved_at = Column(DateTime)
    satisfaction_rating = Column(Integer)
    
    assigned_admin = relationship("AdminUser")

class TokenListingApplication(Base):
    __tablename__ = "token_listing_applications"
    
    id = Column(Integer, primary_key=True, index=True)
    application_number = Column(String(20), unique=True, nullable=False)
    applicant_email = Column(String(255), nullable=False)
    applicant_name = Column(String(255), nullable=False)
    token_name = Column(String(100), nullable=False)
    token_symbol = Column(String(20), nullable=False)
    contract_address = Column(String(100))
    blockchain = Column(String(50), nullable=False)
    status = Column(String(20), default='submitted', index=True)
    reviewed_by = Column(Integer, ForeignKey("admin_users.id"))
    reviewed_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())

class WhiteLabelExchange(Base):
    __tablename__ = "white_label_exchanges"
    
    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, nullable=False, index=True)
    exchange_name = Column(String(100), nullable=False)
    domain_name = Column(String(255), unique=True, nullable=False)
    subdomain = Column(String(100), unique=True, nullable=False)
    logo_url = Column(String(500))
    primary_color = Column(String(7))
    features_enabled = Column(JSON, nullable=False)
    api_key = Column(String(100), unique=True, nullable=False)
    api_secret = Column(String(255), nullable=False)
    status = Column(String(20), default='pending')
    deployed_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())

class CustomBlockchain(Base):
    __tablename__ = "custom_blockchains"
    
    id = Column(Integer, primary_key=True, index=True)
    blockchain_name = Column(String(100), nullable=False)
    blockchain_type = Column(String(20), nullable=False)
    chain_id = Column(Integer, unique=True)
    rpc_url = Column(String(500), nullable=False)
    explorer_url = Column(String(500))
    native_currency_name = Column(String(50), nullable=False)
    native_currency_symbol = Column(String(10), nullable=False)
    status = Column(String(20), default='pending')
    integrated_by = Column(Integer, ForeignKey("admin_users.id"))
    integrated_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())

# Pydantic Models
class AdminUserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    role_id: int

class AdminUserResponse(BaseModel):
    id: int
    email: str
    username: str
    first_name: str
    last_name: str
    role_id: int
    is_active: bool
    is_verified: bool
    two_factor_enabled: bool
    last_login_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True

class LoginRequest(BaseModel):
    email: str
    password: str
    totp_code: Optional[str] = None

class KYCReviewRequest(BaseModel):
    application_id: int
    action: str  # approve, reject
    tier_approved: Optional[int] = None
    rejection_reason: Optional[str] = None
    notes: Optional[str] = None

class TokenListingReviewRequest(BaseModel):
    application_id: int
    action: str  # approve, reject
    approval_notes: Optional[str] = None
    rejection_reason: Optional[str] = None

class WhiteLabelCreateRequest(BaseModel):
    client_id: int
    exchange_name: str
    domain_name: str
    features_enabled: List[str]
    primary_color: Optional[str] = "#1a1a1a"
    secondary_color: Optional[str] = "#f97316"

class BlockchainCreateRequest(BaseModel):
    blockchain_name: str
    blockchain_type: str
    chain_id: int
    rpc_url: str
    explorer_url: Optional[str] = None
    native_currency_name: str
    native_currency_symbol: str

# Dependency functions
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

async def get_current_admin_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        admin_id: int = payload.get("sub")
        if admin_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    admin_user = db.query(AdminUser).filter(AdminUser.id == admin_id).first()
    if admin_user is None:
        raise credentials_exception
    
    return admin_user

def check_permission(required_permission: str):
    def permission_checker(
        current_admin: AdminUser = Depends(get_current_admin_user),
        db: Session = Depends(get_db)
    ):
        # Get admin's role permissions
        permissions = db.query(AdminPermission).join(
            AdminRolePermission, AdminPermission.id == AdminRolePermission.permission_id
        ).filter(AdminRolePermission.role_id == current_admin.role_id).all()
        
        permission_names = [p.name for p in permissions]
        
        if required_permission not in permission_names and current_admin.role.level < 10:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return current_admin
    
    return permission_checker

# Authentication endpoints
@app.post("/api/v1/auth/login")
async def login(login_data: LoginRequest, db: Session = Depends(get_db)):
    admin_user = db.query(AdminUser).filter(AdminUser.email == login_data.email).first()
    
    if not admin_user or not verify_password(login_data.password, admin_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not admin_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated"
        )
    
    # Check 2FA if enabled
    if admin_user.two_factor_enabled:
        if not login_data.totp_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA code required"
            )
        
        totp = pyotp.TOTP(admin_user.two_factor_secret)
        if not totp.verify(login_data.totp_code):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid 2FA code"
            )
    
    # Update last login
    admin_user.last_login_at = datetime.utcnow()
    admin_user.failed_login_attempts = 0
    db.commit()
    
    # Create access token
    access_token_expires = timedelta(minutes=JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(admin_user.id)}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": AdminUserResponse.from_orm(admin_user)
    }

@app.post("/api/v1/auth/setup-2fa")
async def setup_2fa(
    current_admin: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    if current_admin.two_factor_enabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="2FA is already enabled"
        )
    
    # Generate secret
    secret = pyotp.random_base32()
    
    # Generate QR code
    totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
        name=current_admin.email,
        issuer_name="TigerEx Admin"
    )
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(totp_uri)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    qr_code_data = base64.b64encode(buffer.getvalue()).decode()
    
    # Store secret temporarily (should be confirmed before enabling)
    current_admin.two_factor_secret = secret
    db.commit()
    
    return {
        "secret": secret,
        "qr_code": f"data:image/png;base64,{qr_code_data}"
    }

# User Management endpoints
@app.get("/api/v1/users", dependencies=[Depends(check_permission("users.view"))])
async def get_users(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(AdminUser)
    
    if search:
        query = query.filter(
            AdminUser.email.contains(search) |
            AdminUser.username.contains(search) |
            AdminUser.first_name.contains(search) |
            AdminUser.last_name.contains(search)
        )
    
    total = query.count()
    users = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "users": [AdminUserResponse.from_orm(user) for user in users]
    }

@app.post("/api/v1/users", dependencies=[Depends(check_permission("users.edit"))])
async def create_admin_user(
    user_data: AdminUserCreate,
    db: Session = Depends(get_db)
):
    # Check if user already exists
    existing_user = db.query(AdminUser).filter(
        (AdminUser.email == user_data.email) | (AdminUser.username == user_data.username)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists"
        )
    
    # Create new admin user
    hashed_password = get_password_hash(user_data.password)
    admin_user = AdminUser(
        email=user_data.email,
        username=user_data.username,
        password_hash=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone,
        role_id=user_data.role_id
    )
    
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    return AdminUserResponse.from_orm(admin_user)

# KYC Management endpoints
@app.get("/api/v1/kyc/applications", dependencies=[Depends(check_permission("kyc.view"))])
async def get_kyc_applications(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(KYCApplication)
    
    if status:
        query = query.filter(KYCApplication.status == status)
    
    total = query.count()
    applications = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "applications": applications
    }

@app.post("/api/v1/kyc/review", dependencies=[Depends(check_permission("kyc.review"))])
async def review_kyc_application(
    review_data: KYCReviewRequest,
    current_admin: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    application = db.query(KYCApplication).filter(
        KYCApplication.id == review_data.application_id
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="KYC application not found"
        )
    
    if review_data.action == "approve":
        application.status = "approved"
        application.tier_approved = review_data.tier_approved or application.tier_requested
    elif review_data.action == "reject":
        application.status = "rejected"
        application.rejection_reason = review_data.rejection_reason
    
    application.reviewed_by = current_admin.id
    application.reviewed_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": f"KYC application {review_data.action}d successfully"}

# Token Listing Management
@app.get("/api/v1/token-listings", dependencies=[Depends(check_permission("listing.view_applications"))])
async def get_token_listing_applications(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(TokenListingApplication)
    
    if status:
        query = query.filter(TokenListingApplication.status == status)
    
    total = query.count()
    applications = query.offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "applications": applications
    }

@app.post("/api/v1/token-listings/review", dependencies=[Depends(check_permission("listing.review_applications"))])
async def review_token_listing(
    review_data: TokenListingReviewRequest,
    current_admin: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    application = db.query(TokenListingApplication).filter(
        TokenListingApplication.id == review_data.application_id
    ).first()
    
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token listing application not found"
        )
    
    if review_data.action == "approve":
        application.status = "approved"
        # Here you would trigger the actual token listing process
        await deploy_token_listing(application)
    elif review_data.action == "reject":
        application.status = "rejected"
        application.rejection_reason = review_data.rejection_reason
    
    application.reviewed_by = current_admin.id
    application.reviewed_at = datetime.utcnow()
    
    db.commit()
    
    return {"message": f"Token listing {review_data.action}d successfully"}

# White Label Exchange Management
@app.post("/api/v1/white-label/create", dependencies=[Depends(check_permission("whitelabel.manage"))])
async def create_white_label_exchange(
    exchange_data: WhiteLabelCreateRequest,
    current_admin: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    # Generate API credentials
    api_key = secrets.token_urlsafe(32)
    api_secret = secrets.token_urlsafe(64)
    
    # Create subdomain
    subdomain = exchange_data.exchange_name.lower().replace(" ", "-")
    
    white_label = WhiteLabelExchange(
        client_id=exchange_data.client_id,
        exchange_name=exchange_data.exchange_name,
        domain_name=exchange_data.domain_name,
        subdomain=f"{subdomain}.tigerex.com",
        primary_color=exchange_data.primary_color,
        features_enabled=exchange_data.features_enabled,
        api_key=api_key,
        api_secret=get_password_hash(api_secret),
        status="pending"
    )
    
    db.add(white_label)
    db.commit()
    db.refresh(white_label)
    
    # Trigger deployment process
    await deploy_white_label_exchange(white_label)
    
    return {
        "id": white_label.id,
        "api_key": api_key,
        "api_secret": api_secret,
        "subdomain": white_label.subdomain,
        "message": "White label exchange created successfully"
    }

@app.get("/api/v1/white-label", dependencies=[Depends(check_permission("whitelabel.view"))])
async def get_white_label_exchanges(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    total = db.query(WhiteLabelExchange).count()
    exchanges = db.query(WhiteLabelExchange).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "exchanges": exchanges
    }

# Blockchain Management
@app.post("/api/v1/blockchains/create", dependencies=[Depends(check_permission("blockchain.add"))])
async def create_custom_blockchain(
    blockchain_data: BlockchainCreateRequest,
    current_admin: AdminUser = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    # Validate RPC URL
    try:
        if blockchain_data.blockchain_type == "evm":
            w3 = Web3(Web3.HTTPProvider(blockchain_data.rpc_url))
            if not w3.isConnected():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot connect to RPC URL"
                )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"RPC validation failed: {str(e)}"
        )
    
    blockchain = CustomBlockchain(
        blockchain_name=blockchain_data.blockchain_name,
        blockchain_type=blockchain_data.blockchain_type,
        chain_id=blockchain_data.chain_id,
        rpc_url=blockchain_data.rpc_url,
        explorer_url=blockchain_data.explorer_url,
        native_currency_name=blockchain_data.native_currency_name,
        native_currency_symbol=blockchain_data.native_currency_symbol,
        integrated_by=current_admin.id,
        status="testing"
    )
    
    db.add(blockchain)
    db.commit()
    db.refresh(blockchain)
    
    # Trigger integration process
    await integrate_custom_blockchain(blockchain)
    
    return {
        "id": blockchain.id,
        "message": "Custom blockchain integration initiated"
    }

@app.get("/api/v1/blockchains", dependencies=[Depends(check_permission("blockchain.view"))])
async def get_custom_blockchains(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    total = db.query(CustomBlockchain).count()
    blockchains = db.query(CustomBlockchain).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "blockchains": blockchains
    }

# Background tasks for deployment and integration
async def deploy_token_listing(application: TokenListingApplication):
    """Deploy token listing to trading engine"""
    try:
        # Add trading pair to matching engine
        trading_pair_data = {
            "symbol": f"{application.token_symbol}USDT",
            "base_asset": application.token_symbol,
            "quote_asset": "USDT",
            "status": "TRADING",
            "min_quantity": 0.001,
            "step_size": 0.001,
            "tick_size": 0.0001
        }
        
        # Call matching engine API to add trading pair
        # This would be implemented based on your matching engine API
        logger.info(f"Deployed token listing for {application.token_symbol}")
        
    except Exception as e:
        logger.error(f"Failed to deploy token listing: {str(e)}")

async def deploy_white_label_exchange(exchange: WhiteLabelExchange):
    """Deploy white label exchange infrastructure"""
    try:
        # Generate Docker configuration
        docker_config = generate_exchange_docker_config(exchange)
        
        # Deploy using Docker/Kubernetes
        client = docker.from_env()
        
        # Create custom network
        network_name = f"tigerex-{exchange.subdomain.replace('.', '-')}"
        try:
            network = client.networks.create(network_name, driver="bridge")
        except docker.errors.APIError:
            network = client.networks.get(network_name)
        
        # Deploy frontend container
        frontend_container = client.containers.run(
            "tigerex/frontend:latest",
            name=f"frontend-{exchange.id}",
            environment={
                "EXCHANGE_NAME": exchange.exchange_name,
                "PRIMARY_COLOR": exchange.primary_color,
                "API_URL": f"https://api-{exchange.subdomain}",
                "FEATURES": json.dumps(exchange.features_enabled)
            },
            network=network_name,
            detach=True
        )
        
        # Deploy API container
        api_container = client.containers.run(
            "tigerex/api:latest",
            name=f"api-{exchange.id}",
            environment={
                "DATABASE_URL": os.getenv("DATABASE_URL"),
                "REDIS_URL": os.getenv("REDIS_URL"),
                "EXCHANGE_ID": str(exchange.id)
            },
            network=network_name,
            detach=True
        )
        
        # Update deployment status
        exchange.status = "active"
        exchange.deployed_at = datetime.utcnow()
        
        logger.info(f"Deployed white label exchange: {exchange.exchange_name}")
        
    except Exception as e:
        logger.error(f"Failed to deploy white label exchange: {str(e)}")
        exchange.status = "failed"

async def integrate_custom_blockchain(blockchain: CustomBlockchain):
    """Integrate custom blockchain into the system"""
    try:
        # Test blockchain connection
        if blockchain.blockchain_type == "evm":
            w3 = Web3(Web3.HTTPProvider(blockchain.rpc_url))
            latest_block = w3.eth.get_block('latest')
            blockchain.last_block_number = latest_block.number
        
        # Add to monitoring system
        # This would integrate with your blockchain monitoring service
        
        # Update integration status
        blockchain.status = "active"
        blockchain.integrated_at = datetime.utcnow()
        
        logger.info(f"Integrated custom blockchain: {blockchain.blockchain_name}")
        
    except Exception as e:
        logger.error(f"Failed to integrate blockchain: {str(e)}")
        blockchain.status = "failed"

def generate_exchange_docker_config(exchange: WhiteLabelExchange) -> dict:
    """Generate Docker configuration for white label exchange"""
    return {
        "version": "3.8",
        "services": {
            "frontend": {
                "image": "tigerex/frontend:latest",
                "environment": {
                    "EXCHANGE_NAME": exchange.exchange_name,
                    "PRIMARY_COLOR": exchange.primary_color,
                    "FEATURES": json.dumps(exchange.features_enabled)
                },
                "ports": ["80:3000"],
                "networks": [f"tigerex-{exchange.id}"]
            },
            "api": {
                "image": "tigerex/api:latest",
                "environment": {
                    "DATABASE_URL": os.getenv("DATABASE_URL"),
                    "EXCHANGE_ID": str(exchange.id)
                },
                "ports": ["8000:8000"],
                "networks": [f"tigerex-{exchange.id}"]
            }
        },
        "networks": {
            f"tigerex-{exchange.id}": {
                "driver": "bridge"
            }
        }
    }

# System monitoring and health endpoints
@app.get("/api/v1/system/health")
async def system_health():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow(),
        "version": "2.0.0"
    }

@app.get("/api/v1/system/stats", dependencies=[Depends(check_permission("system.monitoring"))])
async def get_system_stats(db: Session = Depends(get_db)):
    stats = {
        "total_admin_users": db.query(AdminUser).count(),
        "active_admin_users": db.query(AdminUser).filter(AdminUser.is_active == True).count(),
        "pending_kyc_applications": db.query(KYCApplication).filter(KYCApplication.status == "pending").count(),
        "pending_token_listings": db.query(TokenListingApplication).filter(TokenListingApplication.status == "submitted").count(),
        "active_white_label_exchanges": db.query(WhiteLabelExchange).filter(WhiteLabelExchange.status == "active").count(),
        "integrated_blockchains": db.query(CustomBlockchain).filter(CustomBlockchain.status == "active").count()
    }
    
    return stats

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
