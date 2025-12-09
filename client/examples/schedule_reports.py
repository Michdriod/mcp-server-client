"""
Schedule Reports Example

Shows how to create and manage scheduled reports.
"""
import asyncio
from client.mcp_client import QueryAssistantClient


async def main():
    """Create and manage scheduled reports"""
    
    user_id = 1
    
    async with QueryAssistantClient() as client:
        print("Scheduled Reports Management\n")
        
        # 1. List existing schedules
        print("1. Listing existing schedules...")
        schedules = await client.list_scheduled_reports(user_id)
        
        if schedules:
            print(f"   Found {len(schedules)} schedules:")
            for schedule in schedules:
                status = "Active" if schedule['is_active'] else "Paused"
                print(f"   - [{schedule['id']}] {schedule['name']} ({status})")
        else:
            print("   No schedules found")
        
        print()
        
        # 2. Create new schedule
        print("2. Creating new schedule...")
        
        new_schedule = {
            'name': 'Daily Top Customers Report',
            'query': 'Show me the top 10 customers by order value today',
            'schedule': '0 9 * * *',  # Every day at 9 AM
            'email': 'admin@example.com',
            'format': 'excel'
        }
        
        try:
            result = await client.create_scheduled_report(
                user_id=user_id,
                name=new_schedule['name'],
                query=new_schedule['query'],
                schedule=new_schedule['schedule'],
                email=new_schedule['email'],
                format=new_schedule['format']
            )
            
            schedule_id = result.get('schedule_id')
            print(f"   ✓ Schedule created with ID: {schedule_id}")
            print(f"   Name: {new_schedule['name']}")
            print(f"   Schedule: {new_schedule['schedule']} (Daily at 9 AM)")
            print(f"   Email: {new_schedule['email']}")
            print(f"   Format: {new_schedule['format'].upper()}")
        
        except Exception as e:
            print(f"   ✗ Error creating schedule: {str(e)}")
            schedule_id = None
        
        print()
        
        # 3. Trigger report immediately (if created)
        if schedule_id:
            print("3. Triggering report immediately...")
            
            try:
                await client.trigger_report_now(user_id, schedule_id)
                print(f"   ✓ Report triggered! Check email at {new_schedule['email']}")
            except Exception as e:
                print(f"   ✗ Error triggering report: {str(e)}")
            
            print()
            
            # 4. Update schedule (pause it)
            print("4. Pausing the schedule...")
            
            try:
                await client.update_scheduled_report(
                    user_id=user_id,
                    schedule_id=schedule_id,
                    is_active=False
                )
                print(f"   ✓ Schedule paused")
            except Exception as e:
                print(f"   ✗ Error updating schedule: {str(e)}")
            
            print()
            
            # 5. List schedules again to see changes
            print("5. Listing schedules after changes...")
            schedules = await client.list_scheduled_reports(user_id)
            
            if schedules:
                for schedule in schedules:
                    if schedule['id'] == schedule_id:
                        status = "Active" if schedule['is_active'] else "Paused"
                        print(f"   - [{schedule['id']}] {schedule['name']} ({status}) ← Updated!")
                    else:
                        status = "Active" if schedule['is_active'] else "Paused"
                        print(f"   - [{schedule['id']}] {schedule['name']} ({status})")
            
            print()
            
            # 6. Optional: Delete schedule (commented out to preserve it)
            # print("6. Deleting the schedule...")
            # try:
            #     await client.delete_scheduled_report(user_id, schedule_id)
            #     print(f"   ✓ Schedule deleted")
            # except Exception as e:
            #     print(f"   ✗ Error deleting schedule: {str(e)}")
        
        print("\nSchedule management complete!")


async def create_multiple_schedules():
    """Example: Create multiple schedules at once"""
    
    user_id = 1
    
    schedules = [
        {
            'name': 'Weekly Sales Summary',
            'query': 'Show total sales and orders for this week',
            'schedule': '0 9 * * 1',  # Every Monday at 9 AM
            'email': 'sales@example.com',
            'format': 'excel'
        },
        {
            'name': 'Monthly Revenue Report',
            'query': 'Show revenue breakdown by product category this month',
            'schedule': '0 8 1 * *',  # First day of month at 8 AM
            'email': 'finance@example.com',
            'format': 'pdf'
        },
        {
            'name': 'Daily Order Count',
            'query': 'How many orders were placed today?',
            'schedule': '0 18 * * *',  # Every day at 6 PM
            'email': 'operations@example.com',
            'format': 'csv'
        }
    ]
    
    async with QueryAssistantClient() as client:
        print(f"Creating {len(schedules)} schedules...\n")
        
        for schedule in schedules:
            try:
                result = await client.create_scheduled_report(
                    user_id=user_id,
                    name=schedule['name'],
                    query=schedule['query'],
                    schedule=schedule['schedule'],
                    email=schedule['email'],
                    format=schedule['format']
                )
                
                print(f"✓ {schedule['name']}")
                print(f"  ID: {result.get('schedule_id')}")
                print(f"  Schedule: {schedule['schedule']}")
                print()
            
            except Exception as e:
                print(f"✗ {schedule['name']}: {str(e)}\n")


if __name__ == "__main__":
    # Run main example
    asyncio.run(main())
    
    # Uncomment to create multiple schedules
    # asyncio.run(create_multiple_schedules())
