"""API routes for ValueRail."""

from fastapi import APIRouter

from app.api.accounts import router as accounts_router
from app.api.transactions import router as transactions_router
from app.api.health import router as health_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["Health"])
api_router.include_router(accounts_router, prefix="/accounts", tags=["Accounts"])
api_router.include_router(transactions_router, prefix="/transactions", tags=["Transactions"])
