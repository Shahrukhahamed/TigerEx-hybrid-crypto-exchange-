FROM ubuntu:22.04 as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    pkg-config \
    libboost-all-dev \
    libpqxx-dev \
    libpq-dev \
    libssl-dev \
    librdkafka-dev \
    libhiredis-dev \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Install Redis++
RUN git clone https://github.com/sewenew/redis-plus-plus.git && \
    cd redis-plus-plus && \
    mkdir build && cd build && \
    cmake .. && make && make install

# Install Prometheus C++ client
RUN git clone https://github.com/jupp0r/prometheus-cpp.git && \
    cd prometheus-cpp && \
    git submodule init && git submodule update && \
    mkdir build && cd build && \
    cmake .. -DENABLE_PULL=OFF -DENABLE_PUSH=OFF && \
    make && make install

WORKDIR /app

# Copy source code
COPY . .

# Build the application
RUN mkdir build && cd build && \
    cmake .. -DCMAKE_BUILD_TYPE=Release && \
    make -j$(nproc)

# Runtime stage
FROM ubuntu:22.04

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libboost-system1.74.0 \
    libboost-filesystem1.74.0 \
    libboost-thread1.74.0 \
    libpqxx-6.4 \
    libpq5 \
    libssl3 \
    librdkafka1 \
    libhiredis0.14 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy built application
COPY --from=builder /app/build/TigerExAdvancedTradingEngine /app/
COPY --from=builder /usr/local/lib/libredis++.so* /usr/local/lib/
COPY --from=builder /usr/local/lib/libprometheus-cpp-core.so* /usr/local/lib/

# Update library cache
RUN ldconfig

WORKDIR /app

# Create non-root user
RUN useradd -m -u 1000 tigerex && chown -R tigerex:tigerex /app
USER tigerex

# Expose port
EXPOSE 8091

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8091/health || exit 1

# Run the application
CMD ["./TigerExAdvancedTradingEngine"]