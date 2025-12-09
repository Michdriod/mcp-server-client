"""
Advanced Usage Example

Demonstrates advanced features like saved queries, history, and analytics.
"""
import asyncio
from datetime import datetime
from client.mcp_client import QueryAssistantClient


async def main():
    """Demonstrate advanced features"""
    
    user_id = 1
    
    async with QueryAssistantClient() as client:
        print("Advanced Features Demo\n")
        print("="*60 + "\n")
        
        # 1. Save queries for reuse
        print("1. SAVED QUERIES")
        print("-" * 60)
        
        queries_to_save = [
            {
                'name': 'Top Customers',
                'description': 'Shows top 10 customers by revenue',
                'query': 'Show me the top 10 customers by total order value'
            },
            {
                'name': 'Product Performance',
                'description': 'Best selling products this month',
                'query': 'What are the best selling products this month?'
            }
        ]
        
        saved_ids = []
        
        for item in queries_to_save:
            try:
                result = await client.save_query(
                    user_id=user_id,
                    name=item['name'],
                    description=item['description'],
                    query=item['query']
                )
                query_id = result.get('query_id')
                saved_ids.append(query_id)
                print(f"✓ Saved: {item['name']} (ID: {query_id})")
            except Exception as e:
                print(f"✗ Error saving {item['name']}: {str(e)}")
        
        print()
        
        # 2. List saved queries
        print("2. LISTING SAVED QUERIES")
        print("-" * 60)
        
        saved_queries = await client.list_saved_queries(user_id)
        
        if saved_queries:
            for query in saved_queries:
                print(f"[{query['id']}] {query['name']}")
                print(f"    {query.get('description', 'No description')}")
                print(f"    Query: {query['natural_query'][:50]}...")
                print()
        else:
            print("No saved queries found\n")
        
        # 3. Load and execute saved query
        if saved_ids:
            print("3. EXECUTING SAVED QUERY")
            print("-" * 60)
            
            query_id = saved_ids[0]
            print(f"Loading query ID: {query_id}")
            
            query_data = await client.load_saved_query(user_id, query_id)
            
            if query_data:
                print(f"Name: {query_data['name']}")
                print(f"Query: {query_data['natural_query']}\n")
                
                # Execute it
                result = await client.query_database(query_data['natural_query'], user_id)
                
                if result and 'results' in result:
                    print(f"✓ Executed successfully")
                    print(f"  Rows: {result.get('row_count', 0)}")
                    print(f"  Time: {result.get('execution_time_ms', 0):.0f}ms\n")
        
        # 4. Query history
        print("4. QUERY HISTORY")
        print("-" * 60)
        
        history = await client.get_query_history(user_id, days=7)
        
        if history:
            print(f"Found {len(history)} queries in the last 7 days\n")
            
            # Show last 5
            for item in history[:5]:
                exec_time = item.get('executed_at', '')
                if exec_time:
                    exec_time = str(exec_time)[:19]
                
                print(f"[{exec_time}]")
                print(f"  Query: {item['natural_query'][:60]}...")
                print(f"  Rows: {item.get('row_count', 0)}, Time: {item.get('execution_time_ms', 0):.0f}ms")
                print()
        else:
            print("No history available\n")
        
        # 5. User statistics
        print("5. USER STATISTICS")
        print("-" * 60)
        
        stats = await client.get_user_statistics(user_id)
        
        if stats:
            print(f"Total Queries: {stats.get('total_queries', 0)}")
            print(f"Saved Queries: {stats.get('saved_queries', 0)}")
            print(f"Active Schedules: {stats.get('active_schedules', 0)}")
            print(f"Avg Response Time: {stats.get('avg_response_time', 0):.0f}ms")
            print(f"Cache Hit Rate: {stats.get('cache_hit_rate', 0):.1f}%")
            print()
        
        # 6. Popular queries
        print("6. POPULAR QUERIES")
        print("-" * 60)
        
        popular = await client.get_popular_queries(user_id, days=30, limit=5)
        
        if popular:
            for i, item in enumerate(popular, 1):
                print(f"{i}. {item['natural_query'][:60]}...")
                print(f"   Executed {item.get('execution_count', 0)} times")
                print(f"   Avg time: {item.get('avg_time', 0):.0f}ms")
                print()
        else:
            print("No popular queries found\n")
        
        print("="*60)
        print("Demo complete!")


async def workflow_example():
    """Example: Complete workflow from query to scheduled report"""
    
    user_id = 1
    
    async with QueryAssistantClient() as client:
        print("Complete Workflow Example\n")
        
        # Step 1: Test query
        query = "Show revenue by product category this month"
        print(f"1. Testing query: {query}")
        
        result = await client.query_database(query, user_id)
        
        if result and 'results' in result:
            print(f"   ✓ Query works! {result.get('row_count', 0)} rows")
        else:
            print("   ✗ Query failed")
            return
        
        # Step 2: Save the query
        print("\n2. Saving query for reuse...")
        
        save_result = await client.save_query(
            user_id=user_id,
            name="Monthly Revenue Report",
            description="Revenue breakdown by product category",
            query=query
        )
        
        query_id = save_result.get('query_id')
        print(f"   ✓ Saved with ID: {query_id}")
        
        # Step 3: Export sample data
        print("\n3. Exporting sample data...")
        
        export_result = await client.export_query_results(user_id, query, 'excel')
        
        if export_result and 'file_path' in export_result:
            print(f"   ✓ Exported to: {export_result['file_path']}")
        
        # Step 4: Create visualization
        print("\n4. Creating visualization...")
        
        chart_result = await client.generate_chart(user_id, query, 'bar')
        
        if chart_result and 'chart_path' in chart_result:
            print(f"   ✓ Chart saved: {chart_result['chart_path']}")
        
        # Step 5: Schedule monthly report
        print("\n5. Scheduling monthly report...")
        
        schedule_result = await client.create_scheduled_report(
            user_id=user_id,
            name="Monthly Revenue Report",
            query=query,
            schedule="0 9 1 * *",  # First day of month at 9 AM
            email="finance@example.com",
            format="excel"
        )
        
        schedule_id = schedule_result.get('schedule_id')
        print(f"   ✓ Scheduled with ID: {schedule_id}")
        print(f"   Will run on 1st of each month at 9 AM")
        
        print("\n✓ Workflow complete! The report is now automated.")


if __name__ == "__main__":
    # Run main demo
    asyncio.run(main())
    
    # Uncomment to run workflow example
    # asyncio.run(workflow_example())
