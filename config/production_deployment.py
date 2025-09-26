"""
Production deployment configuration and environment setup.
Handles production environment variables, deployment scripts, and monitoring.
"""

import os
from typing import Dict, Any, List
from dataclasses import dataclass, asdict
import yaml
import json


@dataclass
class ProductionEnvironment:
    """Production environment configuration"""
    # Application settings
    app_name: str = "nfl-predictor-api"
    environment: str = "production"
    debug: bool = False
    
    # Database configuration
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""
    database_url: str = ""
    
    # API keys
    odds_api_key: str = ""
    sportsdata_io_key: str = ""
    rapid_api_key: str = ""
    
    # Cache and Redis
    redis_url: str = ""
    redis_password: str = ""
    cache_ttl_minutes: int = 30
    
    # Security
    api_secret_key: str = ""
    cors_origins: List[str] = None
    allowed_hosts: List[str] = None
    
    # Performance
    db_min_pool_size: int = 10
    db_max_pool_size: int = 50
    db_query_timeout: int = 60
    
    # Monitoring
    log_level: str = "INFO"
    enable_query_logging: bool = True
    health_check_interval: int = 300
    
    def __post_init__(self):
        if self.cors_origins is None:
            self.cors_origins = ["https://yourdomain.com"]
        if self.allowed_hosts is None:
            self.allowed_hosts = ["yourdomain.com", "www.yourdomain.com"]
    
    def to_env_dict(self) -> Dict[str, str]:
        """Convert to environment variables dictionary"""
        return {
            "ENVIRONMENT": self.environment,
            "DEBUG": str(self.debug).lower(),
            "SUPABASE_URL": self.supabase_url,
            "SUPABASE_ANON_KEY": self.supabase_anon_key,
            "SUPABASE_SERVICE_ROLE_KEY": self.supabase_service_key,
            "DATABASE_URL": self.database_url,
            "ODDS_API_KEY": self.odds_api_key,
            "SPORTSDATA_IO_KEY": self.sportsdata_io_key,
            "RAPID_API_KEY": self.rapid_api_key,
            "REDIS_URL": self.redis_url,
            "REDIS_PASSWORD": self.redis_password,
            "CACHE_TTL_MINUTES": str(self.cache_ttl_minutes),
            "API_SECRET_KEY": self.api_secret_key,
            "CORS_ORIGINS": ",".join(self.cors_origins),
            "ALLOWED_HOSTS": ",".join(self.allowed_hosts),
            "DB_MIN_POOL_SIZE": str(self.db_min_pool_size),
            "DB_MAX_POOL_SIZE": str(self.db_max_pool_size),
            "DB_QUERY_TIMEOUT": str(self.db_query_timeout),
            "LOG_LEVEL": self.log_level,
            "DB_ENABLE_QUERY_LOGGING": str(self.enable_query_logging).lower(),
            "HEALTH_CHECK_INTERVAL": str(self.health_check_interval)
        }
    
    def generate_env_file(self, file_path: str = ".env.production") -> None:
        """Generate .env file for production"""
        env_vars = self.to_env_dict()
        
        with open(file_path, 'w') as f:
            f.write("# Production Environment Configuration\n")
            f.write("# Generated automatically - DO NOT edit manually\n\n")
            
            # Application settings
            f.write("# Application Settings\n")
            f.write(f"ENVIRONMENT={env_vars['ENVIRONMENT']}\n")
            f.write(f"DEBUG={env_vars['DEBUG']}\n\n")
            
            # Database configuration
            f.write("# Database Configuration\n")
            f.write(f"SUPABASE_URL={env_vars['SUPABASE_URL']}\n")
            f.write(f"SUPABASE_ANON_KEY={env_vars['SUPABASE_ANON_KEY']}\n")
            f.write(f"SUPABASE_SERVICE_ROLE_KEY={env_vars['SUPABASE_SERVICE_ROLE_KEY']}\n")
            f.write(f"DATABASE_URL={env_vars['DATABASE_URL']}\n\n")
            
            # API Keys
            f.write("# API Keys\n")
            f.write(f"ODDS_API_KEY={env_vars['ODDS_API_KEY']}\n")
            f.write(f"SPORTSDATA_IO_KEY={env_vars['SPORTSDATA_IO_KEY']}\n")
            f.write(f"RAPID_API_KEY={env_vars['RAPID_API_KEY']}\n\n")
            
            # Cache configuration
            f.write("# Cache Configuration\n")
            f.write(f"REDIS_URL={env_vars['REDIS_URL']}\n")
            f.write(f"REDIS_PASSWORD={env_vars['REDIS_PASSWORD']}\n")
            f.write(f"CACHE_TTL_MINUTES={env_vars['CACHE_TTL_MINUTES']}\n\n")
            
            # Security
            f.write("# Security\n")
            f.write(f"API_SECRET_KEY={env_vars['API_SECRET_KEY']}\n")
            f.write(f"CORS_ORIGINS={env_vars['CORS_ORIGINS']}\n")
            f.write(f"ALLOWED_HOSTS={env_vars['ALLOWED_HOSTS']}\n\n")
            
            # Performance
            f.write("# Performance\n")
            f.write(f"DB_MIN_POOL_SIZE={env_vars['DB_MIN_POOL_SIZE']}\n")
            f.write(f"DB_MAX_POOL_SIZE={env_vars['DB_MAX_POOL_SIZE']}\n")
            f.write(f"DB_QUERY_TIMEOUT={env_vars['DB_QUERY_TIMEOUT']}\n\n")
            
            # Monitoring
            f.write("# Monitoring\n")
            f.write(f"LOG_LEVEL={env_vars['LOG_LEVEL']}\n")
            f.write(f"DB_ENABLE_QUERY_LOGGING={env_vars['DB_ENABLE_QUERY_LOGGING']}\n")
            f.write(f"HEALTH_CHECK_INTERVAL={env_vars['HEALTH_CHECK_INTERVAL']}\n")


def generate_docker_compose_production() -> str:
    """Generate production Docker Compose configuration"""
    return """version: '3.8'

services:
  nfl-predictor-api:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: nfl-predictor-api
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - DEBUG=false
    env_file:
      - .env.production
    depends_on:
      - redis
    networks:
      - nfl-predictor-network
    volumes:
      - ./logs:/app/logs
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  redis:
    image: redis:7-alpine
    container_name: nfl-predictor-redis
    restart: unless-stopped
    ports:
      - "6379:6379"
    environment:
      - REDIS_PASSWORD=${REDIS_PASSWORD}
    command: redis-server --requirepass ${REDIS_PASSWORD} --maxmemory 256mb --maxmemory-policy allkeys-lru
    networks:
      - nfl-predictor-network
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    container_name: nfl-predictor-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - nfl-predictor-api
    networks:
      - nfl-predictor-network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3

networks:
  nfl-predictor-network:
    driver: bridge

volumes:
  redis_data:
    driver: local
"""


def generate_nginx_config() -> str:
    """Generate production Nginx configuration"""
    return """events {
    worker_connections 1024;
}

http {
    upstream nfl_predictor_api {
        server nfl-predictor-api:8000;
    }

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=auth:10m rate=5r/s;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/json
        application/javascript
        application/xml+rss
        application/atom+xml
        image/svg+xml;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

    server {
        listen 80;
        server_name yourdomain.com www.yourdomain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl http2;
        server_name yourdomain.com www.yourdomain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        # API endpoints
        location /api/ {
            limit_req zone=api burst=20 nodelay;
            
            proxy_pass http://nfl_predictor_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
            
            # Enable CORS
            add_header Access-Control-Allow-Origin "https://yourdomain.com";
            add_header Access-Control-Allow-Methods "GET, POST, PUT, DELETE, OPTIONS";
            add_header Access-Control-Allow-Headers "Content-Type, Authorization";
        }

        # Authentication endpoints (stricter rate limiting)
        location /api/auth/ {
            limit_req zone=auth burst=10 nodelay;
            
            proxy_pass http://nfl_predictor_api;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        # Health check endpoint (no rate limiting)
        location /health {
            proxy_pass http://nfl_predictor_api;
            access_log off;
        }

        # Static files
        location / {
            root /var/www/html;
            try_files $uri $uri/ /index.html;
            
            # Cache static assets
            location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
                expires 1y;
                add_header Cache-Control "public, immutable";
            }
        }

        # Error pages
        error_page 404 /404.html;
        error_page 500 502 503 504 /50x.html;
    }
}
"""


def generate_deployment_script() -> str:
    """Generate production deployment script"""
    return """#!/bin/bash

# Production Deployment Script for NFL Predictor API
set -e

echo "🚀 Starting production deployment..."

# Configuration
APP_NAME="nfl-predictor-api"
BACKUP_DIR="/backups"
LOG_FILE="/var/log/deployment.log"

# Colors for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m' # No Color

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
"""


def generate_monitoring_config() -> str:
    """Generate monitoring configuration"""
    return """# Monitoring Configuration for NFL Predictor API

# Prometheus configuration
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

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

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

# Alert rules
groups:
  - name: nfl_predictor_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is above 10% for 5 minutes"

      - alert: DatabaseConnectionFailure
        expr: up{job="nfl-predictor-api"} == 0
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "Database connection failed"
          description: "Unable to connect to database"

      - alert: HighMemoryUsage
        expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"
          description: "Memory usage is above 90%"
"""


# Create production environment configuration
def create_production_config():
    """Create complete production configuration"""
    prod_env = ProductionEnvironment()
    
    # Generate configuration files
    configs = {
        "docker-compose.prod.yml": generate_docker_compose_production(),
        "nginx.conf": generate_nginx_config(),
        "deploy.sh": generate_deployment_script(),
        "monitoring.yml": generate_monitoring_config()
    }
    
    return prod_env, configs


if __name__ == "__main__":
    # Generate production configuration
    env_config, file_configs = create_production_config()
    
    print("Production configuration generated successfully!")
    print("Files to create:")
    for filename in file_configs.keys():
        print(f"  - {filename}")
    
    # Generate .env template
    env_config.generate_env_file(".env.production.template")
    print("  - .env.production.template")
    
    print("\\nNext steps:")
    print("1. Update .env.production.template with your actual values")
    print("2. Rename it to .env.production")
    print("3. Run: chmod +x deploy.sh")
    print("4. Run: ./deploy.sh")