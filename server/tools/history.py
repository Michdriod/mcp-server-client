"""
Query history tracking and retrieval.
"""
from datetime import datetime, timedelta
from typing import Any

from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.models import QueryHistory, QueryStatus


class HistoryManager:
    """Manage query history."""
    
    async def log_query(
        self,
        user_id: int,
        natural_query: str,
        sql_query: str,
        success: bool,
        row_count: int = 0,
        execution_time_ms: float = 0,
        error: str | None = None,
        session: AsyncSession | None = None,
    ) -> None:
        """
        Log a query execution to history.
        
        Args:
            user_id: User ID
            natural_query: Natural language query
            sql_query: Generated SQL query
            success: Whether the query succeeded
            row_count: Number of rows returned
            execution_time_ms: Execution time in milliseconds
            error: Error message if failed
            session: Database session
        """
        if session is None:
            raise ValueError("Database session is required")
        
        try:
            history_entry = QueryHistory(
                user_id=user_id,
                question=natural_query,
                generated_sql=sql_query,
                status="success" if success else "failed",
                result_rows=row_count if success else None,
                execution_time_ms=execution_time_ms if success else None,
                error_message=error if not success else None,
            )
            
            session.add(history_entry)
            await session.flush()  # Don't commit, let the caller handle that
            print(f"✅ Query logged to history (ID: {history_entry.id})")
            
        except Exception as e:
            print(f"⚠️  Failed to log query to history: {e}")
            # Don't raise - logging failures shouldn't break the query
    
    async def get_recent_queries(
        self,
        user_id: int,
        session: AsyncSession,
        limit: int = 20,
        status: QueryStatus | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get recent queries for a user.
        
        Args:
            user_id: User ID
            session: Database session
            limit: Maximum number of queries to return
            status: Filter by query status (optional)
        
        Returns:
            List of query history records
        """
        stmt = (
            select(QueryHistory)
            .where(QueryHistory.user_id == user_id)
            .order_by(desc(QueryHistory.created_at))
            .limit(limit)
        )
        
        if status:
            stmt = stmt.where(QueryHistory.status == status)
        
        result = await session.execute(stmt)
        queries = result.scalars().all()
        
        return [
            {
                "id": q.id,
                "question": q.question,
                "sql": q.generated_sql,
                "status": q.status,
                "result_rows": q.result_rows,
                "execution_time_ms": q.execution_time_ms,
                "error_message": q.error_message,
                "created_at": q.created_at.isoformat(),
            }
            for q in queries
        ]
    
    async def get_query_by_id(
        self,
        query_id: int,
        user_id: int,
        session: AsyncSession,
    ) -> dict[str, Any] | None:
        """
        Get a specific query by ID.
        
        Args:
            query_id: Query history ID
            user_id: User ID (for access control)
            session: Database session
        
        Returns:
            Query history record or None if not found
        """
        stmt = select(QueryHistory).where(
            QueryHistory.id == query_id,
            QueryHistory.user_id == user_id,
        )
        
        result = await session.execute(stmt)
        query = result.scalar_one_or_none()
        
        if not query:
            return None
        
        return {
            "id": query.id,
            "question": query.question,
            "sql": query.generated_sql,
            "status": query.status.value,
            "result_rows": query.result_rows,
            "execution_time_ms": query.execution_time_ms,
            "error_message": query.error_message,
            "created_at": query.created_at.isoformat(),
        }
    
    async def get_popular_queries(
        self,
        session: AsyncSession,
        limit: int = 10,
        days: int = 30,
    ) -> list[dict[str, Any]]:
        """
        Get most frequently executed queries.
        
        Args:
            session: Database session
            limit: Maximum number of queries to return
            days: Look back period in days
        
        Returns:
            List of popular queries with execution counts
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        stmt = (
            select(
                QueryHistory.question,
                QueryHistory.generated_sql,
                func.count(QueryHistory.id).label("execution_count"),
                func.avg(QueryHistory.execution_time_ms).label("avg_execution_time"),
                func.sum(QueryHistory.result_rows).label("total_rows_returned"),
            )
            .where(
                QueryHistory.created_at >= cutoff_date,
                QueryHistory.status == QueryStatus.SUCCESS,
            )
            .group_by(QueryHistory.question, QueryHistory.generated_sql)
            .order_by(desc("execution_count"))
            .limit(limit)
        )
        
        result = await session.execute(stmt)
        queries = result.all()
        
        return [
            {
                "question": q.question,
                "sql": q.generated_sql,
                "execution_count": q.execution_count,
                "avg_execution_time_ms": round(q.avg_execution_time, 2) if q.avg_execution_time else 0,
                "total_rows_returned": q.total_rows_returned or 0,
            }
            for q in queries
        ]
    
    async def get_user_statistics(
        self,
        user_id: int,
        session: AsyncSession,
        days: int = 30,
    ) -> dict[str, Any]:
        """
        Get statistics for a user's query activity.
        
        Args:
            user_id: User ID
            session: Database session
            days: Look back period in days
        
        Returns:
            Dictionary with user statistics
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Total queries
        total_stmt = select(func.count(QueryHistory.id)).where(
            QueryHistory.user_id == user_id,
            QueryHistory.created_at >= cutoff_date,
        )
        total_result = await session.execute(total_stmt)
        total_queries = total_result.scalar() or 0
        
        # Successful queries
        success_stmt = select(func.count(QueryHistory.id)).where(
            QueryHistory.user_id == user_id,
            QueryHistory.created_at >= cutoff_date,
            QueryHistory.status == QueryStatus.SUCCESS,
        )
        success_result = await session.execute(success_stmt)
        successful_queries = success_result.scalar() or 0
        
        # Failed queries
        failed_stmt = select(func.count(QueryHistory.id)).where(
            QueryHistory.user_id == user_id,
            QueryHistory.created_at >= cutoff_date,
            QueryHistory.status == QueryStatus.FAILED,
        )
        failed_result = await session.execute(failed_stmt)
        failed_queries = failed_result.scalar() or 0
        
        # Average execution time
        avg_time_stmt = select(func.avg(QueryHistory.execution_time_ms)).where(
            QueryHistory.user_id == user_id,
            QueryHistory.created_at >= cutoff_date,
            QueryHistory.status == QueryStatus.SUCCESS,
        )
        avg_time_result = await session.execute(avg_time_stmt)
        avg_execution_time = avg_time_result.scalar() or 0
        
        # Total rows returned
        total_rows_stmt = select(func.sum(QueryHistory.result_rows)).where(
            QueryHistory.user_id == user_id,
            QueryHistory.created_at >= cutoff_date,
            QueryHistory.status == QueryStatus.SUCCESS,
        )
        total_rows_result = await session.execute(total_rows_stmt)
        total_rows = total_rows_result.scalar() or 0
        
        return {
            "user_id": user_id,
            "period_days": days,
            "total_queries": total_queries,
            "successful_queries": successful_queries,
            "failed_queries": failed_queries,
            "success_rate": round(successful_queries / total_queries * 100, 2) if total_queries > 0 else 0,
            "avg_execution_time_ms": round(avg_execution_time, 2),
            "total_rows_returned": total_rows,
        }


# Global history manager instance
history_manager = HistoryManager()
