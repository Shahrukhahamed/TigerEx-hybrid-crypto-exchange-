"""
TigerEx Role-Based Admin System
Multi-role admin dashboard with specialized interfaces for different admin types
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

import aioredis
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator, EmailStr
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, DECIMAL, ForeignKey, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.sql import func
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="TigerEx Role-Based Admin System",
    description="Multi-role admin dashboard with specialized interfaces for different admin types",
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
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "role-admin-secret-key")

config = Config()

# Database setup
engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

security = HTTPBearer()

# Enums
class AdminRole(str, Enum):
    SUPER_ADMIN = "super_admin"
    KYC_ADMIN = "kyc_admin"
    CUSTOMER_SUPPORT = "customer_support"
    P2P_MANAGER = "p2p_manager"
    AFFILIATE_MANAGER = "affiliate_manager"
    BUSINESS_DEV_MANAGER = "business_dev_manager"
    LISTING_MANAGER = "listing_manager"
    RISK_MANAGER = "risk_manager"
    COMPLIANCE_OFFICER = "compliance_officer"
    TECHNICAL_ADMIN = "technical_admin"

class TicketStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

class TicketPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class KYCStatus(str, Enum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_ADDITIONAL_INFO = "requires_additional_info"

class AffiliateStatus(str, Enum):
    PENDING = "pending"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    TERMINATED = "terminated"

# Database Models
class AdminUser(Base):
    __tablename__ = "admin_users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Basic Info
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(200))
    
    # Role and Permissions
    role = Column(SQLEnum(AdminRole), nullable=False)
    permissions = Column(JSON, default=list)
    department = Column(String(100))
    manager_id = Column(String(50))
    
    # Status
    is_active = Column(Boolean, default=True)
    is_2fa_enabled = Column(Boolean, default=False)
    totp_secret = Column(String(32))
    
    # Session Management
    last_login_at = Column(DateTime)
    last_login_ip = Column(String(45))
    failed_login_attempts = Column(Integer, default=0)
    locked_until = Column(DateTime)
    
    # Performance Metrics
    tickets_resolved = Column(Integer, default=0)
    avg_resolution_time = Column(DECIMAL(10, 2), default=0)
    customer_satisfaction = Column(DECIMAL(3, 2), default=0)
    
    # Audit
    created_by = Column(String(50))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class SupportTicket(Base):
    __tablename__ = "support_tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Ticket Info
    user_id = Column(String(50), nullable=False)
    subject = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String(50), nullable=False)
    priority = Column(SQLEnum(TicketPriority), default=TicketPriority.MEDIUM)
    status = Column(SQLEnum(TicketStatus), default=TicketStatus.OPEN)
    
    # Assignment
    assigned_to = Column(String(50))
    assigned_at = Column(DateTime)
    
    # Resolution
    resolution = Column(Text)
    resolved_at = Column(DateTime)
    resolution_time = Column(Integer)  # in minutes
    
    # Satisfaction
    satisfaction_rating = Column(Integer)  # 1-5 stars
    satisfaction_feedback = Column(Text)
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class KYCApplication(Base):
    __tablename__ = "kyc_applications"
    
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # User Info
    user_id = Column(String(50), nullable=False)
    user_email = Column(String(255), nullable=False)
    
    # Personal Information
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(DateTime, nullable=False)
    nationality = Column(String(3), nullable=False)
    country_of_residence = Column(String(3), nullable=False)
    
    # Address Information
    address_line1 = Column(String(200), nullable=False)
    address_line2 = Column(String(200))
    city = Column(String(100), nullable=False)
    state_province = Column(String(100))
    postal_code = Column(String(20), nullable=False)
    
    # Documents
    id_document_type = Column(String(50), nullable=False)
    id_document_url = Column(String(500), nullable=False)
    proof_of_address_url = Column(String(500), nullable=False)
    selfie_url = Column(String(500), nullable=False)
    
    # Verification
    status = Column(SQLEnum(KYCStatus), default=KYCStatus.PENDING)
    reviewed_by = Column(String(50))
    reviewed_at = Column(DateTime)
    rejection_reason = Column(Text)
    additional_info_requested = Column(Text)
    
    # Risk Assessment
    risk_score = Column(Integer, default=50)
    risk_factors = Column(JSON)
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class AffiliatePartner(Base):
    __tablename__ = "affiliate_partners"
    
    id = Column(Integer, primary_key=True, index=True)
    partner_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Partner Info
    partner_name = Column(String(200), nullable=False)
    partner_type = Column(String(50), nullable=False)  # individual, company, regional
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(20))
    
    # Company Info (if applicable)
    company_name = Column(String(200))
    company_registration = Column(String(100))
    tax_id = Column(String(50))
    
    # Address
    address_line1 = Column(String(200))
    address_line2 = Column(String(200))
    city = Column(String(100))
    country = Column(String(3))
    
    # Affiliate Details
    referral_code = Column(String(20), unique=True, nullable=False)
    commission_rate = Column(DECIMAL(5, 4), default=0.2)  # 20%
    payment_method = Column(String(50))
    payment_details = Column(JSON)
    
    # Performance
    total_referrals = Column(Integer, default=0)
    active_referrals = Column(Integer, default=0)
    total_commission_earned = Column(DECIMAL(20, 2), default=0)
    total_commission_paid = Column(DECIMAL(20, 2), default=0)
    
    # Status
    status = Column(SQLEnum(AffiliateStatus), default=AffiliateStatus.PENDING)
    approved_by = Column(String(50))
    approved_at = Column(DateTime)
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

class TokenListingApplication(Base):
    __tablename__ = "token_listing_applications"
    
    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(String(50), unique=True, nullable=False, index=True)
    
    # Token Info
    token_name = Column(String(100), nullable=False)
    token_symbol = Column(String(20), nullable=False)
    blockchain_network = Column(String(50), nullable=False)
    contract_address = Column(String(100))
    
    # Project Info
    project_name = Column(String(200), nullable=False)
    project_description = Column(Text, nullable=False)
    website_url = Column(String(500))
    whitepaper_url = Column(String(500))
    
    # Team Info
    team_info = Column(JSON)
    advisors_info = Column(JSON)
    
    # Technical Info
    total_supply = Column(DECIMAL(30, 8))
    circulating_supply = Column(DECIMAL(30, 8))
    token_distribution = Column(JSON)
    
    # Market Info
    current_exchanges = Column(JSON)
    trading_volume = Column(DECIMAL(20, 2))
    market_cap = Column(DECIMAL(20, 2))
    
    # Legal and Compliance
    legal_opinion_url = Column(String(500))
    audit_report_url = Column(String(500))
    compliance_certificates = Column(JSON)
    
    # Application Status
    status = Column(String(50), default="pending")
    reviewed_by = Column(String(50))
    reviewed_at = Column(DateTime)
    listing_fee = Column(DECIMAL(20, 2))
    listing_fee_paid = Column(Boolean, default=False)
    
    # Audit
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

# Pydantic Models
class TicketAssignment(BaseModel):
    assigned_to: str
    priority: Optional[TicketPriority] = None

class TicketResolution(BaseModel):
    resolution: str
    status: TicketStatus = TicketStatus.RESOLVED

class KYCReview(BaseModel):
    status: KYCStatus
    rejection_reason: Optional[str] = None
    additional_info_requested: Optional[str] = None
    risk_score: Optional[int] = None

class AffiliateApproval(BaseModel):
    status: AffiliateStatus
    commission_rate: Optional[Decimal] = None
    notes: Optional[str] = None

# Dependencies
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_admin(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Simplified admin authentication - in production, verify JWT and check admin role
    return {"user_id": "admin_123", "role": AdminRole.SUPER_ADMIN, "username": "admin"}

def check_role(allowed_roles: List[AdminRole]):
    def role_checker(current_admin: Dict[str, Any] = Depends(get_current_admin)):
        if current_admin["role"] not in allowed_roles and current_admin["role"] != AdminRole.SUPER_ADMIN:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_admin
    return role_checker

# Role-Based Admin Manager
class RoleBasedAdminManager:
    def __init__(self):
        self.redis_client = None
        
    async def initialize(self):
        self.redis_client = await aioredis.from_url(config.REDIS_URL)
    
    async def get_dashboard_data(self, admin_role: AdminRole, db: Session) -> Dict[str, Any]:
        """Get role-specific dashboard data"""
        
        if admin_role == AdminRole.CUSTOMER_SUPPORT:
            return await self._get_support_dashboard(db)
        elif admin_role == AdminRole.KYC_ADMIN:
            return await self._get_kyc_dashboard(db)
        elif admin_role == AdminRole.P2P_MANAGER:
            return await self._get_p2p_dashboard(db)
        elif admin_role == AdminRole.AFFILIATE_MANAGER:
            return await self._get_affiliate_dashboard(db)
        elif admin_role == AdminRole.LISTING_MANAGER:
            return await self._get_listing_dashboard(db)
        elif admin_role == AdminRole.BUSINESS_DEV_MANAGER:
            return await self._get_business_dev_dashboard(db)
        else:
            return await self._get_general_dashboard(db)
    
    async def _get_support_dashboard(self, db: Session) -> Dict[str, Any]:
        """Customer Support dashboard data"""
        
        # Ticket statistics
        total_tickets = db.query(SupportTicket).count()
        open_tickets = db.query(SupportTicket).filter(SupportTicket.status == TicketStatus.OPEN).count()
        in_progress_tickets = db.query(SupportTicket).filter(SupportTicket.status == TicketStatus.IN_PROGRESS).count()
        resolved_today = db.query(SupportTicket).filter(
            SupportTicket.status == TicketStatus.RESOLVED,
            SupportTicket.resolved_at >= datetime.utcnow().date()
        ).count()
        
        # Average resolution time
        avg_resolution = db.query(func.avg(SupportTicket.resolution_time)).filter(
            SupportTicket.status == TicketStatus.RESOLVED
        ).scalar() or 0
        
        # Recent tickets
        recent_tickets = db.query(SupportTicket).order_by(SupportTicket.created_at.desc()).limit(10).all()
        
        # Ticket categories
        category_stats = db.query(
            SupportTicket.category,
            func.count(SupportTicket.id).label('count')
        ).group_by(SupportTicket.category).all()
        
        return {
            "overview": {
                "total_tickets": total_tickets,
                "open_tickets": open_tickets,
                "in_progress_tickets": in_progress_tickets,
                "resolved_today": resolved_today,
                "avg_resolution_time": float(avg_resolution) if avg_resolution else 0
            },
            "recent_tickets": [
                {
                    "ticket_id": ticket.ticket_id,
                    "subject": ticket.subject,
                    "category": ticket.category,
                    "priority": ticket.priority,
                    "status": ticket.status,
                    "created_at": ticket.created_at.isoformat()
                }
                for ticket in recent_tickets
            ],
            "category_stats": [
                {"category": stat.category, "count": stat.count}
                for stat in category_stats
            ]
        }
    
    async def _get_kyc_dashboard(self, db: Session) -> Dict[str, Any]:
        """KYC Admin dashboard data"""
        
        # KYC statistics
        total_applications = db.query(KYCApplication).count()
        pending_review = db.query(KYCApplication).filter(KYCApplication.status == KYCStatus.PENDING).count()
        under_review = db.query(KYCApplication).filter(KYCApplication.status == KYCStatus.UNDER_REVIEW).count()
        approved_today = db.query(KYCApplication).filter(
            KYCApplication.status == KYCStatus.APPROVED,
            KYCApplication.reviewed_at >= datetime.utcnow().date()
        ).count()
        
        # Recent applications
        recent_applications = db.query(KYCApplication).order_by(KYCApplication.created_at.desc()).limit(10).all()
        
        # Risk score distribution
        risk_distribution = db.query(
            func.case(
                (KYCApplication.risk_score < 30, 'Low'),
                (KYCApplication.risk_score < 70, 'Medium'),
                else_='High'
            ).label('risk_level'),
            func.count(KYCApplication.id).label('count')
        ).group_by('risk_level').all()
        
        return {
            "overview": {
                "total_applications": total_applications,
                "pending_review": pending_review,
                "under_review": under_review,
                "approved_today": approved_today
            },
            "recent_applications": [
                {
                    "application_id": app.application_id,
                    "user_email": app.user_email,
                    "first_name": app.first_name,
                    "last_name": app.last_name,
                    "status": app.status,
                    "risk_score": app.risk_score,
                    "created_at": app.created_at.isoformat()
                }
                for app in recent_applications
            ],
            "risk_distribution": [
                {"risk_level": dist.risk_level, "count": dist.count}
                for dist in risk_distribution
            ]
        }
    
    async def _get_affiliate_dashboard(self, db: Session) -> Dict[str, Any]:
        """Affiliate Manager dashboard data"""
        
        # Affiliate statistics
        total_partners = db.query(AffiliatePartner).count()
        active_partners = db.query(AffiliatePartner).filter(AffiliatePartner.status == AffiliateStatus.ACTIVE).count()
        pending_approval = db.query(AffiliatePartner).filter(AffiliatePartner.status == AffiliateStatus.PENDING).count()
        
        # Commission statistics
        total_commission_earned = db.query(func.sum(AffiliatePartner.total_commission_earned)).scalar() or 0
        total_commission_paid = db.query(func.sum(AffiliatePartner.total_commission_paid)).scalar() or 0
        
        # Top performers
        top_performers = db.query(AffiliatePartner).order_by(
            AffiliatePartner.total_commission_earned.desc()
        ).limit(10).all()
        
        return {
            "overview": {
                "total_partners": total_partners,
                "active_partners": active_partners,
                "pending_approval": pending_approval,
                "total_commission_earned": float(total_commission_earned),
                "total_commission_paid": float(total_commission_paid),
                "pending_commission": float(total_commission_earned - total_commission_paid)
            },
            "top_performers": [
                {
                    "partner_id": partner.partner_id,
                    "partner_name": partner.partner_name,
                    "total_referrals": partner.total_referrals,
                    "active_referrals": partner.active_referrals,
                    "total_commission_earned": float(partner.total_commission_earned),
                    "commission_rate": float(partner.commission_rate)
                }
                for partner in top_performers
            ]
        }
    
    async def _get_listing_dashboard(self, db: Session) -> Dict[str, Any]:
        """Listing Manager dashboard data"""
        
        # Listing statistics
        total_applications = db.query(TokenListingApplication).count()
        pending_review = db.query(TokenListingApplication).filter(
            TokenListingApplication.status == "pending"
        ).count()
        approved_applications = db.query(TokenListingApplication).filter(
            TokenListingApplication.status == "approved"
        ).count()
        
        # Recent applications
        recent_applications = db.query(TokenListingApplication).order_by(
            TokenListingApplication.created_at.desc()
        ).limit(10).all()
        
        # Blockchain distribution
        blockchain_stats = db.query(
            TokenListingApplication.blockchain_network,
            func.count(TokenListingApplication.id).label('count')
        ).group_by(TokenListingApplication.blockchain_network).all()
        
        return {
            "overview": {
                "total_applications": total_applications,
                "pending_review": pending_review,
                "approved_applications": approved_applications
            },
            "recent_applications": [
                {
                    "application_id": app.application_id,
                    "token_name": app.token_name,
                    "token_symbol": app.token_symbol,
                    "blockchain_network": app.blockchain_network,
                    "status": app.status,
                    "created_at": app.created_at.isoformat()
                }
                for app in recent_applications
            ],
            "blockchain_stats": [
                {"blockchain": stat.blockchain_network, "count": stat.count}
                for stat in blockchain_stats
            ]
        }
    
    async def _get_business_dev_dashboard(self, db: Session) -> Dict[str, Any]:
        """Business Development Manager dashboard data"""
        
        # Partnership statistics
        institutional_clients = 25  # Mock data
        partnership_deals = 12
        revenue_partnerships = 5500000  # $5.5M
        
        # Regional statistics
        regional_stats = [
            {"region": "North America", "clients": 45, "revenue": 2500000},
            {"region": "Europe", "clients": 38, "revenue": 2000000},
            {"region": "Asia Pacific", "clients": 52, "revenue": 3000000},
            {"region": "Latin America", "clients": 15, "revenue": 800000},
            {"region": "Middle East", "clients": 8, "revenue": 400000}
        ]
        
        return {
            "overview": {
                "institutional_clients": institutional_clients,
                "partnership_deals": partnership_deals,
                "revenue_partnerships": revenue_partnerships,
                "active_negotiations": 8
            },
            "regional_stats": regional_stats
        }
    
    async def _get_general_dashboard(self, db: Session) -> Dict[str, Any]:
        """General admin dashboard data"""
        
        return {
            "overview": {
                "total_users": 50000,
                "active_users_24h": 12500,
                "total_volume_24h": 125000000,
                "total_trades_24h": 45000
            }
        }

# Initialize manager
admin_manager = RoleBasedAdminManager()

@app.on_event("startup")
async def startup_event():
    await admin_manager.initialize()

# API Endpoints
@app.get("/api/v1/admin/dashboard")
async def get_admin_dashboard(
    current_admin: Dict[str, Any] = Depends(get_current_admin),
    db: Session = Depends(get_db)
):
    """Get role-specific admin dashboard"""
    dashboard_data = await admin_manager.get_dashboard_data(current_admin["role"], db)
    return dashboard_data

# Customer Support Endpoints
@app.get("/api/v1/admin/support/tickets")
async def get_support_tickets(
    status: Optional[TicketStatus] = None,
    priority: Optional[TicketPriority] = None,
    assigned_to: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_admin: Dict[str, Any] = Depends(check_role([AdminRole.CUSTOMER_SUPPORT])),
    db: Session = Depends(get_db)
):
    """Get support tickets"""
    query = db.query(SupportTicket)
    
    if status:
        query = query.filter(SupportTicket.status == status)
    if priority:
        query = query.filter(SupportTicket.priority == priority)
    if assigned_to:
        query = query.filter(SupportTicket.assigned_to == assigned_to)
    
    tickets = query.order_by(SupportTicket.created_at.desc()).offset(offset).limit(limit).all()
    total = query.count()
    
    return {
        "tickets": [
            {
                "ticket_id": ticket.ticket_id,
                "user_id": ticket.user_id,
                "subject": ticket.subject,
                "category": ticket.category,
                "priority": ticket.priority,
                "status": ticket.status,
                "assigned_to": ticket.assigned_to,
                "created_at": ticket.created_at.isoformat(),
                "resolution_time": ticket.resolution_time
            }
            for ticket in tickets
        ],
        "total": total
    }

@app.post("/api/v1/admin/support/tickets/{ticket_id}/assign")
async def assign_ticket(
    ticket_id: str,
    assignment: TicketAssignment,
    current_admin: Dict[str, Any] = Depends(check_role([AdminRole.CUSTOMER_SUPPORT])),
    db: Session = Depends(get_db)
):
    """Assign ticket to admin"""
    ticket = db.query(SupportTicket).filter(SupportTicket.ticket_id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    ticket.assigned_to = assignment.assigned_to
    ticket.assigned_at = datetime.utcnow()
    ticket.status = TicketStatus.IN_PROGRESS
    
    if assignment.priority:
        ticket.priority = assignment.priority
    
    db.commit()
    
    return {"message": "Ticket assigned successfully"}

@app.post("/api/v1/admin/support/tickets/{ticket_id}/resolve")
async def resolve_ticket(
    ticket_id: str,
    resolution: TicketResolution,
    current_admin: Dict[str, Any] = Depends(check_role([AdminRole.CUSTOMER_SUPPORT])),
    db: Session = Depends(get_db)
):
    """Resolve support ticket"""
    ticket = db.query(SupportTicket).filter(SupportTicket.ticket_id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    ticket.resolution = resolution.resolution
    ticket.status = resolution.status
    ticket.resolved_at = datetime.utcnow()
    
    if ticket.created_at:
        ticket.resolution_time = int((datetime.utcnow() - ticket.created_at).total_seconds() / 60)
    
    db.commit()
    
    return {"message": "Ticket resolved successfully"}

# KYC Admin Endpoints
@app.get("/api/v1/admin/kyc/applications")
async def get_kyc_applications(
    status: Optional[KYCStatus] = None,
    risk_level: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_admin: Dict[str, Any] = Depends(check_role([AdminRole.KYC_ADMIN])),
    db: Session = Depends(get_db)
):
    """Get KYC applications"""
    query = db.query(KYCApplication)
    
    if status:
        query = query.filter(KYCApplication.status == status)
    if risk_level:
        if risk_level == "low":
            query = query.filter(KYCApplication.risk_score < 30)
        elif risk_level == "medium":
            query = query.filter(KYCApplication.risk_score.between(30, 70))
        elif risk_level == "high":
            query = query.filter(KYCApplication.risk_score > 70)
    
    applications = query.order_by(KYCApplication.created_at.desc()).offset(offset).limit(limit).all()
    total = query.count()
    
    return {
        "applications": [
            {
                "application_id": app.application_id,
                "user_email": app.user_email,
                "first_name": app.first_name,
                "last_name": app.last_name,
                "nationality": app.nationality,
                "status": app.status,
                "risk_score": app.risk_score,
                "created_at": app.created_at.isoformat()
            }
            for app in applications
        ],
        "total": total
    }

@app.post("/api/v1/admin/kyc/applications/{application_id}/review")
async def review_kyc_application(
    application_id: str,
    review: KYCReview,
    current_admin: Dict[str, Any] = Depends(check_role([AdminRole.KYC_ADMIN])),
    db: Session = Depends(get_db)
):
    """Review KYC application"""
    application = db.query(KYCApplication).filter(
        KYCApplication.application_id == application_id
    ).first()
    
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    application.status = review.status
    application.reviewed_by = current_admin["user_id"]
    application.reviewed_at = datetime.utcnow()
    
    if review.rejection_reason:
        application.rejection_reason = review.rejection_reason
    if review.additional_info_requested:
        application.additional_info_requested = review.additional_info_requested
    if review.risk_score:
        application.risk_score = review.risk_score
    
    db.commit()
    
    return {"message": "KYC application reviewed successfully"}

# Affiliate Manager Endpoints
@app.get("/api/v1/admin/affiliates")
async def get_affiliate_partners(
    status: Optional[AffiliateStatus] = None,
    partner_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_admin: Dict[str, Any] = Depends(check_role([AdminRole.AFFILIATE_MANAGER])),
    db: Session = Depends(get_db)
):
    """Get affiliate partners"""
    query = db.query(AffiliatePartner)
    
    if status:
        query = query.filter(AffiliatePartner.status == status)
    if partner_type:
        query = query.filter(AffiliatePartner.partner_type == partner_type)
    
    partners = query.order_by(AffiliatePartner.created_at.desc()).offset(offset).limit(limit).all()
    total = query.count()
    
    return {
        "partners": [
            {
                "partner_id": partner.partner_id,
                "partner_name": partner.partner_name,
                "partner_type": partner.partner_type,
                "contact_email": partner.contact_email,
                "referral_code": partner.referral_code,
                "commission_rate": float(partner.commission_rate),
                "total_referrals": partner.total_referrals,
                "total_commission_earned": float(partner.total_commission_earned),
                "status": partner.status,
                "created_at": partner.created_at.isoformat()
            }
            for partner in partners
        ],
        "total": total
    }

@app.post("/api/v1/admin/affiliates/{partner_id}/approve")
async def approve_affiliate_partner(
    partner_id: str,
    approval: AffiliateApproval,
    current_admin: Dict[str, Any] = Depends(check_role([AdminRole.AFFILIATE_MANAGER])),
    db: Session = Depends(get_db)
):
    """Approve/reject affiliate partner"""
    partner = db.query(AffiliatePartner).filter(AffiliatePartner.partner_id == partner_id).first()
    if not partner:
        raise HTTPException(status_code=404, detail="Partner not found")
    
    partner.status = approval.status
    partner.approved_by = current_admin["user_id"]
    partner.approved_at = datetime.utcnow()
    
    if approval.commission_rate:
        partner.commission_rate = approval.commission_rate
    
    db.commit()
    
    return {"message": "Affiliate partner status updated successfully"}

# Listing Manager Endpoints
@app.get("/api/v1/admin/listings")
async def get_token_listings(
    status: Optional[str] = None,
    blockchain: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_admin: Dict[str, Any] = Depends(check_role([AdminRole.LISTING_MANAGER])),
    db: Session = Depends(get_db)
):
    """Get token listing applications"""
    query = db.query(TokenListingApplication)
    
    if status:
        query = query.filter(TokenListingApplication.status == status)
    if blockchain:
        query = query.filter(TokenListingApplication.blockchain_network == blockchain)
    
    applications = query.order_by(TokenListingApplication.created_at.desc()).offset(offset).limit(limit).all()
    total = query.count()
    
    return {
        "applications": [
            {
                "application_id": app.application_id,
                "token_name": app.token_name,
                "token_symbol": app.token_symbol,
                "project_name": app.project_name,
                "blockchain_network": app.blockchain_network,
                "status": app.status,
                "listing_fee": float(app.listing_fee) if app.listing_fee else None,
                "listing_fee_paid": app.listing_fee_paid,
                "created_at": app.created_at.isoformat()
            }
            for app in applications
        ],
        "total": total
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "role-based-admin-system"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
