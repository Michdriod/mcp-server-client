"""
Structured Logging Configuration
"""
import logging
import sys
import json
from datetime import datetime, UTC
from typing import Any, Dict
from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for structured logging"""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)
        
        # Add timestamp
        log_record['timestamp'] = datetime.now(UTC).isoformat()
        
        # Add level
        log_record['level'] = record.levelname
        
        # Add logger name
        log_record['logger'] = record.name
        
        # Add service info
        log_record['service'] = 'database-query-assistant'
        
        # Add trace ID if available
        if hasattr(record, 'trace_id'):
            log_record['trace_id'] = record.trace_id
        
        # Add user ID if available
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id


def setup_logging(level: str = "INFO", json_logs: bool = True) -> None:
    """
    Configure structured logging
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: Whether to use JSON formatting
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers
    root_logger.handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    
    if json_logs:
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(logger)s %(message)s'
        )
    else:
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)


# Query logger for audit trail
query_logger = logging.getLogger('query_audit')


def log_query(user_id: int, query: str, execution_time_ms: float, row_count: int, cached: bool = False) -> None:
    """
    Log query execution for audit trail
    """
    query_logger.info(
        "Query executed",
        extra={
            'user_id': user_id,
            'query': query[:100],  # Truncate long queries
            'execution_time_ms': execution_time_ms,
            'row_count': row_count,
            'cached': cached
        }
    )


# Error logger
error_logger = logging.getLogger('errors')


def log_error(error: Exception, context: Dict[str, Any] = None) -> None:
    """
    Log errors with context
    """
    error_logger.error(
        f"Error occurred: {str(error)}",
        extra={
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context or {}
        },
        exc_info=True
    )
