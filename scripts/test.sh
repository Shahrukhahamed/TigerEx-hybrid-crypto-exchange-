#!/bin/bash

# TigerEx Testing Script
# Comprehensive testing suite for all components

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
TEST_TYPE=${1:-all}
COVERAGE_THRESHOLD=80
PARALLEL_JOBS=4

# Check prerequisites
check_prerequisites() {
    log_info "Checking test prerequisites..."
    
    # Check Python and pytest
    if ! command -v python3 &> /dev/null; then
        log_error "Python3 is not installed"
        exit 1
    fi
    
    if ! python3 -c "import pytest" &> /dev/null; then
        log_error "pytest is not installed. Run: pip install pytest"
        exit 1
    fi
    
    # Check Node.js and npm
    if ! command -v node &> /dev/null; then
        log_error "Node.js is not installed"
        exit 1
    fi
    
    if ! command -v npm &> /dev/null; then
        log_error "npm is not installed"
        exit 1
    fi
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Setup test environment
setup_test_environment() {
    log_info "Setting up test environment..."
    
    # Create test databases
    docker run -d --name test-postgres \
        -e POSTGRES_DB=tigerex_test \
        -e POSTGRES_USER=test \
        -e POSTGRES_PASSWORD=test \
        -p 5433:5432 \
        postgres:15-alpine || true
    
    docker run -d --name test-redis \
        -p 6380:6379 \
        redis:7-alpine || true
    
    # Wait for databases to be ready
    sleep 10
    
    # Set test environment variables
    export DATABASE_URL="postgresql://test:test@localhost:5433/tigerex_test"
    export REDIS_URL="redis://localhost:6380"
    export ENVIRONMENT="test"
    
    log_success "Test environment setup completed"
}

# Cleanup test environment
cleanup_test_environment() {
    log_info "Cleaning up test environment..."
    
    docker stop test-postgres test-redis || true
    docker rm test-postgres test-redis || true
    
    log_success "Test environment cleaned up"
}

# Run unit tests
run_unit_tests() {
    log_info "Running unit tests..."
    
    # Python services unit tests
    python_services=(
        "nft-marketplace"
        "copy-trading"
        "compliance-engine"
        "institutional-services"
        "risk-management"
    )
    
    for service in "${python_services[@]}"; do
        if [ -d "backend/${service}" ]; then
            log_info "Running unit tests for ${service}..."
            cd "backend/${service}"
            
            # Install dependencies
            if [ -f "requirements.txt" ]; then
                pip install -r requirements.txt
            fi
            
            # Run tests with coverage
            python -m pytest tests/unit/ \
                --cov=src \
                --cov-report=html \
                --cov-report=term \
                --cov-fail-under=${COVERAGE_THRESHOLD} \
                -v
            
            cd - > /dev/null
        fi
    done
    
    # Frontend unit tests
    if [ -d "frontend" ]; then
        log_info "Running frontend unit tests..."
        cd frontend
        
        npm install
        npm run test:unit
        
        cd - > /dev/null
    fi
    
    log_success "Unit tests completed"
}

# Run integration tests
run_integration_tests() {
    log_info "Running integration tests..."
    
    # Start test services
    docker-compose -f devops/docker-compose.test.yml up -d
    
    # Wait for services to be ready
    sleep 30
    
    # Run integration tests
    python -m pytest tests/integration/ \
        --maxfail=5 \
        --tb=short \
        -v \
        --durations=10
    
    # Stop test services
    docker-compose -f devops/docker-compose.test.yml down
    
    log_success "Integration tests completed"
}

# Run end-to-end tests
run_e2e_tests() {
    log_info "Running end-to-end tests..."
    
    # Start full application stack
    docker-compose -f devops/docker-compose.yml up -d
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 60
    
    # Run E2E tests
    if [ -d "tests/e2e" ]; then
        cd tests/e2e
        npm install
        npm run test
        cd - > /dev/null
    fi
    
    # Stop application stack
    docker-compose -f devops/docker-compose.yml down
    
    log_success "End-to-end tests completed"
}

# Run performance tests
run_performance_tests() {
    log_info "Running performance tests..."
    
    # Start application stack
    docker-compose -f devops/docker-compose.yml up -d
    
    # Wait for services to be ready
    sleep 60
    
    # Run load tests with Artillery or k6
    if command -v k6 &> /dev/null; then
        log_info "Running load tests with k6..."
        k6 run tests/performance/load-test.js
    else
        log_warning "k6 not installed, skipping performance tests"
    fi
    
    # Stop application stack
    docker-compose -f devops/docker-compose.yml down
    
    log_success "Performance tests completed"
}

# Run security tests
run_security_tests() {
    log_info "Running security tests..."
    
    # Static security analysis
    if command -v bandit &> /dev/null; then
        log_info "Running Bandit security analysis..."
        find backend -name "*.py" -exec bandit {} \;
    fi
    
    # Dependency vulnerability check
    if command -v safety &> /dev/null; then
        log_info "Checking for vulnerable dependencies..."
        find backend -name "requirements.txt" -exec safety check -r {} \;
    fi
    
    # Frontend security check
    if [ -d "frontend" ]; then
        cd frontend
        if command -v npm &> /dev/null; then
            npm audit
        fi
        cd - > /dev/null
    fi
    
    log_success "Security tests completed"
}

# Run linting and code quality checks
run_code_quality_checks() {
    log_info "Running code quality checks..."
    
    # Python linting
    python_services=(
        "nft-marketplace"
        "copy-trading"
        "compliance-engine"
        "institutional-services"
        "risk-management"
    )
    
    for service in "${python_services[@]}"; do
        if [ -d "backend/${service}" ]; then
            log_info "Running linting for ${service}..."
            cd "backend/${service}"
            
            # Black formatting check
            if command -v black &> /dev/null; then
                black --check src/ || log_warning "Code formatting issues found in ${service}"
            fi
            
            # Flake8 linting
            if command -v flake8 &> /dev/null; then
                flake8 src/ || log_warning "Linting issues found in ${service}"
            fi
            
            # MyPy type checking
            if command -v mypy &> /dev/null; then
                mypy src/ || log_warning "Type checking issues found in ${service}"
            fi
            
            cd - > /dev/null
        fi
    done
    
    # Frontend linting
    if [ -d "frontend" ]; then
        log_info "Running frontend linting..."
        cd frontend
        
        if [ -f "package.json" ]; then
            npm run lint || log_warning "Frontend linting issues found"
            npm run type-check || log_warning "Frontend type checking issues found"
        fi
        
        cd - > /dev/null
    fi
    
    log_success "Code quality checks completed"
}

# Generate test report
generate_test_report() {
    log_info "Generating test report..."
    
    # Create reports directory
    mkdir -p reports
    
    # Combine coverage reports
    if command -v coverage &> /dev/null; then
        coverage combine
        coverage html -d reports/coverage
        coverage xml -o reports/coverage.xml
    fi
    
    # Generate test summary
    cat > reports/test-summary.md << EOF
# TigerEx Test Report

## Test Summary
- **Date**: $(date)
- **Environment**: ${ENVIRONMENT:-test}
- **Coverage Threshold**: ${COVERAGE_THRESHOLD}%

## Test Results
- Unit Tests: $([ -f "reports/unit-tests.xml" ] && echo "✅ PASSED" || echo "❌ FAILED")
- Integration Tests: $([ -f "reports/integration-tests.xml" ] && echo "✅ PASSED" || echo "❌ FAILED")
- E2E Tests: $([ -f "reports/e2e-tests.xml" ] && echo "✅ PASSED" || echo "❌ FAILED")
- Performance Tests: $([ -f "reports/performance-tests.xml" ] && echo "✅ PASSED" || echo "❌ FAILED")
- Security Tests: $([ -f "reports/security-tests.xml" ] && echo "✅ PASSED" || echo "❌ FAILED")

## Coverage Report
Coverage report available at: reports/coverage/index.html

## Next Steps
1. Review failed tests and fix issues
2. Ensure coverage meets threshold (${COVERAGE_THRESHOLD}%)
3. Address any security vulnerabilities
4. Deploy to staging environment for further testing
EOF
    
    log_success "Test report generated at reports/test-summary.md"
}

# Main test function
main() {
    log_info "Starting TigerEx test suite..."
    log_info "Test type: ${TEST_TYPE}"
    
    case "${TEST_TYPE}" in
        "unit")
            check_prerequisites
            setup_test_environment
            run_unit_tests
            cleanup_test_environment
            ;;
        "integration")
            check_prerequisites
            setup_test_environment
            run_integration_tests
            cleanup_test_environment
            ;;
        "e2e")
            check_prerequisites
            run_e2e_tests
            ;;
        "performance")
            check_prerequisites
            run_performance_tests
            ;;
        "security")
            check_prerequisites
            run_security_tests
            ;;
        "quality")
            check_prerequisites
            run_code_quality_checks
            ;;
        "all")
            check_prerequisites
            setup_test_environment
            run_unit_tests
            run_integration_tests
            cleanup_test_environment
            run_e2e_tests
            run_performance_tests
            run_security_tests
            run_code_quality_checks
            generate_test_report
            ;;
        *)
            log_error "Unknown test type: ${TEST_TYPE}"
            usage
            exit 1
            ;;
    esac
    
    log_success "TigerEx test suite completed!"
}

# Script usage
usage() {
    echo "Usage: $0 [test_type]"
    echo ""
    echo "Test types:"
    echo "  unit         - Run unit tests only"
    echo "  integration  - Run integration tests only"
    echo "  e2e          - Run end-to-end tests only"
    echo "  performance  - Run performance tests only"
    echo "  security     - Run security tests only"
    echo "  quality      - Run code quality checks only"
    echo "  all          - Run all tests (default)"
    echo ""
    echo "Examples:"
    echo "  $0           # Run all tests"
    echo "  $0 unit      # Run only unit tests"
    echo "  $0 security  # Run only security tests"
}

# Handle script arguments
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    usage
    exit 0
fi

# Trap to cleanup on exit
trap cleanup_test_environment EXIT

# Run main function
main "$@"
