#!/bin/bash

# TigerEx Production Deployment Script
# This script deploys the TigerEx platform to production environment

set -e  # Exit on any error

# Configuration
ENVIRONMENT=${1:-production}
NAMESPACE="tigerex-${ENVIRONMENT}"
DOCKER_REGISTRY="tigerex"
VERSION=${2:-latest}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if kubectl is installed
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is not installed. Please install kubectl first."
        exit 1
    fi
    
    # Check if docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check if helm is installed
    if ! command -v helm &> /dev/null; then
        log_error "Helm is not installed. Please install Helm first."
        exit 1
    fi
    
    # Check kubectl connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster. Please check your kubeconfig."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."
    
    # Services to build
    services=(
        "api-gateway"
        "matching-engine"
        "transaction-engine"
        "risk-management"
        "dex-integration"
        "nft-marketplace"
        "copy-trading"
        "compliance-engine"
        "institutional-services"
        "notification-service"
        "frontend"
    )
    
    for service in "${services[@]}"; do
        log_info "Building ${service}..."
        
        if [ -f "backend/${service}/Dockerfile" ]; then
            docker build -t "${DOCKER_REGISTRY}/${service}:${VERSION}" "backend/${service}/"
        elif [ -f "frontend/Dockerfile" ] && [ "${service}" = "frontend" ]; then
            docker build -t "${DOCKER_REGISTRY}/${service}:${VERSION}" "frontend/"
        else
            log_warning "Dockerfile not found for ${service}, skipping..."
            continue
        fi
        
        # Push to registry
        log_info "Pushing ${service} to registry..."
        docker push "${DOCKER_REGISTRY}/${service}:${VERSION}"
    done
    
    log_success "Docker images built and pushed"
}

# Create namespace
create_namespace() {
    log_info "Creating namespace ${NAMESPACE}..."
    
    if kubectl get namespace "${NAMESPACE}" &> /dev/null; then
        log_warning "Namespace ${NAMESPACE} already exists"
    else
        kubectl create namespace "${NAMESPACE}"
        log_success "Namespace ${NAMESPACE} created"
    fi
}

# Deploy infrastructure
deploy_infrastructure() {
    log_info "Deploying infrastructure components..."
    
    # Deploy PostgreSQL
    log_info "Deploying PostgreSQL..."
    kubectl apply -f devops/kubernetes/production-deployment.yaml -n "${NAMESPACE}"
    
    # Wait for PostgreSQL to be ready
    log_info "Waiting for PostgreSQL to be ready..."
    kubectl wait --for=condition=ready pod -l app=postgres -n "${NAMESPACE}" --timeout=300s
    
    # Deploy Redis
    log_info "Deploying Redis..."
    kubectl wait --for=condition=ready pod -l app=redis -n "${NAMESPACE}" --timeout=300s
    
    log_success "Infrastructure components deployed"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    # Create a job to run migrations
    cat <<EOF | kubectl apply -f - -n "${NAMESPACE}"
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migration-${VERSION}
  namespace: ${NAMESPACE}
spec:
  template:
    spec:
      containers:
      - name: migration
        image: postgres:15-alpine
        command: ["sh", "-c"]
        args:
        - |
          export PGPASSWORD=\$POSTGRES_PASSWORD
          until pg_isready -h postgres-service -p 5432 -U postgres; do
            echo "Waiting for PostgreSQL..."
            sleep 2
          done
          echo "Running migrations..."
          # Add migration commands here
          echo "Migrations completed"
        env:
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: tigerex-secrets
              key: postgres-password
      restartPolicy: Never
  backoffLimit: 3
EOF
    
    # Wait for migration job to complete
    kubectl wait --for=condition=complete job/db-migration-${VERSION} -n "${NAMESPACE}" --timeout=300s
    
    log_success "Database migrations completed"
}

# Deploy applications
deploy_applications() {
    log_info "Deploying application services..."
    
    # Update image tags in deployment
    sed -i.bak "s/:latest/:${VERSION}/g" devops/kubernetes/production-deployment.yaml
    
    # Apply the deployment
    kubectl apply -f devops/kubernetes/production-deployment.yaml -n "${NAMESPACE}"
    
    # Wait for deployments to be ready
    deployments=(
        "api-gateway"
        "matching-engine"
        "nft-marketplace"
        "copy-trading"
        "compliance-engine"
        "frontend"
    )
    
    for deployment in "${deployments[@]}"; do
        log_info "Waiting for ${deployment} to be ready..."
        kubectl wait --for=condition=available deployment/${deployment} -n "${NAMESPACE}" --timeout=600s
    done
    
    # Restore original file
    mv devops/kubernetes/production-deployment.yaml.bak devops/kubernetes/production-deployment.yaml
    
    log_success "Application services deployed"
}

# Setup monitoring
setup_monitoring() {
    log_info "Setting up monitoring..."
    
    # Deploy Prometheus
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo update
    
    helm upgrade --install prometheus prometheus-community/kube-prometheus-stack \
        --namespace monitoring \
        --create-namespace \
        --set grafana.adminPassword=admin123 \
        --wait
    
    log_success "Monitoring setup completed"
}

# Setup ingress and SSL
setup_ingress() {
    log_info "Setting up ingress and SSL..."
    
    # Install cert-manager if not exists
    if ! kubectl get namespace cert-manager &> /dev/null; then
        kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml
        kubectl wait --for=condition=ready pod -l app=cert-manager -n cert-manager --timeout=300s
    fi
    
    # Create ClusterIssuer for Let's Encrypt
    cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: admin@tigerex.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
    
    log_success "Ingress and SSL setup completed"
}

# Health check
health_check() {
    log_info "Performing health checks..."
    
    # Check if all pods are running
    if kubectl get pods -n "${NAMESPACE}" | grep -v Running | grep -v Completed | grep -q .; then
        log_warning "Some pods are not in Running state:"
        kubectl get pods -n "${NAMESPACE}" | grep -v Running | grep -v Completed
    else
        log_success "All pods are running"
    fi
    
    # Check services
    log_info "Checking services..."
    kubectl get services -n "${NAMESPACE}"
    
    # Check ingress
    log_info "Checking ingress..."
    kubectl get ingress -n "${NAMESPACE}"
    
    log_success "Health checks completed"
}

# Cleanup old resources
cleanup() {
    log_info "Cleaning up old resources..."
    
    # Remove old completed jobs
    kubectl delete jobs --field-selector status.successful=1 -n "${NAMESPACE}" || true
    
    # Remove old replica sets
    kubectl delete rs --all -n "${NAMESPACE}" || true
    
    log_success "Cleanup completed"
}

# Rollback function
rollback() {
    local previous_version=${1:-"previous"}
    log_warning "Rolling back to version: ${previous_version}"
    
    # Rollback deployments
    deployments=$(kubectl get deployments -n "${NAMESPACE}" -o name)
    for deployment in $deployments; do
        kubectl rollout undo "${deployment}" -n "${NAMESPACE}"
    done
    
    # Wait for rollback to complete
    for deployment in $deployments; do
        kubectl rollout status "${deployment}" -n "${NAMESPACE}" --timeout=300s
    done
    
    log_success "Rollback completed"
}

# Main deployment function
main() {
    log_info "Starting TigerEx deployment to ${ENVIRONMENT} environment..."
    log_info "Version: ${VERSION}"
    
    case "${1}" in
        "rollback")
            rollback "${2}"
            ;;
        "health")
            health_check
            ;;
        "cleanup")
            cleanup
            ;;
        *)
            check_prerequisites
            build_images
            create_namespace
            deploy_infrastructure
            run_migrations
            deploy_applications
            setup_monitoring
            setup_ingress
            health_check
            cleanup
            
            log_success "TigerEx deployment completed successfully!"
            log_info "Access the application at: https://tigerex.com"
            log_info "API endpoint: https://api.tigerex.com"
            log_info "WebSocket endpoint: wss://ws.tigerex.com"
            ;;
    esac
}

# Script usage
usage() {
    echo "Usage: $0 [environment] [version]"
    echo "       $0 rollback [version]"
    echo "       $0 health"
    echo "       $0 cleanup"
    echo ""
    echo "Examples:"
    echo "  $0 production v1.0.0    # Deploy version v1.0.0 to production"
    echo "  $0 staging latest       # Deploy latest to staging"
    echo "  $0 rollback v0.9.0      # Rollback to version v0.9.0"
    echo "  $0 health               # Check deployment health"
    echo "  $0 cleanup              # Cleanup old resources"
}

# Handle script arguments
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    usage
    exit 0
fi

# Run main function
main "$@"
