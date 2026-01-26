"""Transaction API endpoints (mint and transfer)."""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.transaction import (
    MintRequest,
    TransferRequest,
    TransactionResponse,
    TransactionListResponse,
)
from app.services.ledger_service import LedgerService
from app.services.exceptions import (
    AccountNotFoundError,
    InsufficientBalanceError,
    InvalidTransferError,
)

router = APIRouter()


def _transaction_to_response(transaction) -> TransactionResponse:
    """Convert a Transaction model to a response schema."""
    return TransactionResponse(
        id=transaction.id,
        type=transaction.type.value,
        from_account_id=transaction.from_account_id,
        to_account_id=transaction.to_account_id,
        amount=transaction.amount,
        description=transaction.description,
        idempotency_key=transaction.idempotency_key,
        created_at=transaction.created_at
    )


@router.post("/mint", response_model=TransactionResponse, status_code=201)
def mint_value(
    request: MintRequest,
    db: Session = Depends(get_db)
):
    """
    Mint new value to an account.
    
    Creates new digital value and adds it to the specified account.
    This operation is atomic and recorded in the immutable ledger.
    
    Use an idempotency key to ensure safe retries without double-minting.
    
    Rate limited to 60 requests per minute per IP address.
    """
    service = LedgerService(db)
    
    try:
        transaction = service.mint(
            account_id=request.account_id,
            amount=request.amount,
            description=request.description,
            idempotency_key=request.idempotency_key
        )
    except AccountNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return _transaction_to_response(transaction)


@router.post("/transfer", response_model=TransactionResponse, status_code=201)
def transfer_value(
    request: TransferRequest,
    db: Session = Depends(get_db)
):
    """
    Transfer value between accounts.
    
    Moves digital value from one account to another atomically.
    The operation will fail if the source account has insufficient balance.
    
    Use an idempotency key to ensure safe retries without double-spending.
    
    Rate limited to 60 requests per minute per IP address.
    
    Error codes:
    - 404: Account not found (source or destination)
    - 400: Insufficient balance or invalid transfer
    """
    service = LedgerService(db)
    
    try:
        transaction = service.transfer(
            from_account_id=request.from_account_id,
            to_account_id=request.to_account_id,
            amount=request.amount,
            description=request.description,
            idempotency_key=request.idempotency_key
        )
    except AccountNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except InsufficientBalanceError as e:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "insufficient_balance",
                "message": str(e),
                "account_id": e.account_id,
                "available": e.available,
                "required": e.required
            }
        )
    except InvalidTransferError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    return _transaction_to_response(transaction)


@router.get("", response_model=TransactionListResponse)
def list_transactions(
    account_id: Optional[str] = Query(default=None, description="Filter by account ID"),
    limit: int = Query(default=100, le=1000, ge=1),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    """
    List transactions from the ledger.
    
    Returns a paginated list of transactions, optionally filtered by account.
    Transactions are ordered by creation time (newest first).
    """
    service = LedgerService(db)
    
    transactions = service.list_transactions(
        account_id=account_id,
        limit=limit,
        offset=offset
    )
    total = service.count_transactions(account_id=account_id)
    
    return TransactionListResponse(
        transactions=[_transaction_to_response(t) for t in transactions],
        total=total
    )


@router.get("/{transaction_id}", response_model=TransactionResponse)
def get_transaction(
    transaction_id: str,
    db: Session = Depends(get_db)
):
    """
    Get a transaction by ID.
    
    Returns the details of a specific transaction from the ledger.
    """
    service = LedgerService(db)
    
    transaction = service.get_transaction(transaction_id)
    if not transaction:
        raise HTTPException(
            status_code=404,
            detail=f"Transaction not found: {transaction_id}"
        )
    
    return _transaction_to_response(transaction)
