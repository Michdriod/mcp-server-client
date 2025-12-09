"""
Permission management utilities.
Helper functions for managing user permissions.
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.db.models import RolePermission, User, UserRole


async def grant_table_permission(
    user_id: int,
    database: str,
    table: str,
    allowed_columns: Optional[list[str]],
    row_filter: Optional[str],
    session: AsyncSession,
) -> RolePermission:
    """
    Grant table access permission to a user.
    
    Args:
        user_id: User ID
        database: Database name
        table: Table name
        allowed_columns: List of allowed columns (None = all columns)
        row_filter: SQL WHERE clause for row-level security
        session: Database session
    
    Returns:
        Created or updated permission
    """
    # Check if permission already exists
    result = await session.execute(
        select(RolePermission).where(
            RolePermission.user_id == user_id,
            RolePermission.database_name == database,
            RolePermission.table_name == table,
        )
    )
    permission = result.scalar_one_or_none()
    
    if permission:
        # Update existing permission
        permission.allowed_columns = allowed_columns
        permission.row_filter = row_filter
        permission.can_read = True
    else:
        # Create new permission
        permission = RolePermission(
            user_id=user_id,
            database_name=database,
            table_name=table,
            allowed_columns=allowed_columns,
            row_filter=row_filter,
            can_read=True,
        )
        session.add(permission)
    
    await session.commit()
    await session.refresh(permission)
    
    return permission


async def revoke_table_permission(
    user_id: int,
    database: str,
    table: str,
    session: AsyncSession,
) -> bool:
    """
    Revoke table access permission from a user.
    
    Args:
        user_id: User ID
        database: Database name
        table: Table name
        session: Database session
    
    Returns:
        True if permission was revoked, False if not found
    """
    result = await session.execute(
        select(RolePermission).where(
            RolePermission.user_id == user_id,
            RolePermission.database_name == database,
            RolePermission.table_name == table,
        )
    )
    permission = result.scalar_one_or_none()
    
    if permission:
        await session.delete(permission)
        await session.commit()
        return True
    
    return False


async def update_user_role(
    user_id: int,
    new_role: UserRole,
    session: AsyncSession,
) -> Optional[User]:
    """
    Update a user's role.
    
    Args:
        user_id: User ID
        new_role: New role to assign
        session: Database session
    
    Returns:
        Updated user or None if not found
    """
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if user:
        user.role = new_role
        await session.commit()
        await session.refresh(user)
    
    return user


async def get_user_permissions_summary(
    user_id: int,
    session: AsyncSession,
) -> dict:
    """
    Get a summary of all permissions for a user.
    
    Args:
        user_id: User ID
        session: Database session
    
    Returns:
        Dictionary with user info and permissions
    """
    # Get user
    user_result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = user_result.scalar_one_or_none()
    
    if not user:
        return {}
    
    # Get all permissions
    perms_result = await session.execute(
        select(RolePermission).where(RolePermission.user_id == user_id)
    )
    permissions = perms_result.scalars().all()
    
    return {
        "user_id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role.value,
        "is_active": user.is_active,
        "permissions": [
            {
                "database": perm.database_name,
                "table": perm.table_name,
                "can_read": perm.can_read,
                "allowed_columns": perm.allowed_columns,
                "has_row_filter": perm.row_filter is not None,
            }
            for perm in permissions
        ],
    }
