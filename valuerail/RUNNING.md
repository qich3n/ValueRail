# How to Run ValueRail

Complete guide to setting up and running the ValueRail application.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Detailed Setup](#detailed-setup)
- [Running the Application](#running-the-application)
- [Accessing the Application](#accessing-the-application)
- [Docker Deployment](#docker-deployment)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

## Prerequisites

- **Python 3.11 or higher** (Python 3.13 may have compatibility issues with some packages)
- **pip** (Python package manager)
- **Git** (for cloning the repository)
- **Docker & Docker Compose** (optional, for containerized deployment)

## Quick Start

### Step 1: Navigate to Project Directory
```bash
cd valuerail
```

### Step 2: Create Virtual Environment
```bash
python3.11 -m venv venv
```

**Note:** Use Python 3.11 specifically, as Python 3.13 has compatibility issues with pydantic-core.

### Step 3: Activate Virtual Environment

**On macOS/Linux:**
```bash
source venv/bin/activate
```

**On Windows:**
```bash
venv\Scripts\activate
```

You should see `(venv)` in your terminal prompt.

### Step 4: Install Dependencies
```bash
pip install --upgrade pip
pip install fastapi==0.109.0 "uvicorn[standard]==0.27.0" sqlalchemy==2.0.25 pydantic==2.5.3 pydantic-settings==2.1.0 alembic==1.13.1 pytest==7.4.4 pytest-asyncio==0.23.3 httpx==0.26.0
```

**Note:** `psycopg2-binary` is optional and only needed for PostgreSQL. For SQLite (default), you can skip it.

### Step 5: Start the Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Step 6: Open in Browser
Navigate to: **http://localhost:8000**

The web interface will load automatically!

## Detailed Setup

### Option A: Local Development (SQLite)

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd ValueRail/valuerail
   ```

2. **Create virtual environment**:
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```
   
   If `psycopg2-binary` fails (it's only needed for PostgreSQL), install the rest:
   ```bash
   pip install fastapi==0.109.0 "uvicorn[standard]==0.27.0" sqlalchemy==2.0.25 pydantic==2.5.3 pydantic-settings==2.1.0 alembic==1.13.1 pytest==7.4.4 pytest-asyncio==0.23.3 httpx==0.26.0
   ```

4. **Run the application**:
   ```bash
   uvicorn app.main:app --reload
   ```

5. **Access the application**:
   - **Web Frontend**: http://localhost:8000
   - **API Documentation**: http://localhost:8000/docs
   - **Health Check**: http://localhost:8000/api/v1/health

### Option B: Docker Deployment (PostgreSQL)

1. **Start services with Docker Compose**:
   ```bash
   docker-compose up -d
   ```

2. **View logs**:
   ```bash
   docker-compose logs -f valuerail
   ```

3. **Access the application**:
   - **Web Frontend**: http://localhost:8000
   - **PostgreSQL**: localhost:5432

4. **Stop services**:
   ```bash
   docker-compose down
   ```

### Option C: Development Docker (SQLite)

```bash
docker-compose -f docker-compose.dev.yml up -d
```

## Running the Application

### Basic Command
```bash
uvicorn app.main:app --reload
```

### With Custom Host/Port
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode (No Auto-reload)
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Command Options
- `--reload`: Auto-reload on code changes (development only)
- `--host 0.0.0.0`: Listen on all network interfaces
- `--port 8000`: Specify port (default is 8000)
- `--workers 4`: Number of worker processes (production)

## Accessing the Application

Once the server is running, you can access:

### Web Interface
- **Main Application**: http://localhost:8000
  - Interactive dashboard
  - Account management
  - Mint and transfer operations
  - Transaction history

### API Endpoints
- **Swagger UI**: http://localhost:8000/docs
  - Interactive API documentation
  - Test endpoints directly in browser
  
- **ReDoc**: http://localhost:8000/redoc
  - Alternative API documentation format

- **Health Check**: http://localhost:8000/api/v1/health
  - Returns: `{"status":"healthy","service":"ValueRail"}`

### API Endpoints List
- `POST /api/v1/accounts` - Create account
- `GET /api/v1/accounts` - List all accounts
- `GET /api/v1/accounts/{id}` - Get account details
- `GET /api/v1/accounts/{id}/balance` - Get account balance
- `POST /api/v1/transactions/mint` - Mint value to account
- `POST /api/v1/transactions/transfer` - Transfer between accounts
- `GET /api/v1/transactions` - List transactions
- `GET /api/v1/transactions/{id}` - Get transaction details

## Testing the Application

### Quick Test with curl

**1. Health Check:**
```bash
curl http://localhost:8000/api/v1/health
```

**2. Create an Account:**
```bash
curl -X POST http://localhost:8000/api/v1/accounts \
  -H "Content-Type: application/json" \
  -d '{"name": "Alice"}'
```

**3. Mint Value** (replace `<account_id>` with ID from step 2):
```bash
curl -X POST http://localhost:8000/api/v1/transactions/mint \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "<account_id>",
    "amount": 10000,
    "description": "Initial deposit",
    "idempotency_key": "mint-001"
  }'
```

**4. Check Balance:**
```bash
curl http://localhost:8000/api/v1/accounts/<account_id>/balance
```

### Running Tests

```bash
# Activate virtual environment first
source venv/bin/activate

# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_transfers.py

# Run with coverage report
pytest --cov=app tests/
```

## Configuration

### Environment Variables

Create a `.env` file in the `valuerail` directory (optional):

```env
# Database
DATABASE_URL=sqlite:///./valuerail.db
# For PostgreSQL: DATABASE_URL=postgresql://user:password@localhost:5432/valuerail

# Application
DEBUG=false
APP_NAME=ValueRail
APP_VERSION=1.0.0

# CORS (comma-separated origins, or "*" for all)
CORS_ORIGINS=*
# Production example: CORS_ORIGINS=http://localhost:3000,https://example.com
```

### Default Configuration

- **Database**: SQLite (`valuerail.db` in project directory)
- **Port**: 8000
- **Debug Mode**: false
- **CORS**: Allows all origins (configurable)

## Troubleshooting

### Port Already in Use
```bash
# Use a different port
uvicorn app.main:app --reload --port 8001
```

### Import Errors
- Make sure virtual environment is activated
- Verify all dependencies are installed: `pip list`
- Reinstall dependencies: `pip install -r requirements.txt`

### Database Errors
- The app creates `valuerail.db` automatically on first run
- If you see database errors, try deleting `valuerail.db` and restarting
- For PostgreSQL, ensure the database exists and credentials are correct

### Python Version Issues
- **Use Python 3.11** - Python 3.13 has compatibility issues
- Check version: `python3.11 --version`
- Create venv with specific version: `python3.11 -m venv venv`

### Frontend Not Loading
- Ensure server is running
- Check browser console for errors (F12)
- Verify you're accessing `http://localhost:8000` (not `/docs`)
- Check that static files exist in `static/` directory

### psycopg2-binary Installation Fails
- This is **normal** - it's only needed for PostgreSQL
- For SQLite (default), you can skip it
- Install other packages individually if needed

### Module Not Found Errors
- Activate virtual environment: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`
- Check Python path: `which python` (should point to venv)

## Stopping the Server

- Press `CTRL+C` in the terminal where the server is running
- Or find and kill the process:
  ```bash
  pkill -f "uvicorn app.main:app"
  ```

## Next Steps

1. **Explore the Web Interface**: http://localhost:8000
   - Create accounts
   - Mint value
   - Transfer between accounts
   - View transaction history

2. **Try the API**: http://localhost:8000/docs
   - Interactive API testing
   - See request/response formats
   - Test all endpoints

3. **Read the Code**:
   - `app/main.py` - Application entry point
   - `app/api/` - API endpoints
   - `app/services/` - Business logic
   - `app/models/` - Database models

4. **Run Tests**: `pytest -v`

## Production Deployment

For production deployment:

1. **Set environment variables**:
   ```env
   DATABASE_URL=postgresql://user:password@host:5432/valuerail
   DEBUG=false
   CORS_ORIGINS=https://yourdomain.com
   ```

2. **Use production server**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
   ```

3. **Or use Docker**:
   ```bash
   docker-compose up -d
   ```

4. **Set up reverse proxy** (nginx, etc.) for HTTPS and domain routing

## Support

For issues or questions:
- Check the [README.md](README.md) for detailed documentation
- Review test files in `tests/` for usage examples
- Check API documentation at `/docs` endpoint
