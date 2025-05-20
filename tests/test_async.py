"""
Simple test script to verify the async functionality in the Share of Search Tool.
"""
import asyncio
import aiohttp
from datetime import datetime, timedelta
import os
import sys

# Add the current directory to the path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from api_client.dataforseo_client import get_search_volume_async
from data_processing.async_fetcher import fetch_multi_country_search_volume_data_async

async def test_async_client():
    """Test the async API client functionality."""
    print("Testing async API client...")
    try:
        async with aiohttp.ClientSession() as session:
            # Using dummy credentials for testing only
            results, error, loc_code = await get_search_volume_async(
                session=session,
                login="test_login",
                password="test_password",
                keywords=["test1", "test2"],
                location_code=2276,  # Germany
                language_code="en",
                date_from=datetime.now() - timedelta(days=30),
                date_to=datetime.now()
            )
            
            if error and "Unauthorized" in error:
                # This is expected with dummy credentials
                print("✅ API client function executed correctly (expected auth error)")
                return True
            else:
                print(f"❓ Unexpected response: {error}")
                return False
    except Exception as e:
        print(f"❌ Error in async API client: {e}")
        return False

if __name__ == "__main__":
    try:
        print("Running async compatibility test...")
        asyncio.run(test_async_client())
        print("All tests completed.")
    except Exception as e:
        print(f"❌ Error running tests: {e}")
