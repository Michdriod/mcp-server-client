"""
FastMCP Server for Database Query Assistant.
Exposes tools for natural language database querying.
"""
import asyncio
from contextlib import asynccontextmanager
from typing import Any

from dotenv import load_dotenv
import os
from pathlib import Path

# Load environment variables from .env file BEFORE any other imports
# Get the project root directory (parent of server directory)
project_root = Path(__file__).parent.parent
env_path = project_root / '.env'
load_dotenv(dotenv_path=env_path)

from fastmcp import FastMCP
from pydantic import BaseModel, Field

from server.db.connection import DatabaseConnection
from server.query.query_executor import query_executor
from server.query.sql_generator import sql_generator
from server.db.models import SavedQuery, QueryStatus, ScheduledReport, ReportFormat, ReportStatus
from server.tools.chart_generator import chart_generator, ChartType
from server.tools.history import history_manager
from server.tools.exporters import export_to_csv, export_to_excel, export_to_pdf, export_to_json
from sqlalchemy import select, delete
from shared.config import settings
from croniter import croniter
from datetime import datetime, UTC

from dotenv import load_dotenv

#load .env file
load_dotenv()

# Initialize FastMCP app
mcp = FastMCP("Database Query Assistant")


# Pydantic models for tool parameters
class QueryDatabaseParams(BaseModel):
    """Parameters for query_database tool."""
    question: str = Field(..., description="Natural language question about the data")
    user_id: int = Field(..., description="User ID executing the query")


class GetSchemaInfoParams(BaseModel):
    """Parameters for get_schema_info tool."""
    table_name: str = Field(..., description="Name of the table to get schema for")


class SaveQueryParams(BaseModel):
    """Parameters for save_query tool."""
    name: str = Field(..., description="Name for the saved query")
    description: str = Field(..., description="Description of what the query does")
    question: str = Field(..., description="Natural language question")
    sql: str = Field(..., description="Generated SQL query")
    user_id: int = Field(..., description="User ID saving the query")


class LoadSavedQueryParams(BaseModel):
    """Parameters for load_saved_query tool."""
    query_id: int = Field(..., description="ID of the saved query to load")
    user_id: int = Field(..., description="User ID loading the query")


class GenerateChartParams(BaseModel):
    """Parameters for generate_chart tool."""
    data: list[dict[str, Any]] = Field(..., description="Query results to visualize")
    chart_type: ChartType | None = Field(None, description="Type of chart (auto-detected if None)")
    title: str | None = Field(None, description="Chart title (auto-generated if None)")
    x_column: str | None = Field(None, description="Column for x-axis (auto-detected if None)")
    y_column: str | None = Field(None, description="Column for y-axis (auto-detected if None)")


# Database connection manager
db_connection = DatabaseConnection()


@asynccontextmanager
async def get_db_session():
    """Get async database session."""
    async with db_connection.session() as session:
        yield session


@mcp.tool()
async def query_database(question: str, user_id: int) -> dict[str, Any]:
    """
    Query the database using natural language.
    
    This tool converts natural language questions into SQL queries,
    executes them safely with permission checks and timeouts,
    and returns the results.
    
    Args:
        question: Natural language question (e.g., "What are the top 5 customers by revenue?")
        user_id: ID of the user executing the query
    
    Returns:
        Dictionary containing:
        - rows: List of result rows
        - row_count: Number of rows returned
        - columns: List of column names
        - execution_time_ms: Query execution time
        - sql: Generated SQL query
        - cached: Whether results came from cache
    
    Example:
        >>> result = await query_database(
        ...     question="Show me users who registered this month",
        ...     user_id=1
        ... )
        >>> print(f"Found {result['row_count']} users")
    """
    async with get_db_session() as session:
        try:
            # 1. Get schema context
            schema_context = await sql_generator.get_schema_context(
                session=session,
                database_name="public"
            )
            
            # 2. Generate SQL from natural language
            sql_result = await sql_generator.generate_sql(
                question=question,
                schema_context=schema_context,
                user_id=user_id
            )
            
            # sql_generator.generate_sql() raises QueryValidationError if SQL is invalid
            # so if we reach here, the SQL is valid
            
            # 3. Execute the generated SQL
            result = await query_executor.execute_query(
                sql=sql_result.sql,
                user_id=user_id,
                session=session,
                cache_results=True,
            )
            
            # 4. Log query to history
            try:
                await history_manager.log_query(
                    user_id=user_id,
                    natural_query=question,
                    sql_query=sql_result.sql,
                    success=True,
                    row_count=result.get("row_count", 0),
                    execution_time_ms=result.get("execution_time_ms", 0),
                    session=session
                )
            except Exception as history_error:
                # Don't fail the query if history logging fails
                print(f"Warning: Failed to log query to history: {history_error}")
            
            # 5. Add explanation and confidence
            result["explanation"] = sql_result.explanation
            result["confidence"] = sql_result.confidence
            result["question"] = question
            result["status"] = "success"
            
            return result
            
        except PermissionError as e:
            # Log failed query to history
            try:
                async with get_db_session() as session:
                    await history_manager.log_query(
                        user_id=user_id,
                        natural_query=question,
                        sql_query="",
                        success=False,
                        error=str(e),
                        session=session
                    )
            except:
                pass
            
            return {
                "error": f"Permission denied: {str(e)}",
                "question": question,
                "status": "permission_denied",
            }
        except TimeoutError as e:
            # Log failed query to history
            try:
                async with get_db_session() as session:
                    await history_manager.log_query(
                        user_id=user_id,
                        natural_query=question,
                        sql_query="",
                        success=False,
                        error=str(e),
                        session=session
                    )
            except:
                pass
            
            return {
                "error": f"Query timeout: {str(e)}",
                "question": question,
                "status": "timeout",
            }
        except Exception as e:
            # Log failed query to history
            try:
                async with get_db_session() as session:
                    await history_manager.log_query(
                        user_id=user_id,
                        natural_query=question,
                        sql_query="",
                        success=False,
                        error=str(e),
                        session=session
                    )
            except:
                pass
            
            return {
                "error": f"Query failed: {str(e)}",
                "question": question,
                "status": "error",
            }


@mcp.tool()
async def get_schema_info(table_name: str) -> dict[str, Any]:
    """
    Get detailed schema information for a specific table.
    
    Args:
        table_name: Name of the table to inspect
    
    Returns:
        Dictionary containing:
        - table_name: Name of the table
        - columns: List of column details (name, type, nullable, default)
        - primary_keys: List of primary key columns
        - foreign_keys: List of foreign key relationships
        - indexes: List of indexes on the table
    
    Example:
        >>> schema = await get_schema_info("users")
        >>> print(f"Table has {len(schema['columns'])} columns")
    """
    async with get_db_session() as session:
        try:
            # Get column information
            columns_query = """
                SELECT 
                    column_name,
                    data_type,
                    is_nullable,
                    column_default,
                    character_maximum_length
                FROM information_schema.columns
                WHERE table_schema = 'public'
                    AND table_name = :table_name
                ORDER BY ordinal_position
            """
            
            result = await session.execute(
                columns_query,
                {"table_name": table_name}
            )
            columns = [
                {
                    "name": row.column_name,
                    "type": row.data_type,
                    "nullable": row.is_nullable == "YES",
                    "default": row.column_default,
                    "max_length": row.character_maximum_length,
                }
                for row in result.fetchall()
            ]
            
            if not columns:
                return {
                    "error": f"Table '{table_name}' not found",
                    "status": "not_found",
                }
            
            # Get primary keys
            pk_query = """
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                WHERE tc.table_schema = 'public'
                    AND tc.table_name = :table_name
                    AND tc.constraint_type = 'PRIMARY KEY'
            """
            
            result = await session.execute(pk_query, {"table_name": table_name})
            primary_keys = [row.column_name for row in result.fetchall()]
            
            # Get foreign keys
            fk_query = """
                SELECT
                    kcu.column_name,
                    ccu.table_name AS foreign_table_name,
                    ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                    ON tc.constraint_name = kcu.constraint_name
                JOIN information_schema.constraint_column_usage ccu
                    ON ccu.constraint_name = tc.constraint_name
                WHERE tc.table_schema = 'public'
                    AND tc.table_name = :table_name
                    AND tc.constraint_type = 'FOREIGN KEY'
            """
            
            result = await session.execute(fk_query, {"table_name": table_name})
            foreign_keys = [
                {
                    "column": row.column_name,
                    "references_table": row.foreign_table_name,
                    "references_column": row.foreign_column_name,
                }
                for row in result.fetchall()
            ]
            
            return {
                "table_name": table_name,
                "columns": columns,
                "primary_keys": primary_keys,
                "foreign_keys": foreign_keys,
                "status": "success",
            }
            
        except Exception as e:
            return {
                "error": f"Failed to get schema: {str(e)}",
                "table_name": table_name,
                "status": "error",
            }


@mcp.tool()
async def list_tables() -> dict[str, Any]:
    """
    List all tables available in the database.
    
    Returns:
        Dictionary containing:
        - tables: List of table information (name, row_count, size)
        - total_tables: Total number of tables
    
    Example:
        >>> tables = await list_tables()
        >>> for table in tables['tables']:
        ...     print(f"{table['name']}: {table['row_count']} rows")
    """
    async with get_db_session() as session:
        try:
            query = """
                SELECT 
                    tablename as table_name,
                    schemaname as schema_name
                FROM pg_catalog.pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
            """
            
            result = await session.execute(query)
            tables = []
            
            for row in result.fetchall():
                # Get row count for each table
                count_query = f"SELECT COUNT(*) FROM {row.table_name}"
                count_result = await session.execute(count_query)
                row_count = count_result.scalar()
                
                tables.append({
                    "name": row.table_name,
                    "schema": row.schema_name,
                    "row_count": row_count,
                })
            
            return {
                "tables": tables,
                "total_tables": len(tables),
                "status": "success",
            }
            
        except Exception as e:
            return {
                "error": f"Failed to list tables: {str(e)}",
                "status": "error",
            }


@mcp.tool()
async def save_query(
    name: str,
    description: str,
    question: str,
    sql: str,
    user_id: int
) -> dict[str, Any]:
    """
    Save a query for later reuse.
    
    Args:
        name: Name for the saved query
        description: Description of what the query does
        question: Natural language question
        sql: SQL query to save
        user_id: ID of the user saving the query
    
    Returns:
        Dictionary containing:
        - query_id: ID of the saved query
        - name: Name of the query
        - status: Success or error status
    
    Example:
        >>> result = await save_query(
        ...     name="Monthly Revenue",
        ...     description="Calculate total revenue for the current month",
        ...     question="What is the total revenue this month?",
        ...     sql="SELECT SUM(amount) FROM orders WHERE ...",
        ...     user_id=1
        ... )
        >>> print(f"Saved as query ID: {result['query_id']}")
    """
    async with get_db_session() as session:
        try:
            saved_query = SavedQuery(
                user_id=user_id,
                name=name,
                description=description,
                question=question,
                generated_sql=sql,  # Fixed: use generated_sql not sql_query
            )
            
            session.add(saved_query)
            await session.commit()
            await session.refresh(saved_query)
            
            print(f"✅ Query saved successfully with ID: {saved_query.id}")
            
            return {
                "query_id": saved_query.id,
                "name": name,
                "status": "success",
            }
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Failed to save query: {e}")
            import traceback
            traceback.print_exc()
            return {
                "error": f"Failed to save query: {str(e)}",
                "status": "error",
            }


@mcp.tool()
async def load_saved_query(query_id: int, user_id: int) -> dict[str, Any]:
    """
    Load a previously saved query.
    
    Args:
        query_id: ID of the saved query to load
        user_id: ID of the user loading the query
    
    Returns:
        Dictionary containing:
        - query_id: ID of the query
        - name: Name of the query
        - description: Description
        - question: Natural language question
        - sql: SQL query
        - created_at: When it was saved
        - status: Success or error status
    
    Example:
        >>> query = await load_saved_query(query_id=5, user_id=1)
        >>> print(f"Loaded: {query['name']}")
        >>> result = await query_database(query['question'], user_id=1)
    """
    async with get_db_session() as session:
        try:
            stmt = select(SavedQuery).where(
                SavedQuery.id == query_id,
                SavedQuery.user_id == user_id
            )
            result = await session.execute(stmt)
            saved_query = result.scalar_one_or_none()
            
            if not saved_query:
                return {
                    "error": "Query not found or access denied",
                    "status": "not_found",
                }
            
            return {
                "query_id": saved_query.id,
                "name": saved_query.name,
                "description": saved_query.description,
                "question": saved_query.question,
                "sql": saved_query.sql_query,
                "created_at": saved_query.created_at.isoformat(),
                "status": "success",
            }
            
        except Exception as e:
            return {
                "error": f"Failed to load query: {str(e)}",
                "status": "error",
            }


@mcp.tool()
async def list_saved_queries(user_id: int, limit: int = 20) -> dict[str, Any]:
    """
    List saved queries for a user.
    
    Args:
        user_id: ID of the user
        limit: Maximum number of queries to return (default: 20)
    
    Returns:
        Dictionary containing:
        - queries: List of saved queries
        - total: Total number of saved queries
        - status: Success or error status
    
    Example:
        >>> result = await list_saved_queries(user_id=1, limit=10)
        >>> for query in result['queries']:
        ...     print(f"{query['id']}: {query['name']}")
    """
    async with get_db_session() as session:
        try:
            stmt = (
                select(SavedQuery)
                .where(SavedQuery.user_id == user_id)
                .order_by(SavedQuery.created_at.desc())
                .limit(limit)
            )
            result = await session.execute(stmt)
            queries = result.scalars().all()
            
            return {
                "queries": [
                    {
                        "id": q.id,
                        "name": q.name,
                        "description": q.description,
                        "question": q.question,
                        "created_at": q.created_at.isoformat(),
                    }
                    for q in queries
                ],
                "total": len(queries),
                "status": "success",
            }
            
        except Exception as e:
            return {
                "error": f"Failed to list queries: {str(e)}",
                "status": "error",
            }


@mcp.tool()
async def delete_saved_query(query_id: int, user_id: int) -> dict[str, Any]:
    """
    Delete a saved query.
    
    Args:
        query_id: ID of the saved query to delete
        user_id: ID of the user who owns the query
    
    Returns:
        Dictionary containing:
        - status: Success or error status
        - message: Success message or error details
    
    Example:
        >>> result = await delete_saved_query(query_id=1, user_id=1)
        >>> print(result['message'])
    """
    async with get_db_session() as session:
        try:
            # Find the query to delete
            stmt = select(SavedQuery).where(
                SavedQuery.id == query_id,
                SavedQuery.user_id == user_id
            )
            result = await session.execute(stmt)
            query_to_delete = result.scalar_one_or_none()
            
            if not query_to_delete:
                return {
                    "error": "Query not found or not owned by user",
                    "status": "error",
                }
            
            # Delete the query
            await session.delete(query_to_delete)
            await session.commit()
            
            print(f"✅ Query {query_id} deleted successfully")
            
            return {
                "status": "success",
                "message": "Query deleted successfully",
            }
            
        except Exception as e:
            await session.rollback()
            print(f"❌ Failed to delete query: {e}")
            return {
                "error": f"Failed to delete query: {str(e)}",
                "status": "error",
            }


@mcp.tool()
async def generate_chart(
    data: list[dict[str, Any]],
    chart_type: ChartType | None = None,
    title: str | None = None,
    x_column: str | None = None,
    y_column: str | None = None,
) -> dict[str, Any]:
    """
    Generate a chart from query results.
    
    This tool creates visualizations (bar, line, pie, scatter) from data.
    Chart type is auto-detected if not specified.
    
    Args:
        data: List of dictionaries containing query results
        chart_type: Type of chart to generate (auto-detected if None)
        title: Chart title (auto-generated if None)
        x_column: Column to use for x-axis (auto-detected if None)
        y_column: Column to use for y-axis (auto-detected if None)
    
    Returns:
        Dictionary containing:
        - filepath: Path to generated chart image
        - chart_type: Type of chart generated
        - status: Success or error status
    
    Example:
        >>> result = await query_database("Show revenue by month", user_id=1)
        >>> chart = await generate_chart(
        ...     data=result['rows'],
        ...     chart_type='line',
        ...     title='Monthly Revenue'
        ... )
        >>> print(f"Chart saved to: {chart['filepath']}")
    """
    try:
        filepath = chart_generator.generate_chart(
            data=data,
            chart_type=chart_type,
            title=title,
            x_column=x_column,
            y_column=y_column,
        )
        
        return {
            "filepath": filepath,
            "chart_type": chart_type or "auto-detected",
            "status": "success",
        }
        
    except ValueError as e:
        return {
            "error": str(e),
            "status": "error",
        }
    except Exception as e:
        return {
            "error": f"Failed to generate chart: {str(e)}",
            "status": "error",
        }


@mcp.tool()
async def create_table_image(
    data: list[dict[str, Any]],
    title: str | None = None,
    max_rows: int = 20,
) -> dict[str, Any]:
    """
    Create a table image from query results.
    
    This tool generates a formatted table image for presenting data.
    
    Args:
        data: List of dictionaries containing query results
        title: Table title
        max_rows: Maximum rows to display (default: 20)
    
    Returns:
        Dictionary containing:
        - filepath: Path to generated table image
        - rows_displayed: Number of rows in the table
        - status: Success or error status
    
    Example:
        >>> result = await query_database("Show top customers", user_id=1)
        >>> table = await create_table_image(
        ...     data=result['rows'],
        ...     title='Top 10 Customers',
        ...     max_rows=10
        ... )
        >>> print(f"Table saved to: {table['filepath']}")
    """
    try:
        filepath = chart_generator.create_table_image(
            data=data,
            title=title,
            max_rows=max_rows,
        )
        
        return {
            "filepath": filepath,
            "rows_displayed": min(len(data), max_rows),
            "total_rows": len(data),
            "status": "success",
        }
        
    except ValueError as e:
        return {
            "error": str(e),
            "status": "error",
        }
    except Exception as e:
        return {
            "error": f"Failed to create table: {str(e)}",
            "status": "error",
        }


@mcp.tool()
async def get_query_history(
    user_id: int,
    limit: int = 20,
    status: str | None = None,
) -> dict[str, Any]:
    """
    Get recent query history for a user.
    
    Args:
        user_id: User ID
        limit: Maximum number of queries to return (default: 20)
        status: Filter by status: 'success', 'failed', or None for all
    
    Returns:
        Dictionary containing:
        - queries: List of recent queries
        - total: Total number of queries returned
        - status: Success or error status
    
    Example:
        >>> history = await get_query_history(user_id=1, limit=10)
        >>> for query in history['queries']:
        ...     print(f"{query['question']}: {query['status']}")
    """
    async with get_db_session() as session:
        try:
            # Handle status filtering - only apply if valid status provided
            query_status = None
            if status and status != "None" and status.upper() in QueryStatus.__members__:
                query_status = QueryStatus[status.upper()]
            
            queries = await history_manager.get_recent_queries(
                user_id=user_id,
                session=session,
                limit=limit,
                status=query_status,
            )
            
            return {
                "queries": queries,
                "total": len(queries),
                "status": "success",
            }
            
        except Exception as e:
            return {
                "error": f"Failed to get history: {str(e)}",
                "status": "error",
            }


@mcp.tool()
async def get_popular_queries(limit: int = 10, days: int = 30) -> dict[str, Any]:
    """
    Get most frequently executed queries.
    
    Args:
        limit: Maximum number of queries to return (default: 10)
        days: Look back period in days (default: 30)
    
    Returns:
        Dictionary containing:
        - queries: List of popular queries with execution counts
        - period_days: Look back period used
        - status: Success or error status
    
    Example:
        >>> popular = await get_popular_queries(limit=5, days=7)
        >>> for query in popular['queries']:
        ...     print(f"{query['question']}: {query['execution_count']} times")
    """
    async with get_db_session() as session:
        try:
            queries = await history_manager.get_popular_queries(
                session=session,
                limit=limit,
                days=days,
            )
            
            return {
                "queries": queries,
                "period_days": days,
                "status": "success",
            }
            
        except Exception as e:
            return {
                "error": f"Failed to get popular queries: {str(e)}",
                "status": "error",
            }


@mcp.tool()
async def get_user_statistics(user_id: int, days: int = 30) -> dict[str, Any]:
    """
    Get statistics for a user's query activity.
    
    Args:
        user_id: User ID
        days: Look back period in days (default: 30)
    
    Returns:
        Dictionary containing:
        - total_queries: Total number of queries
        - successful_queries: Number of successful queries
        - failed_queries: Number of failed queries
        - success_rate: Success rate percentage
        - avg_execution_time_ms: Average execution time
        - total_rows_returned: Total rows returned
        - status: Success or error status
    
    Example:
        >>> stats = await get_user_statistics(user_id=1, days=7)
        >>> print(f"Success rate: {stats['success_rate']}%")
    """
    async with get_db_session() as session:
        try:
            stats = await history_manager.get_user_statistics(
                user_id=user_id,
                session=session,
                days=days,
            )
            
            return {**stats, "status": "success"}
            
        except Exception as e:
            return {
                "error": f"Failed to get statistics: {str(e)}",
                "status": "error",
            }


@mcp.tool()
async def export_query_results(
    data: list[dict[str, Any]],
    format: str = "csv",
    filename: str | None = None,
    title: str | None = None,
) -> dict[str, Any]:
    """
    Export query results to a file.
    
    Supported formats: csv, excel, pdf, json
    
    Args:
        data: Query results to export
        format: Export format (csv, excel, pdf, json)
        filename: Output filename without extension (auto-generated if None)
        title: Title for the export (used in Excel/PDF)
    
    Returns:
        Dictionary containing:
        - filepath: Path to exported file
        - format: Export format used
        - row_count: Number of rows exported
        - status: Success or error status
    
    Example:
        >>> result = await query_database("Show top customers", user_id=1)
        >>> export = await export_query_results(
        ...     data=result['rows'],
        ...     format='excel',
        ...     title='Top Customers Report'
        ... )
        >>> print(f"Exported to: {export['filepath']}")
    """
    try:
        if format == "csv":
            filepath = await export_to_csv(data, filename)
        elif format == "excel":
            filepath = await export_to_excel(data, filename, title)
        elif format == "pdf":
            filepath = await export_to_pdf(data, filename, title)
        elif format == "json":
            filepath = await export_to_json(data, filename)
        else:
            return {
                "error": f"Unsupported format: {format}",
                "status": "error",
            }
        
        return {
            "filepath": filepath,
            "format": format,
            "row_count": len(data),
            "status": "success",
        }
        
    except ValueError as e:
        return {
            "error": str(e),
            "status": "error",
        }
    except Exception as e:
        return {
            "error": f"Export failed: {str(e)}",
            "status": "error",
        }


@mcp.tool()
async def create_scheduled_report(
    name: str,
    description: str,
    saved_query_id: int,
    schedule_cron: str,
    format: str,
    recipients: list[str],
    user_id: int,
) -> dict[str, Any]:
    """
    Create a new scheduled report.
    
    Args:
        name: Report name
        description: Report description
        saved_query_id: ID of the saved query to run
        schedule_cron: Cron expression (e.g., "0 9 * * *" for daily at 9 AM)
        format: Report format (csv, excel, pdf)
        recipients: List of email addresses to send report to
        user_id: User ID creating the report
    
    Returns:
        Dictionary with created report details
    
    Example:
        >>> report = await create_scheduled_report(
        ...     name="Daily Sales Report",
        ...     description="Daily sales summary",
        ...     saved_query_id=5,
        ...     schedule_cron="0 9 * * *",  # Daily at 9 AM
        ...     format="excel",
        ...     recipients=["manager@example.com"],
        ...     user_id=1
        ... )
    """
    async with get_db_session() as session:
        try:
            # Validate cron expression
            try:
                cron = croniter(schedule_cron, datetime.now(UTC).replace(tzinfo=None))
                next_run = cron.get_next(datetime)
            except Exception as e:
                return {
                    "error": f"Invalid cron expression: {str(e)}",
                    "status": "error",
                }
            
            # Validate format
            try:
                report_format = ReportFormat[format.upper()]
            except KeyError:
                return {
                    "error": f"Invalid format: {format}. Use: csv, excel, or pdf",
                    "status": "error",
                }
            
            # Create scheduled report
            report = ScheduledReport(
                user_id=user_id,
                saved_query_id=saved_query_id,
                name=name,
                description=description,
                schedule_cron=schedule_cron,
                format=report_format,
                recipients=recipients,
                next_run_at=next_run,
                status=ReportStatus.PENDING,
            )
            
            session.add(report)
            await session.commit()
            await session.refresh(report)
            
            return {
                "report_id": report.id,
                "name": report.name,
                "schedule_cron": report.schedule_cron,
                "next_run_at": report.next_run_at.isoformat(),
                "status": "success",
            }
            
        except Exception as e:
            await session.rollback()
            return {
                "error": f"Failed to create report: {str(e)}",
                "status": "error",
            }


@mcp.tool()
async def list_scheduled_reports(user_id: int) -> dict[str, Any]:
    """
    List all scheduled reports for a user.
    
    Args:
        user_id: User ID
    
    Returns:
        Dictionary containing list of scheduled reports
    
    Example:
        >>> reports = await list_scheduled_reports(user_id=1)
        >>> for report in reports['reports']:
        ...     print(f"{report['name']}: {report['schedule_cron']}")
    """
    async with get_db_session() as session:
        try:
            stmt = (
                select(ScheduledReport)
                .where(ScheduledReport.user_id == user_id)
                .order_by(ScheduledReport.created_at.desc())
            )
            result = await session.execute(stmt)
            reports = result.scalars().all()
            
            return {
                "reports": [
                    {
                        "id": r.id,
                        "name": r.name,
                        "description": r.description,
                        "saved_query_id": r.saved_query_id,
                        "schedule_cron": r.schedule_cron,
                        "format": r.format.value,
                        "recipients": r.recipients,
                        "is_active": r.is_active,
                        "last_run_at": r.last_run_at.isoformat() if r.last_run_at else None,
                        "next_run_at": r.next_run_at.isoformat() if r.next_run_at else None,
                        "status": r.status.value,
                        "created_at": r.created_at.isoformat(),
                    }
                    for r in reports
                ],
                "total": len(reports),
                "status": "success",
            }
            
        except Exception as e:
            return {
                "error": f"Failed to list reports: {str(e)}",
                "status": "error",
            }


@mcp.tool()
async def update_scheduled_report(
    report_id: int,
    user_id: int,
    name: str | None = None,
    description: str | None = None,
    schedule_cron: str | None = None,
    format: str | None = None,
    recipients: list[str] | None = None,
    is_active: bool | None = None,
) -> dict[str, Any]:
    """
    Update a scheduled report.
    
    Args:
        report_id: Report ID
        user_id: User ID
        name: New name (optional)
        description: New description (optional)
        schedule_cron: New cron expression (optional)
        format: New format (optional)
        recipients: New recipients list (optional)
        is_active: Active status (optional)
    
    Returns:
        Dictionary with update status
    
    Example:
        >>> result = await update_scheduled_report(
        ...     report_id=5,
        ...     user_id=1,
        ...     schedule_cron="0 10 * * *",  # Change to 10 AM
        ...     is_active=True
        ... )
    """
    async with get_db_session() as session:
        try:
            stmt = select(ScheduledReport).where(
                ScheduledReport.id == report_id,
                ScheduledReport.user_id == user_id,
            )
            result = await session.execute(stmt)
            report = result.scalar_one_or_none()
            
            if not report:
                return {
                    "error": "Report not found or access denied",
                    "status": "error",
                }
            
            # Update fields
            if name is not None:
                report.name = name
            if description is not None:
                report.description = description
            if schedule_cron is not None:
                try:
                    cron = croniter(schedule_cron, datetime.now(UTC).replace(tzinfo=None))
                    report.schedule_cron = schedule_cron
                    report.next_run_at = cron.get_next(datetime)
                except Exception as e:
                    return {
                        "error": f"Invalid cron expression: {str(e)}",
                        "status": "error",
                    }
            if format is not None:
                try:
                    report.format = ReportFormat[format.upper()]
                except KeyError:
                    return {
                        "error": f"Invalid format: {format}",
                        "status": "error",
                    }
            if recipients is not None:
                report.recipients = recipients
            if is_active is not None:
                report.is_active = is_active
            
            report.updated_at = datetime.now(UTC).replace(tzinfo=None)
            await session.commit()
            
            return {
                "report_id": report_id,
                "status": "success",
            }
            
        except Exception as e:
            await session.rollback()
            return {
                "error": f"Failed to update report: {str(e)}",
                "status": "error",
            }


@mcp.tool()
async def delete_scheduled_report(report_id: int, user_id: int) -> dict[str, Any]:
    """
    Delete a scheduled report.
    
    Args:
        report_id: Report ID
        user_id: User ID
    
    Returns:
        Dictionary with deletion status
    
    Example:
        >>> result = await delete_scheduled_report(report_id=5, user_id=1)
    """
    async with get_db_session() as session:
        try:
            stmt = select(ScheduledReport).where(
                ScheduledReport.id == report_id,
                ScheduledReport.user_id == user_id,
            )
            result = await session.execute(stmt)
            report = result.scalar_one_or_none()
            
            if not report:
                return {
                    "error": "Report not found or access denied",
                    "status": "error",
                }
            
            await session.delete(report)
            await session.commit()
            
            return {
                "report_id": report_id,
                "status": "success",
            }
            
        except Exception as e:
            await session.rollback()
            return {
                "error": f"Failed to delete report: {str(e)}",
                "status": "error",
            }


@mcp.tool()
async def trigger_report_now(report_id: int, user_id: int) -> dict[str, Any]:
    """
    Trigger a scheduled report to run immediately.
    
    Args:
        report_id: Report ID
        user_id: User ID
    
    Returns:
        Dictionary with execution status
    
    Example:
        >>> result = await trigger_report_now(report_id=5, user_id=1)
        >>> print(f"Report executed: {result['status']}")
    """
    print(f"🔥 TRIGGER_REPORT_NOW CALLED: report_id={report_id}, user_id={user_id}")
    
    async with get_db_session() as session:
        try:
            # Get the scheduled report
            stmt = select(ScheduledReport).where(
                ScheduledReport.id == report_id,
                ScheduledReport.user_id == user_id,
            )
            result = await session.execute(stmt)
            report = result.scalar_one_or_none()
            
            if not report:
                return {
                    "error": "Report not found or access denied",
                    "status": "error",
                }
            
            # Check if report has a valid saved query
            if not report.saved_query_id:
                return {
                    "error": "Report has no associated query",
                    "status": "error",
                }
            
            # Get the saved query
            stmt = select(SavedQuery).where(SavedQuery.id == report.saved_query_id)
            result = await session.execute(stmt)
            saved_query = result.scalar_one_or_none()
            
            if not saved_query:
                return {
                    "error": "Associated query not found",
                    "status": "error",
                }
            
            # Execute the query using the global executor instance
            from server.query.query_executor import query_executor
            # Use the generated SQL from the saved query
            query_result = await query_executor.execute_query(
                saved_query.generated_sql, 
                user_id, 
                session
            )
            
            # Generate report file and send emails
            try:
                print(f"DEBUG: Starting email generation for report {report_id}")
                import pandas as pd
                import os
                from datetime import datetime
                
                # Import email sender with error handling
                try:
                    from server.scheduler.email_sender import send_report_email
                    print("DEBUG: Email sender imported successfully")
                except Exception as import_error:
                    print(f"DEBUG: Failed to import email sender: {import_error}")
                    # Fallback - just update the report without sending email
                    report.last_run_at = datetime.now(UTC).replace(tzinfo=None)
                    await session.commit()
                    return {
                        "report_id": report_id,
                        "status": "success", 
                        "message": f"Report executed but email disabled due to import error. Retrieved {query_result.get('row_count', 0)} rows.",
                        "execution_time": query_result.get("execution_time_ms"),
                        "row_count": query_result.get("row_count"),
                        "email_status": f"❌ Email disabled: {str(import_error)}",
                        "recipients_count": len(report.recipients)
                    }
                
                # Convert query results to DataFrame
                df = pd.DataFrame(query_result.get("rows", []))
                
                if df.empty:
                    return {
                        "error": "Query returned no data to report",
                        "status": "error",
                    }
                
                # Create reports directory if it doesn't exist
                reports_dir = "/tmp/reports"
                os.makedirs(reports_dir, exist_ok=True)
                
                # Generate report filename with timestamp
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                report_filename = f"report_{report_id}_{timestamp}.csv"
                report_path = os.path.join(reports_dir, report_filename)
                
                # Save as CSV
                df.to_csv(report_path, index=False)
                
                # Send email to all recipients
                email_sent_count = 0
                email_errors = []
                
                # Send email with the correct function signature
                try:
                    # Debug: Check email settings
                    from shared.config import settings
                    print(f"DEBUG: Email settings - HOST: {settings.email_smtp_host}, USER: {settings.email_username}, FROM_NAME: {getattr(settings, 'email_from_name', None)}")
                    
                    email_result = await send_report_email(
                        recipients=report.recipients,
                        subject=f"Scheduled Report: {report.name}",
                        report_name=report.name,
                        description=report.description or "Scheduled Report",
                        data=query_result.get("rows", []),
                        attachment_path=report_path,
                        format="csv"
                    )
                    
                    print(f"DEBUG: Email result: {email_result}")
                    
                    if email_result.get("status") == "success":
                        email_sent_count = len(report.recipients)
                    else:
                        email_errors.append(f"Email failed: {email_result.get('error', 'Unknown error')}")
                        
                except Exception as email_error:
                    email_errors.append(f"Failed to send emails: {str(email_error)}")
                    print(f"DEBUG: Email exception: {email_error}")
                    import traceback
                    print(f"DEBUG: Full traceback: {traceback.format_exc()}")
                
                # Update last run time
                report.last_run_at = datetime.now(UTC).replace(tzinfo=None)
                await session.commit()
                
                # Clean up temporary file
                try:
                    os.remove(report_path)
                except:
                    pass
                
                # Prepare status message
                if email_sent_count > 0:
                    email_status = f"✅ Successfully sent emails to {email_sent_count} recipients"
                    if email_errors:
                        email_status += f" (Failed: {len(email_errors)})"
                else:
                    email_status = f"❌ Failed to send any emails. Errors: {'; '.join(email_errors[:3])}"
                
                return {
                    "report_id": report_id,
                    "status": "success",
                    "message": f"Report executed successfully. Retrieved {query_result.get('row_count', 0)} rows. {email_status}",
                    "execution_time": query_result.get("execution_time_ms"),
                    "row_count": query_result.get("row_count"),
                    "email_status": email_status,
                    "emails_sent": email_sent_count,
                    "email_errors": email_errors,
                    "recipients_count": len(report.recipients)
                }
                
            except Exception as email_error:
                # If email fails, still update the report run time but note the email failure
                report.last_run_at = datetime.now(UTC).replace(tzinfo=None)
                await session.commit()
                
                return {
                    "report_id": report_id,
                    "status": "partial_success",
                    "message": f"Report executed but email failed. Retrieved {query_result.get('row_count', 0)} rows.",
                    "execution_time": query_result.get("execution_time_ms"),
                    "row_count": query_result.get("row_count"),
                    "email_status": f"❌ Email failed: {str(email_error)}",
                    "emails_sent": 0,
                    "recipients_count": len(report.recipients)
                }
            
        except Exception as e:
            await session.rollback()
            import traceback
            error_details = traceback.format_exc()
            print(f"Report execution error: {error_details}")  # For debugging
            return {
                "error": f"Failed to execute report: {str(e)}",
                "status": "error",
            }


if __name__ == "__main__":
    # Initialize Redis cache (synchronous)
    from server.cache import cache
    cache.initialize()
    print("✅ Redis cache initialized")
    
    # Note: Database will initialize lazily on first use
    # This avoids event loop conflicts with FastMCP's event loop
    print("✅ Database will initialize on first query")
    
    # Run the MCP server (stdio transport by default)
    print(f"✅ Starting MCP Server on stdio transport")
    mcp.run()
