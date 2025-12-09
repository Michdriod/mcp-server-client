# MCP Tools Quick Reference

This document provides a quick reference for all 11 MCP tools exposed by the Database Query Assistant server.

## 🔍 Query Tools

### 1. `query_database`
Convert natural language to SQL and execute queries.

**Parameters:**
- `question` (str): Natural language question
- `user_id` (int): User ID executing the query

**Returns:**
```python
{
    "rows": [...],              # Query results
    "row_count": 42,           # Number of rows returned
    "columns": ["id", "name"], # Column names
    "execution_time_ms": 123.45,
    "sql": "SELECT ...",       # Generated SQL
    "explanation": "...",      # AI's explanation
    "confidence": 0.95,        # AI confidence score
    "cached": False,           # Cache hit/miss
    "question": "...",         # Original question
    "status": "success"
}
```

**Example:**
```python
result = await query_database(
    question="What are the top 5 customers by total order value?",
    user_id=1
)
```

### 2. `get_schema_info`
Get detailed schema information for a table.

**Parameters:**
- `table_name` (str): Name of the table

**Returns:**
```python
{
    "table_name": "customers",
    "columns": [
        {
            "name": "id",
            "type": "integer",
            "nullable": False,
            "default": "nextval(...)",
            "max_length": None
        },
        ...
    ],
    "primary_keys": ["id"],
    "foreign_keys": [
        {
            "column": "user_id",
            "references_table": "users",
            "references_column": "id"
        }
    ],
    "status": "success"
}
```

**Example:**
```python
schema = await get_schema_info(table_name="orders")
```

### 3. `list_tables`
List all available tables in the database.

**Parameters:** None

**Returns:**
```python
{
    "tables": [
        {
            "name": "customers",
            "schema": "public",
            "row_count": 1523
        },
        ...
    ],
    "total_tables": 8,
    "status": "success"
}
```

**Example:**
```python
tables = await list_tables()
for table in tables['tables']:
    print(f"{table['name']}: {table['row_count']} rows")
```

---

## 💾 Query Management Tools

### 4. `save_query`
Save a query for later reuse.

**Parameters:**
- `name` (str): Name for the saved query
- `description` (str): Description of what the query does
- `question` (str): Natural language question
- `sql` (str): SQL query to save
- `user_id` (int): User ID saving the query

**Returns:**
```python
{
    "query_id": 42,
    "name": "Monthly Revenue",
    "status": "success"
}
```

**Example:**
```python
result = await save_query(
    name="Monthly Revenue",
    description="Calculate total revenue for the current month",
    question="What is the total revenue this month?",
    sql="SELECT SUM(amount) FROM orders WHERE ...",
    user_id=1
)
```

### 5. `load_saved_query`
Load a previously saved query.

**Parameters:**
- `query_id` (int): ID of the saved query
- `user_id` (int): User ID loading the query

**Returns:**
```python
{
    "query_id": 42,
    "name": "Monthly Revenue",
    "description": "Calculate total revenue...",
    "question": "What is the total revenue this month?",
    "sql": "SELECT SUM(amount) ...",
    "created_at": "2024-01-15T14:30:22",
    "status": "success"
}
```

**Example:**
```python
query = await load_saved_query(query_id=42, user_id=1)
# Then execute it
result = await query_database(query['question'], user_id=1)
```

### 6. `list_saved_queries`
List all saved queries for a user.

**Parameters:**
- `user_id` (int): User ID
- `limit` (int, optional): Max queries to return (default: 20)

**Returns:**
```python
{
    "queries": [
        {
            "id": 42,
            "name": "Monthly Revenue",
            "description": "Calculate...",
            "question": "What is...",
            "created_at": "2024-01-15T14:30:22"
        },
        ...
    ],
    "total": 15,
    "status": "success"
}
```

**Example:**
```python
saved = await list_saved_queries(user_id=1, limit=10)
```

---

## 📊 Visualization Tools

### 7. `generate_chart`
Generate a chart from query results.

**Parameters:**
- `data` (list[dict]): Query results to visualize
- `chart_type` (str, optional): "bar", "line", "pie", or "scatter" (auto-detected if None)
- `title` (str, optional): Chart title (auto-generated if None)
- `x_column` (str, optional): Column for x-axis (auto-detected if None)
- `y_column` (str, optional): Column for y-axis (auto-detected if None)

**Returns:**
```python
{
    "filepath": "charts/line_20240115_143022.png",
    "chart_type": "line",
    "status": "success"
}
```

**Example:**
```python
# Query data
result = await query_database("Show monthly revenue for 2024", user_id=1)

# Generate chart
chart = await generate_chart(
    data=result['rows'],
    chart_type='line',
    title='2024 Monthly Revenue'
)
print(f"Chart saved to: {chart['filepath']}")
```

**Chart Type Auto-Detection:**
- **Pie**: ≤10 rows, 2 columns (1 numeric)
- **Scatter**: 2+ numeric columns
- **Line**: Date/time + numeric column
- **Bar**: Default fallback

### 8. `create_table_image`
Create a formatted table image from results.

**Parameters:**
- `data` (list[dict]): Query results to visualize
- `title` (str, optional): Table title
- `max_rows` (int, optional): Max rows to display (default: 20)

**Returns:**
```python
{
    "filepath": "charts/table_20240115_143022.png",
    "rows_displayed": 20,
    "total_rows": 150,
    "status": "success"
}
```

**Example:**
```python
result = await query_database("Show top 10 customers", user_id=1)

table = await create_table_image(
    data=result['rows'],
    title='Top 10 Customers by Revenue',
    max_rows=10
)
```

---

## 📜 History & Analytics Tools

### 9. `get_query_history`
Get recent query history for a user.

**Parameters:**
- `user_id` (int): User ID
- `limit` (int, optional): Max queries to return (default: 20)
- `status` (str, optional): Filter by "success" or "failed" (None for all)

**Returns:**
```python
{
    "queries": [
        {
            "id": 123,
            "question": "Show top customers",
            "sql": "SELECT ...",
            "status": "success",
            "result_rows": 10,
            "execution_time_ms": 45.23,
            "error_message": None,
            "created_at": "2024-01-15T14:30:22"
        },
        ...
    ],
    "total": 20,
    "status": "success"
}
```

**Example:**
```python
# Get all recent queries
history = await get_query_history(user_id=1, limit=10)

# Get only failed queries
failed = await get_query_history(user_id=1, limit=10, status='failed')
```

### 10. `get_popular_queries`
Get most frequently executed queries.

**Parameters:**
- `limit` (int, optional): Max queries to return (default: 10)
- `days` (int, optional): Look back period in days (default: 30)

**Returns:**
```python
{
    "queries": [
        {
            "question": "Show top customers",
            "sql": "SELECT ...",
            "execution_count": 42,
            "avg_execution_time_ms": 123.45,
            "total_rows_returned": 420
        },
        ...
    ],
    "period_days": 30,
    "status": "success"
}
```

**Example:**
```python
# Most popular queries in last 7 days
popular = await get_popular_queries(limit=5, days=7)

for query in popular['queries']:
    print(f"{query['question']}: {query['execution_count']} times")
```

### 11. `get_user_statistics`
Get statistics for a user's query activity.

**Parameters:**
- `user_id` (int): User ID
- `days` (int, optional): Look back period in days (default: 30)

**Returns:**
```python
{
    "user_id": 1,
    "period_days": 30,
    "total_queries": 150,
    "successful_queries": 142,
    "failed_queries": 8,
    "success_rate": 94.67,
    "avg_execution_time_ms": 234.56,
    "total_rows_returned": 12345,
    "status": "success"
}
```

**Example:**
```python
stats = await get_user_statistics(user_id=1, days=7)
print(f"Success rate: {stats['success_rate']}%")
print(f"Avg execution time: {stats['avg_execution_time_ms']}ms")
```

---

## 🔄 Common Workflows

### Workflow 1: Explore and Query
```python
# 1. Discover available tables
tables = await list_tables()

# 2. Get schema for interesting table
schema = await get_schema_info(table_name="customers")

# 3. Query the data
result = await query_database(
    question="Show customers who registered this month",
    user_id=1
)

# 4. Visualize results
chart = await generate_chart(data=result['rows'])
```

### Workflow 2: Save and Reuse
```python
# 1. Execute and test query
result = await query_database("Show monthly revenue", user_id=1)

# 2. Save if useful
saved = await save_query(
    name="Monthly Revenue",
    description="Revenue aggregated by month",
    question="Show monthly revenue",
    sql=result['sql'],
    user_id=1
)

# 3. Later, load and execute
query = await load_saved_query(query_id=saved['query_id'], user_id=1)
result = await query_database(query['question'], user_id=1)
```

### Workflow 3: Analysis and Optimization
```python
# 1. Check user statistics
stats = await get_user_statistics(user_id=1, days=7)

# 2. Find failed queries
failed = await get_query_history(user_id=1, limit=10, status='failed')

# 3. Find popular queries (optimize these first)
popular = await get_popular_queries(limit=5, days=30)
```

---

## 🚨 Error Handling

All tools return a status field and may include an error field:

```python
# Success
{
    "status": "success",
    ...
}

# Error
{
    "status": "error",
    "error": "Table 'invalid' not found"
}

# Permission Error
{
    "status": "permission_denied",
    "error": "Permission denied: Access denied to table: customers"
}

# Timeout
{
    "status": "timeout",
    "error": "Query timeout: Query exceeded timeout of 30 seconds"
}
```

Always check the `status` field before processing results:

```python
result = await query_database("...", user_id=1)

if result['status'] == 'success':
    # Process results
    for row in result['rows']:
        print(row)
elif result['status'] == 'permission_denied':
    print("You don't have access to this data")
elif result['status'] == 'timeout':
    print("Query took too long, try simplifying it")
else:
    print(f"Error: {result.get('error', 'Unknown error')}")
```

---

## 💡 Tips & Best Practices

### Query Performance
- ✅ Use specific questions: "Show top 10 customers by revenue"
- ❌ Avoid vague questions: "Tell me about customers"
- ✅ Limit results: Questions naturally include "top 10", "last month"
- ❌ Avoid unlimited: "Show all orders" (limited to 1000 rows anyway)

### Chart Generation
- Auto-detection works well, but specify chart_type for consistency
- Limit data to reasonable size (≤100 rows for readability)
- Use descriptive titles for better context

### Query Management
- Save frequently used queries with descriptive names
- Use descriptions to explain business logic
- Review popular queries to understand common patterns

### History & Analytics
- Monitor failed queries to identify permission issues
- Track success rates to measure data quality
- Use statistics to optimize slow queries

---

## 🔐 Security Notes

- All queries are logged with `user_id` for audit trails
- RBAC enforces table-level access control
- Row-level security filters data by user
- SQL injection protection via query validation
- 30-second timeout prevents resource exhaustion
- Max 1000 rows prevents memory issues

---

## 🎯 Quick Start Example

```python
# Full example: Query → Visualize → Save
import asyncio

async def analyze_customer_data():
    # 1. Query data
    result = await query_database(
        question="Show top 10 customers by total order value in 2024",
        user_id=1
    )
    
    if result['status'] != 'success':
        print(f"Error: {result['error']}")
        return
    
    print(f"Found {result['row_count']} customers")
    print(f"Query took {result['execution_time_ms']}ms")
    
    # 2. Generate chart
    chart = await generate_chart(
        data=result['rows'],
        chart_type='bar',
        title='Top 10 Customers by Revenue (2024)'
    )
    
    print(f"Chart saved to: {chart['filepath']}")
    
    # 3. Save query for reuse
    saved = await save_query(
        name="Top Customers 2024",
        description="Top 10 customers by revenue in 2024",
        question=result['question'],
        sql=result['sql'],
        user_id=1
    )
    
    print(f"Query saved with ID: {saved['query_id']}")

# Run the analysis
asyncio.run(analyze_customer_data())
```

---

For more details, see `PHASE2_SUMMARY.md`.
