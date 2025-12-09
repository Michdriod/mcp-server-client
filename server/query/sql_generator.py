"""
SQL generation engine using Pydantic AI Agent with Groq.
Converts natural language questions to safe SQL queries.
"""
import hashlib
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict
from pydantic_ai import Agent, RunContext
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from server.auth import validator, QueryValidationError
from server.cache import cache
from shared.config import settings


class SQLGenerationResult(BaseModel):
    """Result from SQL generation."""
    model_config = ConfigDict(extra='ignore')  # Ignore extra fields from LLM
    
    sql: str = Field(description="Generated SQL query")
    tables_used: list[str] = Field(description="Tables referenced in query")
    confidence: float = Field(description="Confidence score 0-1", ge=0.0, le=1.0)
    explanation: str = Field(description="Explanation of what query does")


class SchemaContext(BaseModel):
    """Database schema context for the AI."""
    available_tables: list[str]
    table_schemas: dict[str, list[str]]  # table_name -> column_names
    table_relationships: Optional[dict[str, list[str]]] = None  # table -> foreign keys info
    sample_data: Optional[dict[str, list[dict]]] = None


class SQLGenerator:
    """Generates SQL from natural language using Pydantic AI + Groq."""
    
    def __init__(self):
        """Initialize SQL generator with Pydantic AI agent."""
        self.agent = Agent(
            model=settings.llm_model,
            output_type=SQLGenerationResult,
            instructions=self._build_system_prompt(),
            retries=1,  # Limit retries for faster response
        )
    
    @staticmethod
    def _build_system_prompt() -> str:
        """Build system prompt for SQL generation."""
        return """You are an expert SQL query generator for PostgreSQL databases.

        Your job is to convert natural language questions into safe, efficient SQL queries.

        RULES:
        1. ONLY generate SELECT queries (read-only)
        2. Use proper PostgreSQL syntax
        3. Always use table and column names that exist in the schema
        4. Pay close attention to foreign key relationships when joining tables
        5. When a question involves products, orders, customers, etc., use proper JOINs through the relationship tables
        6. For many-to-many relationships (e.g., orders ↔ products), look for junction tables like order_items
        7. Add WHERE clauses to limit results when appropriate
        8. Use LIMIT to prevent returning too many rows (max 1000)
        9. For date queries, use proper date functions
        10. For aggregations, use GROUP BY when needed
        11. Never use subqueries unless absolutely necessary (prefer JOINs)
        12. Always include column aliases for clarity
        13. Be cautious with LIKE queries (they can be slow)

        SAFETY:
        - Never generate DROP, DELETE, UPDATE, INSERT, ALTER, TRUNCATE commands
        - Always validate table names against available schema
        - Use parameterized queries when dealing with user input
        - Add appropriate WHERE clauses to filter data

        JOINING TABLES:
        - Always check the foreign key relationships provided in the schema
        - For questions like "customers who ordered X", you typically need:
          customers → orders (via customer_id) → order_items (via order_id) → products (via product_id)
        - Use INNER JOIN when you want only matching records
        - Use LEFT JOIN when you want all records from the left table even if no match

        OUTPUT FORMAT:
        Return a SQLGenerationResult with:
        - sql: The complete SQL query
        - tables_used: List of table names used
        - confidence: How confident you are (0.0 to 1.0)
        - explanation: Brief explanation of what the query does

        EXAMPLES:
        Question: "Show me all users"
        Response: {
        "sql": "SELECT id, username, email, created_at FROM users LIMIT 100",
        "tables_used": ["users"],
        "confidence": 0.95,
        "explanation": "Retrieves first 100 users with their basic information"
        }

        Question: "What were sales last month?"
        Response: {
        "sql": "SELECT SUM(amount) as total_sales, COUNT(*) as order_count FROM sales WHERE date >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '1 month') AND date < DATE_TRUNC('month', CURRENT_DATE)",
        "tables_used": ["sales"],
        "confidence": 0.90,
        "explanation": "Calculates total sales amount and number of orders from last month"
        }

        Question: "Top 10 customers by revenue"
        Response: {
        "sql": "SELECT c.id, c.name, SUM(o.amount) as total_revenue FROM customers c JOIN orders o ON c.id = o.customer_id GROUP BY c.id, c.name ORDER BY total_revenue DESC LIMIT 10",
        "tables_used": ["customers", "orders"],
        "confidence": 0.85,
        "explanation": "Finds top 10 customers ranked by their total order revenue"
        }

        Question: "How many customers ordered keyboards?"
        Response: {
        "sql": "SELECT COUNT(DISTINCT c.id) as customer_count FROM customers c JOIN orders o ON c.id = o.customer_id JOIN order_items oi ON o.id = oi.order_id JOIN products p ON oi.product_id = p.id WHERE p.name ILIKE '%keyboard%'",
        "tables_used": ["customers", "orders", "order_items", "products"],
        "confidence": 0.90,
        "explanation": "Counts unique customers who have ordered products with 'keyboard' in the name"
        }
        """
            
    async def generate_sql(
        self,
        question: str,
        schema_context: SchemaContext,
        user_id: Optional[int] = None,
    ) -> SQLGenerationResult:
        """
        Generate SQL from natural language question.
        
        Args:
            question: Natural language question
            schema_context: Available tables and schemas
            user_id: User ID for context (optional)
        
        Returns:
            SQLGenerationResult with generated SQL
        
        Raises:
            QueryValidationError: If generated SQL is unsafe
        """
        # Check cache first - cache SQL generation results
        cache_key = self._get_query_cache_key(question, schema_context)
        cached_result = await cache.get(cache_key)
        
        if cached_result:
            # Return cached SQL result
            return SQLGenerationResult(**cached_result)
        
        # Build compact context message with schema info
        context_message = self._build_context_message(schema_context)
        
        # Call Pydantic AI agent with Groq - use concise prompt
        result = await self.agent.run(
            f"{context_message}\n\nQuestion: {question}",
            message_history=[],
        )
        
        # In Pydantic AI, the structured output is in result.output when output_type is specified
        sql_result = result.output
        
        if not isinstance(sql_result, SQLGenerationResult):
            raise ValueError(
                f"Expected SQLGenerationResult, got {type(sql_result)}"
            )
        
        # Validate generated SQL for safety
        is_valid, error_msg = validator.validate_query(sql_result.sql, allow_write=False)
        if not is_valid:
            raise QueryValidationError(f"Generated unsafe SQL: {error_msg}")
        
        # Verify tables exist in schema
        for table in sql_result.tables_used:
            if table not in schema_context.available_tables:
                raise QueryValidationError(
                    f"Generated query references non-existent table: {table}"
                )
        
        # Cache the result for 1 hour (3600 seconds)
        await cache.set(cache_key, sql_result.model_dump(), expire=3600)
        
        return sql_result
    
    @staticmethod
    def _get_query_cache_key(question: str, schema_context: SchemaContext) -> str:
        """Generate cache key for SQL generation."""
        # Normalize question - lowercase and strip whitespace
        normalized_question = question.lower().strip()
        
        # Create a hash of tables to detect schema changes
        tables_hash = hashlib.md5(
            "".join(sorted(schema_context.available_tables)).encode()
        ).hexdigest()[:8]
        
        # Create cache key
        question_hash = hashlib.md5(normalized_question.encode()).hexdigest()[:16]
        return f"sql_gen:{tables_hash}:{question_hash}"
    
    @staticmethod
    def _build_context_message(schema_context: SchemaContext) -> str:
        """Build context message with schema information."""
        context_parts = ["DATABASE SCHEMA:"]
        
        # Only include business tables (skip internal MCP tables for speed)
        business_tables = [t for t in schema_context.available_tables 
                          if t not in ['users', 'query_history', 'saved_queries', 
                                      'scheduled_reports', 'role_permissions', 
                                      'database_connections']]
        
        # Add tables and columns in compact format
        for table in business_tables:
            columns = schema_context.table_schemas.get(table, [])
            # Shorten column info - just names without types for common cases
            col_names = [c.split(' (')[0] for c in columns]
            context_parts.append(f"{table}: {', '.join(col_names)}")
        
        # Add table relationships in compact format
        if schema_context.table_relationships:
            context_parts.append("\nRELATIONSHIPS:")
            for table in business_tables:
                if table in schema_context.table_relationships:
                    relationships = schema_context.table_relationships[table]
                    if relationships:
                        context_parts.append(f"{table}: {'; '.join(relationships)}")
        
        return "\n".join(context_parts)
    
    async def get_schema_context(
        self,
        session: AsyncSession,
        database_name: str = "public",
    ) -> SchemaContext:
        """
        Get database schema context from PostgreSQL.
        
        Args:
            session: Database session
            database_name: Schema name (default: public)
        
        Returns:
            SchemaContext with tables and columns
        """
        # Check cache first
        cache_key = f"schema:{database_name}"
        cached_schema = await cache.get_schema_metadata(database_name, "all_tables")
        
        if cached_schema:
            return SchemaContext(**cached_schema)
        
        # Query information_schema for tables
        tables_query = text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = :schema
            ORDER BY table_name
        """)
        
        result = await session.execute(tables_query, {"schema": database_name})
        available_tables = [row[0] for row in result.fetchall()]
        
        # Get columns for each table
        table_schemas = {}
        for table in available_tables:
            columns_query = text("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = :schema AND table_name = :table
                ORDER BY ordinal_position
            """)
            
            result = await session.execute(
                columns_query, {"schema": database_name, "table": table}
            )
            columns = [f"{row[0]} ({row[1]})" for row in result.fetchall()]
            table_schemas[table] = columns
        
        # Get foreign key relationships
        table_relationships = {}
        relationships_query = text("""
            SELECT
                tc.table_name,
                kcu.column_name,
                ccu.table_name AS foreign_table_name,
                ccu.column_name AS foreign_column_name
            FROM information_schema.table_constraints AS tc
            JOIN information_schema.key_column_usage AS kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage AS ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = :schema
            ORDER BY tc.table_name, kcu.column_name
        """)
        
        result = await session.execute(relationships_query, {"schema": database_name})
        for row in result.fetchall():
            table_name = row[0]
            column_name = row[1]
            foreign_table = row[2]
            foreign_column = row[3]
            
            if table_name not in table_relationships:
                table_relationships[table_name] = []
            
            table_relationships[table_name].append(
                f"{column_name} → {foreign_table}.{foreign_column}"
            )
        
        schema_context = SchemaContext(
            available_tables=available_tables,
            table_schemas=table_schemas,
            table_relationships=table_relationships,
        )
        
        # Cache schema for 1 hour
        await cache.set_schema_metadata(
            database_name,
            "all_tables",
            schema_context.model_dump(),
        )
        
        return schema_context


# Global SQL generator instance
sql_generator = SQLGenerator()
