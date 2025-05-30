# How to Run TigerEx Locally

This guide will help you set up and run the TigerEx cryptocurrency exchange platform on your local development environment.

## Prerequisites

Before you begin, ensure you have the following installed on your system:

### Required Software
- **Docker & Docker Compose** (v20.10+)
- **Node.js** (v18.0+)
- **Go** (v1.21+)
- **Rust** (v1.75+)
- **Python** (v3.11+)
- **Git** (v2.30+)

### Optional (for advanced development)
- **Kubernetes** (minikube or kind for local k8s)
- **PostgreSQL** (v15+) - if running without Docker
- **Redis** (v7+) - if running without Docker

## Quick Start (Docker Compose)

The fastest way to get TigerEx running locally is using Docker Compose:

### 1. Clone the Repository
```bash
git clone https://github.com/Shahrukhahamed/TigerEx-hybrid-crypto-exchange-.git
cd TigerEx-hybrid-crypto-exchange-
```

### 2. Start All Services
```bash
cd devops
docker-compose up -d
```

This will start all services including:
- PostgreSQL database
- Redis cache
- Kafka message broker
- All backend microservices
- Frontend application
- Monitoring stack (Prometheus, Grafana)

### 3. Access the Application
- **Web Application**: http://localhost:3000
- **API Gateway**: http://localhost:8000
- **Admin Panel**: http://localhost:3001
- **Grafana Monitoring**: http://localhost:3001 (admin/admin)
- **Kafka UI**: http://localhost:8080

### 4. Create Test User
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@tigerex.com",
    "username": "testuser",
    "password": "password123",
    "first_name": "Test",
    "last_name": "User",
    "country": "US"
  }'
```

## Development Setup (Manual)

For active development, you may want to run services individually:

### 1. Infrastructure Services

Start the required infrastructure services:

```bash
cd devops
docker-compose up -d postgres redis kafka zookeeper
```

### 2. Database Setup

Run the database migrations:

```bash
cd backend/database

# Connect to PostgreSQL
psql -h localhost -U postgres -d tigerex

# Run migrations (in psql)
\i migrations/2025_03_03_000001_create_users_table.sql
\i migrations/2025_03_03_000002_create_admins_table.sql
\i migrations/2025_03_03_000010_create_trading_tables.sql
\i migrations/2025_03_03_000011_create_admin_tables.sql
\i migrations/2025_03_03_000012_create_token_listing_table.sql
\i migrations/2025_03_03_000013_create_blockchain_integration_table.sql

# Run seed data
\i seeds/users_seed.sql
\i seeds/admins_seed.sql
\i seeds/roles_seed.sql
\i seeds/permissions_seed.sql
```

### 3. Backend Services

Start each backend service in separate terminals:

#### Terminal 1 - Matching Engine (C++)
```bash
cd backend/matching-engine

# Install dependencies (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install -y build-essential cmake libssl-dev libboost-all-dev

# Build
mkdir build && cd build
cmake ..
make -j$(nproc)

# Run
./matching_engine
```

#### Terminal 2 - Transaction Engine (Rust)
```bash
cd backend/transaction-engine

# Install Rust (if not installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env

# Run
cargo run
```

#### Terminal 3 - API Gateway (Go)
```bash
cd backend/api-gateway

# Install Go dependencies
go mod download

# Set environment variables
export DATABASE_URL="postgres://postgres:password@localhost:5432/tigerex?sslmode=disable"
export REDIS_URL="redis://localhost:6379"
export JWT_SECRET="your-secret-key"

# Run
go run main.go
```

#### Terminal 4 - Risk Management (Python)
```bash
cd backend/risk-management

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://postgres:password@localhost:5432/tigerex"
export REDIS_URL="redis://localhost:6379"

# Run
python src/main.py
```

#### Terminal 5 - Auth Service (Rust)
```bash
cd backend/auth-service

# Set environment variables
export DATABASE_URL="postgresql://postgres:password@localhost:5432/tigerex"
export REDIS_URL="redis://localhost:6379"
export JWT_SECRET="your-secret-key"

# Run
cargo run
```

### 4. Trading Services

#### Spot Trading (C++)
```bash
cd backend/trading/spot-trading
mkdir build && cd build
cmake ..
make -j$(nproc)
./spot_trading
```

#### Futures Trading USD-M (C++)
```bash
cd backend/trading/futures-trading/usd-m
mkdir build && cd build
cmake ..
make -j$(nproc)
./futures_usd_trading
```

### 5. Frontend Application

#### Terminal 6 - Frontend (Next.js)
```bash
cd frontend

# Install dependencies
npm install

# Set environment variables
export NEXT_PUBLIC_API_URL="http://localhost:8000"
export NEXT_PUBLIC_WS_URL="ws://localhost:8080"

# Run development server
npm run dev
```

## Environment Variables

Create a `.env.local` file in the frontend directory:

```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8080

# Authentication
NEXTAUTH_URL=http://localhost:3000
NEXTAUTH_SECRET=your-nextauth-secret

# Feature Flags
NEXT_PUBLIC_ENABLE_FUTURES=true
NEXT_PUBLIC_ENABLE_OPTIONS=true
NEXT_PUBLIC_ENABLE_NFT=true
```

Create environment files for backend services:

### backend/api-gateway/.env
```env
PORT=8080
DATABASE_URL=postgres://postgres:password@localhost:5432/tigerex?sslmode=disable
REDIS_URL=redis://localhost:6379
JWT_SECRET=your-super-secret-jwt-key
ENVIRONMENT=development
RATE_LIMIT_RPS=100
RATE_LIMIT_BURST=200
```

### backend/transaction-engine/.env
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/tigerex
REDIS_URL=redis://localhost:6379
KAFKA_BROKERS=localhost:9092
```

### backend/risk-management/.env
```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/tigerex
REDIS_URL=redis://localhost:6379
KAFKA_BROKERS=localhost:9092
```

## Testing the Setup

### 1. Health Checks
```bash
# Check API Gateway
curl http://localhost:8000/health

# Check Matching Engine
curl http://localhost:8080/health

# Check Transaction Engine
curl http://localhost:8081/health

# Check Risk Management
curl http://localhost:8082/health
```

### 2. Test Trading Flow

#### Register a User
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "trader@example.com",
    "username": "trader1",
    "password": "securepassword123",
    "first_name": "John",
    "last_name": "Trader",
    "country": "US"
  }'
```

#### Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "trader@example.com",
    "password": "securepassword123"
  }'
```

#### Get Market Data
```bash
curl http://localhost:8000/api/v1/market/ticker/BTCUSDT
```

#### Place an Order (requires authentication token)
```bash
curl -X POST http://localhost:8000/api/v1/order \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -d '{
    "symbol": "BTCUSDT",
    "side": "BUY",
    "type": "LIMIT",
    "quantity": "0.001",
    "price": "50000"
  }'
```

## Troubleshooting

### Common Issues

#### 1. Port Already in Use
```bash
# Find process using port
lsof -i :8000

# Kill process
kill -9 <PID>
```

#### 2. Database Connection Issues
```bash
# Check PostgreSQL is running
docker ps | grep postgres

# Check connection
psql -h localhost -U postgres -d tigerex -c "SELECT 1;"
```

#### 3. Redis Connection Issues
```bash
# Check Redis is running
docker ps | grep redis

# Test connection
redis-cli -h localhost -p 6379 ping
```

#### 4. Kafka Issues
```bash
# Check Kafka is running
docker ps | grep kafka

# List topics
docker exec -it tigerex-kafka kafka-topics --list --bootstrap-server localhost:9092
```

### Performance Optimization

#### 1. Increase File Limits (Linux/macOS)
```bash
# Add to ~/.bashrc or ~/.zshrc
ulimit -n 65536
```

#### 2. Optimize Docker Resources
```bash
# Increase Docker memory to 8GB+
# Increase Docker CPU cores to 4+
```

#### 3. Database Optimization
```sql
-- Connect to PostgreSQL and run:
-- Increase shared_buffers
ALTER SYSTEM SET shared_buffers = '256MB';

-- Increase work_mem
ALTER SYSTEM SET work_mem = '4MB';

-- Reload configuration
SELECT pg_reload_conf();
```

## Development Workflow

### 1. Making Changes

#### Backend Changes
- Modify code in respective service directories
- Services will auto-reload in development mode
- Run tests: `make test` (C++), `cargo test` (Rust), `go test ./...` (Go), `pytest` (Python)

#### Frontend Changes
- Modify code in `frontend/` directory
- Next.js will auto-reload with hot module replacement
- Run tests: `npm test`

### 2. Adding New Features

#### New API Endpoint
1. Add route in `backend/api-gateway/main.go`
2. Implement handler function
3. Add validation and authentication
4. Update API documentation

#### New Trading Feature
1. Add logic in appropriate trading service
2. Update matching engine if needed
3. Add database migrations if required
4. Update frontend components

### 3. Database Changes

#### Adding Migrations
```bash
cd backend/database/migrations
# Create new migration file
touch 2025_03_03_000014_add_new_feature.sql
```

#### Running New Migrations
```bash
psql -h localhost -U postgres -d tigerex -f migrations/2025_03_03_000014_add_new_feature.sql
```

## Monitoring and Debugging

### 1. Logs
```bash
# View logs for specific service
docker-compose logs -f api-gateway
docker-compose logs -f matching-engine
docker-compose logs -f transaction-engine
```

### 2. Metrics
- Access Grafana at http://localhost:3001
- Default credentials: admin/admin
- Pre-configured dashboards for all services

### 3. Database Monitoring
```sql
-- Check active connections
SELECT count(*) FROM pg_stat_activity;

-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
```

### 4. Performance Profiling

#### Go Services
```bash
# Enable pprof endpoint
go tool pprof http://localhost:8000/debug/pprof/profile
```

#### Rust Services
```bash
# Use cargo flamegraph
cargo install flamegraph
cargo flamegraph --bin transaction-engine
```

## Security Considerations

### 1. Development Security
- Use strong passwords for all services
- Enable 2FA for admin accounts
- Regularly update dependencies
- Run security scans: `npm audit`, `cargo audit`

### 2. Network Security
- Services communicate over localhost only
- Use HTTPS in production
- Implement proper CORS policies

### 3. Data Security
- Encrypt sensitive data at rest
- Use secure JWT secrets
- Implement proper session management

## Next Steps

Once you have the local environment running:

1. **Explore the Admin Panel**: Access admin features at http://localhost:3001
2. **Test Trading Features**: Try spot trading, futures, and other features
3. **Review API Documentation**: Check the API endpoints and WebSocket streams
4. **Run Performance Tests**: Use the included load testing scripts
5. **Customize Configuration**: Modify settings for your specific needs

## Getting Help

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section above
2. Review service logs for error messages
3. Check the [GitHub Issues](https://github.com/Shahrukhahamed/TigerEx-hybrid-crypto-exchange-/issues)
4. Join our [Discord community](https://discord.gg/tigerex)
5. Contact support at support@tigerex.com

## Contributing

Ready to contribute? Check out our [Contributing Guide](../../CONTRIBUTING.md) for:
- Code style guidelines
- Testing requirements
- Pull request process
- Development best practices

---

**Happy Trading! 🚀**