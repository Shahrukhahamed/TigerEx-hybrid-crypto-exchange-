"""
Integration tests for P2P Trading System
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys

# Import the P2P trading service
sys.path.append('backend/p2p-trading/src')
from main import app, get_db, Base

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_p2p.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="module")
def setup_database():
    """Setup test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def client(setup_database):
    """Test client fixture"""
    return TestClient(app)

@pytest.fixture
def auth_headers():
    """Mock authentication headers"""
    return {"Authorization": "Bearer mock-user-token"}

class TestP2PTrading:
    """Test P2P Trading System"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["service"] == "p2p-trading"
    
    def test_create_payment_method(self, client, auth_headers):
        """Test payment method creation"""
        payment_method_data = {
            "method_type": "bank_transfer",
            "method_name": "My Bank Account",
            "account_details": {
                "bank_name": "Test Bank",
                "account_number": "1234567890",
                "routing_number": "123456789"
            },
            "supported_currencies": ["USD", "EUR"],
            "supported_countries": ["US", "GB"],
            "min_amount": 50,
            "max_amount": 10000,
            "daily_limit": 5000
        }
        
        response = client.post(
            "/api/v1/p2p/payment-methods",
            json=payment_method_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "method_id" in data
        assert data["method_type"] == "bank_transfer"
        assert data["method_name"] == "My Bank Account"
        assert data["status"] == "created"
    
    def test_get_payment_methods(self, client, auth_headers):
        """Test getting payment methods"""
        response = client.get("/api/v1/p2p/payment-methods", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "payment_methods" in data
        assert isinstance(data["payment_methods"], list)
    
    def test_create_p2p_order(self, client, auth_headers):
        """Test P2P order creation"""
        order_data = {
            "order_type": "sell",
            "cryptocurrency": "BTC",
            "fiat_currency": "USD",
            "crypto_amount": 0.1,
            "price_per_unit": 45000,
            "min_trade_amount": 500,
            "max_trade_amount": 4500,
            "accepted_payment_methods": ["bank_transfer", "paypal"],
            "terms": "Payment within 24 hours",
            "auto_reply_message": "Hello! Please follow the payment instructions.",
            "allowed_countries": ["US", "GB", "CA"],
            "blocked_countries": []
        }
        
        response = client.post(
            "/api/v1/p2p/orders",
            json=order_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "order_id" in data
        assert data["order_type"] == "sell"
        assert data["cryptocurrency"] == "BTC"
        assert data["fiat_currency"] == "USD"
        assert data["status"] == "active"
    
    def test_get_p2p_orders(self, client):
        """Test getting P2P orders"""
        response = client.get("/api/v1/p2p/orders")
        assert response.status_code == 200
        
        data = response.json()
        assert "orders" in data
        assert isinstance(data["orders"], list)
    
    def test_get_p2p_orders_with_filters(self, client):
        """Test getting P2P orders with filters"""
        response = client.get("/api/v1/p2p/orders?order_type=sell&cryptocurrency=BTC&fiat_currency=USD")
        assert response.status_code == 200
        
        data = response.json()
        assert "orders" in data
        assert isinstance(data["orders"], list)
    
    def test_get_user_trades(self, client, auth_headers):
        """Test getting user's trades"""
        response = client.get("/api/v1/p2p/trades", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "trades" in data
        assert isinstance(data["trades"], list)
    
    def test_create_p2p_trade_invalid_order(self, client, auth_headers):
        """Test creating P2P trade with invalid order"""
        trade_data = {
            "order_id": "INVALID_ORDER_ID",
            "fiat_amount": 1000,
            "payment_method_id": "1",
            "message": "I want to buy this"
        }
        
        response = client.post(
            "/api/v1/p2p/trades",
            json=trade_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "Order not found" in response.json()["detail"]
    
    def test_confirm_payment_invalid_trade(self, client, auth_headers):
        """Test confirming payment for invalid trade"""
        response = client.post(
            "/api/v1/p2p/trades/INVALID_TRADE_ID/confirm-payment",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "Trade not found" in response.json()["detail"]
    
    def test_release_crypto_invalid_trade(self, client, auth_headers):
        """Test releasing crypto for invalid trade"""
        response = client.post(
            "/api/v1/p2p/trades/INVALID_TRADE_ID/release",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "Trade not found" in response.json()["detail"]
    
    def test_create_dispute_invalid_trade(self, client, auth_headers):
        """Test creating dispute for invalid trade"""
        dispute_data = {
            "dispute_reason": "payment_not_received",
            "description": "The seller did not send payment as agreed",
            "evidence_urls": ["https://example.com/evidence1.jpg"]
        }
        
        response = client.post(
            "/api/v1/p2p/trades/INVALID_TRADE_ID/dispute",
            json=dispute_data,
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "Trade not found" in response.json()["detail"]

if __name__ == "__main__":
    pytest.main([__file__])
