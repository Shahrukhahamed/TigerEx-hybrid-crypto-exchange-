-- Admin Panel Tables

-- Blockchains table
CREATE TABLE IF NOT EXISTS blockchains (
    id SERIAL PRIMARY KEY,
    blockchain_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    symbol VARCHAR(10) NOT NULL,
    network VARCHAR(20) NOT NULL,
    rpc_url VARCHAR(500) NOT NULL,
    chain_id INTEGER NOT NULL,
    block_explorer_url VARCHAR(500),
    is_testnet BOOLEAN DEFAULT FALSE,
    supports_smart_contracts BOOLEAN DEFAULT TRUE,
    native_currency_symbol VARCHAR(10) NOT NULL,
    native_currency_decimals INTEGER DEFAULT 18,
    is_active BOOLEAN DEFAULT TRUE,
    is_trading_enabled BOOLEAN DEFAULT TRUE,
    is_deposit_enabled BOOLEAN DEFAULT TRUE,
    is_withdrawal_enabled BOOLEAN DEFAULT TRUE,
    gas_price_gwei DECIMAL(20,8),
    withdrawal_fee DECIMAL(20,8),
    min_withdrawal_amount DECIMAL(20,8),
    description TEXT,
    logo_url VARCHAR(500),
    website_url VARCHAR(500),
    documentation_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tokens table
CREATE TABLE IF NOT EXISTS tokens (
    id SERIAL PRIMARY KEY,
    token_id VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    decimals INTEGER NOT NULL DEFAULT 18,
    blockchain_id INTEGER REFERENCES blockchains(id) ON DELETE CASCADE,
    contract_address VARCHAR(100),
    token_standard VARCHAR(10) NOT NULL,
    total_supply DECIMAL(30,8),
    circulating_supply DECIMAL(30,8),
    max_supply DECIMAL(30,8),
    current_price_usd DECIMAL(20,8),
    market_cap_usd DECIMAL(20,2),
    volume_24h_usd DECIMAL(20,2),
    price_change_24h DECIMAL(10,4),
    coingecko_id VARCHAR(100),
    coinmarketcap_id VARCHAR(100),
    description TEXT,
    logo_url VARCHAR(500),
    website_url VARCHAR(500),
    whitepaper_url VARCHAR(500),
    twitter_url VARCHAR(500),
    telegram_url VARCHAR(500),
    discord_url VARCHAR(500),
    github_url VARCHAR(500),
    is_tradable BOOLEAN DEFAULT TRUE,
    min_trade_amount DECIMAL(20,8),
    max_trade_amount DECIMAL(20,8),
    is_deposit_enabled BOOLEAN DEFAULT TRUE,
    is_withdrawal_enabled BOOLEAN DEFAULT TRUE,
    min_deposit_amount DECIMAL(20,8),
    min_withdrawal_amount DECIMAL(20,8),
    withdrawal_fee DECIMAL(20,8),
    status VARCHAR(20) DEFAULT 'pending',
    listing_date TIMESTAMP,
    delisting_date TIMESTAMP,
    is_verified BOOLEAN DEFAULT FALSE,
    verification_level INTEGER DEFAULT 0,
    risk_score INTEGER DEFAULT 50,
    risk_factors JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trading pairs table
CREATE TABLE IF NOT EXISTS trading_pairs (
    id SERIAL PRIMARY KEY,
    pair_id VARCHAR(50) UNIQUE NOT NULL,
    base_token_id INTEGER REFERENCES tokens(id) ON DELETE CASCADE,
    quote_token_id INTEGER REFERENCES tokens(id) ON DELETE CASCADE,
    symbol VARCHAR(20) NOT NULL UNIQUE,
    min_order_size DECIMAL(20,8) NOT NULL,
    max_order_size DECIMAL(20,8),
    min_price DECIMAL(20,8),
    max_price DECIMAL(20,8),
    price_precision INTEGER DEFAULT 8,
    quantity_precision INTEGER DEFAULT 8,
    maker_fee DECIMAL(5,4) DEFAULT 0.001,
    taker_fee DECIMAL(5,4) DEFAULT 0.001,
    last_price DECIMAL(20,8),
    volume_24h DECIMAL(30,8) DEFAULT 0,
    high_24h DECIMAL(20,8),
    low_24h DECIMAL(20,8),
    price_change_24h DECIMAL(10,4) DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',
    is_spot_enabled BOOLEAN DEFAULT TRUE,
    is_margin_enabled BOOLEAN DEFAULT FALSE,
    is_futures_enabled BOOLEAN DEFAULT FALSE,
    listed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    delisted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Token listings table
CREATE TABLE IF NOT EXISTS token_listings (
    id SERIAL PRIMARY KEY,
    listing_id VARCHAR(50) UNIQUE NOT NULL,
    token_name VARCHAR(100) NOT NULL,
    token_symbol VARCHAR(20) NOT NULL,
    blockchain_network VARCHAR(20) NOT NULL,
    contract_address VARCHAR(100),
    applicant_name VARCHAR(100) NOT NULL,
    applicant_email VARCHAR(255) NOT NULL,
    company_name VARCHAR(255),
    total_supply DECIMAL(30,8),
    circulating_supply DECIMAL(30,8),
    token_description TEXT,
    use_case TEXT,
    whitepaper_url VARCHAR(500),
    audit_report_url VARCHAR(500),
    legal_opinion_url VARCHAR(500),
    current_exchanges JSONB,
    trading_volume DECIMAL(20,2),
    market_cap DECIMAL(20,2),
    status VARCHAR(20) DEFAULT 'pending',
    review_notes TEXT,
    reviewed_by VARCHAR(50),
    reviewed_at TIMESTAMP,
    listing_fee_paid BOOLEAN DEFAULT FALSE,
    listing_fee_amount DECIMAL(20,2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_blockchains_blockchain_id ON blockchains(blockchain_id);
CREATE INDEX IF NOT EXISTS idx_blockchains_network ON blockchains(network);
CREATE INDEX IF NOT EXISTS idx_blockchains_chain_id ON blockchains(chain_id);

CREATE INDEX IF NOT EXISTS idx_tokens_token_id ON tokens(token_id);
CREATE INDEX IF NOT EXISTS idx_tokens_symbol ON tokens(symbol);
CREATE INDEX IF NOT EXISTS idx_tokens_blockchain_id ON tokens(blockchain_id);
CREATE INDEX IF NOT EXISTS idx_tokens_contract_address ON tokens(contract_address);
CREATE INDEX IF NOT EXISTS idx_tokens_status ON tokens(status);

CREATE INDEX IF NOT EXISTS idx_trading_pairs_pair_id ON trading_pairs(pair_id);
CREATE INDEX IF NOT EXISTS idx_trading_pairs_symbol ON trading_pairs(symbol);
CREATE INDEX IF NOT EXISTS idx_trading_pairs_base_token_id ON trading_pairs(base_token_id);
CREATE INDEX IF NOT EXISTS idx_trading_pairs_quote_token_id ON trading_pairs(quote_token_id);
CREATE INDEX IF NOT EXISTS idx_trading_pairs_status ON trading_pairs(status);

CREATE INDEX IF NOT EXISTS idx_token_listings_listing_id ON token_listings(listing_id);
CREATE INDEX IF NOT EXISTS idx_token_listings_status ON token_listings(status);
CREATE INDEX IF NOT EXISTS idx_token_listings_token_symbol ON token_listings(token_symbol);
