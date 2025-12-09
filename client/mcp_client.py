"""
MCP Client for Database Query Assistant.
Provides Python API for interacting with the MCP server.
"""
import asyncio
from typing import Any, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import json
import sys
import os

# Import settings to access environment variables
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from shared.config import settings

class QueryAssistantClient:
    """Client for Database Query Assistant MCP server."""
    
    def __init__(self, server_path: str = "server.mcp_server.py"):
        """
        Initialize MCP client.
        
        Args:
            server_path: Path to MCP server script
        """
        self.server_path = server_path
        self.session: Optional[ClientSession] = None
        self._context = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    async def connect(self):
        """Connect to MCP server."""        
        # Get the Python executable from the current environment
        python_exe = sys.executable
        
        # Prepare environment with required variables
        env = os.environ.copy()
        
        # Ensure GROQ_API_KEY is set in the subprocess environment
        if not env.get('GROQ_API_KEY') and hasattr(settings, 'groq_api_key'):
            env['GROQ_API_KEY'] = settings.groq_api_key
        
        # Use python -m to ensure proper module resolution
        server_params = StdioServerParameters(
            command=python_exe,
            args=["-m", "server.mcp_server"],
            env=env
        )
        
        self._context = stdio_client(server_params)
        read, write = await self._context.__aenter__()
        self.session = ClientSession(read, write)
        await self.session.__aenter__()
        
        # Initialize session
        await self.session.initialize()
    
    async def disconnect(self):
        """Disconnect from MCP server."""
        if self.session:
            await self.session.__aexit__(None, None, None)
        if self._context:
            await self._context.__aexit__(None, None, None)
    
    async def call_tool(self, tool_name: str, **kwargs) -> dict[str, Any]:
        """
        Generic method to call any MCP tool.
        
        Args:
            tool_name: Name of the tool to call
            **kwargs: Tool arguments as keyword arguments
        
        Returns:
            Tool result as dictionary
        """
        if not self.session:
            raise RuntimeError("Client not connected. Call connect() first.")
        
        result = await self.session.call_tool(
            tool_name,
            arguments=kwargs
        )
        
        # Parse JSON response
        text_result = result.content[0].text if result.content else "{}"
        return json.loads(text_result)
    
    async def query_database(
        self,
        question: str,
        user_id: int = 1,
    ) -> dict[str, Any]:
        """
        Query database with natural language.
        
        Args:
            question: Natural language question
            user_id: User ID executing the query
        
        Returns:
            Query results with rows, columns, SQL, etc.
        """
        result = await self.session.call_tool(
            "query_database",
            arguments={"question": question, "user_id": user_id}
        )
        
        # Parse JSON response
        text_result = result.content[0].text if result.content else "{}"
        return json.loads(text_result)
    
    async def get_schema_info(self, table_name: str) -> dict[str, Any]:
        """
        Get schema information for a table.
        
        Args:
            table_name: Name of the table
        
        Returns:
            Schema details (columns, types, keys)
        """
        result = await self.session.call_tool(
            "get_schema_info",
            arguments={"table_name": table_name}
        )
        text_result = result.content[0].text if result.content else "{}"
        return json.loads(text_result)
    
    async def list_tables(self) -> dict[str, Any]:
        """
        List all available tables.
        
        Returns:
            List of tables with row counts
        """
        result = await self.session.call_tool("list_tables", arguments={})
        text_result = result.content[0].text if result.content else "{}"
        return json.loads(text_result)
    
    async def save_query(
        self,
        name: str,
        description: str,
        question: str,
        sql: str,
        user_id: int = 1,
    ) -> dict[str, Any]:
        """
        Save a query for later reuse.
        
        Args:
            name: Query name
            description: Query description
            question: Natural language question
            sql: SQL query
            user_id: User ID
        
        Returns:
            Saved query details
        """
        result = await self.session.call_tool(
            "save_query",
            arguments={
                "name": name,
                "description": description,
                "question": question,
                "sql": sql,
                "user_id": user_id,
            }
        )
        text_result = result.content[0].text if result.content else "{}"
        return json.loads(text_result)
    
    async def load_saved_query(
        self,
        query_id: int,
        user_id: int = 1,
    ) -> dict[str, Any]:
        """
        Load a saved query.
        
        Args:
            query_id: Saved query ID
            user_id: User ID
        
        Returns:
            Saved query details
        """
        result = await self.session.call_tool(
            "load_saved_query",
            arguments={"query_id": query_id, "user_id": user_id}
        )
        text_result = result.content[0].text if result.content else "{}"
        return json.loads(text_result)
    
    async def list_saved_queries(
        self,
        user_id: int = 1,
        limit: int = 20,
    ) -> dict[str, Any]:
        """
        List saved queries.
        
        Args:
            user_id: User ID
            limit: Max queries to return
        
        Returns:
            List of saved queries
        """
        result = await self.session.call_tool(
            "list_saved_queries",
            arguments={"user_id": user_id, "limit": limit}
        )
        text_result = result.content[0].text if result.content else "{}"
        return json.loads(text_result)
    
    async def delete_saved_query(
        self,
        query_id: int,
        user_id: int = 1,
    ) -> dict[str, Any]:
        """
        Delete a saved query.
        
        Args:
            query_id: ID of the query to delete
            user_id: User ID
        
        Returns:
            Deletion result
        """
        result = await self.session.call_tool(
            "delete_saved_query",
            arguments={"query_id": query_id, "user_id": user_id}
        )
        text_result = result.content[0].text if result.content else "{}"
        return json.loads(text_result)
    
    async def generate_chart(
        self,
        data: list[dict[str, Any]],
        chart_type: Optional[str] = None,
        title: Optional[str] = None,
        x_column: Optional[str] = None,
        y_column: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Generate a chart from data.
        
        Args:
            data: Query results
            chart_type: Chart type (bar, line, pie, scatter)
            title: Chart title
            x_column: X-axis column
            y_column: Y-axis column
        
        Returns:
            Chart file path
        """
        result = await self.session.call_tool(
            "generate_chart",
            arguments={
                "data": data,
                "chart_type": chart_type,
                "title": title,
                "x_column": x_column,
                "y_column": y_column,
            }
        )
        text_result = result.content[0].text if result.content else "{}"
        return json.loads(text_result)
    
    async def create_table_image(
        self,
        data: list[dict[str, Any]],
        title: Optional[str] = None,
        max_rows: int = 20,
    ) -> dict[str, Any]:
        """
        Create a table image from data.
        
        Args:
            data: Query results
            title: Table title
            max_rows: Max rows to display
        
        Returns:
            Table image file path
        """
        result = await self.session.call_tool(
            "create_table_image",
            arguments={"data": data, "title": title, "max_rows": max_rows}
        )
        text_result = result.content[0].text if result.content else "{}"
        return json.loads(text_result)
    
    async def get_query_history(
        self,
        user_id: int = 1,
        limit: int = 20,
        status: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Get query history.
        
        Args:
            user_id: User ID
            limit: Max queries to return
            status: Filter by status (success, failed)
        
        Returns:
            Query history
        """
        result = await self.session.call_tool(
            "get_query_history",
            arguments={"user_id": user_id, "limit": limit, "status": status}
        )
        text_result = result.content[0].text if result.content else "{}"
        return json.loads(text_result)
    
    async def get_popular_queries(
        self,
        limit: int = 10,
        days: int = 30,
    ) -> dict[str, Any]:
        """
        Get popular queries.
        
        Args:
            limit: Max queries to return
            days: Look back period in days
        
        Returns:
            Popular queries with execution counts
        """
        result = await self.session.call_tool(
            "get_popular_queries",
            arguments={"limit": limit, "days": days}
        )
        text_result = result.content[0].text if result.content else "{}"
        return json.loads(text_result)
    
    async def get_user_statistics(
        self,
        user_id: int = 1,
        days: int = 30,
    ) -> dict[str, Any]:
        """
        Get user statistics.
        
        Args:
            user_id: User ID
            days: Look back period in days
        
        Returns:
            User activity statistics
        """
        result = await self.session.call_tool(
            "get_user_statistics",
            arguments={"user_id": user_id, "days": days}
        )
        text_result = result.content[0].text if result.content else "{}"
        return json.loads(text_result)
    
    async def export_query_results(
        self,
        data: list[dict[str, Any]],
        format: str = "csv",
        filename: Optional[str] = None,
        title: Optional[str] = None,
    ) -> dict[str, Any]:
        """
        Export query results to file.
        
        Args:
            data: Query results
            format: Export format (csv, excel, pdf, json)
            filename: Output filename
            title: Export title
        
        Returns:
            Export file path
        """
        result = await self.session.call_tool(
            "export_query_results",
            arguments={
                "data": data,
                "format": format,
                "filename": filename,
                "title": title,
            }
        )
        text_result = result.content[0].text if result.content else "{}"
        return json.loads(text_result)
    
    async def create_scheduled_report(
        self,
        name: str,
        description: str,
        saved_query_id: int,
        schedule_cron: str,
        format: str,
        recipients: list[str],
        user_id: int = 1,
    ) -> dict[str, Any]:
        """
        Create a scheduled report.
        
        Args:
            name: Report name
            description: Report description
            saved_query_id: Saved query ID
            schedule_cron: Cron expression
            format: Report format (csv, excel, pdf)
            recipients: Email recipients
            user_id: User ID
        
        Returns:
            Created report details
        """
        result = await self.session.call_tool(
            "create_scheduled_report",
            arguments={
                "name": name,
                "description": description,
                "saved_query_id": saved_query_id,
                "schedule_cron": schedule_cron,
                "format": format,
                "recipients": recipients,
                "user_id": user_id,
            }
        )
        text_result = result.content[0].text if result.content else "{}"
        return json.loads(text_result)
    
    async def list_scheduled_reports(
        self,
        user_id: int = 1,
    ) -> dict[str, Any]:
        """
        List scheduled reports.
        
        Args:
            user_id: User ID
        
        Returns:
            List of scheduled reports
        """
        result = await self.session.call_tool(
            "list_scheduled_reports",
            arguments={"user_id": user_id}
        )
        text_result = result.content[0].text if result.content else "{}"
        return json.loads(text_result)
    
    async def update_scheduled_report(
        self,
        report_id: int,
        user_id: int = 1,
        name: Optional[str] = None,
        description: Optional[str] = None,
        schedule_cron: Optional[str] = None,
        format: Optional[str] = None,
        recipients: Optional[list[str]] = None,
        is_active: Optional[bool] = None,
    ) -> dict[str, Any]:
        """
        Update a scheduled report.
        
        Args:
            report_id: Report ID
            user_id: User ID
            name: New name
            description: New description
            schedule_cron: New cron expression
            format: New format
            recipients: New recipients
            is_active: Active status
        
        Returns:
            Update status
        """
        result = await self.session.call_tool(
            "update_scheduled_report",
            arguments={
                "report_id": report_id,
                "user_id": user_id,
                "name": name,
                "description": description,
                "schedule_cron": schedule_cron,
                "format": format,
                "recipients": recipients,
                "is_active": is_active,
            }
        )
        text_result = result.content[0].text if result.content else "{}"
        return json.loads(text_result)
    
    async def delete_scheduled_report(
        self,
        report_id: int,
        user_id: int = 1,
    ) -> dict[str, Any]:
        """
        Delete a scheduled report.
        
        Args:
            report_id: Report ID
            user_id: User ID
        
        Returns:
            Deletion status
        """
        result = await self.session.call_tool(
            "delete_scheduled_report",
            arguments={"report_id": report_id, "user_id": user_id}
        )
        text_result = result.content[0].text if result.content else "{}"
        return json.loads(text_result)
    
    async def trigger_report_now(
        self,
        report_id: int,
        user_id: int = 1,
    ) -> dict[str, Any]:
        """
        Trigger a report to run immediately.
        
        Args:
            report_id: Report ID
            user_id: User ID
        
        Returns:
            Execution status
        """
        result = await self.session.call_tool(
            "trigger_report_now",
            arguments={"report_id": report_id, "user_id": user_id}
        )
        text_result = result.content[0].text if result.content else "{}"
        return json.loads(text_result)


# Convenience function for quick queries
async def quick_query(question: str, user_id: int = 1) -> dict[str, Any]:
    """
    Quick query without maintaining connection.
    
    Args:
        question: Natural language question
        user_id: User ID
    
    Returns:
        Query results
    """
    async with QueryAssistantClient() as client:
        return await client.query_database(question, user_id)
