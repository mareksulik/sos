import streamlit as st
import pandas as pd
import time # Import pre pauzu
# Importujeme upravenú funkciu z api_client
from api_client.dataforseo_client import get_search_volume_for_task 

@st.cache_data(ttl=3600) 
def fetch_search_volume_data_single(login, password, kw_list_tuple, loc_code, lang_code, date_from, date_to):
    """
    Získa a cachuje dáta pre analýzu jednej krajiny.
    Filtruje dáta na presný časový rozsah mesiacov.
    """
    keywords = list(kw_list_tuple)
    
    if not all([login, password, keywords, loc_code, lang_code, date_from, date_to]):
        if not login or not password: return None, "Chyba: Chýbajú API prihlasovacie údaje."
        return None, "Chyba: Chýbajú vstupné parametre pre fetch_search_volume_data_single."

    all_monthly_data_from_api, error_msg = get_search_volume_for_task(login, password, keywords, loc_code, lang_code, date_from, date_to)

    if error_msg:
        return None, error_msg
    if not all_monthly_data_from_api: 
        return [], None 

    filtered_results = []
    request_start_date_ts = pd.Timestamp(date_from).replace(day=1)
    request_end_date_ts = pd.Timestamp(date_to).replace(day=1)  

    for record in all_monthly_data_from_api:
        record_date_ts = pd.Timestamp(record['Date']).replace(day=1)
        if request_start_date_ts <= record_date_ts <= request_end_date_ts:
            filtered_results.append(record)
             
    return filtered_results, None


@st.cache_data(ttl=3600)
def fetch_multi_country_search_volume_data(login, password, kw_list_tuple, selected_location_codes_tuple, lang_code, date_from, date_to, all_location_options_tuple):
    """
    Získa a cachuje dáta pre analýzu viacerých krajín.
    Iteruje cez krajiny a volá fetch_search_volume_data_single.
    """
    all_results_list = [] 
    errors_list = []
    
    kw_list = list(kw_list_tuple)
    selected_location_codes = list(selected_location_codes_tuple)
    
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
                # Môžeme tu vrátiť čiastočné výsledky alebo None, None
                # Pre jednoduchosť teraz len pridáme chybu a pokračujeme (alebo by sme mohli prerušiť)
                # return pd.DataFrame(all_results_list) if all_results_list else pd.DataFrame(), "\n".join(errors_list)
        elif single_country_data_list:
            for record in single_country_data_list:
                record_with_country = record.copy() 
                record_with_country['Country'] = location_name 
                all_results_list.append(record_with_country)
        
        progress_bar.progress((i + 1) / len(selected_location_codes))
        
        # Pridanie pauzy medzi API volaniami, aby sa predišlo "Too many requests"
        if i < len(selected_location_codes) - 1: # Nerobíme pauzu po poslednom volaní
            # Počet sekúnd na pauzu; 60s / 12 req = 5s/req. Pridajme malú rezervu.
            # Ak však jedno volanie zlyhalo, možno chceme dlhšiu pauzu.
            # Pre jednoduchosť, fixná pauza.
            sleep_duration = 5.5 # sekúnd
            status_text.info(f"Pauza {sleep_duration}s pred ďalším API volaním...")
            time.sleep(sleep_duration)


    status_text.empty()
    progress_bar.empty()

    if not errors_list and not all_results_list:
        return pd.DataFrame(), "Pre zadané kritériá a vybrané krajiny neboli nájdené žiadne dáta."
    
    final_error_message = "\n".join(errors_list) if errors_list else None
    all_results_df = pd.DataFrame(all_results_list) if all_results_list else pd.DataFrame()
    
    return all_results_df, final_error_message