#!/bin/bash
# API Server Startup Script
# Ensures proper environment setup before starting the server

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🚀 Starting Database Query Assistant API Server..."

# Load environment variables from .env file
if [ -f .env ]; then
    echo "📋 Loading environment variables from .env..."
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
    echo "✅ Environment variables loaded"
else
    echo "⚠️  Warning: .env file not found"
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Error: Virtual environment not found. Please run setup.sh first."
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Check if Redis is running (optional)
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        echo "✅ Redis is running - caching enabled"
    else
        echo "⚠️  Redis is not running - caching will be disabled"
        echo "   To enable caching, run: redis-server"
    fi
else
    echo "ℹ️  Redis not installed - caching will be disabled"
fi

# Start the API server
echo "🎯 Starting API server on port 8000..."
python server/api_server.py
