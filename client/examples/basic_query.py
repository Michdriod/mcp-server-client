"""
Basic Query Example

Shows how to execute a simple natural language query using the MCP client.
"""
import asyncio
from client.mcp_client import QueryAssistantClient


async def main():
    """Execute a basic query"""
    
    # User ID: 1=admin, 2=sales analyst, 3=finance team
    user_id = 1
    
    # Natural language query
    query = "Show me the top 5 customers by total order value"
    
    print(f"Executing query: {query}\n")
    
    # Use the client with context manager (auto-connects and disconnects)
    async with QueryAssistantClient() as client:
        # Execute query
        result = await client.query_database(query, user_id)
        
        # Display results
        if result and 'results' in result:
            print(f"✓ Query executed successfully!")
            print(f"  Rows: {result.get('row_count', 0)}")
            print(f"  Columns: {result.get('column_count', 0)}")
            print(f"  Time: {result.get('execution_time_ms', 0):.0f}ms")
            print(f"  Cached: {result.get('cached', False)}")
            print(f"\nSQL Generated:\n{result.get('sql_query', 'N/A')}\n")
            
            # Print results
            print("Results:")
            for i, row in enumerate(result['results'][:10], 1):
                print(f"{i}. {row}")
            
            if len(result['results']) > 10:
                print(f"\n... and {len(result['results']) - 10} more rows")
        else:
            print("✗ No results returned")


if __name__ == "__main__":
    asyncio.run(main())
