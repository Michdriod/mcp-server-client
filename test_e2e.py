#!/usr/bin/env python3
"""
End-to-end test for MCP Server and Client.
Tests the full flow: Client -> MCP Server -> Groq AI -> SQL -> PostgreSQL -> Redis Cache
"""
import asyncio
import sys
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_mcp_connection():
    """Test 1: Connect to MCP server and list available tools."""
    print("\n🧪 Test 1: Connecting to MCP Server...")
    
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "server.mcp_server"],
        env={"GROQ_API_KEY": os.getenv("GROQ_API_KEY", "your_groq_api_key_here")}
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            print(f"✅ Connected! Found {len(tools.tools)} tools:")
            for tool in tools.tools[:5]:  # Show first 5
                print(f"   - {tool.name}: {tool.description}")
            
            return session, tools


async def test_database_query(session):
    """Test 2: Execute a natural language query."""
    print("\n🧪 Test 2: Testing database query with natural language...")
    
    # Call the query_database tool
    result = await session.call_tool(
        "query_database",
        arguments={
            "question": "How many customers do we have?",
            "user_id": 1
        }
    )
    
    print(f"✅ Query executed!")
    print(f"Result: {result}")
    
    return result


async def test_schema_info(session):
    """Test 3: Get schema information."""
    print("\n🧪 Test 3: Getting schema information...")
    
    result = await session.call_tool(
        "get_schema_info",
        arguments={
            "table_name": "customers"
        }
    )
    
    print(f"✅ Schema retrieved!")
    print(f"Result: {result}")
    
    return result


async def main():
    """Run all end-to-end tests."""
    print("=" * 80)
    print("🚀 Starting End-to-End Test Suite")
    print("=" * 80)
    
    # Check for API key
    if not os.getenv("GROQ_API_KEY"):
        print("❌ GROQ_API_KEY environment variable not set")
        print("Please run: export GROQ_API_KEY=your_actual_key")
        return 1
    
    try:
        server_params = StdioServerParameters(
            command="python",
            args=["-m", "server.mcp_server"],
            env={"GROQ_API_KEY": os.getenv("GROQ_API_KEY", "your_groq_api_key_here")}
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Test 1: Connection
                tools = await session.list_tools()
                print(f"\n🧪 Test 1: Connection")
                print(f"✅ Connected! Found {len(tools.tools)} tools")
                
                # Test 2: Database Query
                print(f"\n🧪 Test 2: Testing database query with natural language...")
                result = await session.call_tool(
                    "query_database",
                    arguments={
                        "question": "How many customers do we have?",
                        "user_id": 1
                    }
                )
                print(f"✅ Query executed!")
                print(f"Result: {result.content[0].text if result.content else result}")
                
                # Test 3: Schema Info
                print(f"\n🧪 Test 3: Getting schema information...")
                result = await session.call_tool(
                    "get_schema_info",
                    arguments={
                        "table_name": "customers"
                    }
                )
                print(f"✅ Schema retrieved!")
                print(f"Result: {result.content[0].text if result.content else result}")
        
        print("\n" + "=" * 80)
        print("✅ All tests passed!")
        print("=" * 80)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
