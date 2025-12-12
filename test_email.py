#!/usr/bin/env python3
"""
Test email functionality.
"""
import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from server.scheduler.email_sender import send_report_email


async def test_email():
    """Test sending an email."""
    try:
        result = await send_report_email(
            recipients=["michwaleh@gmail.com"],
            subject="Test Report",
            report_name="Test Report",
            description="This is a test report",
            data=[
                {"column1": "value1", "column2": "value2"},
                {"column1": "value3", "column2": "value4"}
            ],
            format="csv"
        )
        print("Email test result:", result)
        
    except Exception as e:
        print(f"Email test failed: {e}")


if __name__ == "__main__":
    asyncio.run(test_email())