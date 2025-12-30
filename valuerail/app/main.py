"""ValueRail - Digital Value Settlement and Ledger System."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings
from app.database import init_db
from app.api import api_router

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup/shutdown events."""
    # Startup: Initialize database
    init_db()
    yield
    # Shutdown: cleanup if needed


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

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled errors."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred"
        }
    )


# Include API routes
app.include_router(api_router, prefix="/api/v1")


# Root endpoint
@app.get("/")
def root():
    """Root endpoint with service information."""
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/api/v1/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
