# TigerEx API Documentation
## Complete API Reference for All Services

### 🌟 Overview
TigerEx provides comprehensive REST and WebSocket APIs for all platform features. Our APIs are designed for high performance, reliability, and ease of use.

---

## 🔐 Authentication

### API Key Authentication
```http
GET /api/v1/account/info
X-API-Key: your_api_key
X-API-Secret: your_api_secret
X-Timestamp: 1640995200000
X-Signature: calculated_signature
```

### JWT Token Authentication
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "twoFactorCode": "123456"
}
```

---

## 💳 Payment Gateway API

### Base URL: `https://api.tigerex.com/payment`

#### Create Payment Intent
```http
POST /api/v1/payments/intent
Content-Type: application/json
Authorization: Bearer {token}

{
  "amount": "100.00",
  "currency": "USD",
  "payment_method": "CREDIT_CARD",
  "payment_provider": "STRIPE",
  "metadata": {
    "order_id": "order_123"
  }
}
```

**Response:**
```json
{
  "payment_intent_id": "pi_1234567890",
  "client_secret": "pi_1234567890_secret_abcdef",
  "amount": "100.00",
  "currency": "USD",
  "status": "PENDING",
  "expires_at": "2024-01-01T12:00:00Z"
}
```

#### Confirm Payment
```http
POST /api/v1/payments/confirm
Content-Type: application/json
Authorization: Bearer {token}

{
  "payment_intent_id": "pi_1234567890",
  "payment_method_id": "pm_1234567890",
  "billing_address": {
    "line1": "123 Main St",
    "city": "New York",
    "state": "NY",
    "postal_code": "10001",
    "country": "US"
  }
}
```

#### Get Payment Methods
```http
GET /api/v1/payments/methods?currency=USD
Authorization: Bearer {token}
```

**Response:**
```json
{
  "payment_methods": [
    {
      "method": "CREDIT_CARD",
      "provider": "stripe",
      "currencies": ["USD", "EUR", "GBP"],
      "fees": {
        "percentage": 2.9,
        "fixed": 0.30
      }
    }
  ]
}
```

#### Add Payment Method
```http
POST /api/v1/payments/methods
Content-Type: application/json
Authorization: Bearer {token}

{
  "payment_method": "CREDIT_CARD",
  "card_details": {
    "number": "4242424242424242",
    "exp_month": 12,
    "exp_year": 2025,
    "cvc": "123",
    "name": "John Doe"
  },
  "billing_address": {
    "line1": "123 Main St",
    "city": "New York",
    "state": "NY",
    "postal_code": "10001",
    "country": "US"
  }
}
```

#### Withdraw Funds
```http
POST /api/v1/payments/withdraw
Content-Type: application/json
Authorization: Bearer {token}

{
  "amount": "50.00",
  "currency": "USD",
  "payment_method_id": "pm_1234567890",
  "destination_address": "0x742d35Cc6634C0532925a3b8D"
}
```

---

## 📈 Advanced Trading Engine API

### Base URL: `https://api.tigerex.com/trading`

#### Submit Order
```http
POST /api/v1/orders
Content-Type: application/json
Authorization: Bearer {token}

{
  "symbol": "BTCUSDT",
  "type": "LIMIT",
  "side": "BUY",
  "quantity": "0.01",
  "price": "45000.00",
  "time_in_force": "GTC",
  "trading_mode": "SPOT",
  "client_order_id": "my_order_123"
}
```

**Response:**
```json
{
  "order_id": "ORD_1640995200000_12345678",
  "client_order_id": "my_order_123",
  "symbol": "BTCUSDT",
  "status": "NEW",
  "type": "LIMIT",
  "side": "BUY",
  "quantity": "0.01",
  "price": "45000.00",
  "executed_qty": "0.00",
  "created_time": "2024-01-01T12:00:00Z"
}
```

#### Cancel Order
```http
DELETE /api/v1/orders/{order_id}
Authorization: Bearer {token}
```

#### Get Open Orders
```http
GET /api/v1/orders/open?symbol=BTCUSDT
Authorization: Bearer {token}
```

#### Get Order Book
```http
GET /api/v1/orderbook/{symbol}?limit=100
```

**Response:**
```json
{
  "symbol": "BTCUSDT",
  "bids": [
    ["44950.00", "0.15"],
    ["44940.00", "0.25"]
  ],
  "asks": [
    ["45000.00", "0.10"],
    ["45010.00", "0.20"]
  ],
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### Get Positions
```http
GET /api/v1/positions
Authorization: Bearer {token}
```

#### Advanced Order Types
```http
POST /api/v1/orders/advanced
Content-Type: application/json
Authorization: Bearer {token}

{
  "symbol": "BTCUSDT",
  "type": "OCO",
  "side": "SELL",
  "quantity": "0.01",
  "price": "46000.00",
  "stop_price": "44000.00",
  "stop_limit_price": "43900.00",
  "time_in_force": "GTC"
}
```

#### Grid Trading
```http
POST /api/v1/strategies/grid
Content-Type: application/json
Authorization: Bearer {token}

{
  "symbol": "BTCUSDT",
  "grid_spacing": "100.00",
  "grid_count": 10,
  "base_quantity": "0.01",
  "upper_price": "50000.00",
  "lower_price": "40000.00"
}
```

---

## 🏦 Lending & Borrowing API

### Base URL: `https://api.tigerex.com/lending`

#### Get Available Products
```http
GET /api/v1/lending/products?type=FLEXIBLE_SAVINGS&asset=BTC
Authorization: Bearer {token}
```

**Response:**
```json
{
  "products": [
    {
      "product_id": "FLEX_BTC_001",
      "name": "BTC Flexible Savings",
      "type": "FLEXIBLE_SAVINGS",
      "asset": "BTC",
      "interest_rate": "0.05",
      "min_amount": "0.001",
      "max_amount": "100.0",
      "is_flexible": true,
      "risk_level": "LOW"
    }
  ]
}
```

#### Subscribe to Product
```http
POST /api/v1/lending/subscribe
Content-Type: application/json
Authorization: Bearer {token}

{
  "product_id": "FLEX_BTC_001",
  "amount": "0.1",
  "auto_renew": true
}
```

#### Redeem Position
```http
POST /api/v1/lending/redeem
Content-Type: application/json
Authorization: Bearer {token}

{
  "position_id": "POS_1640995200000_12345678",
  "amount": "0.05"
}
```

#### Create Loan
```http
POST /api/v1/lending/loans
Content-Type: application/json
Authorization: Bearer {token}

{
  "loan_asset": "USDT",
  "loan_amount": "1000.00",
  "collateral_asset": "BTC",
  "collateral_amount": "0.025",
  "term_days": 30
}
```

#### Repay Loan
```http
POST /api/v1/lending/loans/repay
Content-Type: application/json
Authorization: Bearer {token}

{
  "loan_id": "LOAN_1640995200000_12345678",
  "amount": "500.00",
  "is_full_repayment": false
}
```

#### Get User Positions
```http
GET /api/v1/lending/positions
Authorization: Bearer {token}
```

#### Get User Loans
```http
GET /api/v1/lending/loans
Authorization: Bearer {token}
```

---

## 🔗 Token Listing API

### Base URL: `https://api.tigerex.com/tokens`

#### Submit Token Listing
```http
POST /api/v1/tokens/submit-listing
Content-Type: application/json
Authorization: Bearer {token}

{
  "token_info": {
    "symbol": "TIGER",
    "name": "TigerEx Token",
    "contract_address": "0x742d35Cc6634C0532925a3b8D",
    "blockchain": "ethereum",
    "token_type": "ERC20",
    "decimals": 18,
    "total_supply": "1000000000"
  },
  "listing_type": "HYBRID",
  "requested_pairs": ["USDT", "USDC", "BTC", "ETH"],
  "project_info": {
    "website": "https://tigerex.com",
    "whitepaper": "https://tigerex.com/whitepaper.pdf",
    "description": "TigerEx native token"
  }
}
```

#### Get Listing Status
```http
GET /api/v1/tokens/listing-status/{application_id}
Authorization: Bearer {token}
```

#### Get Listed Tokens
```http
GET /api/v1/tokens/listed?blockchain=ethereum&status=ACTIVE
```

---

## 💧 Liquidity Aggregator API

### Base URL: `https://api.tigerex.com/liquidity`

#### Get Best Route
```http
GET /api/v1/liquidity/route/BTCUSDT?side=BUY&quantity=1.5
Authorization: Bearer {token}
```

**Response:**
```json
{
  "symbol": "BTCUSDT",
  "side": "BUY",
  "quantity": "1.5",
  "routes": [
    {
      "exchange": "binance",
      "quantity": "1.0",
      "price": "45000.00"
    },
    {
      "exchange": "uniswap_v3",
      "quantity": "0.5",
      "price": "45010.00"
    }
  ],
  "total_price": "45003.33",
  "price_impact": "0.0074",
  "execution_time_ms": 150
}
```

#### Execute Route
```http
POST /api/v1/liquidity/execute
Content-Type: application/json
Authorization: Bearer {token}

{
  "route_id": "route_1640995200000_12345678",
  "slippage_tolerance": "0.01"
}
```

#### Get Arbitrage Opportunities
```http
GET /api/v1/liquidity/arbitrage?min_profit=0.5
Authorization: Bearer {token}
```

---

## 🌐 Web3 Integration API

### Base URL: `https://api.tigerex.com/web3`

#### Get Supported Blockchains
```http
GET /api/v1/web3/blockchains
```

#### Deploy Smart Contract
```http
POST /api/v1/web3/contracts/deploy
Content-Type: application/json
Authorization: Bearer {token}

{
  "blockchain": "ethereum",
  "contract_code": "0x608060405234801561001057600080fd5b50...",
  "constructor_args": ["TigerEx Token", "TIGER", 18],
  "gas_limit": "2000000"
}
```

#### Call Smart Contract
```http
POST /api/v1/web3/contracts/call
Content-Type: application/json
Authorization: Bearer {token}

{
  "blockchain": "ethereum",
  "contract_address": "0x742d35Cc6634C0532925a3b8D",
  "function_name": "transfer",
  "function_args": ["0x123...", "1000000000000000000"],
  "gas_limit": "100000"
}
```

#### Get Token Balance
```http
GET /api/v1/web3/balances/{address}?blockchain=ethereum&token=0x742d35Cc6634C0532925a3b8D
Authorization: Bearer {token}
```

#### Create DEX Pool
```http
POST /api/v1/web3/dex/pools
Content-Type: application/json
Authorization: Bearer {token}

{
  "dex_protocol": "uniswap_v3",
  "token_a": "0x742d35Cc6634C0532925a3b8D",
  "token_b": "0xA0b86a33E6441E6C7D3E4C",
  "fee_tier": "3000",
  "initial_price": "1.0"
}
```

---

## 📊 Market Data API

### Base URL: `https://api.tigerex.com/market`

#### Get Ticker
```http
GET /api/v1/market/ticker/{symbol}
```

**Response:**
```json
{
  "symbol": "BTCUSDT",
  "price": "45000.00",
  "price_change": "500.00",
  "price_change_percent": "1.12",
  "high_price": "45500.00",
  "low_price": "44000.00",
  "volume": "1234.56",
  "quote_volume": "55555555.00",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

#### Get Klines
```http
GET /api/v1/market/klines/{symbol}?interval=1h&limit=100&start_time=1640995200000&end_time=1641081600000
```

#### Get Trades
```http
GET /api/v1/market/trades/{symbol}?limit=100
```

#### Get 24hr Statistics
```http
GET /api/v1/market/24hr/{symbol}
```

---

## 👤 Account Management API

### Base URL: `https://api.tigerex.com/account`

#### Get Account Info
```http
GET /api/v1/account/info
Authorization: Bearer {token}
```

**Response:**
```json
{
  "user_id": "user_123456",
  "email": "user@example.com",
  "kyc_status": "VERIFIED",
  "account_type": "INDIVIDUAL",
  "created_at": "2024-01-01T12:00:00Z",
  "permissions": ["SPOT_TRADING", "MARGIN_TRADING", "FUTURES_TRADING"]
}
```

#### Get Balances
```http
GET /api/v1/account/balances
Authorization: Bearer {token}
```

**Response:**
```json
{
  "balances": [
    {
      "asset": "BTC",
      "free": "1.23456789",
      "locked": "0.10000000",
      "total": "1.33456789"
    },
    {
      "asset": "USDT",
      "free": "10000.00",
      "locked": "500.00",
      "total": "10500.00"
    }
  ]
}
```

#### Get Trade History
```http
GET /api/v1/account/trades?symbol=BTCUSDT&limit=100&start_time=1640995200000
Authorization: Bearer {token}
```

#### Get Deposit History
```http
GET /api/v1/account/deposits?asset=BTC&status=SUCCESS&limit=50
Authorization: Bearer {token}
```

#### Get Withdrawal History
```http
GET /api/v1/account/withdrawals?asset=USDT&status=SUCCESS&limit=50
Authorization: Bearer {token}
```

---

## 🔔 Notification Service API

### Base URL: `https://api.tigerex.com/notifications`

#### Get Notifications
```http
GET /api/v1/notifications?type=TRADE&status=UNREAD&limit=50
Authorization: Bearer {token}
```

#### Mark as Read
```http
PUT /api/v1/notifications/{notification_id}/read
Authorization: Bearer {token}
```

#### Create Price Alert
```http
POST /api/v1/notifications/alerts
Content-Type: application/json
Authorization: Bearer {token}

{
  "symbol": "BTCUSDT",
  "condition": "ABOVE",
  "price": "50000.00",
  "notification_methods": ["EMAIL", "PUSH", "SMS"]
}
```

---

## 🌐 WebSocket API

### Base URL: `wss://ws.tigerex.com`

#### Connection
```javascript
const ws = new WebSocket('wss://ws.tigerex.com/stream');

ws.onopen = function() {
    // Subscribe to streams
    ws.send(JSON.stringify({
        method: 'SUBSCRIBE',
        params: ['btcusdt@ticker', 'btcusdt@depth'],
        id: 1
    }));
};
```

#### Market Data Streams
```javascript
// Ticker stream
{
    "stream": "btcusdt@ticker",
    "data": {
        "symbol": "BTCUSDT",
        "price": "45000.00",
        "change": "500.00",
        "changePercent": "1.12",
        "volume": "1234.56",
        "timestamp": 1640995200000
    }
}

// Order book stream
{
    "stream": "btcusdt@depth",
    "data": {
        "symbol": "BTCUSDT",
        "bids": [["44950.00", "0.15"]],
        "asks": [["45000.00", "0.10"]],
        "timestamp": 1640995200000
    }
}

// Trade stream
{
    "stream": "btcusdt@trade",
    "data": {
        "symbol": "BTCUSDT",
        "price": "45000.00",
        "quantity": "0.01",
        "side": "BUY",
        "timestamp": 1640995200000
    }
}
```

#### User Data Streams
```javascript
// Order updates
{
    "stream": "user@orders",
    "data": {
        "order_id": "ORD_1640995200000_12345678",
        "symbol": "BTCUSDT",
        "status": "FILLED",
        "executed_qty": "0.01",
        "avg_price": "45000.00",
        "timestamp": 1640995200000
    }
}

// Balance updates
{
    "stream": "user@balances",
    "data": {
        "asset": "BTC",
        "free": "1.23456789",
        "locked": "0.10000000",
        "timestamp": 1640995200000
    }
}
```

---

## 📈 Rate Limits

### REST API Limits
- **Public endpoints**: 1200 requests per minute
- **Private endpoints**: 6000 requests per minute
- **Order placement**: 100 orders per 10 seconds
- **Order cancellation**: 100 cancellations per 10 seconds

### WebSocket Limits
- **Connections per IP**: 5 connections
- **Subscriptions per connection**: 200 streams
- **Messages per second**: 10 messages

---

## 🔧 Error Handling

### HTTP Status Codes
- `200` - Success
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error
- `503` - Service Unavailable

### Error Response Format
```json
{
  "error": {
    "code": "INSUFFICIENT_BALANCE",
    "message": "Insufficient balance for this operation",
    "details": {
      "required": "100.00",
      "available": "50.00",
      "asset": "USDT"
    }
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "request_id": "req_1640995200000_12345678"
}
```

---

## 🛠️ SDKs and Libraries

### Official SDKs
- **Python**: `pip install tigerex-python`
- **JavaScript/Node.js**: `npm install tigerex-js`
- **Java**: Maven/Gradle dependency
- **C#**: NuGet package
- **Go**: Go module
- **Rust**: Cargo crate

### Example Usage (Python)
```python
from tigerex import TigerExClient

client = TigerExClient(
    api_key='your_api_key',
    api_secret='your_api_secret'
)

# Place order
order = client.create_order(
    symbol='BTCUSDT',
    side='BUY',
    type='LIMIT',
    quantity='0.01',
    price='45000.00'
)

# Get account balance
balances = client.get_account_balances()

# Subscribe to WebSocket
def on_message(msg):
    print(f"Received: {msg}")

client.start_user_socket(on_message)
```

---

## 🧪 Testing

### Sandbox Environment
- **Base URL**: `https://api-sandbox.tigerex.com`
- **WebSocket**: `wss://ws-sandbox.tigerex.com`
- **Test credentials**: Available in developer portal

### Test Data
- Use test API keys for sandbox environment
- Sandbox has separate order books and balances
- All features available for testing

---

## 📚 Additional Resources

### Documentation
- **API Reference**: Complete API documentation
- **Tutorials**: Step-by-step guides
- **Best Practices**: Recommended patterns
- **Changelog**: API version history

### Support
- **Developer Portal**: https://developers.tigerex.com
- **Discord**: Developer community
- **Email**: developers@tigerex.com
- **Status Page**: https://status.tigerex.com

---

*TigerEx API - Powering the Future of Cryptocurrency Trading*