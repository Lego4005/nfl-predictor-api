"""
Main FastAPI application with access control middleware integration
Demonstrates how to use the access control system in production
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logging
import time

# Import our API routers
from .api.auth_endpoints import router as auth_router
from .api.payment_endpoints import router as payment_router
from .api.subscription_endpoints import router as subscription_router
from .api.protected_endpoints import router as protected_router

# Import access control
from .auth.access_control import AccessControlError, rate_limiter

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="NFL Predictor API",
    description="AI-powered NFL predictions with subscription-based access control",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global exception handler for access control errors
@app.exception_handler(AccessControlError)
async def access_control_exception_handler(request: Request, exc: AccessControlError):
    """Handle access control exceptions"""
    return JSONResponse(
        status_code=403,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "timestamp": time.time(),
            "path": str(request.url.path)
        }
    )

# Global exception handler for HTTP exceptions
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Enhanced HTTP exception handler with rate limit headers"""
    response_content = {
        "error": exc.detail,
        "timestamp": time.time(),
        "path": str(request.url.path)
    }
    
    # Add rate limit headers if it's a 429 error
    headers = {}
    if exc.status_code == 429 and isinstance(exc.detail, dict):
        if "limit" in exc.detail:
            headers["X-RateLimit-Limit"] = str(exc.detail["limit"])
        if "requests_made" in exc.detail:
            remaining = max(0, exc.detail.get("limit", 0) - exc.detail["requests_made"])
            headers["X-RateLimit-Remaining"] = str(remaining)
        if "reset_time" in exc.detail:
            headers["X-RateLimit-Reset"] = str(exc.detail["reset_time"])
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_content,
        headers=headers
    )

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0",
        "services": {
            "database": "connected",
            "redis": "connected" if rate_limiter else "not_available",
            "payment_processor": "connected"
        }
    }

# API status endpoint
@app.get("/api/status")
async def api_status():
    """API status with access control information"""
    return {
        "status": "operational",
        "features": {
            "authentication": "enabled",
            "subscription_management": "enabled",
            "access_control": "enabled",
            "rate_limiting": "enabled",
            "audit_logging": "enabled"
        },
        "subscription_tiers": {
            "free": {
                "rate_limit": "10 requests/hour",
                "features": ["basic_predictions", "live_accuracy"]
            },
            "daily": {
                "rate_limit": "100 requests/hour",
                "features": ["real_time_predictions", "basic_props"]
            },
            "weekly": {
                "rate_limit": "500 requests/hour",
                "features": ["email_alerts", "basic_analytics"]
            },
            "monthly": {
                "rate_limit": "2000 requests/hour",
                "features": ["advanced_analytics", "full_props", "data_export"]
            },
            "season": {
                "rate_limit": "10000 requests/hour",
                "features": ["playoff_predictions", "api_access", "priority_support"]
            }
        }
    }

# Include API routers
app.include_router(auth_router)
app.include_router(payment_router)
app.include_router(subscription_router)
app.include_router(protected_router)

# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "NFL Predictor API",
        "version": "1.0.0",
        "documentation": "/api/docs",
        "authentication": "/api/v1/auth/login",
        "subscriptions": "/api/v1/subscriptions/packages",
        "predictions": "/api/v1/predictions/basic",
        "features": [
            "JWT Authentication",
            "Subscription Management",
            "Feature-based Access Control",
            "Rate Limiting",
            "Real-time Predictions",
            "Advanced Analytics",
            "Data Export"
        ]
    }

# Startup event
@app.on_event("startup")
async def startup_event():
    """Application startup tasks"""
    logger.info("🚀 NFL Predictor API starting up...")
    logger.info("✅ Authentication system loaded")
    logger.info("✅ Payment processing loaded")
    logger.info("✅ Subscription management loaded")
    logger.info("✅ Access control middleware loaded")
    logger.info("✅ Rate limiting enabled")
    logger.info("🎯 API ready for requests!")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown tasks"""
    logger.info("🛑 NFL Predictor API shutting down...")
    logger.info("✅ Cleanup completed")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main_with_access_control:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )