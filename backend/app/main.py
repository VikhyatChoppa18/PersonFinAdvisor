"""
Main FastAPI application entry point.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.exceptions import RequestValidationError, HTTPException as FastAPIHTTPException
import structlog

from app.core.config import settings
from app.api.v1.api import api_router
from app.db.database import engine
from app.db import models
from app.core.logging import configure_logging
from app.core.exceptions import (
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler
)

# Configure logging
configure_logging()

# Create database tables
models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Multi-agent AI platform for personalized financial planning",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(FastAPIHTTPException, http_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# CORS middleware - must be added before other middleware
# Ensure localhost:3001 is always allowed
cors_origins = settings.BACKEND_CORS_ORIGINS.copy() if isinstance(settings.BACKEND_CORS_ORIGINS, list) else list(settings.BACKEND_CORS_ORIGINS)
if "http://localhost:3001" not in cors_origins:
    cors_origins.append("http://localhost:3001")
if "http://localhost:3000" not in cors_origins:
    cors_origins.append("http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# Gzip compression
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

logger = structlog.get_logger()


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "personalfinance-api"}


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting up Personal Finance AI Platform")
    # Initialize agents, models, etc.
    from app.services.agent_service import AgentService
    from app.services.model_service import ModelService
    
    app.state.agent_service = AgentService()
    app.state.model_service = ModelService()
    
    logger.info("Services initialized successfully")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Personal Finance AI Platform")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=None,  # Use structlog
    )
