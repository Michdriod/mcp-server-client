# Database Query Assistant - Client Guide

Complete guide for using the Database Query Assistant clients (Python API, Web UI, and CLI).

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Python API](#python-api)
5. [Web UI](#web-ui)
6. [CLI](#cli)
7. [Examples](#examples)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## Overview

The Database Query Assistant provides three client interfaces:

- **Python API** - Programmatic access via `QueryAssistantClient` class
- **Web UI** - Interactive Streamlit web application
- **CLI** - Command-line interface with Rich formatting

All clients communicate with the MCP server using the Model Context Protocol.

### Features

✅ Natural language database queries  
✅ SQL generation with Pydantic AI + Groq  
✅ Result caching (5 min query, 1 hr schema, 15 min permissions)  
✅ Data visualization (line, bar, pie charts)  
✅ Multi-format export (CSV, Excel, PDF, JSON)  
✅ Saved queries  
✅ Scheduled reports with email delivery  
✅ Query history and analytics  
✅ RBAC security  

---

## Installation

### Prerequisites

- Python 3.12+
- PostgreSQL database
- Redis server
- Groq API key

### Install Dependencies

```bash
# Clone repository
cd mcp-server-client

# Install project
pip install -e .

# Or install specific client dependencies
pip install mcp
pip install streamlit pandas  # For Web UI
pip install typer rich  # For CLI
```

### Verify Installation

```bash
# Check Python version
python --version  # Should be 3.12+

# Check packages
pip list | grep mcp
pip list | grep streamlit
pip list | grep typer
```

---

## Configuration

### Environment Variables

Create `.env` file in project root:

```bash
# Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database
DB_USER=your_user
DB_PASSWORD=your_password

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=  # Optional

# Groq AI Configuration
GROQ_API_KEY=your_groq_api_key_here

# Email Configuration (for scheduled reports)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=noreply@yourcompany.com
SMTP_FROM_NAME=Database Query Assistant
```

### Get Groq API Key

1. Visit [https://console.groq.com](https://console.groq.com)
2. Sign up or log in
3. Go to API Keys
4. Create new key
5. Copy to `.env` file

### Database Setup

Run the SQL script to create tables and sample data:

```sql
-- Already provided in Phase 1
-- See server/migrations/ for schema
```

### Start Services

```bash
# 1. Start PostgreSQL (if not running)
brew services start postgresql  # macOS
# or
sudo service postgresql start  # Linux

# 2. Start Redis (if not running)
brew services start redis  # macOS
# or
sudo service redis-server start  # Linux

# 3. Start MCP Server
python server/mcp_server.py

# 4. Start Celery Worker (for scheduled reports)
celery -A server.celery_app worker --loglevel=info

# 5. Start Celery Beat (for scheduling)
celery -A server.celery_app beat --loglevel=info
```

---

## Python API

### Quick Start

```python
import asyncio
from client.mcp_client import QueryAssistantClient

async def main():
    async with QueryAssistantClient() as client:
        result = await client.query_database(
            "Show me the top 5 customers by order value",
            user_id=1
        )
        print(result)

asyncio.run(main())
```

### API Reference

#### Connection Management

```python
# Context manager (recommended)
async with QueryAssistantClient() as client:
    # Client is connected
    result = await client.query_database("...", user_id=1)
# Client is automatically disconnected

# Manual connection
client = QueryAssistantClient()
await client.connect()
# ... use client ...
await client.disconnect()
```

#### Query Execution

```python
# Basic query
result = await client.query_database(
    query="Show top 10 products by sales",
    user_id=1
)

# Returns:
# {
#     'results': [...],  # List of dicts
#     'row_count': 10,
#     'column_count': 5,
#     'execution_time_ms': 123.45,
#     'cached': False,
#     'sql_query': 'SELECT ...'
# }
```

#### Schema Information

```python
# Get all tables
tables = await client.list_tables()
# Returns: ['customers', 'products', 'orders', ...]

# Get detailed schema
schema = await client.get_schema_info()
# Returns: [
#     {
#         'table_name': 'customers',
#         'columns': [...],
#         'sample_query': 'SELECT ...'
#     },
#     ...
# ]
```

#### Saved Queries

```python
# Save a query
result = await client.save_query(
    user_id=1,
    name="Top Customers",
    description="Shows top 10 customers by revenue",
    query="Show me the top 10 customers by total order value"
)
# Returns: {'query_id': 123, ...}

# List saved queries
queries = await client.list_saved_queries(user_id=1)
# Returns: [{'id': 123, 'name': '...', 'query': '...', ...}, ...]

# Load and execute saved query
query_data = await client.load_saved_query(user_id=1, query_id=123)
result = await client.query_database(query_data['natural_query'], user_id=1)
```

#### Visualizations

```python
# Generate chart
chart = await client.generate_chart(
    user_id=1,
    query="Show monthly sales trends",
    chart_type="line"  # Options: line, bar, pie
)
# Returns: {'chart_path': '/path/to/chart.png', ...}

# Create table image
image = await client.create_table_image(
    user_id=1,
    query="Show all products"
)
# Returns: {'image_path': '/path/to/table.png', ...}
```

#### Export Data

```python
# Export query results
export = await client.export_query_results(
    user_id=1,
    query="Show all customers",
    format="excel"  # Options: csv, excel, pdf, json
)
# Returns: {'file_path': '/path/to/export.xlsx', ...}
```

#### Analytics

```python
# Get query history
history = await client.get_query_history(
    user_id=1,
    days=30  # Last 30 days
)
# Returns: [{'executed_at': '...', 'natural_query': '...', ...}, ...]

# Get popular queries
popular = await client.get_popular_queries(
    user_id=1,
    days=30,
    limit=10
)
# Returns: [{'natural_query': '...', 'execution_count': 5, ...}, ...]

# Get user statistics
stats = await client.get_user_statistics(user_id=1)
# Returns: {
#     'total_queries': 100,
#     'saved_queries': 10,
#     'active_schedules': 3,
#     'avg_response_time': 150.5,
#     'cache_hit_rate': 35.2
# }
```

#### Scheduled Reports

```python
# Create schedule
schedule = await client.create_scheduled_report(
    user_id=1,
    name="Daily Sales Report",
    query="Show today's sales summary",
    schedule="0 9 * * *",  # Cron expression: daily at 9 AM
    email="user@example.com",
    format="excel"
)
# Returns: {'schedule_id': 456, ...}

# List schedules
schedules = await client.list_scheduled_reports(user_id=1)
# Returns: [{'id': 456, 'name': '...', 'is_active': True, ...}, ...]

# Update schedule
await client.update_scheduled_report(
    user_id=1,
    schedule_id=456,
    name="Updated Name",  # Optional
    schedule="0 10 * * *",  # Optional
    is_active=False  # Optional
)

# Delete schedule
await client.delete_scheduled_report(user_id=1, schedule_id=456)

# Trigger immediately
await client.trigger_report_now(user_id=1, schedule_id=456)
```

### Convenience Functions

```python
from client.mcp_client import quick_query

# One-liner for quick queries
result = quick_query("Show top 5 products", user_id=1)
print(result)
```

---

## Web UI

### Starting the Web UI

```bash
# From project root
streamlit run client/web_ui/app.py

# Or from web_ui directory
cd client/web_ui
streamlit run app.py
```

Access at: `http://localhost:8501`

### Features

#### 🏠 Query Page

- **Query Input**: Type natural language questions
- **Execute Button**: Run queries with one click
- **Results Table**: Sortable, filterable data table
- **Metadata**: Rows, columns, execution time, cache status
- **Charts**: Generate line, bar, or pie charts
- **Export**: Download as CSV or Excel
- **Save Query**: Store for later use

**Example queries:**
```
Show me the top 5 customers by total order value
What were the total sales by product category last month?
List all orders from customers in California
Show revenue trends by week
```

#### 📊 Analytics Page

- **Statistics**: Total queries, avg response time, cache hit rate
- **Query History**: Browse past queries with timestamps
- **Timeline Chart**: Visualize query frequency over time
- **Time Range**: Adjust with slider (1-90 days)

#### 📅 Schedules Page

- **Create Schedule**: Form with name, query, cron, email, format
- **Schedule List**: View all scheduled reports
- **Status Toggle**: Pause/resume schedules
- **Run Now**: Trigger report immediately
- **Delete**: Remove schedules

**Cron expressions:**
```
0 9 * * *     - Daily at 9 AM
0 9 * * 1     - Every Monday at 9 AM
0 */4 * * *   - Every 4 hours
0 0 1 * *     - First day of each month
30 8 * * 1-5  - Weekdays at 8:30 AM
```

#### 💾 Saved Queries Page

- **Query List**: All saved queries with descriptions
- **Execute**: Run saved query with one click
- **Details**: View query text and metadata

#### ℹ️ Schema Page

- **Table List**: All available tables
- **Column Details**: Name, type, nullable status
- **Sample Queries**: Pre-made SQL examples

### Tips

- Use **Ctrl+Enter** to submit queries quickly
- Results are **cached for 5 minutes** for performance
- **Charts work best** with numeric and date columns
- **Export** preserves all rows (no limit)
- **Test queries** before scheduling them

---

## CLI

### Installation

```bash
pip install typer rich
```

### Commands

#### query - Execute Query

```bash
# Basic query
dbquery query "Show me the top 5 customers by order value"

# With user ID
dbquery query "What were last month's sales?" --user 2

# Output as JSON
dbquery query "List all products" --output json

# Output as CSV
dbquery query "Show customers" --output csv

# Save to file
dbquery query "Show all orders" --save

# Generate chart
dbquery query "Show revenue trends" --chart line
```

**Options:**
- `--user, -u`: User ID (1=admin, 2=sales, 3=finance)
- `--output, -o`: Output format (table, json, csv)
- `--save, -s`: Save results to file
- `--chart, -c`: Generate chart (line, bar, pie)

#### saved - Manage Saved Queries

```bash
# List saved queries
dbquery saved list

# Execute saved query
dbquery saved execute --id 5

# With different user
dbquery saved list --user 2
```

#### schedule - Manage Scheduled Reports

```bash
# List schedules
dbquery schedule list

# Create schedule
dbquery schedule create \
  --name "Daily Sales" \
  --query "Show today's sales" \
  --cron "0 9 * * *" \
  --email user@example.com \
  --format excel

# Trigger report now
dbquery schedule trigger --id 5

# Delete schedule
dbquery schedule delete --id 5
```

#### export - Export Results

```bash
# Export as CSV
dbquery export "Show all customers" --format csv

# Export as Excel
dbquery export "Last month's sales" --format excel

# Export with custom filename
dbquery export "Show orders" --format pdf --output report.pdf
```

**Formats:**
- `csv` - Comma-separated values
- `excel` - Excel workbook (.xlsx)
- `pdf` - PDF document
- `json` - JSON file

#### schema - View Schema

```bash
# Show all tables
dbquery schema

# Show specific table
dbquery schema --table customers
```

#### history - Query History

```bash
# Show last 7 days
dbquery history

# Show last 30 days, limit 50 results
dbquery history --days 30 --limit 50

# Different user
dbquery history --user 2
```

#### stats - User Statistics

```bash
# Show statistics
dbquery stats

# For different user
dbquery stats --user 2
```

#### interactive - Interactive Mode

```bash
# Start interactive mode
dbquery interactive

# Then enter queries one by one
Query> Show me the top 10 products
Query> What were sales last week?
Query> exit
```

### CLI Tips

- Use **tab completion** for commands (if enabled)
- Output is **formatted with colors** using Rich
- Large tables are **limited to 50 rows** for readability
- Use `--help` on any command for details

---

## Examples

See `client/examples/` directory for complete examples:

### 1. basic_query.py

```python
async with QueryAssistantClient() as client:
    result = await client.query_database(
        "Show me the top 5 customers by total order value",
        user_id=1
    )
    print(result)
```

### 2. batch_queries.py

```python
queries = [
    "Show me the top 5 customers by order count",
    "What are the most popular products?",
    "Show total sales by month for this year"
]

async with QueryAssistantClient() as client:
    for query in queries:
        result = await client.query_database(query, user_id=1)
        print(f"{query}: {result['row_count']} rows")
```

### 3. schedule_reports.py

```python
async with QueryAssistantClient() as client:
    await client.create_scheduled_report(
        user_id=1,
        name="Daily Sales Report",
        query="Show today's sales",
        schedule="0 9 * * *",
        email="sales@example.com",
        format="excel"
    )
```

### 4. export_data.py

```python
async with QueryAssistantClient() as client:
    result = await client.export_query_results(
        user_id=1,
        query="Show all customers",
        format="excel"
    )
    print(f"Exported to: {result['file_path']}")
```

### 5. advanced_usage.py

```python
async with QueryAssistantClient() as client:
    # Save query
    await client.save_query(user_id=1, name="Top Customers", ...)
    
    # Get history
    history = await client.get_query_history(user_id=1, days=30)
    
    # Get statistics
    stats = await client.get_user_statistics(user_id=1)
```

Run examples:

```bash
python client/examples/basic_query.py
python client/examples/batch_queries.py
python client/examples/schedule_reports.py
python client/examples/export_data.py
python client/examples/advanced_usage.py
```

---

## Best Practices

### General

1. **Use context managers** - Always use `async with` for automatic cleanup
2. **Handle errors** - Wrap operations in try-except blocks
3. **Check results** - Verify 'results' key exists before processing
4. **Test queries** - Test queries before scheduling or saving
5. **Cache awareness** - Repeated queries are cached for 5 minutes

### Python API

```python
# ✅ Good - Context manager
async with QueryAssistantClient() as client:
    result = await client.query_database(query, user_id)

# ❌ Bad - Manual management (error-prone)
client = QueryAssistantClient()
await client.connect()
result = await client.query_database(query, user_id)
# Forgot to disconnect!
```

### Performance

```python
# ✅ Good - Reuse connection
async with QueryAssistantClient() as client:
    for query in queries:
        result = await client.query_database(query, user_id)

# ❌ Bad - New connection each time
for query in queries:
    async with QueryAssistantClient() as client:
        result = await client.query_database(query, user_id)
```

### Error Handling

```python
# ✅ Good - Graceful error handling
try:
    result = await client.query_database(query, user_id)
    if result and 'results' in result:
        process_results(result['results'])
    else:
        logger.warning("No results returned")
except Exception as e:
    logger.error(f"Query failed: {e}")
```

### Scheduling

```python
# ✅ Good - Test before scheduling
result = await client.query_database(query, user_id)
if result and 'results' in result:
    # Query works, schedule it
    await client.create_scheduled_report(...)

# ❌ Bad - Schedule untested query
await client.create_scheduled_report(...)  # Might fail repeatedly
```

---

## Troubleshooting

### Connection Issues

**Problem:** `Cannot connect to MCP server`

**Solutions:**
1. Verify MCP server is running: `python server/mcp_server.py`
2. Check `.env` configuration
3. Verify database connection
4. Check Redis connection
5. Review server logs for errors

### Query Failures

**Problem:** `No results returned`

**Solutions:**
1. Test query in simpler form
2. Check user permissions in database
3. Verify table/column names exist
4. Review generated SQL in logs
5. Check for SQL injection blocks

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'mcp'`

**Solutions:**
```bash
# Install project in development mode
pip install -e .

# Or install specific package
pip install mcp
```

### Web UI Issues

**Problem:** `Streamlit not found`

**Solution:**
```bash
pip install streamlit pandas
```

**Problem:** `Port 8501 already in use`

**Solution:**
```bash
streamlit run client/web_ui/app.py --server.port 8502
```

### CLI Issues

**Problem:** `Command not found: dbquery`

**Solutions:**
```bash
# Run directly
python client/cli.py query "..."

# Or create alias
alias dbquery="python $(pwd)/client/cli.py"
```

### Celery Issues

**Problem:** `Scheduled reports not sending`

**Solutions:**
1. Verify Celery worker is running
2. Verify Celery beat is running
3. Check Redis connection
4. Check SMTP settings in `.env`
5. Review Celery logs

### Export Issues

**Problem:** `Export failed`

**Solutions:**
1. Check disk space
2. Verify output directory exists
3. Check file permissions
4. Try different format
5. Check query returns data

### Performance Issues

**Problem:** `Queries are slow`

**Solutions:**
1. Check cache hit rate (should be > 30%)
2. Add database indexes
3. Optimize queries
4. Check database connection pool
5. Monitor Redis memory

---

## FAQ

### General

**Q: Which client should I use?**  
A: 
- **Web UI** - Best for non-technical users, exploration, visualization
- **CLI** - Best for power users, automation, scripts
- **Python API** - Best for integration, custom applications

**Q: Can I use multiple clients simultaneously?**  
A: Yes, all clients connect to the same MCP server.

**Q: Do I need all three clients?**  
A: No, use what you need. Web UI is most user-friendly.

### Security

**Q: Is my data secure?**  
A: Yes. The system includes:
- RBAC (Role-Based Access Control)
- SQL injection prevention
- Query validation
- Row-level security
- Permission caching

**Q: Can users see each other's data?**  
A: Only if database permissions allow it. RBAC is enforced.

### Performance

**Q: How fast are queries?**  
A: 
- First execution: 100-500ms (depends on query)
- Cached execution: <50ms
- Cache duration: 5 minutes

**Q: What's cached?**  
A:
- Query results: 5 minutes
- Schema info: 1 hour
- Permissions: 15 minutes

### Scheduling

**Q: What email providers work?**  
A: Any SMTP provider (Gmail, Outlook, SendGrid, etc.)

**Q: Can I schedule multiple reports?**  
A: Yes, unlimited schedules per user.

**Q: What formats can I schedule?**  
A: CSV, Excel, PDF, JSON

### Development

**Q: Can I customize the clients?**  
A: Yes, all code is open and modifiable.

**Q: Can I add new features?**  
A: Yes, see examples for patterns.

**Q: How do I contribute?**  
A: Fork the repository and submit pull requests.

---

## Support

### Resources

- **Examples**: `client/examples/`
- **API Reference**: `client/mcp_client.py`
- **Web UI Guide**: `client/web_ui/README.md`
- **Server Docs**: `server/README.md`

### Getting Help

1. Check this guide
2. Review examples
3. Check troubleshooting section
4. Review server logs
5. Test with simple queries first

### Common Workflows

**Workflow 1: Ad-hoc Analysis**
1. Open Web UI
2. Enter query
3. View results
4. Export if needed

**Workflow 2: Automated Reporting**
1. Test query in Web UI
2. Save query
3. Create schedule
4. Verify email delivery

**Workflow 3: Integration**
1. Read Python API docs
2. Copy example code
3. Modify for your needs
4. Test thoroughly
5. Deploy

---

## Next Steps

1. **Try the Web UI** - Most user-friendly: `streamlit run client/web_ui/app.py`
2. **Run examples** - Learn patterns: `python client/examples/basic_query.py`
3. **Explore CLI** - Power user features: `python client/cli.py --help`
4. **Build integration** - Use Python API in your app
5. **Customize** - Modify code for your needs

---

## Version History

- **v1.0.0** (Phase 4) - Initial client release
  - Python API client
  - Streamlit Web UI
  - CLI with Rich formatting
  - Example scripts
  - Comprehensive documentation

---

**Built with:** Python 3.12+, MCP, Pydantic AI, Groq, PostgreSQL, Redis, FastMCP, Celery, Streamlit, Typer, Rich

**License:** MIT
