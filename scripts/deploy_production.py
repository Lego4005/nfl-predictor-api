#!/usr/bin/env python3
"""
Production deployment script for NFL Predictor API.
Sets up environment variables, validates configuration, and prepares for deployment.
"""

import os
import sys
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
import subprocess
import argparse


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProductionDeployment:
    """Handles production deployment setup and validation"""
    
    def __init__(self, environment: str = "production"):
        self.environment = environment
        self.required_env_vars = [
            "ODDS_API_KEY",
            "SPORTSDATA_IO_KEY",
            "REDIS_URL",
            "CORS_ORIGINS",
            "API_BASE_URL"
        ]
        self.optional_env_vars = [
            "RAPID_API_KEY",
            "REDIS_PASSWORD",
            "API_SECRET_KEY",
            "DATABASE_URL"
        ]
    
    def check_python_version(self) -> bool:
        """Check if Python version is compatible"""
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 8):
            logger.error(f"Python 3.8+ required, found {version.major}.{version.minor}")
            return False
        
        logger.info(f"Python version check passed: {version.major}.{version.minor}.{version.micro}")
        return True
    
    def check_dependencies(self) -> bool:
        """Check if required Python packages are installed"""
        required_packages = [
            "fastapi",
            "uvicorn",
            "redis",
            "aiohttp",
            "pandas",
            "numpy",
            "fpdf"
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package)
                logger.info(f"✓ {package} is installed")
            except ImportError:
                missing_packages.append(package)
                logger.error(f"✗ {package} is missing")
        
        if missing_packages:
            logger.error(f"Missing packages: {', '.join(missing_packages)}")
            logger.info("Run: pip install -r requirements.txt")
            return False
        
        return True
    
    def validate_environment_variables(self) -> Dict[str, List[str]]:
        """Validate environment variables"""
        issues = {
            "missing_required": [],
            "missing_optional": [],
            "invalid_values": [],
            "warnings": []
        }
        
        # Check required variables
        for var in self.required_env_vars:
            value = os.getenv(var)
            if not value:
                issues["missing_required"].append(var)
            else:
                logger.info(f"✓ {var} is set")
                
                # Validate specific formats
                if var == "REDIS_URL" and not value.startswith(("redis://", "rediss://")):
                    issues["invalid_values"].append(f"{var} must start with redis:// or rediss://")
                
                if var == "API_BASE_URL" and self.environment == "production":
                    if not value.startswith("https://"):
                        issues["warnings"].append(f"{var} should use HTTPS in production")
                
                if var == "CORS_ORIGINS" and value == "*" and self.environment == "production":
                    issues["warnings"].append("CORS_ORIGINS should not be '*' in production")
        
        # Check optional variables
        for var in self.optional_env_vars:
            value = os.getenv(var)
            if not value:
                issues["missing_optional"].append(var)
            else:
                logger.info(f"✓ {var} is set")
        
        return issues
    
    def test_redis_connection(self) -> bool:
        """Test Redis connection"""
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            logger.warning("REDIS_URL not set, skipping Redis test")
            return False
        
        try:
            import redis
            
            # Parse Redis URL
            r = redis.from_url(redis_url, decode_responses=True)
            
            # Test connection
            r.ping()
            logger.info("✓ Redis connection successful")
            
            # Test basic operations
            test_key = "nfl_predictor:deployment_test"
            r.set(test_key, "test_value", ex=60)
            value = r.get(test_key)
            r.delete(test_key)
            
            if value == "test_value":
                logger.info("✓ Redis read/write operations successful")
                return True
            else:
                logger.error("✗ Redis read/write test failed")
                return False
                
        except Exception as e:
            logger.error(f"✗ Redis connection failed: {e}")
            return False
    
    def test_api_keys(self) -> Dict[str, bool]:
        """Test API key validity (basic format check)"""
        results = {}
        
        # Test Odds API key
        odds_key = os.getenv("ODDS_API_KEY")
        if odds_key:
            # Basic format validation (Odds API keys are typically 32 chars)
            if len(odds_key) >= 20 and odds_key.isalnum():
                results["odds_api"] = True
                logger.info("✓ Odds API key format looks valid")
            else:
                results["odds_api"] = False
                logger.warning("⚠ Odds API key format may be invalid")
        else:
            results["odds_api"] = False
        
        # Test SportsDataIO key
        sportsdata_key = os.getenv("SPORTSDATA_IO_KEY")
        if sportsdata_key:
            # Basic format validation (SportsDataIO keys are typically UUIDs)
            if len(sportsdata_key) >= 30:
                results["sportsdata_io"] = True
                logger.info("✓ SportsDataIO API key format looks valid")
            else:
                results["sportsdata_io"] = False
                logger.warning("⚠ SportsDataIO API key format may be invalid")
        else:
            results["sportsdata_io"] = False
        
        # Test RapidAPI key (optional)
        rapid_key = os.getenv("RAPID_API_KEY")
        if rapid_key:
            if len(rapid_key) >= 40:
                results["rapid_api"] = True
                logger.info("✓ RapidAPI key format looks valid")
            else:
                results["rapid_api"] = False
                logger.warning("⚠ RapidAPI key format may be invalid")
        else:
            results["rapid_api"] = None  # Optional
        
        return results
    
    def create_systemd_service(self, service_name: str = "nfl-predictor") -> bool:
        """Create systemd service file for production deployment"""
        service_content = f"""[Unit]
Description=NFL Predictor API
After=network.target redis.service
Wants=redis.service

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory={os.getcwd()}
Environment=PATH={os.getcwd()}/venv/bin
EnvironmentFile={os.getcwd()}/.env
ExecStart={os.getcwd()}/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
ProtectSystem=strict
ProtectHome=yes
ReadWritePaths={os.getcwd()}

[Install]
WantedBy=multi-user.target
"""
        
        service_file = f"/tmp/{service_name}.service"
        
        try:
            with open(service_file, 'w') as f:
                f.write(service_content)
            
            logger.info(f"✓ Systemd service file created: {service_file}")
            logger.info(f"To install: sudo cp {service_file} /etc/systemd/system/")
            logger.info(f"Then run: sudo systemctl enable {service_name} && sudo systemctl start {service_name}")
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to create systemd service: {e}")
            return False
    
    def create_nginx_config(self, domain: str, service_name: str = "nfl-predictor") -> bool:
        """Create nginx configuration for reverse proxy"""
        nginx_content = f"""server {{
    listen 80;
    server_name {domain};
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}}

server {{
    listen 443 ssl http2;
    server_name {domain};
    
    # SSL configuration (update paths as needed)
    ssl_certificate /etc/letsencrypt/live/{domain}/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/{domain}/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req zone=api burst=20 nodelay;
    
    # Proxy to FastAPI
    location / {{
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # CORS headers (if needed)
        add_header Access-Control-Allow-Origin "{os.getenv('CORS_ORIGINS', '*')}";
        add_header Access-Control-Allow-Methods "GET, POST, OPTIONS";
        add_header Access-Control-Allow-Headers "Content-Type, Authorization";
    }}
    
    # Health check endpoint (no rate limiting)
    location /v1/health {{
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}
"""
        
        config_file = f"/tmp/{service_name}-nginx.conf"
        
        try:
            with open(config_file, 'w') as f:
                f.write(nginx_content)
            
            logger.info(f"✓ Nginx configuration created: {config_file}")
            logger.info(f"To install: sudo cp {config_file} /etc/nginx/sites-available/{service_name}")
            logger.info(f"Then run: sudo ln -s /etc/nginx/sites-available/{service_name} /etc/nginx/sites-enabled/")
            logger.info("Don't forget to obtain SSL certificates with: sudo certbot --nginx")
            return True
            
        except Exception as e:
            logger.error(f"✗ Failed to create nginx config: {e}")
            return False
    
    def run_deployment_checks(self) -> bool:
        """Run all deployment checks"""
        logger.info("Starting production deployment checks...")
        
        all_passed = True
        
        # Python version check
        if not self.check_python_version():
            all_passed = False
        
        # Dependencies check
        if not self.check_dependencies():
            all_passed = False
        
        # Environment variables check
        env_issues = self.validate_environment_variables()
        if env_issues["missing_required"]:
            logger.error(f"Missing required environment variables: {env_issues['missing_required']}")
            all_passed = False
        
        if env_issues["invalid_values"]:
            logger.error(f"Invalid environment values: {env_issues['invalid_values']}")
            all_passed = False
        
        if env_issues["warnings"]:
            for warning in env_issues["warnings"]:
                logger.warning(f"⚠ {warning}")
        
        if env_issues["missing_optional"]:
            logger.info(f"Optional variables not set: {env_issues['missing_optional']}")
        
        # Redis connection test
        if not self.test_redis_connection():
            logger.warning("⚠ Redis connection failed - caching will be disabled")
        
        # API keys test
        api_results = self.test_api_keys()
        for service, valid in api_results.items():
            if valid is False:
                logger.error(f"✗ {service} API key validation failed")
                if service in ["odds_api", "sportsdata_io"]:
                    all_passed = False
            elif valid is None:
                logger.info(f"ℹ {service} API key not configured (optional)")
        
        return all_passed
    
    def generate_deployment_report(self) -> Dict:
        """Generate comprehensive deployment report"""
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "environment": self.environment,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "checks": {}
        }
        
        # Run all checks and collect results
        report["checks"]["python_version"] = self.check_python_version()
        report["checks"]["dependencies"] = self.check_dependencies()
        report["checks"]["environment_variables"] = self.validate_environment_variables()
        report["checks"]["redis_connection"] = self.test_redis_connection()
        report["checks"]["api_keys"] = self.test_api_keys()
        
        # Overall status
        critical_failures = (
            not report["checks"]["python_version"] or
            not report["checks"]["dependencies"] or
            bool(report["checks"]["environment_variables"]["missing_required"]) or
            bool(report["checks"]["environment_variables"]["invalid_values"])
        )
        
        report["deployment_ready"] = not critical_failures
        
        return report


def main():
    """Main deployment script"""
    parser = argparse.ArgumentParser(description="NFL Predictor Production Deployment")
    parser.add_argument("--environment", default="production", choices=["staging", "production"])
    parser.add_argument("--domain", help="Domain name for nginx configuration")
    parser.add_argument("--service-name", default="nfl-predictor", help="Systemd service name")
    parser.add_argument("--create-configs", action="store_true", help="Create systemd and nginx configs")
    parser.add_argument("--report-only", action="store_true", help="Generate report without running checks")
    
    args = parser.parse_args()
    
    deployment = ProductionDeployment(args.environment)
    
    if args.report_only:
        # Generate and save report
        report = deployment.generate_deployment_report()
        report_file = f"deployment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Deployment report saved to: {report_file}")
        print(json.dumps(report, indent=2))
        return
    
    # Run deployment checks
    success = deployment.run_deployment_checks()
    
    if success:
        logger.info("✅ All deployment checks passed!")
        
        if args.create_configs:
            # Create systemd service
            deployment.create_systemd_service(args.service_name)
            
            # Create nginx config if domain provided
            if args.domain:
                deployment.create_nginx_config(args.domain, args.service_name)
            else:
                logger.info("Use --domain to generate nginx configuration")
        
        logger.info("🚀 Ready for production deployment!")
        
    else:
        logger.error("❌ Deployment checks failed. Please fix the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    main()