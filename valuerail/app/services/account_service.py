"""Account service for managing accounts and balances."""

from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models import Account, Balance
from app.services.exceptions import AccountNotFoundError


class AccountService:
    """Service for account operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_account(self, name: str, account_id: Optional[str] = None) -> Account:
        """
        Create a new account with an initial zero balance.
        
        This operation is atomic - both the account and balance are created
        together in a single transaction.
        
        Args:
            name: The name of the account holder
            account_id: Optional custom account ID (UUID generated if not provided)
            
        Returns:
            The created Account object
        """
        # Create the account
        account = Account(name=name)
        if account_id:
            account.id = account_id
        
        self.db.add(account)
        self.db.flush()  # Get the generated ID
        
        # Create the associated balance record with zero balance
        balance = Balance(account_id=account.id, amount=0)
        self.db.add(balance)
        
        self.db.commit()
        self.db.refresh(account)
        
        return account
    
    def get_account(self, account_id: str) -> Account:
        """
        Get an account by ID.
        
        Args:
            account_id: The account identifier
            
        Returns:
            The Account object
            
        Raises:
            AccountNotFoundError: If the account doesn't exist
        """
        account = self.db.query(Account).filter(Account.id == account_id).first()
        if not account:
            raise AccountNotFoundError(account_id)
        return account
    
    def get_account_with_balance(self, account_id: str) -> tuple[Account, Balance]:
        """
        Get an account with its balance.
        
        Args:
            account_id: The account identifier
            
        Returns:
            Tuple of (Account, Balance)
            
        Raises:
            AccountNotFoundError: If the account doesn't exist
        """
        account = self.get_account(account_id)
        balance = self.db.query(Balance).filter(
            Balance.account_id == account_id
        ).first()
        return account, balance
    
    def get_balance(self, account_id: str) -> int:
        """
        Get the current balance of an account.
        
        Args:
            account_id: The account identifier
            
        Returns:
            The current balance in smallest units
            
        Raises:
            AccountNotFoundError: If the account doesn't exist
        """
        balance = self.db.query(Balance).filter(
            Balance.account_id == account_id
        ).first()
        if not balance:
            raise AccountNotFoundError(account_id)
        return balance.amount
    
    def list_accounts(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Account]:
        """
        List all accounts with pagination.
        
        Args:
            limit: Maximum number of accounts to return
            offset: Number of accounts to skip
            
        Returns:
            List of Account objects
        """
        return (
            self.db.query(Account)
            .order_by(Account.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
    
    def count_accounts(self) -> int:
        """Count total number of accounts."""
        return self.db.query(Account).count()
