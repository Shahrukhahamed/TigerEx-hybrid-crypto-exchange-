"""
TigerEx Payment Gateway Service
Advanced payment processing system with debit/credit card support
Integrates payment methods from Binance, Bybit, OKX and global providers
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import hmac
import base64

import aiohttp
import asyncpg
import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, validator
import stripe
import paypal
from adyen import Adyen
import braintree
from square.client import Client as SquareClient
import razorpay
from payu import PayU
from mercadopago import SDK as MercadoPagoSDK
import alipay
import wechatpay
from coinbase_commerce.client import Client as CoinbaseClient
from bitpay import BitPayClient
import plaid
from dwolla import DwollaClient
import wise
from revolut import RevolutClient
from kafka import KafkaProducer
import boto3
from celery import Celery
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import tensorflow as tf

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(
    title="TigerEx Payment Gateway",
    description="Advanced payment processing with global card support",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Configuration
class Config:
    DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/tigerex")
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    KAFKA_BROKERS = os.getenv("KAFKA_BROKERS", "localhost:9092").split(",")
    
    # Payment Provider Keys
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
    STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
    STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
    
    PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID")
    PAYPAL_CLIENT_SECRET = os.getenv("PAYPAL_CLIENT_SECRET")
    PAYPAL_WEBHOOK_ID = os.getenv("PAYPAL_WEBHOOK_ID")
    
    ADYEN_API_KEY = os.getenv("ADYEN_API_KEY")
    ADYEN_MERCHANT_ACCOUNT = os.getenv("ADYEN_MERCHANT_ACCOUNT")
    ADYEN_HMAC_KEY = os.getenv("ADYEN_HMAC_KEY")
    
    SQUARE_ACCESS_TOKEN = os.getenv("SQUARE_ACCESS_TOKEN")
    SQUARE_APPLICATION_ID = os.getenv("SQUARE_APPLICATION_ID")
    SQUARE_WEBHOOK_SIGNATURE_KEY = os.getenv("SQUARE_WEBHOOK_SIGNATURE_KEY")
    
    RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
    RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")
    
    COINBASE_API_KEY = os.getenv("COINBASE_API_KEY")
    COINBASE_WEBHOOK_SECRET = os.getenv("COINBASE_WEBHOOK_SECRET")
    
    BITPAY_TOKEN = os.getenv("BITPAY_TOKEN")
    BITPAY_PRIVATE_KEY = os.getenv("BITPAY_PRIVATE_KEY")
    
    PLAID_CLIENT_ID = os.getenv("PLAID_CLIENT_ID")
    PLAID_SECRET = os.getenv("PLAID_SECRET")
    
    DWOLLA_KEY = os.getenv("DWOLLA_KEY")
    DWOLLA_SECRET = os.getenv("DWOLLA_SECRET")
    
    WISE_API_TOKEN = os.getenv("WISE_API_TOKEN")
    REVOLUT_API_KEY = os.getenv("REVOLUT_API_KEY")
    
    # Regional Payment Providers
    ALIPAY_APP_ID = os.getenv("ALIPAY_APP_ID")
    ALIPAY_PRIVATE_KEY = os.getenv("ALIPAY_PRIVATE_KEY")
    WECHAT_APP_ID = os.getenv("WECHAT_APP_ID")
    WECHAT_MCH_ID = os.getenv("WECHAT_MCH_ID")
    WECHAT_API_KEY = os.getenv("WECHAT_API_KEY")
    
    PAYU_MERCHANT_KEY = os.getenv("PAYU_MERCHANT_KEY")
    PAYU_SALT = os.getenv("PAYU_SALT")
    
    MERCADOPAGO_ACCESS_TOKEN = os.getenv("MERCADOPAGO_ACCESS_TOKEN")
    
    # Fraud Detection
    SIFT_API_KEY = os.getenv("SIFT_API_KEY")
    KOUNT_MERCHANT_ID = os.getenv("KOUNT_MERCHANT_ID")
    KOUNT_API_KEY = os.getenv("KOUNT_API_KEY")
    
    # Compliance
    CHAINALYSIS_API_KEY = os.getenv("CHAINALYSIS_API_KEY")
    ELLIPTIC_API_KEY = os.getenv("ELLIPTIC_API_KEY")

config = Config()

# Enums
class PaymentMethod(str, Enum):
    CREDIT_CARD = "CREDIT_CARD"
    DEBIT_CARD = "DEBIT_CARD"
    BANK_TRANSFER = "BANK_TRANSFER"
    PAYPAL = "PAYPAL"
    APPLE_PAY = "APPLE_PAY"
    GOOGLE_PAY = "GOOGLE_PAY"
    ALIPAY = "ALIPAY"
    WECHAT_PAY = "WECHAT_PAY"
    SEPA = "SEPA"
    ACH = "ACH"
    WIRE_TRANSFER = "WIRE_TRANSFER"
    CRYPTO = "CRYPTO"
    GIFT_CARD = "GIFT_CARD"
    VOUCHER = "VOUCHER"

class PaymentStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"
    DISPUTED = "DISPUTED"
    EXPIRED = "EXPIRED"

class PaymentProvider(str, Enum):
    STRIPE = "STRIPE"
    PAYPAL = "PAYPAL"
    ADYEN = "ADYEN"
    SQUARE = "SQUARE"
    RAZORPAY = "RAZORPAY"
    BRAINTREE = "BRAINTREE"
    COINBASE = "COINBASE"
    BITPAY = "BITPAY"
    PLAID = "PLAID"
    DWOLLA = "DWOLLA"
    WISE = "WISE"
    REVOLUT = "REVOLUT"
    ALIPAY = "ALIPAY"
    WECHAT = "WECHAT"
    PAYU = "PAYU"
    MERCADOPAGO = "MERCADOPAGO"

class TransactionType(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    PURCHASE = "PURCHASE"
    REFUND = "REFUND"
    TRANSFER = "TRANSFER"

# Data Models
@dataclass
class PaymentCard:
    id: str
    user_id: str
    card_type: str  # VISA, MASTERCARD, AMEX, etc.
    last_four: str
    expiry_month: int
    expiry_year: int
    cardholder_name: str
    billing_address: Dict[str, str]
    is_verified: bool
    is_default: bool
    provider_token: str
    fingerprint: str
    created_at: datetime
    updated_at: datetime

@dataclass
class BankAccount:
    id: str
    user_id: str
    account_type: str  # CHECKING, SAVINGS
    bank_name: str
    account_number_masked: str
    routing_number: str
    account_holder_name: str
    currency: str
    country: str
    is_verified: bool
    is_default: bool
    provider_token: str
    created_at: datetime
    updated_at: datetime

@dataclass
class PaymentTransaction:
    id: str
    user_id: str
    transaction_type: TransactionType
    payment_method: PaymentMethod
    payment_provider: PaymentProvider
    amount: Decimal
    currency: str
    fee: Decimal
    net_amount: Decimal
    status: PaymentStatus
    provider_transaction_id: str
    provider_reference: str
    metadata: Dict[str, Any]
    risk_score: float
    fraud_flags: List[str]
    compliance_status: str
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None

@dataclass
class PaymentIntent:
    id: str
    user_id: str
    amount: Decimal
    currency: str
    payment_method: PaymentMethod
    payment_provider: PaymentProvider
    client_secret: str
    status: PaymentStatus
    metadata: Dict[str, Any]
    expires_at: datetime
    created_at: datetime

# Pydantic Models
class CreatePaymentIntentRequest(BaseModel):
    amount: Decimal
    currency: str = "USD"
    payment_method: PaymentMethod
    payment_provider: Optional[PaymentProvider] = None
    metadata: Optional[Dict[str, Any]] = {}

class ConfirmPaymentRequest(BaseModel):
    payment_intent_id: str
    payment_method_id: Optional[str] = None
    card_details: Optional[Dict[str, Any]] = None
    billing_address: Optional[Dict[str, str]] = None

class AddPaymentMethodRequest(BaseModel):
    payment_method: PaymentMethod
    card_details: Optional[Dict[str, Any]] = None
    bank_details: Optional[Dict[str, Any]] = None
    billing_address: Optional[Dict[str, str]] = None

class WithdrawRequest(BaseModel):
    amount: Decimal
    currency: str
    payment_method_id: str
    destination_address: Optional[str] = None

# Database connection
async def get_db_connection():
    return await asyncpg.connect(config.DATABASE_URL)

# Redis connection
async def get_redis_connection():
    return await redis.from_url(config.REDIS_URL)

# Payment Gateway Manager
class PaymentGatewayManager:
    def __init__(self):
        self.providers = {}
        self.fraud_detector = self.load_fraud_detection_model()
        self.initialize_providers()
    
    def initialize_providers(self):
        """Initialize all payment providers"""
        try:
            # Stripe
            if config.STRIPE_SECRET_KEY:
                stripe.api_key = config.STRIPE_SECRET_KEY
                self.providers['stripe'] = StripeProvider()
                logger.info("Initialized Stripe provider")
            
            # PayPal
            if config.PAYPAL_CLIENT_ID:
                self.providers['paypal'] = PayPalProvider()
                logger.info("Initialized PayPal provider")
            
            # Adyen
            if config.ADYEN_API_KEY:
                self.providers['adyen'] = AdyenProvider()
                logger.info("Initialized Adyen provider")
            
            # Square
            if config.SQUARE_ACCESS_TOKEN:
                self.providers['square'] = SquareProvider()
                logger.info("Initialized Square provider")
            
            # Razorpay
            if config.RAZORPAY_KEY_ID:
                self.providers['razorpay'] = RazorpayProvider()
                logger.info("Initialized Razorpay provider")
            
            # Coinbase Commerce
            if config.COINBASE_API_KEY:
                self.providers['coinbase'] = CoinbaseProvider()
                logger.info("Initialized Coinbase provider")
            
            # Regional providers
            if config.ALIPAY_APP_ID:
                self.providers['alipay'] = AlipayProvider()
                logger.info("Initialized Alipay provider")
            
            if config.WECHAT_APP_ID:
                self.providers['wechat'] = WeChatProvider()
                logger.info("Initialized WeChat Pay provider")
            
            logger.info(f"Initialized {len(self.providers)} payment providers")
            
        except Exception as e:
            logger.error(f"Error initializing payment providers: {e}")
    
    def load_fraud_detection_model(self):
        """Load ML model for fraud detection"""
        try:
            return IsolationForest(contamination=0.1, random_state=42)
        except Exception as e:
            logger.error(f"Failed to load fraud detection model: {e}")
            return None
    
    async def create_payment_intent(self, request: CreatePaymentIntentRequest, user_id: str) -> PaymentIntent:
        """Create a payment intent"""
        intent_id = str(uuid.uuid4())
        
        # Select optimal provider
        provider_name = await self.select_optimal_provider(request.payment_method, request.currency, request.amount)
        provider = self.providers.get(provider_name)
        
        if not provider:
            raise HTTPException(status_code=400, detail=f"Provider {provider_name} not available")
        
        # Create intent with provider
        client_secret = await provider.create_payment_intent(intent_id, request.amount, request.currency)
        
        # Store in database
        intent = PaymentIntent(
            id=intent_id,
            user_id=user_id,
            amount=request.amount,
            currency=request.currency,
            payment_method=request.payment_method,
            payment_provider=PaymentProvider(provider_name.upper()),
            client_secret=client_secret,
            status=PaymentStatus.PENDING,
            metadata=request.metadata,
            expires_at=datetime.utcnow() + timedelta(hours=1),
            created_at=datetime.utcnow()
        )
        
        db = await get_db_connection()
        await db.execute("""
            INSERT INTO payment_intents (id, user_id, amount, currency, payment_method, 
                                       payment_provider, client_secret, status, metadata, 
                                       expires_at, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
        """, intent.id, intent.user_id, str(intent.amount), intent.currency, 
            intent.payment_method.value, intent.payment_provider.value, 
            intent.client_secret, intent.status.value, json.dumps(intent.metadata),
            intent.expires_at, intent.created_at)
        await db.close()
        
        return intent
    
    async def confirm_payment(self, request: ConfirmPaymentRequest, user_id: str) -> PaymentTransaction:
        """Confirm and process payment"""
        # Get payment intent
        db = await get_db_connection()
        row = await db.fetchrow("""
            SELECT * FROM payment_intents WHERE id = $1 AND user_id = $2
        """, request.payment_intent_id, user_id)
        await db.close()
        
        if not row:
            raise HTTPException(status_code=404, detail="Payment intent not found")
        
        intent = PaymentIntent(**dict(row))
        
        if intent.status != PaymentStatus.PENDING:
            raise HTTPException(status_code=400, detail="Payment intent already processed")
        
        if intent.expires_at < datetime.utcnow():
            raise HTTPException(status_code=400, detail="Payment intent expired")
        
        # Fraud detection
        risk_score = await self.assess_fraud_risk(intent, request, user_id)
        
        if risk_score > 0.8:
            raise HTTPException(status_code=400, detail="Transaction blocked due to high risk")
        
        # Process payment with provider
        provider = self.providers.get(intent.payment_provider.value.lower())
        result = await provider.confirm_payment(intent, request)
        
        # Create transaction record
        transaction = PaymentTransaction(
            id=str(uuid.uuid4()),
            user_id=user_id,
            transaction_type=TransactionType.DEPOSIT,
            payment_method=intent.payment_method,
            payment_provider=intent.payment_provider,
            amount=intent.amount,
            currency=intent.currency,
            fee=result.get('fee', Decimal('0')),
            net_amount=intent.amount - result.get('fee', Decimal('0')),
            status=PaymentStatus(result['status']),
            provider_transaction_id=result['transaction_id'],
            provider_reference=result.get('reference', ''),
            metadata=result.get('metadata', {}),
            risk_score=risk_score,
            fraud_flags=result.get('fraud_flags', []),
            compliance_status=result.get('compliance_status', 'PENDING'),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
            completed_at=datetime.utcnow() if result['status'] == 'COMPLETED' else None
        )
        
        # Save transaction
        await self.save_transaction(transaction)
        
        # Update user balance if successful
        if transaction.status == PaymentStatus.COMPLETED:
            await self.update_user_balance(user_id, transaction.net_amount, transaction.currency)
        
        return transaction
    
    async def select_optimal_provider(self, payment_method: PaymentMethod, currency: str, amount: Decimal) -> str:
        """Select optimal payment provider based on various factors"""
        # Provider scoring based on fees, success rates, and availability
        provider_scores = {}
        
        for provider_name, provider in self.providers.items():
            if await provider.supports_payment_method(payment_method, currency):
                score = await provider.calculate_score(payment_method, currency, amount)
                provider_scores[provider_name] = score
        
        if not provider_scores:
            raise HTTPException(status_code=400, detail="No suitable payment provider available")
        
        # Return provider with highest score
        return max(provider_scores, key=provider_scores.get)
    
    async def assess_fraud_risk(self, intent: PaymentIntent, request: ConfirmPaymentRequest, user_id: str) -> float:
        """Assess fraud risk using ML model"""
        try:
            # Extract features for fraud detection
            features = [
                float(intent.amount),
                len(intent.currency),
                intent.payment_method.value.__hash__() % 1000,
                datetime.utcnow().hour,
                datetime.utcnow().weekday(),
            ]
            
            if self.fraud_detector:
                features_array = np.array(features).reshape(1, -1)
                risk_score = abs(self.fraud_detector.decision_function(features_array)[0])
                return min(1.0, max(0.0, risk_score))
            else:
                # Fallback risk assessment
                risk_score = 0.1
                if intent.amount > Decimal('10000'):
                    risk_score += 0.3
                if intent.currency not in ['USD', 'EUR', 'GBP']:
                    risk_score += 0.2
                return min(1.0, risk_score)
                
        except Exception as e:
            logger.error(f"Error assessing fraud risk: {e}")
            return 0.5
    
    async def save_transaction(self, transaction: PaymentTransaction):
        """Save transaction to database"""
        db = await get_db_connection()
        await db.execute("""
            INSERT INTO payment_transactions (id, user_id, transaction_type, payment_method,
                                            payment_provider, amount, currency, fee, net_amount,
                                            status, provider_transaction_id, provider_reference,
                                            metadata, risk_score, fraud_flags, compliance_status,
                                            created_at, updated_at, completed_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18, $19)
        """, transaction.id, transaction.user_id, transaction.transaction_type.value,
            transaction.payment_method.value, transaction.payment_provider.value,
            str(transaction.amount), transaction.currency, str(transaction.fee),
            str(transaction.net_amount), transaction.status.value,
            transaction.provider_transaction_id, transaction.provider_reference,
            json.dumps(transaction.metadata), transaction.risk_score,
            json.dumps(transaction.fraud_flags), transaction.compliance_status,
            transaction.created_at, transaction.updated_at, transaction.completed_at)
        await db.close()
    
    async def update_user_balance(self, user_id: str, amount: Decimal, currency: str):
        """Update user balance"""
        db = await get_db_connection()
        await db.execute("""
            INSERT INTO user_balances (user_id, currency, balance, available_balance, locked_balance, updated_at)
            VALUES ($1, $2, $3, $3, 0, $4)
            ON CONFLICT (user_id, currency) 
            DO UPDATE SET 
                balance = user_balances.balance + $3,
                available_balance = user_balances.available_balance + $3,
                updated_at = $4
        """, user_id, currency, str(amount), datetime.utcnow())
        await db.close()

# Payment Provider Base Class
class PaymentProvider:
    def __init__(self):
        self.name = ""
        self.supported_methods = []
        self.supported_currencies = []
    
    async def supports_payment_method(self, method: PaymentMethod, currency: str) -> bool:
        return method in self.supported_methods and currency in self.supported_currencies
    
    async def calculate_score(self, method: PaymentMethod, currency: str, amount: Decimal) -> float:
        # Base scoring logic - override in subclasses
        return 0.5
    
    async def create_payment_intent(self, intent_id: str, amount: Decimal, currency: str) -> str:
        raise NotImplementedError
    
    async def confirm_payment(self, intent: PaymentIntent, request: ConfirmPaymentRequest) -> Dict[str, Any]:
        raise NotImplementedError

# Stripe Provider
class StripeProvider(PaymentProvider):
    def __init__(self):
        super().__init__()
        self.name = "stripe"
        self.supported_methods = [PaymentMethod.CREDIT_CARD, PaymentMethod.DEBIT_CARD, PaymentMethod.APPLE_PAY, PaymentMethod.GOOGLE_PAY]
        self.supported_currencies = ["USD", "EUR", "GBP", "CAD", "AUD", "JPY", "CHF", "SEK", "NOK", "DKK"]
    
    async def calculate_score(self, method: PaymentMethod, currency: str, amount: Decimal) -> float:
        score = 0.8  # High base score for Stripe
        if currency == "USD":
            score += 0.1
        if amount < Decimal('1000'):
            score += 0.1
        return min(1.0, score)
    
    async def create_payment_intent(self, intent_id: str, amount: Decimal, currency: str) -> str:
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Stripe uses cents
                currency=currency.lower(),
                metadata={'tigerex_intent_id': intent_id}
            )
            return intent.client_secret
        except Exception as e:
            logger.error(f"Stripe payment intent creation failed: {e}")
            raise HTTPException(status_code=500, detail="Payment intent creation failed")
    
    async def confirm_payment(self, intent: PaymentIntent, request: ConfirmPaymentRequest) -> Dict[str, Any]:
        try:
            # Confirm payment with Stripe
            stripe_intent = stripe.PaymentIntent.confirm(
                intent.client_secret.split('_secret_')[0],
                payment_method=request.payment_method_id
            )
            
            return {
                'status': 'COMPLETED' if stripe_intent.status == 'succeeded' else 'FAILED',
                'transaction_id': stripe_intent.id,
                'reference': stripe_intent.charges.data[0].id if stripe_intent.charges.data else '',
                'fee': Decimal(str(stripe_intent.charges.data[0].application_fee_amount or 0)) / 100,
                'metadata': {'stripe_intent_id': stripe_intent.id}
            }
        except Exception as e:
            logger.error(f"Stripe payment confirmation failed: {e}")
            return {
                'status': 'FAILED',
                'transaction_id': '',
                'reference': '',
                'fee': Decimal('0'),
                'metadata': {'error': str(e)}
            }

# PayPal Provider
class PayPalProvider(PaymentProvider):
    def __init__(self):
        super().__init__()
        self.name = "paypal"
        self.supported_methods = [PaymentMethod.PAYPAL]
        self.supported_currencies = ["USD", "EUR", "GBP", "CAD", "AUD", "JPY"]
    
    async def calculate_score(self, method: PaymentMethod, currency: str, amount: Decimal) -> float:
        score = 0.7
        if method == PaymentMethod.PAYPAL:
            score += 0.2
        return min(1.0, score)
    
    async def create_payment_intent(self, intent_id: str, amount: Decimal, currency: str) -> str:
        # PayPal implementation
        return f"paypal_intent_{intent_id}"
    
    async def confirm_payment(self, intent: PaymentIntent, request: ConfirmPaymentRequest) -> Dict[str, Any]:
        # PayPal confirmation implementation
        return {
            'status': 'COMPLETED',
            'transaction_id': f"paypal_txn_{uuid.uuid4()}",
            'reference': f"paypal_ref_{uuid.uuid4()}",
            'fee': intent.amount * Decimal('0.029'),  # 2.9% fee
            'metadata': {}
        }

# Additional providers (Adyen, Square, Razorpay, etc.) would follow similar patterns

# Adyen Provider
class AdyenProvider(PaymentProvider):
    def __init__(self):
        super().__init__()
        self.name = "adyen"
        self.supported_methods = [PaymentMethod.CREDIT_CARD, PaymentMethod.DEBIT_CARD, PaymentMethod.APPLE_PAY, PaymentMethod.GOOGLE_PAY]
        self.supported_currencies = ["USD", "EUR", "GBP", "CAD", "AUD", "JPY", "CHF", "SEK", "NOK", "DKK"]
        
        if config.ADYEN_API_KEY:
            self.client = Adyen()
            self.client.client.xapikey = config.ADYEN_API_KEY
            self.client.client.platform = "test"  # or "live"
    
    async def calculate_score(self, method: PaymentMethod, currency: str, amount: Decimal) -> float:
        score = 0.85  # High score for Adyen's global reach
        if currency in ["EUR", "GBP"]:
            score += 0.1
        return min(1.0, score)
    
    async def create_payment_intent(self, intent_id: str, amount: Decimal, currency: str) -> str:
        try:
            request = {
                "amount": {
                    "currency": currency,
                    "value": int(amount * 100)
                },
                "reference": intent_id,
                "merchantAccount": config.ADYEN_MERCHANT_ACCOUNT,
                "returnUrl": "https://tigerex.com/payment/return"
            }
            
            result = self.client.checkout.payments(request)
            return result.message.get('pspReference', '')
        except Exception as e:
            logger.error(f"Adyen payment intent creation failed: {e}")
            raise HTTPException(status_code=500, detail="Payment intent creation failed")

# Square Provider
class SquareProvider(PaymentProvider):
    def __init__(self):
        super().__init__()
        self.name = "square"
        self.supported_methods = [PaymentMethod.CREDIT_CARD, PaymentMethod.DEBIT_CARD, PaymentMethod.APPLE_PAY, PaymentMethod.GOOGLE_PAY]
        self.supported_currencies = ["USD", "CAD", "AUD", "GBP", "JPY"]
        
        if config.SQUARE_ACCESS_TOKEN:
            self.client = SquareClient(
                access_token=config.SQUARE_ACCESS_TOKEN,
                environment='sandbox'  # or 'production'
            )

# Razorpay Provider
class RazorpayProvider(PaymentProvider):
    def __init__(self):
        super().__init__()
        self.name = "razorpay"
        self.supported_methods = [PaymentMethod.CREDIT_CARD, PaymentMethod.DEBIT_CARD, PaymentMethod.BANK_TRANSFER]
        self.supported_currencies = ["INR"]
        
        if config.RAZORPAY_KEY_ID:
            self.client = razorpay.Client(auth=(config.RAZORPAY_KEY_ID, config.RAZORPAY_KEY_SECRET))

# Coinbase Provider
class CoinbaseProvider(PaymentProvider):
    def __init__(self):
        super().__init__()
        self.name = "coinbase"
        self.supported_methods = [PaymentMethod.CRYPTO]
        self.supported_currencies = ["USD", "EUR", "GBP", "BTC", "ETH", "USDC", "USDT"]
        
        if config.COINBASE_API_KEY:
            self.client = CoinbaseClient(api_key=config.COINBASE_API_KEY)

# Alipay Provider
class AlipayProvider(PaymentProvider):
    def __init__(self):
        super().__init__()
        self.name = "alipay"
        self.supported_methods = [PaymentMethod.ALIPAY]
        self.supported_currencies = ["CNY", "USD", "EUR"]

# WeChat Pay Provider
class WeChatProvider(PaymentProvider):
    def __init__(self):
        super().__init__()
        self.name = "wechat"
        self.supported_methods = [PaymentMethod.WECHAT_PAY]
        self.supported_currencies = ["CNY", "USD", "EUR"]

# Initialize payment gateway
payment_gateway = PaymentGatewayManager()

# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    # Implement JWT token validation
    return {"id": "user123", "role": "user"}

# API Endpoints

@app.post("/api/v1/payments/intent")
async def create_payment_intent(
    request: CreatePaymentIntentRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a payment intent"""
    try:
        intent = await payment_gateway.create_payment_intent(request, current_user["id"])
        return {
            "payment_intent_id": intent.id,
            "client_secret": intent.client_secret,
            "amount": str(intent.amount),
            "currency": intent.currency,
            "status": intent.status.value,
            "expires_at": intent.expires_at.isoformat()
        }
    except Exception as e:
        logger.error(f"Error creating payment intent: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/payments/confirm")
async def confirm_payment(
    request: ConfirmPaymentRequest,
    current_user: dict = Depends(get_current_user)
):
    """Confirm and process payment"""
    try:
        transaction = await payment_gateway.confirm_payment(request, current_user["id"])
        return {
            "transaction_id": transaction.id,
            "status": transaction.status.value,
            "amount": str(transaction.amount),
            "fee": str(transaction.fee),
            "net_amount": str(transaction.net_amount),
            "provider_transaction_id": transaction.provider_transaction_id,
            "risk_score": transaction.risk_score
        }
    except Exception as e:
        logger.error(f"Error confirming payment: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/payments/methods")
async def get_payment_methods(
    currency: str = "USD",
    current_user: dict = Depends(get_current_user)
):
    """Get available payment methods"""
    try:
        methods = []
        for provider_name, provider in payment_gateway.providers.items():
            for method in provider.supported_methods:
                if currency in provider.supported_currencies:
                    methods.append({
                        "method": method.value,
                        "provider": provider_name,
                        "currencies": provider.supported_currencies,
                        "fees": await get_provider_fees(provider_name, method, currency)
                    })
        
        return {"payment_methods": methods}
    except Exception as e:
        logger.error(f"Error getting payment methods: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/payments/methods")
async def add_payment_method(
    request: AddPaymentMethodRequest,
    current_user: dict = Depends(get_current_user)
):
    """Add a new payment method"""
    try:
        # Implementation for adding payment methods
        method_id = str(uuid.uuid4())
        
        # Store payment method securely
        if request.payment_method in [PaymentMethod.CREDIT_CARD, PaymentMethod.DEBIT_CARD]:
            # Tokenize card with provider
            token = await tokenize_card(request.card_details, request.billing_address)
            
            card = PaymentCard(
                id=method_id,
                user_id=current_user["id"],
                card_type=request.card_details.get("brand", "").upper(),
                last_four=request.card_details.get("last4", ""),
                expiry_month=request.card_details.get("exp_month", 0),
                expiry_year=request.card_details.get("exp_year", 0),
                cardholder_name=request.card_details.get("name", ""),
                billing_address=request.billing_address or {},
                is_verified=False,
                is_default=False,
                provider_token=token,
                fingerprint=generate_card_fingerprint(request.card_details),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            await save_payment_card(card)
        
        return {
            "payment_method_id": method_id,
            "status": "added",
            "requires_verification": True
        }
    except Exception as e:
        logger.error(f"Error adding payment method: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/payments/transactions")
async def get_transactions(
    limit: int = 50,
    offset: int = 0,
    status: Optional[PaymentStatus] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get user's payment transactions"""
    try:
        db = await get_db_connection()
        
        query = """
            SELECT * FROM payment_transactions 
            WHERE user_id = $1
        """
        params = [current_user["id"]]
        
        if status:
            query += " AND status = $2"
            params.append(status.value)
        
        query += " ORDER BY created_at DESC LIMIT $" + str(len(params) + 1) + " OFFSET $" + str(len(params) + 2)
        params.extend([limit, offset])
        
        rows = await db.fetch(query, *params)
        await db.close()
        
        transactions = [dict(row) for row in rows]
        return {"transactions": transactions}
    except Exception as e:
        logger.error(f"Error getting transactions: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/payments/withdraw")
async def withdraw_funds(
    request: WithdrawRequest,
    current_user: dict = Depends(get_current_user)
):
    """Withdraw funds to external payment method"""
    try:
        # Verify user has sufficient balance
        balance = await get_user_balance(current_user["id"], request.currency)
        if balance < request.amount:
            raise HTTPException(status_code=400, detail="Insufficient balance")
        
        # Create withdrawal transaction
        transaction_id = str(uuid.uuid4())
        
        # Process withdrawal based on payment method
        result = await process_withdrawal(
            transaction_id,
            current_user["id"],
            request.amount,
            request.currency,
            request.payment_method_id,
            request.destination_address
        )
        
        return {
            "transaction_id": transaction_id,
            "status": result["status"],
            "estimated_arrival": result.get("estimated_arrival"),
            "fee": str(result.get("fee", Decimal("0")))
        }
    except Exception as e:
        logger.error(f"Error processing withdrawal: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/payments/webhooks/{provider}")
async def handle_webhook(
    provider: str,
    request: Request
):
    """Handle payment provider webhooks"""
    try:
        body = await request.body()
        headers = dict(request.headers)
        
        # Verify webhook signature
        if not await verify_webhook_signature(provider, body, headers):
            raise HTTPException(status_code=400, detail="Invalid webhook signature")
        
        # Process webhook based on provider
        await process_webhook(provider, json.loads(body))
        
        return {"status": "processed"}
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Helper functions
async def get_provider_fees(provider_name: str, method: PaymentMethod, currency: str) -> Dict[str, Any]:
    """Get fees for a specific provider and payment method"""
    # Fee structure based on provider and method
    fee_structures = {
        "stripe": {
            PaymentMethod.CREDIT_CARD: {"percentage": 2.9, "fixed": 0.30},
            PaymentMethod.DEBIT_CARD: {"percentage": 2.9, "fixed": 0.30},
        },
        "paypal": {
            PaymentMethod.PAYPAL: {"percentage": 2.9, "fixed": 0.30},
        },
        "adyen": {
            PaymentMethod.CREDIT_CARD: {"percentage": 2.6, "fixed": 0.10},
        }
    }
    
    return fee_structures.get(provider_name, {}).get(method, {"percentage": 3.0, "fixed": 0.50})

async def tokenize_card(card_details: Dict[str, Any], billing_address: Dict[str, str]) -> str:
    """Tokenize card details with payment provider"""
    # Implementation for card tokenization
    return f"token_{uuid.uuid4()}"

def generate_card_fingerprint(card_details: Dict[str, Any]) -> str:
    """Generate unique fingerprint for card"""
    card_data = f"{card_details.get('number', '')}{card_details.get('exp_month', '')}{card_details.get('exp_year', '')}"
    return hashlib.sha256(card_data.encode()).hexdigest()[:16]

async def save_payment_card(card: PaymentCard):
    """Save payment card to database"""
    db = await get_db_connection()
    await db.execute("""
        INSERT INTO payment_cards (id, user_id, card_type, last_four, expiry_month, expiry_year,
                                 cardholder_name, billing_address, is_verified, is_default,
                                 provider_token, fingerprint, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14)
    """, card.id, card.user_id, card.card_type, card.last_four, card.expiry_month,
        card.expiry_year, card.cardholder_name, json.dumps(card.billing_address),
        card.is_verified, card.is_default, card.provider_token, card.fingerprint,
        card.created_at, card.updated_at)
    await db.close()

async def get_user_balance(user_id: str, currency: str) -> Decimal:
    """Get user's available balance"""
    db = await get_db_connection()
    row = await db.fetchrow("""
        SELECT available_balance FROM user_balances 
        WHERE user_id = $1 AND currency = $2
    """, user_id, currency)
    await db.close()
    
    return Decimal(row["available_balance"]) if row else Decimal("0")

async def process_withdrawal(transaction_id: str, user_id: str, amount: Decimal, 
                           currency: str, payment_method_id: str, destination_address: Optional[str]) -> Dict[str, Any]:
    """Process withdrawal transaction"""
    # Implementation for withdrawal processing
    return {
        "status": "PROCESSING",
        "estimated_arrival": datetime.utcnow() + timedelta(hours=24),
        "fee": amount * Decimal("0.01")  # 1% fee
    }

async def verify_webhook_signature(provider: str, body: bytes, headers: Dict[str, str]) -> bool:
    """Verify webhook signature from payment provider"""
    # Implementation for webhook signature verification
    return True

async def process_webhook(provider: str, payload: Dict[str, Any]):
    """Process webhook payload from payment provider"""
    # Implementation for webhook processing
    pass

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "providers": list(payment_gateway.providers.keys())
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8090)