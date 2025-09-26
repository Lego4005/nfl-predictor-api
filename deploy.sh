#!/bin/bash

# Production Deployment Script for NFL Predictor API
set -e

echo "🚀 Starting production deployment..."

# Configuration
APP_NAME="nfl-predictor-api"
BACKUP_DIR="/backups"
LOG_FILE="/var/log/deployment.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a $LOG_FILE
}

error_exit() {
    echo -e "${RED}ERROR: $1${NC}" | tee -a $LOG_FILE
    exit 1
}

success_msg() {
    echo -e "${GREEN}SUCCESS: $1${NC}" | tee -a $LOG_FILE
}

warning_msg() {
    echo -e "${YELLOW}WARNING: $1${NC}" | tee -a $LOG_FILE
}

# Check requirements
check_requirements() {
    log "Checking deployment requirements..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        error_exit "Docker is not installed"
    fi
    
    # Check if Docker Compose is installed
    if ! command -v docker-compose &> /dev/null; then
        error_exit "Docker Compose is not installed"
    fi
    
    # Check if .env.production exists
    if [ ! -f ".env.production" ]; then
        error_exit ".env.production file not found"
    fi
    
    success_msg "All requirements satisfied"
}

# Create backup
create_backup() {
    log "Creating backup..."
    
    BACKUP_TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    BACKUP_PATH="$BACKUP_DIR/backup_$BACKUP_TIMESTAMP"
    
    mkdir -p $BACKUP_PATH
    
    # Backup database (if applicable)
    if [ -f "data/database.db" ]; then
        cp data/database.db $BACKUP_PATH/
    fi
    
    # Backup configuration
    cp .env.production $BACKUP_PATH/
    cp docker-compose.prod.yml $BACKUP_PATH/
    
    success_msg "Backup created at $BACKUP_PATH"
}

# Pull latest code
update_code() {
    log "Updating code..."
    
    # Ensure we're on the main branch
    git checkout main
    
    # Pull latest changes
    git pull origin main
    
    success_msg "Code updated successfully"
}

# Build and deploy
deploy_application() {
    log "Deploying application..."
    
    # Stop existing containers
    docker-compose -f docker-compose.prod.yml down
    
    # Remove old images
    docker image prune -f
    
    # Build new images
    docker-compose -f docker-compose.prod.yml build --no-cache
    
    # Start services
    docker-compose -f docker-compose.prod.yml up -d
    
    success_msg "Application deployed successfully"
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."
    
    # Wait for database to be ready
    sleep 10
    
    # Run migrations using Supabase CLI or direct SQL
    if command -v supabase &> /dev/null; then
        supabase db push
    else
        warning_msg "Supabase CLI not found, skipping migrations"
    fi
    
    success_msg "Database migrations completed"
}

# Health check
health_check() {
    log "Performing health check..."
    
    # Wait for services to start
    sleep 30
    
    # Check API health
    if curl -f http://localhost/health &> /dev/null; then
        success_msg "Health check passed"
    else
        error_exit "Health check failed"
    fi
}

# Update monitoring
update_monitoring() {
    log "Updating monitoring configuration..."
    
    # Restart monitoring services if they exist
    if docker ps | grep -q "prometheus"; then
        docker restart prometheus
    fi
    
    if docker ps | grep -q "grafana"; then
        docker restart grafana
    fi
    
    success_msg "Monitoring updated"
}

# Cleanup old backups (keep last 10)
cleanup_backups() {
    log "Cleaning up old backups..."
    
    if [ -d "$BACKUP_DIR" ]; then
        cd $BACKUP_DIR
        ls -t | tail -n +11 | xargs -r rm -rf
    fi
    
    success_msg "Backup cleanup completed"
}

# Main deployment process
main() {
    log "Starting deployment process..."
    
    check_requirements
    create_backup
    update_code
    deploy_application
    run_migrations
    health_check
    update_monitoring
    cleanup_backups
    
    success_msg "🎉 Deployment completed successfully!"
    
    # Display deployment summary
    echo ""
    echo "=== Deployment Summary ==="
    echo "Application: $APP_NAME"
    echo "Timestamp: $(date)"
    echo "Status: SUCCESS"
    echo "Health Check: http://localhost/health"
    echo "=========================="
}

# Execute main function
main "$@"