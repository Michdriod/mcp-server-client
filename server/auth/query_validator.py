"""
SQL query validator for security and safety.
Prevents SQL injection and dangerous operations.
"""
import re
from typing import Optional

import sqlparse
from sqlparse.sql import Statement
from sqlparse.tokens import Keyword, DML


class QueryValidationError(Exception):
    """Raised when a query fails validation."""
    pass


class QueryValidator:
    """Validates SQL queries for security and safety."""
    
    # Dangerous SQL keywords that should be blocked
    FORBIDDEN_KEYWORDS = {
        "DROP",
        "DELETE",
        "UPDATE",
        "INSERT",
        "ALTER",
        "CREATE",
        "TRUNCATE",
        "REPLACE",
        "GRANT",
        "REVOKE",
        "COMMIT",
        "ROLLBACK",
        "SAVEPOINT",
        "EXEC",
        "EXECUTE",
        "CALL",
    }
    
    # Dangerous patterns that could indicate SQL injection
    SUSPICIOUS_PATTERNS = [
        r";\s*DROP",  # Chained DROP statements
        r";\s*DELETE",  # Chained DELETE statements
        r"--",  # SQL comments (could hide malicious code)
        r"/\*.*\*/",  # Block comments
        r"xp_cmdshell",  # Command execution
        r"INTO\s+OUTFILE",  # File writes
        r"INTO\s+DUMPFILE",  # File writes
        r"LOAD_FILE",  # File reads
        r"UNION.*SELECT",  # UNION-based injection
    ]
    
    @staticmethod
    def validate_query(sql: str, allow_write: bool = False) -> tuple[bool, Optional[str]]:
        """
        Validate SQL query for security and safety.
        
        Args:
            sql: SQL query to validate
            allow_write: Whether to allow write operations (INSERT, UPDATE, DELETE)
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not sql or not sql.strip():
            return False, "Empty query"
        
        # Normalize whitespace
        sql_upper = sql.upper()
        sql_normalized = " ".join(sql.split())
        
        # Check for forbidden keywords
        if not allow_write:
            for keyword in QueryValidator.FORBIDDEN_KEYWORDS:
                # Use word boundaries to avoid false positives (e.g., "DROP" in "BACKDROP")
                pattern = r"\b" + keyword + r"\b"
                if re.search(pattern, sql_upper):
                    return False, f"Forbidden keyword: {keyword}. Only SELECT queries are allowed."
        
        # Check for suspicious patterns
        for pattern in QueryValidator.SUSPICIOUS_PATTERNS:
            if re.search(pattern, sql_upper, re.IGNORECASE):
                return False, f"Suspicious pattern detected: {pattern}"
        
        # Parse SQL to check structure
        try:
            parsed = sqlparse.parse(sql_normalized)
            if not parsed:
                return False, "Could not parse SQL query"
            
            # Check number of statements (should be exactly 1)
            if len(parsed) > 1:
                return False, "Multiple SQL statements not allowed"
            
            statement: Statement = parsed[0]
            
            # Get the statement type
            stmt_type = statement.get_type()
            
            if not allow_write and stmt_type != "SELECT":
                return False, f"Only SELECT queries allowed, got: {stmt_type}"
            
        except Exception as e:
            return False, f"SQL parsing error: {str(e)}"
        
        return True, None
    
    @staticmethod
    def sanitize_table_name(table_name: str) -> str:
        """
        Sanitize table name to prevent SQL injection.
        
        Args:
            table_name: Table name to sanitize
        
        Returns:
            Sanitized table name
        
        Raises:
            QueryValidationError: If table name is invalid
        """
        # Allow only alphanumeric, underscore, and dot (for schema.table)
        if not re.match(r"^[a-zA-Z0-9_\.]+$", table_name):
            raise QueryValidationError(
                f"Invalid table name: {table_name}. Only alphanumeric and underscore allowed."
            )
        
        return table_name
    
    @staticmethod
    def sanitize_column_name(column_name: str) -> str:
        """
        Sanitize column name to prevent SQL injection.
        
        Args:
            column_name: Column name to sanitize
        
        Returns:
            Sanitized column name
        
        Raises:
            QueryValidationError: If column name is invalid
        """
        # Allow only alphanumeric and underscore
        if not re.match(r"^[a-zA-Z0-9_]+$", column_name):
            raise QueryValidationError(
                f"Invalid column name: {column_name}. Only alphanumeric and underscore allowed."
            )
        
        return column_name
    
    @staticmethod
    def extract_tables_from_query(sql: str) -> list[str]:
        """
        Extract table names from SQL query.
        
        Args:
            sql: SQL query
        
        Returns:
            List of table names found in the query
        """
        tables = []
        
        try:
            parsed = sqlparse.parse(sql)
            if not parsed:
                return tables
            
            statement = parsed[0]
            
            # Extract FROM clause tables
            from_seen = False
            for token in statement.tokens:
                if from_seen:
                    if token.ttype is Keyword:
                        break
                    # Get table name
                    if hasattr(token, "get_real_name"):
                        table_name = token.get_real_name()
                        if table_name:
                            tables.append(table_name)
                    elif not token.is_whitespace:
                        # Handle simple table names
                        table_str = str(token).strip()
                        if table_str and not table_str.upper() in ["AS", "ON", "JOIN", "LEFT", "RIGHT", "INNER", "OUTER"]:
                            # Remove aliases
                            table_name = table_str.split()[0]
                            if table_name:
                                tables.append(table_name)
                
                if token.ttype is Keyword and token.value.upper() == "FROM":
                    from_seen = True
            
        except Exception:
            # If parsing fails, return empty list
            pass
        
        return list(set(tables))  # Remove duplicates
    
    @staticmethod
    def estimate_query_cost(sql: str) -> dict:
        """
        Estimate query cost/complexity.
        
        Args:
            sql: SQL query
        
        Returns:
            Dictionary with cost estimates
        """
        sql_upper = sql.upper()
        
        cost = {
            "has_joins": "JOIN" in sql_upper,
            "has_subqueries": "SELECT" in sql_upper[sql_upper.find("FROM"):] if "FROM" in sql_upper else False,
            "has_aggregations": any(agg in sql_upper for agg in ["COUNT", "SUM", "AVG", "MIN", "MAX", "GROUP BY"]),
            "has_order_by": "ORDER BY" in sql_upper,
            "estimated_complexity": "low",
        }
        
        # Calculate complexity score
        complexity_score = 0
        if cost["has_joins"]:
            complexity_score += 2
        if cost["has_subqueries"]:
            complexity_score += 3
        if cost["has_aggregations"]:
            complexity_score += 1
        if cost["has_order_by"]:
            complexity_score += 1
        
        if complexity_score >= 5:
            cost["estimated_complexity"] = "high"
        elif complexity_score >= 3:
            cost["estimated_complexity"] = "medium"
        
        return cost


# Convenience instance
validator = QueryValidator()
