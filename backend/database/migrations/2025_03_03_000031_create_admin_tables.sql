-- Admin Panel and Blockchain Management Tables
-- TigerEx Advanced Admin System

-- Admin Users Table (extends user_auth)
CREATE TABLE admin_users (
    id SERIAL PRIMARY KEY,
    admin_id VARCHAR(50) UNIQUE NOT NULL,
    user_id VARCHAR(50) NOT NULL, -- References user_auth.user_id
    
    -- Admin Info
    admin_level INTEGER NOT NULL DEFAULT 1, -- 1=basic, 2=senior, 3=super
    department VARCHAR(100),
    position VARCHAR(100),
    manager_id VARCHAR(50),
    
    -- Permissions
    permissions JSONB DEFAULT '[]',
    access_level INTEGER DEFAULT 1, -- 1-10 access levels
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    is_suspended BOOLEAN DEFAULT FALSE,
    suspension_reason TEXT,
    
    -- Performance Metrics
    tickets_handled INTEGER DEFAULT 0,
    avg_response_time DECIMAL(10,2) DEFAULT 0,
    customer_satisfaction DECIMAL(3,2) DEFAULT 0,
    
    -- Audit
    created_by VARCHAR(50),
    approved_by VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Custom Blockchains Table
CREATE TABLE custom_blockchains (
    id SERIAL PRIMARY KEY,
    blockchain_id VARCHAR(50) UNIQUE NOT NULL,
    
    -- Basic Info
    name VARCHAR(100) NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    description TEXT,
    
    -- Network Configuration
    chain_id INTEGER UNIQUE NOT NULL,
    network_type VARCHAR(20) NOT NULL, -- mainnet, testnet, devnet
    consensus_mechanism VARCHAR(50) NOT NULL, -- PoS, PoW, DPoS, etc.
    
    -- Technical Details
    block_time INTEGER NOT NULL, -- in seconds
    gas_limit BIGINT DEFAULT 30000000,
    gas_price_gwei DECIMAL(20,8) DEFAULT 20,
    
    -- URLs
    rpc_url VARCHAR(500),
    ws_url VARCHAR(500),
    explorer_url VARCHAR(500),
    
    -- Deployment Info
    deployment_status VARCHAR(20) DEFAULT 'pending', -- pending, deploying, deployed, failed
    deployment_config JSONB,
    docker_image VARCHAR(200),
    k8s_namespace VARCHAR(100),
    
    -- Domain and SSL
    domain_name VARCHAR(200),
    ssl_certificate TEXT,
    
    -- Performance Metrics
    current_block_height BIGINT DEFAULT 0,
    total_transactions BIGINT DEFAULT 0,
    active_validators INTEGER DEFAULT 0,
    
    -- Created by
    created_by VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Custom DEXs Table
CREATE TABLE custom_dexs (
    id SERIAL PRIMARY KEY,
    dex_id VARCHAR(50) UNIQUE NOT NULL,
    
    -- Basic Info
    name VARCHAR(100) NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    description TEXT,
    
    -- Blockchain Reference
    blockchain_id INTEGER REFERENCES custom_blockchains(id),
    
    -- Smart Contracts
    router_contract VARCHAR(100),
    factory_contract VARCHAR(100),
    weth_contract VARCHAR(100),
    multicall_contract VARCHAR(100),
    
    -- Fee Configuration
    swap_fee DECIMAL(5,4) DEFAULT 0.003, -- 0.3%
    protocol_fee DECIMAL(5,4) DEFAULT 0.0005, -- 0.05%
    
    -- Deployment Info
    deployment_status VARCHAR(20) DEFAULT 'pending',
    deployment_config JSONB,
    frontend_url VARCHAR(500),
    
    -- Domain and SSL
    domain_name VARCHAR(200),
    ssl_certificate TEXT,
    
    -- Performance Metrics
    total_volume DECIMAL(30,8) DEFAULT 0,
    total_trades BIGINT DEFAULT 0,
    active_pairs INTEGER DEFAULT 0,
    
    -- Created by
    created_by VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- White Label Exchanges Table
CREATE TABLE whitelabel_exchanges (
    id SERIAL PRIMARY KEY,
    exchange_id VARCHAR(50) UNIQUE NOT NULL,
    
    -- Basic Info
    name VARCHAR(100) NOT NULL,
    brand_name VARCHAR(100) NOT NULL,
    description TEXT,
    
    -- Exchange Type
    exchange_type VARCHAR(20) NOT NULL, -- cex, dex, hybrid
    
    -- Branding
    logo_url VARCHAR(500),
    primary_color VARCHAR(7), -- Hex color
    secondary_color VARCHAR(7),
    favicon_url VARCHAR(500),
    custom_css TEXT,
    
    -- Configuration
    supported_features JSONB DEFAULT '[]',
    trading_pairs JSONB DEFAULT '[]',
    payment_methods JSONB DEFAULT '[]',
    supported_countries JSONB DEFAULT '[]',
    
    -- Deployment Info
    deployment_status VARCHAR(20) DEFAULT 'pending',
    deployment_config JSONB,
    frontend_url VARCHAR(500),
    api_url VARCHAR(500),
    admin_url VARCHAR(500),
    
    -- Domain and SSL
    domain_name VARCHAR(200),
    ssl_certificate TEXT,
    
    -- Client Info
    client_id VARCHAR(50) NOT NULL,
    client_email VARCHAR(255) NOT NULL,
    client_company VARCHAR(200),
    
    -- Billing
    monthly_fee DECIMAL(20,2) DEFAULT 0,
    transaction_fee_percentage DECIMAL(5,4) DEFAULT 0,
    
    -- Created by
    created_by VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Block Explorers Table
CREATE TABLE block_explorers (
    id SERIAL PRIMARY KEY,
    explorer_id VARCHAR(50) UNIQUE NOT NULL,
    
    -- Basic Info
    name VARCHAR(100) NOT NULL,
    blockchain_id INTEGER REFERENCES custom_blockchains(id),
    
    -- Configuration
    api_url VARCHAR(500),
    frontend_url VARCHAR(500),
    websocket_url VARCHAR(500),
    
    -- Features
    supported_features JSONB DEFAULT '[]',
    
    -- Deployment Info
    deployment_status VARCHAR(20) DEFAULT 'pending',
    deployment_config JSONB,
    
    -- Domain and SSL
    domain_name VARCHAR(200),
    ssl_certificate TEXT,
    
    -- Created by
    created_by VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Wallet Systems Table
CREATE TABLE wallet_systems (
    id SERIAL PRIMARY KEY,
    wallet_id VARCHAR(50) UNIQUE NOT NULL,
    
    -- Basic Info
    name VARCHAR(100) NOT NULL,
    wallet_type VARCHAR(50) NOT NULL, -- hot, cold, custodial, non-custodial
    description TEXT,
    
    -- Configuration
    supported_blockchains JSONB DEFAULT '[]',
    supported_tokens JSONB DEFAULT '[]',
    security_features JSONB DEFAULT '[]',
    
    -- Deployment Info
    deployment_status VARCHAR(20) DEFAULT 'pending',
    deployment_config JSONB,
    
    -- Created by
    created_by VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Admin Activity Log
CREATE TABLE admin_activity_log (
    id SERIAL PRIMARY KEY,
    activity_id VARCHAR(50) UNIQUE NOT NULL,
    
    -- Admin Info
    admin_id VARCHAR(50) NOT NULL,
    admin_username VARCHAR(100),
    
    -- Activity Info
    activity_type VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50), -- blockchain, dex, exchange, etc.
    resource_id VARCHAR(50),
    
    -- Details
    action VARCHAR(100) NOT NULL,
    description TEXT,
    old_values JSONB,
    new_values JSONB,
    
    -- Context
    ip_address INET,
    user_agent TEXT,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System Settings Table
CREATE TABLE system_settings (
    id SERIAL PRIMARY KEY,
    setting_key VARCHAR(100) UNIQUE NOT NULL,
    setting_value JSONB NOT NULL,
    setting_type VARCHAR(50) NOT NULL, -- string, number, boolean, object, array
    description TEXT,
    
    -- Access Control
    is_public BOOLEAN DEFAULT FALSE,
    required_permission VARCHAR(100),
    
    -- Audit
    updated_by VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Deployment Jobs Table
CREATE TABLE deployment_jobs (
    id SERIAL PRIMARY KEY,
    job_id VARCHAR(50) UNIQUE NOT NULL,
    
    -- Job Info
    job_type VARCHAR(50) NOT NULL, -- blockchain, dex, exchange, explorer
    resource_id VARCHAR(50) NOT NULL,
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending', -- pending, running, completed, failed
    progress_percentage INTEGER DEFAULT 0,
    
    -- Execution Details
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    logs TEXT,
    
    -- Configuration
    deployment_config JSONB,
    
    -- Created by
    created_by VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_admin_users_admin_id ON admin_users(admin_id);
CREATE INDEX idx_admin_users_user_id ON admin_users(user_id);
CREATE INDEX idx_custom_blockchains_blockchain_id ON custom_blockchains(blockchain_id);
CREATE INDEX idx_custom_blockchains_chain_id ON custom_blockchains(chain_id);
CREATE INDEX idx_custom_dexs_dex_id ON custom_dexs(dex_id);
CREATE INDEX idx_custom_dexs_blockchain_id ON custom_dexs(blockchain_id);
CREATE INDEX idx_whitelabel_exchanges_exchange_id ON whitelabel_exchanges(exchange_id);
CREATE INDEX idx_whitelabel_exchanges_client_id ON whitelabel_exchanges(client_id);
CREATE INDEX idx_block_explorers_explorer_id ON block_explorers(explorer_id);
CREATE INDEX idx_block_explorers_blockchain_id ON block_explorers(blockchain_id);
CREATE INDEX idx_wallet_systems_wallet_id ON wallet_systems(wallet_id);
CREATE INDEX idx_admin_activity_log_admin_id ON admin_activity_log(admin_id);
CREATE INDEX idx_admin_activity_log_activity_type ON admin_activity_log(activity_type);
CREATE INDEX idx_admin_activity_log_created_at ON admin_activity_log(created_at);
CREATE INDEX idx_system_settings_setting_key ON system_settings(setting_key);
CREATE INDEX idx_deployment_jobs_job_id ON deployment_jobs(job_id);
CREATE INDEX idx_deployment_jobs_status ON deployment_jobs(status);

-- Update triggers
CREATE TRIGGER update_admin_users_updated_at BEFORE UPDATE ON admin_users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_custom_blockchains_updated_at BEFORE UPDATE ON custom_blockchains FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_custom_dexs_updated_at BEFORE UPDATE ON custom_dexs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_whitelabel_exchanges_updated_at BEFORE UPDATE ON whitelabel_exchanges FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_block_explorers_updated_at BEFORE UPDATE ON block_explorers FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_wallet_systems_updated_at BEFORE UPDATE ON wallet_systems FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_deployment_jobs_updated_at BEFORE UPDATE ON deployment_jobs FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_system_settings_updated_at BEFORE UPDATE ON system_settings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
