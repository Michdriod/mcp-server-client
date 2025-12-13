"""
Report scheduler for executing scheduled queries and generating reports.
"""
import asyncio
from datetime import datetime, timedelta, UTC
from typing import Any

from celery import shared_task
from croniter import croniter
from sqlalchemy import select, and_

from server.celery_app import celery_app
from server.db.connection import DatabaseConnection
from server.db.models import ScheduledReport, ReportStatus, QueryHistory, SavedQuery
from server.query.query_executor import query_executor
from server.tools.exporters import export_to_csv, export_to_excel, export_to_pdf
from server.scheduler.email_sender import send_report_email
from shared.config import settings


db_connection = DatabaseConnection()


@shared_task(bind=True, name="server.scheduler.report_scheduler.check_and_run_scheduled_reports")
def check_and_run_scheduled_reports(self):
    """
    Check for scheduled reports that need to run and execute them.
    Called every minute by Celery Beat.
    """
    return asyncio.run(_check_and_run_scheduled_reports_async())


async def _check_and_run_scheduled_reports_async():
    """Async implementation of check_and_run_scheduled_reports."""
    await db_connection.connect()
    
    try:
        async with db_connection.get_session() as session:
            # Find active reports that are due to run
            now = datetime.now(UTC).replace(tzinfo=None)
            
            stmt = select(ScheduledReport).where(
                and_(
                    ScheduledReport.is_active == True,
                    ScheduledReport.next_run_at <= now,
                )
            )
            
            result = await session.execute(stmt)
            reports = result.scalars().all()
            
            executed_count = 0
            
            for report in reports:
                try:
                    # Execute the report
                    await _execute_scheduled_report(report, session)
                    executed_count += 1
                    
                    # Update next run time
                    cron = croniter(report.schedule_cron, now)
                    report.next_run_at = cron.get_next(datetime)
                    report.last_run_at = now
                    report.status = ReportStatus.COMPLETED
                    
                except Exception as e:
                    print(f"Error executing report {report.id}: {e}")
                    report.status = ReportStatus.FAILED
                
                await session.commit()
            
            return {
                "checked_at": now.isoformat(),
                "reports_found": len(reports),
                "reports_executed": executed_count,
            }
    
    finally:
        await db_connection.disconnect()


async def _execute_scheduled_report(report: ScheduledReport, session):
    """Execute a single scheduled report."""
    # Load the saved query
    if report.saved_query_id:
        stmt = select(SavedQuery).where(SavedQuery.id == report.saved_query_id)
        result = await session.execute(stmt)
        saved_query = result.scalar_one_or_none()
        
        if not saved_query:
            raise ValueError(f"Saved query {report.saved_query_id} not found")
        
        sql = saved_query.sql_query
    else:
        raise ValueError("Report has no associated saved query")
    
    # Execute the query
    query_result = await query_executor.execute_query(
        sql=sql,
        user_id=report.user_id,
        session=session,
        cache_results=False,  # Don't cache scheduled report results
    )
    
    # Export to requested format
    export_path = await _export_report(
        report=report,
        data=query_result["rows"],
        format=report.format.value,
    )
    
    # Send email if recipients specified
    if report.recipients and len(report.recipients) > 0:
        await send_report_email(
            recipients=report.recipients,
            subject=f"Scheduled Report: {report.name}",
            report_name=report.name,
            description=report.description or "",
            data=query_result["rows"],
            attachment_path=export_path,
            format=report.format.value,
        )


async def _export_report(report: ScheduledReport, data: list[dict], format: str) -> str:
    """Export report data to the specified format."""
    filename = f"{report.name.replace(' ', '_')}_{datetime.now(UTC).strftime('%Y%m%d_%H%M%S')}"
    
    if format == "csv":
        return await export_to_csv(data, filename)
    elif format == "excel":
        return await export_to_excel(data, filename, title=report.name)
    elif format == "pdf":
        return await export_to_pdf(data, filename, title=report.name)
    else:
        raise ValueError(f"Unsupported format: {format}")


@shared_task(bind=True, name="server.scheduler.report_scheduler.execute_report_now")
def execute_report_now(self, report_id: int, user_id: int):
    """
    Execute a scheduled report immediately (manual trigger).
    
    Args:
        report_id: ID of the scheduled report
        user_id: User ID triggering the report
    
    Returns:
        Dictionary with execution results
    """
    return asyncio.run(_execute_report_now_async(report_id, user_id))


async def _execute_report_now_async(report_id: int, user_id: int):
    """Async implementation of execute_report_now."""
    await db_connection.connect()
    
    try:
        async with db_connection.get_session() as session:
            # Load the report
            stmt = select(ScheduledReport).where(
                and_(
                    ScheduledReport.id == report_id,
                    ScheduledReport.user_id == user_id,
                )
            )
            result = await session.execute(stmt)
            report = result.scalar_one_or_none()
            
            if not report:
                return {
                    "error": "Report not found or access denied",
                    "status": "error",
                }
            
            # Execute the report
            try:
                await _execute_scheduled_report(report, session)
                
                # Update last run time
                report.last_run_at = datetime.now(UTC).replace(tzinfo=None)
                report.status = ReportStatus.COMPLETED
                await session.commit()
                
                return {
                    "report_id": report_id,
                    "report_name": report.name,
                    "executed_at": report.last_run_at.isoformat(),
                    "status": "success",
                }
                
            except Exception as e:
                report.status = ReportStatus.FAILED
                await session.commit()
                return {
                    "error": str(e),
                    "status": "error",
                }
    
    finally:
        await db_connection.disconnect()


@shared_task(bind=True, name="server.scheduler.report_scheduler.cleanup_old_query_history")
def cleanup_old_query_history(self, days_to_keep: int = 90):
    """
    Clean up old query history records.
    
    Args:
        days_to_keep: Number of days to keep history (default: 90)
    
    Returns:
        Number of records deleted
    """
    return asyncio.run(_cleanup_old_query_history_async(days_to_keep))


async def _cleanup_old_query_history_async(days_to_keep: int):
    """Async implementation of cleanup_old_query_history."""
    await db_connection.connect()
    
    try:
        async with db_connection.get_session() as session:
            cutoff_date = datetime.now(UTC).replace(tzinfo=None) - timedelta(days=days_to_keep)
            
            # Delete old records
            stmt = select(QueryHistory).where(
                QueryHistory.created_at < cutoff_date
            )
            result = await session.execute(stmt)
            old_records = result.scalars().all()
            
            count = len(old_records)
            
            for record in old_records:
                await session.delete(record)
            
            await session.commit()
            
            return {
                "deleted_count": count,
                "cutoff_date": cutoff_date.isoformat(),
                "status": "success",
            }
    
    finally:
        await db_connection.disconnect()
