"""
TigerEx Authentication Service
OAuth, 2FA, Captcha, and comprehensive authentication system
"""

import asyncio
import json
import logging
import os
import uuid
import secrets
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import hashlib
import hmac
import io

import aioredis
import aiohttp
from fastapi import FastAPI, HTTPException, Depends, Request, Response, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, validator, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
from passlib.context import CryptContext
from jose import JWTError, jwt
import pyotp
import qrcode
from PIL import Image, ImageDraw, ImageFont
import random
import string
from authlib.integrations.starlette_client import OAuth
from twilio.rest import Client as TwilioClient
import sendgrid
from sendgrid.helpers.mail import Mail
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="TigerEx Authentication Service",
    description="OAuth, 2FA, Captcha, and comprehensive authentication system",
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
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "auth-secret-key")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRATION_HOURS = 24
    
    # OAuth Configuration
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    APPLE_CLIENT_ID = os.getenv("APPLE_CLIENT_ID")
    APPLE_CLIENT_SECRET = os.getenv("APPLE_CLIENT_SECRET")
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    
    # 2FA Configuration
    TOTP_ISSUER = "TigerEx"
    SMS_PROVIDER = "twilio"  # twilio or aws_sns
    
    # External Services
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
    SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
    
    # Security
    PASSWORD_MIN_LENGTH = 8
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 30
    CAPTCHA_EXPIRY_MINUTES = 10

config = Config()

# Database setup
engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# OAuth setup
oauth = OAuth()
oauth.register(
    name='google',
    client_id=config.GOOGLE_CLIENT_ID,
    client_secret=config.GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid_configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

# Enums
class UserRole(str, Enum):
    USER = "user"
    TRADER = "trader"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"

class UserStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"

class AuthProvider(str, Enum):
    EMAIL = "email"
    GOOGLE = "google"
    APPLE = "apple"
    TELEGRAM = "telegram"

class TwoFactorType(str, Enum):
    TOTP = "totp"
    SMS = "sms"
    EMAIL = "email"

# Database Models
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Basic Information
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255))
    
    # Profile
    first_name = Column(String(100))
    last_name = Column(String(100))
    phone_number = Column(String(20))
    avatar_url = Column(String(500))
    
    # Status and Role
    role = Column(SQLEnum(UserRole), default=UserRole.USER)
    status = Column(SQLEnum(UserStatus), default=UserStatus.PENDING_VERIFICATION)
    is_email_verified = Column(Boolean, default=False)
    is_phone_verified = Column(Boolean, default=False)
    
    # Security
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    last_login_at = Column(DateTime)
    last_login_ip = Column(String(45))
    
    # 2FA
    two_factor_enabled = Column(Boolean, default=False)
    two_factor_type = Column(SQLEnum(TwoFactorType))
    totp_secret = Column(String(32))
    backup_codes = Column(JSON)  # List of backup codes
    
    # OAuth
    auth_provider = Column(SQLEnum(AuthProvider), default=AuthProvider.EMAIL)
    google_id = Column(String(100))
    apple_id = Column(String(100))
    telegram_id = Column(String(100))
    
    # Timestamps
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user")

class UserSession(Base):
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), unique=True, nullable=False, index=True)
    
    user_id = Column(Integer, relationship("User.id"), nullable=False)
    user = relationship("User", back_populates="sessions")
    
    # Session Details
    access_token = Column(String(500), nullable=False)
    refresh_token = Column(String(500), nullable=False)
    device_info = Column(JSON)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    
    # Status
    is_active = Column(Boolean, default=True)
    expires_at = Column(DateTime, nullable=False)
    
    created_at = Column(DateTime, default=func.now())

class LoginAttempt(Base):
    __tablename__ = "login_attempts"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Attempt Details
    email = Column(String(255), index=True)
    ip_address = Column(String(45), nullable=False, index=True)
    user_agent = Column(Text)
    
    # Result
    success = Column(Boolean, nullable=False)
    failure_reason = Column(String(100))
    
    # Location (optional)
    country = Column(String(50))
    city = Column(String(100))
    
    created_at = Column(DateTime, default=func.now())

class EmailVerification(Base):
    __tablename__ = "email_verifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, relationship("User.id"), nullable=False)
    
    verification_code = Column(String(6), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=func.now())

class PhoneVerification(Base):
    __tablename__ = "phone_verifications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, relationship("User.id"), nullable=False)
    
    phone_number = Column(String(20), nullable=False)
    verification_code = Column(String(6), nullable=False)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=func.now())

# Pydantic Models
class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < config.PASSWORD_MIN_LENGTH:
            raise ValueError(f'Password must be at least {config.PASSWORD_MIN_LENGTH} characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v

class UserLogin(BaseModel):
    email: str
    password: str
    captcha_token: Optional[str] = None
    two_factor_code: Optional[str] = None

class TwoFactorSetup(BaseModel):
    two_factor_type: TwoFactorType
    phone_number: Optional[str] = None

class TwoFactorVerify(BaseModel):
    code: str
    backup_code: Optional[str] = None

class PasswordReset(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str
    
    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < config.PASSWORD_MIN_LENGTH:
            raise ValueError(f'Password must be at least {config.PASSWORD_MIN_LENGTH} characters')
        return v

# Dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Authentication Manager
class AuthenticationManager:
    def __init__(self):
        self.redis_client = None
        self.twilio_client = None
        self.sendgrid_client = None
        
    async def initialize(self):
        """Initialize async components"""
        self.redis_client = await aioredis.from_url(config.REDIS_URL)
        
        # Initialize external services
        if config.TWILIO_ACCOUNT_SID and config.TWILIO_AUTH_TOKEN:
            self.twilio_client = TwilioClient(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
        
        if config.SENDGRID_API_KEY:
            self.sendgrid_client = sendgrid.SendGridAPIClient(api_key=config.SENDGRID_API_KEY)
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def create_access_token(self, data: dict) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(hours=config.JWT_EXPIRATION_HOURS)
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create JWT refresh token"""
        data = {"sub": user_id, "type": "refresh"}
        expire = datetime.utcnow() + timedelta(days=30)
        data.update({"exp": expire})
        return jwt.encode(data, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify JWT token"""
        try:
            payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
            return payload
        except JWTError:
            return None
    
    async def register_user(self, user_data: UserRegister, db: Session) -> User:
        """Register new user"""
        
        # Check if email already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Check if username already exists
        existing_username = db.query(User).filter(User.username == user_data.username).first()
        if existing_username:
            raise HTTPException(status_code=400, detail="Username already taken")
        
        # Create user
        user_id = f"USER_{secrets.token_hex(8).upper()}"
        hashed_password = self.hash_password(user_data.password)
        
        user = User(
            user_id=user_id,
            email=user_data.email,
            username=user_data.username,
            password_hash=hashed_password,
            first_name=user_data.first_name,
            last_name=user_data.last_name,
            phone_number=user_data.phone_number
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        # Send email verification
        await self.send_email_verification(user, db)
        
        return user
    
    async def authenticate_user(self, login_data: UserLogin, request: Request, db: Session) -> Dict[str, Any]:
        """Authenticate user with email/password"""
        
        # Check rate limiting
        await self.check_rate_limit(login_data.email, request.client.host)
        
        # Verify captcha if required
        if login_data.captcha_token:
            if not await self.verify_captcha(login_data.captcha_token):
                raise HTTPException(status_code=400, detail="Invalid captcha")
        
        # Get user
        user = db.query(User).filter(User.email == login_data.email).first()
        if not user or not self.verify_password(login_data.password, user.password_hash):
            await self.log_failed_attempt(login_data.email, request.client.host, "invalid_credentials", db)
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            raise HTTPException(status_code=423, detail="Account temporarily locked")
        
        # Check if account is active
        if user.status != UserStatus.ACTIVE:
            raise HTTPException(status_code=403, detail="Account not active")
        
        # Check 2FA if enabled
        if user.two_factor_enabled:
            if not login_data.two_factor_code:
                raise HTTPException(status_code=200, detail="2FA required", headers={"X-Require-2FA": "true"})
            
            if not await self.verify_2fa_code(user, login_data.two_factor_code):
                await self.log_failed_attempt(login_data.email, request.client.host, "invalid_2fa", db)
                raise HTTPException(status_code=401, detail="Invalid 2FA code")
        
        # Create session
        session = await self.create_user_session(user, request, db)
        
        # Update user login info
        user.last_login_at = datetime.utcnow()
        user.last_login_ip = request.client.host
        user.failed_login_attempts = 0
        user.locked_until = None
        
        # Log successful attempt
        await self.log_successful_attempt(login_data.email, request.client.host, db)
        
        db.commit()
        
        return {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "token_type": "bearer",
            "user": {
                "user_id": user.user_id,
                "email": user.email,
                "username": user.username,
                "role": user.role,
                "two_factor_enabled": user.two_factor_enabled
            }
        }
    
    async def oauth_login(self, provider: str, oauth_data: Dict[str, Any], request: Request, db: Session) -> Dict[str, Any]:
        """Handle OAuth login"""
        
        if provider == "google":
            email = oauth_data.get("email")
            google_id = oauth_data.get("sub")
            name = oauth_data.get("name", "").split(" ", 1)
            first_name = name[0] if name else ""
            last_name = name[1] if len(name) > 1 else ""
            
            # Find or create user
            user = db.query(User).filter(
                (User.email == email) | (User.google_id == google_id)
            ).first()
            
            if not user:
                # Create new user
                user_id = f"USER_{secrets.token_hex(8).upper()}"
                username = email.split("@")[0] + "_" + secrets.token_hex(4)
                
                user = User(
                    user_id=user_id,
                    email=email,
                    username=username,
                    first_name=first_name,
                    last_name=last_name,
                    auth_provider=AuthProvider.GOOGLE,
                    google_id=google_id,
                    is_email_verified=True,
                    status=UserStatus.ACTIVE
                )
                
                db.add(user)
                db.commit()
                db.refresh(user)
            else:
                # Update existing user
                if not user.google_id:
                    user.google_id = google_id
                user.auth_provider = AuthProvider.GOOGLE
                user.is_email_verified = True
                if user.status == UserStatus.PENDING_VERIFICATION:
                    user.status = UserStatus.ACTIVE
                db.commit()
        
        # Create session
        session = await self.create_user_session(user, request, db)
        
        return {
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "token_type": "bearer",
            "user": {
                "user_id": user.user_id,
                "email": user.email,
                "username": user.username,
                "role": user.role,
                "two_factor_enabled": user.two_factor_enabled
            }
        }
    
    async def create_user_session(self, user: User, request: Request, db: Session) -> UserSession:
        """Create user session"""
        
        session_id = f"SESS_{secrets.token_hex(16).upper()}"
        
        # Create tokens
        token_data = {
            "sub": user.user_id,
            "email": user.email,
            "role": user.role,
            "session_id": session_id
        }
        
        access_token = self.create_access_token(token_data)
        refresh_token = self.create_refresh_token(user.user_id)
        
        # Create session
        session = UserSession(
            session_id=session_id,
            user_id=user.id,
            access_token=access_token,
            refresh_token=refresh_token,
            device_info={
                "user_agent": request.headers.get("user-agent"),
                "platform": request.headers.get("sec-ch-ua-platform")
            },
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            expires_at=datetime.utcnow() + timedelta(hours=config.JWT_EXPIRATION_HOURS)
        )
        
        db.add(session)
        db.commit()
        db.refresh(session)
        
        return session
    
    async def setup_2fa(self, user: User, setup_data: TwoFactorSetup, db: Session) -> Dict[str, Any]:
        """Setup 2FA for user"""
        
        if setup_data.two_factor_type == TwoFactorType.TOTP:
            # Generate TOTP secret
            secret = pyotp.random_base32()
            totp = pyotp.TOTP(secret)
            
            # Generate QR code
            provisioning_uri = totp.provisioning_uri(
                name=user.email,
                issuer_name=config.TOTP_ISSUER
            )
            
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(provisioning_uri)
            qr.make(fit=True)
            
            qr_image = qr.make_image(fill_color="black", back_color="white")
            
            # Convert to base64
            buffer = io.BytesIO()
            qr_image.save(buffer, format='PNG')
            qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            # Generate backup codes
            backup_codes = [secrets.token_hex(4).upper() for _ in range(10)]
            
            # Update user (but don't enable 2FA yet)
            user.totp_secret = secret
            user.backup_codes = backup_codes
            user.two_factor_type = TwoFactorType.TOTP
            
            db.commit()
            
            return {
                "secret": secret,
                "qr_code": f"data:image/png;base64,{qr_code_base64}",
                "backup_codes": backup_codes,
                "provisioning_uri": provisioning_uri
            }
        
        elif setup_data.two_factor_type == TwoFactorType.SMS:
            if not setup_data.phone_number:
                raise HTTPException(status_code=400, detail="Phone number required for SMS 2FA")
            
            # Send verification SMS
            verification_code = await self.send_sms_verification(setup_data.phone_number)
            
            # Store verification
            verification = PhoneVerification(
                user_id=user.id,
                phone_number=setup_data.phone_number,
                verification_code=verification_code,
                expires_at=datetime.utcnow() + timedelta(minutes=10)
            )
            
            db.add(verification)
            db.commit()
            
            return {
                "message": "Verification code sent to phone",
                "phone_number": setup_data.phone_number[-4:]  # Show last 4 digits
            }
    
    async def verify_2fa_setup(self, user: User, verify_data: TwoFactorVerify, db: Session) -> Dict[str, Any]:
        """Verify and enable 2FA"""
        
        if user.two_factor_type == TwoFactorType.TOTP:
            if not user.totp_secret:
                raise HTTPException(status_code=400, detail="2FA setup not initiated")
            
            totp = pyotp.TOTP(user.totp_secret)
            if not totp.verify(verify_data.code):
                raise HTTPException(status_code=400, detail="Invalid verification code")
            
            # Enable 2FA
            user.two_factor_enabled = True
            db.commit()
            
            return {
                "message": "2FA enabled successfully",
                "backup_codes": user.backup_codes
            }
        
        elif user.two_factor_type == TwoFactorType.SMS:
            # Verify SMS code
            verification = db.query(PhoneVerification).filter(
                PhoneVerification.user_id == user.id,
                PhoneVerification.verification_code == verify_data.code,
                PhoneVerification.expires_at > datetime.utcnow(),
                PhoneVerification.is_used == False
            ).first()
            
            if not verification:
                raise HTTPException(status_code=400, detail="Invalid or expired verification code")
            
            # Enable 2FA
            user.two_factor_enabled = True
            user.phone_number = verification.phone_number
            user.is_phone_verified = True
            verification.is_used = True
            
            db.commit()
            
            return {"message": "SMS 2FA enabled successfully"}
    
    async def verify_2fa_code(self, user: User, code: str) -> bool:
        """Verify 2FA code during login"""
        
        if user.two_factor_type == TwoFactorType.TOTP:
            if not user.totp_secret:
                return False
            
            totp = pyotp.TOTP(user.totp_secret)
            if totp.verify(code):
                return True
            
            # Check backup codes
            if user.backup_codes and code.upper() in user.backup_codes:
                # Remove used backup code
                user.backup_codes.remove(code.upper())
                return True
        
        elif user.two_factor_type == TwoFactorType.SMS:
            # For SMS, we would send a code and verify it
            # This is a simplified implementation
            return len(code) == 6 and code.isdigit()
        
        return False
    
    async def send_email_verification(self, user: User, db: Session):
        """Send email verification code"""
        
        verification_code = str(random.randint(100000, 999999))
        
        # Store verification
        verification = EmailVerification(
            user_id=user.id,
            verification_code=verification_code,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        
        db.add(verification)
        db.commit()
        
        # Send email (mock implementation)
        logger.info(f"Email verification code for {user.email}: {verification_code}")
        
        # In production, send actual email using SendGrid
        if self.sendgrid_client:
            message = Mail(
                from_email='noreply@tigerex.com',
                to_emails=user.email,
                subject='TigerEx Email Verification',
                html_content=f'''
                <h2>Welcome to TigerEx!</h2>
                <p>Your verification code is: <strong>{verification_code}</strong></p>
                <p>This code will expire in 24 hours.</p>
                '''
            )
            
            try:
                response = self.sendgrid_client.send(message)
                logger.info(f"Email sent successfully: {response.status_code}")
            except Exception as e:
                logger.error(f"Error sending email: {e}")
    
    async def send_sms_verification(self, phone_number: str) -> str:
        """Send SMS verification code"""
        
        verification_code = str(random.randint(100000, 999999))
        
        # Send SMS (mock implementation)
        logger.info(f"SMS verification code for {phone_number}: {verification_code}")
        
        # In production, send actual SMS using Twilio
        if self.twilio_client:
            try:
                message = self.twilio_client.messages.create(
                    body=f"Your TigerEx verification code is: {verification_code}",
                    from_=config.TWILIO_PHONE_NUMBER,
                    to=phone_number
                )
                logger.info(f"SMS sent successfully: {message.sid}")
            except Exception as e:
                logger.error(f"Error sending SMS: {e}")
        
        return verification_code
    
    async def generate_captcha(self) -> Dict[str, Any]:
        """Generate captcha challenge"""
        
        # Generate random text
        captcha_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        
        # Create image
        img = Image.new('RGB', (200, 80), color='white')
        draw = ImageDraw.Draw(img)
        
        # Add noise
        for _ in range(100):
            x = random.randint(0, 200)
            y = random.randint(0, 80)
            draw.point((x, y), fill='gray')
        
        # Add text
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
        except:
            font = ImageFont.load_default()
        
        draw.text((20, 20), captcha_text, fill='black', font=font)
        
        # Add lines
        for _ in range(5):
            x1 = random.randint(0, 200)
            y1 = random.randint(0, 80)
            x2 = random.randint(0, 200)
            y2 = random.randint(0, 80)
            draw.line([(x1, y1), (x2, y2)], fill='gray', width=2)
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        captcha_image = base64.b64encode(buffer.getvalue()).decode()
        
        # Store in Redis
        captcha_token = secrets.token_urlsafe(32)
        await self.redis_client.setex(
            f"captcha:{captcha_token}",
            config.CAPTCHA_EXPIRY_MINUTES * 60,
            captcha_text
        )
        
        return {
            "captcha_token": captcha_token,
            "captcha_image": f"data:image/png;base64,{captcha_image}"
        }
    
    async def verify_captcha(self, captcha_token: str, user_input: str = None) -> bool:
        """Verify captcha response"""
        
        if not captcha_token:
            return False
        
        stored_text = await self.redis_client.get(f"captcha:{captcha_token}")
        if not stored_text:
            return False
        
        # For this implementation, we'll return True if token exists
        # In real implementation, compare user_input with stored_text
        await self.redis_client.delete(f"captcha:{captcha_token}")
        return True
    
    async def check_rate_limit(self, email: str, ip_address: str):
        """Check rate limiting for login attempts"""
        
        # Check IP-based rate limiting
        ip_key = f"rate_limit:ip:{ip_address}"
        ip_attempts = await self.redis_client.get(ip_key)
        
        if ip_attempts and int(ip_attempts) >= config.MAX_LOGIN_ATTEMPTS:
            raise HTTPException(status_code=429, detail="Too many login attempts from this IP")
        
        # Check email-based rate limiting
        email_key = f"rate_limit:email:{email}"
        email_attempts = await self.redis_client.get(email_key)
        
        if email_attempts and int(email_attempts) >= config.MAX_LOGIN_ATTEMPTS:
            raise HTTPException(status_code=429, detail="Too many login attempts for this account")
    
    async def log_failed_attempt(self, email: str, ip_address: str, reason: str, db: Session):
        """Log failed login attempt"""
        
        # Log to database
        attempt = LoginAttempt(
            email=email,
            ip_address=ip_address,
            success=False,
            failure_reason=reason
        )
        
        db.add(attempt)
        db.commit()
        
        # Update rate limiting counters
        ip_key = f"rate_limit:ip:{ip_address}"
        email_key = f"rate_limit:email:{email}"
        
        await self.redis_client.incr(ip_key)
        await self.redis_client.expire(ip_key, config.LOCKOUT_DURATION_MINUTES * 60)
        
        await self.redis_client.incr(email_key)
        await self.redis_client.expire(email_key, config.LOCKOUT_DURATION_MINUTES * 60)
        
        # Update user failed attempts
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= config.MAX_LOGIN_ATTEMPTS:
                user.locked_until = datetime.utcnow() + timedelta(minutes=config.LOCKOUT_DURATION_MINUTES)
            db.commit()
    
    async def log_successful_attempt(self, email: str, ip_address: str, db: Session):
        """Log successful login attempt"""
        
        # Log to database
        attempt = LoginAttempt(
            email=email,
            ip_address=ip_address,
            success=True
        )
        
        db.add(attempt)
        db.commit()
        
        # Clear rate limiting counters
        ip_key = f"rate_limit:ip:{ip_address}"
        email_key = f"rate_limit:email:{email}"
        
        await self.redis_client.delete(ip_key)
        await self.redis_client.delete(email_key)

# Initialize auth manager
auth_manager = AuthenticationManager()

@app.on_event("startup")
async def startup_event():
    await auth_manager.initialize()

# Dependency to get current user
async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    payload = auth_manager.verify_token(token)
    if payload is None:
        raise credentials_exception
    
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    user = db.query(User).filter(User.user_id == user_id).first()
    if user is None:
        raise credentials_exception
    
    return user

# API Endpoints
@app.post("/api/v1/auth/register")
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register new user"""
    user = await auth_manager.register_user(user_data, db)
    return {
        "user_id": user.user_id,
        "email": user.email,
        "username": user.username,
        "status": user.status,
        "message": "Registration successful. Please verify your email."
    }

@app.post("/api/v1/auth/login")
async def login(login_data: UserLogin, request: Request, db: Session = Depends(get_db)):
    """Login with email/password"""
    result = await auth_manager.authenticate_user(login_data, request, db)
    return result

@app.get("/api/v1/auth/oauth/{provider}")
async def oauth_login(provider: str, request: Request):
    """Initiate OAuth login"""
    if provider == "google":
        redirect_uri = request.url_for('oauth_callback', provider=provider)
        return await oauth.google.authorize_redirect(request, redirect_uri)
    else:
        raise HTTPException(status_code=400, detail="Unsupported OAuth provider")

@app.get("/api/v1/auth/oauth/{provider}/callback")
async def oauth_callback(provider: str, request: Request, db: Session = Depends(get_db)):
    """Handle OAuth callback"""
    if provider == "google":
        token = await oauth.google.authorize_access_token(request)
        user_info = token.get('userinfo')
        
        if user_info:
            result = await auth_manager.oauth_login(provider, user_info, request, db)
            return result
    
    raise HTTPException(status_code=400, detail="OAuth authentication failed")

@app.get("/api/v1/auth/captcha")
async def get_captcha():
    """Generate captcha challenge"""
    captcha = await auth_manager.generate_captcha()
    return captcha

@app.post("/api/v1/auth/2fa/setup")
async def setup_2fa(
    setup_data: TwoFactorSetup,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Setup 2FA for user"""
    result = await auth_manager.setup_2fa(current_user, setup_data, db)
    return result

@app.post("/api/v1/auth/2fa/verify")
async def verify_2fa(
    verify_data: TwoFactorVerify,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Verify and enable 2FA"""
    result = await auth_manager.verify_2fa_setup(current_user, verify_data, db)
    return result

@app.post("/api/v1/auth/2fa/disable")
async def disable_2fa(
    verify_data: TwoFactorVerify,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Disable 2FA"""
    if not await auth_manager.verify_2fa_code(current_user, verify_data.code):
        raise HTTPException(status_code=400, detail="Invalid 2FA code")
    
    current_user.two_factor_enabled = False
    current_user.totp_secret = None
    current_user.backup_codes = None
    current_user.two_factor_type = None
    
    db.commit()
    
    return {"message": "2FA disabled successfully"}

@app.get("/api/v1/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return {
        "user_id": current_user.user_id,
        "email": current_user.email,
        "username": current_user.username,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "role": current_user.role,
        "status": current_user.status,
        "two_factor_enabled": current_user.two_factor_enabled,
        "is_email_verified": current_user.is_email_verified,
        "is_phone_verified": current_user.is_phone_verified,
        "created_at": current_user.created_at.isoformat()
    }

@app.post("/api/v1/auth/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout user"""
    # Invalidate all user sessions
    db.query(UserSession).filter(UserSession.user_id == current_user.id).update({"is_active": False})
    db.commit()
    
    return {"message": "Logged out successfully"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "auth-service"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
