import streamlit as st
import requests
import base64
import json
import pandas as pd
from datetime import datetime # Použijeme datetime z datetime modulu

# Import konfigurácie
from config import LOCATIONS_URL, LANGUAGES_URL, SEARCH_VOLUME_LIVE_URL

@st.cache_data(ttl=3600) # Cache na 1 hodinu
def load_locations(login, password):
    if not login or not password: return [], "Chýbajú API prihlasovacie údaje."
    credentials = f"{login}:{password}"; encoded_credentials = base64.b64encode(credentials.encode()).decode()
    headers = {'Authorization': f'Basic {encoded_credentials}'}
    location_options = []; error_msg = None
    try:
        response = requests.get(LOCATIONS_URL, headers=headers, timeout=45)
        response.raise_for_status(); data = response.json()
        if data.get("tasks") and data["tasks"][0].get("status_code") == 20000:
            results = data["tasks"][0].get("result")
            if results:
                temp_locations = {}
                for item in results:
                    code = item.get("location_code"); name = item.get("location_name"); type = item.get("location_type")
                    display_name = f"{name}" + (f" ({type})" if type and type != "Country" else "")
                    if code and name: temp_locations[code] = {'name': name, 'type': type, 'display': display_name}
                location_options = sorted([(data['display'], code) for code, data in temp_locations.items()], key=lambda x: x[0])
            else: error_msg = "API (lokácie): Žiadne výsledky."
        elif data.get("tasks") and data["tasks"][0].get("status_code") == 40101:
             error_msg = "API (lokácie): Chyba 40101 - Neautorizované."
        elif data.get("tasks"): error_msg = f"API (lokácie): Kód {data['tasks'][0].get('status_code','N/A')} - {data['tasks'][0].get('status_message','N/A')}"
        else: error_msg = "API (lokácie): Neočakávaná odpoveď."
    except requests.exceptions.HTTPError as e:
        error_msg = f"Chyba HTTP pri komunikácii s API (lokácie): {e}"
    except requests.exceptions.RequestException as e: error_msg = f"Chyba pri komunikácii s API (lokácie): {e}"
    except Exception as e: error_msg = f"Neočekávaná chyba pri načítaní lokácií: {e}"
    return location_options, error_msg

@st.cache_data(ttl=3600) # Cache na 1 hodinu
def load_languages(login, password):
    if not login or not password: return [], "Chýbajú API prihlasovacie údaje."
    credentials = f"{login}:{password}"; encoded_credentials = base64.b64encode(credentials.encode()).decode()
    headers = {'Authorization': f'Basic {encoded_credentials}'}
    language_options = []; error_msg = None
    try:
        response = requests.get(LANGUAGES_URL, headers=headers, timeout=20)
        response.raise_for_status(); data = response.json()
        if data.get("tasks") and data["tasks"][0].get("status_code") == 20000:
            results = data["tasks"][0].get("result")
            if results:
                temp_languages = {}
                for item in results:
                    code = item.get("language_code"); name = item.get("language_name")
                    if code and name: temp_languages[code] = name
                language_options = sorted([(name, code) for code, name in temp_languages.items()], key=lambda x: x[0])
            else: error_msg = "API (jazyky): Žiadne výsledky."
        elif data.get("tasks") and data["tasks"][0].get("status_code") == 40101:
            error_msg = "API (jazyky): Chyba 40101 - Neautorizované."
        elif data.get("tasks"): error_msg = f"API (jazyky): Kód {data['tasks'][0].get('status_code','N/A')} - {data['tasks'][0].get('status_message','N/A')}"
        else: error_msg = "API (jazyky): Neočakávaná odpoveď."
    except requests.exceptions.HTTPError as e:
        error_msg = f"Chyba HTTP pri komunikácii s API (jazyky): {e}"
    except requests.exceptions.RequestException as e: error_msg = f"API (jazyky): Chyba komunikácie - {e}"
    except Exception as e: error_msg = f"Neočekávaná chyba pri načítaní jazykov: {e}"
    return language_options, error_msg

def get_search_volume_for_task(login, password, keywords, location_code, language_code, date_from, date_to):
    """Získa objem vyhľadávania pre jednu sadu parametrov (jeden task)."""
    results_list = []; error_msg = None
    
    credentials = f"{login}:{password}"; encoded_credentials = base64.b64encode(credentials.encode()).decode()
    headers = { 'Authorization': f'Basic {encoded_credentials}', 'Content-Type': 'application/json' }
    post_data = [{ 
        "keywords": keywords, 
        "location_code": location_code, 
        "language_code": language_code, 
        "date_from": date_from.strftime("%Y-%m-%d"), 
        "date_to": date_to.strftime("%Y-%m-%d"),
        "tag": "streamlit_app_request" 
    }]

    try:
        response = requests.post(SEARCH_VOLUME_LIVE_URL, headers=headers, json=post_data, timeout=60)
        response.raise_for_status(); response_data = response.json()

        if response_data.get("tasks") and response_data["tasks"][0].get("status_code") == 20000:
            task_result_items = response_data["tasks"][0].get("result")
            if task_result_items:
                for item in task_result_items:
                    keyword = item.get("keyword"); monthly_searches = item.get("monthly_searches")
                    if not keyword or not monthly_searches: continue
                    for ms_item in monthly_searches:
                        year = ms_item.get("year"); month = ms_item.get("month"); sv = ms_item.get("search_volume")
                        if year and month and sv is not None:
                            try:
                                # API vracia dáta pre celý mesiac, aj keď je dopyt na kratšie obdobie v rámci mesiaca.
                                # Filtrovanie na presné obdobie date_from/date_to sa deje až po načítaní.
                                month_date = pd.to_datetime(f'{year}-{month:02d}-01')
                                results_list.append({ 
                                    "Keyword": keyword, 
                                    "Date": month_date, 
                                    "Search Volume": sv,
                                    "Location Code": location_code, # Pridáme pre multi-country
                                    # Názov krajiny sa doplní vo fetcher.py
                                })
                            except ValueError: pass # Ignorujeme neplatné dátumy
            # Ak API vráti OK, ale žiadne výsledky (prázdny results_list), to nie je chyba API
            # to sa spracuje vo vyššej vrstve
            
        elif response_data.get("tasks") and response_data["tasks"][0].get("status_code") == 40101:
            error_msg = f"API: Kód {response_data['tasks'][0]['status_code']} - {response_data['tasks'][0]['status_message']}. Skontrolujte API prihlasovacie údaje."
        elif response_data.get("tasks"):
            error_msg = f"API: Kód {response_data['tasks'][0].get('status_code','N/A')} - {response_data['tasks'][0].get('status_message','N/A')}"
        else:
            error_msg = "API vrátilo neočakávanú štruktúru odpovede."
            st.warning(f"Detail odpovede: {str(response_data)[:500]}") # Logovanie detailu
            
    except requests.exceptions.Timeout: error_msg = "Chyba: Vypršal časový limit pri čakaní na odpoveď z API."
    except requests.exceptions.HTTPError as e:
         error_msg = f"Chyba HTTP pri komunikácii s API: {e}"
    except requests.exceptions.RequestException as e: error_msg = f"Chyba pri komunikácii s API: {e}";
    except json.JSONDecodeError: error_msg = f"Chyba: Nepodarilo sa dekódovať JSON odpoveď."
    except Exception as e: error_msg = f"Nastala neočakávaná chyba pri spracovaní API volania: {e}"
    
    return results_list, error_msg