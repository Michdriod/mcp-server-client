#!/bin/bash

# One-command setup script for Database Query Assistant
# Usage: ./setup.sh

set -e

echo "🚀 Database Query Assistant - Automated Setup"
echo "=============================================="
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
    echo "✅ Virtual environment created"
else
    echo "✅ Virtual environment already exists"
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source .venv/bin/activate

# Install uv if not present
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv package manager..."
    pip install uv
    echo "✅ uv installed"
else
    echo "✅ uv already installed"
fi

# Install watchdog
echo "📦 Installing watchdog..."
uv pip install watchdog
echo "✅ watchdog installed"

# Install project dependencies
echo "📦 Installing project dependencies (this may take a minute)..."
uv pip install -e .
echo "✅ All dependencies installed"

# Check services
echo ""
echo "🔍 Checking required services..."

# Check PostgreSQL
if psql -U postgres -c "SELECT 1" &> /dev/null; then
    echo "✅ PostgreSQL is running"
else
    echo "❌ PostgreSQL is not running"
    echo "   Start it with: brew services start postgresql@17"
    exit 1
fi

# Check Redis
if redis-cli ping &> /dev/null; then
    echo "✅ Redis is running"
else
    echo "❌ Redis is not running"
    echo "   Start it with: brew services start redis"
    exit 1
fi

# Check .env file
if [ -f ".env" ]; then
    echo "✅ .env file exists"
    
    # Check for required variables
    if grep -q "GROQ_API_KEY" .env && grep -q "LLM_MODEL" .env; then
        echo "✅ Environment variables configured"
    else
        echo "⚠️  Please add GROQ_API_KEY and LLM_MODEL to .env"
    fi
else
    echo "⚠️  .env file not found"
    echo "   Copy .env.example to .env and configure it"
fi

echo ""
echo "=============================================="
echo "✅ Setup complete!"
echo "=============================================="
echo ""
echo "Next steps:"
echo "  1. Configure .env file (if not done)"
echo "  2. Create database: psql -U postgres -c 'CREATE DATABASE Mcp;'"
echo "  3. Load schema: psql -U postgres -d Mcp -f my_db_setup_file.sql"
echo "  4. Test: source .venv/bin/activate && python3 test_e2e.py"
echo "  5. Run: source .venv/bin/activate && streamlit run client/web_ui/app.py"
echo ""
