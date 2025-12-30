"""Tests for minting operations."""

import pytest


class TestMinting:
    """Tests for minting new value."""
    
    def test_mint_success(self, client, create_test_account):
        """Test successful minting of value."""
        account = create_test_account("Alice")
        
        response = client.post(
            "/api/v1/transactions/mint",
            json={
                "account_id": account["id"],
                "amount": 1000,
                "description": "Initial funding"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["type"] == "MINT"
        assert data["from_account_id"] is None
        assert data["to_account_id"] == account["id"]
        assert data["amount"] == 1000
        assert data["description"] == "Initial funding"
        
        # Verify balance updated
        balance_response = client.get(f"/api/v1/accounts/{account['id']}/balance")
        assert balance_response.json()["balance"] == 1000
    
    def test_mint_multiple_times(self, client, create_test_account):
        """Test minting multiple times to same account."""
        account = create_test_account("Alice")
        
        # Mint 3 times
        for i in range(3):
            response = client.post(
                "/api/v1/transactions/mint",
                json={
                    "account_id": account["id"],
                    "amount": 100
                }
            )
            assert response.status_code == 201
        
        # Verify total balance
        balance_response = client.get(f"/api/v1/accounts/{account['id']}/balance")
        assert balance_response.json()["balance"] == 300
    
    def test_mint_zero_amount_fails(self, client, create_test_account):
        """Test that minting zero is rejected."""
        account = create_test_account("Alice")
        
        response = client.post(
            "/api/v1/transactions/mint",
            json={
                "account_id": account["id"],
                "amount": 0
            }
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_mint_negative_amount_fails(self, client, create_test_account):
        """Test that minting negative amount is rejected."""
        account = create_test_account("Alice")
        
        response = client.post(
            "/api/v1/transactions/mint",
            json={
                "account_id": account["id"],
                "amount": -100
            }
        )
        
        assert response.status_code == 422
    
    def test_mint_to_nonexistent_account_fails(self, client):
        """Test that minting to non-existent account fails."""
        response = client.post(
            "/api/v1/transactions/mint",
            json={
                "account_id": "nonexistent-id",
                "amount": 1000
            }
        )
        
        assert response.status_code == 404
    
    def test_mint_creates_ledger_entry(self, client, create_test_account):
        """Test that minting creates an immutable ledger entry."""
        account = create_test_account("Alice")
        
        mint_response = client.post(
            "/api/v1/transactions/mint",
            json={
                "account_id": account["id"],
                "amount": 1000
            }
        )
        
        transaction_id = mint_response.json()["id"]
        
        # Verify transaction exists in ledger
        ledger_response = client.get(f"/api/v1/transactions/{transaction_id}")
        assert ledger_response.status_code == 200
        assert ledger_response.json()["id"] == transaction_id


class TestMintIdempotency:
    """Tests for mint idempotency."""
    
    def test_mint_with_idempotency_key(self, client, create_test_account):
        """Test minting with idempotency key."""
        account = create_test_account("Alice")
        
        response = client.post(
            "/api/v1/transactions/mint",
            json={
                "account_id": account["id"],
                "amount": 1000,
                "idempotency_key": "mint-key-123"
            }
        )
        
        assert response.status_code == 201
        assert response.json()["idempotency_key"] == "mint-key-123"
    
    def test_mint_idempotency_prevents_duplicate(self, client, create_test_account):
        """Test that same idempotency key prevents duplicate minting."""
        account = create_test_account("Alice")
        idempotency_key = "unique-mint-key-456"
        
        # First mint
        response1 = client.post(
            "/api/v1/transactions/mint",
            json={
                "account_id": account["id"],
                "amount": 1000,
                "idempotency_key": idempotency_key
            }
        )
        assert response1.status_code == 201
        transaction_id = response1.json()["id"]
        
        # Second mint with same key
        response2 = client.post(
            "/api/v1/transactions/mint",
            json={
                "account_id": account["id"],
                "amount": 1000,
                "idempotency_key": idempotency_key
            }
        )
        
        # Should return the same transaction
        assert response2.status_code == 201
        assert response2.json()["id"] == transaction_id
        
        # Balance should only be 1000, not 2000
        balance_response = client.get(f"/api/v1/accounts/{account['id']}/balance")
        assert balance_response.json()["balance"] == 1000
    
    def test_different_idempotency_keys_create_separate_transactions(
        self, client, create_test_account
    ):
        """Test that different idempotency keys create separate transactions."""
        account = create_test_account("Alice")
        
        # First mint
        response1 = client.post(
            "/api/v1/transactions/mint",
            json={
                "account_id": account["id"],
                "amount": 1000,
                "idempotency_key": "key-1"
            }
        )
        
        # Second mint with different key
        response2 = client.post(
            "/api/v1/transactions/mint",
            json={
                "account_id": account["id"],
                "amount": 1000,
                "idempotency_key": "key-2"
            }
        )
        
        # Should be different transactions
        assert response1.json()["id"] != response2.json()["id"]
        
        # Balance should be 2000
        balance_response = client.get(f"/api/v1/accounts/{account['id']}/balance")
        assert balance_response.json()["balance"] == 2000
