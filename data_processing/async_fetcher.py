"""
Implementation of asynchronous fetcher for multi-country search volume data.

This module provides a significantly faster alternative to the standard fetcher by making 
API calls in parallel using asyncio and aiohttp. The implementation:

1. Groups API calls into batches to respect rate limits
2. Makes concurrent API requests within each batch
3. Pauses between batches to avoid API rate limiting
4. Properly handles errors and combines results

The async implementation can be 2-5x faster than the sequential version,
depending on the number of countries being analyzed.
"""
import asyncio
import aiohttp
import pandas as pd
import streamlit as st
import time
from typing import List, Dict, Tuple, Any, Optional
from datetime import datetime
import logging

from api_client.dataforseo_client import get_search_volume_async
from config import CacheSettings, DataProcessingSettings

# Set up logging
logger = logging.getLogger(__name__)

# This async function itself is not cached - the wrapper function will handle caching
async def _fetch_multi_country_search_volume_data_async_internal(
    login: str,
    password: str,
    kw_list_tuple: Tuple[str, ...],
    selected_location_codes_tuple: Tuple[int, ...],
    lang_code: str,
    date_from: datetime,
    date_to: datetime,
    all_location_options_tuple: Tuple[Tuple[str, int], ...]
) -> Tuple[pd.DataFrame, Optional[str]]:
    """
    Asynchronously fetches search volume data for multiple countries in parallel.
    Uses aiohttp to make concurrent API calls for each location.
    
    This is an internal implementation that should not be called directly.
    Use fetch_multi_country_search_volume_data_async instead.
    
    Args:
        login: API username
        password: API password
        kw_list_tuple: Tuple of keywords
        selected_location_codes_tuple: Tuple of location codes
        lang_code: Language code
        date_from: Start date
        date_to: End date
        all_location_options_tuple: Tuple of all available locations
        
    Returns:
        Tuple[pd.DataFrame, Optional[str]]: Tuple of (resulting DataFrame, error message or None)
    """
    all_results_list = [] 
    errors_list = []
    
    kw_list = list(kw_list_tuple)
    selected_location_codes = list(selected_location_codes_tuple)
    
    # Create a map from location_code to name
    location_code_to_name_map = {code: name for name, code in list(all_location_options_tuple)}

    progress_bar = st.progress(0)
    status_text = st.empty()
    status_text.info(f"⏳ Initializing data fetching for {len(selected_location_codes)} countries...")
    
    # Determine batch size based on API limitations
    # Each batch will be processed concurrently, with pauses between batches
    # Default batch size of 5 is conservative, can be adjusted based on API limits
    batch_size = DataProcessingSettings.get('ASYNC_BATCH_SIZE', 5)
    
    # Dynamically adjust batch size based on the number of countries
    # For a small number of countries, we can process them all at once
    if len(selected_location_codes) <= 3:
        batch_size = len(selected_location_codes)
    # For many countries, be more conservative to avoid rate limiting
    elif len(selected_location_codes) > 10:
        batch_size = min(batch_size, 4)  # Reduce batch size for large requests
    
    # Process location codes in batches
    for batch_index in range(0, len(selected_location_codes), batch_size):
        batch_locs = selected_location_codes[batch_index:batch_index + batch_size]
        status_text.info(f"⏳ Fetching data for batch {batch_index//batch_size + 1} of {(len(selected_location_codes) + batch_size - 1)//batch_size}...")
        
        async with aiohttp.ClientSession() as session:
            # Create a list of tasks to run concurrently
            tasks = []
            for loc_code in batch_locs:
                tasks.append(
                    get_search_volume_async(
                        session=session,
                        login=login,
                        password=password,
                        keywords=kw_list,
                        location_code=loc_code,
                        language_code=lang_code,
                        date_from=date_from,
                        date_to=date_to
                    )
                )
            
            # Execute all tasks concurrently and gather results
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process the results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    # Handle exceptions from the tasks
                    loc_code = batch_locs[i]
                    location_name = location_code_to_name_map.get(loc_code, str(loc_code))
                    error_msg = f"Error for country {location_name}: {str(result)}"
                    errors_list.append(error_msg)
                    logger.error(error_msg)
                else:
                    # Process successful results
                    single_country_data_list, error_msg_single, loc_code = result
                    location_name = location_code_to_name_map.get(loc_code, str(loc_code))
                    
                    if error_msg_single:
                        errors_list.append(f"Error for country {location_name} ({loc_code}): {error_msg_single}")
                        # If the error includes "Too many requests", we might need a longer pause
                        if "50301" in error_msg_single or "Too many requests" in error_msg_single:
                            status_text.error(f"API Limit exceeded for country {location_name}. Try again in a while or with fewer countries.")
                            # Dynamically increase pause between batches if we hit rate limits
                            if batch_index + batch_size < len(selected_location_codes):
                                current_pause = DataProcessingSettings.get('ASYNC_BATCH_PAUSE', 3)
                                DataProcessingSettings.ASYNC_BATCH_PAUSE = min(10, current_pause * 1.5)  # Increase pause but cap at 10 seconds
                                logger.warning(f"Increased batch pause to {DataProcessingSettings.ASYNC_BATCH_PAUSE}s due to rate limiting")
                    elif single_country_data_list:
                        # Add the country information to the data
                        country_data = [
                            {**record, 'Country': location_name} 
                            for record in single_country_data_list
                        ]
                        all_results_list.extend(country_data)
            
            # Update progress
            progress_bar.progress((batch_index + len(batch_locs)) / len(selected_location_codes))
        
        # Add a pause between batches to respect API rate limits
        if batch_index + batch_size < len(selected_location_codes):  # No pause after the last batch
            sleep_duration = DataProcessingSettings.get('ASYNC_BATCH_PAUSE', 3)  # seconds
            status_text.info(f"Pausing {sleep_duration}s before the next batch of API calls...")
            await asyncio.sleep(sleep_duration)
    
    status_text.empty()
    progress_bar.empty()
    
    if not errors_list and not all_results_list:
        return pd.DataFrame(), "No data found for the specified criteria and selected countries."
    
    final_error_message = "\n".join(errors_list) if errors_list else None
    
    # Efficiently create DataFrame directly from the result list
    all_results_df = pd.DataFrame(all_results_list) if all_results_list else pd.DataFrame()
    
    return all_results_df, final_error_message

# This is the cached wrapper function that calls the async implementation
@st.cache_data(ttl=CacheSettings.SEARCH_DATA_TTL)
def fetch_multi_country_search_volume_data_async(
    login: str,
    password: str,
    kw_list_tuple: Tuple[str, ...],
    selected_location_codes_tuple: Tuple[int, ...],
    lang_code: str,
    date_from: datetime,
    date_to: datetime,
    all_location_options_tuple: Tuple[Tuple[str, int], ...]
) -> Tuple[pd.DataFrame, Optional[str]]:
    """
    Cached wrapper for async fetching of search volume data for multiple countries.
    This function runs the async implementation and returns the result.
    
    IMPORTANT: This structure solves the UnserializableReturnValueError that occurs
    when trying to cache an async function. Instead of caching the coroutine directly,
    we cache this wrapper function that calls the async implementation and
    returns serializable results.
    
    Args:
        login: API username
        password: API password
        kw_list_tuple: Tuple of keywords
        selected_location_codes_tuple: Tuple of location codes
        lang_code: Language code
        date_from: Start date
        date_to: End date
        all_location_options_tuple: Tuple of all available locations
        
    Returns:
        Tuple[pd.DataFrame, Optional[str]]: Tuple of (resulting DataFrame, error message or None)
    """
    # Run the async function using asyncio.run
    return asyncio.run(_fetch_multi_country_search_volume_data_async_internal(
        login, password, kw_list_tuple, selected_location_codes_tuple,
        lang_code, date_from, date_to, all_location_options_tuple
    ))
