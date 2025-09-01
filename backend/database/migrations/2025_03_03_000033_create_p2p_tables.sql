-- P2P Trading System Tables
-- TigerEx Advanced P2P Trading Platform

-- P2P Users Table (extends user_auth)
CREATE TABLE p2p_users (
    id SERIAL PRIMARY KEY,
    p2p_user_id VARCHAR(50) UNIQUE NOT NULL,
    user_id VARCHAR(50) NOT NULL, -- References user_auth.user_id
    
    -- P2P Profile
    display_name VARCHAR(100) NOT NULL,
    bio TEXT,
    avatar_url VARCHAR(500),
    
    -- Trading Stats
    total_orders INTEGER DEFAULT 0,
    completed_orders INTEGER DEFAULT 0,
    completion_rate DECIMAL(5,2) DEFAULT 0, -- Percentage
    avg_release_time INTEGER DEFAULT 0, -- in minutes
    avg_response_time INTEGER DEFAULT 0, -- in minutes
    
    -- Ratings
    positive_feedback INTEGER DEFAULT 0,
    negative_feedback INTEGER DEFAULT 0,
    total_feedback INTEGER DEFAULT 0,
    rating DECIMAL(3,2) DEFAULT 0, -- 0-5 stars
    
    -- Trading Volume (30 days)
    volume_30d_usd DECIMAL(20,2) DEFAULT 0,
    orders_30d INTEGER DEFAULT 0,
    
    -- Verification Status
    is_verified BOOLEAN DEFAULT FALSE,
    verification_level INTEGER DEFAULT 0, -- 0-5
    kyc_level VARCHAR(20) DEFAULT 'basic', -- basic, intermediate, advanced
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_online BOOLEAN DEFAULT FALSE,
    last_seen_at TIMESTAMP,
    
    -- Settings
    auto_reply_enabled BOOLEAN DEFAULT FALSE,
    auto_reply_message TEXT,
    preferred_languages JSONB DEFAULT '["en"]',
    timezone VARCHAR(50) DEFAULT 'UTC',
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- P2P Advertisements Table
CREATE TABLE p2p_advertisements (
    id SERIAL PRIMARY KEY,
    ad_id VARCHAR(50) UNIQUE NOT NULL,
    
    -- Advertiser
    advertiser_id VARCHAR(50) NOT NULL REFERENCES p2p_users(p2p_user_id),
    
    -- Advertisement Type
    ad_type VARCHAR(10) NOT NULL, -- buy, sell
    trade_type VARCHAR(20) NOT NULL, -- online, offline
    
    -- Asset Information
    asset VARCHAR(20) NOT NULL, -- BTC, ETH, USDT, etc.
    fiat_currency VARCHAR(3) NOT NULL, -- USD, EUR, CNY, etc.
    
    -- Pricing
    price_type VARCHAR(20) NOT NULL, -- fixed, floating
    fixed_price DECIMAL(20,8),
    margin_percentage DECIMAL(5,2), -- For floating price
    
    -- Limits
    min_order_amount DECIMAL(20,2) NOT NULL,
    max_order_amount DECIMAL(20,2) NOT NULL,
    available_amount DECIMAL(30,8) NOT NULL,
    
    -- Payment Methods
    payment_methods JSONB NOT NULL, -- Array of payment method IDs
    
    -- Terms and Conditions
    terms TEXT,
    auto_reply_message TEXT,
    
    -- Time Limits
    payment_time_limit INTEGER DEFAULT 15, -- minutes
    
    -- Filters
    min_completion_rate DECIMAL(5,2) DEFAULT 0,
    min_orders_completed INTEGER DEFAULT 0,
    verified_users_only BOOLEAN DEFAULT FALSE,
    
    -- Geographic Restrictions
    allowed_countries JSONB DEFAULT '[]', -- Empty = all countries
    blocked_countries JSONB DEFAULT '[]',
    
    -- Status
    status VARCHAR(20) DEFAULT 'active', -- active, paused, completed, cancelled
    is_visible BOOLEAN DEFAULT TRUE,
    
    -- Statistics
    total_orders INTEGER DEFAULT 0,
    completed_orders INTEGER DEFAULT 0,
    
    -- Audit
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

-- P2P Orders Table
CREATE TABLE p2p_orders (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(50) UNIQUE NOT NULL,
    
    -- Order Participants
    advertiser_id VARCHAR(50) NOT NULL REFERENCES p2p_users(p2p_user_id),
    buyer_id VARCHAR(50) NOT NULL REFERENCES p2p_users(p2p_user_id),
    seller_id VARCHAR(50) NOT NULL REFERENCES p2p_users(p2p_user_id),
    
    -- Advertisement Reference
    ad_id VARCHAR(50) NOT NULL REFERENCES p2p_advertisements(ad_id),
    
    -- Order Details
    order_type VARCHAR(10) NOT NULL, -- buy, sell
    asset VARCHAR(20) NOT NULL,
    fiat_currency VARCHAR(3) NOT NULL,
    
    -- Amounts
    crypto_amount DECIMAL(30,8) NOT NULL,
    fiat_amount DECIMAL(20,2) NOT NULL,
    unit_price DECIMAL(20,8) NOT NULL,
    
    -- Payment Information
    payment_method_id VARCHAR(50) NOT NULL,
    payment_details JSONB,
    
    -- Status Tracking
    status VARCHAR(20) DEFAULT 'pending', -- pending, paid, appealing, completed, cancelled, expired
    
    -- Time Tracking
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    payment_deadline TIMESTAMP,
    paid_at TIMESTAMP,
    released_at TIMESTAMP,
    completed_at TIMESTAMP,
    cancelled_at TIMESTAMP,
    
    -- Escrow Information
    escrow_address VARCHAR(100),
    escrow_tx_hash VARCHAR(100),
    release_tx_hash VARCHAR(100),
    
    -- Communication
    chat_room_id VARCHAR(50),
    
    -- Fees
    platform_fee DECIMAL(20,8) DEFAULT 0,
    
    -- Appeal Information
    appeal_id VARCHAR(50),
    appeal_reason TEXT,
    appealed_by VARCHAR(50),
    appealed_at TIMESTAMP,
    
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- P2P Payment Methods Table
CREATE TABLE p2p_payment_methods (
    id SERIAL PRIMARY KEY,
    method_id VARCHAR(50) UNIQUE NOT NULL,
    
    -- Method Info
    name VARCHAR(100) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL, -- BANK_TRANSFER, PAYPAL, ALIPAY, etc.
    category VARCHAR(50) NOT NULL, -- bank, digital_wallet, cash, etc.
    
    -- Supported Currencies
    supported_currencies JSONB NOT NULL, -- Array of currency codes
    
    -- Geographic Availability
    available_countries JSONB DEFAULT '[]', -- Empty = all countries
    
    -- Processing Information
    min_amount DECIMAL(20,2) DEFAULT 0,
    max_amount DECIMAL(20,2),
    processing_time_minutes INTEGER DEFAULT 0,
    
    -- Requirements
    requires_bank_account BOOLEAN DEFAULT FALSE,
    requires_phone_verification BOOLEAN DEFAULT FALSE,
    requires_id_verification BOOLEAN DEFAULT FALSE,
    
    -- Display Information
    icon_url VARCHAR(500),
    description TEXT,
    instructions TEXT,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- P2P User Payment Methods Table
CREATE TABLE p2p_user_payment_methods (
    id SERIAL PRIMARY KEY,
    user_method_id VARCHAR(50) UNIQUE NOT NULL,
    
    -- User and Method
    p2p_user_id VARCHAR(50) NOT NULL REFERENCES p2p_users(p2p_user_id),
    payment_method_id VARCHAR(50) NOT NULL REFERENCES p2p_payment_methods(method_id),
    
    -- Method Details
    account_name VARCHAR(200) NOT NULL,
    account_details JSONB NOT NULL, -- Account number, routing, etc.
    
    -- Verification
    is_verified BOOLEAN DEFAULT FALSE,
    verified_at TIMESTAMP,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(p2p_user_id, payment_method_id)
);

-- P2P Chat Messages Table
CREATE TABLE p2p_chat_messages (
    id SERIAL PRIMARY KEY,
    message_id VARCHAR(50) UNIQUE NOT NULL,
    
    -- Chat Room
    chat_room_id VARCHAR(50) NOT NULL,
    order_id VARCHAR(50) NOT NULL REFERENCES p2p_orders(order_id),
    
    -- Message Info
    sender_id VARCHAR(50) NOT NULL REFERENCES p2p_users(p2p_user_id),
    message_type VARCHAR(20) DEFAULT 'text', -- text, image, file, system
    content TEXT NOT NULL,
    
    -- File Attachments
    file_url VARCHAR(500),
    file_name VARCHAR(255),
    file_size INTEGER,
    
    -- Status
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
    
    -- System Messages
    is_system_message BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- P2P Feedback Table
CREATE TABLE p2p_feedback (
    id SERIAL PRIMARY KEY,
    feedback_id VARCHAR(50) UNIQUE NOT NULL,
    
    -- Order Reference
    order_id VARCHAR(50) NOT NULL REFERENCES p2p_orders(order_id),
    
    -- Feedback Participants
    reviewer_id VARCHAR(50) NOT NULL REFERENCES p2p_users(p2p_user_id),
    reviewee_id VARCHAR(50) NOT NULL REFERENCES p2p_users(p2p_user_id),
    
    -- Feedback Details
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    feedback_type VARCHAR(20) NOT NULL, -- positive, negative, neutral
    comment TEXT,
    
    -- Categories
    communication_rating INTEGER CHECK (communication_rating >= 1 AND communication_rating <= 5),
    speed_rating INTEGER CHECK (speed_rating >= 1 AND speed_rating <= 5),
    reliability_rating INTEGER CHECK (reliability_rating >= 1 AND reliability_rating <= 5),
    
    -- Status
    is_visible BOOLEAN DEFAULT TRUE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- P2P Appeals Table
CREATE TABLE p2p_appeals (
    id SERIAL PRIMARY KEY,
    appeal_id VARCHAR(50) UNIQUE NOT NULL,
    
    -- Order Reference
    order_id VARCHAR(50) NOT NULL REFERENCES p2p_orders(order_id),
    
    -- Appeal Info
    appellant_id VARCHAR(50) NOT NULL REFERENCES p2p_users(p2p_user_id),
    respondent_id VARCHAR(50) NOT NULL REFERENCES p2p_users(p2p_user_id),
    
    -- Appeal Details
    reason VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    evidence_urls JSONB DEFAULT '[]', -- Array of evidence file URLs
    
    -- Admin Assignment
    assigned_admin_id VARCHAR(50),
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending', -- pending, investigating, resolved, rejected
    
    -- Resolution
    resolution TEXT,
    resolution_action VARCHAR(50), -- release_crypto, return_crypto, partial_release, etc.
    resolved_by VARCHAR(50),
    resolved_at TIMESTAMP,
    
    -- Time Tracking
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- P2P Blacklist Table
CREATE TABLE p2p_blacklist (
    id SERIAL PRIMARY KEY,
    blacklist_id VARCHAR(50) UNIQUE NOT NULL,
    
    -- Users
    blocker_id VARCHAR(50) NOT NULL REFERENCES p2p_users(p2p_user_id),
    blocked_id VARCHAR(50) NOT NULL REFERENCES p2p_users(p2p_user_id),
    
    -- Reason
    reason VARCHAR(100),
    notes TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(blocker_id, blocked_id)
);

-- P2P Statistics Table
CREATE TABLE p2p_statistics (
    id SERIAL PRIMARY KEY,
    stat_date DATE NOT NULL,
    
    -- Trading Volume
    total_volume_usd DECIMAL(20,2) DEFAULT 0,
    total_orders INTEGER DEFAULT 0,
    completed_orders INTEGER DEFAULT 0,
    
    -- By Asset
    btc_volume DECIMAL(30,8) DEFAULT 0,
    eth_volume DECIMAL(30,8) DEFAULT 0,
    usdt_volume DECIMAL(30,8) DEFAULT 0,
    
    -- By Currency
    usd_volume DECIMAL(20,2) DEFAULT 0,
    eur_volume DECIMAL(20,2) DEFAULT 0,
    cny_volume DECIMAL(20,2) DEFAULT 0,
    
    -- User Activity
    active_users INTEGER DEFAULT 0,
    new_users INTEGER DEFAULT 0,
    
    -- Performance Metrics
    avg_completion_time INTEGER DEFAULT 0, -- minutes
    completion_rate DECIMAL(5,2) DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(stat_date)
);

-- P2P Settings Table
CREATE TABLE p2p_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value JSONB NOT NULL,
    description TEXT,
    
    updated_by VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for Performance
CREATE INDEX idx_p2p_users_user_id ON p2p_users(user_id);
CREATE INDEX idx_p2p_users_p2p_user_id ON p2p_users(p2p_user_id);
CREATE INDEX idx_p2p_users_is_active ON p2p_users(is_active);
CREATE INDEX idx_p2p_users_rating ON p2p_users(rating);

CREATE INDEX idx_p2p_advertisements_ad_id ON p2p_advertisements(ad_id);
CREATE INDEX idx_p2p_advertisements_advertiser_id ON p2p_advertisements(advertiser_id);
CREATE INDEX idx_p2p_advertisements_asset_currency ON p2p_advertisements(asset, fiat_currency);
CREATE INDEX idx_p2p_advertisements_status ON p2p_advertisements(status);
CREATE INDEX idx_p2p_advertisements_ad_type ON p2p_advertisements(ad_type);

CREATE INDEX idx_p2p_orders_order_id ON p2p_orders(order_id);
CREATE INDEX idx_p2p_orders_advertiser_id ON p2p_orders(advertiser_id);
CREATE INDEX idx_p2p_orders_buyer_id ON p2p_orders(buyer_id);
CREATE INDEX idx_p2p_orders_seller_id ON p2p_orders(seller_id);
CREATE INDEX idx_p2p_orders_status ON p2p_orders(status);
CREATE INDEX idx_p2p_orders_created_at ON p2p_orders(created_at);

CREATE INDEX idx_p2p_payment_methods_method_id ON p2p_payment_methods(method_id);
CREATE INDEX idx_p2p_payment_methods_code ON p2p_payment_methods(code);
CREATE INDEX idx_p2p_payment_methods_is_active ON p2p_payment_methods(is_active);

CREATE INDEX idx_p2p_user_payment_methods_p2p_user_id ON p2p_user_payment_methods(p2p_user_id);
CREATE INDEX idx_p2p_user_payment_methods_payment_method_id ON p2p_user_payment_methods(payment_method_id);

CREATE INDEX idx_p2p_chat_messages_chat_room_id ON p2p_chat_messages(chat_room_id);
CREATE INDEX idx_p2p_chat_messages_order_id ON p2p_chat_messages(order_id);
CREATE INDEX idx_p2p_chat_messages_sender_id ON p2p_chat_messages(sender_id);
CREATE INDEX idx_p2p_chat_messages_created_at ON p2p_chat_messages(created_at);

CREATE INDEX idx_p2p_feedback_order_id ON p2p_feedback(order_id);
CREATE INDEX idx_p2p_feedback_reviewer_id ON p2p_feedback(reviewer_id);
CREATE INDEX idx_p2p_feedback_reviewee_id ON p2p_feedback(reviewee_id);

CREATE INDEX idx_p2p_appeals_appeal_id ON p2p_appeals(appeal_id);
CREATE INDEX idx_p2p_appeals_order_id ON p2p_appeals(order_id);
CREATE INDEX idx_p2p_appeals_status ON p2p_appeals(status);
CREATE INDEX idx_p2p_appeals_assigned_admin_id ON p2p_appeals(assigned_admin_id);

CREATE INDEX idx_p2p_blacklist_blocker_id ON p2p_blacklist(blocker_id);
CREATE INDEX idx_p2p_blacklist_blocked_id ON p2p_blacklist(blocked_id);

CREATE INDEX idx_p2p_statistics_stat_date ON p2p_statistics(stat_date);

-- Update triggers
CREATE TRIGGER update_p2p_users_updated_at BEFORE UPDATE ON p2p_users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_p2p_advertisements_updated_at BEFORE UPDATE ON p2p_advertisements FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_p2p_orders_updated_at BEFORE UPDATE ON p2p_orders FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_p2p_payment_methods_updated_at BEFORE UPDATE ON p2p_payment_methods FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_p2p_user_payment_methods_updated_at BEFORE UPDATE ON p2p_user_payment_methods FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_p2p_appeals_updated_at BEFORE UPDATE ON p2p_appeals FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_p2p_settings_updated_at BEFORE UPDATE ON p2p_settings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
