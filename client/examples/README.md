# Example Scripts

This directory contains example scripts demonstrating how to use the Database Query Assistant client.

## Available Examples

### 1. basic_query.py
**Simple query execution**

Shows how to execute a basic natural language query and display results.

```bash
python basic_query.py
```

Features:
- Connect to MCP server
- Execute query
- Display results with metadata
- Show generated SQL

### 2. batch_queries.py
**Multiple queries efficiently**

Execute multiple queries using a single connection and compare performance.

```bash
python batch_queries.py
```

Features:
- Batch query execution
- Performance tracking
- Cache hit rate analysis
- Summary statistics

### 3. schedule_reports.py
**Automated report scheduling**

Create and manage scheduled reports with email delivery.

```bash
python schedule_reports.py
```

Features:
- Create schedules with cron expressions
- List existing schedules
- Update schedule status (pause/resume)
- Trigger reports immediately
- Delete schedules

### 4. export_data.py
**Export in multiple formats**

Export query results as CSV, Excel, PDF, or JSON files.

```bash
python export_data.py
```

Features:
- Export to CSV, Excel, PDF, JSON
- Generate charts alongside exports
- Bulk export multiple queries
- Custom file naming

### 5. advanced_usage.py
**Complete workflow demonstration**

Shows advanced features like saved queries, history, and analytics.

```bash
python advanced_usage.py
```

Features:
- Save and load queries
- Query history tracking
- User statistics
- Popular queries analysis
- Complete workflow example

## Running Examples

### Prerequisites

1. **Install dependencies:**
```bash
pip install -e ../../
```

2. **Configure environment:**
Create `.env` file in project root with:
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=your_database
DB_USER=your_user
DB_PASSWORD=your_password

REDIS_HOST=localhost
REDIS_PORT=6379

GROQ_API_KEY=your_groq_key

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

3. **Start services:**
```bash
# Start PostgreSQL (if not running)
# Start Redis (if not running)

# Start MCP server
python server/mcp_server.py

# Start Celery worker (for scheduled reports)
celery -A server.celery_app worker --loglevel=info

# Start Celery beat (for scheduling)
celery -A server.celery_app beat --loglevel=info
```

### Running Individual Examples

```bash
# Basic query
python examples/basic_query.py

# Batch queries
python examples/batch_queries.py

# Schedule reports
python examples/schedule_reports.py

# Export data
python examples/export_data.py

# Advanced usage
python examples/advanced_usage.py
```

## Customization

Each example can be customized by editing the script:

### Change User ID
```python
user_id = 1  # 1=admin, 2=sales analyst, 3=finance team
```

### Modify Queries
```python
query = "Your natural language question here"
```

### Adjust Export Format
```python
format = 'excel'  # Options: csv, excel, pdf, json
```

### Change Schedule
```python
schedule = '0 9 * * *'  # Cron expression
```

## Common Patterns

### Pattern 1: Query → Save → Schedule
```python
# 1. Test query
result = await client.query_database(query, user_id)

# 2. Save it
save_result = await client.save_query(user_id, name, description, query)

# 3. Schedule it
schedule_result = await client.create_scheduled_report(
    user_id, name, query, schedule, email, format
)
```

### Pattern 2: Query → Export → Visualize
```python
# 1. Execute query
result = await client.query_database(query, user_id)

# 2. Export data
export_result = await client.export_query_results(user_id, query, 'excel')

# 3. Generate chart
chart_result = await client.generate_chart(user_id, query, 'bar')
```

### Pattern 3: Batch Processing
```python
# Execute multiple queries efficiently
async with QueryAssistantClient() as client:
    for query in queries:
        result = await client.query_database(query, user_id)
        # Process result
```

## Tips

1. **Use context manager**: Always use `async with QueryAssistantClient()` for automatic cleanup
2. **Handle errors**: Wrap operations in try-except blocks
3. **Batch operations**: Reuse connection for multiple queries
4. **Check results**: Verify 'results' key exists before processing
5. **Test queries**: Test queries before scheduling them

## Example Query Ideas

- "Show me the top 10 customers by revenue"
- "What were total sales last month?"
- "List products with low inventory"
- "Show order trends by week"
- "Which customers haven't ordered in 90 days?"
- "What's the average order value by customer segment?"
- "Show monthly revenue by product category"
- "List all pending orders"

## Troubleshooting

**Import errors:**
```bash
# Install project in development mode
pip install -e ../../
```

**Connection errors:**
- Ensure MCP server is running
- Check .env configuration
- Verify database/Redis are accessible

**No results:**
- Check query syntax
- Verify user permissions
- Review server logs

**Export failures:**
- Ensure output directory exists
- Check disk space
- Verify export format is supported

## Next Steps

After running the examples:
1. Try the Web UI: Use your external frontend (Streamlit removed)
2. Try the CLI: `python client/cli.py --help`
3. Build your own integration using the examples as templates
4. Check the main documentation: `CLIENT_GUIDE.md`

## Support

For more information:
- Check `CLIENT_GUIDE.md` for comprehensive documentation
- Review `client/mcp_client.py` for full API reference
- See `server/mcp_server.py` for available MCP tools
