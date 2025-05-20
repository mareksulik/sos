"""
Simple test script to verify the async functionality in the Share of Search Tool.
"""
import asyncio
import aiohttp
import traceback
from datetime import datetime, timedelta
import os
import sys

# Add the current directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

print("Imports successful")

try:
    from api_client.dataforseo_client import get_search_volume_async
    print("Successfully imported get_search_volume_async")
except Exception as e:
    print(f"Error importing get_search_volume_async: {e}")
    traceback.print_exc()

try:
    print("Testing basic asyncio functionality...")
    
    async def simple_test():
        print("Inside async function")
        return "success"
        
    result = asyncio.run(simple_test())
    print(f"Basic asyncio test result: {result}")
except Exception as e:
    print(f"Error in basic asyncio test: {e}")
    traceback.print_exc()

print("Test completed.")
