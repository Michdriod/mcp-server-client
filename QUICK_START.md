# Quick Start Guide

## Prerequisites ✅

All services are running:
- ✅ PostgreSQL (database: Mcp)
- ✅ Redis (localhost:6379)
- ✅ Python 3.12+ with dependencies installed
- ✅ Environment variables configured in `.env`

## Running the Application

### Option 1: Automated Startup Script (Recommended)

```bash
./run_app.sh
```

This script will:
1. Check all prerequisites
2. Verify database and Redis connections
3. Let you choose how to run the app:
   - Test MCP Server
   - Start Web UI
   - Start CLI
   - Run examples
   - Start Celery worker

### Option 2: Manual Steps

#### A. Test End-to-End (Verify Everything Works)

```bash
python test_e2e.py
```

**Expected output:**
```
🚀 Starting End-to-End Test Suite
🧪 Test 1: Connection
✅ Connected! Found 17 tools
🧪 Test 2: Testing database query with natural language...
✅ Query executed!
🧪 Test 3: Getting schema information...
✅ Schema retrieved!
✅ All tests passed!
```

#### B. Start Web UI (Best for Non-Technical Users)

```bash
Legacy Streamlit UI has been removed. Use your preferred frontend.
```

Access at: **http://localhost:8501**

**Features:**
- Natural language query input
- Interactive data tables
- Chart generation
- Export to CSV/Excel/PDF
- Schedule management
- Query history

#### C. Start CLI (Best for Power Users)

```bash
# Interactive mode
python client/cli.py interactive

# Direct query
python client/cli.py query "Show me top 5 customers"

# Export data
python client/cli.py export "Show all customers" --format excel

# View history
python client/cli.py history --days 7

# Manage schedules
python client/cli.py schedule list
```

#### D. Run Example Scripts

```bash
# Simple query example
python client/examples/basic_query.py

# Batch queries
python client/examples/batch_queries.py

# Schedule reports
python client/examples/schedule_reports.py

# Export data
python client/examples/export_data.py

# Advanced usage
python client/examples/advanced_usage.py
```

#### E. Start Celery Workers (For Scheduled Reports)

**Terminal 1 - Worker:**
```bash
celery -A server.celery_app worker --loglevel=info
```

**Terminal 2 - Beat Scheduler:**
```bash
celery -A server.celery_app beat --loglevel=info
```

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                    User Interfaces                       │
├─────────────┬─────────────────┬─────────────────────────┤
│   Web UI    │       CLI       │      Python API         │
│ (Frontend)  │     (Rich)      │   (async/await)         │
└──────┬──────┴────────┬────────┴──────────┬──────────────┘
       │               │                    │
       └───────────────┴────────────────────┘
                       │
              ┌────────▼────────┐
              │   MCP Server    │
              │   (FastMCP)     │
              │   17 Tools      │
              └────────┬────────┘
                       │
       ┌───────────────┼───────────────┐
       │               │               │
   ┌───▼───┐    ┌──────▼──────┐  ┌────▼────┐
   │ Groq  │    │ PostgreSQL  │  │  Redis  │
   │  AI   │    │  Database   │  │  Cache  │
   └───────┘    └─────────────┘  └─────────┘
```

## MCP Server Tools (17 Available)

1. **query_database** - Natural language to SQL query
2. **execute_sql** - Direct SQL execution
3. **get_schema_info** - Database schema details
4. **list_tables** - Show all tables
5. **save_query** - Save query for reuse
6. **get_saved_queries** - List saved queries
7. **load_query** - Load saved query
8. **get_query_history** - View query history
9. **get_query_stats** - Query analytics
10. **export_query_to_csv** - Export as CSV
11. **export_query_to_excel** - Export as Excel
12. **export_query_to_pdf** - Export as PDF
13. **export_query_to_json** - Export as JSON
14. **generate_chart** - Create visualizations
15. **create_scheduled_report** - Schedule reports
16. **list_scheduled_reports** - View schedules
17. **update_scheduled_report** - Modify schedules

## Configuration

### Environment Variables (`.env`)

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost/Mcp

# Redis
REDIS_URL=redis://localhost:6379/0

# LLM (supports multiple providers)
GROQ_API_KEY=your_groq_api_key
LLM_MODEL=groq:llama-3.3-70b-versatile

# To switch providers:
# LLM_MODEL=openai:gpt-4
# LLM_MODEL=anthropic:claude-3-5-sonnet-20241022

# Security
JWT_SECRET_KEY=your_secret_key
QUERY_TIMEOUT_SECONDS=30
MAX_QUERY_RESULTS=1000

# Email (for scheduled reports)
EMAIL_SMTP_HOST=smtp.gmail.com
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
```

## Testing Queries

Try these natural language queries:

### Simple Queries
- "How many customers do we have?"
- "Show me all products"
- "List the first 10 orders"

### Complex Queries
- "What were the top 5 products by revenue last month?"
- "Show me customers who haven't ordered in the last 30 days"
- "Calculate average order value by customer segment"

### Analytical Queries
- "Show monthly sales trend for 2024"
- "Compare revenue by product category"
- "Find top 10 customers by total order value"

## Troubleshooting

### MCP Server won't start
```bash
# Check if GROQ_API_KEY is set
grep GROQ_API_KEY .env

# Check if LLM_MODEL is set
grep LLM_MODEL .env

# Test database connection
psql -U postgres -d Mcp -c "SELECT 1"

# Test Redis connection
redis-cli ping
```

### Database connection error
```bash
# Verify PostgreSQL is running
brew services list | grep postgresql

# Check connection string
echo $DATABASE_URL
```

### Redis connection error
```bash
# Start Redis
brew services start redis

# Or run manually
redis-server
```

### Groq API errors
- Verify API key: https://console.groq.com/keys
- Check rate limits: https://console.groq.com/docs/rate-limits
- Try alternative model: `LLM_MODEL=groq:llama-3.1-8b-instant`

## Performance Tips

1. **Use caching**: Redis caches query results for 5 minutes
2. **Limit results**: Add "LIMIT 100" to large queries
3. **Use saved queries**: Reuse queries to save AI inference time
4. **Schedule heavy reports**: Use Celery for long-running queries

## Next Steps

1. ✅ Test end-to-end: `python test_e2e.py`
2. 🌐 Explore Web UI: Use your external frontend (Streamlit removed)
3. 📖 Read full docs: `CLIENT_GUIDE.md`
4. 🔧 Try examples: `client/examples/*.py`
5. 📅 Set up schedules: Schedule daily/weekly reports

## Support

- **API Documentation**: See `CLIENT_GUIDE.md`
- **Examples**: Check `client/examples/`
- **Issues**: GitHub Issues
- **Logs**: Check terminal output for detailed errors

---

**Ready to start?** Run: `./run_app.sh`
