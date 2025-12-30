"""Tests for account operations."""

import pytest


class TestAccountCreation:
    """Tests for account creation."""
    
    def test_create_account_success(self, client):
        """Test successful account creation."""
        response = client.post(
            "/api/v1/accounts",
            json={"name": "Alice"}
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert "id" in data
        assert data["name"] == "Alice"
        assert data["balance"] == 0
        assert "created_at" in data
    
    def test_create_account_empty_name_fails(self, client):
        """Test that empty name is rejected."""
        response = client.post(
            "/api/v1/accounts",
            json={"name": ""}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_create_multiple_accounts(self, client):
        """Test creating multiple accounts."""
        names = ["Alice", "Bob", "Charlie"]
        accounts = []
        
        for name in names:
            response = client.post(
                "/api/v1/accounts",
                json={"name": name}
            )
            assert response.status_code == 201
            accounts.append(response.json())
        
        # Each account should have a unique ID
        ids = [a["id"] for a in accounts]
        assert len(ids) == len(set(ids))


class TestAccountRetrieval:
    """Tests for account retrieval."""
    
    def test_get_account_success(self, client, create_test_account):
        """Test retrieving an existing account."""
        account = create_test_account("Alice")
        
        response = client.get(f"/api/v1/accounts/{account['id']}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == account["id"]
        assert data["name"] == "Alice"
    
    def test_get_account_not_found(self, client):
        """Test retrieving a non-existent account."""
        response = client.get("/api/v1/accounts/nonexistent-id")
        
        assert response.status_code == 404
    
    def test_list_accounts(self, client, create_test_account):
        """Test listing accounts."""
        # Create some accounts
        for name in ["Alice", "Bob", "Charlie"]:
            create_test_account(name)
        
        response = client.get("/api/v1/accounts")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
    
    def test_list_accounts_pagination(self, client, create_test_account):
        """Test pagination of account list."""
        # Create 5 accounts
        for i in range(5):
            create_test_account(f"Account {i}")
        
        # Get first page
        response = client.get("/api/v1/accounts?limit=2&offset=0")
        assert response.status_code == 200
        assert len(response.json()) == 2
        
        # Get second page
        response = client.get("/api/v1/accounts?limit=2&offset=2")
        assert response.status_code == 200
        assert len(response.json()) == 2


class TestAccountBalance:
    """Tests for account balance retrieval."""
    
    def test_get_balance_new_account(self, client, create_test_account):
        """Test that new accounts have zero balance."""
        account = create_test_account("Alice")
        
        response = client.get(f"/api/v1/accounts/{account['id']}/balance")
        
        assert response.status_code == 200
        data = response.json()
        assert data["balance"] == 0
    
    def test_get_balance_not_found(self, client):
        """Test balance for non-existent account."""
        response = client.get("/api/v1/accounts/nonexistent-id/balance")
        
        assert response.status_code == 404
