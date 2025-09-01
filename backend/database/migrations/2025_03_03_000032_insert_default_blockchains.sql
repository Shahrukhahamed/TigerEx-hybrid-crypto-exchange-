-- Insert Default Blockchain Configurations
-- TigerEx Default Blockchain and Token Support

-- Insert default supported blockchains
INSERT INTO custom_blockchains (
    blockchain_id, name, symbol, description, chain_id, network_type, 
    consensus_mechanism, block_time, gas_limit, rpc_url, ws_url, explorer_url,
    deployment_status, created_by
) VALUES 
-- Ethereum Mainnet
('ETH_MAINNET', 'Ethereum', 'ETH', 'Ethereum Mainnet - The original smart contract platform', 
 1, 'mainnet', 'Proof of Stake', 12, 30000000,
 'https://mainnet.infura.io/v3/YOUR_PROJECT_ID', 'wss://mainnet.infura.io/ws/v3/YOUR_PROJECT_ID',
 'https://etherscan.io', 'deployed', 'system'),

-- Binance Smart Chain
('BSC_MAINNET', 'Binance Smart Chain', 'BNB', 'Binance Smart Chain - Fast and low-cost blockchain',
 56, 'mainnet', 'Proof of Staked Authority', 3, 50000000,
 'https://bsc-dataseed.binance.org', 'wss://bsc-ws-node.nariox.org:443',
 'https://bscscan.com', 'deployed', 'system'),

-- Polygon
('POLYGON_MAINNET', 'Polygon', 'MATIC', 'Polygon - Ethereum scaling solution',
 137, 'mainnet', 'Proof of Stake', 2, 30000000,
 'https://polygon-rpc.com', 'wss://polygon-rpc.com',
 'https://polygonscan.com', 'deployed', 'system'),

-- Arbitrum One
('ARBITRUM_ONE', 'Arbitrum One', 'ETH', 'Arbitrum One - Ethereum Layer 2 scaling solution',
 42161, 'mainnet', 'Optimistic Rollup', 1, 32000000,
 'https://arb1.arbitrum.io/rpc', 'wss://arb1.arbitrum.io/ws',
 'https://arbiscan.io', 'deployed', 'system'),

-- Optimism
('OPTIMISM_MAINNET', 'Optimism', 'ETH', 'Optimism - Ethereum Layer 2 scaling solution',
 10, 'mainnet', 'Optimistic Rollup', 2, 30000000,
 'https://mainnet.optimism.io', 'wss://mainnet.optimism.io',
 'https://optimistic.etherscan.io', 'deployed', 'system'),

-- Avalanche C-Chain
('AVALANCHE_C', 'Avalanche C-Chain', 'AVAX', 'Avalanche C-Chain - High-performance blockchain',
 43114, 'mainnet', 'Avalanche Consensus', 2, 15000000,
 'https://api.avax.network/ext/bc/C/rpc', 'wss://api.avax.network/ext/bc/C/ws',
 'https://snowtrace.io', 'deployed', 'system'),

-- Fantom Opera
('FANTOM_OPERA', 'Fantom Opera', 'FTM', 'Fantom Opera - Fast and secure blockchain',
 250, 'mainnet', 'Lachesis Consensus', 1, 10000000,
 'https://rpc.ftm.tools', 'wss://wsapi.fantom.network',
 'https://ftmscan.com', 'deployed', 'system'),

-- Solana (Non-EVM)
('SOLANA_MAINNET', 'Solana', 'SOL', 'Solana - High-performance blockchain',
 0, 'mainnet', 'Proof of History', 1, 0,
 'https://api.mainnet-beta.solana.com', 'wss://api.mainnet-beta.solana.com',
 'https://explorer.solana.com', 'deployed', 'system'),

-- TigerChain (Custom)
('TIGER_MAINNET', 'TigerChain', 'TIGER', 'TigerEx native blockchain for advanced trading features',
 88888, 'mainnet', 'Delegated Proof of Stake', 1, 50000000,
 'https://rpc.tigerchain.com', 'wss://ws.tigerchain.com',
 'https://explorer.tigerchain.com', 'deployed', 'system');

-- Insert default system settings
INSERT INTO system_settings (setting_key, setting_value, setting_type, description, is_public) VALUES
('supported_blockchains', '["ETH_MAINNET", "BSC_MAINNET", "POLYGON_MAINNET", "ARBITRUM_ONE", "OPTIMISM_MAINNET", "AVALANCHE_C", "FANTOM_OPERA", "SOLANA_MAINNET", "TIGER_MAINNET"]', 'array', 'List of supported blockchain networks', true),
('default_gas_prices', '{"ETH_MAINNET": 20, "BSC_MAINNET": 5, "POLYGON_MAINNET": 30, "ARBITRUM_ONE": 0.1, "OPTIMISM_MAINNET": 0.001, "AVALANCHE_C": 25, "FANTOM_OPERA": 100}', 'object', 'Default gas prices in Gwei for each network', true),
('max_deployment_time', '3600', 'number', 'Maximum deployment time in seconds', false),
('auto_ssl_enabled', 'true', 'boolean', 'Enable automatic SSL certificate generation', false),
('default_domain_suffix', '.tigerex.com', 'string', 'Default domain suffix for deployments', false);

-- Insert default DEX configurations
INSERT INTO custom_dexs (
    dex_id, name, symbol, description, blockchain_id, 
    router_contract, factory_contract, weth_contract,
    deployment_status, created_by
) VALUES
-- Ethereum DEXs
('UNISWAP_V3_ETH', 'Uniswap V3', 'UNI', 'Uniswap V3 on Ethereum', 1,
 '0xE592427A0AEce92De3Edee1F18E0157C05861564', '0x1F98431c8aD98523631AE4a59f267346ea31F984', '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
 'deployed', 'system'),

-- BSC DEXs  
('PANCAKESWAP_V3_BSC', 'PancakeSwap V3', 'CAKE', 'PancakeSwap V3 on BSC', 2,
 '0x13f4EA83D0bd40E75C8222255bc855a974568Dd4', '0x0BFbCF9fa4f9C56B0F40a671Ad40E0805A091865', '0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c',
 'deployed', 'system'),

-- Polygon DEXs
('QUICKSWAP_POLYGON', 'QuickSwap', 'QUICK', 'QuickSwap on Polygon', 3,
 '0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff', '0x5757371414417b8C6CAad45bAeF941aBc7d3Ab32', '0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270',
 'deployed', 'system');

-- Insert default block explorers
INSERT INTO block_explorers (
    explorer_id, name, blockchain_id, api_url, frontend_url, websocket_url,
    supported_features, deployment_status, created_by
) VALUES
('ETHERSCAN', 'Etherscan', 1, 'https://api.etherscan.io/api', 'https://etherscan.io', 'wss://etherscan.io/ws',
 '["transactions", "blocks", "addresses", "tokens", "contracts", "analytics"]', 'deployed', 'system'),

('BSCSCAN', 'BscScan', 2, 'https://api.bscscan.com/api', 'https://bscscan.com', 'wss://bscscan.com/ws',
 '["transactions", "blocks", "addresses", "tokens", "contracts", "analytics"]', 'deployed', 'system'),

('POLYGONSCAN', 'PolygonScan', 3, 'https://api.polygonscan.com/api', 'https://polygonscan.com', 'wss://polygonscan.com/ws',
 '["transactions", "blocks", "addresses", "tokens", "contracts", "analytics"]', 'deployed', 'system'),

('TIGER_EXPLORER', 'TigerExplorer', 9, 'https://api.explorer.tigerchain.com/api', 'https://explorer.tigerchain.com', 'wss://explorer.tigerchain.com/ws',
 '["transactions", "blocks", "addresses", "tokens", "contracts", "analytics", "staking", "governance"]', 'deployed', 'system');

-- Insert default wallet systems
INSERT INTO wallet_systems (
    wallet_id, name, wallet_type, description, supported_blockchains, 
    supported_tokens, security_features, deployment_status, created_by
) VALUES
('TIGER_HOT_WALLET', 'TigerEx Hot Wallet', 'hot', 'High-performance hot wallet for trading',
 '["ETH_MAINNET", "BSC_MAINNET", "POLYGON_MAINNET", "ARBITRUM_ONE", "OPTIMISM_MAINNET", "AVALANCHE_C", "FANTOM_OPERA", "TIGER_MAINNET"]',
 '["ETH", "BTC", "BNB", "MATIC", "AVAX", "FTM", "TIGER", "USDT", "USDC", "DAI"]',
 '["multi_signature", "hardware_security_module", "cold_storage_backup", "real_time_monitoring"]',
 'deployed', 'system'),

('TIGER_COLD_WALLET', 'TigerEx Cold Wallet', 'cold', 'Ultra-secure cold storage wallet',
 '["ETH_MAINNET", "BSC_MAINNET", "POLYGON_MAINNET", "TIGER_MAINNET"]',
 '["ETH", "BTC", "BNB", "MATIC", "TIGER", "USDT", "USDC"]',
 '["air_gapped", "multi_signature", "hardware_security_module", "geographic_distribution"]',
 'deployed', 'system'),

('TIGER_CUSTODIAL', 'TigerEx Custodial Wallet', 'custodial', 'Institutional-grade custodial wallet service',
 '["ETH_MAINNET", "BSC_MAINNET", "POLYGON_MAINNET", "ARBITRUM_ONE", "OPTIMISM_MAINNET", "AVALANCHE_C", "TIGER_MAINNET"]',
 '["ETH", "BTC", "BNB", "MATIC", "AVAX", "TIGER", "USDT", "USDC", "DAI", "WBTC"]',
 '["insurance_coverage", "regulatory_compliance", "audit_trail", "multi_signature", "cold_storage"]',
 'deployed', 'system'),

('TIGER_NON_CUSTODIAL', 'TigerEx Non-Custodial Wallet', 'non_custodial', 'User-controlled non-custodial wallet',
 '["ETH_MAINNET", "BSC_MAINNET", "POLYGON_MAINNET", "ARBITRUM_ONE", "OPTIMISM_MAINNET", "AVALANCHE_C", "FANTOM_OPERA", "SOLANA_MAINNET", "TIGER_MAINNET"]',
 '["ETH", "BTC", "BNB", "MATIC", "AVAX", "FTM", "SOL", "TIGER", "USDT", "USDC", "DAI", "WBTC", "LINK", "UNI", "AAVE"]',
 '["seed_phrase_backup", "hardware_wallet_support", "biometric_authentication", "social_recovery"]',
 'deployed', 'system');

-- Insert default admin permissions
INSERT INTO system_settings (setting_key, setting_value, setting_type, description, is_public, required_permission) VALUES
('admin_permissions', '{
  "super_admin": ["*"],
  "blockchain_admin": ["blockchain:*", "dex:*", "explorer:*"],
  "exchange_admin": ["exchange:*", "wallet:*"],
  "support_admin": ["user:read", "ticket:*", "kyc:read"],
  "compliance_admin": ["kyc:*", "aml:*", "compliance:*"],
  "technical_admin": ["system:read", "deployment:read", "monitoring:*"]
}', 'object', 'Default admin permission sets', false, 'admin:manage'),

('deployment_templates', '{
  "blockchain": {
    "ethereum_compatible": {
      "docker_image": "ethereum/client-go:latest",
      "required_resources": {"cpu": "2", "memory": "4Gi", "storage": "100Gi"},
      "default_ports": [8545, 8546, 30303]
    },
    "substrate": {
      "docker_image": "parity/substrate:latest", 
      "required_resources": {"cpu": "4", "memory": "8Gi", "storage": "200Gi"},
      "default_ports": [9944, 9933, 30333]
    }
  },
  "dex": {
    "uniswap_v3": {
      "contracts": ["UniswapV3Factory", "UniswapV3Router", "NonfungiblePositionManager"],
      "required_tokens": ["WETH", "USDC", "USDT"]
    }
  }
}', 'object', 'Deployment templates for different resource types', false, 'admin:deploy');

-- Create default super admin (should be updated with real credentials)
INSERT INTO admin_users (
    admin_id, user_id, admin_level, department, position,
    permissions, access_level, created_by
) VALUES (
    'SUPER_ADMIN_001', 'system_admin', 3, 'Technology', 'Chief Technology Officer',
    '["*"]', 10, 'system'
);

COMMIT;
