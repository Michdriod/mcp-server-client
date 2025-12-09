"""
Unit Tests for Query Validator
"""
import pytest
from server.auth.query_validator import QueryValidator, QueryValidationError


@pytest.fixture
def validator():
    """Create validator instance"""
    return QueryValidator()


def test_forbidden_keywords(validator):
    """Test detection of forbidden keywords"""
    # Should raise error for DROP
    with pytest.raises(QueryValidationError, match="Forbidden SQL keyword"):
        validator.validate("DROP TABLE users")
    
    # Should raise error for DELETE
    with pytest.raises(QueryValidationError, match="Forbidden SQL keyword"):
        validator.validate("DELETE FROM users WHERE id=1")
    
    # Should raise error for TRUNCATE
    with pytest.raises(QueryValidationError, match="Forbidden SQL keyword"):
        validator.validate("TRUNCATE TABLE users")


def test_sql_injection(validator):
    """Test detection of SQL injection patterns"""
    # OR 1=1
    with pytest.raises(QueryValidationError, match="SQL injection"):
        validator.validate("SELECT * FROM users WHERE id=1 OR 1=1")
    
    # Union-based injection
    with pytest.raises(QueryValidationError, match="SQL injection"):
        validator.validate("SELECT * FROM users UNION SELECT * FROM passwords")
    
    # Comment-based injection
    with pytest.raises(QueryValidationError, match="SQL injection"):
        validator.validate("SELECT * FROM users WHERE id=1--")


def test_valid_queries(validator):
    """Test that valid queries pass validation"""
    # Simple SELECT
    assert validator.validate("SELECT * FROM users") is True
    
    # SELECT with WHERE
    assert validator.validate("SELECT name, email FROM users WHERE active=true") is True
    
    # SELECT with JOIN
    assert validator.validate("SELECT u.name, o.total FROM users u JOIN orders o ON u.id=o.user_id") is True


def test_extract_tables(validator):
    """Test table extraction from SQL"""
    sql = "SELECT u.name, o.total FROM users u JOIN orders o ON u.id=o.user_id"
    tables = validator.extract_tables(sql)
    
    assert "users" in tables
    assert "orders" in tables


def test_estimate_complexity(validator):
    """Test query complexity estimation"""
    # Simple query
    simple = "SELECT * FROM users"
    assert validator.estimate_complexity(simple) < 5
    
    # Complex query with JOINs
    complex_query = """
    SELECT u.name, COUNT(o.id), SUM(o.total)
    FROM users u
    JOIN orders o ON u.id = o.user_id
    JOIN order_items oi ON o.id = oi.order_id
    WHERE u.active = true
    GROUP BY u.name
    HAVING COUNT(o.id) > 5
    ORDER BY SUM(o.total) DESC
    """
    assert validator.estimate_complexity(complex_query) > 10
