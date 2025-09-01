-- Insert default P2P platform settings

INSERT INTO p2p_settings (setting_key, setting_value, description, updated_by) VALUES
(
    'escrow_timeout_hours',
    '24',
    'Default timeout for escrow in hours',
    'system'
),
(
    'dispute_timeout_hours',
    '72',
    'Default timeout for dispute resolution in hours',
    'system'
),
(
    'min_trade_amount',
    '10',
    'Minimum trade amount in USD',
    'system'
),
(
    'max_trade_amount',
    '100000',
    'Maximum trade amount in USD',
    'system'
),
(
    'platform_fee_percentage',
    '0.5',
    'Platform fee percentage',
    'system'
),
(
    'supported_cryptocurrencies',
    '["BTC", "ETH", "USDT", "USDC", "BNB", "ADA", "DOT", "MATIC", "AVAX", "SOL"]',
    'List of supported cryptocurrencies for P2P trading',
    'system'
),
(
    'supported_fiat_currencies',
    '["USD", "EUR", "GBP", "JPY", "CNY", "INR", "BRL", "RUB", "KRW", "AUD", "CAD", "CHF", "SGD", "HKD", "MXN", "ZAR", "TRY", "AED", "SAR", "EGP"]',
    'List of supported fiat currencies for P2P trading',
    'system'
),
(
    'supported_payment_methods',
    '["bank_transfer", "paypal", "wise", "revolut", "cash_app", "venmo", "zelle", "alipay", "wechat_pay", "upi", "pix", "interac"]',
    'List of supported payment methods',
    'system'
),
(
    'kyc_required_for_p2p',
    'true',
    'Whether KYC verification is required for P2P trading',
    'system'
),
(
    'max_active_orders_per_user',
    '10',
    'Maximum number of active orders per user',
    'system'
),
(
    'auto_release_enabled',
    'false',
    'Whether automatic crypto release is enabled after payment confirmation',
    'system'
),
(
    'dispute_escalation_hours',
    '24',
    'Hours after which unresolved disputes are escalated',
    'system'
),
(
    'feedback_required',
    'true',
    'Whether feedback is required after trade completion',
    'system'
),
(
    'supported_countries',
    '["US", "GB", "DE", "FR", "IT", "ES", "NL", "BE", "AT", "CH", "SE", "NO", "DK", "FI", "IE", "PT", "GR", "PL", "CZ", "HU", "SK", "SI", "EE", "LV", "LT", "LU", "MT", "CY", "BG", "RO", "HR", "CA", "AU", "NZ", "JP", "KR", "SG", "HK", "TW", "MY", "TH", "PH", "ID", "VN", "IN", "BD", "PK", "LK", "NP", "MM", "KH", "LA", "BN", "MV", "BT", "MN", "KZ", "UZ", "KG", "TJ", "TM", "AF", "IR", "IQ", "SA", "AE", "QA", "BH", "KW", "OM", "YE", "JO", "LB", "SY", "IL", "PS", "TR", "GE", "AM", "AZ", "RU", "UA", "BY", "MD", "LT", "LV", "EE", "FI", "SE", "NO", "DK", "IS", "BR", "AR", "CL", "PE", "CO", "VE", "UY", "PY", "BO", "EC", "GY", "SR", "GF", "FK", "MX", "GT", "BZ", "SV", "HN", "NI", "CR", "PA", "CU", "JM", "HT", "DO", "PR", "VI", "AG", "DM", "LC", "VC", "GD", "BB", "TT", "GY", "SR", "GF", "ZA", "NA", "BW", "ZW", "ZM", "MW", "MZ", "SZ", "LS", "MG", "MU", "SC", "KM", "YT", "RE", "SH", "NG", "GH", "CI", "BF", "ML", "NE", "SN", "GM", "GW", "SL", "LR", "TG", "BJ", "CV", "ST", "GQ", "GA", "CG", "CD", "CF", "CM", "TD", "SD", "SS", "ET", "ER", "DJ", "SO", "KE", "UG", "RW", "BI", "TZ", "EG", "LY", "TN", "DZ", "MA", "EH"]',
    'List of supported countries for P2P trading',
    'system'
);

-- Insert sample payment method configurations
INSERT INTO p2p_settings (setting_key, setting_value, description, updated_by) VALUES
(
    'payment_method_bank_transfer',
    '{"min_amount": 50, "max_amount": 50000, "processing_time": "1-3 business days", "countries": ["US", "GB", "DE", "FR", "IT", "ES", "CA", "AU"], "currencies": ["USD", "EUR", "GBP", "CAD", "AUD"]}',
    'Bank transfer payment method configuration',
    'system'
),
(
    'payment_method_paypal',
    '{"min_amount": 10, "max_amount": 10000, "processing_time": "instant", "countries": ["US", "GB", "DE", "FR", "IT", "ES", "CA", "AU", "NL", "BE"], "currencies": ["USD", "EUR", "GBP", "CAD", "AUD"]}',
    'PayPal payment method configuration',
    'system'
),
(
    'payment_method_wise',
    '{"min_amount": 20, "max_amount": 25000, "processing_time": "1-2 business days", "countries": ["US", "GB", "DE", "FR", "IT", "ES", "CA", "AU", "SG", "HK"], "currencies": ["USD", "EUR", "GBP", "CAD", "AUD", "SGD", "HKD"]}',
    'Wise (formerly TransferWise) payment method configuration',
    'system'
),
(
    'payment_method_revolut',
    '{"min_amount": 10, "max_amount": 15000, "processing_time": "instant", "countries": ["GB", "DE", "FR", "IT", "ES", "PL", "IE", "LT"], "currencies": ["EUR", "GBP", "USD", "PLN"]}',
    'Revolut payment method configuration',
    'system'
),
(
    'payment_method_alipay',
    '{"min_amount": 100, "max_amount": 50000, "processing_time": "instant", "countries": ["CN", "HK", "SG", "MY"], "currencies": ["CNY", "HKD", "SGD", "MYR"]}',
    'Alipay payment method configuration',
    'system'
),
(
    'payment_method_upi',
    '{"min_amount": 100, "max_amount": 100000, "processing_time": "instant", "countries": ["IN"], "currencies": ["INR"]}',
    'UPI (Unified Payments Interface) payment method configuration',
    'system'
),
(
    'payment_method_pix',
    '{"min_amount": 50, "max_amount": 50000, "processing_time": "instant", "countries": ["BR"], "currencies": ["BRL"]}',
    'PIX payment method configuration',
    'system'
);
