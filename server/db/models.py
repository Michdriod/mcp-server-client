"""
SQLAlchemy ORM models for database tables.
"""
from datetime import datetime, UTC
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


class UserRole(str, PyEnum):
    """User roles for RBAC."""
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"


class QueryStatus(str, PyEnum):
    """Status of query execution."""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"


class ReportFormat(str, PyEnum):
    """Report output formats."""
    PDF = "pdf"
    CSV = "csv"
    EXCEL = "excel"
    PNG = "png"


class ReportStatus(str, PyEnum):
    """Status of scheduled report."""
    PENDING = "pending"
    ACTIVE = "active"
    PAUSED = "paused"
    FAILED = "failed"


class User(Base):
    """User model with authentication and role information."""
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="viewer")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), onupdate=lambda: datetime.now(UTC).replace(tzinfo=None), nullable=False
    )
    
    # Relationships
    query_history: Mapped[list["QueryHistory"]] = relationship("QueryHistory", back_populates="user")
    saved_queries: Mapped[list["SavedQuery"]] = relationship("SavedQuery", back_populates="user")
    scheduled_reports: Mapped[list["ScheduledReport"]] = relationship("ScheduledReport", back_populates="user")
    permissions: Mapped[list["RolePermission"]] = relationship("RolePermission", back_populates="user")


class QueryHistory(Base):
    """Tracks all executed queries for history and auditing."""
    __tablename__ = "query_history"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    generated_sql: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    result_rows: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    execution_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), nullable=False, index=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="query_history")
    
    __table_args__ = (
        Index("idx_user_created", "user_id", "created_at"),
    )


class SavedQuery(Base):
    """User's saved/favorite queries."""
    __tablename__ = "saved_queries"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    question: Mapped[str] = mapped_column(Text, nullable=False)
    generated_sql: Mapped[str] = mapped_column(Text, nullable=False)
    is_favorite: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), onupdate=lambda: datetime.now(UTC).replace(tzinfo=None), nullable=False
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="saved_queries")
    
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_user_query_name"),
    )


class ScheduledReport(Base):
    """Scheduled reports with cron-like scheduling."""
    __tablename__ = "scheduled_reports"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    saved_query_id: Mapped[int] = mapped_column(Integer, ForeignKey("saved_queries.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    schedule_cron: Mapped[str] = mapped_column(String(100), nullable=False)
    format: Mapped[ReportFormat] = mapped_column(Enum(ReportFormat), nullable=False, default=ReportFormat.CSV)
    recipients: Mapped[list[str]] = mapped_column(JSON, nullable=False)  # List of email addresses
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    status: Mapped[ReportStatus] = mapped_column(Enum(ReportStatus), nullable=False, default=ReportStatus.ACTIVE)
    last_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    next_run_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), onupdate=lambda: datetime.now(UTC).replace(tzinfo=None), nullable=False
    )
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="scheduled_reports")


class RolePermission(Base):
    """Maps users to table/column/row-level permissions."""
    __tablename__ = "role_permissions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    database_name: Mapped[str] = mapped_column(String(100), nullable=False)
    table_name: Mapped[str] = mapped_column(String(100), nullable=False)
    allowed_columns: Mapped[Optional[list[str]]] = mapped_column(JSON, nullable=True)  # None = all columns
    row_filter: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # SQL WHERE clause
    can_read: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="permissions")
    
    __table_args__ = (
        Index("idx_user_table", "user_id", "database_name", "table_name"),
        UniqueConstraint("user_id", "database_name", "table_name", name="uq_user_table_permission"),
    )


class DatabaseConnection(Base):
    """Multi-database connection registry."""
    __tablename__ = "database_connections"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    connection_url: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_by: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(UTC).replace(tzinfo=None), onupdate=lambda: datetime.now(UTC).replace(tzinfo=None), nullable=False
    )
