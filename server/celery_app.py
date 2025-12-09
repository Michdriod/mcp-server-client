"""
Celery application for background tasks and scheduled reports.
"""
from celery import Celery
from celery.schedules import crontab

from shared.config import settings


# Initialize Celery app
celery_app = Celery(
    "query_assistant",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "server.scheduler.report_scheduler",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",
        "visibility_timeout": 3600,
    },
    
    # Task execution settings
    task_always_eager=False,  # Set to True for testing (synchronous execution)
    task_eager_propagates=True,
    task_ignore_result=False,
    task_track_started=True,
    task_time_limit=300,  # 5 minutes max per task
    task_soft_time_limit=240,  # Soft limit at 4 minutes
    
    # Worker settings
    worker_prefetch_multiplier=4,
    worker_max_tasks_per_child=1000,
    
    # Beat scheduler settings
    beat_schedule={
        # Example: Check for scheduled reports every minute
        "check-scheduled-reports": {
            "task": "server.scheduler.report_scheduler.check_and_run_scheduled_reports",
            "schedule": crontab(minute="*"),  # Every minute
        },
        # Cleanup old query history (daily at 2 AM)
        "cleanup-old-history": {
            "task": "server.scheduler.report_scheduler.cleanup_old_query_history",
            "schedule": crontab(hour=2, minute=0),  # Daily at 2 AM
        },
    },
)

# Task routes (optional - for multiple queues)
celery_app.conf.task_routes = {
    "server.scheduler.report_scheduler.*": {"queue": "reports"},
    "server.scheduler.email_sender.*": {"queue": "emails"},
}


if __name__ == "__main__":
    celery_app.start()
