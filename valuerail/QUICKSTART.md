# Quick Start Guide - ValueRail

## Option 1: Run Locally (Recommended for Testing)

### Step 1: Install Dependencies

```bash
cd /Users/qich3n/Downloads/ValueRail/valuerail
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Run the Application

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

You should see output like:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Step 3: Verify It's Running

Open your browser or use curl:

**Browser:**
- http://localhost:8000 - Root endpoint
- http://localhost:8000/docs - Interactive API docs (Swagger UI)
- http://localhost:8000/api/v1/health - Health check

**Command line:**
```bash
# Health check
curl http://localhost:8000/api/v1/health

# Root endpoint
curl http://localhost:8000

# Should return:
# {"status":"healthy","service":"ValueRail"}
```

## Option 2: Run with Docker (PostgreSQL)

```bash
cd /Users/qich3n/Downloads/ValueRail/valuerail
docker-compose up -d
```

Check logs:
```bash
docker-compose logs -f valuerail
```

## Option 3: Run Tests to Verify

```bash
cd /Users/qich3n/Downloads/ValueRail/valuerail
pytest -v
```

## How to Know It's Working

✅ **Signs the application is running:**
1. Server starts without errors
2. Health endpoint returns: `{"status": "healthy", "service": "ValueRail"}`
3. Swagger UI loads at http://localhost:8000/docs
4. You can create accounts and transactions

**Quick Test:**
```bash
# 1. Check health
curl http://localhost:8000/api/v1/health

# 2. Create an account
curl -X POST http://localhost:8000/api/v1/accounts \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Account"}'

# 3. List accounts
curl http://localhost:8000/api/v1/accounts
```

## Troubleshooting

- **Port 8000 already in use?** Change port: `uvicorn app.main:app --port 8001`
- **Import errors?** Make sure you activated the virtual environment and installed requirements
- **Database errors?** The app will create a SQLite database automatically on first run

