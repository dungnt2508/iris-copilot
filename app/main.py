"""
IRIS Backend v2 - Main Application
Clean Architecture Implementation
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time
import logging
from prometheus_client import Counter, Histogram, generate_latest
from starlette.responses import Response

from app.core.config import settings
from app.core.logger import setup_logging
from app.api.v1 import api_router
from app.infrastructure.db.base import init_db, close_db
from app.infrastructure.db.session import check_database_health

# Setup logging
logger = setup_logging(
    level=settings.log_level,
    format_type=settings.log_format
)

# Prometheus metrics
REQUEST_COUNT = Counter(
    'app_requests_total', 
    'Total requests',
    ['method', 'endpoint', 'status']
)
REQUEST_DURATION = Histogram(
    'app_request_duration_seconds',
    'Request duration',
    ['method', 'endpoint']
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifecycle manager
    Handles startup and shutdown events
    """
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Environment: {settings.environment}")
    
    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
    
    # Initialize Redis cache
    # await init_redis()
    
    # Initialize background tasks
    # start_background_tasks()
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
    # Close database connections
    try:
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Database shutdown failed: {e}")
    
    # Close Redis connections
    # await close_redis()
    
    # Cancel background tasks
    # await cancel_background_tasks()
    
    logger.info("Application shutdown complete")


# Security scheme for Azure AD tokens
security = HTTPBearer(description="Azure AD access token")

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="IRIS Digital Assistant - Clean Architecture Implementation",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Trusted Host middleware (security)
if settings.is_production():
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.iris.ai", "iris.ai", "infra-inno.pnj.com.vn"]
    )


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add request processing time to response headers"""
    start_time = time.time()
    
    # Track metrics
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Update Prometheus metrics
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(process_time)
    
    return response


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    """Add unique request ID for tracing"""
    import uuid
    request_id = str(uuid.uuid4())
    
    # Add to request state
    request.state.request_id = request_id
    
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    
    return response


# Exception handlers
@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": f"The requested resource was not found",
            "path": str(request.url.path)
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request: Request, exc):
    """Custom 500 handler"""
    logger.error(f"Internal server error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "request_id": getattr(request.state, "request_id", None)
        }
    )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - API information"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "documentation": "/docs" if settings.debug else None,
        "health": "/health",
        "metrics": "/metrics" if settings.enable_metrics else None
    }


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint
    Returns service health status
    """
    health_status = {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "timestamp": time.time()
    }
    
    # Check database
    try:
        db_healthy = await check_database_health()
        health_status["database"] = "healthy" if db_healthy else "unhealthy"
        if not db_healthy:
            health_status["status"] = "degraded"
            logger.error("Database health check failed")
    except Exception as e:
        health_status["database"] = "unhealthy"
        health_status["status"] = "degraded"
        logger.error(f"Database health check failed: {e}")
    
    # Check Redis
    # try:
    #     await check_redis_health()
    #     health_status["cache"] = "healthy"
    # except Exception as e:
    #     health_status["cache"] = "unhealthy"
    #     health_status["status"] = "degraded"
    #     logger.error(f"Redis health check failed: {e}")
    
    return health_status


# Metrics endpoint
if settings.enable_metrics:
    @app.get("/metrics", tags=["Monitoring"])
    async def metrics():
        """Prometheus metrics endpoint"""
        return Response(
            content=generate_latest(),
            media_type="text/plain"
        )


# Include API routers
app.include_router(
    api_router,
    prefix=settings.api_v1_prefix
)


# Development only endpoints
if settings.debug:
    @app.get("/debug/config", tags=["Debug"])
    async def debug_config():
        """Show current configuration (development only)"""
        from app.api.v1.dependencies import get_repository_info
        repo_info = await get_repository_info()
        
        return {
            "environment": settings.environment,
            "debug": settings.debug,
            "database_url": settings.database_url.split("@")[1] if "@" in settings.database_url else "hidden",
            "redis_url": settings.redis_url.split("@")[1] if "@" in settings.redis_url else "hidden",
            "cors_origins": settings.cors_origins,
            "repository_mode": repo_info["mode"],
            "features": {
                "registration": settings.enable_registration,
                "email_verification": settings.require_email_verification,
                "social_login": settings.enable_social_login,
                "rate_limiting": settings.rate_limit_enabled
            }
        }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )