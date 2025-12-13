"""
FastAPI REST Server for Database Query Assistant

Exposes MCP tools as REST endpoints for the frontend.
Uses a single persistent MCP client connection for efficiency.
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel, Field
from pydantic_ai import Agent
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager
import asyncio
from datetime import datetime
import os

# Import MCP client for backend operations
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from client.mcp_client import QueryAssistantClient
from shared.config import settings

# Global persistent MCP client
mcp_client: Optional[QueryAssistantClient] = None

# AI agent for empty result explanations (lazy initialization)
_empty_result_agent: Optional[Agent] = None

def get_empty_result_agent() -> Agent:
    """Get or create the empty result explanation agent."""
    global _empty_result_agent
    if _empty_result_agent is None:
        _empty_result_agent = Agent(
            model=settings.llm_model,
            output_type=str,
            instructions="""You are a helpful database assistant. When a query returns no results, 
            provide a friendly, concise explanation (1-2 sentences) about why the data doesn't exist.
            Be specific about what was searched for. Use a conversational tone."""
        )
    return _empty_result_agent

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage MCP client lifecycle - create once, reuse for all requests"""
    global mcp_client
    
    print("🚀 Starting MCP client connection...")
    mcp_client = QueryAssistantClient()
    await mcp_client.__aenter__()
    print("✅ MCP client connected and ready")
    
    yield
    
    print("🔌 Closing MCP client connection...")
    if mcp_client:
        await mcp_client.__aexit__(None, None, None)
    print("✅ MCP client closed")

# Create FastAPI app with lifespan management
app = FastAPI(
    title="Database Query Assistant API",
    description="Natural language database query REST API",
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://localhost:3000", 
        "http://localhost:8080", 
        "http://localhost:8081",  # New frontend port
        "http://172.20.10.2:8080", 
        "http://172.20.10.2:8081",
        "http://169.254.170.214:8080",
        "http://169.254.170.214:8081"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Request/Response Models ===

class QueryRequest(BaseModel):
    question: str
    user_id: int = Field(default=1, description="User ID (1=Admin, 2=Analyst, 3=Viewer)")
    output_format: Optional[str] = Field(default="table", description="table, json, or csv")
    chart_type: Optional[str] = Field(default=None, description="bar, line, pie, scatter, or null")

class QueryResponse(BaseModel):
    status: str
    columns: List[str]
    rows: List[Dict[str, Any]]
    rowCount: int  # camelCase for frontend
    columnCount: int
    executionTime: float  # camelCase for frontend (in ms)
    cached: bool
    sql: Optional[str] = None  # renamed from generated_sql
    chartPath: Optional[str] = None  # camelCase for frontend
    error: Optional[str] = None
    emptyResultMessage: Optional[str] = None  # AI-generated explanation for empty results
    queryId: Optional[int] = None  # For export tracking

class SaveQueryRequest(BaseModel):
    name: str
    query: str
    user_id: int = 1
    description: Optional[str] = None

class SavedQueryResponse(BaseModel):
    id: int
    name: str
    query: str
    description: Optional[str]
    createdAt: str  # camelCase for frontend
    lastExecuted: Optional[str] = None  # camelCase for frontend

class QueryHistoryItem(BaseModel):
    id: int
    query: str
    status: str
    rowCount: Optional[int] = None  # camelCase for frontend
    executionTime: Optional[float] = None  # camelCase for frontend
    createdAt: str  # camelCase for frontend
    error: Optional[str] = None

class DashboardStatsResponse(BaseModel):
    totalCustomers: int  # camelCase for frontend
    totalOrders: int
    totalRevenue: float
    pendingOrders: int
    customerGrowth: float
    orderGrowth: float
    revenueGrowth: float

class ExportRequest(BaseModel):
    query_id: int
    format: str = Field(default="csv", description="csv, json, or excel")
    user_id: int = 1

class SchemaInfoRequest(BaseModel):
    table_name: str

class PopularQueriesRequest(BaseModel):
    limit: int = 10
    days: int = 30

class UserStatsRequest(BaseModel):
    user_id: int = 1
    days: int = 30

class CreateReportRequest(BaseModel):
    name: str
    description: str
    saved_query_id: int
    schedule_cron: str = Field(description="Cron expression like '0 9 * * *'")
    format: str = Field(default="csv", description="csv, excel, or pdf")
    recipients: List[str] = Field(description="List of email addresses")
    user_id: int = 1

class UpdateReportRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    schedule_cron: Optional[str] = None
    format: Optional[str] = None
    recipients: Optional[List[str]] = None
    is_active: Optional[bool] = None
    user_id: int = 1

class ScheduledReportResponse(BaseModel):
    id: int
    name: str
    description: str
    savedQueryId: int  # camelCase for frontend
    scheduleCron: str  # camelCase for frontend
    format: str
    recipients: List[str]
    isActive: bool  # camelCase for frontend
    nextRunAt: Optional[str] = None  # camelCase for frontend
    lastRunAt: Optional[str] = None  # camelCase for frontend
    createdAt: str  # camelCase for frontend

# === API Endpoints ===

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "Database Query Assistant API",
        "version": "1.0.0",
        "endpoints": [
            "POST /api/query - Execute natural language query",
            "GET /api/saved-queries - List saved queries",
            "POST /api/saved-queries - Save a query",
            "DELETE /api/saved-queries/{id} - Delete a query",
            "GET /api/history - Get query history",
            "GET /api/dashboard/stats - Get dashboard statistics",
            "GET /api/charts/{filename} - Get chart image",
        ]
    }

@app.post("/api/query", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    """Execute a natural language database query"""
    global mcp_client
    
    if not mcp_client:
        raise HTTPException(status_code=503, detail="MCP client not initialized")
    
    try:
        # Execute the query using persistent MCP client
        result = await mcp_client.query_database(
            request.question,
            request.user_id
        )
        
        # Debug logging
        print(f"DEBUG - MCP Result keys: {result.keys() if result else 'None'}")
        print(f"DEBUG - MCP Result: {result}")
        
        # Generate AI explanation for empty results
        empty_message = None
        rows = result.get("rows", [])
        if len(rows) == 0:
            try:
                print(f"Empty result detected, generating AI explanation...")
                agent = get_empty_result_agent()
                ai_response = await agent.run(
                    f"User asked: '{request.question}'. The database query returned no results. "
                    f"Provide a brief, friendly explanation for why this might be the case."
                )
                # Pydantic AI returns the output directly, not wrapped in .data
                empty_message = str(ai_response) if not isinstance(ai_response, str) else ai_response
                print(f"AI explanation: {empty_message}")
            except Exception as e:
                print(f"Failed to generate AI explanation: {e}")
                import traceback
                traceback.print_exc()
                empty_message = "No results found for your query."
        
        # Generate chart if requested
        chart_path = None
        if request.chart_type:
            try:
                chart_result = await mcp_client.generate_chart(
                    request.user_id,
                    request.question,
                    request.chart_type
                )
                if chart_result and 'chart_path' in chart_result:
                    chart_path = os.path.basename(chart_result['chart_path'])
            except Exception as e:
                print(f"Chart generation failed: {e}")
        
        return QueryResponse(
            status="success",
            columns=result.get("columns", []),
            rows=rows,  # Changed from "results" to "rows"
            rowCount=result.get("row_count", 0),
            columnCount=result.get("column_count", 0),
            executionTime=result.get("execution_time_ms", 0),
            cached=result.get("cached", False),
            sql=result.get("sql"),  # Changed from "generated_sql" to "sql"
            chartPath=chart_path,
            emptyResultMessage=empty_message,
            queryId=result.get("query_id")  # Include query_id for export
        )
    
    except Exception as e:
        print(f"Query execution error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/saved-queries")
async def list_saved_queries(user_id: int = 1):
    """List all saved queries for a user"""
    global mcp_client
    
    if not mcp_client:
        raise HTTPException(status_code=503, detail="MCP client not initialized")
    
    try:
        result = await mcp_client.list_saved_queries(user_id)
        
        queries = []
        if result and 'queries' in result:
            for q in result['queries']:
                queries.append(SavedQueryResponse(
                    id=q['id'],
                    name=q['name'],
                    query=q['question'],  # Fixed: use 'question' not 'natural_query'
                    description=q.get('description'),
                    createdAt=q['created_at'],
                    lastExecuted=q.get('last_executed')
                ))
        
        return queries
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/saved-queries")
async def save_query(request: SaveQueryRequest):
    """Save a query for later use"""
    global mcp_client
    
    if not mcp_client:
        raise HTTPException(status_code=503, detail="MCP client not initialized")
    
    try:
        # Execute the query first to get the SQL
        query_result = await mcp_client.query_database(
            request.query,
            request.user_id
        )
        
        # Get the generated SQL from the query result
        sql = query_result.get("sql", "")
        
        # Now save the query with the correct parameters
        result = await mcp_client.save_query(
            name=request.name,
            description=request.description or "",
            question=request.query,
            sql=sql,
            user_id=request.user_id
        )
        
        # Extract query_id from the result
        query_id = result.get("query_id") or result.get("id")
        
        if not query_id:
            print(f"Warning: No query_id in save result: {result}")
        
        return {
            "status": "success",
            "query_id": query_id,
            "message": "Query saved successfully"
        }
    
    except Exception as e:
        print(f"Save query error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/saved-queries/{query_id}")
async def delete_saved_query(query_id: int, user_id: int = 1):
    """Delete a saved query"""
    global mcp_client
    
    if not mcp_client:
        raise HTTPException(status_code=503, detail="MCP client not initialized")
    
    try:
        result = await mcp_client.delete_saved_query(query_id, user_id)
        
        if result.get('status') == 'error':
            raise HTTPException(status_code=404, detail=result.get('error', 'Query not found'))
        
        return {"status": "success", "message": "Query deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history")
async def get_query_history(user_id: int = 1, days: int = 30):
    """Get query execution history"""
    global mcp_client
    
    if not mcp_client:
        raise HTTPException(status_code=503, detail="MCP client not initialized")
    
    try:
        # MCP method expects (user_id, limit, status), not days
        # Use days * 2 as a rough estimate for limit (assuming ~2 queries per day)
        limit = max(20, days * 2)
        result = await mcp_client.get_query_history(user_id, limit=limit, status=None)
        
        print(f"DEBUG - History result: {result}")
        
        history = []
        # MCP returns 'queries', not 'history'
        if result and 'queries' in result:
            for item in result['queries']:
                history.append(QueryHistoryItem(
                    id=str(item['id']),  # Convert to string for frontend
                    query=item.get('question', ''),  # Use 'question' field
                    status="success" if item.get('status') == 'success' else "error",
                    rowCount=item.get('result_rows'),
                    executionTime=item.get('execution_time_ms'),
                    createdAt=item.get('created_at', ''),
                    error=item.get('error_message')
                ))
        
        return history
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(user_id: int = 1):
    """Get dashboard statistics"""
    global mcp_client
    
    if not mcp_client:
        raise HTTPException(status_code=503, detail="MCP client not initialized")
    
    try:
        # Get basic stats
        stats = await mcp_client.get_user_statistics(user_id)
        
        # Execute simple aggregate queries for dashboard
        customers = await mcp_client.query_database("SELECT COUNT(*) as count FROM customers", user_id)
        print(f"DEBUG - Customers response: {customers}")
        orders = await mcp_client.query_database("SELECT COUNT(*) as count FROM orders", user_id)
        print(f"DEBUG - Orders response: {orders}")
        revenue = await mcp_client.query_database("SELECT SUM(amount) as total FROM orders", user_id)
        print(f"DEBUG - Revenue response: {revenue}")
        pending = await mcp_client.query_database("SELECT COUNT(*) as count FROM orders WHERE status = 'pending'", user_id)
        print(f"DEBUG - Pending response: {pending}")
        
        return DashboardStatsResponse(
            totalCustomers=customers.get("rows", [{}])[0].get("count", 0),
            totalOrders=orders.get("rows", [{}])[0].get("count", 0),
            totalRevenue=float(revenue.get("rows", [{}])[0].get("total", 0) or 0),
            pendingOrders=pending.get("rows", [{}])[0].get("count", 0),
            customerGrowth=12.5,  # TODO: Calculate actual growth
            orderGrowth=8.3,
            revenueGrowth=15.2
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/orders-by-status")
async def get_orders_by_status(user_id: int = 1):
    """Get order counts grouped by status"""
    global mcp_client
    
    if not mcp_client:
        raise HTTPException(status_code=503, detail="MCP client not initialized")
    
    try:
        result = await mcp_client.query_database(
            "SELECT status, COUNT(*) as count FROM orders GROUP BY status",
            user_id
        )
        
        data = []
        for row in result.get("rows", []):
            data.append({
                "name": row.get("status", "unknown").capitalize(),
                "value": row.get("count", 0)
            })
        
        return data
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/revenue-by-category")
async def get_revenue_by_category(user_id: int = 1):
    """Get revenue grouped by product category"""
    global mcp_client
    
    if not mcp_client:
        raise HTTPException(status_code=503, detail="MCP client not initialized")
    
    try:
        result = await mcp_client.query_database(
            "SELECT p.category as category, SUM(oi.quantity * oi.unit_price) as revenue "
            "FROM order_items oi "
            "JOIN products p ON oi.product_id = p.id "
            "GROUP BY p.category",
            user_id
        )
        
        data = []
        for row in result.get("rows", []):
            data.append({
                "name": row.get("category", "unknown"),
                "value": float(row.get("revenue", 0) or 0)
            })
        
        return data
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/dashboard/orders-over-time")
async def get_orders_over_time(user_id: int = 1):
    """Get orders and revenue over time"""
    global mcp_client
    
    if not mcp_client:
        raise HTTPException(status_code=503, detail="MCP client not initialized")
    
    try:
        result = await mcp_client.query_database(
            "SELECT TO_CHAR(order_date, 'Mon') as month, "
            "COUNT(*) as orders, SUM(amount) as revenue "
            "FROM orders "
            "WHERE order_date >= CURRENT_DATE - INTERVAL '6 months' "
            "GROUP BY TO_CHAR(order_date, 'Mon'), EXTRACT(MONTH FROM order_date) "
            "ORDER BY EXTRACT(MONTH FROM order_date)",
            user_id
        )
        
        data = []
        for row in result.get("rows", []):
            data.append({
                "name": row.get("month", ""),
                "orders": row.get("orders", 0),
                "revenue": float(row.get("revenue", 0) or 0)
            })
        
        return data
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/charts/{filename}")
async def get_chart(filename: str):
    """Serve generated chart images"""
    try:
        chart_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "charts",
            filename
        )
        
        if not os.path.exists(chart_path):
            raise HTTPException(status_code=404, detail="Chart not found")
        
        return FileResponse(chart_path, media_type="image/png")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === Scheduled Reports Endpoints ===

@app.post("/api/reports")
async def create_scheduled_report(request: CreateReportRequest):
    """Create a new scheduled report"""
    try:
        if not mcp_client:
            raise HTTPException(status_code=503, detail="MCP client not initialized")
        
        result = await mcp_client.call_tool(
            "create_scheduled_report",
            name=request.name,
            description=request.description,
            saved_query_id=request.saved_query_id,
            schedule_cron=request.schedule_cron,
            format=request.format,
            recipients=request.recipients,
            user_id=request.user_id
        )
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "reportId": result.get("report_id"),
            "name": result.get("name"),
            "scheduleCron": result.get("schedule_cron"),
            "nextRunAt": result.get("next_run_at"),
            "status": "success"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/reports")
async def list_scheduled_reports(user_id: int = 1):
    """List all scheduled reports for a user"""
    try:
        if not mcp_client:
            raise HTTPException(status_code=503, detail="MCP client not initialized")
        
        result = await mcp_client.call_tool(
            "list_scheduled_reports",
            user_id=user_id
        )
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Transform to camelCase for frontend
        reports = result.get("reports", [])
        return [
            {
                "id": r.get("id"),
                "name": r.get("name"),
                "description": r.get("description"),
                "savedQueryId": r.get("saved_query_id"),
                "scheduleCron": r.get("schedule_cron"),
                "format": r.get("format"),
                "recipients": r.get("recipients", []),
                "isActive": r.get("is_active"),
                "nextRunAt": r.get("next_run_at"),
                "lastRunAt": r.get("last_run_at"),
                "createdAt": r.get("created_at")
            }
            for r in reports
        ]
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/reports/{report_id}")
async def update_scheduled_report(report_id: int, request: UpdateReportRequest):
    """Update a scheduled report"""
    try:
        if not mcp_client:
            raise HTTPException(status_code=503, detail="MCP client not initialized")
        
        result = await mcp_client.call_tool(
            "update_scheduled_report",
            report_id=report_id,
            user_id=request.user_id,
            name=request.name,
            description=request.description,
            schedule_cron=request.schedule_cron,
            format=request.format,
            recipients=request.recipients,
            is_active=request.is_active
        )
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {
            "reportId": report_id,
            "status": "success"
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/reports/{report_id}")
async def delete_scheduled_report(report_id: int, user_id: int = 1):
    """Delete a scheduled report"""
    try:
        if not mcp_client:
            raise HTTPException(status_code=503, detail="MCP client not initialized")
        
        result = await mcp_client.call_tool(
            "delete_scheduled_report",
            report_id=report_id,
            user_id=user_id
        )
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        
        return {"status": "success"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/reports/{report_id}/execute")
async def execute_scheduled_report(report_id: int, user_id: int = 1):
    """Execute a scheduled report immediately"""
    try:
        if not mcp_client:
            raise HTTPException(status_code=503, detail="MCP client not initialized")
        
        result = await mcp_client.call_tool(
            "trigger_report_now",
            report_id=report_id,
            user_id=user_id
        )
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Return detailed response format like the newer endpoint
        return {
            "status": "success",
            "message": result.get("message", "Report executed successfully"),
            "execution_time": result.get("execution_time"),
            "row_count": result.get("row_count"),
            "email_status": result.get("email_status", "Unknown"),
            "emails_sent": result.get("emails_sent", 0),
            "recipients_count": result.get("recipients_count", 0)
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Error handler

@app.post("/api/export")
async def export_query_results(request: ExportRequest):
    """Export query results in various formats (CSV, JSON, Excel)"""
    try:
        if not mcp_client:
            raise HTTPException(status_code=503, detail="MCP client not initialized")
        
        result = await mcp_client.call_tool(
            "export_query_results",
            query_id=request.query_id,
            format=request.format,
            user_id=request.user_id
        )
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === Analytics Endpoints ===

@app.get("/api/analytics/popular-queries")
async def get_popular_queries(limit: int = 10, days: int = 30):
    """Get most popular queries by usage"""
    try:
        if not mcp_client:
            raise HTTPException(status_code=503, detail="MCP client not initialized")
        
        result = await mcp_client.call_tool(
            "get_popular_queries",
            limit=limit,
            days=days
        )
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Transform to camelCase for frontend
        queries = result.get("queries", [])
        return {
            "queries": [
                {
                    "question": q.get("question"),
                    "executionCount": q.get("execution_count"),
                    "avgExecutionTime": q.get("avg_execution_time"),
                    "lastExecuted": q.get("last_executed")
                }
                for q in queries
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/user-stats")
async def get_user_statistics(user_id: int = 1, days: int = 30):
    """Get user activity statistics"""
    try:
        if not mcp_client:
            raise HTTPException(status_code=503, detail="MCP client not initialized")
        
        result = await mcp_client.call_tool(
            "get_user_statistics",
            user_id=user_id,
            days=days
        )
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Transform to camelCase for frontend
        stats = result.get("statistics", {})
        return {
            "totalQueries": stats.get("total_queries"),
            "successfulQueries": stats.get("successful_queries"),
            "failedQueries": stats.get("failed_queries"),
            "avgExecutionTime": stats.get("avg_execution_time"),
            "totalRowsReturned": stats.get("total_rows_returned"),
            "savedQueries": stats.get("saved_queries"),
            "mostActiveDay": stats.get("most_active_day"),
            "activityByDay": stats.get("activity_by_day", [])
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === Schema Explorer Endpoints ===

@app.get("/api/schema/tables")
async def list_database_tables():
    """List all database tables with metadata"""
    try:
        if not mcp_client:
            raise HTTPException(status_code=503, detail="MCP client not initialized")
        
        result = await mcp_client.call_tool("list_tables")
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Transform to camelCase for frontend
        tables = result.get("tables", [])
        return {
            "tables": [
                {
                    "name": t.get("name"),
                    "rowCount": t.get("row_count"),
                    "columnCount": t.get("column_count"),
                    "description": t.get("description")
                }
                for t in tables
            ]
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/schema/tables/{table_name}")
async def get_table_schema(table_name: str):
    """Get detailed schema information for a specific table"""
    try:
        if not mcp_client:
            raise HTTPException(status_code=503, detail="MCP client not initialized")
        
        result = await mcp_client.call_tool(
            "get_schema_info",
            table_name=table_name
        )
        
        if result.get("error"):
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Transform to camelCase for frontend
        schema = result.get("schema", {})
        return {
            "tableName": schema.get("table_name"),
            "columns": [
                {
                    "name": col.get("name"),
                    "type": col.get("type"),
                    "nullable": col.get("nullable"),
                    "primaryKey": col.get("primary_key"),
                    "foreignKey": col.get("foreign_key"),
                    "defaultValue": col.get("default")
                }
                for col in schema.get("columns", [])
            ],
            "rowCount": schema.get("row_count"),
            "sampleData": schema.get("sample_data", [])
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/cleanup-history")
async def cleanup_history(days_to_keep: int = 1):
    """Manually clean up old query history records"""
    global mcp_client
    
    if not mcp_client:
        raise HTTPException(status_code=503, detail="MCP client not initialized")
    
    try:
        result = await mcp_client.call_tool("cleanup_query_history", days_to_keep=days_to_keep)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# === Scheduled Reports Endpoints ===

@app.get("/api/scheduled-reports", response_model=List[ScheduledReportResponse])
async def list_scheduled_reports(user_id: int = 1):
    """List all scheduled reports for a user"""
    global mcp_client
    
    if not mcp_client:
        raise HTTPException(status_code=503, detail="MCP client not initialized")
    
    try:
        result = await mcp_client.call_tool("list_scheduled_reports", user_id=user_id)
        reports = result.get("reports", [])
        
        return [
            ScheduledReportResponse(
                id=report["id"],
                name=report["name"],
                description=report.get("description", ""),
                savedQueryId=report["saved_query_id"],
                scheduleCron=report["cron_schedule"],
                format=report["format"],
                recipients=report["recipients"],
                isActive=report["is_active"],
                nextRunAt=report.get("next_run_at"),
                lastRunAt=report.get("last_run_at"),
                createdAt=report["created_at"]
            )
            for report in reports
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/scheduled-reports", response_model=ScheduledReportResponse)
async def create_scheduled_report(report: CreateReportRequest):
    """Create a new scheduled report"""
    global mcp_client
    
    if not mcp_client:
        raise HTTPException(status_code=503, detail="MCP client not initialized")
    
    try:
        result = await mcp_client.call_tool(
            "create_scheduled_report",
            name=report.name,
            description=report.description or "",
            saved_query_id=report.savedQueryId,
            cron_schedule=report.scheduleCron,
            format=report.format,
            recipients=report.recipients or [],
            user_id=report.user_id
        )
        
        created_report = result["report"]
        return ScheduledReportResponse(
            id=created_report["id"],
            name=created_report["name"],
            description=created_report.get("description", ""),
            savedQueryId=created_report["saved_query_id"],
            scheduleCron=created_report["cron_schedule"],
            format=created_report["format"],
            recipients=created_report["recipients"],
            isActive=created_report["is_active"],
            nextRunAt=created_report.get("next_run_at"),
            lastRunAt=created_report.get("last_run_at"),
            createdAt=created_report["created_at"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/scheduled-reports/{report_id}", response_model=ScheduledReportResponse)
async def update_scheduled_report(report_id: int, report: UpdateReportRequest):
    """Update an existing scheduled report"""
    global mcp_client
    
    if not mcp_client:
        raise HTTPException(status_code=503, detail="MCP client not initialized")
    
    try:
        result = await mcp_client.call_tool(
            "update_scheduled_report",
            report_id=report_id,
            name=report.name,
            description=report.description or "",
            saved_query_id=report.savedQueryId,
            cron_schedule=report.scheduleCron,
            format=report.format,
            recipients=report.recipients or [],
            is_active=report.is_active,
            user_id=report.user_id
        )
        
        updated_report = result["report"]
        return ScheduledReportResponse(
            id=updated_report["id"],
            name=updated_report["name"],
            description=updated_report.get("description", ""),
            savedQueryId=updated_report["saved_query_id"],
            scheduleCron=updated_report["cron_schedule"],
            format=updated_report["format"],
            recipients=updated_report["recipients"],
            isActive=updated_report["is_active"],
            nextRunAt=updated_report.get("next_run_at"),
            lastRunAt=updated_report.get("last_run_at"),
            createdAt=updated_report["created_at"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/scheduled-reports/{report_id}")
async def delete_scheduled_report(report_id: int, user_id: int = 1):
    """Delete a scheduled report"""
    global mcp_client
    
    if not mcp_client:
        raise HTTPException(status_code=503, detail="MCP client not initialized")
    
    try:
        result = await mcp_client.call_tool(
            "delete_scheduled_report",
            report_id=report_id,
            user_id=user_id
        )
        return {"status": "success", "message": result.get("message", "Report deleted successfully")}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# Error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "message": str(exc),
            "detail": "An unexpected error occurred"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
