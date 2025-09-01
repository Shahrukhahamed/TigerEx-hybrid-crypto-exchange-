-- Insert default blockchain configurations

INSERT INTO blockchains (
    blockchain_id, name, symbol, network, rpc_url, chain_id, block_explorer_url,
    is_testnet, supports_smart_contracts, native_currency_symbol, native_currency_decimals,
    description, logo_url, website_url
) VALUES 
(
    'CHAIN_ETHEREUM', 'Ethereum', 'ETH', 'ethereum', 
    'https://mainnet.infura.io/v3/your-key', 1, 'https://etherscan.io',
    FALSE, TRUE, 'ETH', 18,
    'Ethereum is a decentralized platform that runs smart contracts',
    'https://ethereum.org/static/6b935ac0e6194247347855dc3d328e83/6ed5f/eth-diamond-black.webp',
    'https://ethereum.org'
),
(
    'CHAIN_POLYGON', 'Polygon', 'MATIC', 'polygon',
    'https://polygon-rpc.com', 137, 'https://polygonscan.com',
    FALSE, TRUE, 'MATIC', 18,
    'Polygon is a decentralized Ethereum scaling platform',
    'https://wallet-asset.matic.network/img/tokens/matic.svg',
    'https://polygon.technology'
),
(
    'CHAIN_BSC', 'BNB Smart Chain', 'BNB', 'bsc',
    'https://bsc-dataseed.binance.org', 56, 'https://bscscan.com',
    FALSE, TRUE, 'BNB', 18,
    'BNB Smart Chain is a blockchain network built for running smart contract-based applications',
    'https://bin.bnbstatic.com/static/images/common/favicon.ico',
    'https://www.bnbchain.org'
),
(
    'CHAIN_ARBITRUM', 'Arbitrum One', 'ETH', 'arbitrum',
    'https://arb1.arbitrum.io/rpc', 42161, 'https://arbiscan.io',
    FALSE, TRUE, 'ETH', 18,
    'Arbitrum is a Layer 2 scaling solution for Ethereum',
    'https://bridge.arbitrum.io/logo.png',
    'https://arbitrum.io'
),
(
    'CHAIN_OPTIMISM', 'Optimism', 'ETH', 'optimism',
    'https://mainnet.optimism.io', 10, 'https://optimistic.etherscan.io',
    FALSE, TRUE, 'ETH', 18,
    'Optimism is a Layer 2 scaling solution for Ethereum using optimistic rollups',
    'https://optimism.io/images/optimism.svg',
    'https://optimism.io'
),
(
    'CHAIN_AVALANCHE', 'Avalanche C-Chain', 'AVAX', 'avalanche',
    'https://api.avax.network/ext/bc/C/rpc', 43114, 'https://snowtrace.io',
    FALSE, TRUE, 'AVAX', 18,
    'Avalanche is a high-performance, scalable, customizable, and secure blockchain platform',
    'https://cryptologos.cc/logos/avalanche-avax-logo.svg',
    'https://avax.network'
);

-- Insert default tokens (major cryptocurrencies)
INSERT INTO tokens (
    token_id, name, symbol, decimals, blockchain_id, token_standard,
    description, logo_url, website_url, coingecko_id, status, is_verified, verification_level
) VALUES 
(
    'TOKEN_ETH', 'Ethereum', 'ETH', 18, 
    (SELECT id FROM blockchains WHERE blockchain_id = 'CHAIN_ETHEREUM'),
    'NATIVE',
    'Ethereum is a decentralized platform that runs smart contracts',
    'https://ethereum.org/static/6b935ac0e6194247347855dc3d328e83/6ed5f/eth-diamond-black.webp',
    'https://ethereum.org',
    'ethereum',
    'active', TRUE, 5
),
(
    'TOKEN_MATIC', 'Polygon', 'MATIC', 18,
    (SELECT id FROM blockchains WHERE blockchain_id = 'CHAIN_POLYGON'),
    'NATIVE',
    'Polygon is a decentralized Ethereum scaling platform',
    'https://wallet-asset.matic.network/img/tokens/matic.svg',
    'https://polygon.technology',
    'matic-network',
    'active', TRUE, 5
),
(
    'TOKEN_BNB', 'BNB', 'BNB', 18,
    (SELECT id FROM blockchains WHERE blockchain_id = 'CHAIN_BSC'),
    'NATIVE',
    'BNB is the native token of BNB Smart Chain',
    'https://bin.bnbstatic.com/static/images/common/favicon.ico',
    'https://www.bnbchain.org',
    'binancecoin',
    'active', TRUE, 5
),
(
    'TOKEN_AVAX', 'Avalanche', 'AVAX', 18,
    (SELECT id FROM blockchains WHERE blockchain_id = 'CHAIN_AVALANCHE'),
    'NATIVE',
    'AVAX is the native token of Avalanche platform',
    'https://cryptologos.cc/logos/avalanche-avax-logo.svg',
    'https://avax.network',
    'avalanche-2',
    'active', TRUE, 5
);

-- Insert USDT on multiple chains
INSERT INTO tokens (
    token_id, name, symbol, decimals, blockchain_id, contract_address, token_standard,
    description, logo_url, website_url, coingecko_id, status, is_verified, verification_level
) VALUES 
(
    'TOKEN_USDT_ETH', 'Tether USD', 'USDT', 6,
    (SELECT id FROM blockchains WHERE blockchain_id = 'CHAIN_ETHEREUM'),
    '0xdAC17F958D2ee523a2206206994597C13D831ec7', 'ERC20',
    'Tether USD is a stablecoin pegged to the US Dollar',
    'https://tether.to/images/logoCircle.png',
    'https://tether.to',
    'tether',
    'active', TRUE, 5
),
(
    'TOKEN_USDT_POLYGON', 'Tether USD', 'USDT', 6,
    (SELECT id FROM blockchains WHERE blockchain_id = 'CHAIN_POLYGON'),
    '0xc2132D05D31c914a87C6611C10748AEb04B58e8F', 'ERC20',
    'Tether USD is a stablecoin pegged to the US Dollar',
    'https://tether.to/images/logoCircle.png',
    'https://tether.to',
    'tether',
    'active', TRUE, 5
),
(
    'TOKEN_USDT_BSC', 'Tether USD', 'USDT', 18,
    (SELECT id FROM blockchains WHERE blockchain_id = 'CHAIN_BSC'),
    '0x55d398326f99059fF775485246999027B3197955', 'BEP20',
    'Tether USD is a stablecoin pegged to the US Dollar',
    'https://tether.to/images/logoCircle.png',
    'https://tether.to',
    'tether',
    'active', TRUE, 5
);

-- Insert default trading pairs
INSERT INTO trading_pairs (
    pair_id, base_token_id, quote_token_id, symbol, min_order_size,
    price_precision, quantity_precision, maker_fee, taker_fee
) VALUES 
(
    'PAIR_ETHUSDT', 
    (SELECT id FROM tokens WHERE token_id = 'TOKEN_ETH'),
    (SELECT id FROM tokens WHERE token_id = 'TOKEN_USDT_ETH'),
    'ETHUSDT', 0.001, 2, 6, 0.001, 0.001
),
(
    'PAIR_BNBUSDT',
    (SELECT id FROM tokens WHERE token_id = 'TOKEN_BNB'),
    (SELECT id FROM tokens WHERE token_id = 'TOKEN_USDT_BSC'),
    'BNBUSDT', 0.01, 2, 6, 0.001, 0.001
),
(
    'PAIR_MATICUSDT',
    (SELECT id FROM tokens WHERE token_id = 'TOKEN_MATIC'),
    (SELECT id FROM tokens WHERE token_id = 'TOKEN_USDT_POLYGON'),
    'MATICUSDT', 1.0, 4, 2, 0.001, 0.001
),
(
    'PAIR_AVAXUSDT',
    (SELECT id FROM tokens WHERE token_id = 'TOKEN_AVAX'),
    (SELECT id FROM tokens WHERE token_id = 'TOKEN_USDT_ETH'),
    'AVAXUSDT', 0.01, 2, 4, 0.001, 0.001
);
