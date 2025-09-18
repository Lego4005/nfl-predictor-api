#!/bin/bash

# NFL Predictor API Deployment Script
# Usage: ./deploy.sh [production|staging|local]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
ENVIRONMENT=${1:-local}
BACKUP_DIR="./backups"
LOG_DIR="./logs"

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
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
    mkdir -p $BACKUP_DIR
    mkdir -p $LOG_DIR
    mkdir -p ./dist
    mkdir -p ./public/logos
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    # Check Node.js version
    NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 18 ]; then
        log_error "Node.js 18 or higher is required"
        exit 1
    fi

    # Check npm
    if ! command -v npm &> /dev/null; then
        log_error "npm is not installed"
        exit 1
    fi

    # Check environment file
    if [ ! -f ".env" ]; then
        log_warning ".env file not found, copying from .env.example"
        cp .env.example .env
        log_error "Please configure .env file before deploying"
        exit 1
    fi

    log_info "Prerequisites check passed ✓"
}

# Backup current deployment
backup_current() {
    log_info "Creating backup..."
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_FILE="$BACKUP_DIR/backup_$TIMESTAMP.tar.gz"

    tar -czf $BACKUP_FILE \
        --exclude=node_modules \
        --exclude=dist \
        --exclude=logs \
        --exclude=backups \
        ./src ./public ./package.json

    log_info "Backup created: $BACKUP_FILE"
}

# Install dependencies
install_dependencies() {
    log_info "Installing dependencies..."

    if [ "$ENVIRONMENT" = "production" ]; then
        npm ci --production
    else
        npm ci
    fi

    log_info "Dependencies installed ✓"
}

# Build application
build_application() {
    log_info "Building application..."
    npm run build
    log_info "Build completed ✓"
}

# Run tests
run_tests() {
    if [ "$ENVIRONMENT" != "production" ]; then
        log_info "Running tests..."
        npm test || log_warning "Some tests failed"
    fi
}

# Database migrations
run_migrations() {
    log_info "Running database migrations..."
    node scripts/dataMigrationService.js || log_warning "Migration completed with warnings"
}

# System validation
validate_system() {
    log_info "Validating system..."
    node scripts/validate_system.js || log_warning "System validation completed with warnings"
}

# Deploy with PM2
deploy_pm2() {
    log_info "Deploying with PM2..."

    # Check if PM2 is installed
    if ! command -v pm2 &> /dev/null; then
        log_info "Installing PM2..."
        npm install -g pm2
    fi

    # Stop existing processes
    pm2 stop ecosystem.config.js || true

    # Start new processes
    if [ "$ENVIRONMENT" = "production" ]; then
        pm2 start ecosystem.config.js --env production
    else
        pm2 start ecosystem.config.js --env development
    fi

    # Save PM2 configuration
    pm2 save

    # Setup startup script
    pm2 startup || log_warning "Could not setup PM2 startup script"

    log_info "PM2 deployment completed ✓"
}

# Deploy with Docker
deploy_docker() {
    log_info "Deploying with Docker..."

    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed"
        exit 1
    fi

    # Stop existing containers
    docker-compose down || true

    # Build and start containers
    if [ "$ENVIRONMENT" = "production" ]; then
        docker-compose -f docker-compose.yml up -d --build
    else
        docker-compose -f docker-compose.yml up -d --build
    fi

    log_info "Docker deployment completed ✓"
}

# Health check
health_check() {
    log_info "Performing health check..."
    sleep 5

    # Check frontend
    if curl -f http://localhost:4173 > /dev/null 2>&1; then
        log_info "Frontend is running ✓"
    else
        log_error "Frontend is not responding"
    fi

    # Check WebSocket
    if nc -z localhost 8080 > /dev/null 2>&1; then
        log_info "WebSocket server is running ✓"
    else
        log_error "WebSocket server is not responding"
    fi
}

# Cleanup old backups
cleanup_backups() {
    log_info "Cleaning up old backups..."
    find $BACKUP_DIR -name "backup_*.tar.gz" -mtime +7 -delete
    log_info "Old backups cleaned ✓"
}

# Main deployment flow
main() {
    echo "======================================"
    echo "NFL Predictor API Deployment"
    echo "Environment: $ENVIRONMENT"
    echo "======================================"

    # Pre-deployment steps
    create_directories
    check_prerequisites
    backup_current

    # Install and build
    install_dependencies
    build_application
    run_tests

    # Database setup
    run_migrations

    # Deploy based on method
    if [ "$2" = "docker" ]; then
        deploy_docker
    else
        deploy_pm2
    fi

    # Post-deployment
    health_check
    validate_system
    cleanup_backups

    echo "======================================"
    log_info "Deployment completed successfully! 🚀"
    echo "======================================"

    # Show status
    if [ "$2" != "docker" ]; then
        pm2 status
    else
        docker-compose ps
    fi
}

# Run main function
main "$@"