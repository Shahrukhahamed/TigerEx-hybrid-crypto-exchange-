FROM rust:1.75-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    pkg-config \
    libssl-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy Cargo files
COPY Cargo.toml Cargo.lock ./

# Create src directory and dummy main.rs for dependency caching
RUN mkdir src && echo "fn main() {}" > src/main.rs

# Build dependencies
RUN cargo build --release && rm -rf src

# Copy source code
COPY src ./src

# Build application
RUN cargo build --release

# Runtime stage
FROM debian:bookworm-slim

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    ca-certificates \
    libssl3 \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd -m -u 1000 appuser

# Copy binary from builder
COPY --from=builder /app/target/release/spot-trading /usr/local/bin/spot-trading

# Change ownership
RUN chown appuser:appuser /usr/local/bin/spot-trading

USER appuser

EXPOSE 8091

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8091/health || exit 1

CMD ["spot-trading"]
