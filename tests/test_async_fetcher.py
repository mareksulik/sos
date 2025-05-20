"""
Unit tests for the async fetcher implementation.

To run these tests, execute:
    python -m unittest tests/test_async_fetcher.py
"""
import unittest
import asyncio
import aiohttp
from datetime import datetime, timedelta
import sys
import os
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_client.dataforseo_client import get_search_volume_async
from data_processing.async_fetcher import (
    _fetch_multi_country_search_volume_data_async_internal,
    fetch_multi_country_search_volume_data_async
)

class MockSession:
    """Mock aiohttp.ClientSession for testing"""
    
    def __init__(self, response_data=None, should_raise=False):
        self.response_data = response_data or {"tasks": [{"status_code": 20000, "result": []}]}
        self.should_raise = should_raise
        self.post_calls = []
    
    async def post(self, url, headers=None, json=None, timeout=None):
        """Mock post method"""
        self.post_calls.append({
            "url": url,
            "headers": headers,
            "json": json,
            "timeout": timeout
        })
        
        if self.should_raise:
            raise aiohttp.ClientError("Test error")
        
        return self
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def json(self):
        """Return mock response data"""
        return self.response_data
    
    def raise_for_status(self):
        """Mock raise_for_status method"""
        if self.should_raise:
            raise aiohttp.ClientResponseError(
                request_info=None,
                history=None,
                status=500,
                message="Test error",
                headers=None
            )


class TestAsyncFetcher(unittest.TestCase):
    """Test cases for async fetcher implementation"""
    
    def test_fetch_multi_country_search_volume_data_async_signature(self):
        """Test that the async function has the same signature as the original function"""
        from data_processing.fetcher import fetch_multi_country_search_volume_data
        import inspect
        
        async_sig = inspect.signature(fetch_multi_country_search_volume_data_async)
        orig_sig = inspect.signature(fetch_multi_country_search_volume_data)
        
        # Both functions should have the same parameter names
        self.assertEqual(async_sig.parameters.keys(), orig_sig.parameters.keys())
        
        # Both functions should return the same type
        self.assertEqual(async_sig.return_annotation, orig_sig.return_annotation)

    async def async_test_get_search_volume_async(self):
        """Test the async API client function"""
        mock_session = MockSession()
        result, error, loc_code = await get_search_volume_async(
            session=mock_session,
            login="test",
            password="test",
            keywords=["test"],
            location_code=123,
            language_code="en",
            date_from=datetime.now(),
            date_to=datetime.now()
        )
        
        # Assert that the post method was called with the expected parameters
        self.assertEqual(len(mock_session.post_calls), 1)
        self.assertEqual(mock_session.post_calls[0]["json"][0]["keywords"], ["test"])
        self.assertEqual(mock_session.post_calls[0]["json"][0]["location_code"], 123)
        
        # Without real data, we expect an empty result list
        self.assertEqual(result, [])
        self.assertIsNone(error)
        self.assertEqual(loc_code, 123)

    def test_get_search_volume_async(self):
        """Run the async test using asyncio.run"""
        asyncio.run(self.async_test_get_search_volume_async())

    async def async_test_get_search_volume_async_error_handling(self):
        """Test error handling in the async API client function"""
        mock_session = MockSession(should_raise=True)
        result, error, loc_code = await get_search_volume_async(
            session=mock_session,
            login="test",
            password="test",
            keywords=["test"],
            location_code=123,
            language_code="en",
            date_from=datetime.now(),
            date_to=datetime.now()
        )
        
        # Assert that error is handled properly
        self.assertEqual(result, [])
        self.assertIsNotNone(error)
        self.assertEqual(loc_code, 123)

    def test_get_search_volume_async_error_handling(self):
        """Run the async error handling test using asyncio.run"""
        asyncio.run(self.async_test_get_search_volume_async_error_handling())

if __name__ == '__main__':
    unittest.main()
