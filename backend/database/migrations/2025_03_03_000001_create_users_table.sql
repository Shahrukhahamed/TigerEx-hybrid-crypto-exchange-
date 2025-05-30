-- Create users table with comprehensive user management
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(20),
    country VARCHAR(3), -- ISO country code
    date_of_birth DATE,
    
    -- Verification status
    is_verified BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    phone_verified BOOLEAN DEFAULT FALSE,
    kyc_status VARCHAR(20) DEFAULT 'PENDING', -- PENDING, APPROVED, REJECTED, EXPIRED
    kyc_level INTEGER DEFAULT 0, -- 0: Basic, 1: Intermediate, 2: Advanced
    
    -- Security settings
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    two_factor_secret VARCHAR(32),
    backup_codes TEXT[], -- Array of backup codes
    password_reset_token VARCHAR(255),
    password_reset_expires TIMESTAMP,
    
    -- API access
    api_key_enabled BOOLEAN DEFAULT FALSE,
    api_rate_limit INTEGER DEFAULT 1000, -- requests per minute
    
    -- Trading permissions
    trading_enabled BOOLEAN DEFAULT TRUE,
    withdrawal_enabled BOOLEAN DEFAULT TRUE,
    margin_enabled BOOLEAN DEFAULT FALSE,
    futures_enabled BOOLEAN DEFAULT FALSE,
    options_enabled BOOLEAN DEFAULT FALSE,
    
    -- Account tiers and limits
    vip_level INTEGER DEFAULT 0,
    tier VARCHAR(20) DEFAULT 'BASIC', -- BASIC, SILVER, GOLD, PLATINUM, VIP
    daily_withdrawal_limit DECIMAL(20,8) DEFAULT 1000.00,
    monthly_withdrawal_limit DECIMAL(20,8) DEFAULT 10000.00,
    
    -- Referral system
    referral_code VARCHAR(20) UNIQUE,
    referred_by BIGINT REFERENCES users(id),
    referral_count INTEGER DEFAULT 0,
    referral_earnings DECIMAL(20,8) DEFAULT 0,
    
    -- Compliance and risk
    risk_score INTEGER DEFAULT 0, -- 0-100 risk score
    aml_status VARCHAR(20) DEFAULT 'CLEAR', -- CLEAR, FLAGGED, BLOCKED
    sanctions_check BOOLEAN DEFAULT FALSE,
    pep_check BOOLEAN DEFAULT FALSE, -- Politically Exposed Person
    
    -- Session management
    last_login TIMESTAMP,
    last_ip INET,
    login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    
    -- Preferences
    language VARCHAR(10) DEFAULT 'en',
    timezone VARCHAR(50) DEFAULT 'UTC',
    currency VARCHAR(10) DEFAULT 'USD',
    notifications_enabled BOOLEAN DEFAULT TRUE,
    marketing_emails BOOLEAN DEFAULT FALSE,
    
    -- Metadata
    user_agent TEXT,
    registration_ip INET,
    registration_source VARCHAR(50), -- WEB, MOBILE, API
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    
    -- Constraints
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$'),
    CONSTRAINT valid_username CHECK (username ~* '^[A-Za-z0-9_]{3,50}$'),
    CONSTRAINT valid_kyc_status CHECK (kyc_status IN ('PENDING', 'APPROVED', 'REJECTED', 'EXPIRED')),
    CONSTRAINT valid_tier CHECK (tier IN ('BASIC', 'SILVER', 'GOLD', 'PLATINUM', 'VIP')),
    CONSTRAINT valid_aml_status CHECK (aml_status IN ('CLEAR', 'FLAGGED', 'BLOCKED'))
);

-- Create indexes for performance
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_referral_code ON users(referral_code);
CREATE INDEX idx_users_kyc_status ON users(kyc_status);
CREATE INDEX idx_users_is_active ON users(is_active);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_last_login ON users(last_login);
CREATE INDEX idx_users_risk_score ON users(risk_score);

-- Create trigger for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments
COMMENT ON TABLE users IS 'Main users table with comprehensive user management features';
COMMENT ON COLUMN users.kyc_level IS '0: Basic (email), 1: Intermediate (phone+ID), 2: Advanced (full KYC)';
COMMENT ON COLUMN users.risk_score IS 'Risk score from 0-100, higher means more risky';
COMMENT ON COLUMN users.vip_level IS 'VIP level for fee discounts and special features';