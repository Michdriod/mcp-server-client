"""
Role-Based Access Control (RBAC) implementation.
Manages user roles and permissions for database access.
"""
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from server.cache import cache
from server.db.models import RolePermission, User, UserRole


class RBACManager:
    """Manages role-based access control for database operations."""
    
    @staticmethod
    async def check_table_access(
        user_id: int,
        database: str,
        table: str,
        session: AsyncSession,
    ) -> tuple[bool, Optional[dict]]:
        """
        Check if user has access to a specific table.
        
        Args:
            user_id: User ID
            database: Database name
            table: Table name
            session: Database session
        
        Returns:
            Tuple of (has_access, permissions_dict)
        """
        # Check cache first
        cached_perms = await cache.get_user_permissions(user_id, database, table)
        if cached_perms is not None:
            return cached_perms.get("can_read", False), cached_perms
        
        # Fetch user and their role
        user_result = await session.execute(
            select(User).where(User.id == user_id, User.is_active == True)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            return False, None
        
        # Admins have access to everything
        if user.role == UserRole.ADMIN:
            permissions = {
                "can_read": True,
                "allowed_columns": None,  # All columns
                "row_filter": None,
            }
            await cache.set_user_permissions(user_id, database, table, permissions)
            return True, permissions
        
        # Check specific table permissions
        perm_result = await session.execute(
            select(RolePermission).where(
                RolePermission.user_id == user_id,
                RolePermission.database_name == database,
                RolePermission.table_name == table,
            )
        )
        permission = perm_result.scalar_one_or_none()
        
        if not permission:
            # No explicit permission = no access (deny by default)
            return False, None
        
        permissions = {
            "can_read": permission.can_read,
            "allowed_columns": permission.allowed_columns,
            "row_filter": permission.row_filter,
        }
        
        # Cache the permissions
        await cache.set_user_permissions(user_id, database, table, permissions)
        
        return permission.can_read, permissions
    
    @staticmethod
    async def get_user_role(user_id: int, session: AsyncSession) -> Optional[UserRole]:
        """
        Get user's role.
        
        Args:
            user_id: User ID
            session: Database session
        
        Returns:
            User's role or None if user not found
        """
        result = await session.execute(
            select(User.role).where(User.id == user_id, User.is_active == True)
        )
        return result.scalar_one_or_none()
    
    @staticmethod
    async def is_admin(user_id: int, session: AsyncSession) -> bool:
        """
        Check if user is an admin.
        
        Args:
            user_id: User ID
            session: Database session
        
        Returns:
            True if user is admin, False otherwise
        """
        role = await RBACManager.get_user_role(user_id, session)
        return role == UserRole.ADMIN
    
    @staticmethod
    async def get_accessible_tables(
        user_id: int, database: str, session: AsyncSession
    ) -> list[str]:
        """
        Get list of tables user can access.
        
        Args:
            user_id: User ID
            database: Database name
            session: Database session
        
        Returns:
            List of table names user can access
        """
        # Check if admin (access to all tables)
        if await RBACManager.is_admin(user_id, session):
            # Return special marker for "all tables"
            return ["*"]
        
        # Get explicitly granted tables
        result = await session.execute(
            select(RolePermission.table_name).where(
                RolePermission.user_id == user_id,
                RolePermission.database_name == database,
                RolePermission.can_read == True,
            )
        )
        
        return [row[0] for row in result.all()]
    
    @staticmethod
    async def apply_row_level_security(
        user_id: int,
        database: str,
        table: str,
        base_sql: str,
        session: AsyncSession,
    ) -> str:
        """
        Apply row-level security filters to SQL query.
        
        Args:
            user_id: User ID
            database: Database name
            table: Table name
            base_sql: Base SQL query
            session: Database session
        
        Returns:
            Modified SQL with row-level filters applied
        """
        has_access, permissions = await RBACManager.check_table_access(
            user_id, database, table, session
        )
        
        if not has_access or not permissions:
            raise PermissionError(f"User {user_id} has no access to {database}.{table}")
        
        row_filter = permissions.get("row_filter")
        if not row_filter:
            return base_sql
        
        # Apply row filter to WHERE clause
        if "WHERE" in base_sql.upper():
            # Append to existing WHERE clause
            return base_sql.replace("WHERE", f"WHERE ({row_filter}) AND", 1)
        else:
            # Add WHERE clause
            # Find the position to insert (before ORDER BY, LIMIT, etc.)
            insert_pos = len(base_sql)
            for keyword in ["ORDER BY", "LIMIT", "OFFSET", "GROUP BY", "HAVING"]:
                pos = base_sql.upper().find(keyword)
                if pos != -1:
                    insert_pos = min(insert_pos, pos)
            
            return (
                base_sql[:insert_pos].rstrip()
                + f" WHERE {row_filter} "
                + base_sql[insert_pos:]
            )
    
    @staticmethod
    async def filter_columns(
        user_id: int,
        database: str,
        table: str,
        columns: list[str],
        session: AsyncSession,
    ) -> list[str]:
        """
        Filter columns based on user permissions.
        
        Args:
            user_id: User ID
            database: Database name
            table: Table name
            columns: Requested columns
            session: Database session
        
        Returns:
            Filtered list of allowed columns
        """
        has_access, permissions = await RBACManager.check_table_access(
            user_id, database, table, session
        )
        
        if not has_access or not permissions:
            raise PermissionError(f"User {user_id} has no access to {database}.{table}")
        
        allowed_columns = permissions.get("allowed_columns")
        if allowed_columns is None:
            # None means all columns are allowed
            return columns
        
        # Filter to only allowed columns
        allowed_set = set(allowed_columns)
        return [col for col in columns if col in allowed_set]


# Convenience instance
rbac = RBACManager()
