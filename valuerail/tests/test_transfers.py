"""Tests for transfer operations."""

import pytest


class TestTransfers:
    """Tests for transferring value between accounts."""
    
    def test_transfer_success(self, client, create_test_account):
        """Test successful transfer between accounts."""
        # Create two accounts
        alice = create_test_account("Alice")
        bob = create_test_account("Bob")
        
        # Fund Alice's account
        client.post(
            "/api/v1/transactions/mint",
            json={"account_id": alice["id"], "amount": 1000}
        )
        
        # Transfer from Alice to Bob
        response = client.post(
            "/api/v1/transactions/transfer",
            json={
                "from_account_id": alice["id"],
                "to_account_id": bob["id"],
                "amount": 300,
                "description": "Payment for services"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["type"] == "TRANSFER"
        assert data["from_account_id"] == alice["id"]
        assert data["to_account_id"] == bob["id"]
        assert data["amount"] == 300
        
        # Verify balances
        alice_balance = client.get(f"/api/v1/accounts/{alice['id']}/balance").json()
        bob_balance = client.get(f"/api/v1/accounts/{bob['id']}/balance").json()
        
        assert alice_balance["balance"] == 700
        assert bob_balance["balance"] == 300
    
    def test_transfer_entire_balance(self, client, create_test_account):
        """Test transferring entire balance."""
        alice = create_test_account("Alice")
        bob = create_test_account("Bob")
        
        client.post(
            "/api/v1/transactions/mint",
            json={"account_id": alice["id"], "amount": 1000}
        )
        
        response = client.post(
            "/api/v1/transactions/transfer",
            json={
                "from_account_id": alice["id"],
                "to_account_id": bob["id"],
                "amount": 1000
            }
        )
        
        assert response.status_code == 201
        
        alice_balance = client.get(f"/api/v1/accounts/{alice['id']}/balance").json()
        bob_balance = client.get(f"/api/v1/accounts/{bob['id']}/balance").json()
        
        assert alice_balance["balance"] == 0
        assert bob_balance["balance"] == 1000


class TestInsufficientBalance:
    """Tests for insufficient balance scenarios."""
    
    def test_transfer_insufficient_balance(self, client, create_test_account):
        """Test that transfer fails with insufficient balance."""
        alice = create_test_account("Alice")
        bob = create_test_account("Bob")
        
        # Fund Alice with 100
        client.post(
            "/api/v1/transactions/mint",
            json={"account_id": alice["id"], "amount": 100}
        )
        
        # Try to transfer 200
        response = client.post(
            "/api/v1/transactions/transfer",
            json={
                "from_account_id": alice["id"],
                "to_account_id": bob["id"],
                "amount": 200
            }
        )
        
        assert response.status_code == 400
        data = response.json()["detail"]
        assert data["error"] == "insufficient_balance"
        assert data["available"] == 100
        assert data["required"] == 200
    
    def test_transfer_from_zero_balance(self, client, create_test_account):
        """Test transfer from account with zero balance."""
        alice = create_test_account("Alice")
        bob = create_test_account("Bob")
        
        response = client.post(
            "/api/v1/transactions/transfer",
            json={
                "from_account_id": alice["id"],
                "to_account_id": bob["id"],
                "amount": 1
            }
        )
        
        assert response.status_code == 400
    
    def test_insufficient_balance_doesnt_affect_balances(
        self, client, create_test_account
    ):
        """Test that failed transfer doesn't change any balances."""
        alice = create_test_account("Alice")
        bob = create_test_account("Bob")
        
        client.post(
            "/api/v1/transactions/mint",
            json={"account_id": alice["id"], "amount": 100}
        )
        
        # Failed transfer
        client.post(
            "/api/v1/transactions/transfer",
            json={
                "from_account_id": alice["id"],
                "to_account_id": bob["id"],
                "amount": 200
            }
        )
        
        # Verify balances unchanged
        alice_balance = client.get(f"/api/v1/accounts/{alice['id']}/balance").json()
        bob_balance = client.get(f"/api/v1/accounts/{bob['id']}/balance").json()
        
        assert alice_balance["balance"] == 100
        assert bob_balance["balance"] == 0


class TestTransferValidation:
    """Tests for transfer validation."""
    
    def test_transfer_zero_amount_fails(self, client, create_test_account):
        """Test that transferring zero is rejected."""
        alice = create_test_account("Alice")
        bob = create_test_account("Bob")
        
        response = client.post(
            "/api/v1/transactions/transfer",
            json={
                "from_account_id": alice["id"],
                "to_account_id": bob["id"],
                "amount": 0
            }
        )
        
        assert response.status_code == 422
    
    def test_transfer_negative_amount_fails(self, client, create_test_account):
        """Test that transferring negative amount is rejected."""
        alice = create_test_account("Alice")
        bob = create_test_account("Bob")
        
        response = client.post(
            "/api/v1/transactions/transfer",
            json={
                "from_account_id": alice["id"],
                "to_account_id": bob["id"],
                "amount": -100
            }
        )
        
        assert response.status_code == 422
    
    def test_transfer_to_same_account_fails(self, client, create_test_account):
        """Test that self-transfer is rejected."""
        alice = create_test_account("Alice")
        
        client.post(
            "/api/v1/transactions/mint",
            json={"account_id": alice["id"], "amount": 1000}
        )
        
        response = client.post(
            "/api/v1/transactions/transfer",
            json={
                "from_account_id": alice["id"],
                "to_account_id": alice["id"],
                "amount": 100
            }
        )
        
        assert response.status_code == 422
    
    def test_transfer_from_nonexistent_account_fails(self, client, create_test_account):
        """Test transfer from non-existent account."""
        bob = create_test_account("Bob")
        
        response = client.post(
            "/api/v1/transactions/transfer",
            json={
                "from_account_id": "nonexistent-id",
                "to_account_id": bob["id"],
                "amount": 100
            }
        )
        
        assert response.status_code == 404
    
    def test_transfer_to_nonexistent_account_fails(self, client, create_test_account):
        """Test transfer to non-existent account."""
        alice = create_test_account("Alice")
        
        client.post(
            "/api/v1/transactions/mint",
            json={"account_id": alice["id"], "amount": 1000}
        )
        
        response = client.post(
            "/api/v1/transactions/transfer",
            json={
                "from_account_id": alice["id"],
                "to_account_id": "nonexistent-id",
                "amount": 100
            }
        )
        
        assert response.status_code == 404


class TestTransferIdempotency:
    """Tests for transfer idempotency."""
    
    def test_transfer_with_idempotency_key(self, client, create_test_account):
        """Test transfer with idempotency key."""
        alice = create_test_account("Alice")
        bob = create_test_account("Bob")
        
        client.post(
            "/api/v1/transactions/mint",
            json={"account_id": alice["id"], "amount": 1000}
        )
        
        response = client.post(
            "/api/v1/transactions/transfer",
            json={
                "from_account_id": alice["id"],
                "to_account_id": bob["id"],
                "amount": 300,
                "idempotency_key": "transfer-key-123"
            }
        )
        
        assert response.status_code == 201
        assert response.json()["idempotency_key"] == "transfer-key-123"
    
    def test_transfer_idempotency_prevents_double_spending(
        self, client, create_test_account
    ):
        """Test that same idempotency key prevents double spending."""
        alice = create_test_account("Alice")
        bob = create_test_account("Bob")
        idempotency_key = "unique-transfer-key-456"
        
        client.post(
            "/api/v1/transactions/mint",
            json={"account_id": alice["id"], "amount": 1000}
        )
        
        # First transfer
        response1 = client.post(
            "/api/v1/transactions/transfer",
            json={
                "from_account_id": alice["id"],
                "to_account_id": bob["id"],
                "amount": 300,
                "idempotency_key": idempotency_key
            }
        )
        assert response1.status_code == 201
        transaction_id = response1.json()["id"]
        
        # Retry with same key (simulating network retry)
        response2 = client.post(
            "/api/v1/transactions/transfer",
            json={
                "from_account_id": alice["id"],
                "to_account_id": bob["id"],
                "amount": 300,
                "idempotency_key": idempotency_key
            }
        )
        
        # Should return the same transaction
        assert response2.status_code == 201
        assert response2.json()["id"] == transaction_id
        
        # Verify no double-spending occurred
        alice_balance = client.get(f"/api/v1/accounts/{alice['id']}/balance").json()
        bob_balance = client.get(f"/api/v1/accounts/{bob['id']}/balance").json()
        
        assert alice_balance["balance"] == 700  # Not 400
        assert bob_balance["balance"] == 300    # Not 600
    
    def test_different_idempotency_keys_create_separate_transfers(
        self, client, create_test_account
    ):
        """Test that different idempotency keys create separate transfers."""
        alice = create_test_account("Alice")
        bob = create_test_account("Bob")
        
        client.post(
            "/api/v1/transactions/mint",
            json={"account_id": alice["id"], "amount": 1000}
        )
        
        # First transfer
        response1 = client.post(
            "/api/v1/transactions/transfer",
            json={
                "from_account_id": alice["id"],
                "to_account_id": bob["id"],
                "amount": 200,
                "idempotency_key": "key-1"
            }
        )
        
        # Second transfer with different key
        response2 = client.post(
            "/api/v1/transactions/transfer",
            json={
                "from_account_id": alice["id"],
                "to_account_id": bob["id"],
                "amount": 200,
                "idempotency_key": "key-2"
            }
        )
        
        # Should be different transactions
        assert response1.json()["id"] != response2.json()["id"]
        
        # Verify balances
        alice_balance = client.get(f"/api/v1/accounts/{alice['id']}/balance").json()
        bob_balance = client.get(f"/api/v1/accounts/{bob['id']}/balance").json()
        
        assert alice_balance["balance"] == 600
        assert bob_balance["balance"] == 400


class TestTransactionLedger:
    """Tests for transaction ledger operations."""
    
    def test_transactions_are_recorded(self, client, create_test_account):
        """Test that all transactions are recorded in ledger."""
        alice = create_test_account("Alice")
        bob = create_test_account("Bob")
        
        # Mint
        client.post(
            "/api/v1/transactions/mint",
            json={"account_id": alice["id"], "amount": 1000}
        )
        
        # Transfer
        client.post(
            "/api/v1/transactions/transfer",
            json={
                "from_account_id": alice["id"],
                "to_account_id": bob["id"],
                "amount": 300
            }
        )
        
        # List all transactions
        response = client.get("/api/v1/transactions")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] == 2
        assert len(data["transactions"]) == 2
    
    def test_filter_transactions_by_account(self, client, create_test_account):
        """Test filtering transactions by account."""
        alice = create_test_account("Alice")
        bob = create_test_account("Bob")
        charlie = create_test_account("Charlie")
        
        # Fund accounts
        client.post(
            "/api/v1/transactions/mint",
            json={"account_id": alice["id"], "amount": 1000}
        )
        client.post(
            "/api/v1/transactions/mint",
            json={"account_id": charlie["id"], "amount": 1000}
        )
        
        # Transfer from Alice to Bob
        client.post(
            "/api/v1/transactions/transfer",
            json={
                "from_account_id": alice["id"],
                "to_account_id": bob["id"],
                "amount": 300
            }
        )
        
        # Transfer from Charlie to Bob
        client.post(
            "/api/v1/transactions/transfer",
            json={
                "from_account_id": charlie["id"],
                "to_account_id": bob["id"],
                "amount": 200
            }
        )
        
        # Filter by Alice (should see mint + 1 transfer)
        alice_txs = client.get(
            f"/api/v1/transactions?account_id={alice['id']}"
        ).json()
        assert alice_txs["total"] == 2
        
        # Filter by Bob (should see 2 transfers)
        bob_txs = client.get(
            f"/api/v1/transactions?account_id={bob['id']}"
        ).json()
        assert bob_txs["total"] == 2
    
    def test_get_single_transaction(self, client, create_test_account):
        """Test retrieving a single transaction."""
        alice = create_test_account("Alice")
        
        mint_response = client.post(
            "/api/v1/transactions/mint",
            json={"account_id": alice["id"], "amount": 1000}
        )
        transaction_id = mint_response.json()["id"]
        
        response = client.get(f"/api/v1/transactions/{transaction_id}")
        assert response.status_code == 200
        assert response.json()["id"] == transaction_id
    
    def test_get_nonexistent_transaction(self, client):
        """Test retrieving non-existent transaction."""
        response = client.get("/api/v1/transactions/nonexistent-id")
        assert response.status_code == 404
