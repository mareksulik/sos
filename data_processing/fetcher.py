"""
Modul pre načítanie dát z API a ich spracovanie pre aplikáciu.
Podporuje načítavanie dát pre jednu krajinu a pre viacero krajín.
"""
from typing import List, Dict, Tuple, Any, Optional
import streamlit as st
import pandas as pd
import time
import logging
import asyncio
import aiohttp
from datetime import datetime

# Importujeme upravenú funkciu z api_client
from api_client.dataforseo_client import get_search_volume_for_task
from config import CacheSettings, DataProcessingSettings

# Nastavenie loggera
logger = logging.getLogger(__name__)

@st.cache_data(ttl=CacheSettings.SEARCH_DATA_TTL)
def fetch_search_volume_data_single(
    login: str,
    password: str,
    kw_list_tuple: Tuple[str, ...],
    loc_code: int,
    lang_code: str,
    date_from: datetime,
    date_to: datetime
) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """
    Získa a cachuje dáta pre analýzu jednej krajiny.
    Filtruje dáta na presný časový rozsah mesiacov.
    
    Args:
        login: API prihlasovacie meno
        password: API heslo
        kw_list_tuple: Tuple kľúčových slov
        loc_code: Kód lokácie
        lang_code: Kód jazyka
        date_from: Počiatočný dátum
        date_to: Koncový dátum
        
    Returns:
        Tuple[List[Dict[str, Any]], Optional[str]]: Dvojica (výsledky, chybová správa alebo None)
    """
    keywords = list(kw_list_tuple)
    
    if not all([login, password, keywords, loc_code, lang_code, date_from, date_to]):
        if not login or not password:
            return None, "Chyba: Chýbajú API prihlasovacie údaje."
        return None, "Chyba: Chýbajú vstupné parametre pre fetch_search_volume_data_single."

    all_monthly_data_from_api, error_msg = get_search_volume_for_task(
        login, password, keywords, loc_code, lang_code, date_from, date_to
    )

    if error_msg:
        return None, error_msg
        
    if not all_monthly_data_from_api: 
        return [], None 

    # Efektívnejšie filtrovanie pomocou pandas
    try:
        # Konvertujeme na DataFrame pre efektívnejšie filtrovanie
        df = pd.DataFrame(all_monthly_data_from_api)
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Vytvoríme filtre pre dátumy
        request_start_date_ts = pd.Timestamp(date_from).replace(day=1)
        request_end_date_ts = pd.Timestamp(date_to).replace(day=1)
        
        # Filtrujeme dáta
        mask = (df['Date'] >= request_start_date_ts) & (df['Date'] <= request_end_date_ts)
        filtered_df = df[mask]
        
        # Konvertujeme naspäť na zoznam slovníkov
        filtered_results = filtered_df.to_dict('records')
    except Exception as e:
        # Fallback na pôvodný spôsob filtrovania, ak nastane chyba
        logger.error(f"Chyba pri filtrovaní dát: {e}")
        filtered_results = []
        request_start_date_ts = pd.Timestamp(date_from).replace(day=1)
        request_end_date_ts = pd.Timestamp(date_to).replace(day=1)  

        for record in all_monthly_data_from_api:
            record_date_ts = pd.Timestamp(record['Date']).replace(day=1)
            if request_start_date_ts <= record_date_ts <= request_end_date_ts:
                filtered_results.append(record)
             
    return filtered_results, None


@st.cache_data(ttl=CacheSettings.SEARCH_DATA_TTL)
def fetch_multi_country_search_volume_data(
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
    Získa a cachuje dáta pre analýzu viacerých krajín.
    Iteruje cez krajiny a volá fetch_search_volume_data_single.
    
    Args:
        login: API prihlasovacie meno
        password: API heslo
        kw_list_tuple: Tuple kľúčových slov
        selected_location_codes_tuple: Tuple kódov lokácií
        lang_code: Kód jazyka
        date_from: Počiatočný dátum
        date_to: Koncový dátum
        all_location_options_tuple: Tuple všetkých dostupných lokácií
        
    Returns:
        Tuple[pd.DataFrame, Optional[str]]: Dvojica (výsledný DataFrame, chybová správa alebo None)
    """
    all_results_list = [] 
    errors_list = []
    
    kw_list = list(kw_list_tuple)
    selected_location_codes = list(selected_location_codes_tuple)
    
    # Vytvoríme mapu z location_code na názov
    location_code_to_name_map = {code: name for name, code in list(all_location_options_tuple)}

    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, loc_code in enumerate(selected_location_codes):
        location_name = location_code_to_name_map.get(loc_code, str(loc_code))
        status_text.info(f"⏳ Získavam dáta pre krajinu: {location_name} ({i+1}/{len(selected_location_codes)})...")
        
        single_country_data_list, error_msg_single = fetch_search_volume_data_single(
            login, password, 
            tuple(kw_list), 
            loc_code,
            lang_code,
            date_from,
            date_to
        )

        if error_msg_single:
            errors_list.append(f"Chyba pre krajinu {location_name} ({loc_code}): {error_msg_single}")
            # Ak chyba obsahuje "Too many requests", môžeme pridať dlhšiu pauzu alebo zastaviť
            if "50301" in error_msg_single or "Too many requests" in error_msg_single:
                status_text.error(f"API Limit prekročený pri krajine {location_name}. Skúste znova o chvíľu alebo s menším počtom krajín.")
                # Môžeme tu vrátiť čiastočné výsledky a pokračovať
        elif single_country_data_list:
            # Možnosť optimalizácie - pridanie údajov naraz do DataFrame
            country_data = [
                {**record, 'Country': location_name} 
                for record in single_country_data_list
            ]
            all_results_list.extend(country_data)
        
        progress_bar.progress((i + 1) / len(selected_location_codes))
        
        # Pridanie pauzy medzi API volaniami, aby sa predišlo "Too many requests"
        if i < len(selected_location_codes) - 1:  # Nerobíme pauzu po poslednom volaní
            sleep_duration = DataProcessingSettings.API_RATE_LIMIT_SLEEP  # sekundy
            status_text.info(f"Pauza {sleep_duration}s pred ďalším API volaním...")
            time.sleep(sleep_duration)

    status_text.empty()
    progress_bar.empty()

    if not errors_list and not all_results_list:
        return pd.DataFrame(), "Pre zadané kritériá a vybrané krajiny neboli nájdené žiadne dáta."
    
    final_error_message = "\n".join(errors_list) if errors_list else None
    
    # Efektívnejšie vytváranie DataFrame - rovno z listu výsledkov
    all_results_df = pd.DataFrame(all_results_list) if all_results_list else pd.DataFrame()
    
    return all_results_df, final_error_message