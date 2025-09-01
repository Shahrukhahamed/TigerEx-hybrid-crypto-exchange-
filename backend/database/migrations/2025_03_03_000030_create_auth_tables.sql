-- Authentication and Security Tables
-- TigerEx Advanced Authentication System

-- User Authentication Table
CREATE TABLE user_auth (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    salt VARCHAR(32) NOT NULL,
    
    -- 2FA Settings
    is_2fa_enabled BOOLEAN DEFAULT FALSE,
    totp_secret VARCHAR(32),
    backup_codes TEXT[], -- Array of backup codes
    
    -- Biometric Authentication
    biometric_enabled BOOLEAN DEFAULT FALSE,
    biometric_public_key TEXT,
    
    -- OAuth Providers
    google_id VARCHAR(100),
    apple_id VARCHAR(100),
    telegram_id VARCHAR(100),
    facebook_id VARCHAR(100),
    twitter_id VARCHAR(100),
    
    -- Security Settings
    login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    password_changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Session Management
    last_login_at TIMESTAMP,
    last_login_ip INET,
    current_session_id VARCHAR(100),
    
    -- Device Management
    trusted_devices JSONB DEFAULT '[]',
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Sessions Table
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) UNIQUE NOT NULL,
    user_id VARCHAR(50) NOT NULL REFERENCES user_auth(user_id),
    
    -- Session Info
    device_info JSONB,
    ip_address INET,
    user_agent TEXT,
    location JSONB, -- Country, city, etc.
    
    -- Session Status
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP NOT NULL,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Security
    csrf_token VARCHAR(100),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- API Keys Table
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    key_id VARCHAR(50) UNIQUE NOT NULL,
    user_id VARCHAR(50) NOT NULL REFERENCES user_auth(user_id),
    
    -- Key Info
    name VARCHAR(100) NOT NULL,
    api_key VARCHAR(64) UNIQUE NOT NULL,
    secret_key_hash VARCHAR(255) NOT NULL,
    
    -- Permissions
    permissions JSONB DEFAULT '[]', -- Array of permissions
    ip_whitelist INET[] DEFAULT '{}',
    
    -- Rate Limiting
    rate_limit_per_minute INTEGER DEFAULT 1000,
    rate_limit_per_hour INTEGER DEFAULT 10000,
    rate_limit_per_day INTEGER DEFAULT 100000,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    expires_at TIMESTAMP,
    
    -- Usage Stats
    last_used_at TIMESTAMP,
    total_requests BIGINT DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Security Events Table
CREATE TABLE security_events (
    id SERIAL PRIMARY KEY,
    event_id VARCHAR(50) UNIQUE NOT NULL,
    user_id VARCHAR(50) REFERENCES user_auth(user_id),
    
    -- Event Info
    event_type VARCHAR(50) NOT NULL, -- login, logout, password_change, 2fa_enable, etc.
    event_status VARCHAR(20) NOT NULL, -- success, failure, suspicious
    
    -- Context
    ip_address INET,
    user_agent TEXT,
    device_info JSONB,
    location JSONB,
    
    -- Details
    event_details JSONB,
    risk_score INTEGER DEFAULT 0, -- 0-100
    
    -- Response
    action_taken VARCHAR(100), -- none, account_locked, email_sent, etc.
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Password Reset Tokens
CREATE TABLE password_reset_tokens (
    id SERIAL PRIMARY KEY,
    token VARCHAR(100) UNIQUE NOT NULL,
    user_id VARCHAR(50) NOT NULL REFERENCES user_auth(user_id),
    
    -- Token Info
    expires_at TIMESTAMP NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMP,
    
    -- Security
    ip_address INET,
    user_agent TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Email Verification Tokens
CREATE TABLE email_verification_tokens (
    id SERIAL PRIMARY KEY,
    token VARCHAR(100) UNIQUE NOT NULL,
    user_id VARCHAR(50) NOT NULL REFERENCES user_auth(user_id),
    email VARCHAR(255) NOT NULL,
    
    -- Token Info
    expires_at TIMESTAMP NOT NULL,
    is_used BOOLEAN DEFAULT FALSE,
    used_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Device Trust Table
CREATE TABLE trusted_devices (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(100) UNIQUE NOT NULL,
    user_id VARCHAR(50) NOT NULL REFERENCES user_auth(user_id),
    
    -- Device Info
    device_name VARCHAR(100),
    device_type VARCHAR(50), -- mobile, desktop, tablet
    os_info VARCHAR(100),
    browser_info VARCHAR(100),
    
    -- Trust Info
    trusted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    last_used_at TIMESTAMP,
    
    -- Security
    device_fingerprint VARCHAR(255),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for Performance
CREATE INDEX idx_user_auth_email ON user_auth(email);
CREATE INDEX idx_user_auth_user_id ON user_auth(user_id);
CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_session_id ON user_sessions(session_id);
CREATE INDEX idx_user_sessions_expires_at ON user_sessions(expires_at);
CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_api_key ON api_keys(api_key);
CREATE INDEX idx_security_events_user_id ON security_events(user_id);
CREATE INDEX idx_security_events_event_type ON security_events(event_type);
CREATE INDEX idx_security_events_created_at ON security_events(created_at);
CREATE INDEX idx_password_reset_tokens_token ON password_reset_tokens(token);
CREATE INDEX idx_email_verification_tokens_token ON email_verification_tokens(token);
CREATE INDEX idx_trusted_devices_user_id ON trusted_devices(user_id);
CREATE INDEX idx_trusted_devices_device_id ON trusted_devices(device_id);

-- Update triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_user_auth_updated_at BEFORE UPDATE ON user_auth FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_api_keys_updated_at BEFORE UPDATE ON api_keys FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
