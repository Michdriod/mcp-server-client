# Database Query Assistant - API Reference

Complete API reference for all 17 MCP tools.

## Table of Contents

1. [Overview](#overview)
2. [Core Query Tools](#core-query-tools)
3. [Schema & Metadata Tools](#schema--metadata-tools)
4. [Query Management Tools](#query-management-tools)
5. [Visualization Tools](#visualization-tools)
6. [History & Analytics Tools](#history--analytics-tools)
7. [Export Tools](#export-tools)
8. [Scheduled Reports Tools](#scheduled-reports-tools)
9. [Error Handling](#error-handling)
10. [Rate Limiting](#rate-limiting)

---

## Overview

### Authentication

All tools require a `user_id` parameter for user tracking and permissions.

### Response Format

All tools return a standardized response:

```json
{
  "status": "success|error",
  "data": { ... },
  "error": "error message (if status=error)"
}
```

### Base URL

- **MCP Server**: `http://localhost:3000` (default)
- **Web UI**: `http://localhost:8501` (default)

---

## Core Query Tools

### 1. query_database

Execute natural language database queries.

**Function:**
```python
async def query_database(question: str, user_id: int) -> dict
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| question | str | Yes | Natural language question about the data |
| user_id | int | Yes | User ID executing the query |

**Returns:**
```json
{
  "status": "success",
  "rows": [...],
  "row_count": 125,
  "columns": ["id", "name", "revenue"],
  "execution_time_ms": 45.3,
  "sql": "SELECT ...",
  "cached": false,
  "explanation": "This query retrieves...",
  "confidence": 0.95,
  "question": "What are the top 5 customers?"
}
```

**Examples:**

```python
# Simple aggregation
result = await query_database(
    question="What is the total revenue this month?",
    user_id=1
)
print(f"Revenue: ${result['rows'][0]['total']}")

# Top N query
result = await query_database(
    question="Show me the top 10 customers by revenue",
    user_id=1
)
for row in result['rows']:
    print(f"{row['name']}: ${row['revenue']}")

# Time-based query
result = await query_database(
    question="How many new users registered last week?",
    user_id=1
)
print(f"New users: {result['rows'][0]['count']}")

# Join query
result = await query_database(
    question="List all orders with customer names",
    user_id=1
)
```

**Error Responses:**

```json
{
  "status": "permission_denied",
  "error": "Permission denied: User cannot access table 'salaries'",
  "question": "Show all salaries"
}

{
  "status": "timeout",
  "error": "Query timeout: Exceeded 30 second limit",
  "question": "Complex aggregation query"
}

{
  "status": "failed",
  "error": "SQL syntax error: Invalid column name",
  "question": "Show invalid_column"
}
```

**Security Features:**
- SQL injection protection
- Query complexity analysis
- Execution timeout (30s)
- Forbidden keywords (DROP, DELETE, TRUNCATE, etc.)
- Permission checks per user

**Performance:**
- Results cached for 5 minutes
- Automatic query optimization
- Connection pooling (20-40 connections)
- Parallel execution for independent queries

---

## Schema & Metadata Tools

### 2. get_schema_info

Get detailed schema information for a table.

**Function:**
```python
async def get_schema_info(table_name: str) -> dict
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| table_name | str | Yes | Name of the table to inspect |

**Returns:**
```json
{
  "status": "success",
  "table_name": "users",
  "columns": [
    {
      "name": "id",
      "type": "integer",
      "nullable": false,
      "default": "nextval('users_id_seq')",
      "max_length": null
    },
    {
      "name": "email",
      "type": "character varying",
      "nullable": false,
      "default": null,
      "max_length": 255
    }
  ],
  "primary_keys": ["id"],
  "foreign_keys": [
    {
      "column": "company_id",
      "references_table": "companies",
      "references_column": "id"
    }
  ]
}
```

**Example:**
```python
schema = await get_schema_info("orders")
print(f"Table: {schema['table_name']}")
print(f"Columns: {len(schema['columns'])}")
for col in schema['columns']:
    print(f"  - {col['name']} ({col['type']})")
```

### 3. list_tables

List all tables in the database.

**Function:**
```python
async def list_tables() -> dict
```

**Parameters:** None

**Returns:**
```json
{
  "status": "success",
  "tables": [
    {
      "name": "users",
      "schema": "public",
      "row_count": 1250
    },
    {
      "name": "orders",
      "schema": "public",
      "row_count": 5432
    }
  ],
  "total_tables": 12
}
```

**Example:**
```python
tables = await list_tables()
print(f"Database has {tables['total_tables']} tables:")
for table in tables['tables']:
    print(f"  {table['name']}: {table['row_count']} rows")
```

---

## Query Management Tools

### 4. save_query

Save a query for reuse.

**Function:**
```python
async def save_query(
    name: str,
    description: str,
    question: str,
    sql: str,
    user_id: int
) -> dict
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| name | str | Yes | Name for the saved query |
| description | str | Yes | Description of the query |
| question | str | Yes | Natural language question |
| sql | str | Yes | SQL query to save |
| user_id | int | Yes | User ID |

**Returns:**
```json
{
  "status": "success",
  "query_id": 42,
  "name": "Monthly Revenue"
}
```

**Example:**
```python
result = await save_query(
    name="Top Customers",
    description="Shows top 10 customers by total revenue",
    question="Who are our top customers?",
    sql="SELECT customer_id, SUM(amount) as revenue FROM orders GROUP BY customer_id ORDER BY revenue DESC LIMIT 10",
    user_id=1
)
print(f"Saved as query #{result['query_id']}")
```

### 5. load_saved_query

Load a previously saved query.

**Function:**
```python
async def load_saved_query(query_id: int, user_id: int) -> dict
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| query_id | int | Yes | ID of saved query |
| user_id | int | Yes | User ID |

**Returns:**
```json
{
  "status": "success",
  "query_id": 42,
  "name": "Monthly Revenue",
  "description": "Calculate monthly revenue",
  "question": "What is the revenue this month?",
  "sql": "SELECT ...",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Example:**
```python
query = await load_saved_query(query_id=42, user_id=1)
print(f"Loaded: {query['name']}")

# Execute the loaded query
result = await query_database(query['question'], user_id=1)
```

### 6. list_saved_queries

List all saved queries for a user.

**Function:**
```python
async def list_saved_queries(user_id: int, limit: int = 20) -> dict
```

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| user_id | int | Yes | - | User ID |
| limit | int | No | 20 | Maximum queries to return |

**Returns:**
```json
{
  "status": "success",
  "queries": [
    {
      "id": 42,
      "name": "Monthly Revenue",
      "description": "Calculate monthly revenue",
      "question": "What is the revenue?",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 15
}
```

**Example:**
```python
saved = await list_saved_queries(user_id=1, limit=10)
for query in saved['queries']:
    print(f"{query['id']}: {query['name']}")
```

---

## Visualization Tools

### 7. generate_chart

Generate charts from query results.

**Function:**
```python
async def generate_chart(
    data: list[dict],
    chart_type: str | None = None,
    title: str | None = None,
    x_column: str | None = None,
    y_column: str | None = None
) -> dict
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| data | list[dict] | Yes | Query results to visualize |
| chart_type | str | No | Chart type: bar, line, pie, scatter (auto-detect) |
| title | str | No | Chart title (auto-generated) |
| x_column | str | No | X-axis column (auto-detect) |
| y_column | str | No | Y-axis column (auto-detect) |

**Returns:**
```json
{
  "status": "success",
  "filepath": "/exports/chart_20240115_103045.png",
  "chart_type": "bar"
}
```

**Examples:**

```python
# Auto-detect chart type
result = await query_database("Show revenue by month", user_id=1)
chart = await generate_chart(data=result['rows'])

# Bar chart
chart = await generate_chart(
    data=result['rows'],
    chart_type='bar',
    title='Monthly Revenue',
    x_column='month',
    y_column='revenue'
)

# Line chart (time series)
chart = await generate_chart(
    data=result['rows'],
    chart_type='line',
    title='User Growth Over Time'
)

# Pie chart
chart = await generate_chart(
    data=result['rows'],
    chart_type='pie',
    title='Revenue by Category'
)
```

**Supported Chart Types:**
- **bar**: Bar charts for categorical comparisons
- **line**: Line charts for time series
- **pie**: Pie charts for proportions
- **scatter**: Scatter plots for correlations

### 8. create_table_image

Create formatted table images.

**Function:**
```python
async def create_table_image(
    data: list[dict],
    title: str | None = None,
    max_rows: int = 20
) -> dict
```

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| data | list[dict] | Yes | - | Query results |
| title | str | No | None | Table title |
| max_rows | int | No | 20 | Maximum rows to display |

**Returns:**
```json
{
  "status": "success",
  "filepath": "/exports/table_20240115_103045.png",
  "rows_displayed": 20,
  "total_rows": 150
}
```

**Example:**
```python
result = await query_database("Show top customers", user_id=1)
table = await create_table_image(
    data=result['rows'],
    title='Top 10 Customers by Revenue',
    max_rows=10
)
```

---

## History & Analytics Tools

### 9. get_query_history

Get recent query history.

**Function:**
```python
async def get_query_history(
    user_id: int,
    limit: int = 20,
    status: str | None = None
) -> dict
```

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| user_id | int | Yes | - | User ID |
| limit | int | No | 20 | Maximum queries |
| status | str | No | None | Filter: 'success', 'failed', or None |

**Returns:**
```json
{
  "status": "success",
  "queries": [
    {
      "id": 123,
      "question": "Show top customers",
      "sql": "SELECT ...",
      "status": "success",
      "execution_time_ms": 45.3,
      "row_count": 10,
      "executed_at": "2024-01-15T10:30:00Z"
    }
  ],
  "total": 20
}
```

**Example:**
```python
# All queries
history = await get_query_history(user_id=1, limit=50)

# Only successful queries
history = await get_query_history(user_id=1, status='success')

# Only failed queries
history = await get_query_history(user_id=1, status='failed')
```

### 10. get_popular_queries

Get most frequently executed queries.

**Function:**
```python
async def get_popular_queries(limit: int = 10, days: int = 30) -> dict
```

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| limit | int | No | 10 | Maximum queries |
| days | int | No | 30 | Look back period |

**Returns:**
```json
{
  "status": "success",
  "queries": [
    {
      "question": "Show revenue by month",
      "execution_count": 45,
      "avg_execution_time_ms": 38.2,
      "last_executed_at": "2024-01-15T10:30:00Z"
    }
  ],
  "period_days": 30
}
```

**Example:**
```python
popular = await get_popular_queries(limit=5, days=7)
for query in popular['queries']:
    print(f"{query['question']}: {query['execution_count']} executions")
```

### 11. get_user_statistics

Get user query statistics.

**Function:**
```python
async def get_user_statistics(user_id: int, days: int = 30) -> dict
```

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| user_id | int | Yes | - | User ID |
| days | int | No | 30 | Look back period |

**Returns:**
```json
{
  "status": "success",
  "total_queries": 150,
  "successful_queries": 142,
  "failed_queries": 8,
  "success_rate": 94.67,
  "avg_execution_time_ms": 42.5,
  "total_rows_returned": 12500,
  "most_used_tables": ["orders", "customers", "products"]
}
```

**Example:**
```python
stats = await get_user_statistics(user_id=1, days=7)
print(f"Success rate: {stats['success_rate']}%")
print(f"Avg execution: {stats['avg_execution_time_ms']}ms")
```

---

## Export Tools

### 12. export_query_results

Export results to various formats.

**Function:**
```python
async def export_query_results(
    data: list[dict],
    format: str = "csv",
    filename: str | None = None,
    title: str | None = None
) -> dict
```

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| data | list[dict] | Yes | - | Query results |
| format | str | No | csv | Format: csv, excel, pdf, json |
| filename | str | No | None | Filename (auto-generated) |
| title | str | No | None | Title for Excel/PDF |

**Returns:**
```json
{
  "status": "success",
  "filepath": "/exports/results_20240115_103045.xlsx",
  "format": "excel",
  "row_count": 150
}
```

**Examples:**

```python
result = await query_database("Show all customers", user_id=1)

# CSV export
csv = await export_query_results(
    data=result['rows'],
    format='csv',
    filename='customers'
)

# Excel export
excel = await export_query_results(
    data=result['rows'],
    format='excel',
    filename='customers',
    title='Customer List'
)

# PDF export
pdf = await export_query_results(
    data=result['rows'],
    format='pdf',
    title='Monthly Sales Report'
)

# JSON export
json = await export_query_results(
    data=result['rows'],
    format='json'
)
```

**Supported Formats:**
- **csv**: Comma-separated values (UTF-8)
- **excel**: Excel workbook (.xlsx) with formatting
- **pdf**: PDF document with table formatting
- **json**: JSON array with pretty printing

---

## Scheduled Reports Tools

### 13. create_scheduled_report

Create automated report schedules.

**Function:**
```python
async def create_scheduled_report(
    name: str,
    description: str,
    saved_query_id: int,
    schedule_cron: str,
    format: str,
    recipients: list[str],
    user_id: int
) -> dict
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| name | str | Yes | Report name |
| description | str | Yes | Report description |
| saved_query_id | int | Yes | ID of saved query |
| schedule_cron | str | Yes | Cron expression |
| format | str | Yes | Format: csv, excel, pdf |
| recipients | list[str] | Yes | Email addresses |
| user_id | int | Yes | User ID |

**Returns:**
```json
{
  "status": "success",
  "report_id": 15,
  "name": "Daily Sales Report",
  "schedule_cron": "0 9 * * *",
  "next_run_at": "2024-01-16T09:00:00Z"
}
```

**Examples:**

```python
# Daily report at 9 AM
report = await create_scheduled_report(
    name="Daily Sales Report",
    description="Daily sales summary",
    saved_query_id=42,
    schedule_cron="0 9 * * *",
    format="excel",
    recipients=["manager@example.com", "ceo@example.com"],
    user_id=1
)

# Weekly report (Monday at 8 AM)
report = await create_scheduled_report(
    name="Weekly Summary",
    description="Weekly performance metrics",
    saved_query_id=43,
    schedule_cron="0 8 * * 1",
    format="pdf",
    recipients=["team@example.com"],
    user_id=1
)

# Monthly report (1st day at 10 AM)
report = await create_scheduled_report(
    name="Monthly Report",
    description="Monthly revenue analysis",
    saved_query_id=44,
    schedule_cron="0 10 1 * *",
    format="excel",
    recipients=["finance@example.com"],
    user_id=1
)
```

**Cron Expression Examples:**
| Schedule | Cron Expression | Description |
|----------|----------------|-------------|
| Every day at 9 AM | `0 9 * * *` | Daily report |
| Every Monday at 8 AM | `0 8 * * 1` | Weekly report |
| 1st of month at 10 AM | `0 10 1 * *` | Monthly report |
| Every hour | `0 * * * *` | Hourly report |
| Every 6 hours | `0 */6 * * *` | Every 6 hours |
| Weekdays at 9 AM | `0 9 * * 1-5` | Business days only |

### 14. list_scheduled_reports

List all scheduled reports.

**Function:**
```python
async def list_scheduled_reports(user_id: int) -> dict
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| user_id | int | Yes | User ID |

**Returns:**
```json
{
  "status": "success",
  "reports": [
    {
      "id": 15,
      "name": "Daily Sales Report",
      "description": "Daily sales summary",
      "schedule_cron": "0 9 * * *",
      "format": "excel",
      "recipients": ["manager@example.com"],
      "is_active": true,
      "last_run_at": "2024-01-15T09:00:00Z",
      "next_run_at": "2024-01-16T09:00:00Z",
      "status": "success",
      "created_at": "2024-01-10T12:00:00Z"
    }
  ],
  "total": 5
}
```

**Example:**
```python
reports = await list_scheduled_reports(user_id=1)
for report in reports['reports']:
    print(f"{report['name']}: {report['schedule_cron']}")
    print(f"  Next run: {report['next_run_at']}")
    print(f"  Status: {report['status']}")
```

### 15. update_scheduled_report

Update report configuration.

**Function:**
```python
async def update_scheduled_report(
    report_id: int,
    user_id: int,
    name: str | None = None,
    description: str | None = None,
    schedule_cron: str | None = None,
    format: str | None = None,
    recipients: list[str] | None = None,
    is_active: bool | None = None
) -> dict
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| report_id | int | Yes | Report ID |
| user_id | int | Yes | User ID |
| name | str | No | New name |
| description | str | No | New description |
| schedule_cron | str | No | New schedule |
| format | str | No | New format |
| recipients | list[str] | No | New recipients |
| is_active | bool | No | Enable/disable |

**Returns:**
```json
{
  "status": "success",
  "report_id": 15
}
```

**Examples:**

```python
# Change schedule
result = await update_scheduled_report(
    report_id=15,
    user_id=1,
    schedule_cron="0 10 * * *"  # Change to 10 AM
)

# Add recipients
result = await update_scheduled_report(
    report_id=15,
    user_id=1,
    recipients=["manager@example.com", "newuser@example.com"]
)

# Disable report
result = await update_scheduled_report(
    report_id=15,
    user_id=1,
    is_active=False
)

# Change format
result = await update_scheduled_report(
    report_id=15,
    user_id=1,
    format="pdf"
)
```

### 16. delete_scheduled_report

Delete a scheduled report.

**Function:**
```python
async def delete_scheduled_report(report_id: int, user_id: int) -> dict
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| report_id | int | Yes | Report ID |
| user_id | int | Yes | User ID |

**Returns:**
```json
{
  "status": "success",
  "report_id": 15
}
```

**Example:**
```python
result = await delete_scheduled_report(report_id=15, user_id=1)
print(f"Deleted report #{result['report_id']}")
```

### 17. trigger_report_now

Manually trigger report execution.

**Function:**
```python
async def trigger_report_now(report_id: int, user_id: int) -> dict
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| report_id | int | Yes | Report ID |
| user_id | int | Yes | User ID |

**Returns:**
```json
{
  "status": "triggered",
  "report_id": 15,
  "task_id": "abc123-def456-789",
  "message": "Report execution started in background"
}
```

**Example:**
```python
result = await trigger_report_now(report_id=15, user_id=1)
print(f"Task ID: {result['task_id']}")

# Check task status later
task_status = celery_app.AsyncResult(result['task_id'])
print(f"Status: {task_status.status}")
```

---

## Error Handling

### Standard Error Response

```json
{
  "status": "error",
  "error": "Detailed error message",
  "error_code": "ERR_CODE"
}
```

### Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `PERMISSION_DENIED` | User lacks permission | 403 |
| `NOT_FOUND` | Resource not found | 404 |
| `VALIDATION_ERROR` | Invalid parameters | 400 |
| `TIMEOUT` | Query exceeded time limit | 408 |
| `SQL_ERROR` | SQL syntax or execution error | 500 |
| `RATE_LIMIT` | Too many requests | 429 |
| `SERVER_ERROR` | Internal server error | 500 |

### Error Handling Example

```python
result = await query_database(
    question="Show sensitive data",
    user_id=1
)

if result['status'] == 'error':
    if 'Permission denied' in result['error']:
        print("Access denied - check user permissions")
    elif 'timeout' in result['error'].lower():
        print("Query too slow - try simplifying")
    elif 'syntax' in result['error'].lower():
        print("SQL error - query generation failed")
    else:
        print(f"Unexpected error: {result['error']}")
else:
    print(f"Success! {result['row_count']} rows returned")
```

---

## Rate Limiting

### Limits

- **Query Execution**: 100 queries/user/hour
- **Export Operations**: 50 exports/user/hour
- **Report Creation**: 20 reports/user/day
- **API Requests**: 1000 requests/user/hour

### Rate Limit Headers

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1705327200
```

### Rate Limit Exceeded Response

```json
{
  "status": "error",
  "error": "Rate limit exceeded",
  "error_code": "RATE_LIMIT",
  "retry_after": 3600
}
```

---

## Best Practices

### Performance

1. **Use caching**: Results cached for 5 minutes automatically
2. **Limit result size**: Use LIMIT in queries for large datasets
3. **Batch operations**: Group multiple queries when possible
4. **Monitor query history**: Review slow queries in statistics

### Security

1. **Never expose user_id**: Keep user IDs secure
2. **Validate inputs**: All parameters validated server-side
3. **Use saved queries**: Pre-validate complex queries
4. **Review permissions**: Regular permission audits

### Monitoring

1. **Track statistics**: Use `get_user_statistics` regularly
2. **Review failures**: Check failed queries in history
3. **Monitor performance**: Track execution times
4. **Set up alerts**: Configure alerts for failures

---

## SDK Examples

### Python Client

```python
from mcp_client import MCPClient

client = MCPClient("http://localhost:3000")

# Query database
result = await client.query_database(
    "What is the total revenue?",
    user_id=1
)

# Generate chart
chart = await client.generate_chart(
    data=result['rows'],
    chart_type='bar'
)

# Schedule report
report = await client.create_scheduled_report(
    name="Daily Report",
    saved_query_id=42,
    schedule_cron="0 9 * * *",
    format="excel",
    recipients=["team@example.com"],
    user_id=1
)
```

### TypeScript Client

```typescript
import { MCPClient } from '@mcp/client';

const client = new MCPClient('http://localhost:3000');

// Query database
const result = await client.queryDatabase({
  question: 'What is the total revenue?',
  userId: 1
});

// Generate chart
const chart = await client.generateChart({
  data: result.rows,
  chartType: 'bar'
});

// Schedule report
const report = await client.createScheduledReport({
  name: 'Daily Report',
  savedQueryId: 42,
  scheduleCron: '0 9 * * *',
  format: 'excel',
  recipients: ['team@example.com'],
  userId: 1
});
```

---

## Support

For API issues:
- Check logs in `/var/log/mcp-server/`
- Review health endpoint: `http://localhost:3000/health`
- Monitor Prometheus metrics: `http://localhost:3000/metrics`

**Last Updated:** Phase 5 & 6 Complete  
**API Version:** 1.0.0  
**Documentation:** https://github.com/your-org/mcp-server-client
