"""
FastAPI Gateway - Main Application
NFL AI Expert Prediction Platform
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import time
import uuid
import asyncio

# Configuration
from src.api.config import settings

# Services
from src.api.services.database import db_service
from src.api.services.cache import cache_service

# Routers
from src.api.routers import experts, council, bets, games

# WebSocket
from src.api.websocket.manager import connection_manager
from src.api.websocket.handlers import handle_client_message

# Setup logging
logging.basicConfig(
    level=settings.log_level,
    format=settings.log_format
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown"""
    # Startup
    logger.info("Starting NFL Predictor API Gateway...")

    try:
        # Initialize database connection
        await db_service.initialize()
        logger.info("Database service initialized")

        # Initialize cache
        await cache_service.initialize()
        logger.info("Cache service initialized")

        # Start WebSocket heartbeat loop
        asyncio.create_task(connection_manager.heartbeat_loop())
        logger.info("WebSocket heartbeat started")

        logger.info(f"API Gateway running on {settings.host}:{settings.port}")

    except Exception as e:
        logger.error(f"Startup failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down API Gateway...")

    try:
        await cache_service.close()
        logger.info("Cache service closed")
    except Exception as e:
        logger.error(f"Shutdown error: {e}")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.version,
    description="REST API + WebSocket gateway for NFL AI Expert predictions",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)


# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests with timing"""
    start_time = time.time()
    request_id = str(uuid.uuid4())

    # Add request ID to state
    request.state.request_id = request_id

    logger.info(f"[{request_id}] {request.method} {request.url.path} - Started")

    response = await call_next(request)

    duration = time.time() - start_time
    logger.info(
        f"[{request_id}] {request.method} {request.url.path} - "
        f"Completed in {duration:.3f}s with status {response.status_code}"
    )

    # Add request ID to response headers
    response.headers["X-Request-ID"] = request_id

    return response


# Exception Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler"""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(f"[{request_id}] Unhandled exception: {exc}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "request_id": request_id
        }
    )


# Include routers
app.include_router(experts.router)
app.include_router(council.router)
app.include_router(bets.router)
app.include_router(games.router)


# Root endpoint
@app.get("/")
async def root():
    """API Gateway root endpoint"""
    return {
        "service": settings.app_name,
        "version": settings.version,
        "status": "operational",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "experts": "/api/v1/experts",
            "council": "/api/v1/council",
            "bets": "/api/v1/bets",
            "games": "/api/v1/games",
            "websocket": "/ws/updates"
        }
    }


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "database": "connected" if db_service.client else "disconnected",
        "cache": "connected" if cache_service.client else "disconnected",
        "websocket_connections": len(connection_manager.active_connections)
    }


# WebSocket endpoint
@app.websocket("/ws/updates")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time updates.

    Supports:
    - Bet placed events
    - Line movement events
    - Expert elimination events
    - Bankroll update events

    Client can subscribe to specific channels and filter by expert/game IDs.
    """
    client_id = str(uuid.uuid4())

    try:
        await connection_manager.connect(client_id, websocket)

        logger.info(f"WebSocket client {client_id} connected")

        # Main message loop
        while True:
            try:
                # Receive message from client
                data = await websocket.receive_json()

                # Handle message
                await handle_client_message(client_id, data)

            except WebSocketDisconnect:
                logger.info(f"WebSocket client {client_id} disconnected normally")
                break
            except Exception as e:
                logger.error(f"WebSocket error for client {client_id}: {e}")
                await connection_manager.send_personal_message(client_id, {
                    "type": "error",
                    "message": "Failed to process message"
                })

    except Exception as e:
        logger.error(f"WebSocket connection error for {client_id}: {e}")

    finally:
        connection_manager.disconnect(client_id)


# Run with: uvicorn src.api.main:app --reload --port 8000
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )