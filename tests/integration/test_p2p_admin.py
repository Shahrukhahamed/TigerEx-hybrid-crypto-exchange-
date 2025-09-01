"""
Integration tests for P2P Admin Dashboard
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys

# Import the P2P admin service
sys.path.append('backend/p2p-admin/src')
from main import app, get_db, Base

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_p2p_admin.db"
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
def admin_headers():
    """Mock admin authentication headers"""
    return {"Authorization": "Bearer mock-admin-token"}

class TestP2PAdmin:
    """Test P2P Admin Dashboard"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["service"] == "p2p-admin-dashboard"
    
    def test_get_dashboard_stats(self, client, admin_headers):
        """Test dashboard statistics"""
        response = client.get("/api/v1/p2p-admin/dashboard", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "overview" in data
        assert "growth" in data
        assert "top_cryptocurrencies" in data
        assert "top_countries" in data
        
        # Check overview structure
        overview = data["overview"]
        assert "total_users" in overview
        assert "active_orders" in overview
        assert "completed_trades" in overview
        assert "pending_disputes" in overview
        assert "total_volume_24h" in overview
        assert "total_fees_24h" in overview
    
    def test_get_p2p_users(self, client, admin_headers):
        """Test getting P2P users"""
        response = client.get("/api/v1/p2p-admin/users", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert "limit" in data
        assert "offset" in data
        assert isinstance(data["users"], list)
    
    def test_get_p2p_users_with_filters(self, client, admin_headers):
        """Test getting P2P users with filters"""
        response = client.get(
            "/api/v1/p2p-admin/users?country=US&verified=true&blocked=false&search=test",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "users" in data
        assert isinstance(data["users"], list)
    
    def test_get_p2p_trades(self, client, admin_headers):
        """Test getting P2P trades"""
        response = client.get("/api/v1/p2p-admin/trades", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "trades" in data
        assert "total" in data
        assert isinstance(data["trades"], list)
    
    def test_get_p2p_trades_with_filters(self, client, admin_headers):
        """Test getting P2P trades with filters"""
        response = client.get(
            "/api/v1/p2p-admin/trades?status=completed&cryptocurrency=BTC&min_amount=100&max_amount=10000",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "trades" in data
        assert isinstance(data["trades"], list)
    
    def test_get_disputes(self, client, admin_headers):
        """Test getting disputes"""
        response = client.get("/api/v1/p2p-admin/disputes", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "disputes" in data
        assert "total" in data
        assert isinstance(data["disputes"], list)
    
    def test_get_disputes_with_filters(self, client, admin_headers):
        """Test getting disputes with filters"""
        response = client.get(
            "/api/v1/p2p-admin/disputes?status=open&assigned_admin=admin_123",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "disputes" in data
        assert isinstance(data["disputes"], list)
    
    def test_resolve_dispute_invalid_id(self, client, admin_headers):
        """Test resolving invalid dispute"""
        resolution_data = {
            "resolution": "Buyer provided valid payment proof",
            "winner": "buyer",
            "admin_notes": "Payment was made on time"
        }
        
        response = client.post(
            "/api/v1/p2p-admin/disputes/INVALID_DISPUTE_ID/resolve",
            json=resolution_data,
            headers=admin_headers
        )
        
        assert response.status_code == 404
        assert "Dispute not found" in response.json()["detail"]
    
    def test_manage_user_invalid_id(self, client, admin_headers):
        """Test managing invalid user"""
        action_data = {
            "action": "block",
            "reason": "Suspicious activity",
            "duration_days": 30
        }
        
        response = client.post(
            "/api/v1/p2p-admin/users/INVALID_USER_ID/action",
            json=action_data,
            headers=admin_headers
        )
        
        assert response.status_code == 404
        assert "User not found" in response.json()["detail"]
    
    def test_get_p2p_orders(self, client, admin_headers):
        """Test getting P2P orders"""
        response = client.get("/api/v1/p2p-admin/orders", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "orders" in data
        assert "total" in data
        assert isinstance(data["orders"], list)
    
    def test_get_analytics_chart(self, client, admin_headers):
        """Test getting analytics chart"""
        response = client.get(
            "/api/v1/p2p-admin/analytics/chart?chart_type=trade_volume&period=30d",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "chart_data" in data
    
    def test_get_payment_methods(self, client, admin_headers):
        """Test getting payment methods"""
        response = client.get("/api/v1/p2p-admin/payment-methods", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "payment_methods" in data
        assert "total" in data
        assert isinstance(data["payment_methods"], list)
    
    def test_get_p2p_settings(self, client, admin_headers):
        """Test getting P2P settings"""
        response = client.get("/api/v1/p2p-admin/settings", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "settings" in data
        assert isinstance(data["settings"], list)
    
    def test_update_p2p_settings(self, client, admin_headers):
        """Test updating P2P settings"""
        settings_data = {
            "setting_key": "test_setting",
            "setting_value": {"test": "value"},
            "description": "Test setting for integration tests"
        }
        
        response = client.post(
            "/api/v1/p2p-admin/settings",
            json=settings_data,
            headers=admin_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["setting_key"] == "test_setting"
        assert "message" in data
    
    def test_get_admin_actions(self, client, admin_headers):
        """Test getting admin actions"""
        response = client.get("/api/v1/p2p-admin/admin-actions", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "admin_actions" in data
        assert "total" in data
        assert isinstance(data["admin_actions"], list)
    
    def test_get_admin_actions_with_filters(self, client, admin_headers):
        """Test getting admin actions with filters"""
        response = client.get(
            "/api/v1/p2p-admin/admin-actions?admin_id=admin_123&action_type=resolve_dispute&target_type=dispute",
            headers=admin_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "admin_actions" in data
        assert isinstance(data["admin_actions"], list)

if __name__ == "__main__":
    pytest.main([__file__])
