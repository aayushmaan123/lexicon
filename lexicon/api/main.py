"""FastAPI application setup for Lexicon API."""

import logging
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from lexicon.api.models import HealthCheckResponse
from lexicon.api.routes import contracts, documents, knowledge_base, research

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting Lexicon API...")
    yield
    logger.info("Shutting down Lexicon API...")


# Initialize FastAPI application
app = FastAPI(
    title="Lexicon API",
    description=(
        "REST API for the Lexicon Legal AI Platform. Provides endpoints for document analysis, "
        "contract review, legal research, and knowledge base management.\n\n"
        "⚠️ **DISCLAIMER**: All outputs are informational only and should not be considered legal advice. "
        "This system operates only on documents you provide and does not access public legal databases. "
        "Always consult qualified legal professionals for actual legal matters."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)


# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests."""
    logger.info(f"Request: {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(
        f"Response: {request.method} {request.url.path} - Status: {response.status_code}"
    )
    return response


# Error handling middleware
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
):
    """Handle request validation errors."""
    logger.warning(f"Validation error for {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "message": "Request validation failed",
                "type": "ValidationError",
                "details": exc.errors(),
            }
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception for {request.url.path}: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "message": "Internal server error",
                "type": type(exc).__name__,
                "details": str(exc),
            }
        },
    )


# Include routers
app.include_router(documents.router)
app.include_router(contracts.router)
app.include_router(research.router)
app.include_router(knowledge_base.router)


# Health check endpoint
@app.get(
    "/health",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    tags=["health"],
    summary="Health check",
    description="Check the health status of the API service.",
)
async def health_check() -> HealthCheckResponse:
    """
    Health check endpoint.

    Returns the current health status of the API service.

    Returns:
        HealthCheckResponse with status, timestamp, and version
    """
    return HealthCheckResponse(
        status="healthy",
        timestamp=datetime.now(UTC),
        version="1.0.0",
    )


# Root endpoint
@app.get(
    "/",
    tags=["root"],
    summary="API root",
    description="Root endpoint providing API information.",
)
async def root():
    """
    Root endpoint.

    Returns basic API information and links to documentation.
    """
    return {
        "name": "Lexicon API",
        "version": "1.0.0",
        "description": "Legal AI Platform API",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
    }
