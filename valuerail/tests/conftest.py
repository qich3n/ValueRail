"""Test configuration and fixtures."""

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.database import Base, get_db
from app.main import app


# Create test database engine (in-memory SQLite)
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Enable foreign keys for SQLite
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        # Drop all tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database dependency override."""
    
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def create_test_account(client):
    """Factory fixture to create test accounts."""
    
    def _create_account(name: str = "Test Account"):
        response = client.post("/api/v1/accounts", json={"name": name})
        assert response.status_code == 201
        return response.json()
    
    return _create_account


@pytest.fixture
def funded_account(client, create_test_account):
    """Create an account with funds."""
    account = create_test_account("Funded Account")
    
    # Mint 10000 units to the account
    response = client.post(
        "/api/v1/transactions/mint",
        json={
            "account_id": account["id"],
            "amount": 10000,
            "description": "Initial funding"
        }
    )
    assert response.status_code == 201
    
    return account
