"""ValueRail - Digital Value Settlement and Ledger System."""

import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.config import get_settings
from app.database import init_db
from app.api import api_router
from app.services.exceptions import (
    ValueRailError,
    AccountNotFoundError,
    InsufficientBalanceError,
    InvalidTransferError,
    DuplicateAccountError,
    IdempotencyKeyExistsError,
)

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if get_settings().debug else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

settings = get_settings()

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup: Initialize database
    logger.info("Starting ValueRail application...")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database: %s", e, exc_info=True)
        raise
    yield
    # Shutdown: cleanup if needed
    logger.info("Shutting down ValueRail application...")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="""
    ValueRail is a minimal digital value settlement and ledger system.
    
    It simulates how digital dollars (or stablecoins) move between accounts
    in a safe, atomic, and auditable way.
    
    ## Features
    
    - **Account Management**: Create and manage accounts
    - **Minting**: Issue new digital value to accounts
    - **Transfers**: Move value between accounts atomically
    - **Immutable Ledger**: All transactions are recorded and cannot be modified
    - **Idempotency**: Safe retries with idempotency keys
    
    ## Safety Guarantees
    
    - Atomic transactions (all-or-nothing)
    - No negative balances
    - No double-spending
    - Complete audit trail
    """,
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add state for limiter
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda request, exc: JSONResponse(
    status_code=429,
    content={
        "error": "rate_limit_exceeded",
        "message": "Too many requests. Please try again later."
    }
))

# Add request size limit middleware (10 MB)
MAX_REQUEST_SIZE = 10 * 1024 * 1024  # 10 MB

@app.middleware("http")
async def size_limit_middleware(request: Request, call_next):
    """Middleware to limit request body size."""
    if request.method in ("POST", "PUT", "PATCH"):
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                if int(content_length) > MAX_REQUEST_SIZE:
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": "payload_too_large",
                            "message": f"Request body exceeds maximum size of {MAX_REQUEST_SIZE // 1024 // 1024}MB"
                        }
                    )
            except ValueError:
                pass
    
    return await call_next(request)

# Add CORS middleware
# Configure via CORS_ORIGINS environment variable (comma-separated)
# e.g., CORS_ORIGINS=http://localhost:3000,https://example.com
# Use "*" for development (default)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Custom exception handlers for ValueRail errors
@app.exception_handler(AccountNotFoundError)
async def account_not_found_handler(_request: Request, exc: AccountNotFoundError):
    """Handle account not found errors."""
    logger.warning("Account not found: %s", exc.account_id)
    return JSONResponse(
        status_code=404,
        content={
            "error": "account_not_found",
            "message": str(exc),
            "account_id": exc.account_id
        }
    )


@app.exception_handler(InsufficientBalanceError)
async def insufficient_balance_handler(_request: Request, exc: InsufficientBalanceError):
    """Handle insufficient balance errors."""
    logger.warning(
        "Insufficient balance: account=%s, available=%s, required=%s",
        exc.account_id,
        exc.available,
        exc.required
    )
    return JSONResponse(
        status_code=400,
        content={
            "error": "insufficient_balance",
            "message": str(exc),
            "account_id": exc.account_id,
            "available": exc.available,
            "required": exc.required
        }
    )


@app.exception_handler(InvalidTransferError)
async def invalid_transfer_handler(_request: Request, exc: InvalidTransferError):
    """Handle invalid transfer errors."""
    logger.warning("Invalid transfer: %s", str(exc))
    return JSONResponse(
        status_code=400,
        content={
            "error": "invalid_transfer",
            "message": str(exc)
        }
    )


@app.exception_handler(DuplicateAccountError)
async def duplicate_account_handler(_request: Request, exc: DuplicateAccountError):
    """Handle duplicate account errors."""
    logger.warning("Duplicate account: %s", exc.account_id)
    return JSONResponse(
        status_code=409,
        content={
            "error": "duplicate_account",
            "message": str(exc),
            "account_id": exc.account_id
        }
    )


@app.exception_handler(IdempotencyKeyExistsError)
async def idempotency_key_exists_handler(_request: Request, exc: IdempotencyKeyExistsError):
    """Handle idempotency key already exists errors."""
    logger.info("Idempotency key already exists: %s", exc.key)
    # Return the cached response with 200 status
    import json
    try:
        response_data = json.loads(exc.response) if isinstance(exc.response, str) else exc.response
        return JSONResponse(status_code=200, content=response_data)
    except (json.JSONDecodeError, TypeError):
        return JSONResponse(
            status_code=409,
            content={
                "error": "idempotency_key_exists",
                "message": str(exc),
                "key": exc.key
            }
        )


@app.exception_handler(ValueRailError)
async def valuerail_error_handler(_request: Request, exc: ValueRailError):
    """Handle generic ValueRail errors."""
    logger.error("ValueRail error: %s", str(exc), exc_info=True)
    return JSONResponse(
        status_code=400,
        content={
            "error": "valuerail_error",
            "message": str(exc)
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    logger.error(
        "Unhandled exception: %s: %s",
        type(exc).__name__,
        str(exc),
        exc_info=True,
        extra={"path": request.url.path, "method": request.method}
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred" if not settings.debug else str(exc)
        }
    )


# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Serve static files (frontend)
try:
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
    if os.path.exists(static_dir):
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
        logger.info("Serving static files from %s", static_dir)
except Exception as e:
    logger.warning("Could not mount static files: %s", e)

# Root endpoint - serve frontend if available
@app.get("/")
def root():
    """Root endpoint - serves frontend or API info."""
    static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static")
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    
    # Fallback to API info
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/api/v1/health",
        "frontend": "/static/index.html"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
