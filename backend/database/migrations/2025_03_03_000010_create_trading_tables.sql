-- Trading pairs table
CREATE TABLE IF NOT EXISTS trading_pairs (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) UNIQUE NOT NULL, -- e.g., BTCUSDT
    base_asset VARCHAR(10) NOT NULL,    -- e.g., BTC
    quote_asset VARCHAR(10) NOT NULL,   -- e.g., USDT
    
    -- Trading status
    status VARCHAR(20) DEFAULT 'TRADING', -- TRADING, HALT, BREAK, DELISTED
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Price and quantity filters
    min_quantity DECIMAL(20,8) NOT NULL DEFAULT 0.00000001,
    max_quantity DECIMAL(20,8) NOT NULL DEFAULT 1000000000,
    step_size DECIMAL(20,8) NOT NULL DEFAULT 0.00000001,
    min_price DECIMAL(20,8) NOT NULL DEFAULT 0.00000001,
    max_price DECIMAL(20,8) NOT NULL DEFAULT 1000000,
    tick_size DECIMAL(20,8) NOT NULL DEFAULT 0.00000001,
    min_notional DECIMAL(20,8) NOT NULL DEFAULT 10.00,
    
    -- Fee structure
    maker_fee DECIMAL(6,4) DEFAULT 0.0010, -- 0.1%
    taker_fee DECIMAL(6,4) DEFAULT 0.0010, -- 0.1%
    
    -- Trading features
    is_spot_enabled BOOLEAN DEFAULT TRUE,
    is_margin_enabled BOOLEAN DEFAULT FALSE,
    is_futures_enabled BOOLEAN DEFAULT FALSE,
    is_options_enabled BOOLEAN DEFAULT FALSE,
    
    -- Margin trading parameters
    margin_max_leverage DECIMAL(8,2) DEFAULT 1.00,
    margin_maintenance_rate DECIMAL(6,4) DEFAULT 0.05, -- 5%
    margin_initial_rate DECIMAL(6,4) DEFAULT 0.10, -- 10%
    
    -- Futures parameters
    futures_max_leverage DECIMAL(8,2) DEFAULT 1.00,
    futures_maintenance_rate DECIMAL(6,4) DEFAULT 0.05,
    futures_initial_rate DECIMAL(6,4) DEFAULT 0.10,
    contract_size DECIMAL(20,8) DEFAULT 1.00,
    settlement_asset VARCHAR(10),
    
    -- Market data
    last_price DECIMAL(20,8),
    price_change_24h DECIMAL(20,8),
    price_change_percent_24h DECIMAL(8,4),
    volume_24h DECIMAL(30,8),
    high_24h DECIMAL(20,8),
    low_24h DECIMAL(20,8),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT valid_status CHECK (status IN ('TRADING', 'HALT', 'BREAK', 'DELISTED'))
);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id),
    symbol VARCHAR(20) NOT NULL,
    client_order_id VARCHAR(50),
    
    -- Order details
    side VARCHAR(10) NOT NULL, -- BUY, SELL
    type VARCHAR(20) NOT NULL, -- MARKET, LIMIT, STOP_LOSS, STOP_LIMIT, TAKE_PROFIT, etc.
    time_in_force VARCHAR(10) DEFAULT 'GTC', -- GTC, IOC, FOK, GTD
    
    -- Quantities and prices
    quantity DECIMAL(20,8) NOT NULL,
    price DECIMAL(20,8),
    stop_price DECIMAL(20,8),
    iceberg_quantity DECIMAL(20,8),
    
    -- Execution details
    filled_quantity DECIMAL(20,8) DEFAULT 0,
    remaining_quantity DECIMAL(20,8),
    avg_fill_price DECIMAL(20,8),
    
    -- Status and fees
    status VARCHAR(20) DEFAULT 'NEW', -- NEW, PARTIALLY_FILLED, FILLED, CANCELED, REJECTED, EXPIRED
    fee DECIMAL(20,8) DEFAULT 0,
    fee_asset VARCHAR(10),
    
    -- Advanced order features
    reduce_only BOOLEAN DEFAULT FALSE,
    post_only BOOLEAN DEFAULT FALSE,
    close_position BOOLEAN DEFAULT FALSE,
    
    -- Margin/Futures specific
    position_side VARCHAR(10), -- LONG, SHORT, BOTH
    working_type VARCHAR(20), -- CONTRACT_PRICE, MARK_PRICE
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    filled_at TIMESTAMP,
    canceled_at TIMESTAMP,
    
    -- Metadata
    source VARCHAR(20) DEFAULT 'WEB', -- WEB, API, MOBILE
    ip_address INET,
    
    CONSTRAINT valid_side CHECK (side IN ('BUY', 'SELL')),
    CONSTRAINT valid_type CHECK (type IN ('MARKET', 'LIMIT', 'STOP_LOSS', 'STOP_LIMIT', 'TAKE_PROFIT', 'TAKE_PROFIT_LIMIT', 'TRAILING_STOP', 'OCO', 'ICEBERG')),
    CONSTRAINT valid_time_in_force CHECK (time_in_force IN ('GTC', 'IOC', 'FOK', 'GTD')),
    CONSTRAINT valid_status CHECK (status IN ('NEW', 'PARTIALLY_FILLED', 'FILLED', 'CANCELED', 'REJECTED', 'EXPIRED')),
    CONSTRAINT positive_quantity CHECK (quantity > 0),
    CONSTRAINT positive_price CHECK (price IS NULL OR price > 0)
);

-- Trades table
CREATE TABLE IF NOT EXISTS trades (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    
    -- Order references
    buy_order_id BIGINT NOT NULL REFERENCES orders(id),
    sell_order_id BIGINT NOT NULL REFERENCES orders(id),
    buyer_id BIGINT NOT NULL REFERENCES users(id),
    seller_id BIGINT NOT NULL REFERENCES users(id),
    
    -- Trade details
    price DECIMAL(20,8) NOT NULL,
    quantity DECIMAL(20,8) NOT NULL,
    quote_quantity DECIMAL(30,8) NOT NULL,
    
    -- Fees
    buyer_fee DECIMAL(20,8) DEFAULT 0,
    seller_fee DECIMAL(20,8) DEFAULT 0,
    fee_asset VARCHAR(10),
    
    -- Trade type
    trade_type VARCHAR(20) DEFAULT 'SPOT', -- SPOT, MARGIN, FUTURES, OPTIONS
    
    -- Market maker identification
    is_buyer_maker BOOLEAN,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT positive_price CHECK (price > 0),
    CONSTRAINT positive_quantity CHECK (quantity > 0)
);

-- Balances table
CREATE TABLE IF NOT EXISTS balances (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id),
    asset VARCHAR(10) NOT NULL,
    
    -- Balance types
    available DECIMAL(30,8) DEFAULT 0 CHECK (available >= 0),
    locked DECIMAL(30,8) DEFAULT 0 CHECK (locked >= 0),
    staked DECIMAL(30,8) DEFAULT 0 CHECK (staked >= 0),
    
    -- Margin balances
    margin_available DECIMAL(30,8) DEFAULT 0,
    margin_locked DECIMAL(30,8) DEFAULT 0,
    margin_borrowed DECIMAL(30,8) DEFAULT 0,
    margin_interest DECIMAL(30,8) DEFAULT 0,
    
    -- Futures balances
    futures_available DECIMAL(30,8) DEFAULT 0,
    futures_locked DECIMAL(30,8) DEFAULT 0,
    unrealized_pnl DECIMAL(30,8) DEFAULT 0,
    
    -- Timestamps
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, asset)
);

-- Positions table (for margin and futures)
CREATE TABLE IF NOT EXISTS positions (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id),
    symbol VARCHAR(20) NOT NULL,
    
    -- Position details
    side VARCHAR(10) NOT NULL, -- LONG, SHORT
    size DECIMAL(20,8) NOT NULL,
    entry_price DECIMAL(20,8) NOT NULL,
    mark_price DECIMAL(20,8),
    liquidation_price DECIMAL(20,8),
    
    -- PnL
    unrealized_pnl DECIMAL(30,8) DEFAULT 0,
    realized_pnl DECIMAL(30,8) DEFAULT 0,
    
    -- Margin
    margin_used DECIMAL(30,8) NOT NULL,
    maintenance_margin DECIMAL(30,8) NOT NULL,
    leverage DECIMAL(8,2) NOT NULL,
    
    -- Position type
    position_type VARCHAR(20) DEFAULT 'ISOLATED', -- ISOLATED, CROSS
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP,
    
    UNIQUE(user_id, symbol, side),
    CONSTRAINT valid_side CHECK (side IN ('LONG', 'SHORT')),
    CONSTRAINT positive_size CHECK (size >= 0),
    CONSTRAINT positive_leverage CHECK (leverage > 0)
);

-- Deposits table
CREATE TABLE IF NOT EXISTS deposits (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id),
    asset VARCHAR(10) NOT NULL,
    
    -- Deposit details
    amount DECIMAL(30,8) NOT NULL,
    fee DECIMAL(30,8) DEFAULT 0,
    net_amount DECIMAL(30,8) NOT NULL,
    
    -- Blockchain details
    tx_hash VARCHAR(100),
    block_hash VARCHAR(100),
    block_number BIGINT,
    confirmations INTEGER DEFAULT 0,
    required_confirmations INTEGER DEFAULT 6,
    
    -- Address details
    deposit_address VARCHAR(100),
    deposit_tag VARCHAR(50), -- For assets that require memo/tag
    
    -- Status
    status VARCHAR(20) DEFAULT 'PENDING', -- PENDING, CONFIRMING, COMPLETED, FAILED
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confirmed_at TIMESTAMP,
    credited_at TIMESTAMP,
    
    CONSTRAINT positive_amount CHECK (amount > 0),
    CONSTRAINT valid_status CHECK (status IN ('PENDING', 'CONFIRMING', 'COMPLETED', 'FAILED'))
);

-- Withdrawals table
CREATE TABLE IF NOT EXISTS withdrawals (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(id),
    asset VARCHAR(10) NOT NULL,
    
    -- Withdrawal details
    amount DECIMAL(30,8) NOT NULL,
    fee DECIMAL(30,8) NOT NULL,
    net_amount DECIMAL(30,8) NOT NULL,
    
    -- Destination details
    destination_address VARCHAR(100) NOT NULL,
    destination_tag VARCHAR(50),
    
    -- Blockchain details
    tx_hash VARCHAR(100),
    block_hash VARCHAR(100),
    block_number BIGINT,
    confirmations INTEGER DEFAULT 0,
    
    -- Status and approval
    status VARCHAR(20) DEFAULT 'PENDING', -- PENDING, APPROVED, PROCESSING, COMPLETED, FAILED, CANCELED
    approved_by BIGINT REFERENCES users(id),
    approved_at TIMESTAMP,
    
    -- Security
    requires_approval BOOLEAN DEFAULT FALSE,
    two_factor_verified BOOLEAN DEFAULT FALSE,
    email_verified BOOLEAN DEFAULT FALSE,
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    CONSTRAINT positive_amount CHECK (amount > 0),
    CONSTRAINT positive_fee CHECK (fee >= 0),
    CONSTRAINT valid_status CHECK (status IN ('PENDING', 'APPROVED', 'PROCESSING', 'COMPLETED', 'FAILED', 'CANCELED'))
);

-- Create indexes for performance
CREATE INDEX idx_trading_pairs_symbol ON trading_pairs(symbol);
CREATE INDEX idx_trading_pairs_status ON trading_pairs(status);
CREATE INDEX idx_trading_pairs_base_asset ON trading_pairs(base_asset);
CREATE INDEX idx_trading_pairs_quote_asset ON trading_pairs(quote_asset);

CREATE INDEX idx_orders_user_id ON orders(user_id);
CREATE INDEX idx_orders_symbol ON orders(symbol);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_orders_created_at ON orders(created_at);
CREATE INDEX idx_orders_user_symbol_status ON orders(user_id, symbol, status);

CREATE INDEX idx_trades_symbol ON trades(symbol);
CREATE INDEX idx_trades_buyer_id ON trades(buyer_id);
CREATE INDEX idx_trades_seller_id ON trades(seller_id);
CREATE INDEX idx_trades_created_at ON trades(created_at);
CREATE INDEX idx_trades_symbol_created_at ON trades(symbol, created_at);

CREATE INDEX idx_balances_user_id ON balances(user_id);
CREATE INDEX idx_balances_asset ON balances(asset);
CREATE INDEX idx_balances_user_asset ON balances(user_id, asset);

CREATE INDEX idx_positions_user_id ON positions(user_id);
CREATE INDEX idx_positions_symbol ON positions(symbol);
CREATE INDEX idx_positions_user_symbol ON positions(user_id, symbol);

CREATE INDEX idx_deposits_user_id ON deposits(user_id);
CREATE INDEX idx_deposits_status ON deposits(status);
CREATE INDEX idx_deposits_tx_hash ON deposits(tx_hash);
CREATE INDEX idx_deposits_created_at ON deposits(created_at);

CREATE INDEX idx_withdrawals_user_id ON withdrawals(user_id);
CREATE INDEX idx_withdrawals_status ON withdrawals(status);
CREATE INDEX idx_withdrawals_tx_hash ON withdrawals(tx_hash);
CREATE INDEX idx_withdrawals_created_at ON withdrawals(created_at);

-- Create triggers for updated_at
CREATE TRIGGER update_trading_pairs_updated_at 
    BEFORE UPDATE ON trading_pairs 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_orders_updated_at 
    BEFORE UPDATE ON orders 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_balances_updated_at 
    BEFORE UPDATE ON balances 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_positions_updated_at 
    BEFORE UPDATE ON positions 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Add comments
COMMENT ON TABLE trading_pairs IS 'Trading pairs configuration and market data';
COMMENT ON TABLE orders IS 'All trading orders with comprehensive order types';
COMMENT ON TABLE trades IS 'Executed trades between users';
COMMENT ON TABLE balances IS 'User balances for all assets and trading types';
COMMENT ON TABLE positions IS 'Open positions for margin and futures trading';
COMMENT ON TABLE deposits IS 'Cryptocurrency deposits from blockchain';
COMMENT ON TABLE withdrawals IS 'Cryptocurrency withdrawals to external addresses';