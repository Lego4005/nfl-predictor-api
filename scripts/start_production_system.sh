#!/bin/bash

# Production System Startup Script for NFL Expert Prediction System
# Handles complete system initialization with health checks and monitoring

set -e  # Exit on any error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_DIR="$PROJECT_ROOT/logs"
ENV_FILE="$PROJECT_ROOT/.env.production"

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

# Create necessary directories
create_directories() {
    log_info "Creating necessary directories..."

    mkdir -p "$LOG_DIR"/{api,expert_system,database,performance,training,nginx}
    mkdir -p "$PROJECT_ROOT"/{models,memory,expert_memories,ssl}
    mkdir -p "$PROJECT_ROOT"/config/{grafana/{dashboards,datasources},prometheus}

    log_success "Directories created"
}

# Validate environment configuration
validate_environment() {
    log_info "Validating environment configuration..."

    if [[ ! -f "$ENV_FILE" ]]; then
        log_error "Production environment file not found: $ENV_FILE"
        log_info "Please copy .env.production.template to .env.production and configure it"
        exit 1
    fi

    # Source environment file
    source "$ENV_FILE"

    # Check required variables
    required_vars=(
        "DATABASE_URL"
        "SUPABASE_URL"
        "SUPABASE_ANON_KEY"
        "REDIS_PASSWORD"
        "OPENAI_API_KEY"
        "ANTHROPIC_API_KEY"
    )

    missing_vars=()
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            missing_vars+=("$var")
        fi
    done

    if [[ ${#missing_vars[@]} -gt 0 ]]; then
        log_error "Missing required environment variables:"
        for var in "${missing_vars[@]}"; do
            log_error "  - $var"
        done
        exit 1
    fi

    log_success "Environment configuration validated"
}

# Check system dependencies
check_dependencies() {
    log_info "Checking system dependencies..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi

    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed"
        exit 1
    fi

    # Check Python
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is not installed"
        exit 1
    fi

    # Check Node.js
    if ! command -v node &> /dev/null; then
        log_error "Node.js is not installed"
        exit 1
    fi

    log_success "System dependencies validated"
}

# Setup SSL certificates (self-signed for development)
setup_ssl() {
    log_info "Setting up SSL certificates..."

    SSL_DIR="$PROJECT_ROOT/ssl"

    if [[ ! -f "$SSL_DIR/cert.pem" ]] || [[ ! -f "$SSL_DIR/key.pem" ]]; then
        log_warning "SSL certificates not found, generating self-signed certificates..."

        openssl req -x509 -newkey rsa:4096 -keyout "$SSL_DIR/key.pem" -out "$SSL_DIR/cert.pem" \
            -days 365 -nodes -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"

        log_success "Self-signed SSL certificates generated"
    else
        log_success "SSL certificates found"
    fi
}

# Initialize database schema
initialize_database() {
    log_info "Initializing database schema..."

    cd "$PROJECT_ROOT"

    # Run database migrations
    if [[ -f "scripts/apply_migration.py" ]]; then
        python3 scripts/apply_migration.py
        log_success "Database migrations applied"
    else
        log_warning "No migration script found, skipping database initialization"
    fi
}

# Build Docker images
build_images() {
    log_info "Building Docker images..."

    cd "$PROJECT_ROOT"

    # Build main application image
    docker-compose -f docker-compose.prod.yml build --no-cache

    log_success "Docker images built"
}

# Start core services
start_core_services() {
    log_info "Starting core services..."

    cd "$PROJECT_ROOT"

    # Start infrastructure services first
    docker-compose -f docker-compose.prod.yml up -d redis prometheus grafana

    # Wait for services to be ready
    log_info "Waiting for core services to be ready..."
    sleep 30

    # Check Redis health
    if ! docker-compose -f docker-compose.prod.yml exec -T redis redis-cli ping > /dev/null 2>&1; then
        log_error "Redis is not responding"
        exit 1
    fi

    log_success "Core services started"
}

# Start application services
start_application_services() {
    log_info "Starting application services..."

    cd "$PROJECT_ROOT"

    # Start main API
    docker-compose -f docker-compose.prod.yml up -d nfl-predictor-api

    # Wait for API to be ready
    log_info "Waiting for API to be ready..."
    sleep 60

    # Health check
    max_attempts=30
    attempt=1

    while [[ $attempt -le $max_attempts ]]; do
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            log_success "API is responding"
            break
        fi

        log_info "Attempt $attempt/$max_attempts: Waiting for API..."
        sleep 10
        ((attempt++))
    done

    if [[ $attempt -gt $max_attempts ]]; then
        log_error "API failed to start within timeout"
        exit 1
    fi

    # Start expert system
    docker-compose -f docker-compose.prod.yml up -d expert-system

    # Start monitoring dashboard
    docker-compose -f docker-compose.prod.yml up -d monitoring-dashboard

    # Start nginx
    docker-compose -f docker-compose.prod.yml up -d nginx

    log_success "Application services started"
}

# Run system health check
run_health_check() {
    log_info "Running comprehensive health check..."

    cd "$PROJECT_ROOT"

    # Run health check script
    if python3 scripts/monitoring_dashboard.py health; then
        log_success "System health check passed"
    else
        log_warning "System health check reported issues"
    fi
}

# Display system status
display_status() {
    log_info "System Status:"
    echo

    cd "$PROJECT_ROOT"

    # Show running containers
    docker-compose -f docker-compose.prod.yml ps

    echo
    log_info "Service URLs:"
    echo "  🌐 Main Application: https://localhost"
    echo "  📊 Grafana Dashboard: http://localhost:3000"
    echo "  📈 Prometheus: http://localhost:9090"
    echo "  🏥 Health Check: http://localhost:8000/health"
    echo "  📋 API Documentation: http://localhost:8000/docs"

    echo
    log_info "Log Files:"
    echo "  📝 Application Logs: $LOG_DIR/"
    echo "  🐳 Docker Logs: docker-compose -f docker-compose.prod.yml logs -f"

    echo
    log_info "Management Commands:"
    echo "  📊 Monitoring Dashboard: python3 scripts/monitoring_dashboard.py dashboard"
    echo "  🏥 Health Check: python3 scripts/monitoring_dashboard.py health"
    echo "  🎯 Training Status: python3 scripts/monitoring_dashboard.py training"
    echo "  🔧 Maintenance: python3 scripts/monitoring_dashboard.py maintenance"
}

# Setup monitoring configuration
setup_monitoring() {
    log_info "Setting up monitoring configuration..."

    # Create Prometheus configuration
    cat > "$PROJECT_ROOT/config/prometheus/prometheus.yml" << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'nfl-predictor-api'
    static_configs:
      - targets: ['nfl-predictor-api:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:80']
EOF

    # Create Grafana datasource configuration
    mkdir -p "$PROJECT_ROOT/config/grafana/datasources"
    cat > "$PROJECT_ROOT/config/grafana/datasources/prometheus.yml" << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF

    log_success "Monitoring configuration created"
}

# Main execution
main() {
    log_info "Starting NFL Expert Prediction System Production Deployment"
    echo "================================================================"

    # Pre-flight checks
    create_directories
    validate_environment
    check_dependencies
    setup_ssl
    setup_monitoring

    # Database setup
    initialize_database

    # Docker deployment
    build_images
    start_core_services
    start_application_services

    # Post-deployment validation
    run_health_check
    display_status

    echo
    log_success "🎉 NFL Expert Prediction System is now running in production mode!"
    echo "================================================================"

    # Keep script running to show logs
    if [[ "${1:-}" == "--follow-logs" ]]; then
        log_info "Following logs (Ctrl+C to exit)..."
        cd "$PROJECT_ROOT"
        docker-compose -f docker-compose.prod.yml logs -f
    fi
}

# Handle script interruption
trap 'log_warning "Deployment interrupted"; exit 1' INT TERM

# Run main function
main "$@"
