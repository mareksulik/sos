"""
API klient pre komunikáciu s DataForSEO REST API.
Podporuje načítanie údajov o lokáciách, jazykoch a vyhľadávacích objemoch.
"""
from typing import List, Dict, Tuple, Any, Optional
import streamlit as st
import requests
import aiohttp
import base64
import json
import pandas as pd
from datetime import datetime
import logging

# Import konfigurácie
from config import ApiEndpoints, CacheSettings, DataProcessingSettings

# Nastavenie loggera
logger = logging.getLogger(__name__)

def _get_auth_headers(login: str, password: str) -> Dict[str, str]:
    """Vytvorí autorizačné hlavičky pre API požiadavku.
    
    Args:
        login: API prihlasovacie meno
        password: API heslo
        
    Returns:
        Dict[str, str]: Slovník s hlavičkami požiadavky
    """
    credentials = f"{login}:{password}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()
    return {'Authorization': f'Basic {encoded_credentials}', 'Content-Type': 'application/json'}

@st.cache_data(ttl=CacheSettings.LOCATIONS_TTL)
def load_locations(login: str, password: str) -> Tuple[List[Tuple[str, int]], Optional[str]]:
    """Načíta dostupné lokácie z DataForSEO API.
    
    Args:
        login: API prihlasovacie meno
        password: API heslo
        
    Returns:
        Tuple[List[Tuple[str, int]], Optional[str]]: Dvojica (zoznam lokácií, chybová správa alebo None)
    """
    if not login or not password:
        return [], "Chýbajú API prihlasovacie údaje."
    
    headers = _get_auth_headers(login, password)
    location_options = [] 
    error_msg = None
    
    try:
        response = requests.get(
            ApiEndpoints.LOCATIONS, 
            headers=headers, 
            timeout=DataProcessingSettings.API_REQUEST_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
        
        if data.get("tasks") and data["tasks"][0].get("status_code") == 20000:
            results = data["tasks"][0].get("result")
            if results:
                temp_locations = {}
                for item in results:
                    code = item.get("location_code")
                    name = item.get("location_name")
                    loc_type = item.get("location_type")
                    display_name = f"{name}" + (f" ({loc_type})" if loc_type and loc_type != "Country" else "")
                    if code and name:
                        temp_locations[code] = {'name': name, 'type': loc_type, 'display': display_name}
                
                location_options = sorted(
                    [(data['display'], code) for code, data in temp_locations.items()], 
                    key=lambda x: x[0]
                )
            else:
                error_msg = "API (lokácie): Žiadne výsledky."
        elif data.get("tasks") and data["tasks"][0].get("status_code") == 40101:
            error_msg = "API (lokácie): Chyba 40101 - Neautorizované."
        elif data.get("tasks"):
            error_msg = f"API (lokácie): Kód {data['tasks'][0].get('status_code','N/A')} - {data['tasks'][0].get('status_message','N/A')}"
        else:
            error_msg = "API (lokácie): Neočakávaná odpoveď."
    except requests.exceptions.HTTPError as e:
        error_msg = f"Chyba HTTP pri komunikácii s API (lokácie): {e}"
        logger.error(error_msg)
    except requests.exceptions.RequestException as e:
        error_msg = f"Chyba pri komunikácii s API (lokácie): {e}"
        logger.error(error_msg)
    except Exception as e:
        error_msg = f"Neočekávaná chyba pri načítaní lokácií: {e}"
        logger.error(error_msg)
    
    return location_options, error_msg

@st.cache_data(ttl=CacheSettings.LANGUAGES_TTL)
def load_languages(login: str, password: str) -> Tuple[List[Tuple[str, str]], Optional[str]]:
    """Načíta dostupné jazyky z DataForSEO API.
    
    Args:
        login: API prihlasovacie meno
        password: API heslo
        
    Returns:
        Tuple[List[Tuple[str, str]], Optional[str]]: Dvojica (zoznam jazykov, chybová správa alebo None)
    """
    if not login or not password:
        return [], "Chýbajú API prihlasovacie údaje."
    
    headers = _get_auth_headers(login, password)
    language_options = []
    error_msg = None
    
    try:
        response = requests.get(
            ApiEndpoints.LANGUAGES, 
            headers=headers, 
            timeout=DataProcessingSettings.API_REQUEST_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()
        
        if data.get("tasks") and data["tasks"][0].get("status_code") == 20000:
            results = data["tasks"][0].get("result")
            if results:
                temp_languages = {}
                for item in results:
                    code = item.get("language_code")
                    name = item.get("language_name")
                    if code and name:
                        temp_languages[code] = name
                
                language_options = sorted(
                    [(name, code) for code, name in temp_languages.items()], 
                    key=lambda x: x[0]
                )
            else:
                error_msg = "API (jazyky): Žiadne výsledky."
        elif data.get("tasks") and data["tasks"][0].get("status_code") == 40101:
            error_msg = "API (jazyky): Chyba 40101 - Neautorizované."
        elif data.get("tasks"):
            error_msg = f"API (jazyky): Kód {data['tasks'][0].get('status_code','N/A')} - {data['tasks'][0].get('status_message','N/A')}"
        else:
            error_msg = "API (jazyky): Neočakávaná odpoveď."
    except requests.exceptions.HTTPError as e:
        error_msg = f"Chyba HTTP pri komunikácii s API (jazyky): {e}"
        logger.error(error_msg)
    except requests.exceptions.RequestException as e:
        error_msg = f"API (jazyky): Chyba komunikácie - {e}"
        logger.error(error_msg)
    except Exception as e:
        error_msg = f"Neočekávaná chyba pri načítaní jazykov: {e}"
        logger.error(error_msg)
    
    return language_options, error_msg

async def get_search_volume_async(
    session: aiohttp.ClientSession,
    login: str, 
    password: str, 
    keywords: List[str], 
    location_code: int, 
    language_code: str, 
    date_from: datetime, 
    date_to: datetime
) -> Tuple[List[Dict[str, Any]], Optional[str], int]:
    """Asynchrónne získa objem vyhľadávania pre jednu sadu parametrov.
    
    Args:
        session: aiohttp ClientSession
        login: API prihlasovacie meno
        password: API heslo
        keywords: Zoznam kľúčových slov
        location_code: Kód lokácie
        language_code: Kód jazyka
        date_from: Počiatočný dátum
        date_to: Koncový dátum
        
    Returns:
        Tuple[List[Dict[str, Any]], Optional[str], int]: Trojica (výsledky, chybová správa alebo None, kód lokácie)
    """
    results_list = []
    error_msg = None
    
    headers = _get_auth_headers(login, password)
    post_data = [{
        "keywords": keywords,
        "location_code": location_code,
        "language_code": language_code,
        "date_from": date_from.strftime("%Y-%m-%d"),
        "date_to": date_to.strftime("%Y-%m-%d"),
        "tag": "streamlit_app_request"
    }]

    try:
        async with session.post(
            ApiEndpoints.SEARCH_VOLUME_LIVE,
            headers=headers,
            json=post_data,
            timeout=DataProcessingSettings.API_REQUEST_TIMEOUT
        ) as response:
            response.raise_for_status()
            response_data = await response.json()

            if response_data.get("tasks") and response_data["tasks"][0].get("status_code") == 20000:
                task_result_items = response_data["tasks"][0].get("result")
                if task_result_items:
                    for item in task_result_items:
                        keyword = item.get("keyword")
                        monthly_searches = item.get("monthly_searches")
                        if not keyword or not monthly_searches:
                            continue
                        
                        for ms_item in monthly_searches:
                            year = ms_item.get("year")
                            month = ms_item.get("month")
                            sv = ms_item.get("search_volume")
                            
                            if year and month and sv is not None:
                                try:
                                    month_date = pd.to_datetime(f'{year}-{month:02d}-01')
                                    results_list.append({
                                        "Keyword": keyword,
                                        "Date": month_date,
                                        "Search Volume": sv,
                                        "Location Code": location_code,
                                    })
                                except ValueError:
                                    # Ignorujeme neplatné dátumy
                                    pass
            elif response_data.get("tasks") and response_data["tasks"][0].get("status_code") == 40101:
                error_msg = f"API: Kód {response_data['tasks'][0]['status_code']} - {response_data['tasks'][0]['status_message']}. Skontrolujte API prihlasovacie údaje."
            elif response_data.get("tasks"):
                error_msg = f"API: Kód {response_data['tasks'][0].get('status_code','N/A')} - {response_data['tasks'][0].get('status_message','N/A')}"
            else:
                error_msg = "API vrátilo neočakávanú štruktúru odpovede."
                logger.warning(f"Detail odpovede: {str(response_data)[:500]}")
    except aiohttp.ClientResponseError as e:
        error_msg = f"Chyba HTTP pri komunikácii s API: {e}"
        logger.error(error_msg)
    except aiohttp.ClientError as e:
        error_msg = f"Chyba pri komunikácii s API: {e}"
        logger.error(error_msg)
    except Exception as e:
        error_msg = f"Nastala neočakávaná chyba pri spracovaní API volania: {e}"
        logger.error(error_msg)
    
    return results_list, error_msg, location_code


def get_search_volume_for_task(
    login: str, 
    password: str, 
    keywords: List[str], 
    location_code: int, 
    language_code: str, 
    date_from: datetime, 
    date_to: datetime
) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """Získa objem vyhľadávania pre jednu sadu parametrov (jeden task).
    
    Args:
        login: API prihlasovacie meno
        password: API heslo
        keywords: Zoznam kľúčových slov
        location_code: Kód lokácie
        language_code: Kód jazyka
        date_from: Počiatočný dátum
        date_to: Koncový dátum
        
    Returns:
        Tuple[List[Dict[str, Any]], Optional[str]]: Dvojica (výsledky, chybová správa alebo None)
    """
    results_list = []
    error_msg = None
    
    headers = _get_auth_headers(login, password)
    post_data = [{
        "keywords": keywords,
        "location_code": location_code,
        "language_code": language_code,
        "date_from": date_from.strftime("%Y-%m-%d"),
        "date_to": date_to.strftime("%Y-%m-%d"),
        "tag": "streamlit_app_request"
    }]

    try:
        response = requests.post(
            ApiEndpoints.SEARCH_VOLUME_LIVE,
            headers=headers,
            json=post_data,
            timeout=DataProcessingSettings.API_REQUEST_TIMEOUT
        )
        response.raise_for_status()
        response_data = response.json()

        if response_data.get("tasks") and response_data["tasks"][0].get("status_code") == 20000:
            task_result_items = response_data["tasks"][0].get("result")
            if task_result_items:
                for item in task_result_items:
                    keyword = item.get("keyword")
                    monthly_searches = item.get("monthly_searches")
                    if not keyword or not monthly_searches:
                        continue
                    
                    for ms_item in monthly_searches:
                        year = ms_item.get("year")
                        month = ms_item.get("month")
                        sv = ms_item.get("search_volume")
                        
                        if year and month and sv is not None:
                            try:
                                # API vracia dáta pre celý mesiac, aj keď je dopyt na kratšie obdobie v rámci mesiaca.
                                # Filtrovanie na presné obdobie date_from/date_to sa deje až po načítaní.
                                month_date = pd.to_datetime(f'{year}-{month:02d}-01')
                                results_list.append({
                                    "Keyword": keyword,
                                    "Date": month_date,
                                    "Search Volume": sv,
                                    "Location Code": location_code,
                                    # Názov krajiny sa doplní vo fetcher.py
                                })
                            except ValueError:
                                # Ignorujeme neplatné dátumy
                                pass
            # Ak API vráti OK, ale žiadne výsledky (prázdny results_list), to nie je chyba API
            # to sa spracuje vo vyššej vrstve
            
        elif response_data.get("tasks") and response_data["tasks"][0].get("status_code") == 40101:
            error_msg = f"API: Kód {response_data['tasks'][0]['status_code']} - {response_data['tasks'][0]['status_message']}. Skontrolujte API prihlasovacie údaje."
        elif response_data.get("tasks"):
            error_msg = f"API: Kód {response_data['tasks'][0].get('status_code','N/A')} - {response_data['tasks'][0].get('status_message','N/A')}"
        else:
            error_msg = "API vrátilo neočakávanú štruktúru odpovede."
            logger.warning(f"Detail odpovede: {str(response_data)[:500]}")
            
    except requests.exceptions.Timeout:
        error_msg = "Chyba: Vypršal časový limit pri čakaní na odpoveď z API."
        logger.error(error_msg)
    except requests.exceptions.HTTPError as e:
        error_msg = f"Chyba HTTP pri komunikácii s API: {e}"
        logger.error(error_msg)
    except requests.exceptions.RequestException as e:
        error_msg = f"Chyba pri komunikácii s API: {e}"
        logger.error(error_msg)
    except json.JSONDecodeError:
        error_msg = f"Chyba: Nepodarilo sa dekódovať JSON odpoveď."
        logger.error(error_msg)
    except Exception as e:
        error_msg = f"Nastala neočakávaná chyba pri spracovaní API volania: {e}"
        logger.error(error_msg)
    
    return results_list, error_msg