import sys
import os
sys.path.append('.')

from app.services.attendance_service import AttendanceService
import logging

# Set up logging to see output
logging.basicConfig(level=logging.INFO)

# Test the browser history retrieval
service = AttendanceService()
try:
    history = service._get_browser_history(hours_back=24)
    print(f'Successfully retrieved {len(history)} history items')
    for item in history[:5]:  # Show first 5 items
        print('  URL:', item['url'])
        print('  Title:', item['title'])
        print('  Visited:', item['visited_at'])
        print()
except Exception as e:
    print(f'Error retrieving browser history: {e}')
