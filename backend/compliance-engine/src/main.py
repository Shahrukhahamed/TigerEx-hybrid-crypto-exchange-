"""
TigerEx Compliance Engine
Enhanced KYC/AML automation, regulatory reporting, and compliance management
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

import aioredis
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, DECIMAL, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
import boto3
import requests
import pandas as pd

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="TigerEx Compliance Engine",
    description="Enhanced KYC/AML automation, regulatory reporting, and compliance management",
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
    AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET", "tigerex-compliance-docs")
    LARGE_TRANSACTION_THRESHOLD = Decimal("10000")
    AML_RISK_SCORE_THRESHOLD = 75
    KYC_DOCUMENT_EXPIRY_DAYS = 365 * 2

config = Config()

# Database setup
engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

security = HTTPBearer()

# Enums
class KYCStatus(str, Enum):
    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"

class DocumentType(str, Enum):
    PASSPORT = "passport"
    DRIVERS_LICENSE = "drivers_license"
    NATIONAL_ID = "national_id"
    UTILITY_BILL = "utility_bill"
    SELFIE = "selfie"

class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ReportType(str, Enum):
    SAR = "sar"  # Suspicious Activity Report
    CTR = "ctr"  # Currency Transaction Report
    AML = "aml"  # Anti-Money Laundering Report

class TransactionType(str, Enum):
    DEPOSIT = "deposit"
    WITHDRAWAL = "withdrawal"
    TRADE = "trade"
    TRANSFER = "transfer"

# Database Models
class KYCApplication(Base):
    __tablename__ = "kyc_applications"
    
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(String(50), unique=True, nullable=False, index=True)
    user_id = Column(String(50), nullable=False, index=True)
    
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    middle_name = Column(String(100))
    date_of_birth = Column(DateTime, nullable=False)
    nationality = Column(String(50), nullable=False)
    country_of_residence = Column(String(50), nullable=False)
    
    address_line1 = Column(String(255), nullable=False)
    address_line2 = Column(String(255))
    city = Column(String(100), nullable=False)
    state_province = Column(String(100))
    postal_code = Column(String(20), nullable=False)
    country = Column(String(50), nullable=False)
    
    email = Column(String(255), nullable=False)
    phone_number = Column(String(20), nullable=False)
    
    occupation = Column(String(100))
    employer = Column(String(255))
    annual_income = Column(DECIMAL(20, 2))
    source_of_funds = Column(String(255))
    
    risk_score = Column(Integer, default=0)
    risk_level = Column(SQLEnum(RiskLevel), default=RiskLevel.MEDIUM)
    risk_factors = Column(JSON)
    
    is_pep = Column(Boolean, default=False)
    pep_details = Column(JSON)
    
    sanctions_hit = Column(Boolean, default=False)
    sanctions_details = Column(JSON)
    
    status = Column(SQLEnum(KYCStatus), default=KYCStatus.PENDING)
    reviewed_by = Column(String(50))
    reviewed_at = Column(DateTime)
    rejection_reason = Column(Text)
    
    auto_approved = Column(Boolean, default=False)
    manual_review_required = Column(Boolean, default=False)
    
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=func.now())
    
    documents = relationship("KYCDocument", back_populates="application")

class KYCDocument(Base):
    __tablename__ = "kyc_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(String(50), unique=True, nullable=False, index=True)
    
    application_id = Column(Integer, ForeignKey("kyc_applications.id"), nullable=False)
    application = relationship("KYCApplication", back_populates="documents")
    
    document_type = Column(SQLEnum(DocumentType), nullable=False)
    document_number = Column(String(100))
    issuing_country = Column(String(50))
    issue_date = Column(DateTime)
    expiry_date = Column(DateTime)
    
    file_url = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(Integer)
    file_hash = Column(String(64))
    
    extracted_data = Column(JSON)
    confidence_score = Column(DECIMAL(5, 2))
    
    is_verified = Column(Boolean, default=False)
    verification_method = Column(String(50))
    verification_details = Column(JSON)
    
    status = Column(String(20), default="pending")
    rejection_reason = Column(Text)
    
    created_at = Column(DateTime, default=func.now())

class AMLAlert(Base):
    __tablename__ = "aml_alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(50), unique=True, nullable=False, index=True)
    
    user_id = Column(String(50), nullable=False, index=True)
    transaction_id = Column(String(50), index=True)
    
    alert_type = Column(String(50), nullable=False)
    severity = Column(SQLEnum(RiskLevel), nullable=False)
    description = Column(Text, nullable=False)
    
    risk_score = Column(Integer, nullable=False)
    risk_factors = Column(JSON)
    
    transaction_amount = Column(DECIMAL(20, 2))
    transaction_currency = Column(String(10))
    transaction_type = Column(SQLEnum(TransactionType))
    
    status = Column(String(20), default="open")
    assigned_to = Column(String(50))
    investigation_notes = Column(Text)
    
    resolution = Column(String(50))
    resolved_by = Column(String(50))
    resolved_at = Column(DateTime)
    
    reported_to_authorities = Column(Boolean, default=False)
    report_reference = Column(String(100))
    
    created_at = Column(DateTime, default=func.now())

class ComplianceReport(Base):
    __tablename__ = "compliance_reports"
    
    id = Column(Integer, primary_key=True, index=True)
    report_id = Column(String(50), unique=True, nullable=False, index=True)
    
    report_type = Column(SQLEnum(ReportType), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)
    
    report_data = Column(JSON)
    file_url = Column(String(500))
    
    submitted_to = Column(String(255))
    submission_reference = Column(String(100))
    submitted_at = Column(DateTime)
    
    status = Column(String(20), default="draft")
    
    generated_by = Column(String(50), nullable=False)
    generated_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())

# Pydantic Models
class KYCApplicationCreate(BaseModel):
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    date_of_birth: datetime
    nationality: str
    country_of_residence: str
    address_line1: str
    address_line2: Optional[str] = None
    city: str
    state_province: Optional[str] = None
    postal_code: str
    country: str
    email: EmailStr
    phone_number: str
    occupation: Optional[str] = None
    employer: Optional[str] = None
    annual_income: Optional[Decimal] = None
    source_of_funds: Optional[str] = None

class DocumentUpload(BaseModel):
    document_type: DocumentType
    document_number: Optional[str] = None
    issuing_country: Optional[str] = None
    issue_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None

# Dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    return {"user_id": "user_123", "username": "testuser", "role": "compliance_officer"}

# Compliance Engine Manager
class ComplianceEngineManager:
    def __init__(self):
        self.redis_client = None
        self.s3_client = None
        
    async def initialize(self):
        self.redis_client = await aioredis.from_url(config.REDIS_URL)
        if os.getenv("AWS_ACCESS_KEY_ID"):
            self.s3_client = boto3.client('s3')
    
    async def submit_kyc_application(self, application_data: KYCApplicationCreate, user: Dict[str, Any], db: Session):
        existing_app = db.query(KYCApplication).filter(
            KYCApplication.user_id == user["user_id"],
            KYCApplication.status.in_([KYCStatus.PENDING, KYCStatus.IN_REVIEW, KYCStatus.APPROVED])
        ).first()
        
        if existing_app:
            if existing_app.status == KYCStatus.APPROVED:
                raise HTTPException(status_code=400, detail="KYC already approved")
            else:
                raise HTTPException(status_code=400, detail="KYC application already exists")
        
        application_id = f"KYC_{secrets.token_hex(8).upper()}"
        
        application = KYCApplication(
            application_id=application_id,
            user_id=user["user_id"],
            first_name=application_data.first_name,
            last_name=application_data.last_name,
            middle_name=application_data.middle_name,
            date_of_birth=application_data.date_of_birth,
            nationality=application_data.nationality,
            country_of_residence=application_data.country_of_residence,
            address_line1=application_data.address_line1,
            address_line2=application_data.address_line2,
            city=application_data.city,
            state_province=application_data.state_province,
            postal_code=application_data.postal_code,
            country=application_data.country,
            email=application_data.email,
            phone_number=application_data.phone_number,
            occupation=application_data.occupation,
            employer=application_data.employer,
            annual_income=application_data.annual_income,
            source_of_funds=application_data.source_of_funds,
            expires_at=datetime.now() + timedelta(days=config.KYC_DOCUMENT_EXPIRY_DAYS)
        )
        
        db.add(application)
        db.commit()
        db.refresh(application)
        
        await self.perform_initial_risk_assessment(application, db)
        return application
    
    async def perform_initial_risk_assessment(self, application: KYCApplication, db: Session):
        risk_factors = []
        risk_score = 0
        
        # Country risk assessment
        high_risk_countries = ["AF", "IR", "KP", "SY"]
        if application.country in high_risk_countries or application.nationality in high_risk_countries:
            risk_factors.append("high_risk_country")
            risk_score += 30
        
        # Age risk assessment
        age = (datetime.now() - application.date_of_birth).days // 365
        if age < 18:
            risk_factors.append("underage")
            risk_score += 50
        elif age > 80:
            risk_factors.append("elderly")
            risk_score += 10
        
        # PEP and sanctions screening
        pep_result = await self.screen_for_pep(application)
        sanctions_result = await self.screen_for_sanctions(application)
        
        if pep_result["is_pep"]:
            risk_factors.append("pep")
            risk_score += 40
            application.is_pep = True
            application.pep_details = pep_result["details"]
        
        if sanctions_result["hit"]:
            risk_factors.append("sanctions_hit")
            risk_score += 100
            application.sanctions_hit = True
            application.sanctions_details = sanctions_result["details"]
        
        application.risk_score = min(risk_score, 100)
        application.risk_factors = risk_factors
        application.risk_level = self.get_risk_level(risk_score)
        
        if risk_score >= config.AML_RISK_SCORE_THRESHOLD or application.sanctions_hit:
            application.manual_review_required = True
            application.status = KYCStatus.IN_REVIEW
        
        db.commit()
    
    async def screen_for_pep(self, application: KYCApplication) -> Dict[str, Any]:
        # Mock PEP screening
        return {"is_pep": False, "details": None}
    
    async def screen_for_sanctions(self, application: KYCApplication) -> Dict[str, Any]:
        # Mock sanctions screening
        return {"hit": False, "details": None}
    
    def get_risk_level(self, risk_score: int) -> RiskLevel:
        if risk_score >= 80:
            return RiskLevel.CRITICAL
        elif risk_score >= 60:
            return RiskLevel.HIGH
        elif risk_score >= 30:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    async def upload_kyc_document(self, application_id: str, document_data: DocumentUpload, file: UploadFile, user: Dict[str, Any], db: Session):
        application = db.query(KYCApplication).filter(
            KYCApplication.application_id == application_id,
            KYCApplication.user_id == user["user_id"]
        ).first()
        
        if not application:
            raise HTTPException(status_code=404, detail="KYC application not found")
        
        if file.size > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large")
        
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'application/pdf']
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Invalid file type")
        
        content = await file.read()
        file_hash = hashlib.sha256(content).hexdigest()
        
        # Mock file upload
        file_url = f"https://example.com/documents/{uuid.uuid4()}.jpg"
        
        document_id = f"DOC_{secrets.token_hex(8).upper()}"
        
        document = KYCDocument(
            document_id=document_id,
            application_id=application.id,
            document_type=document_data.document_type,
            document_number=document_data.document_number,
            issuing_country=document_data.issuing_country,
            issue_date=document_data.issue_date,
            expiry_date=document_data.expiry_date,
            file_url=file_url,
            file_name=file.filename,
            file_size=file.size,
            file_hash=file_hash
        )
        
        db.add(document)
        db.commit()
        db.refresh(document)
        
        # Mock document processing
        document.is_verified = True
        document.verification_method = "automated"
        document.status = "verified"
        db.commit()
        
        return document

compliance_engine = ComplianceEngineManager()

@app.on_event("startup")
async def startup_event():
    await compliance_engine.initialize()

# API Endpoints
@app.post("/api/v1/kyc/applications")
async def submit_kyc_application(
    application_data: KYCApplicationCreate,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    application = await compliance_engine.submit_kyc_application(application_data, current_user, db)
    return {
        "application_id": application.application_id,
        "status": application.status,
        "risk_level": application.risk_level,
        "manual_review_required": application.manual_review_required
    }

@app.post("/api/v1/kyc/applications/{application_id}/documents")
async def upload_kyc_document(
    application_id: str,
    document_data: DocumentUpload = Depends(),
    file: UploadFile = File(...),
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    document = await compliance_engine.upload_kyc_document(
        application_id, document_data, file, current_user, db
    )
    return {
        "document_id": document.document_id,
        "document_type": document.document_type,
        "status": document.status,
        "is_verified": document.is_verified
    }

@app.get("/api/v1/kyc/applications/{application_id}")
async def get_kyc_application(
    application_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    application = db.query(KYCApplication).filter(
        KYCApplication.application_id == application_id,
        KYCApplication.user_id == current_user["user_id"]
    ).first()
    
    if not application:
        raise HTTPException(status_code=404, detail="KYC application not found")
    
    return {
        "application_id": application.application_id,
        "status": application.status,
        "risk_level": application.risk_level,
        "risk_score": application.risk_score,
        "is_pep": application.is_pep,
        "sanctions_hit": application.sanctions_hit,
        "manual_review_required": application.manual_review_required,
        "created_at": application.created_at.isoformat(),
        "expires_at": application.expires_at.isoformat() if application.expires_at else None,
        "documents": [
            {
                "document_id": doc.document_id,
                "document_type": doc.document_type,
                "status": doc.status,
                "is_verified": doc.is_verified,
                "created_at": doc.created_at.isoformat()
            }
            for doc in application.documents
        ]
    }

@app.get("/api/v1/aml/alerts")
async def get_aml_alerts(
    status: Optional[str] = None,
    severity: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(AMLAlert)
    
    if status:
        query = query.filter(AMLAlert.status == status)
    
    if severity:
        query = query.filter(AMLAlert.severity == severity)
    
    alerts = query.order_by(AMLAlert.created_at.desc()).offset(offset).limit(limit).all()
    
    return {
        "alerts": [
            {
                "alert_id": alert.alert_id,
                "user_id": alert.user_id,
                "alert_type": alert.alert_type,
                "severity": alert.severity,
                "description": alert.description,
                "risk_score": alert.risk_score,
                "transaction_amount": str(alert.transaction_amount) if alert.transaction_amount else None,
                "status": alert.status,
                "created_at": alert.created_at.isoformat()
            }
            for alert in alerts
        ]
    }

@app.post("/api/v1/compliance/reports")
async def generate_compliance_report(
    report_type: ReportType,
    period_start: datetime,
    period_end: datetime,
    current_user: Dict[str, Any] = Depends(get_current_user),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    if current_user.get("role") != "compliance_officer":
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    report_id = f"RPT_{secrets.token_hex(8).upper()}"
    
    report = ComplianceReport(
        report_id=report_id,
        report_type=report_type,
        title=f"{report_type.value.upper()} Report",
        description=f"Compliance report for period {period_start} to {period_end}",
        period_start=period_start,
        period_end=period_end,
        generated_by=current_user["user_id"]
    )
    
    db.add(report)
    db.commit()
    
    return {
        "report_id": report_id,
        "status": "generating",
        "estimated_completion": (datetime.now() + timedelta(minutes=10)).isoformat()
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "compliance-engine"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
