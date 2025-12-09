"""
Query executor with timeout, pagination, and error handling.
"""
import asyncio
from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from server.auth import rbac, validator, QueryValidationError
from server.cache import cache
from server.db.models import QueryHistory, QueryStatus
from shared.config import settings


class QueryExecutor:
    """Executes SQL queries with safety controls and logging."""
    
    async def execute_query(
        self,
        sql: str,
        user_id: int,
        session: AsyncSession,
        params: Optional[dict] = None,
        cache_results: bool = True,
    ) -> dict[str, Any]:
        """
        Execute SQL query with timeout and safety checks.
        
        Args:
            sql: SQL query to execute
            user_id: User ID executing the query
            session: Database session
            params: Query parameters (optional)
            cache_results: Whether to cache results (default: True)
        
        Returns:
            Dictionary with results, metadata, and execution stats
        
        Raises:
            QueryValidationError: If query is invalid or unsafe
            PermissionError: If user lacks permission
            TimeoutError: If query exceeds timeout
        """
        start_time = datetime.utcnow()
        
        # 1. Validate SQL
        is_valid, error_msg = validator.validate_query(sql, allow_write=False)
        if not is_valid:
            await self._log_query_failure(
                session, user_id, sql, f"Validation failed: {error_msg}"
            )
            raise QueryValidationError(error_msg)
        
        # 2. Extract tables from query
        tables = validator.extract_tables_from_query(sql)
        if not tables:
            raise QueryValidationError("Could not determine tables from query")
        
        # 3. Check permissions for all tables
        for table in tables:
            has_access, permissions = await rbac.check_table_access(
                user_id, "public", table, session
            )
            if not has_access:
                await self._log_query_failure(
                    session, user_id, sql, f"Access denied to table: {table}"
                )
                raise PermissionError(f"Access denied to table: {table}")
            
            # Apply row-level security if needed
            if permissions and permissions.get("row_filter"):
                sql = await rbac.apply_row_level_security(
                    user_id, "public", table, sql, session
                )
        
        # 4. Check cache first
        if cache_results:
            cached_result = await cache.get_query_result(sql, params)
            if cached_result is not None:
                return {
                    "rows": cached_result,
                    "row_count": len(cached_result),
                    "columns": list(cached_result[0].keys()) if cached_result else [],
                    "execution_time_ms": 0,
                    "cached": True,
                    "sql": sql,
                }
        
        # 5. Execute query with timeout
        try:
            result = await asyncio.wait_for(
                self._execute_with_limit(session, sql, params),
                timeout=settings.query_timeout_seconds,
            )
        except asyncio.TimeoutError:
            await self._log_query_failure(
                session, user_id, sql, "Query timeout exceeded"
            )
            raise TimeoutError(
                f"Query exceeded timeout of {settings.query_timeout_seconds} seconds"
            )
        except Exception as e:
            await self._log_query_failure(session, user_id, sql, str(e))
            raise
        
        # 6. Convert to list of dicts
        rows = []
        columns = result.keys() if result.rowcount > 0 else []
        
        for row in result.fetchall():
            row_dict = dict(zip(columns, row))
            # Convert non-serializable types
            for key, value in row_dict.items():
                if isinstance(value, datetime):
                    row_dict[key] = value.isoformat()
                elif isinstance(value, Decimal):
                    row_dict[key] = float(value)
            rows.append(row_dict)
        
        # 7. Calculate execution time
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # 8. Cache results
        if cache_results and rows:
            await cache.set_query_result(sql, rows, params)
        
        # 9. Log successful query
        await self._log_query_success(
            session, user_id, sql, len(rows), execution_time
        )
        
        return {
            "rows": rows,
            "row_count": len(rows),
            "columns": list(columns),
            "execution_time_ms": round(execution_time, 2),
            "cached": False,
            "sql": sql,
        }
    
    async def _execute_with_limit(
        self,
        session: AsyncSession,
        sql: str,
        params: Optional[dict] = None,
    ):
        """Execute query with result limit."""
        # Add LIMIT if not present
        sql_upper = sql.upper()
        if "LIMIT" not in sql_upper:
            sql = f"{sql.rstrip(';')} LIMIT {settings.max_query_results}"
        
        # Execute query
        if params:
            result = await session.execute(text(sql), params)
        else:
            result = await session.execute(text(sql))
        
        return result
    
    async def _log_query_success(
        self,
        session: AsyncSession,
        user_id: int,
        sql: str,
        row_count: int,
        execution_time_ms: float,
    ) -> None:
        """Log successful query execution."""
        history = QueryHistory(
            user_id=user_id,
            question="",  # Will be filled by MCP server
            generated_sql=sql,
            status=QueryStatus.SUCCESS,
            result_rows=row_count,
            execution_time_ms=execution_time_ms,
        )
        session.add(history)
        await session.commit()
    
    async def _log_query_failure(
        self,
        session: AsyncSession,
        user_id: int,
        sql: str,
        error_message: str,
    ) -> None:
        """Log failed query execution."""
        history = QueryHistory(
            user_id=user_id,
            question="",
            generated_sql=sql,
            status=QueryStatus.FAILED,
            error_message=error_message,
        )
        session.add(history)
        await session.commit()
    
    async def explain_query(
        self,
        sql: str,
        session: AsyncSession,
    ) -> dict[str, Any]:
        """
        Get query execution plan using EXPLAIN.
        
        Args:
            sql: SQL query to explain
            session: Database session
        
        Returns:
            Query execution plan
        """
        explain_sql = f"EXPLAIN (FORMAT JSON) {sql}"
        result = await session.execute(text(explain_sql))
        plan = result.fetchone()[0]
        
        return {
            "query": sql,
            "execution_plan": plan,
            "estimated_cost": self._extract_cost(plan),
        }
    
    @staticmethod
    def _extract_cost(plan: list[dict]) -> dict[str, float]:
        """Extract cost estimates from execution plan."""
        if not plan or not isinstance(plan, list):
            return {}
        
        first_plan = plan[0].get("Plan", {})
        return {
            "startup_cost": first_plan.get("Startup Cost", 0),
            "total_cost": first_plan.get("Total Cost", 0),
            "estimated_rows": first_plan.get("Plan Rows", 0),
        }


# Global executor instance
query_executor = QueryExecutor()
