-- TigerEx Enhanced Admin Roles and Permissions System
-- Comprehensive role-based access control for all admin types

-- Admin Roles Table
CREATE TABLE admin_roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    level INTEGER NOT NULL DEFAULT 1, -- 1=lowest, 10=highest (super admin)
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Admin Users Table
CREATE TABLE admin_users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    role_id INTEGER REFERENCES admin_roles(id),
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    two_factor_enabled BOOLEAN DEFAULT FALSE,
    two_factor_secret VARCHAR(255),
    last_login_at TIMESTAMP,
    last_login_ip INET,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Admin Permissions Table
CREATE TABLE admin_permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(150) NOT NULL,
    description TEXT,
    category VARCHAR(50) NOT NULL, -- user_management, trading_control, system_admin, etc.
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Role Permissions Junction Table
CREATE TABLE admin_role_permissions (
    id SERIAL PRIMARY KEY,
    role_id INTEGER REFERENCES admin_roles(id) ON DELETE CASCADE,
    permission_id INTEGER REFERENCES admin_permissions(id) ON DELETE CASCADE,
    granted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    granted_by INTEGER REFERENCES admin_users(id),
    UNIQUE(role_id, permission_id)
);

-- Admin Activity Logs
CREATE TABLE admin_activity_logs (
    id SERIAL PRIMARY KEY,
    admin_user_id INTEGER REFERENCES admin_users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(50), -- user, trading_pair, order, etc.
    resource_id VARCHAR(100),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- KYC Management Tables
CREATE TABLE kyc_applications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    application_type VARCHAR(20) NOT NULL, -- individual, corporate
    status VARCHAR(20) DEFAULT 'pending', -- pending, under_review, approved, rejected, expired
    tier_requested INTEGER DEFAULT 1, -- 1, 2, 3 (verification levels)
    tier_approved INTEGER DEFAULT 0,
    
    -- Personal Information
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    date_of_birth DATE,
    nationality VARCHAR(50),
    country_of_residence VARCHAR(50),
    address_line1 VARCHAR(255),
    address_line2 VARCHAR(255),
    city VARCHAR(100),
    state_province VARCHAR(100),
    postal_code VARCHAR(20),
    
    -- Corporate Information (if applicable)
    company_name VARCHAR(255),
    company_registration_number VARCHAR(100),
    company_address TEXT,
    business_type VARCHAR(100),
    
    -- Document Information
    documents JSONB, -- Array of document objects
    selfie_url VARCHAR(500),
    
    -- Review Information
    reviewed_by INTEGER REFERENCES admin_users(id),
    reviewed_at TIMESTAMP,
    rejection_reason TEXT,
    notes TEXT,
    
    -- Risk Assessment
    risk_score INTEGER DEFAULT 0, -- 0-100
    risk_factors JSONB,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Customer Support System
CREATE TABLE support_tickets (
    id SERIAL PRIMARY KEY,
    ticket_number VARCHAR(20) UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id),
    assigned_to INTEGER REFERENCES admin_users(id),
    category VARCHAR(50) NOT NULL, -- account, trading, technical, billing, etc.
    priority VARCHAR(20) DEFAULT 'medium', -- low, medium, high, urgent
    status VARCHAR(20) DEFAULT 'open', -- open, in_progress, waiting_user, resolved, closed
    subject VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    
    -- SLA Tracking
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    first_response_at TIMESTAMP,
    resolved_at TIMESTAMP,
    closed_at TIMESTAMP,
    
    -- Metadata
    tags JSONB,
    internal_notes TEXT,
    satisfaction_rating INTEGER, -- 1-5 stars
    satisfaction_feedback TEXT
);

-- Support Ticket Messages
CREATE TABLE support_ticket_messages (
    id SERIAL PRIMARY KEY,
    ticket_id INTEGER REFERENCES support_tickets(id) ON DELETE CASCADE,
    sender_type VARCHAR(20) NOT NULL, -- user, admin
    sender_id INTEGER NOT NULL, -- user_id or admin_user_id
    message TEXT NOT NULL,
    attachments JSONB,
    is_internal BOOLEAN DEFAULT FALSE, -- internal admin notes
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trading Control & Risk Management
CREATE TABLE trading_controls (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    symbol VARCHAR(20),
    control_type VARCHAR(30) NOT NULL, -- position_limit, daily_loss_limit, etc.
    limit_value DECIMAL(20,8) NOT NULL,
    current_value DECIMAL(20,8) DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    set_by INTEGER REFERENCES admin_users(id),
    reason TEXT,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- System Maintenance & Monitoring
CREATE TABLE system_maintenance (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    maintenance_type VARCHAR(30) NOT NULL, -- scheduled, emergency, upgrade
    status VARCHAR(20) DEFAULT 'scheduled', -- scheduled, in_progress, completed, cancelled
    affects_trading BOOLEAN DEFAULT FALSE,
    affects_deposits BOOLEAN DEFAULT FALSE,
    affects_withdrawals BOOLEAN DEFAULT FALSE,
    
    scheduled_start TIMESTAMP NOT NULL,
    scheduled_end TIMESTAMP NOT NULL,
    actual_start TIMESTAMP,
    actual_end TIMESTAMP,
    
    created_by INTEGER REFERENCES admin_users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Token Listing Management
CREATE TABLE token_listing_applications (
    id SERIAL PRIMARY KEY,
    application_number VARCHAR(20) UNIQUE NOT NULL,
    applicant_email VARCHAR(255) NOT NULL,
    applicant_name VARCHAR(255) NOT NULL,
    company_name VARCHAR(255),
    
    -- Token Information
    token_name VARCHAR(100) NOT NULL,
    token_symbol VARCHAR(20) NOT NULL,
    contract_address VARCHAR(100),
    blockchain VARCHAR(50) NOT NULL,
    token_type VARCHAR(20) NOT NULL, -- ERC20, BEP20, etc.
    total_supply DECIMAL(30,0),
    circulating_supply DECIMAL(30,0),
    
    -- Project Information
    website_url VARCHAR(500),
    whitepaper_url VARCHAR(500),
    github_url VARCHAR(500),
    social_links JSONB,
    project_description TEXT,
    
    -- Listing Details
    listing_type VARCHAR(20) NOT NULL, -- spot, futures, both
    requested_pairs JSONB, -- Array of quote currencies
    listing_fee DECIMAL(20,8),
    market_making_commitment DECIMAL(20,8),
    
    -- Review Process
    status VARCHAR(20) DEFAULT 'submitted', -- submitted, under_review, approved, rejected
    reviewed_by INTEGER REFERENCES admin_users(id),
    reviewed_at TIMESTAMP,
    approval_notes TEXT,
    rejection_reason TEXT,
    
    -- Compliance
    kyc_completed BOOLEAN DEFAULT FALSE,
    legal_opinion_provided BOOLEAN DEFAULT FALSE,
    audit_report_provided BOOLEAN DEFAULT FALSE,
    compliance_score INTEGER DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Partner & Regional Partner Management
CREATE TABLE partners (
    id SERIAL PRIMARY KEY,
    partner_type VARCHAR(20) NOT NULL, -- regional, institutional, technology, liquidity
    company_name VARCHAR(255) NOT NULL,
    contact_name VARCHAR(255) NOT NULL,
    contact_email VARCHAR(255) NOT NULL,
    contact_phone VARCHAR(20),
    
    -- Geographic Information
    country VARCHAR(50),
    region VARCHAR(100),
    coverage_areas JSONB, -- Array of countries/regions
    
    -- Partnership Details
    partnership_level VARCHAR(20) DEFAULT 'standard', -- standard, premium, exclusive
    commission_rate DECIMAL(5,4) DEFAULT 0.0000, -- Revenue sharing rate
    volume_commitment DECIMAL(20,8),
    
    -- Status & Verification
    status VARCHAR(20) DEFAULT 'pending', -- pending, active, suspended, terminated
    verified_at TIMESTAMP,
    verified_by INTEGER REFERENCES admin_users(id),
    
    -- Contract Information
    contract_start_date DATE,
    contract_end_date DATE,
    contract_document_url VARCHAR(500),
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Affiliate & Referral System
CREATE TABLE affiliate_programs (
    id SERIAL PRIMARY KEY,
    program_name VARCHAR(100) NOT NULL,
    program_type VARCHAR(20) NOT NULL, -- referral, affiliate, influencer
    commission_structure JSONB NOT NULL, -- Tiered commission rates
    minimum_payout DECIMAL(20,8) DEFAULT 10.00,
    payout_frequency VARCHAR(20) DEFAULT 'monthly', -- daily, weekly, monthly
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE affiliates (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    program_id INTEGER REFERENCES affiliate_programs(id),
    referral_code VARCHAR(20) UNIQUE NOT NULL,
    status VARCHAR(20) DEFAULT 'active', -- active, suspended, terminated
    
    -- Performance Metrics
    total_referrals INTEGER DEFAULT 0,
    active_referrals INTEGER DEFAULT 0,
    total_commission_earned DECIMAL(20,8) DEFAULT 0,
    total_commission_paid DECIMAL(20,8) DEFAULT 0,
    
    -- KYC for Affiliates
    kyc_status VARCHAR(20) DEFAULT 'pending',
    tax_information JSONB,
    
    approved_by INTEGER REFERENCES admin_users(id),
    approved_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- White Label Solutions
CREATE TABLE white_label_exchanges (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES users(id),
    exchange_name VARCHAR(100) NOT NULL,
    domain_name VARCHAR(255) UNIQUE NOT NULL,
    subdomain VARCHAR(100) UNIQUE NOT NULL, -- client.tigerex.com
    
    -- Branding
    logo_url VARCHAR(500),
    primary_color VARCHAR(7), -- Hex color
    secondary_color VARCHAR(7),
    custom_css TEXT,
    
    -- Features Enabled
    features_enabled JSONB NOT NULL, -- Array of enabled features
    trading_pairs JSONB, -- Allowed trading pairs
    supported_languages JSONB,
    
    -- Configuration
    fee_structure JSONB, -- Custom fee structure
    kyc_requirements JSONB,
    withdrawal_limits JSONB,
    
    -- Technical
    api_key VARCHAR(100) UNIQUE NOT NULL,
    api_secret VARCHAR(255) NOT NULL,
    webhook_url VARCHAR(500),
    
    -- Status
    status VARCHAR(20) DEFAULT 'pending', -- pending, active, suspended, terminated
    deployed_at TIMESTAMP,
    last_activity_at TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Blockchain Integration Management
CREATE TABLE custom_blockchains (
    id SERIAL PRIMARY KEY,
    blockchain_name VARCHAR(100) NOT NULL,
    blockchain_type VARCHAR(20) NOT NULL, -- evm, substrate, cosmos, custom
    chain_id INTEGER UNIQUE,
    
    -- Network Configuration
    rpc_url VARCHAR(500) NOT NULL,
    ws_url VARCHAR(500),
    explorer_url VARCHAR(500),
    
    -- Native Currency
    native_currency_name VARCHAR(50) NOT NULL,
    native_currency_symbol VARCHAR(10) NOT NULL,
    native_currency_decimals INTEGER DEFAULT 18,
    
    -- Technical Details
    consensus_mechanism VARCHAR(30), -- pos, pow, poa, etc.
    block_time_seconds INTEGER,
    gas_price_gwei DECIMAL(20,8),
    
    -- Integration Status
    status VARCHAR(20) DEFAULT 'pending', -- pending, testing, active, deprecated
    integrated_by INTEGER REFERENCES admin_users(id),
    integrated_at TIMESTAMP,
    
    -- Monitoring
    last_block_number BIGINT,
    last_sync_at TIMESTAMP,
    is_syncing BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- AI Maintenance System
CREATE TABLE ai_maintenance_tasks (
    id SERIAL PRIMARY KEY,
    task_type VARCHAR(50) NOT NULL, -- performance_optimization, security_scan, etc.
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(20) DEFAULT 'pending', -- pending, running, completed, failed
    
    -- Task Configuration
    parameters JSONB,
    schedule_cron VARCHAR(100), -- Cron expression for recurring tasks
    
    -- Execution Details
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    execution_time_ms INTEGER,
    
    -- Results
    result_summary TEXT,
    result_data JSONB,
    recommendations JSONB,
    
    -- Actions Taken
    actions_taken JSONB,
    manual_review_required BOOLEAN DEFAULT FALSE,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert Default Admin Roles
INSERT INTO admin_roles (name, display_name, description, level) VALUES
('super_admin', 'Super Administrator', 'Full system access and control', 10),
('kyc_admin', 'KYC Administrator', 'Manage user verification and compliance', 7),
('support_admin', 'Customer Support Manager', 'Manage customer support operations', 6),
('trading_admin', 'Trading Administrator', 'Manage trading pairs and market operations', 8),
('compliance_admin', 'Compliance Officer', 'Regulatory compliance and risk management', 8),
('listing_admin', 'Listing Manager', 'Manage token listing applications', 7),
('partner_admin', 'Partner Manager', 'Manage partnerships and affiliates', 6),
('technical_admin', 'Technical Administrator', 'System maintenance and monitoring', 9),
('finance_admin', 'Finance Manager', 'Financial operations and reporting', 7),
('marketing_admin', 'Marketing Manager', 'Marketing campaigns and analytics', 5);

-- Insert Default Permissions
INSERT INTO admin_permissions (name, display_name, category) VALUES
-- User Management
('users.view', 'View Users', 'user_management'),
('users.edit', 'Edit Users', 'user_management'),
('users.suspend', 'Suspend Users', 'user_management'),
('users.verify', 'Verify Users', 'user_management'),
('users.delete', 'Delete Users', 'user_management'),

-- KYC Management
('kyc.view', 'View KYC Applications', 'kyc_management'),
('kyc.review', 'Review KYC Applications', 'kyc_management'),
('kyc.approve', 'Approve KYC Applications', 'kyc_management'),
('kyc.reject', 'Reject KYC Applications', 'kyc_management'),

-- Trading Control
('trading.view_orders', 'View All Orders', 'trading_control'),
('trading.cancel_orders', 'Cancel User Orders', 'trading_control'),
('trading.manage_pairs', 'Manage Trading Pairs', 'trading_control'),
('trading.set_limits', 'Set Trading Limits', 'trading_control'),
('trading.halt_trading', 'Halt Trading', 'trading_control'),

-- Support Management
('support.view_tickets', 'View Support Tickets', 'support_management'),
('support.assign_tickets', 'Assign Support Tickets', 'support_management'),
('support.resolve_tickets', 'Resolve Support Tickets', 'support_management'),

-- System Administration
('system.maintenance', 'System Maintenance', 'system_admin'),
('system.monitoring', 'System Monitoring', 'system_admin'),
('system.backups', 'Manage Backups', 'system_admin'),
('system.logs', 'View System Logs', 'system_admin'),

-- Token Listing
('listing.view_applications', 'View Listing Applications', 'token_listing'),
('listing.review_applications', 'Review Listing Applications', 'token_listing'),
('listing.approve_listings', 'Approve Token Listings', 'token_listing'),

-- Partner Management
('partners.view', 'View Partners', 'partner_management'),
('partners.manage', 'Manage Partners', 'partner_management'),
('affiliates.view', 'View Affiliates', 'partner_management'),
('affiliates.manage', 'Manage Affiliates', 'partner_management'),

-- White Label
('whitelabel.view', 'View White Label Clients', 'white_label'),
('whitelabel.manage', 'Manage White Label Solutions', 'white_label'),
('whitelabel.deploy', 'Deploy White Label Exchanges', 'white_label'),

-- Blockchain Management
('blockchain.view', 'View Blockchain Integrations', 'blockchain_management'),
('blockchain.add', 'Add New Blockchains', 'blockchain_management'),
('blockchain.configure', 'Configure Blockchain Settings', 'blockchain_management'),

-- Financial
('finance.view_reports', 'View Financial Reports', 'finance'),
('finance.manage_fees', 'Manage Fee Structures', 'finance'),
('finance.withdrawals', 'Manage Withdrawals', 'finance');

-- Create indexes for performance
CREATE INDEX idx_admin_users_email ON admin_users(email);
CREATE INDEX idx_admin_users_role_id ON admin_users(role_id);
CREATE INDEX idx_admin_activity_logs_admin_user_id ON admin_activity_logs(admin_user_id);
CREATE INDEX idx_admin_activity_logs_created_at ON admin_activity_logs(created_at);
CREATE INDEX idx_kyc_applications_user_id ON kyc_applications(user_id);
CREATE INDEX idx_kyc_applications_status ON kyc_applications(status);
CREATE INDEX idx_support_tickets_user_id ON support_tickets(user_id);
CREATE INDEX idx_support_tickets_assigned_to ON support_tickets(assigned_to);
CREATE INDEX idx_support_tickets_status ON support_tickets(status);
CREATE INDEX idx_token_listing_applications_status ON token_listing_applications(status);
CREATE INDEX idx_white_label_exchanges_client_id ON white_label_exchanges(client_id);
CREATE INDEX idx_white_label_exchanges_domain_name ON white_label_exchanges(domain_name);
CREATE INDEX idx_custom_blockchains_chain_id ON custom_blockchains(chain_id);
CREATE INDEX idx_custom_blockchains_status ON custom_blockchains(status);

-- Create updated_at triggers
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_admin_users_updated_at BEFORE UPDATE ON admin_users FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_kyc_applications_updated_at BEFORE UPDATE ON kyc_applications FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_token_listing_applications_updated_at BEFORE UPDATE ON token_listing_applications FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_partners_updated_at BEFORE UPDATE ON partners FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_white_label_exchanges_updated_at BEFORE UPDATE ON white_label_exchanges FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_custom_blockchains_updated_at BEFORE UPDATE ON custom_blockchains FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_system_maintenance_updated_at BEFORE UPDATE ON system_maintenance FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
