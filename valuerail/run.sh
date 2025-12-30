#!/bin/bash
# Quick run script for ValueRail

cd "$(dirname "$0")"

echo "🚀 Starting ValueRail..."
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies if needed
if ! python -c "import fastapi" 2>/dev/null; then
    echo "📥 Installing dependencies..."
    pip install -r requirements.txt
fi

echo ""
echo "✅ Starting server on http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo "❤️  Health: http://localhost:8000/api/v1/health"
echo ""
echo "Press CTRL+C to stop"
echo ""

# Run the application
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
