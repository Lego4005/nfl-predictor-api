#!/usr/bin/env python3
"""
Quick-start script for the Real-time NFL Data Pipeline

This script provides an easy way to start the complete real-time data pipeline
with all components properly initialized and configured.
"""

import asyncio
import logging
import sys
import os
from pathlib import Path

# Add src directory to Python path
current_dir = Path(__file__).parent
src_dir = current_dir.parent / "src"
sys.path.insert(0, str(src_dir))

from integration.pipeline_integration import pipeline_integration, create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('pipeline.log')
    ]
)

logger = logging.getLogger(__name__)


async def start_pipeline_standalone():
    """Start the pipeline components without FastAPI server"""
    try:
        logger.info("Starting Real-time NFL Data Pipeline (standalone mode)")

        # Initialize all components
        await pipeline_integration.initialize_all_components()

        logger.info("Pipeline started successfully! Press Ctrl+C to stop.")
        logger.info("WebSocket endpoint: ws://localhost:8000/api/v1/realtime/ws")
        logger.info("Health check: http://localhost:8000/health")

        # Keep running until interrupted
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("Received interrupt signal, shutting down...")

    except Exception as e:
        logger.error(f"Failed to start pipeline: {e}")
        raise
    finally:
        # Graceful shutdown
        await pipeline_integration.shutdown_all_components()
        logger.info("Pipeline shutdown complete")


async def start_pipeline_with_api():
    """Start the pipeline with full FastAPI server"""
    try:
        import uvicorn

        logger.info("Starting Real-time NFL Data Pipeline with API server")

        # Create FastAPI app
        app = create_app()

        # Configure and start server
        config = uvicorn.Config(
            app=app,
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=False,
            access_log=True
        )

        server = uvicorn.Server(config)

        logger.info("Server starting on http://0.0.0.0:8000")
        logger.info("API documentation: http://localhost:8000/docs")
        logger.info("WebSocket endpoint: ws://localhost:8000/api/v1/realtime/ws")
        logger.info("Health check: http://localhost:8000/health")
        logger.info("Metrics: http://localhost:8000/metrics")

        await server.serve()

    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise


def check_dependencies():
    """Check if required dependencies are available"""
    missing_deps = []

    try:
        import redis
    except ImportError:
        missing_deps.append("redis")

    try:
        import aioredis
    except ImportError:
        missing_deps.append("aioredis")

    try:
        import fastapi
    except ImportError:
        missing_deps.append("fastapi")

    try:
        import uvicorn
    except ImportError:
        missing_deps.append("uvicorn")

    if missing_deps:
        logger.error(f"Missing required dependencies: {', '.join(missing_deps)}")
        logger.error("Please install with: pip install -r requirements.txt")
        return False

    return True


def main():
    """Main entry point"""
    if not check_dependencies():
        sys.exit(1)

    # Parse command line arguments
    mode = "api"  # Default mode
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()

    if mode == "standalone":
        logger.info("Starting in standalone mode (no API server)")
        asyncio.run(start_pipeline_standalone())
    elif mode == "api":
        logger.info("Starting in API mode (with FastAPI server)")
        asyncio.run(start_pipeline_with_api())
    else:
        print("Usage: python start_pipeline.py [api|standalone]")
        print("  api        - Start with FastAPI server (default)")
        print("  standalone - Start pipeline only (no HTTP API)")
        sys.exit(1)


if __name__ == "__main__":
    main()