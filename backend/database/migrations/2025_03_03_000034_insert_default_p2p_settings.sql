-- Insert Default P2P Trading Settings and Data
-- TigerEx P2P Platform Configuration

-- Insert default payment methods
INSERT INTO p2p_payment_methods (
    method_id, name, code, category, supported_currencies, 
    available_countries, min_amount, max_amount, processing_time_minutes,
    requires_bank_account, requires_phone_verification, requires_id_verification,
    description, instructions, is_active
) VALUES 
-- Bank Transfers
('PM_BANK_TRANSFER', 'Bank Transfer', 'BANK_TRANSFER', 'bank', 
 '["USD", "EUR", "GBP", "CAD", "AUD", "JPY", "CNY", "INR", "BRL", "KRW"]',
 '[]', 10, 1000000, 60, true, true, true,
 'Direct bank-to-bank transfer', 
 'Please provide your bank account details including account number, routing number, and bank name.',
 true),

('PM_WIRE_TRANSFER', 'Wire Transfer', 'WIRE_TRANSFER', 'bank',
 '["USD", "EUR", "GBP", "CAD", "AUD", "JPY"]',
 '[]', 1000, 10000000, 1440, true, true, true,
 'International wire transfer for large amounts',
 'Wire transfers are secure but may take 1-3 business days to process.',
 true),

-- Digital Wallets
('PM_PAYPAL', 'PayPal', 'PAYPAL', 'digital_wallet',
 '["USD", "EUR", "GBP", "CAD", "AUD", "JPY"]',
 '["US", "CA", "GB", "DE", "FR", "IT", "ES", "AU", "JP"]', 1, 10000, 5, false, true, false,
 'PayPal digital wallet payments',
 'Send payment to the provided PayPal email address.',
 true),

('PM_ALIPAY', 'Alipay', 'ALIPAY', 'digital_wallet',
 '["CNY", "USD", "EUR"]',
 '["CN", "HK", "TW", "SG", "MY"]', 1, 50000, 2, false, true, false,
 'Alipay mobile payments',
 'Scan QR code or send to Alipay account.',
 true),

('PM_WECHAT_PAY', 'WeChat Pay', 'WECHAT_PAY', 'digital_wallet',
 '["CNY", "USD"]',
 '["CN", "HK", "TW"]', 1, 20000, 2, false, true, false,
 'WeChat Pay mobile payments',
 'Scan QR code or send to WeChat Pay account.',
 true),

('PM_ZELLE', 'Zelle', 'ZELLE', 'digital_wallet',
 '["USD"]',
 '["US"]', 1, 5000, 5, true, true, false,
 'Zelle instant bank transfers',
 'Send payment using Zelle to the provided email or phone number.',
 true),

('PM_VENMO', 'Venmo', 'VENMO', 'digital_wallet',
 '["USD"]',
 '["US"]', 1, 3000, 5, false, true, false,
 'Venmo peer-to-peer payments',
 'Send payment to Venmo username.',
 true),

-- Cryptocurrency
('PM_CRYPTO_TRANSFER', 'Crypto Transfer', 'CRYPTO_TRANSFER', 'crypto',
 '["USD", "EUR", "BTC", "ETH", "USDT", "USDC"]',
 '[]', 1, 1000000, 30, false, false, false,
 'Direct cryptocurrency transfer',
 'Send crypto to the provided wallet address.',
 true),

-- Cash
('PM_CASH_DEPOSIT', 'Cash Deposit', 'CASH_DEPOSIT', 'cash',
 '["USD", "EUR", "GBP", "CAD", "AUD", "CNY", "INR", "BRL"]',
 '[]', 50, 10000, 120, false, true, true,
 'Cash deposit at bank or ATM',
 'Deposit cash to the provided bank account and upload receipt.',
 true),

-- Gift Cards
('PM_AMAZON_GIFT_CARD', 'Amazon Gift Card', 'AMAZON_GIFT_CARD', 'gift_card',
 '["USD", "EUR", "GBP", "CAD", "AUD", "JPY"]',
 '["US", "CA", "GB", "DE", "FR", "IT", "ES", "AU", "JP"]', 10, 2000, 5, false, false, false,
 'Amazon gift card payments',
 'Provide gift card code and receipt.',
 true),

-- Mobile Money
('PM_MPESA', 'M-Pesa', 'MPESA', 'mobile_money',
 '["KES", "TZS", "UGX"]',
 '["KE", "TZ", "UG"]', 1, 100000, 5, false, true, false,
 'M-Pesa mobile money',
 'Send payment to M-Pesa number.',
 true);

-- Insert default P2P settings
INSERT INTO p2p_settings (setting_key, setting_value, description) VALUES
('platform_fee_percentage', '0.001', 'Platform fee percentage (0.1%)'),
('min_order_amount_usd', '10', 'Minimum order amount in USD equivalent'),
('max_order_amount_usd', '100000', 'Maximum order amount in USD equivalent'),
('default_payment_time_limit', '15', 'Default payment time limit in minutes'),
('max_payment_time_limit', '60', 'Maximum payment time limit in minutes'),
('min_completion_rate_for_ads', '80', 'Minimum completion rate to post ads'),
('max_active_ads_per_user', '10', 'Maximum active ads per user'),
('appeal_processing_time_hours', '24', 'Target appeal processing time in hours'),
('auto_release_time_hours', '1', 'Auto-release time after payment confirmation'),
('feedback_required', 'true', 'Whether feedback is required after order completion'),

('supported_assets', '["BTC", "ETH", "USDT", "USDC", "BNB", "ADA", "SOL", "MATIC", "AVAX", "DOT"]', 'Supported crypto assets for P2P trading'),
('supported_fiat_currencies', '["USD", "EUR", "GBP", "CAD", "AUD", "JPY", "CNY", "INR", "BRL", "KRW", "RUB", "TRY", "MXN", "ARS", "CLP", "COP", "PEN", "VES", "NGN", "GHS", "KES", "ZAR"]', 'Supported fiat currencies'),

('kyc_requirements', '{
  "basic": {"min_order_amount": 0, "max_order_amount": 1000, "daily_limit": 5000},
  "intermediate": {"min_order_amount": 0, "max_order_amount": 10000, "daily_limit": 50000},
  "advanced": {"min_order_amount": 0, "max_order_amount": 100000, "daily_limit": 500000}
}', 'KYC level requirements and limits'),

('trading_hours', '{
  "enabled": false,
  "timezone": "UTC",
  "start_time": "00:00",
  "end_time": "23:59",
  "days": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
}', 'P2P trading hours configuration'),

('dispute_resolution_process', '{
  "auto_escalation_hours": 2,
  "evidence_submission_hours": 24,
  "admin_response_hours": 12,
  "max_resolution_days": 7
}', 'Dispute resolution process configuration'),

('user_verification_requirements', '{
  "phone_verification": true,
  "email_verification": true,
  "id_verification_for_high_volume": true,
  "bank_account_verification": false
}', 'User verification requirements'),

('advertisement_rules', '{
  "min_margin_percentage": -5,
  "max_margin_percentage": 50,
  "max_terms_length": 500,
  "require_payment_method_verification": true,
  "auto_pause_on_low_balance": true
}', 'Advertisement posting rules'),

('chat_features', '{
  "file_upload_enabled": true,
  "max_file_size_mb": 10,
  "allowed_file_types": ["jpg", "jpeg", "png", "pdf", "txt"],
  "message_encryption": true,
  "auto_translate": false
}', 'Chat system features configuration'),

('security_features', '{
  "ip_whitelist_enabled": false,
  "device_fingerprinting": true,
  "suspicious_activity_detection": true,
  "auto_freeze_on_disputes": true,
  "two_factor_for_large_orders": true
}', 'Security features configuration'),

('notification_settings', '{
  "email_notifications": true,
  "sms_notifications": false,
  "push_notifications": true,
  "telegram_bot_enabled": false
}', 'Notification system settings');

-- Insert sample countries and regions
INSERT INTO p2p_settings (setting_key, setting_value, description) VALUES
('supported_countries', '{
  "high_volume": ["US", "CA", "GB", "DE", "FR", "IT", "ES", "AU", "JP", "KR", "SG", "HK"],
  "medium_volume": ["BR", "MX", "AR", "CL", "CO", "PE", "IN", "TH", "MY", "PH", "ID", "VN"],
  "emerging": ["NG", "GH", "KE", "ZA", "EG", "MA", "TN", "TR", "RU", "UA", "PL", "CZ"],
  "restricted": ["CN", "IR", "KP", "SY", "AF"],
  "banned": []
}', 'Country classification for P2P trading'),

('regional_settings', '{
  "Americas": {
    "primary_currencies": ["USD", "CAD", "BRL", "MXN", "ARS"],
    "popular_payment_methods": ["BANK_TRANSFER", "PAYPAL", "ZELLE", "VENMO"],
    "trading_hours": "24/7"
  },
  "Europe": {
    "primary_currencies": ["EUR", "GBP", "CHF", "SEK", "NOK"],
    "popular_payment_methods": ["BANK_TRANSFER", "PAYPAL", "SEPA"],
    "trading_hours": "24/7"
  },
  "Asia": {
    "primary_currencies": ["CNY", "JPY", "KRW", "INR", "SGD"],
    "popular_payment_methods": ["BANK_TRANSFER", "ALIPAY", "WECHAT_PAY", "UPI"],
    "trading_hours": "24/7"
  },
  "Africa": {
    "primary_currencies": ["NGN", "GHS", "KES", "ZAR", "EGP"],
    "popular_payment_methods": ["BANK_TRANSFER", "MPESA", "MOBILE_MONEY"],
    "trading_hours": "24/7"
  }
}', 'Regional P2P trading settings');

-- Insert risk management settings
INSERT INTO p2p_settings (setting_key, setting_value, description) VALUES
('risk_management', '{
  "max_orders_per_day": 50,
  "max_volume_per_day_usd": 100000,
  "velocity_checks": true,
  "blacklist_checking": true,
  "aml_screening": true,
  "suspicious_pattern_detection": true,
  "auto_freeze_threshold": 10000
}', 'Risk management configuration'),

('fraud_detection', '{
  "duplicate_payment_detection": true,
  "velocity_analysis": true,
  "device_fingerprinting": true,
  "behavioral_analysis": true,
  "machine_learning_scoring": true,
  "manual_review_threshold": 5000
}', 'Fraud detection system settings'),

('compliance_settings', '{
  "transaction_reporting": true,
  "suspicious_activity_reporting": true,
  "record_retention_days": 2555,
  "audit_trail_enabled": true,
  "regulatory_reporting": true
}', 'Compliance and regulatory settings');

COMMIT;
