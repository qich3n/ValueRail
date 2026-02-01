"""Custom exceptions for ValueRail services."""


class ValueRailError(Exception):
    """Base exception for ValueRail errors."""
    pass


class AccountNotFoundError(ValueRailError):
    """Raised when an account is not found."""
    
    def __init__(self, account_id: str):
        self.account_id = account_id
        super().__init__(f"Account not found: {account_id}")


class InsufficientBalanceError(ValueRailError):
    """Raised when an account has insufficient balance for a transfer."""
    
    def __init__(self, account_id: str, available: int, required: int):
        self.account_id = account_id
        self.available = available
        self.required = required
        super().__init__(
            f"Insufficient balance in account {account_id}: "
            f"available={available}, required={required}"
        )


class DuplicateAccountError(ValueRailError):
    """Raised when trying to create a duplicate account."""
    
    def __init__(self, account_id: str):
        self.account_id = account_id
        super().__init__(f"Account already exists: {account_id}")


class InvalidTransferError(ValueRailError):
    """Raised for invalid transfer operations."""
    
    def __init__(self, message: str):
        super().__init__(message)


class IdempotencyKeyExistsError(ValueRailError):
    """Raised when an idempotency key has already been used."""
    
    def __init__(self, key: str, response: str):
        self.key = key
        self.response = response
        super().__init__(f"Idempotency key already exists: {key}")


class TransferLimitExceededError(ValueRailError):
    """Raised when a transfer exceeds the configured maximum amount."""

    def __init__(self, amount: int, maximum: int):
        self.amount = amount
        self.maximum = maximum
        super().__init__(
            f"Transfer amount {amount} exceeds maximum allowed {maximum}"
        )


class DailyMintLimitExceededError(ValueRailError):
    """Raised when an account exceeds the daily mint limit."""

    def __init__(self, account_id: str, requested: int, remaining: int):
        self.account_id = account_id
        self.requested = requested
        self.remaining = remaining
        super().__init__(
            f"Daily mint limit exceeded for account {account_id}: "
            f"requested={requested}, remaining={remaining}"
        )
