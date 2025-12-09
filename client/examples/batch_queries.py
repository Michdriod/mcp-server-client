"""
Batch Queries Example

Shows how to execute multiple queries efficiently and compare results.
"""
import asyncio
from client.mcp_client import QueryAssistantClient


async def main():
    """Execute multiple queries"""
    
    user_id = 1
    
    # Define multiple queries
    queries = [
        "Show me the top 5 customers by order count",
        "What are the most popular products?",
        "Show total sales by month for this year",
        "List customers who haven't ordered in 90 days",
        "What's the average order value by customer segment?"
    ]
    
    print("Executing batch queries...\n")
    
    # Single connection for all queries
    async with QueryAssistantClient() as client:
        results = []
        
        for i, query in enumerate(queries, 1):
            print(f"[{i}/{len(queries)}] {query}")
            
            try:
                result = await client.query_database(query, user_id)
                
                if result and 'results' in result:
                    results.append({
                        'query': query,
                        'row_count': result.get('row_count', 0),
                        'execution_time': result.get('execution_time_ms', 0),
                        'cached': result.get('cached', False),
                        'data': result['results']
                    })
                    print(f"  ✓ {result.get('row_count', 0)} rows in {result.get('execution_time_ms', 0):.0f}ms")
                else:
                    print(f"  ✗ Failed")
            
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
            
            print()
        
        # Summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        
        total_queries = len(results)
        total_rows = sum(r['row_count'] for r in results)
        total_time = sum(r['execution_time'] for r in results)
        cached_count = sum(1 for r in results if r['cached'])
        
        print(f"Queries Executed: {total_queries}")
        print(f"Total Rows Retrieved: {total_rows}")
        print(f"Total Time: {total_time:.0f}ms")
        print(f"Average Time: {total_time / total_queries:.0f}ms per query")
        print(f"Cache Hits: {cached_count}/{total_queries} ({cached_count/total_queries*100:.0f}%)")
        
        # Show sample data from first query
        if results:
            print(f"\n\nSample data from first query:")
            print(f"Query: {results[0]['query']}\n")
            for row in results[0]['data'][:5]:
                print(f"  {row}")


if __name__ == "__main__":
    asyncio.run(main())
