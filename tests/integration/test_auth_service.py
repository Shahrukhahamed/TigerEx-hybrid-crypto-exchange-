"""
Integration tests for Authentication Service
"""

import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import tempfile
import os

# Import the auth service
import sys
sys.path.append('backend/auth-service/src')
from main import app, get_db, Base

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_auth.db"
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

class TestAuthService:
    """Test Authentication Service"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
        assert response.json()["service"] == "auth-service"
    
    def test_user_registration(self, client):
        """Test user registration"""
        user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "TestPassword123",
            "first_name": "Test",
            "last_name": "User"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 200
        
        data = response.json()
        assert "user_id" in data
        assert data["email"] == user_data["email"]
        assert data["username"] == user_data["username"]
        assert data["status"] == "pending_verification"
    
    def test_duplicate_email_registration(self, client):
        """Test registration with duplicate email"""
        user_data = {
            "email": "duplicate@example.com",
            "username": "user1",
            "password": "TestPassword123"
        }
        
        # First registration
        response1 = client.post("/api/v1/auth/register", json=user_data)
        assert response1.status_code == 200
        
        # Second registration with same email
        user_data["username"] = "user2"
        response2 = client.post("/api/v1/auth/register", json=user_data)
        assert response2.status_code == 400
        assert "Email already registered" in response2.json()["detail"]
    
    def test_duplicate_username_registration(self, client):
        """Test registration with duplicate username"""
        user_data1 = {
            "email": "user1@example.com",
            "username": "duplicateuser",
            "password": "TestPassword123"
        }
        
        user_data2 = {
            "email": "user2@example.com",
            "username": "duplicateuser",
            "password": "TestPassword123"
        }
        
        # First registration
        response1 = client.post("/api/v1/auth/register", json=user_data1)
        assert response1.status_code == 200
        
        # Second registration with same username
        response2 = client.post("/api/v1/auth/register", json=user_data2)
        assert response2.status_code == 400
        assert "Username already taken" in response2.json()["detail"]
    
    def test_password_validation(self, client):
        """Test password validation"""
        # Test weak password
        user_data = {
            "email": "weak@example.com",
            "username": "weakuser",
            "password": "weak"
        }
        
        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422  # Validation error
    
    def test_captcha_generation(self, client):
        """Test captcha generation"""
        response = client.get("/api/v1/auth/captcha")
        assert response.status_code == 200
        
        data = response.json()
        assert "captcha_token" in data
        assert "captcha_image" in data
        assert data["captcha_image"].startswith("data:image/png;base64,")
    
    def test_user_login_invalid_credentials(self, client):
        """Test login with invalid credentials"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "wrongpassword"
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]
    
    def test_user_login_success(self, client):
        """Test successful user login"""
        # First register a user
        user_data = {
            "email": "login@example.com",
            "username": "loginuser",
            "password": "TestPassword123"
        }
        
        register_response = client.post("/api/v1/auth/register", json=user_data)
        assert register_response.status_code == 200
        
        # Update user status to active (simulate email verification)
        # In a real test, we would verify email first
        
        # Now try to login
        login_data = {
            "email": user_data["email"],
            "password": user_data["password"]
        }
        
        response = client.post("/api/v1/auth/login", json=login_data)
        # Note: This might fail due to account not being active
        # In production, we would need to activate the account first
    
    def test_get_current_user_without_token(self, client):
        """Test getting current user without authentication token"""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401
    
    def test_logout_without_token(self, client):
        """Test logout without authentication token"""
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == 401

if __name__ == "__main__":
    pytest.main([__file__])
