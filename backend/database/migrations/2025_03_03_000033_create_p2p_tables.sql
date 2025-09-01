-- P2P Trading System Tables

-- P2P Users table
CREATE TABLE IF NOT EXISTS p2p_users (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(50) UNIQUE NOT NULL,
    username VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20),
    country_code VARCHAR(3) NOT NULL,
    total_trades INTEGER DEFAULT 0,
    successful_trades INTEGER DEFAULT 0,
    total_volume DECIMAL(20,2) DEFAULT 0,
    average_rating DECIMAL(3,2) DEFAULT 0,
    total_ratings INTEGER DEFAULT 0,
    is_verified BOOLEAN DEFAULT FALSE,
    is_p2p_enabled BOOLEAN DEFAULT TRUE,
    is_blocked BOOLEAN DEFAULT FALSE,
    first_trade_at TIMESTAMP,
    last_active_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Payment Methods table
CREATE TABLE IF NOT EXISTS payment_methods (
    id SERIAL PRIMARY KEY,
    method_id VARCHAR(50) UNIQUE NOT NULL,
    user_id INTEGER REFERENCES p2p_users(id) ON DELETE CASCADE,
    method_type VARCHAR(20) NOT NULL,
    method_name VARCHAR(100) NOT NULL,
    account_details JSONB NOT NULL,
    supported_currencies JSONB,
    supported_countries JSONB,
    min_amount DECIMAL(20,2),
    max_amount DECIMAL(20,2),
    daily_limit DECIMAL(20,2),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- P2P Orders table
CREATE TABLE IF NOT EXISTS p2p_orders (
    id SERIAL PRIMARY KEY,
    order_id VARCHAR(50) UNIQUE NOT NULL,
    user_id INTEGER REFERENCES p2p_users(id) ON DELETE CASCADE,
    order_type VARCHAR(10) NOT NULL,
    cryptocurrency VARCHAR(10) NOT NULL,
    fiat_currency VARCHAR(3) NOT NULL,
    crypto_amount DECIMAL(30,8) NOT NULL,
    price_per_unit DECIMAL(20,8) NOT NULL,
    total_fiat_amount DECIMAL(20,2) NOT NULL,
    min_trade_amount DECIMAL(20,2),
    max_trade_amount DECIMAL(20,2),
    accepted_payment_methods JSONB,
    terms TEXT,
    auto_reply_message TEXT,
    allowed_countries JSONB,
    blocked_countries JSONB,
    status VARCHAR(20) DEFAULT 'active',
    expires_at TIMESTAMP,
    completed_trades INTEGER DEFAULT 0,
    total_volume DECIMAL(20,2) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- P2P Trades table
CREATE TABLE IF NOT EXISTS p2p_trades (
    id SERIAL PRIMARY KEY,
    trade_id VARCHAR(50) UNIQUE NOT NULL,
    order_id INTEGER REFERENCES p2p_orders(id) ON DELETE CASCADE,
    buyer_id INTEGER REFERENCES p2p_users(id) ON DELETE CASCADE,
    seller_id INTEGER REFERENCES p2p_users(id) ON DELETE CASCADE,
    crypto_amount DECIMAL(30,8) NOT NULL,
    fiat_amount DECIMAL(20,2) NOT NULL,
    price_per_unit DECIMAL(20,8) NOT NULL,
    payment_method_id INTEGER REFERENCES payment_methods(id),
    payment_reference VARCHAR(100),
    status VARCHAR(20) DEFAULT 'pending',
    payment_deadline TIMESTAMP NOT NULL,
    escrow_address VARCHAR(100),
    escrow_transaction_hash VARCHAR(100),
    release_transaction_hash VARCHAR(100),
    chat_room_id VARCHAR(50) NOT NULL,
    platform_fee DECIMAL(20,8) DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Trade Messages table
CREATE TABLE IF NOT EXISTS trade_messages (
    id SERIAL PRIMARY KEY,
    message_id VARCHAR(50) UNIQUE NOT NULL,
    trade_id INTEGER REFERENCES p2p_trades(id) ON DELETE CASCADE,
    sender_id INTEGER REFERENCES p2p_users(id) ON DELETE CASCADE,
    message_type VARCHAR(20) DEFAULT 'text',
    content TEXT NOT NULL,
    file_url VARCHAR(500),
    is_read BOOLEAN DEFAULT FALSE,
    is_system_message BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trade Disputes table
CREATE TABLE IF NOT EXISTS trade_disputes (
    id SERIAL PRIMARY KEY,
    dispute_id VARCHAR(50) UNIQUE NOT NULL,
    trade_id INTEGER REFERENCES p2p_trades(id) ON DELETE CASCADE,
    initiated_by INTEGER REFERENCES p2p_users(id) ON DELETE CASCADE,
    dispute_reason VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    evidence_urls JSONB,
    assigned_admin VARCHAR(50),
    admin_notes TEXT,
    status VARCHAR(20) DEFAULT 'open',
    resolution TEXT,
    winner VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP
);

-- P2P Feedback table
CREATE TABLE IF NOT EXISTS p2p_feedback (
    id SERIAL PRIMARY KEY,
    feedback_id VARCHAR(50) UNIQUE NOT NULL,
    trade_id INTEGER REFERENCES p2p_trades(id) ON DELETE CASCADE,
    from_user_id INTEGER REFERENCES p2p_users(id) ON DELETE CASCADE,
    to_user_id INTEGER REFERENCES p2p_users(id) ON DELETE CASCADE,
    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
    comment TEXT,
    communication_rating INTEGER CHECK (communication_rating >= 1 AND communication_rating <= 5),
    payment_speed_rating INTEGER CHECK (payment_speed_rating >= 1 AND payment_speed_rating <= 5),
    reliability_rating INTEGER CHECK (reliability_rating >= 1 AND reliability_rating <= 5),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- P2P Admin Actions table
CREATE TABLE IF NOT EXISTS p2p_admin_actions (
    id SERIAL PRIMARY KEY,
    action_id VARCHAR(50) UNIQUE NOT NULL,
    admin_id VARCHAR(50) NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    target_type VARCHAR(50) NOT NULL,
    target_id VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    details JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- P2P Settings table
CREATE TABLE IF NOT EXISTS p2p_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value JSONB NOT NULL,
    description TEXT,
    updated_by VARCHAR(50) NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_p2p_users_user_id ON p2p_users(user_id);
CREATE INDEX IF NOT EXISTS idx_p2p_users_country_code ON p2p_users(country_code);
CREATE INDEX IF NOT EXISTS idx_p2p_users_is_verified ON p2p_users(is_verified);
CREATE INDEX IF NOT EXISTS idx_p2p_users_is_blocked ON p2p_users(is_blocked);

CREATE INDEX IF NOT EXISTS idx_payment_methods_method_id ON payment_methods(method_id);
CREATE INDEX IF NOT EXISTS idx_payment_methods_user_id ON payment_methods(user_id);
CREATE INDEX IF NOT EXISTS idx_payment_methods_method_type ON payment_methods(method_type);

CREATE INDEX IF NOT EXISTS idx_p2p_orders_order_id ON p2p_orders(order_id);
CREATE INDEX IF NOT EXISTS idx_p2p_orders_user_id ON p2p_orders(user_id);
CREATE INDEX IF NOT EXISTS idx_p2p_orders_status ON p2p_orders(status);
CREATE INDEX IF NOT EXISTS idx_p2p_orders_cryptocurrency ON p2p_orders(cryptocurrency);
CREATE INDEX IF NOT EXISTS idx_p2p_orders_fiat_currency ON p2p_orders(fiat_currency);
CREATE INDEX IF NOT EXISTS idx_p2p_orders_order_type ON p2p_orders(order_type);

CREATE INDEX IF NOT EXISTS idx_p2p_trades_trade_id ON p2p_trades(trade_id);
CREATE INDEX IF NOT EXISTS idx_p2p_trades_order_id ON p2p_trades(order_id);
CREATE INDEX IF NOT EXISTS idx_p2p_trades_buyer_id ON p2p_trades(buyer_id);
CREATE INDEX IF NOT EXISTS idx_p2p_trades_seller_id ON p2p_trades(seller_id);
CREATE INDEX IF NOT EXISTS idx_p2p_trades_status ON p2p_trades(status);
CREATE INDEX IF NOT EXISTS idx_p2p_trades_chat_room_id ON p2p_trades(chat_room_id);

CREATE INDEX IF NOT EXISTS idx_trade_messages_message_id ON trade_messages(message_id);
CREATE INDEX IF NOT EXISTS idx_trade_messages_trade_id ON trade_messages(trade_id);
CREATE INDEX IF NOT EXISTS idx_trade_messages_sender_id ON trade_messages(sender_id);

CREATE INDEX IF NOT EXISTS idx_trade_disputes_dispute_id ON trade_disputes(dispute_id);
CREATE INDEX IF NOT EXISTS idx_trade_disputes_trade_id ON trade_disputes(trade_id);
CREATE INDEX IF NOT EXISTS idx_trade_disputes_status ON trade_disputes(status);
CREATE INDEX IF NOT EXISTS idx_trade_disputes_assigned_admin ON trade_disputes(assigned_admin);

CREATE INDEX IF NOT EXISTS idx_p2p_feedback_feedback_id ON p2p_feedback(feedback_id);
CREATE INDEX IF NOT EXISTS idx_p2p_feedback_trade_id ON p2p_feedback(trade_id);
CREATE INDEX IF NOT EXISTS idx_p2p_feedback_from_user_id ON p2p_feedback(from_user_id);
CREATE INDEX IF NOT EXISTS idx_p2p_feedback_to_user_id ON p2p_feedback(to_user_id);

CREATE INDEX IF NOT EXISTS idx_p2p_admin_actions_action_id ON p2p_admin_actions(action_id);
CREATE INDEX IF NOT EXISTS idx_p2p_admin_actions_admin_id ON p2p_admin_actions(admin_id);
CREATE INDEX IF NOT EXISTS idx_p2p_admin_actions_target_type ON p2p_admin_actions(target_type);

CREATE INDEX IF NOT EXISTS idx_p2p_settings_setting_key ON p2p_settings(setting_key);
