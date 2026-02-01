"""Ledger service for minting and transfers with atomic operations."""

import json
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select, update, func
from sqlalchemy.exc import IntegrityError

from app.config import get_settings
from app.models import Account, Balance, Transaction, TransactionType, IdempotencyKey
from app.services.exceptions import (
    AccountNotFoundError,
    InsufficientBalanceError,
    InvalidTransferError,
    TransferLimitExceededError,
    DailyMintLimitExceededError,
)


class LedgerService:
    """
    Service for ledger operations: minting and transfers.
    
    All operations are atomic and use database transactions to ensure
    consistency. The ledger is append-only - transactions are never
    modified or deleted.
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.settings = get_settings()
    
    def _check_idempotency_key(self, key: str) -> Optional[dict]:
        """
        Check if an idempotency key has been used before.
        
        Args:
            key: The idempotency key to check
            
        Returns:
            The stored response if key exists, None otherwise
        """
        existing = self.db.query(IdempotencyKey).filter(
            IdempotencyKey.key == key
        ).first()
        
        if existing:
            return json.loads(existing.response)
        return None
    
    def _store_idempotency_key(self, key: str, response: dict) -> None:
        """
        Store an idempotency key with its response.
        
        Args:
            key: The idempotency key
            response: The response to store (will be JSON serialized)
        """
        idempotency_record = IdempotencyKey(
            key=key,
            response=json.dumps(response)
        )
        self.db.add(idempotency_record)
    
    def _get_balance_for_update(self, account_id: str) -> Balance:
        """
        Get a balance record with a row-level lock for update.
        
        This prevents race conditions in concurrent transfers by
        locking the row until the transaction completes.
        
        Args:
            account_id: The account identifier
            
        Returns:
            The locked Balance object
            
        Raises:
            AccountNotFoundError: If the account doesn't exist
        """
        # Use SELECT FOR UPDATE to lock the row
        balance = (
            self.db.query(Balance)
            .filter(Balance.account_id == account_id)
            .with_for_update()
            .first()
        )
        
        if not balance:
            raise AccountNotFoundError(account_id)
        
        return balance

    def _get_daily_minted_amount(self, account_id: str) -> int:
        """
        Get total minted amount for an account for the current UTC day.
        """
        now = datetime.now(timezone.utc)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        total = (
            self.db.query(func.coalesce(func.sum(Transaction.amount), 0))
            .filter(Transaction.type == TransactionType.MINT)
            .filter(Transaction.to_account_id == account_id)
            .filter(Transaction.created_at >= start_of_day)
            .filter(Transaction.created_at < end_of_day)
            .scalar()
        )
        return int(total or 0)
    
    def mint(
        self,
        account_id: str,
        amount: int,
        description: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ) -> Transaction:
        """
        Mint (create) new value and add it to an account.
        
        This operation:
        1. Checks idempotency key if provided
        2. Validates the target account exists
        3. Increases the account balance
        4. Records the transaction in the ledger
        5. Stores the idempotency key if provided
        
        All steps are atomic within a single database transaction.
        
        Args:
            account_id: The target account to mint value to
            amount: The amount to mint (must be positive)
            description: Optional description of the mint operation
            idempotency_key: Optional key to ensure idempotent operation
            
        Returns:
            The created Transaction record
            
        Raises:
            AccountNotFoundError: If the target account doesn't exist
            ValueError: If amount is not positive
        """
        if amount <= 0:
            raise ValueError("Mint amount must be positive")
        
        # Check idempotency key
        if idempotency_key:
            existing_response = self._check_idempotency_key(idempotency_key)
            if existing_response:
                # Return the existing transaction
                return self.db.query(Transaction).filter(
                    Transaction.id == existing_response["id"]
                ).first()

        if self.settings.max_daily_mint_per_account > 0:
            minted_today = self._get_daily_minted_amount(account_id)
            remaining = self.settings.max_daily_mint_per_account - minted_today
            if amount > remaining:
                raise DailyMintLimitExceededError(
                    account_id=account_id,
                    requested=amount,
                    remaining=max(0, remaining)
                )
        
        # Lock and update the balance
        balance = self._get_balance_for_update(account_id)
        balance.amount += amount
        balance.version += 1
        
        # Create the transaction record
        transaction = Transaction(
            type=TransactionType.MINT,
            from_account_id=None,
            to_account_id=account_id,
            amount=amount,
            description=description,
            idempotency_key=idempotency_key
        )
        self.db.add(transaction)
        self.db.flush()
        
        # Store idempotency key
        if idempotency_key:
            self._store_idempotency_key(
                idempotency_key,
                {"id": transaction.id}
            )
        
        self.db.commit()
        self.db.refresh(transaction)
        
        return transaction
    
    def transfer(
        self,
        from_account_id: str,
        to_account_id: str,
        amount: int,
        description: Optional[str] = None,
        idempotency_key: Optional[str] = None
    ) -> Transaction:
        """
        Transfer value between two accounts.
        
        This operation:
        1. Checks idempotency key if provided
        2. Validates both accounts exist
        3. Validates sufficient balance in source account
        4. Decreases source balance and increases destination balance
        5. Records the transaction in the ledger
        6. Stores the idempotency key if provided
        
        All steps are atomic within a single database transaction.
        Row-level locks prevent double-spending in concurrent scenarios.
        
        Args:
            from_account_id: The source account
            to_account_id: The destination account
            amount: The amount to transfer (must be positive)
            description: Optional description of the transfer
            idempotency_key: Optional key to ensure idempotent operation
            
        Returns:
            The created Transaction record
            
        Raises:
            AccountNotFoundError: If either account doesn't exist
            InsufficientBalanceError: If source has insufficient balance
            InvalidTransferError: If transfer is invalid (e.g., same account)
            ValueError: If amount is not positive
        """
        if amount <= 0:
            raise ValueError("Transfer amount must be positive")
        
        if from_account_id == to_account_id:
            raise InvalidTransferError("Cannot transfer to the same account")
        
        # Check idempotency key
        if idempotency_key:
            existing_response = self._check_idempotency_key(idempotency_key)
            if existing_response:
                # Return the existing transaction
                return self.db.query(Transaction).filter(
                    Transaction.id == existing_response["id"]
                ).first()

        if self.settings.max_transfer_amount > 0 and amount > self.settings.max_transfer_amount:
            raise TransferLimitExceededError(
                amount=amount,
                maximum=self.settings.max_transfer_amount
            )
        
        # Lock balances in a consistent order to prevent deadlocks
        # Always lock the lower ID first
        if from_account_id < to_account_id:
            from_balance = self._get_balance_for_update(from_account_id)
            to_balance = self._get_balance_for_update(to_account_id)
        else:
            to_balance = self._get_balance_for_update(to_account_id)
            from_balance = self._get_balance_for_update(from_account_id)
        
        # Check sufficient balance
        if from_balance.amount < amount:
            self.db.rollback()
            raise InsufficientBalanceError(
                from_account_id,
                from_balance.amount,
                amount
            )
        
        # Perform the transfer
        from_balance.amount -= amount
        from_balance.version += 1
        to_balance.amount += amount
        to_balance.version += 1
        
        # Create the transaction record
        transaction = Transaction(
            type=TransactionType.TRANSFER,
            from_account_id=from_account_id,
            to_account_id=to_account_id,
            amount=amount,
            description=description,
            idempotency_key=idempotency_key
        )
        self.db.add(transaction)
        self.db.flush()
        
        # Store idempotency key
        if idempotency_key:
            self._store_idempotency_key(
                idempotency_key,
                {"id": transaction.id}
            )
        
        self.db.commit()
        self.db.refresh(transaction)
        
        return transaction
    
    def get_transaction(self, transaction_id: str) -> Optional[Transaction]:
        """
        Get a transaction by ID.
        
        Args:
            transaction_id: The transaction identifier
            
        Returns:
            The Transaction object or None if not found
        """
        return self.db.query(Transaction).filter(
            Transaction.id == transaction_id
        ).first()
    
    def list_transactions(
        self,
        account_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Transaction]:
        """
        List transactions with optional filtering by account.
        
        Args:
            account_id: Optional account to filter by (as sender or receiver)
            limit: Maximum number of transactions to return
            offset: Number of transactions to skip
            
        Returns:
            List of Transaction objects
        """
        query = self.db.query(Transaction)
        
        if account_id:
            query = query.filter(
                (Transaction.from_account_id == account_id) |
                (Transaction.to_account_id == account_id)
            )
        
        return (
            query
            .order_by(Transaction.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
    
    def count_transactions(self, account_id: Optional[str] = None) -> int:
        """
        Count total number of transactions.
        
        Args:
            account_id: Optional account to filter by
            
        Returns:
            Total count of transactions
        """
        query = self.db.query(Transaction)
        
        if account_id:
            query = query.filter(
                (Transaction.from_account_id == account_id) |
                (Transaction.to_account_id == account_id)
            )
        
        return query.count()
