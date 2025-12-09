# Database Query Assistant - MCP Server & Client

Enterprise-grade natural language database query platform built with **Pydantic AI**, **FastMCP**, and **PostgreSQL**. Query your databases using plain English with built-in security, caching, and scheduled reports.

## Features

- 🤖 **Natural Language Queries**: Ask questions in plain English, get SQL results
- 🔒 **Role-Based Access Control**: Fine-grained permissions (table, column, row-level)
- ⚡ **Redis Caching**: Multi-tier caching for optimal performance
- 📊 **Chart Generation**: Automatic data visualization
- 📅 **Scheduled Reports**: Cron-based report automation
- 🔍 **Query History**: Track and share queries across teams
- 🚀 **Horizontally Scalable**: Connection pooling, load balancing ready
- 🛡️ **SQL Injection Protection**: Query validation and sanitization

## Architecture

```bash
User ↔ AI Agent (Pydantic AI) ↔ MCP Server (FastMCP) ↔ PostgreSQL
                                      ↓
                                  Redis Cache
                                      ↓
                                 Celery Workers
```

## Project Structure

```
mcp-server-client/
├── server/                 # MCP Server (17 tools)
│   ├── db/                # Database (SQLAlchemy async)
│   ├── cache/             # Redis caching
│   ├── auth/              # RBAC & security
│   ├── query/             # SQL generation (Pydantic AI)
│   ├── tools/             # Charts, history, export
│   ├── scheduler/         # Celery tasks
│   ├── celery_app.py      # Celery configuration
│   └── mcp_server.py      # FastMCP server
├── client/                # Client interfaces
│   ├── mcp_client.py      # Python API (async)
│   ├── cli.py             # CLI with Rich
│   ├── web_ui/            # (Removed) Streamlit web app
│   └── examples/          # Example scripts
│       ├── basic_query.py
│       ├── batch_queries.py
│       ├── schedule_reports.py
│       ├── export_data.py
│       └── advanced_usage.py
├── shared/                # Shared config
│   └── config.py
├── migrations/            # Alembic migrations
├── CLIENT_GUIDE.md        # Comprehensive client docs
├── pyproject.toml         # Project dependencies
└── .env                   # Environment variables
```

## Quick Start

### 1. Prerequisites

- Python 3.12+
- PostgreSQL 14+
- Redis 6+
- Groq API key (get from https://console.groq.com)

### 2. Installation

```bash
# Clone repository
git clone https://github.com/Michdriod/mcp-server-client.git
cd mcp-server-client

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .
```

### 3. Configuration

```bash
# Create .env file with your settings
cat > .env << EOF
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database
DB_USER=your_user
DB_PASSWORD=your_password

REDIS_HOST=localhost
REDIS_PORT=6379

GROQ_API_KEY=your_groq_api_key_here

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
EOF
```

### 4. Database Setup

```bash
# Run the provided SQL script in pgAdmin or psql
# Creates 11 tables with sample data
```

### 5. Run the Application

The application consists of three main components that need to be started separately:

#### **Step 1: Start Redis Server**

Open a new terminal and run:

```bash
redis-server
```

**What it does:** Enables query result caching for faster performance. If Redis is not running, the application will still work but without caching.

---

#### **Step 2: Start API Server**

Open a new terminal and run:

**Option A: Using the startup script (recommended)**

```bash
cd /Users/mac/Desktop/mcp-server-client
chmod +x start_api.sh
./start_api.sh
```

**Option B: Manual start**

```bash
cd /Users/mac/Desktop/mcp-server-client
source .venv/bin/activate
export GROQ_API_KEY=your_groq_api_key_here
python server/api_server.py
```

**What it does:** 
- Starts the FastAPI REST server on port 8000
- Loads environment variables from `.env` file
- Spawns the MCP server as a subprocess
- Connects to PostgreSQL and Redis

You should see:
```
🚀 Starting MCP client connection...
✅ MCP client connected and ready
✅ Redis cache initialized successfully
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

#### **Step 3: Start Frontend**

Open a new terminal and run:

```bash
cd /Users/mac/Desktop/mcp-server-client/frontend
npm run dev
```

**What it does:** Starts the React + Vite frontend on port 8081 (or 5173 depending on configuration)

You should see:
```
VITE v5.4.21  ready in XXX ms
➜  Local:   http://localhost:8081/
```

---

#### **Step 4: Access the Application**

Open your browser and navigate to:
- **Frontend:** `http://localhost:8081`
- **API Docs:** `http://localhost:8000/docs` (Swagger UI)

---

#### **Optional: Start Celery (for scheduled reports)**

If you want to use scheduled reports, open two additional terminals:

**Terminal 4: Celery Worker**
```bash
cd /Users/mac/Desktop/mcp-server-client
source .venv/bin/activate
celery -A server.celery_app worker --loglevel=info
```

**Terminal 5: Celery Beat (scheduler)**
```bash
cd /Users/mac/Desktop/mcp-server-client
source .venv/bin/activate
celery -A server.celery_app beat --loglevel=info
```

---

#### **Alternative: CLI and Python API**

Instead of using the web frontend, you can also interact via:

**CLI:**
```bash
python client/cli.py query "Show me the top 5 customers"
python client/cli.py interactive
```

**Python API:**
```bash
python client/examples/basic_query.py
```

## Development Phases

### ✅ Phase 1: Core Infrastructure (Complete)
- Project structure & dependencies
- Database layer (SQLAlchemy async ORM)
- Cache layer (Redis multi-tier)
- Security module (RBAC, query validation)
- 6 database tables created

### ✅ Phase 2: MCP Server (Complete)
- FastMCP server with 11 tools
- SQL generation with Pydantic AI + Groq
- Query execution with timeout & pagination
- Chart generation (matplotlib)
- Query history tracking
- Save/load queries

### ✅ Phase 3: Scheduled Reports (Complete)
- Celery worker + Beat scheduler
- Email delivery with attachments
- Multi-format export (CSV, Excel, PDF, JSON)
- 6 additional MCP tools
- **Total: 17 MCP tools**

### ✅ Phase 4: AI Client & UI (Complete)

- **Python API Client**: Full async API wrapper for all 17 MCP tools
- **Web UI**: Streamlit interface with query, analytics, schedules, saved queries
- **CLI**: Rich-formatted command-line interface with 9 commands
- **Examples**: 5 complete example scripts
- **Documentation**: Comprehensive client guide

### ✅ Phase 5: Scaling & Deployment (Complete)

- **Docker**: Multi-stage builds, docker-compose with 6 services
- **Load Balancing**: NGINX configuration with rate limiting
- **Monitoring**: Health checks, structured logging, Prometheus metrics
- **Production Ready**: Health checks, auto-restart, resource limits

### ✅ Phase 6: Testing & Documentation (Complete)

- **Unit Tests**: Models, cache, validators (pytest + pytest-asyncio)
- **Integration Tests**: MCP client/server communication tests
- **API Documentation**: Complete reference for all 17 tools
- **Deployment Guide**: Comprehensive production deployment docs

## Client Interfaces

<!-- Web UI (Streamlit) section removed: project now uses external frontend -->

### 2. CLI (Rich)

Command-line interface for power users and automation.

```bash
# Query database
python client/cli.py query "Show top 5 customers"

# Interactive mode
python client/cli.py interactive

# Export data
python client/cli.py export "Show all customers" --format excel

# Manage schedules
python client/cli.py schedule list
python client/cli.py schedule create --name "Daily Report" --query "..." --cron "0 9 * * *" --email user@example.com

# View history
python client/cli.py history --days 30

# Get statistics
python client/cli.py stats
```

### 3. Python API

Programmatic access for custom applications.

```python
import asyncio
from client.mcp_client import QueryAssistantClient

async def main():
    async with QueryAssistantClient() as client:
        # Execute query
        result = await client.query_database(
            "Show me the top 5 customers by order value",
            user_id=1
        )
        
        # Export data
        export = await client.export_query_results(
            user_id=1,
            query="Show all customers",
            format="excel"
        )
        
        # Create schedule
        schedule = await client.create_scheduled_report(
            user_id=1,
            name="Daily Report",
            query="Show today's sales",
            schedule="0 9 * * *",
            email="user@example.com",
            format="excel"
        )

asyncio.run(main())
```

**See:** `CLIENT_GUIDE.md` for complete API documentation

## Examples

Located in `client/examples/`:

- `basic_query.py` - Simple query execution
- `batch_queries.py` - Multiple queries efficiently  
- `schedule_reports.py` - Create and manage schedules
- `export_data.py` - Export in multiple formats
- `advanced_usage.py` - Complete workflow examples

```bash
python client/examples/basic_query.py
```

## Configuration Options

### Database
- `DATABASE_URL`: PostgreSQL connection string
- `DATABASE_POOL_SIZE`: Connection pool size (default: 20)
- `DATABASE_MAX_OVERFLOW`: Max overflow connections (default: 40)

### Redis
- `REDIS_URL`: Redis connection string
- `QUERY_CACHE_TTL_SECONDS`: Query cache TTL (default: 300)

### Groq
- `GROQ_API_KEY`: Groq API key for LLM inference
- Recommended model: `llama-3.3-70b-versatile` (complex queries)
- Alternative: `llama-3.1-8b-instant` (simple queries, faster)

### Security
- `QUERY_TIMEOUT_SECONDS`: Query execution timeout (default: 30)
- `MAX_QUERY_RESULTS`: Maximum rows returned (default: 1000)
- `RATE_LIMIT_PER_USER_PER_HOUR`: Requests per user (default: 100)

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests (coming soon)
pytest

# Format code
black .

# Lint
ruff check .
```

## License

MIT License - see [LICENSE](LICENSE)

## Contributing

Contributions welcome! Please read our contributing guidelines first.

---

Built with ❤️ using [Pydantic AI](https://ai.pydantic.dev/), [FastMCP](https://github.com/modelcontextprotocol/python-sdk), and [Groq](https://groq.com/)