# ValueRail

A minimal digital value settlement and ledger system built with FastAPI.

ValueRail simulates how digital dollars (or stablecoins) move between accounts in a safe, atomic, and auditable way. It serves as a simplified model of financial infrastructure, prioritizing correctness, safety, and auditability.

## Features

- **Account Management**: Create and manage accounts with unique identifiers
- **Minting**: Issue new digital value to accounts
- **Transfers**: Move value between accounts atomically
- **Immutable Ledger**: All transactions are recorded and cannot be modified or deleted
- **Idempotency**: Safe retries with idempotency keys to prevent duplicate transactions
- **Double-Spending Prevention**: Database-level constraints and row locking prevent negative balances

## Safety Guarantees

- **Atomicity**: All operations are wrapped in database transactions (all-or-nothing)
- **No Negative Balances**: Enforced at the database level with CHECK constraints
- **No Double-Spending**: Row-level locks prevent race conditions in concurrent transfers
- **Idempotent Operations**: Retry-safe with idempotency keys
- **Complete Audit Trail**: Append-only transaction ledger

## Architecture

### Data Model

```
┌─────────────┐       ┌─────────────┐
│   accounts  │       │  balances   │
├─────────────┤       ├─────────────┤
│ id (PK)     │──────<│ account_id  │
│ name        │       │ amount      │
│ created_at  │       │ version     │
│ updated_at  │       │ updated_at  │
└─────────────┘       └─────────────┘
        │
        │
        ▼
┌───────────────────┐
│   transactions    │
├───────────────────┤
│ id (PK)           │
│ type (MINT/XFER)  │
│ from_account_id   │
│ to_account_id     │
│ amount            │
│ idempotency_key   │
│ description       │
│ created_at        │
└───────────────────┘

┌───────────────────┐
│ idempotency_keys  │
├───────────────────┤
│ key (PK)          │
│ response (JSON)   │
│ created_at        │
└───────────────────┘
```

## Getting Started

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (for containerized deployment)

### Local Development (SQLite)

1. **Clone and setup**:
   ```bash
   cd valuerail
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Run the application**:
   ```bash
   uvicorn app.main:app --reload
   ```

3. **Access the API**:
   - API: http://localhost:8000
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Docker Deployment (PostgreSQL)

1. **Start with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

2. **Access the API**:
   - API: http://localhost:8000
   - PostgreSQL: localhost:5432

3. **Stop services**:
   ```bash
   docker-compose down
   ```

### Development with Docker (SQLite)

```bash
docker-compose -f docker-compose.dev.yml up -d
```

## API Reference

### Accounts

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/accounts` | POST | Create a new account |
| `/api/v1/accounts` | GET | List all accounts |
| `/api/v1/accounts/{id}` | GET | Get account details |
| `/api/v1/accounts/{id}/balance` | GET | Get account balance |

### Transactions

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/transactions/mint` | POST | Mint new value to an account |
| `/api/v1/transactions/transfer` | POST | Transfer value between accounts |
| `/api/v1/transactions` | GET | List all transactions |
| `/api/v1/transactions/{id}` | GET | Get transaction details |

## Usage Examples

### Create an Account

```bash
curl -X POST http://localhost:8000/api/v1/accounts \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice"}'
```

Response:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Alice",
  "balance": 0,
  "created_at": "2024-01-15T10:30:00Z"
}
```

### Mint Value

```bash
curl -X POST http://localhost:8000/api/v1/transactions/mint \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "550e8400-e29b-41d4-a716-446655440000",
    "amount": 10000,
    "description": "Initial funding",
    "idempotency_key": "mint-001"
  }'
```

### Transfer Value

```bash
curl -X POST http://localhost:8000/api/v1/transactions/transfer \
  -H "Content-Type: application/json" \
  -d '{
    "from_account_id": "550e8400-e29b-41d4-a716-446655440000",
    "to_account_id": "660e8400-e29b-41d4-a716-446655440001",
    "amount": 500,
    "description": "Payment for services",
    "idempotency_key": "transfer-001"
  }'
```

### Check Balance

```bash
curl http://localhost:8000/api/v1/accounts/550e8400-e29b-41d4-a716-446655440000/balance
```

## Idempotency

To ensure safe retries and prevent duplicate transactions, include an `idempotency_key` in your mint and transfer requests:

```json
{
  "idempotency_key": "unique-request-id-123",
  ...
}
```

If the same idempotency key is used again:
- The original transaction is returned
- No new transaction is created
- Balances remain unchanged

This is crucial for:
- Network retry scenarios
- Client-side error recovery
- Ensuring exactly-once semantics

## Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_transfers.py

# Run with coverage
pytest --cov=app tests/
```

## Configuration

Configure the application using environment variables or a `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./valuerail.db` | Database connection string |
| `DEBUG` | `false` | Enable debug mode |
| `APP_NAME` | `ValueRail` | Application name |
| `APP_VERSION` | `1.0.0` | Application version |

### PostgreSQL Connection String

```
DATABASE_URL=postgresql://user:password@host:5432/database
```

## Project Structure

```
valuerail/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py            # Configuration settings
│   ├── database.py          # Database connection and session
│   ├── models/              # SQLAlchemy models
│   │   ├── account.py
│   │   ├── balance.py
│   │   ├── transaction.py
│   │   └── idempotency.py
│   ├── schemas/             # Pydantic schemas
│   │   ├── account.py
│   │   ├── transaction.py
│   │   └── common.py
│   ├── services/            # Business logic
│   │   ├── account_service.py
│   │   ├── ledger_service.py
│   │   └── exceptions.py
│   └── api/                 # API endpoints
│       ├── accounts.py
│       ├── transactions.py
│       └── health.py
├── tests/                   # Unit tests
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Design Decisions

### Why Separate Balance Table?

Instead of storing balance on the Account table:
- Enables row-level locking without blocking account reads
- Supports optimistic locking with version field
- Cleaner separation of concerns

### Why Integer Amounts?

Amounts are stored as integers (smallest unit, e.g., cents):
- Avoids floating-point precision issues
- Standard practice in financial systems
- Exact arithmetic operations

### Why Append-Only Ledger?

Transactions are never modified or deleted:
- Complete audit trail
- Regulatory compliance
- Debugging and reconciliation
- Mathematical invariant: sum of all mints = sum of all balances

## License

MIT License
