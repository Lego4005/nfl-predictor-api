"""
FastAPI Application for NFL Predictor Authentication
"""

import os
import logging
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

# Import our modules
from database import run_migrations
from .auth_endpoints import router as auth_router

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("🚀 Starting NFL Predictor API...")
    
    # Run database migrations
    try:
        run_migrations()
        logger.info("✅ Database migrations completed")
    except Exception as e:
        logger.error(f"❌ Database migration failed: {e}")
        # Don't fail startup for database issues in development
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down NFL Predictor API...")

# Create FastAPI app
app = FastAPI(
    title="NFL Predictor API",
    description="Authentication and subscription system for NFL predictions",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "nfl-predictor-api",
        "version": "1.0.0"
    }

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "NFL Predictor API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )

if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from environment
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    # Run the application
    uvicorn.run(
        "src.api.app:app",
        host=host,
        port=port,
        reload=debug,
        log_level="info"
    )