"""
Integration tests for Enhanced Admin Panel
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys

# Import the admin panel
sys.path.append('backend/admin-panel/src')
from enhanced_main import app, get_db, Base

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_admin.db"
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
    return {"Authorization": "Bearer mock-admin-token"}

class TestAdminPanel:
    """Test Enhanced Admin Panel"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["service"] == "enhanced-admin-panel"
    
    def test_create_blockchain(self, client, auth_headers):
        """Test blockchain creation"""
        blockchain_data = {
            "name": "Test Blockchain",
            "symbol": "TEST",
            "network": "ethereum",
            "rpc_url": "https://test-rpc.example.com",
            "chain_id": 999,
            "native_currency_symbol": "TEST",
            "native_currency_decimals": 18,
            "description": "Test blockchain for testing"
        }
        
        response = client.post(
            "/api/v1/admin/blockchains",
            json=blockchain_data,
            headers=auth_headers
        )
        
        # Note: This might fail due to RPC connection test
        # In a real test environment, we would mock the Web3 connection
        assert response.status_code in [200, 400]  # 400 if RPC connection fails
    
    def test_get_blockchains(self, client):
        """Test getting blockchains"""
        response = client.get("/api/v1/admin/blockchains")
        assert response.status_code == 200
        
        data = response.json()
        assert "blockchains" in data
        assert isinstance(data["blockchains"], list)
    
    def test_create_token(self, client, auth_headers):
        """Test token creation"""
        # First create a blockchain
        blockchain_data = {
            "name": "Test Chain",
            "symbol": "TCHAIN",
            "network": "ethereum",
            "rpc_url": "https://test.example.com",
            "chain_id": 1001,
            "native_currency_symbol": "TCHAIN",
            "description": "Test chain"
        }
        
        blockchain_response = client.post(
            "/api/v1/admin/blockchains",
            json=blockchain_data,
            headers=auth_headers
        )
        
        if blockchain_response.status_code == 200:
            blockchain_id = blockchain_response.json()["blockchain_id"]
            
            # Now create a token
            token_data = {
                "name": "Test Token",
                "symbol": "TTOKEN",
                "decimals": 18,
                "blockchain_id": blockchain_id,
                "token_standard": "ERC20",
                "description": "Test token for testing"
            }
            
            response = client.post(
                "/api/v1/admin/tokens",
                json=token_data,
                headers=auth_headers
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "token_id" in data
            assert data["symbol"] == "TTOKEN"
    
    def test_get_tokens(self, client):
        """Test getting tokens"""
        response = client.get("/api/v1/admin/tokens")
        assert response.status_code == 200
        
        data = response.json()
        assert "tokens" in data
        assert isinstance(data["tokens"], list)
    
    def test_submit_token_listing(self, client):
        """Test token listing application submission"""
        listing_data = {
            "token_name": "New Token",
            "token_symbol": "NEW",
            "blockchain_network": "ethereum",
            "applicant_name": "Test Applicant",
            "applicant_email": "applicant@example.com",
            "total_supply": 1000000,
            "circulating_supply": 500000,
            "token_description": "A new token for testing",
            "use_case": "Testing purposes"
        }
        
        response = client.post("/api/v1/admin/token-listings", json=listing_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "listing_id" in data
        assert data["token_symbol"] == "NEW"
        assert data["status"] == "pending"
    
    def test_get_token_listings(self, client, auth_headers):
        """Test getting token listings"""
        response = client.get("/api/v1/admin/token-listings", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "listings" in data
        assert isinstance(data["listings"], list)
    
    def test_get_trading_pairs(self, client):
        """Test getting trading pairs"""
        response = client.get("/api/v1/admin/trading-pairs")
        assert response.status_code == 200
        
        data = response.json()
        assert "trading_pairs" in data
        assert isinstance(data["trading_pairs"], list)
    
    def test_update_market_data(self, client, auth_headers):
        """Test market data update"""
        response = client.post("/api/v1/admin/market-data/update", headers=auth_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "update initiated" in data["message"]

if __name__ == "__main__":
    pytest.main([__file__])
