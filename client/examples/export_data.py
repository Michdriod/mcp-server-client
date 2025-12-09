"""
Export Data Example

Shows how to export query results in different formats.
"""
import asyncio
import os
from client.mcp_client import QueryAssistantClient


async def main():
    """Export query results in multiple formats"""
    
    user_id = 1
    
    # Query to export
    query = "Show me all customers with their total order value and count"
    
    print(f"Query: {query}\n")
    print("Exporting results in multiple formats...\n")
    
    async with QueryAssistantClient() as client:
        # 1. Export as CSV
        print("1. Exporting as CSV...")
        try:
            result = await client.export_query_results(user_id, query, 'csv')
            
            if result and 'file_path' in result:
                file_path = result['file_path']
                file_size = os.path.getsize(file_path)
                print(f"   ✓ CSV exported")
                print(f"   File: {file_path}")
                print(f"   Size: {file_size:,} bytes")
            else:
                print(f"   ✗ Export failed")
        except Exception as e:
            print(f"   ✗ Error: {str(e)}")
        
        print()
        
        # 2. Export as Excel
        print("2. Exporting as Excel...")
        try:
            result = await client.export_query_results(user_id, query, 'excel')
            
            if result and 'file_path' in result:
                file_path = result['file_path']
                file_size = os.path.getsize(file_path)
                print(f"   ✓ Excel exported")
                print(f"   File: {file_path}")
                print(f"   Size: {file_size:,} bytes")
            else:
                print(f"   ✗ Export failed")
        except Exception as e:
            print(f"   ✗ Error: {str(e)}")
        
        print()
        
        # 3. Export as PDF
        print("3. Exporting as PDF...")
        try:
            result = await client.export_query_results(user_id, query, 'pdf')
            
            if result and 'file_path' in result:
                file_path = result['file_path']
                file_size = os.path.getsize(file_path)
                print(f"   ✓ PDF exported")
                print(f"   File: {file_path}")
                print(f"   Size: {file_size:,} bytes")
            else:
                print(f"   ✗ Export failed")
        except Exception as e:
            print(f"   ✗ Error: {str(e)}")
        
        print()
        
        # 4. Export as JSON
        print("4. Exporting as JSON...")
        try:
            result = await client.export_query_results(user_id, query, 'json')
            
            if result and 'file_path' in result:
                file_path = result['file_path']
                file_size = os.path.getsize(file_path)
                print(f"   ✓ JSON exported")
                print(f"   File: {file_path}")
                print(f"   Size: {file_size:,} bytes")
                
                # Preview JSON content
                import json
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    print(f"   Records: {len(data)}")
                    if data:
                        print(f"   Sample: {data[0]}")
            else:
                print(f"   ✗ Export failed")
        except Exception as e:
            print(f"   ✗ Error: {str(e)}")
        
        print("\n" + "="*60)
        print("All exports complete!")


async def export_with_charts():
    """Export data and generate visualizations"""
    
    user_id = 1
    query = "Show monthly sales trends for the last 6 months"
    
    print(f"Query: {query}\n")
    
    async with QueryAssistantClient() as client:
        # 1. Export data
        print("1. Exporting data as Excel...")
        result = await client.export_query_results(user_id, query, 'excel')
        
        if result and 'file_path' in result:
            print(f"   ✓ Data exported: {result['file_path']}\n")
        
        # 2. Generate line chart
        print("2. Generating line chart...")
        chart_result = await client.generate_chart(user_id, query, 'line')
        
        if chart_result and 'chart_path' in chart_result:
            print(f"   ✓ Chart saved: {chart_result['chart_path']}\n")
        
        # 3. Generate bar chart
        print("3. Generating bar chart...")
        chart_result = await client.generate_chart(user_id, query, 'bar')
        
        if chart_result and 'chart_path' in chart_result:
            print(f"   ✓ Chart saved: {chart_result['chart_path']}\n")
        
        print("Export with visualizations complete!")


async def bulk_export():
    """Export multiple queries at once"""
    
    user_id = 1
    
    queries = [
        ("customers", "Show all customers with contact info"),
        ("products", "List all products with pricing"),
        ("orders", "Show all orders from last month"),
        ("sales_summary", "Show total sales by product category")
    ]
    
    print(f"Bulk exporting {len(queries)} queries...\n")
    
    async with QueryAssistantClient() as client:
        for name, query in queries:
            print(f"Exporting {name}...")
            
            try:
                result = await client.export_query_results(user_id, query, 'excel')
                
                if result and 'file_path' in result:
                    # Rename file with custom name
                    import shutil
                    old_path = result['file_path']
                    new_path = f"exports/{name}.xlsx"
                    
                    os.makedirs('exports', exist_ok=True)
                    shutil.move(old_path, new_path)
                    
                    print(f"  ✓ Saved as {new_path}")
                else:
                    print(f"  ✗ Failed")
            
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")
            
            print()
        
        print("Bulk export complete! Check the 'exports' folder.")


if __name__ == "__main__":
    # Run main example
    asyncio.run(main())
    
    # Uncomment to run other examples
    # asyncio.run(export_with_charts())
    # asyncio.run(bulk_export())
