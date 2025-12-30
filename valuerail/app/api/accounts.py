"""Account API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.account import AccountCreate, AccountResponse, AccountWithBalance
from app.services.account_service import AccountService
from app.services.exceptions import AccountNotFoundError

router = APIRouter()


@router.post("", response_model=AccountWithBalance, status_code=201)
def create_account(
    request: AccountCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new account.
    
    Creates a new account with the specified name and initializes
    it with a zero balance.
    """
    service = AccountService(db)
    account = service.create_account(name=request.name)
    
    return AccountWithBalance(
        id=account.id,
        name=account.name,
        balance=0,
        created_at=account.created_at
    )


@router.get("", response_model=List[AccountWithBalance])
def list_accounts(
    limit: int = Query(default=100, le=1000, ge=1),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    """
    List all accounts.
    
    Returns a paginated list of all accounts with their current balances.
    """
    service = AccountService(db)
    accounts = service.list_accounts(limit=limit, offset=offset)
    
    result = []
    for account in accounts:
        balance = account.balance.amount if account.balance else 0
        result.append(AccountWithBalance(
            id=account.id,
            name=account.name,
            balance=balance,
            created_at=account.created_at
        ))
    
    return result


@router.get("/{account_id}", response_model=AccountWithBalance)
def get_account(
    account_id: str,
    db: Session = Depends(get_db)
):
    """
    Get an account by ID.
    
    Returns the account details including current balance.
    """
    service = AccountService(db)
    
    try:
        account, balance = service.get_account_with_balance(account_id)
    except AccountNotFoundError:
        raise HTTPException(status_code=404, detail=f"Account not found: {account_id}")
    
    return AccountWithBalance(
        id=account.id,
        name=account.name,
        balance=balance.amount if balance else 0,
        created_at=account.created_at
    )


@router.get("/{account_id}/balance")
def get_account_balance(
    account_id: str,
    db: Session = Depends(get_db)
):
    """
    Get the current balance of an account.
    
    Returns just the balance amount for quick balance checks.
    """
    service = AccountService(db)
    
    try:
        balance = service.get_balance(account_id)
    except AccountNotFoundError:
        raise HTTPException(status_code=404, detail=f"Account not found: {account_id}")
    
    return {"account_id": account_id, "balance": balance}
