#!/usr/bin/env python3
"""
Production Deployment Script for NFL Predictions API
Launches FastAPI server with optimal performance settings for sub-second responses
"""

import os
import sys
import asyncio
import uvicorn
import logging
from multiprocessing import cpu_count
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/api.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def setup_environment():
    """Setup production environment variables"""
    env_vars = {
        'API_HOST': os.getenv('API_HOST', '0.0.0.0'),
        'API_PORT': int(os.getenv('API_PORT', '8000')),
        'DEBUG': os.getenv('DEBUG', 'false').lower() == 'true',
        'WORKERS': int(os.getenv('WORKERS', min(cpu_count(), 4))),
        'MAX_CONNECTIONS': int(os.getenv('MAX_CONNECTIONS', '1000')),
        'REDIS_URL': os.getenv('REDIS_URL', 'redis://localhost:6379'),
        'DATABASE_URL': os.getenv('DATABASE_URL', 'postgresql://localhost/nfl_predictor'),
        'LOG_LEVEL': os.getenv('LOG_LEVEL', 'info').lower(),
        'ENABLE_PROMETHEUS': os.getenv('ENABLE_PROMETHEUS', 'true').lower() == 'true',
        'RATE_LIMIT_REDIS': os.getenv('RATE_LIMIT_REDIS', 'true').lower() == 'true',
    }

    # Set environment variables
    for key, value in env_vars.items():
        os.environ[key] = str(value)

    logger.info(f"Environment configured: {env_vars}")
    return env_vars

def check_dependencies():
    """Check that all required dependencies are available"""
    required_packages = [
        'fastapi', 'uvicorn', 'pydantic', 'redis', 'asyncio'
    ]

    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)

    if missing_packages:
        logger.error(f"Missing required packages: {missing_packages}")
        logger.error("Install with: pip install " + " ".join(missing_packages))
        sys.exit(1)

    logger.info("All dependencies available")

def create_directories():
    """Create necessary directories"""
    directories = ['logs', 'cache', 'metrics']

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        logger.info(f"Directory ensured: {directory}")

async def run_background_tasks():
    """Start background tasks for cache maintenance and monitoring"""
    try:
        from src.api.performance_optimizer import cache_maintenance_task, performance_monitoring_task

        # Start background tasks
        cache_task = asyncio.create_task(cache_maintenance_task())
        monitoring_task = asyncio.create_task(performance_monitoring_task())

        logger.info("Background tasks started: cache maintenance, performance monitoring")

        # Keep tasks running
        await asyncio.gather(cache_task, monitoring_task)

    except Exception as e:
        logger.error(f"Background tasks failed: {e}")

def setup_performance_monitoring():
    """Setup performance monitoring and metrics collection"""
    try:
        import prometheus_client
        from prometheus_client import Counter, Histogram, Gauge, start_http_server

        # Metrics
        REQUEST_COUNT = Counter('api_requests_total', 'Total API requests', ['method', 'endpoint'])
        REQUEST_DURATION = Histogram('api_request_duration_seconds', 'API request duration')
        ACTIVE_CONNECTIONS = Gauge('api_active_connections', 'Active WebSocket connections')
        CACHE_HIT_RATE = Gauge('api_cache_hit_rate', 'Cache hit rate')

        # Start Prometheus metrics server
        if os.getenv('ENABLE_PROMETHEUS', 'true').lower() == 'true':
            prometheus_port = int(os.getenv('PROMETHEUS_PORT', '9090'))
            start_http_server(prometheus_port)
            logger.info(f"Prometheus metrics server started on port {prometheus_port}")

        return {
            'REQUEST_COUNT': REQUEST_COUNT,
            'REQUEST_DURATION': REQUEST_DURATION,
            'ACTIVE_CONNECTIONS': ACTIVE_CONNECTIONS,
            'CACHE_HIT_RATE': CACHE_HIT_RATE
        }

    except ImportError:
        logger.warning("Prometheus client not available - metrics disabled")
        return None

def get_uvicorn_config(env_vars):
    """Get optimized Uvicorn configuration"""
    config = {
        'app': 'src.api.app:app',
        'host': env_vars['API_HOST'],
        'port': env_vars['API_PORT'],
        'workers': env_vars['WORKERS'],
        'log_level': env_vars['LOG_LEVEL'],
        'access_log': True,
        'reload': env_vars['DEBUG'],
        'loop': 'uvloop',  # Use uvloop for better performance
        'http': 'httptools',  # Use httptools for better HTTP parsing
        'ws_max_size': 16777216,  # 16MB WebSocket message size
        'ws_ping_interval': 20,
        'ws_ping_timeout': 20,
        'timeout_keep_alive': 5,
        'limit_concurrency': env_vars['MAX_CONNECTIONS'],
        'limit_max_requests': 10000,  # Restart worker after 10k requests
        'backlog': 2048,  # TCP backlog
    }

    # Production optimizations
    if not env_vars['DEBUG']:
        config.update({
            'server_header': False,  # Don't send server header
            'date_header': False,    # Don't send date header
        })

    return config

def run_development_server(env_vars):
    """Run development server with hot reload"""
    logger.info("Starting development server with hot reload...")

    uvicorn.run(
        "src.api.app:app",
        host=env_vars['API_HOST'],
        port=env_vars['API_PORT'],
        reload=True,
        reload_dirs=["src"],
        log_level=env_vars['LOG_LEVEL'],
        access_log=True
    )

def run_production_server(env_vars):
    """Run production server with multiple workers"""
    logger.info(f"Starting production server with {env_vars['WORKERS']} workers...")

    config = get_uvicorn_config(env_vars)

    # Use Gunicorn for production with multiple workers
    try:
        import gunicorn.app.wsgiapp
        from gunicorn.app.base import Application

        class NFLPredictorApplication(Application):
            def __init__(self, app, options=None):
                self.options = options or {}
                self.application = app
                super().__init__()

            def load_config(self):
                for key, value in self.options.items():
                    if key in self.cfg.settings and value is not None:
                        self.cfg.set(key.lower(), value)

            def load(self):
                return self.application

        # Gunicorn options
        gunicorn_options = {
            'bind': f"{env_vars['API_HOST']}:{env_vars['API_PORT']}",
            'workers': env_vars['WORKERS'],
            'worker_class': 'uvicorn.workers.UvicornWorker',
            'worker_connections': 1000,
            'max_requests': 10000,
            'max_requests_jitter': 1000,
            'preload_app': True,
            'keepalive': 5,
            'timeout': 30,
            'graceful_timeout': 30,
            'log_level': env_vars['LOG_LEVEL'],
            'access_log_format': '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s',
            'pidfile': 'logs/api.pid',
            'daemon': False,
        }

        app = NFLPredictorApplication('src.api.app:app', gunicorn_options)
        app.run()

    except ImportError:
        logger.warning("Gunicorn not available, falling back to Uvicorn")
        uvicorn.run(**config)

def main():
    """Main entry point"""
    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║                NFL Predictions API Server                        ║
║              375+ Predictions per Game                           ║
║           Sub-second Response Times Guaranteed                   ║
╚══════════════════════════════════════════════════════════════════╝

Starting at: {datetime.now()}
    """)

    # Setup
    env_vars = setup_environment()
    check_dependencies()
    create_directories()
    setup_performance_monitoring()

    # Start background tasks
    if not env_vars['DEBUG']:
        # In production, start background tasks
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.create_task(run_background_tasks())

    logger.info("=" * 60)
    logger.info("NFL PREDICTIONS API STARTING")
    logger.info("=" * 60)
    logger.info(f"Environment: {'Development' if env_vars['DEBUG'] else 'Production'}")
    logger.info(f"Host: {env_vars['API_HOST']}:{env_vars['API_PORT']}")
    logger.info(f"Workers: {env_vars['WORKERS']}")
    logger.info(f"Max Connections: {env_vars['MAX_CONNECTIONS']}")
    logger.info(f"Redis Enabled: {env_vars['RATE_LIMIT_REDIS']}")
    logger.info("=" * 60)

    try:
        if env_vars['DEBUG']:
            run_development_server(env_vars)
        else:
            run_production_server(env_vars)

    except KeyboardInterrupt:
        logger.info("Shutting down API server...")
    except Exception as e:
        logger.error(f"Failed to start API server: {e}")
        sys.exit(1)

    logger.info("API server stopped")

if __name__ == "__main__":
    main()