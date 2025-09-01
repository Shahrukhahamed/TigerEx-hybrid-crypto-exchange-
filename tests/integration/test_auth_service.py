"""
Integration tests for TigerEx Authentication Service
Tests authentication, 2FA, OAuth, and security features
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch
import httpx
from fastapi.testclient import TestClient

# Mock the auth service app
@pytest.fixture
def auth_client():
    """Create test client for auth service"""
    from backend.auth_service.src.main import app
    return TestClient(app)

@pytest.fixture
def test_user_data():
    """Test user data"""
    return {
        "email": "test@tigerex.com",
        "password": "SecurePassword123!",
        "username": "testuser",
        "first_name": "Test",
        "last_name": "User"
    }

class TestUserRegistration:
    """Test user registration functionality"""
    
    def test_register_new_user(self, auth_client, test_user_data):
        """Test successful user registration"""
        response = auth_client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code == 201
        data = response.json()
        assert "user_id" in data
        assert data["email"] == test_user_data["email"]
        assert data["status"] == "pending_verification"
        assert "password" not in data  # Password should not be returned
    
    def test_register_duplicate_email(self, auth_client, test_user_data):
        """Test registration with duplicate email"""
        # Register first user
        auth_client.post("/api/v1/auth/register", json=test_user_data)
        
        # Try to register with same email
        response = auth_client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    def test_register_invalid_email(self, auth_client, test_user_data):
        """Test registration with invalid email"""
        test_user_data["email"] = "invalid-email"
        response = auth_client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code == 422
    
    def test_register_weak_password(self, auth_client, test_user_data):
        """Test registration with weak password"""
        test_user_data["password"] = "123"
        response = auth_client.post("/api/v1/auth/register", json=test_user_data)
        
        assert response.status_code == 400
        assert "password" in response.json()["detail"].lower()

class TestUserLogin:
    """Test user login functionality"""
    
    @pytest.fixture(autouse=True)
    def setup_user(self, auth_client, test_user_data):
        """Setup a verified user for login tests"""
        # Register user
        auth_client.post("/api/v1/auth/register", json=test_user_data)
        
        # Mock email verification
        with patch('backend.auth_service.src.main.verify_email') as mock_verify:
            mock_verify.return_value = True
            auth_client.post("/api/v1/auth/verify-email", json={
                "email": test_user_data["email"],
                "verification_code": "123456"
            })
    
    def test_login_success(self, auth_client, test_user_data):
        """Test successful login"""
        response = auth_client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert "user" in data
        assert data["user"]["email"] == test_user_data["email"]
    
    def test_login_invalid_credentials(self, auth_client, test_user_data):
        """Test login with invalid credentials"""
        response = auth_client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
        assert "invalid credentials" in response.json()["detail"].lower()
    
    def test_login_unverified_user(self, auth_client):
        """Test login with unverified user"""
        # Register new user without verification
        unverified_user = {
            "email": "unverified@tigerex.com",
            "password": "SecurePassword123!",
            "username": "unverified"
        }
        auth_client.post("/api/v1/auth/register", json=unverified_user)
        
        response = auth_client.post("/api/v1/auth/login", json={
            "email": unverified_user["email"],
            "password": unverified_user["password"]
        })
        
        assert response.status_code == 403
        assert "email not verified" in response.json()["detail"].lower()
    
    def test_login_rate_limiting(self, auth_client, test_user_data):
        """Test login rate limiting after failed attempts"""
        # Make multiple failed login attempts
        for _ in range(6):  # Assuming 5 attempts limit
            auth_client.post("/api/v1/auth/login", json={
                "email": test_user_data["email"],
                "password": "wrongpassword"
            })
        
        # Next attempt should be rate limited
        response = auth_client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        
        assert response.status_code == 429
        assert "too many attempts" in response.json()["detail"].lower()

class TestTwoFactorAuthentication:
    """Test 2FA functionality"""
    
    @pytest.fixture(autouse=True)
    def setup_user_with_2fa(self, auth_client, test_user_data):
        """Setup user with 2FA enabled"""
        # Register and verify user
        auth_client.post("/api/v1/auth/register", json=test_user_data)
        
        # Login to get token
        login_response = auth_client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        self.access_token = login_response.json()["access_token"]
        
        # Enable 2FA
        with patch('pyotp.random_base32') as mock_secret:
            mock_secret.return_value = "JBSWY3DPEHPK3PXP"
            response = auth_client.post("/api/v1/auth/2fa/enable", 
                headers={"Authorization": f"Bearer {self.access_token}"})
            self.totp_secret = response.json()["secret"]
    
    def test_enable_2fa(self, auth_client):
        """Test enabling 2FA"""
        with patch('pyotp.random_base32') as mock_secret:
            mock_secret.return_value = "JBSWY3DPEHPK3PXP"
            response = auth_client.post("/api/v1/auth/2fa/enable",
                headers={"Authorization": f"Bearer {self.access_token}"})
        
        assert response.status_code == 200
        data = response.json()
        assert "secret" in data
        assert "qr_code" in data
        assert "backup_codes" in data
    
    def test_verify_2fa_setup(self, auth_client):
        """Test verifying 2FA setup"""
        with patch('pyotp.TOTP.verify') as mock_verify:
            mock_verify.return_value = True
            response = auth_client.post("/api/v1/auth/2fa/verify-setup", 
                json={"totp_code": "123456"},
                headers={"Authorization": f"Bearer {self.access_token}"})
        
        assert response.status_code == 200
        assert response.json()["message"] == "2FA enabled successfully"
    
    def test_login_with_2fa(self, auth_client, test_user_data):
        """Test login with 2FA enabled"""
        # First step - login with password
        response = auth_client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert data["requires_2fa"] == True
        assert "temp_token" in data
        
        # Second step - verify 2FA
        with patch('pyotp.TOTP.verify') as mock_verify:
            mock_verify.return_value = True
            response = auth_client.post("/api/v1/auth/2fa/verify", json={
                "temp_token": data["temp_token"],
                "totp_code": "123456"
            })
        
        assert response.status_code == 200
        final_data = response.json()
        assert "access_token" in final_data
        assert "refresh_token" in final_data

class TestOAuthIntegration:
    """Test OAuth integration"""
    
    def test_google_oauth_initiate(self, auth_client):
        """Test Google OAuth initiation"""
        response = auth_client.get("/api/v1/auth/oauth/google")
        
        assert response.status_code == 200
        data = response.json()
        assert "auth_url" in data
        assert "state" in data
        assert "google.com" in data["auth_url"]
    
    def test_google_oauth_callback(self, auth_client):
        """Test Google OAuth callback"""
        with patch('httpx.AsyncClient.post') as mock_post:
            # Mock Google token response
            mock_post.return_value.json.return_value = {
                "access_token": "mock_access_token",
                "id_token": "mock_id_token"
            }
            
            with patch('jwt.decode') as mock_decode:
                # Mock JWT decode
                mock_decode.return_value = {
                    "sub": "google_user_id",
                    "email": "user@gmail.com",
                    "name": "Test User",
                    "picture": "https://example.com/avatar.jpg"
                }
                
                response = auth_client.post("/api/v1/auth/oauth/google/callback", json={
                    "code": "auth_code",
                    "state": "csrf_state"
                })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "user" in data
        assert data["user"]["email"] == "user@gmail.com"
    
    def test_apple_oauth_callback(self, auth_client):
        """Test Apple OAuth callback"""
        with patch('jwt.decode') as mock_decode:
            mock_decode.return_value = {
                "sub": "apple_user_id",
                "email": "user@icloud.com",
                "name": "Test User"
            }
            
            response = auth_client.post("/api/v1/auth/oauth/apple/callback", json={
                "id_token": "mock_apple_id_token",
                "user": {
                    "name": {"firstName": "Test", "lastName": "User"},
                    "email": "user@icloud.com"
                }
            })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "user@icloud.com"

class TestTokenManagement:
    """Test JWT token management"""
    
    @pytest.fixture(autouse=True)
    def setup_authenticated_user(self, auth_client, test_user_data):
        """Setup authenticated user"""
        # Register and login user
        auth_client.post("/api/v1/auth/register", json=test_user_data)
        
        login_response = auth_client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        
        self.tokens = login_response.json()
        self.access_token = self.tokens["access_token"]
        self.refresh_token = self.tokens["refresh_token"]
    
    def test_token_refresh(self, auth_client):
        """Test token refresh"""
        response = auth_client.post("/api/v1/auth/refresh", json={
            "refresh_token": self.refresh_token
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["access_token"] != self.access_token  # New token
    
    def test_token_validation(self, auth_client):
        """Test token validation"""
        response = auth_client.get("/api/v1/auth/me",
            headers={"Authorization": f"Bearer {self.access_token}"})
        
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "email" in data
    
    def test_invalid_token(self, auth_client):
        """Test invalid token handling"""
        response = auth_client.get("/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid_token"})
        
        assert response.status_code == 401
    
    def test_expired_token(self, auth_client):
        """Test expired token handling"""
        # Mock expired token
        with patch('jwt.decode') as mock_decode:
            from jwt.exceptions import ExpiredSignatureError
            mock_decode.side_effect = ExpiredSignatureError("Token expired")
            
            response = auth_client.get("/api/v1/auth/me",
                headers={"Authorization": f"Bearer {self.access_token}"})
        
        assert response.status_code == 401
        assert "expired" in response.json()["detail"].lower()
    
    def test_logout(self, auth_client):
        """Test user logout"""
        response = auth_client.post("/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {self.access_token}"})
        
        assert response.status_code == 200
        
        # Token should be invalidated
        response = auth_client.get("/api/v1/auth/me",
            headers={"Authorization": f"Bearer {self.access_token}"})
        
        assert response.status_code == 401

class TestPasswordManagement:
    """Test password management features"""
    
    @pytest.fixture(autouse=True)
    def setup_user(self, auth_client, test_user_data):
        """Setup verified user"""
        auth_client.post("/api/v1/auth/register", json=test_user_data)
        self.user_email = test_user_data["email"]
    
    def test_password_reset_request(self, auth_client):
        """Test password reset request"""
        with patch('backend.auth_service.src.main.send_email') as mock_send:
            response = auth_client.post("/api/v1/auth/password-reset", json={
                "email": self.user_email
            })
        
        assert response.status_code == 200
        assert "reset link sent" in response.json()["message"].lower()
        mock_send.assert_called_once()
    
    def test_password_reset_confirm(self, auth_client):
        """Test password reset confirmation"""
        # Mock valid reset token
        with patch('backend.auth_service.src.main.verify_reset_token') as mock_verify:
            mock_verify.return_value = {"user_id": "test_user_id", "email": self.user_email}
            
            response = auth_client.post("/api/v1/auth/password-reset/confirm", json={
                "token": "valid_reset_token",
                "new_password": "NewSecurePassword123!"
            })
        
        assert response.status_code == 200
        assert "password updated" in response.json()["message"].lower()
    
    def test_password_change(self, auth_client, test_user_data):
        """Test password change for authenticated user"""
        # Login first
        login_response = auth_client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        access_token = login_response.json()["access_token"]
        
        # Change password
        response = auth_client.post("/api/v1/auth/change-password", 
            json={
                "current_password": test_user_data["password"],
                "new_password": "NewSecurePassword123!"
            },
            headers={"Authorization": f"Bearer {access_token}"})
        
        assert response.status_code == 200
        
        # Test login with new password
        response = auth_client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": "NewSecurePassword123!"
        })
        
        assert response.status_code == 200

class TestSecurityFeatures:
    """Test security features"""
    
    def test_device_fingerprinting(self, auth_client, test_user_data):
        """Test device fingerprinting"""
        # Register user
        auth_client.post("/api/v1/auth/register", json=test_user_data)
        
        # Login with device fingerprint
        response = auth_client.post("/api/v1/auth/login", 
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"]
            },
            headers={
                "User-Agent": "Mozilla/5.0 (Test Browser)",
                "X-Device-Fingerprint": "test_fingerprint_123"
            })
        
        assert response.status_code == 200
        
        # Check if device is tracked
        access_token = response.json()["access_token"]
        response = auth_client.get("/api/v1/auth/devices",
            headers={"Authorization": f"Bearer {access_token}"})
        
        assert response.status_code == 200
        devices = response.json()["devices"]
        assert len(devices) > 0
        assert devices[0]["fingerprint"] == "test_fingerprint_123"
    
    def test_suspicious_activity_detection(self, auth_client, test_user_data):
        """Test suspicious activity detection"""
        # Register user
        auth_client.post("/api/v1/auth/register", json=test_user_data)
        
        # Simulate login from different locations rapidly
        locations = [
            {"country": "US", "city": "New York"},
            {"country": "CN", "city": "Beijing"},
            {"country": "RU", "city": "Moscow"}
        ]
        
        for location in locations:
            with patch('backend.auth_service.src.main.get_location_from_ip') as mock_location:
                mock_location.return_value = location
                
                response = auth_client.post("/api/v1/auth/login", json={
                    "email": test_user_data["email"],
                    "password": test_user_data["password"]
                })
                
                # Should trigger security alert after suspicious pattern
                if location["country"] == "RU":
                    assert response.status_code == 403
                    assert "suspicious activity" in response.json()["detail"].lower()
    
    def test_session_management(self, auth_client, test_user_data):
        """Test session management"""
        # Register and login
        auth_client.post("/api/v1/auth/register", json=test_user_data)
        
        login_response = auth_client.post("/api/v1/auth/login", json={
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        })
        
        access_token = login_response.json()["access_token"]
        
        # Get active sessions
        response = auth_client.get("/api/v1/auth/sessions",
            headers={"Authorization": f"Bearer {access_token}"})
        
        assert response.status_code == 200
        sessions = response.json()["sessions"]
        assert len(sessions) > 0
        
        # Terminate all other sessions
        response = auth_client.post("/api/v1/auth/sessions/terminate-all",
            headers={"Authorization": f"Bearer {access_token}"})
        
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_concurrent_login_attempts():
    """Test handling of concurrent login attempts"""
    # This would test race conditions and concurrent access
    pass

@pytest.mark.asyncio 
async def test_performance_under_load():
    """Test authentication performance under load"""
    # This would test performance with many concurrent requests
    pass

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
