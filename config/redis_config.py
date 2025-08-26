"""
Redis configuration and deployment setup for NFL Predictor.
Handles Redis instance configuration, monitoring, and alerting.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import subprocess
import time

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

logger = logging.getLogger(__name__)


class RedisDeploymentType(Enum):
    """Redis deployment types"""
    LOCAL = "local"
    DOCKER = "docker"
    CLOUD = "cloud"
    MANAGED = "managed"


@dataclass
class RedisConfig:
    """Redis configuration settings"""
    host: str
    port: int
    password: Optional[str]
    db: int
    max_connections: int
    socket_timeout: int
    socket_connect_timeout: int
    retry_on_timeout: bool
    health_check_interval: int
    max_memory: str
    max_memory_policy: str
    
    def get_connection_url(self) -> str:
        """Get Redis connection URL"""
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"
    
    def get_connection_params(self) -> Dict[str, Any]:
        """Get Redis connection parameters"""
        params = {
            "host": self.host,
            "port": self.port,
            "db": self.db,
            "max_connections": self.max_connections,
            "socket_timeout": self.socket_timeout,
            "socket_connect_timeout": self.socket_connect_timeout,
            "retry_on_timeout": self.retry_on_timeout,
            "health_check_interval": self.health_check_interval,
            "decode_responses": True
        }
        
        if self.password:
            params["password"] = self.password
            
        return params


class RedisDeploymentManager:
    """
    Manages Redis deployment, configuration, and monitoring.
    Supports local, Docker, and cloud deployments.
    """
    
    def __init__(self, deployment_type: RedisDeploymentType = RedisDeploymentType.LOCAL):
        self.deployment_type = deployment_type
        self.config = self._load_config()
        self._redis_client: Optional[redis.Redis] = None
    
    def _load_config(self) -> RedisConfig:
        """Load Redis configuration from environment"""
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        
        # Parse Redis URL
        if redis_url.startswith("redis://"):
            # Simple parsing for redis://[password@]host:port/db
            url_parts = redis_url.replace("redis://", "").split("/")
            db = int(url_parts[1]) if len(url_parts) > 1 else 0
            
            host_part = url_parts[0]
            if "@" in host_part:
                password, host_port = host_part.split("@", 1)
                password = password.lstrip(":")
            else:
                password = None
                host_port = host_part
            
            if ":" in host_port:
                host, port = host_port.split(":", 1)
                port = int(port)
            else:
                host = host_port
                port = 6379
        else:
            # Fallback defaults
            host = "localhost"
            port = 6379
            password = None
            db = 0
        
        return RedisConfig(
            host=host,
            port=port,
            password=password or os.getenv("REDIS_PASSWORD"),
            db=db,
            max_connections=int(os.getenv("REDIS_MAX_CONNECTIONS", "20")),
            socket_timeout=int(os.getenv("REDIS_SOCKET_TIMEOUT", "5")),
            socket_connect_timeout=int(os.getenv("REDIS_CONNECT_TIMEOUT", "5")),
            retry_on_timeout=os.getenv("REDIS_RETRY_ON_TIMEOUT", "true").lower() == "true",
            health_check_interval=int(os.getenv("REDIS_HEALTH_CHECK_INTERVAL", "30")),
            max_memory=os.getenv("REDIS_MAX_MEMORY", "256mb"),
            max_memory_policy=os.getenv("REDIS_MAX_MEMORY_POLICY", "allkeys-lru")
        )
    
    def create_docker_compose(self) -> str:
        """Create Docker Compose configuration for Redis"""
        compose_content = f"""version: '3.8'

services:
  redis:
    image: redis:7-alpine
    container_name: nfl-predictor-redis
    restart: unless-stopped
    ports:
      - "{self.config.port}:6379"
    volumes:
      - redis_data:/data
      - ./redis.conf:/usr/local/etc/redis/redis.conf
    command: redis-server /usr/local/etc/redis/redis.conf
    environment:
      - REDIS_PASSWORD={self.config.password or ''}
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s
    networks:
      - nfl-predictor-network

  redis-commander:
    image: rediscommander/redis-commander:latest
    container_name: nfl-predictor-redis-ui
    restart: unless-stopped
    ports:
      - "8081:8081"
    environment:
      - REDIS_HOSTS=local:redis:6379
      - REDIS_PASSWORD={self.config.password or ''}
    depends_on:
      - redis
    networks:
      - nfl-predictor-network

volumes:
  redis_data:
    driver: local

networks:
  nfl-predictor-network:
    driver: bridge
"""
        
        with open("docker-compose.redis.yml", "w") as f:
            f.write(compose_content)
        
        logger.info("Docker Compose configuration created: docker-compose.redis.yml")
        return "docker-compose.redis.yml"
    
    def create_redis_config_file(self) -> str:
        """Create Redis configuration file"""
        config_content = f"""# Redis configuration for NFL Predictor
# Generated on {datetime.utcnow().isoformat()}

# Network
bind 0.0.0.0
port 6379
timeout 300
tcp-keepalive 300

# General
daemonize no
supervised no
pidfile /var/run/redis_6379.pid
loglevel notice
logfile ""
databases 16

# Snapshotting
save 900 1
save 300 10
save 60 10000
stop-writes-on-bgsave-error yes
rdbcompression yes
rdbchecksum yes
dbfilename dump.rdb
dir ./

# Security
{f'requirepass {self.config.password}' if self.config.password else '# requirepass disabled'}

# Memory management
maxmemory {self.config.max_memory}
maxmemory-policy {self.config.max_memory_policy}

# Append only file
appendonly yes
appendfilename "appendonly.aof"
appendfsync everysec
no-appendfsync-on-rewrite no
auto-aof-rewrite-percentage 100
auto-aof-rewrite-min-size 64mb

# Slow log
slowlog-log-slower-than 10000
slowlog-max-len 128

# Latency monitor
latency-monitor-threshold 100

# Client output buffer limits
client-output-buffer-limit normal 0 0 0
client-output-buffer-limit replica 256mb 64mb 60
client-output-buffer-limit pubsub 32mb 8mb 60

# Advanced config
hash-max-ziplist-entries 512
hash-max-ziplist-value 64
list-max-ziplist-size -2
list-compress-depth 0
set-max-intset-entries 512
zset-max-ziplist-entries 128
zset-max-ziplist-value 64
hll-sparse-max-bytes 3000
stream-node-max-bytes 4096
stream-node-max-entries 100
activerehashing yes
hz 10
dynamic-hz yes
aof-rewrite-incremental-fsync yes
rdb-save-incremental-fsync yes
"""
        
        with open("redis.conf", "w") as f:
            f.write(config_content)
        
        logger.info("Redis configuration file created: redis.conf")
        return "redis.conf"
    
    def create_systemd_service(self) -> str:
        """Create systemd service for Redis"""
        service_content = f"""[Unit]
Description=Advanced key-value store for NFL Predictor
After=network.target
Documentation=http://redis.io/documentation, man:redis-server(1)

[Service]
Type=notify
ExecStart=/usr/bin/redis-server /etc/redis/redis.conf
ExecStop=/bin/kill -s QUIT $MAINPID
TimeoutStopSec=0
Restart=always
User=redis
Group=redis
RuntimeDirectory=redis
RuntimeDirectoryMode=0755

# Security settings
NoNewPrivileges=yes
PrivateTmp=yes
PrivateDevices=yes
ProtectHome=yes
ProtectSystem=strict
ReadWritePaths=/var/lib/redis
ReadWritePaths=/var/log/redis
ReadWritePaths=/var/run/redis

# Resource limits
LimitNOFILE=65535
MemoryMax={self.config.max_memory}

[Install]
WantedBy=multi-user.target
"""
        
        service_file = "/tmp/redis-nfl-predictor.service"
        with open(service_file, "w") as f:
            f.write(service_content)
        
        logger.info(f"Systemd service file created: {service_file}")
        logger.info("To install: sudo cp /tmp/redis-nfl-predictor.service /etc/systemd/system/")
        logger.info("Then run: sudo systemctl enable redis-nfl-predictor && sudo systemctl start redis-nfl-predictor")
        
        return service_file
    
    def test_connection(self) -> Dict[str, Any]:
        """Test Redis connection and return status"""
        if not REDIS_AVAILABLE:
            return {
                "connected": False,
                "error": "Redis Python client not installed",
                "recommendation": "pip install redis"
            }
        
        try:
            client = redis.Redis(**self.config.get_connection_params())
            
            # Test basic operations
            start_time = time.time()
            client.ping()
            ping_time = (time.time() - start_time) * 1000
            
            # Test set/get
            test_key = "nfl_predictor:connection_test"
            client.set(test_key, "test_value", ex=60)
            value = client.get(test_key)
            client.delete(test_key)
            
            # Get server info
            info = client.info()
            
            return {
                "connected": True,
                "ping_time_ms": round(ping_time, 2),
                "redis_version": info.get("redis_version"),
                "used_memory_human": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "uptime_in_seconds": info.get("uptime_in_seconds"),
                "test_operations": "passed"
            }
            
        except redis.ConnectionError as e:
            return {
                "connected": False,
                "error": f"Connection failed: {str(e)}",
                "recommendation": "Check Redis server is running and connection details"
            }
        except redis.AuthenticationError as e:
            return {
                "connected": False,
                "error": f"Authentication failed: {str(e)}",
                "recommendation": "Check Redis password configuration"
            }
        except Exception as e:
            return {
                "connected": False,
                "error": f"Unexpected error: {str(e)}",
                "recommendation": "Check Redis configuration and logs"
            }
    
    def get_redis_client(self) -> Optional[redis.Redis]:
        """Get configured Redis client"""
        if not REDIS_AVAILABLE:
            return None
        
        if not self._redis_client:
            try:
                self._redis_client = redis.Redis(**self.config.get_connection_params())
                # Test connection
                self._redis_client.ping()
            except Exception as e:
                logger.error(f"Failed to create Redis client: {e}")
                return None
        
        return self._redis_client
    
    def setup_monitoring(self) -> Dict[str, str]:
        """Set up Redis monitoring scripts"""
        
        # Health check script
        health_check_script = f"""#!/bin/bash
# Redis health check script for NFL Predictor
# Generated on {datetime.utcnow().isoformat()}

REDIS_HOST="{self.config.host}"
REDIS_PORT="{self.config.port}"
REDIS_PASSWORD="{self.config.password or ''}"

# Function to check Redis health
check_redis_health() {{
    if [ -n "$REDIS_PASSWORD" ]; then
        redis-cli -h $REDIS_HOST -p $REDIS_PORT -a $REDIS_PASSWORD ping
    else
        redis-cli -h $REDIS_HOST -p $REDIS_PORT ping
    fi
}}

# Function to get Redis info
get_redis_info() {{
    if [ -n "$REDIS_PASSWORD" ]; then
        redis-cli -h $REDIS_HOST -p $REDIS_PORT -a $REDIS_PASSWORD info
    else
        redis-cli -h $REDIS_HOST -p $REDIS_PORT info
    fi
}}

# Function to check memory usage
check_memory_usage() {{
    INFO=$(get_redis_info)
    USED_MEMORY=$(echo "$INFO" | grep "used_memory:" | cut -d: -f2 | tr -d '\\r')
    MAX_MEMORY=$(echo "$INFO" | grep "maxmemory:" | cut -d: -f2 | tr -d '\\r')
    
    echo "Used Memory: $USED_MEMORY bytes"
    echo "Max Memory: $MAX_MEMORY bytes"
    
    if [ "$MAX_MEMORY" -gt 0 ]; then
        USAGE_PERCENT=$((USED_MEMORY * 100 / MAX_MEMORY))
        echo "Memory Usage: $USAGE_PERCENT%"
        
        if [ "$USAGE_PERCENT" -gt 80 ]; then
            echo "WARNING: Memory usage is above 80%"
            return 1
        fi
    fi
    
    return 0
}}

# Main health check
echo "Redis Health Check - $(date)"
echo "=================================="

if check_redis_health > /dev/null 2>&1; then
    echo "✓ Redis is responding to ping"
    
    if check_memory_usage; then
        echo "✓ Memory usage is within limits"
        echo "Overall Status: HEALTHY"
        exit 0
    else
        echo "⚠ Memory usage is high"
        echo "Overall Status: WARNING"
        exit 1
    fi
else
    echo "✗ Redis is not responding"
    echo "Overall Status: CRITICAL"
    exit 2
fi
"""
        
        with open("scripts/redis_health_check.sh", "w") as f:
            f.write(health_check_script)
        
        # Monitoring script
        monitoring_script = f"""#!/bin/bash
# Redis monitoring script for NFL Predictor
# Collects metrics and sends alerts

REDIS_HOST="{self.config.host}"
REDIS_PORT="{self.config.port}"
REDIS_PASSWORD="{self.config.password or ''}"
LOG_FILE="/var/log/nfl-predictor/redis-monitor.log"

# Create log directory if it doesn't exist
mkdir -p $(dirname $LOG_FILE)

# Function to log with timestamp
log_message() {{
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> $LOG_FILE
}}

# Function to get Redis metrics
get_redis_metrics() {{
    if [ -n "$REDIS_PASSWORD" ]; then
        redis-cli -h $REDIS_HOST -p $REDIS_PORT -a $REDIS_PASSWORD info
    else
        redis-cli -h $REDIS_HOST -p $REDIS_PORT info
    fi
}}

# Function to check and alert on high memory usage
check_memory_alert() {{
    INFO=$(get_redis_metrics)
    USED_MEMORY=$(echo "$INFO" | grep "used_memory:" | cut -d: -f2 | tr -d '\\r')
    MAX_MEMORY=$(echo "$INFO" | grep "maxmemory:" | cut -d: -f2 | tr -d '\\r')
    
    if [ "$MAX_MEMORY" -gt 0 ]; then
        USAGE_PERCENT=$((USED_MEMORY * 100 / MAX_MEMORY))
        
        if [ "$USAGE_PERCENT" -gt 90 ]; then
            log_message "CRITICAL: Redis memory usage at $USAGE_PERCENT%"
            # Add alerting mechanism here (email, webhook, etc.)
        elif [ "$USAGE_PERCENT" -gt 80 ]; then
            log_message "WARNING: Redis memory usage at $USAGE_PERCENT%"
        fi
    fi
}}

# Function to check connection count
check_connections() {{
    INFO=$(get_redis_metrics)
    CONNECTED_CLIENTS=$(echo "$INFO" | grep "connected_clients:" | cut -d: -f2 | tr -d '\\r')
    
    if [ "$CONNECTED_CLIENTS" -gt 100 ]; then
        log_message "WARNING: High number of Redis connections: $CONNECTED_CLIENTS"
    fi
}}

# Main monitoring loop
log_message "Starting Redis monitoring"

while true; do
    if get_redis_metrics > /dev/null 2>&1; then
        check_memory_alert
        check_connections
    else
        log_message "ERROR: Cannot connect to Redis"
    fi
    
    sleep {self.config.health_check_interval}
done
"""
        
        with open("scripts/redis_monitor.sh", "w") as f:
            f.write(monitoring_script)
        
        logger.info("Monitoring scripts created:")
        logger.info("- scripts/redis_health_check.sh")
        logger.info("- scripts/redis_monitor.sh")
        
        return {
            "health_check": "scripts/redis_health_check.sh",
            "monitor": "scripts/redis_monitor.sh"
        }
    
    def deploy_redis(self) -> Dict[str, Any]:
        """Deploy Redis based on deployment type"""
        result = {
            "deployment_type": self.deployment_type.value,
            "success": False,
            "files_created": [],
            "commands_to_run": [],
            "notes": []
        }
        
        try:
            if self.deployment_type == RedisDeploymentType.DOCKER:
                # Create Docker deployment files
                compose_file = self.create_docker_compose()
                config_file = self.create_redis_config_file()
                
                result["files_created"].extend([compose_file, config_file])
                result["commands_to_run"].extend([
                    "docker-compose -f docker-compose.redis.yml up -d",
                    "docker-compose -f docker-compose.redis.yml logs -f redis"
                ])
                result["notes"].append("Redis will be available on port 6379")
                result["notes"].append("Redis Commander UI available on port 8081")
                
            elif self.deployment_type == RedisDeploymentType.LOCAL:
                # Create local deployment files
                config_file = self.create_redis_config_file()
                service_file = self.create_systemd_service()
                
                result["files_created"].extend([config_file, service_file])
                result["commands_to_run"].extend([
                    "sudo cp redis.conf /etc/redis/",
                    f"sudo cp {service_file} /etc/systemd/system/",
                    "sudo systemctl daemon-reload",
                    "sudo systemctl enable redis-nfl-predictor",
                    "sudo systemctl start redis-nfl-predictor"
                ])
                result["notes"].append("Ensure Redis is installed: sudo apt-get install redis-server")
                
            # Create monitoring scripts for all deployment types
            monitoring_files = self.setup_monitoring()
            result["files_created"].extend(monitoring_files.values())
            
            # Make scripts executable (on Unix systems)
            try:
                import stat
                for script_file in monitoring_files.values():
                    os.chmod(script_file, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
            except:
                result["notes"].append("Make scripts executable: chmod +x scripts/*.sh")
            
            result["success"] = True
            
        except Exception as e:
            result["error"] = str(e)
            logger.error(f"Redis deployment failed: {e}")
        
        return result
    
    def validate_deployment(self) -> Dict[str, Any]:
        """Validate Redis deployment"""
        validation_result = {
            "timestamp": datetime.utcnow().isoformat(),
            "overall_status": "unknown",
            "checks": {}
        }
        
        # Test connection
        connection_test = self.test_connection()
        validation_result["checks"]["connection"] = connection_test
        
        if connection_test["connected"]:
            client = self.get_redis_client()
            if client:
                try:
                    # Test cache operations
                    test_key = "nfl_predictor:deployment_validation"
                    test_data = {"test": True, "timestamp": datetime.utcnow().isoformat()}
                    
                    # Test JSON serialization
                    client.set(test_key, json.dumps(test_data), ex=300)
                    retrieved = client.get(test_key)
                    parsed_data = json.loads(retrieved) if retrieved else None
                    
                    validation_result["checks"]["cache_operations"] = {
                        "set_operation": True,
                        "get_operation": retrieved is not None,
                        "json_serialization": parsed_data == test_data,
                        "ttl_support": client.ttl(test_key) > 0
                    }
                    
                    # Clean up test key
                    client.delete(test_key)
                    
                    # Check memory configuration
                    info = client.info()
                    validation_result["checks"]["configuration"] = {
                        "max_memory_configured": info.get("maxmemory", 0) > 0,
                        "max_memory_policy": info.get("maxmemory_policy", "unknown"),
                        "persistence_enabled": info.get("aof_enabled", 0) == 1 or info.get("rdb_last_save_time", 0) > 0
                    }
                    
                except Exception as e:
                    validation_result["checks"]["cache_operations"] = {
                        "error": str(e)
                    }
        
        # Determine overall status
        if connection_test["connected"]:
            cache_ops = validation_result["checks"].get("cache_operations", {})
            if isinstance(cache_ops, dict) and cache_ops.get("set_operation") and cache_ops.get("get_operation"):
                validation_result["overall_status"] = "healthy"
            else:
                validation_result["overall_status"] = "degraded"
        else:
            validation_result["overall_status"] = "failed"
        
        return validation_result


def get_redis_manager(deployment_type: str = "local") -> RedisDeploymentManager:
    """Get Redis deployment manager instance"""
    deployment_enum = RedisDeploymentType(deployment_type.lower())
    return RedisDeploymentManager(deployment_enum)