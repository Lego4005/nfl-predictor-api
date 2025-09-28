#!/bin/bash

# Enhanced NFL Prediction Dashboard - Production Deployment Script
# Version: 2.0.0
# Description: Comprehensive deployment script with health checks, rollback, and monitoring

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_NAME="nfl-predictions-enhanced"
COMPOSE_FILE="docker-compose.enhanced.yml"
ENV_FILE=".env.production"
BACKUP_DIR="./backups"
LOG_DIR="./logs"
HEALTH_CHECK_TIMEOUT=300
ROLLBACK_ENABLED=true

# Deployment settings
BUILD_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
APP_VERSION=${1:-"latest"}
ENVIRONMENT=${2:-"production"}
DEPLOY_MODE=${3:-"rolling"} # rolling, blue-green, or full

# Logging function
log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log "Checking prerequisites..."
    
    # Check if Docker is installed and running
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed or not in PATH"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        error "Docker daemon is not running"
        exit 1
    fi

    # Check if Docker Compose is available
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        error "Docker Compose is not installed"
        exit 1
    fi

    # Check if required files exist
    if [[ ! -f "$COMPOSE_FILE" ]]; then
        error "Docker Compose file not found: $COMPOSE_FILE"
        exit 1
    fi

    if [[ ! -f "$ENV_FILE" ]]; then
        warning "Environment file not found: $ENV_FILE"
        warning "Using default environment variables"
    fi

    success "Prerequisites check passed"
}

# Create necessary directories
setup_directories() {
    log "Setting up directories..."
    
    mkdir -p "$BACKUP_DIR"
    mkdir -p "$LOG_DIR"
    mkdir -p "./ssl"
    mkdir -p "./monitoring"
    mkdir -p "./nginx/conf.d"
    mkdir -p "./database/backups"
    
    success "Directories created"
}

# Backup current deployment
backup_current_deployment() {
    if [[ "$ROLLBACK_ENABLED" == "true" ]]; then
        log "Creating backup of current deployment..."
        
        local backup_timestamp=$(date +"%Y%m%d_%H%M%S")
        local backup_path="$BACKUP_DIR/deployment_$backup_timestamp"
        
        mkdir -p "$backup_path"
        
        # Backup database if running
        if docker-compose -f "$COMPOSE_FILE" ps postgres | grep -q "Up"; then
            log "Backing up PostgreSQL database..."
            docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_dump -U nfl_user nfl_predictions > "$backup_path/database.sql" || warning "Database backup failed"
        fi
        
        # Backup Redis data if running
        if docker-compose -f "$COMPOSE_FILE" ps redis | grep -q "Up"; then
            log "Backing up Redis data..."
            docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli BGSAVE || warning "Redis backup failed"
        fi
        
        # Backup configuration files
        cp "$COMPOSE_FILE" "$backup_path/" 2>/dev/null || true
        cp "$ENV_FILE" "$backup_path/" 2>/dev/null || true
        
        # Store current image versions
        docker-compose -f "$COMPOSE_FILE" images --format json > "$backup_path/images.json" 2>/dev/null || true
        
        echo "$backup_timestamp" > "./LAST_BACKUP"
        success "Backup created: $backup_path"
    fi
}

# Build images with optimizations
build_images() {
    log "Building Docker images..."
    
    # Set build arguments
    export BUILD_TIME="$BUILD_TIME"
    export APP_VERSION="$APP_VERSION"
    
    # Build with BuildKit for better performance
    export DOCKER_BUILDKIT=1
    export COMPOSE_DOCKER_CLI_BUILD=1
    
    # Pull latest base images
    docker-compose -f "$COMPOSE_FILE" pull --ignore-pull-failures
    
    # Build application images
    if ! docker-compose -f "$COMPOSE_FILE" build --parallel --compress; then
        error "Docker build failed"
        exit 1
    fi
    
    success "Images built successfully"
}

# Health check function
health_check() {
    local service=$1
    local port=$2
    local endpoint=${3:-"/health"}
    local max_attempts=$((HEALTH_CHECK_TIMEOUT / 10))
    local attempt=1
    
    log "Health checking $service on port $port..."
    
    while [[ $attempt -le $max_attempts ]]; do
        if curl -f "http://localhost:$port$endpoint" &>/dev/null; then
            success "$service is healthy"
            return 0
        fi
        
        warning "Health check attempt $attempt/$max_attempts failed for $service"
        sleep 10
        ((attempt++))
    done
    
    error "$service health check failed after $max_attempts attempts"
    return 1
}

# Deploy with rolling update
deploy_rolling() {
    log "Starting rolling deployment..."
    
    # Update services one by one
    local services=("postgres" "redis" "api-server" "websocket-server" "nfl-dashboard" "nginx")
    
    for service in "${services[@]}"; do
        log "Updating service: $service"
        
        # Update the service
        docker-compose -f "$COMPOSE_FILE" up -d --no-deps "$service"
        
        # Wait for service to be ready
        sleep 15
        
        # Check if service is running
        if ! docker-compose -f "$COMPOSE_FILE" ps "$service" | grep -q "Up"; then
            error "Service $service failed to start"
            return 1
        fi
    done
    
    success "Rolling deployment completed"
}

# Deploy with full recreation
deploy_full() {
    log "Starting full deployment..."
    
    # Stop all services
    docker-compose -f "$COMPOSE_FILE" down
    
    # Start all services
    if ! docker-compose -f "$COMPOSE_FILE" up -d; then
        error "Full deployment failed"
        return 1
    fi
    
    success "Full deployment completed"
}

# Post-deployment verification
verify_deployment() {
    log "Verifying deployment..."
    
    # Wait for services to start
    sleep 30
    
    # Check all services are running
    local failed_services=()
    local services=($(docker-compose -f "$COMPOSE_FILE" config --services))
    
    for service in "${services[@]}"; do
        if ! docker-compose -f "$COMPOSE_FILE" ps "$service" | grep -q "Up"; then
            failed_services+=("$service")
        fi
    done
    
    if [[ ${#failed_services[@]} -gt 0 ]]; then
        error "Failed services: ${failed_services[*]}"
        return 1
    fi
    
    # Health check critical services
    local health_checks=(
        "nfl-dashboard:3000:/health"
        "api-server:8000:/health"
        "websocket-server:8080:/health"
    )
    
    for check in "${health_checks[@]}"; do
        IFS=':' read -r service port endpoint <<< "$check"
        if ! health_check "$service" "$port" "/$endpoint"; then
            return 1
        fi
    done
    
    success "Deployment verification passed"
}

# Rollback function
rollback() {
    if [[ "$ROLLBACK_ENABLED" != "true" ]]; then
        error "Rollback is disabled"
        return 1
    fi
    
    if [[ ! -f "./LAST_BACKUP" ]]; then
        error "No backup found for rollback"
        return 1
    fi
    
    local backup_timestamp=$(cat "./LAST_BACKUP")
    local backup_path="$BACKUP_DIR/deployment_$backup_timestamp"
    
    if [[ ! -d "$backup_path" ]]; then
        error "Backup directory not found: $backup_path"
        return 1
    fi
    
    warning "Rolling back to backup: $backup_timestamp"
    
    # Stop current services
    docker-compose -f "$COMPOSE_FILE" down
    
    # Restore configuration files
    if [[ -f "$backup_path/$COMPOSE_FILE" ]]; then
        cp "$backup_path/$COMPOSE_FILE" "./"
    fi
    
    if [[ -f "$backup_path/$ENV_FILE" ]]; then
        cp "$backup_path/$ENV_FILE" "./"
    fi
    
    # Restore database
    if [[ -f "$backup_path/database.sql" ]]; then
        log "Restoring database..."
        docker-compose -f "$COMPOSE_FILE" up -d postgres
        sleep 30
        docker-compose -f "$COMPOSE_FILE" exec -T postgres psql -U nfl_user -d nfl_predictions < "$backup_path/database.sql"
    fi
    
    # Start services
    docker-compose -f "$COMPOSE_FILE" up -d
    
    success "Rollback completed"
}

# Cleanup old resources
cleanup() {
    log "Cleaning up old resources..."
    
    # Remove unused Docker images
    docker image prune -f
    
    # Remove old backups (keep last 10)
    if [[ -d "$BACKUP_DIR" ]]; then
        find "$BACKUP_DIR" -type d -name "deployment_*" | sort -r | tail -n +11 | xargs rm -rf
    fi
    
    # Rotate logs
    if [[ -d "$LOG_DIR" ]]; then
        find "$LOG_DIR" -name "*.log" -type f -mtime +7 -delete
    fi
    
    success "Cleanup completed"
}

# Send notification
send_notification() {
    local status=$1
    local message=$2
    
    # Slack notification (if configured)
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"NFL Predictions Deployment - $status: $message\"}" \
            "$SLACK_WEBHOOK_URL" &>/dev/null || true
    fi
    
    # Discord notification (if configured)
    if [[ -n "${DISCORD_WEBHOOK_URL:-}" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"content\":\"NFL Predictions Deployment - $status: $message\"}" \
            "$DISCORD_WEBHOOK_URL" &>/dev/null || true
    fi
}

# Main deployment function
main() {
    log "Starting NFL Predictions Enhanced Deployment"
    log "Version: $APP_VERSION | Environment: $ENVIRONMENT | Mode: $DEPLOY_MODE"
    
    # Load environment variables
    if [[ -f "$ENV_FILE" ]]; then
        set -a
        source "$ENV_FILE"
        set +a
    fi
    
    # Trap errors for rollback
    trap 'error "Deployment failed"; send_notification "FAILED" "Deployment failed at $(date)"; exit 1' ERR
    
    # Execute deployment steps
    check_prerequisites
    setup_directories
    backup_current_deployment
    build_images
    
    # Deploy based on mode
    case "$DEPLOY_MODE" in
        "rolling")
            deploy_rolling
            ;;
        "full")
            deploy_full
            ;;
        *)
            deploy_full
            ;;
    esac
    
    # Verify deployment
    if verify_deployment; then
        success "Deployment completed successfully!"
        send_notification "SUCCESS" "Deployment completed successfully at $(date)"
        cleanup
    else
        error "Deployment verification failed"
        if [[ "$ROLLBACK_ENABLED" == "true" ]]; then
            warning "Initiating automatic rollback..."
            rollback
        fi
        exit 1
    fi
}

# Handle command line arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "rollback")
        rollback
        ;;
    "health-check")
        verify_deployment
        ;;
    "cleanup")
        cleanup
        ;;
    "backup")
        backup_current_deployment
        ;;
    *)
        echo "Usage: $0 [deploy|rollback|health-check|cleanup|backup] [version] [environment] [mode]"
        echo ""
        echo "Commands:"
        echo "  deploy      - Deploy the application (default)"
        echo "  rollback    - Rollback to previous deployment"
        echo "  health-check- Check application health"
        echo "  cleanup     - Clean up old resources"
        echo "  backup      - Create backup only"
        echo ""
        echo "Options:"
        echo "  version     - Application version (default: latest)"
        echo "  environment - Deployment environment (default: production)"
        echo "  mode        - Deployment mode: rolling|full (default: full)"
        exit 1
        ;;
esac