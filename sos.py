import streamlit as st
import requests
import json
import base64
import pandas as pd
from datetime import date, timedelta
import plotly.express as px
import numpy as np

# --- Konstanty API Endpointov ---
SEARCH_VOLUME_LIVE_URL = "https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live"
LOCATIONS_URL = "https://api.dataforseo.com/v3/keywords_data/google_ads/locations"
LANGUAGES_URL = "https://api.dataforseo.com/v3/keywords_data/google_ads/languages"

# Prednastavené kľúčové slová
DEFAULT_KEYWORDS = "isadore\ncastelli\nrapha\nmaap\npas normal studios\nvan rysel"

# --- Helper funkcie pre získanie lokácií a jazykov (s cache) ---
@st.cache_data
def load_locations(login, password):
    if not login or not password: return [], "Chýbajú API prihlasovacie údaje v Streamlit Secrets."
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
             error_msg = "API (lokácie): Chyba 40101 - Neautorizované. Skontrolujte API prihlasovacie údaje v Streamlit Secrets."
        elif data.get("tasks"): status_code = data.get('tasks', [{}])[0].get('status_code', 'N/A'); status_message = data.get('tasks', [{}])[0].get('status_message', 'N/A'); error_msg = f"API (lokácie): Kód {status_code} - {status_message}"
        else: error_msg = "API (lokácie): Neočakávaná odpoveď."
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
             error_msg = "Chyba pri komunikácii s API (lokácie): 401 Unauthorized. Skontrolujte API prihlasovacie údaje v Streamlit Secrets."
        else:
             error_msg = f"Chyba pri komunikácii s API (lokácie): {e}"
    except requests.exceptions.RequestException as e: error_msg = f"Chyba pri komunikácii s API (lokácie): {e}"
    except Exception as e: error_msg = f"Neočekávaná chyba pri načítaní lokácií: {e}"
    return location_options, error_msg

@st.cache_data
def load_languages(login, password):
    if not login or not password: return [], "Chýbajú API prihlasovacie údaje v Streamlit Secrets."
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
             error_msg = "API (jazyky): Chyba 40101 - Neautorizované. Skontrolujte API prihlasovacie údaje v Streamlit Secrets."
        elif data.get("tasks"): status_code = data.get('tasks', [{}])[0].get('status_code', 'N/A'); status_message = data.get('tasks', [{}])[0].get('status_message', 'N/A'); error_msg = f"API (jazyky): Kód {status_code} - {status_message}"
        else: error_msg = "API (jazyky): Neočakávaná odpoveď."
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
             error_msg = "Chyba pri komunikácii s API (jazyky): 401 Unauthorized. Skontrolujte API prihlasovacie údaje v Streamlit Secrets."
        else:
             error_msg = f"Chyba pri komunikácii s API (jazyky): {e}"
    except requests.exceptions.RequestException as e: error_msg = f"API (jazyky): Chyba komunikácie - {e}"
    except Exception as e: error_msg = f"Neočekávaná chyba pri načítaní jazykov: {e}"
    return language_options, error_msg

@st.cache_data
def get_search_volume_live_with_history(login, password, kw_list_tuple, loc_code, lang_code, date_from, date_to):
    kw_list = list(kw_list_tuple); results_list = []; error_msg = None
    if not all([login, password, kw_list, date_from, date_to]):
        if not login or not password: return None, "Chyba: Chýbajú API prihlasovacie údaje."
        return None, "Chyba: Chýbajú základné vstupné parametre pre API volanie."
    if not loc_code: return None, "Chyba: Kód krajiny (loc_code) musí byť špecifikovaný."
    if not lang_code: return None, "Chyba: Kód jazyka (lang_code) musí byť špecifikovaný."

    credentials = f"{login}:{password}"; encoded_credentials = base64.b64encode(credentials.encode()).decode()
    headers = { 'Authorization': f'Basic {encoded_credentials}', 'Content-Type': 'application/json' }
    post_data_payload = [{ "keywords": kw_list, "location_code": loc_code, "language_code": lang_code, "date_from": date_from.strftime("%Y-%m-%d"), "date_to": date_to.strftime("%Y-%m-%d"), "tag": "streamlit_cached_history_request" }]
    try:
        response = requests.post(SEARCH_VOLUME_LIVE_URL, headers=headers, json=post_data_payload, timeout=60)
        response.raise_for_status(); response_data = response.json()
        if response_data.get("tasks") and response_data["tasks"][0].get("status_code") == 20000:
            task_result_items = response_data["tasks"][0].get("result")
            if task_result_items:
                for item in task_result_items:
                    keyword = item.get("keyword"); monthly_searches_data = item.get("monthly_searches")
                    if not keyword or not monthly_searches_data: continue
                    for monthly_item in monthly_searches_data:
                        year = monthly_item.get("year"); month = monthly_item.get("month"); search_volume_value = monthly_item.get("search_volume")
                        if year and month and search_volume_value is not None:
                            try:
                                month_date = pd.to_datetime(f'{year}-{month:02d}-01')
                                request_start_date = pd.Timestamp(date_from); request_end_date = pd.Timestamp(date_to)
                                first_day_of_month = month_date.replace(day=1)
                                if first_day_of_month >= request_start_date.replace(day=1) and first_day_of_month <= request_end_date.replace(day=1):
                                    results_list.append({ "Keyword": keyword, "Date": month_date, "Search Volume": search_volume_value })
                            except ValueError: pass
            if not results_list and response_data["tasks"][0].get("status_code") == 20000:
                error_msg = None; return [], None 
        elif response_data.get("tasks") and response_data["tasks"][0].get("status_code") == 40101:
             error_msg = f"Chyba API: Kód `{response_data['tasks'][0].get('status_code', 'N/A')}` - {response_data['tasks'][0].get('status_message', 'N/A')}. Skontrolujte API prihlasovacie údaje."
        elif response_data.get("tasks"): error_msg = f"Chyba API: Kód `{response_data['tasks'][0].get('status_code', 'N/A')}` - {response_data['tasks'][0].get('status_message', 'N/A')}"
        else: error_msg = "Chyba: API vrátilo neočakávanú štruktúru odpovede."; st.warning(f"Detail odpovede: {str(response_data)[:500]}")
    except requests.exceptions.Timeout: error_msg = "Chyba: Vypršal časový limit pri čakaní na odpoveď z API."
    except requests.exceptions.HTTPError as e:
         if e.response.status_code == 401: error_msg = "Chyba pri komunikácii s API: 401 Unauthorized. Skontrolujte API prihlasovacie údaje."
         else: error_msg = f"Chyba pri komunikácii s API: {e}"
    except requests.exceptions.RequestException as e: error_msg = f"Chyba pri komunikácii s API: {e}";
    except json.JSONDecodeError: error_msg = f"Chyba: Nepodarilo sa dekódovať JSON odpoveď.\n   Obsah (prvých 500 znakov): {response.text[:500]}"
    except Exception as e: error_msg = f"Nastala neočakávaná chyba v spracovaní API volania: {e}"

    if error_msg: return None, error_msg
    elif not results_list: return [], None
    else: return results_list, None

@st.cache_data
def get_multi_country_search_volume_history(login, password, kw_list_tuple, selected_location_codes_tuple, lang_code, date_from, date_to, all_location_options_tuple):
    all_results_df = pd.DataFrame()
    errors_list = [] 
    kw_list = list(kw_list_tuple)
    selected_location_codes = list(selected_location_codes_tuple)
    location_code_to_name_map = {code: name for name, code in list(all_location_options_tuple)}
    progress_bar = st.progress(0)
    status_text = st.empty() 

    for i, loc_code in enumerate(selected_location_codes):
        location_name_for_status = location_code_to_name_map.get(loc_code, str(loc_code))
        status_text.info(f"⏳ Získavam dáta pre krajinu: {location_name_for_status} ({i+1}/{len(selected_location_codes)})...")
        single_country_data, error_msg_single = get_search_volume_live_with_history(
            login, password, tuple(kw_list), loc_code, lang_code, date_from, date_to
        )
        if error_msg_single:
            errors_list.append(f"Chyba pre krajinu {location_name_for_status} ({loc_code}): {error_msg_single}")
        elif single_country_data: 
            df_country = pd.DataFrame(single_country_data)
            if not df_country.empty:
                df_country['Location Code'] = loc_code
                df_country['Country'] = location_name_for_status 
                all_results_df = pd.concat([all_results_df, df_country], ignore_index=True)
        progress_bar.progress((i + 1) / len(selected_location_codes))
    status_text.empty() 
    progress_bar.empty() 
    if not errors_list and all_results_df.empty:
        return pd.DataFrame(), "Pre zadané kritériá a vybrané krajiny neboli nájdené žiadne dáta."
    final_error_message = "\n".join(errors_list) if errors_list else None
    return all_results_df, final_error_message

# --- Funkcia pre vykreslenie stránky s viacerými krajinami ---
def render_multi_country_page(api_login, api_password, location_options_all, language_options_all, locations_error_msg, languages_error_msg):
    st.header("🌍 Analýza viacerých krajín")
    col1_mc, col2_mc, col3_mc = st.columns(3)
    with col1_mc:
        st.subheader("Kľúčové slová")
        if 'mc_keywords_input' not in st.session_state:
            st.session_state.mc_keywords_input = DEFAULT_KEYWORDS
        st.text_area("Zadajte kľúčové slová:", key="mc_keywords_input", height=150)

    with col2_mc:
        st.subheader("Krajiny (Hlavný filter)")
        loc_display_list_mc = [opt[0] for opt in location_options_all]
        code_to_display_name_map_mc = {code: name for name, code in location_options_all} if location_options_all else {}

        if not location_options_all or not api_login or not api_password:
            st.info("Zoznam krajín nie je dostupný. Skontrolujte API prihlasovacie údaje alebo chyby načítania.")
            if locations_error_msg and (api_login and api_password):
                 st.warning(f"Chyba pri načítaní lokácií: {locations_error_msg}")
        else:
            if 'mc_selected_locations' not in st.session_state: 
                default_loc_codes_priority = [2703, 2203, 2276, 2040] # SK, CZ, DE, AT
                default_display_names_to_set = [code_to_display_name_map_mc[code] for code in default_loc_codes_priority if code in code_to_display_name_map_mc]
                default_display_names_to_set = [name for name in default_display_names_to_set if name in loc_display_list_mc] 
                if not default_display_names_to_set: 
                    if len(loc_display_list_mc) >= 2: default_display_names_to_set = loc_display_list_mc[:2]
                    elif loc_display_list_mc: default_display_names_to_set = loc_display_list_mc[:1]
                    else: default_display_names_to_set = []
                st.session_state.mc_selected_locations = default_display_names_to_set
            
            st.multiselect("Vyberte krajiny pre analýzu:", options=loc_display_list_mc, key="mc_selected_locations", help="Vyberte jednu alebo viac krajín, pre ktoré sa načítajú dáta.")
            st.info("Poznámka: Výber veľkého počtu krajín môže predĺžiť čas načítania dát. API má limit 12 požiadaviek za minútu na účet.")
            
        st.subheader("Jazyk")
        if not language_options_all or not api_login or not api_password:
            st.info("Zoznam jazykov nie je dostupný.")
            if languages_error_msg and (api_login and api_password): st.warning(f"Chyba pri načítaní jazykov: {languages_error_msg}")
        else:
            lang_display_list_mc = [opt[0] for opt in language_options_all]
            if 'mc_language_select' not in st.session_state:
                default_lang_name_mc = next((name for name, code in language_options_all if code.lower() == 'en'), lang_display_list_mc[0] if lang_display_list_mc else "")
                st.session_state.mc_language_select = default_lang_name_mc
            st.selectbox("Vyberte jazyk (pre všetky krajiny):", options=lang_display_list_mc, key="mc_language_select")

    with col3_mc:
        st.subheader("Rozsah dátumov")
        today_mc = date.today()
        default_end_date_mc = today_mc.replace(day=1) - timedelta(days=1)
        default_start_date_mc = date(2022, 1, 1) 
        if default_end_date_mc < default_start_date_mc: 
            default_end_date_mc = default_start_date_mc.replace(year=default_start_date_mc.year + 1, day=1) - timedelta(days=1)
            if default_end_date_mc > (today_mc.replace(day=1) - timedelta(days=1)): default_end_date_mc = today_mc.replace(day=1) - timedelta(days=1)
        if 'mc_date_from' not in st.session_state: st.session_state.mc_date_from = default_start_date_mc
        if 'mc_date_to' not in st.session_state: st.session_state.mc_date_to = default_end_date_mc
        if st.session_state.mc_date_from > st.session_state.mc_date_to :
            st.session_state.mc_date_to = st.session_state.mc_date_from 
            if st.session_state.mc_date_to > (today_mc.replace(day=1) - timedelta(days=1)):
                 st.session_state.mc_date_to = today_mc.replace(day=1) - timedelta(days=1)
                 if st.session_state.mc_date_from > st.session_state.mc_date_to:
                     st.session_state.mc_date_from = st.session_state.mc_date_to.replace(year=st.session_state.mc_date_to.year -1)
        st.date_input("Dátum od:", value=st.session_state.mc_date_from, min_value=date(2022, 1, 1), max_value=st.session_state.mc_date_to, key="mc_date_from")
        st.date_input("Dátum do:", value=st.session_state.mc_date_to, min_value=st.session_state.mc_date_from, max_value=today_mc.replace(day=1) - timedelta(days=1), key="mc_date_to")
        
        st.subheader("Granularita Zobrazenia")
        mc_granularity_options = ['Ročne', 'Štvrťročne', 'Mesačne']
        if 'mc_granularity_choice' not in st.session_state: 
            st.session_state.mc_granularity_choice = 'Ročne' 
        st.radio("Agregovať dáta:", options=mc_granularity_options, key="mc_granularity_choice", horizontal=True)

    keywords_list_mc = [kw.strip() for kw in st.session_state.mc_keywords_input.splitlines() if kw.strip()]
    selected_main_countries_display = st.session_state.get('mc_selected_locations', [])
    selected_location_codes_mc = []
    loc_code_map_mc = {opt[0]: opt[1] for opt in location_options_all} if location_options_all else {}
    if location_options_all and selected_main_countries_display and loc_code_map_mc:
        selected_location_codes_mc = [loc_code_map_mc[name] for name in selected_main_countries_display if name in loc_code_map_mc]
    
    selected_language_code_mc = None 
    if 'mc_language_select' in st.session_state and language_options_all:
        temp_lang_code_map_mc_local = {name: code for name, code in language_options_all}
        selected_language_code_mc = temp_lang_code_map_mc_local.get(st.session_state.mc_language_select)

    date_from_input_mc = st.session_state.mc_date_from
    date_to_input_mc = st.session_state.mc_date_to
    granularity_mc = st.session_state.mc_granularity_choice
    
    run_button_disabled_mc = not selected_location_codes_mc or not selected_language_code_mc or not api_login or not api_password or not keywords_list_mc
    mc_session_key = f"multi_data_{tuple(sorted(keywords_list_mc))}_{tuple(sorted(selected_location_codes_mc))}_{selected_language_code_mc}_{date_from_input_mc}_{date_to_input_mc}_{granularity_mc}"
    mc_cache_info_placeholder = st.empty()

    if mc_session_key in st.session_state and st.session_state[mc_session_key].get("data") is not None:
         mc_cache_info_placeholder.success("✅ Dáta pre tieto parametre (analýza viacerých krajín) sú v cache session.")

    if st.button("📊 Získať dáta a zobraziť grafy (Analýza viacerých krajín)", type="primary", disabled=run_button_disabled_mc, key="mc_run_button"):
        if not keywords_list_mc: st.warning("⚠️ Zadajte kľúčové slová.")
        elif not selected_location_codes_mc: st.warning("⚠️ Vyberte aspoň jednu krajinu v hlavnom filtri.")
        elif not selected_language_code_mc: st.warning("⚠️ Vyberte jazyk.")
        elif date_from_input_mc > date_to_input_mc: st.error("🚨 Dátum 'od' nemôže byť neskorší ako 'do'.")
        else:
            keywords_tuple_mc = tuple(sorted(keywords_list_mc))
            locations_tuple_mc = tuple(sorted(selected_location_codes_mc))
            all_loc_options_tuple_for_cache = tuple(location_options_all) if location_options_all else tuple()
            loaded_from_session_mc = False
            if mc_session_key in st.session_state:
                results_df_mc = st.session_state[mc_session_key].get("data") 
                error_msg_mc = st.session_state[mc_session_key].get("error") 
                if results_df_mc is not None or error_msg_mc is not None:
                     mc_cache_info_placeholder.success("✅ Používam dáta z cache session (analýza viacerých krajín).")
                     loaded_from_session_mc = True
            if not loaded_from_session_mc:
                mc_cache_info_placeholder.info("ℹ️ Cache session (analýza viacerých krajín) nenájdená, volám API...")
                results_df_mc, error_msg_mc = get_multi_country_search_volume_history(
                    api_login, api_password, keywords_tuple_mc, locations_tuple_mc, 
                    selected_language_code_mc, date_from_input_mc, date_to_input_mc,
                    all_loc_options_tuple_for_cache 
                )
                st.session_state[mc_session_key] = {"data": results_df_mc, "error": error_msg_mc, "granularity": granularity_mc}
                mc_cache_info_placeholder.empty() 
            current_df_mc_on_run = st.session_state[mc_session_key].get("data") 
            current_error_mc_on_run = st.session_state[mc_session_key].get("error") 
            if not loaded_from_session_mc and not current_error_mc_on_run and current_df_mc_on_run is not None and not current_df_mc_on_run.empty:
                st.success("✅ Dáta (analýza viacerých krajín) úspešne získané z API!")
    
    if mc_session_key in st.session_state:
        current_df_mc = st.session_state[mc_session_key].get("data") 
        current_error_mc = st.session_state[mc_session_key].get("error")
        granularity_mc_for_display = st.session_state.mc_granularity_choice 

        if current_error_mc:
            if "Pre zadané kritériá" in current_error_mc and (current_df_mc is None or current_df_mc.empty):
                 st.info(f"ℹ️ {current_error_mc}")
            else: st.error(f"🚨 Nastala chyba pri získavaní dát (analýza viacerých krajín):\n{current_error_mc}")
        elif current_df_mc is not None: 
            if current_df_mc.empty:
                st.info("ℹ️ Neboli nájdené žiadne historické dáta pre kombináciu zadaných kľúčových slov, krajín a jazyka v danom časovom období.")
            else:
                mc_history_df_raw = current_df_mc.copy()
                mc_history_df_raw['Date'] = pd.to_datetime(mc_history_df_raw['Date'])
                
                mc_history_df_agg_base = mc_history_df_raw.copy() 
                period_col_name_mc = 'Period'
                granularity_label_mc_display = granularity_mc_for_display.replace('e','á')
                
                def aggregate_data_mc(df, granularity_str, period_col_name): # Premenovaná funkcia
                    agg_df = df.copy()
                    sort_key_func_local = None 
                    if granularity_str == 'Ročne': 
                        agg_df[period_col_name] = agg_df['Date'].dt.year.astype(str)
                        sort_key_func_local = lambda x: pd.to_numeric(x)
                    elif granularity_str == 'Štvrťročne': 
                        agg_df[period_col_name] = agg_df['Date'].dt.to_period('Q').astype(str)
                        sort_key_func_local = lambda x: pd.Period(x, freq='Q')
                    else: # Mesačne
                        agg_df[period_col_name] = agg_df['Date'].dt.strftime('%Y-%m')
                        sort_key_func_local = lambda x: pd.to_datetime(x, format='%Y-%m')
                    return agg_df, sort_key_func_local

                mc_history_df_agg, period_sort_key_mc = aggregate_data_mc(mc_history_df_agg_base, granularity_mc_for_display, period_col_name_mc)

                # --- GRAFY PRE MULTI-COUNTRY ---
                st.markdown("---"); st.subheader(f"1. Celkový Share of Search ({granularity_label_mc_display}) naprieč všetkými vybranými krajinami")
                try:
                    df_for_graph1 = mc_history_df_agg.copy()
                    total_sos_data_g1 = df_for_graph1.groupby([period_col_name_mc, 'Keyword'], observed=False)['Search Volume'].sum().reset_index()
                    total_market_volume_g1 = total_sos_data_g1.groupby(period_col_name_mc, observed=False)['Search Volume'].sum().reset_index().rename(columns={'Search Volume': 'Total Market Volume'})
                    merged_total_sos_g1 = pd.merge(total_sos_data_g1, total_market_volume_g1, on=period_col_name_mc)
                    merged_total_sos_g1['Share_Percent'] = 0.0 
                    mask_total_sos_g1 = merged_total_sos_g1['Total Market Volume'] > 0
                    merged_total_sos_g1.loc[mask_total_sos_g1, 'Share_Percent'] = (merged_total_sos_g1['Search Volume'] / merged_total_sos_g1['Total Market Volume']) * 100
                    merged_total_sos_g1.fillna({'Share_Percent': 0, 'Search Volume': 0}, inplace=True)
                    if not merged_total_sos_g1.empty and merged_total_sos_g1['Total Market Volume'].sum() > 0:
                        unique_periods_graph1 = sorted(merged_total_sos_g1[period_col_name_mc].unique(), key=period_sort_key_mc)
                        keyword_order_graph1 = list(merged_total_sos_g1.groupby('Keyword')['Search Volume'].sum().sort_values(ascending=False).index)
                        fig_graph1 = px.bar(merged_total_sos_g1[merged_total_sos_g1['Total Market Volume'] > 0], x=period_col_name_mc, y='Share_Percent', color='Keyword', text='Share_Percent', barmode='stack', labels={'Share_Percent': '% Podiel', 'Keyword': 'Značka', period_col_name_mc: granularity_label_mc_display}, title="1. Celkový SoS (Podiel % naprieč všetkými vybranými krajinami)", category_orders={"Keyword": keyword_order_graph1, period_col_name_mc: unique_periods_graph1})
                        fig_graph1.update_layout(yaxis_title='% celkového objemu', yaxis_ticksuffix="%", xaxis_type='category', legend_title_text='Značky', height=600)
                        fig_graph1.update_traces(texttemplate='%{text:.1f}%', textposition='inside', insidetextanchor='middle', textfont_size=12)
                        st.plotly_chart(fig_graph1, use_container_width=True)
                    else: st.info("Nedostatok dát pre graf '1. Celkový Share of Search'.")
                except Exception as e: st.error(f"Chyba pri generovaní grafu '1. Celkový Share of Search': {e}")

                st.markdown("---"); st.subheader(f"2. Celkový priemerný objem vyhľadávania ({granularity_label_mc_display}) naprieč všetkými vybranými krajinami")
                try:
                    df_for_graph2 = mc_history_df_agg.copy()
                    graph2_data = pd.DataFrame() # Inicializácia
                    if granularity_mc_for_display != 'Mesačne':
                        monthly_agg_for_g2 = mc_history_df_raw.copy()
                        monthly_agg_for_g2['MonthPeriod'] = monthly_agg_for_g2['Date'].dt.to_period('M')
                        g2_monthly_brand_sums = monthly_agg_for_g2.groupby(['MonthPeriod', 'Keyword'], observed=False)['Search Volume'].sum().reset_index()
                        if granularity_mc_for_display == 'Ročne': g2_monthly_brand_sums[period_col_name_mc] = g2_monthly_brand_sums['MonthPeriod'].dt.year.astype(str)
                        elif granularity_mc_for_display == 'Štvrťročne': g2_monthly_brand_sums[period_col_name_mc] = g2_monthly_brand_sums['MonthPeriod'].dt.to_period('Q').astype(str)
                        graph2_data = g2_monthly_brand_sums.groupby([period_col_name_mc, 'Keyword'], observed=False)['Search Volume'].mean().reset_index()
                    else: 
                        graph2_data = df_for_graph2.groupby([period_col_name_mc, 'Keyword'], observed=False)['Search Volume'].sum().reset_index() 
                    
                    if not graph2_data.empty:
                        unique_periods_graph2 = sorted(graph2_data[period_col_name_mc].unique(), key=period_sort_key_mc)
                        keyword_order_graph2 = list(graph2_data.groupby('Keyword')['Search Volume'].sum().sort_values(ascending=False).index)
                        fig_graph2 = px.line(graph2_data, x=period_col_name_mc, y='Search Volume', color='Keyword', labels={'Search Volume': 'Priemerný objem', 'Keyword': 'Značka', period_col_name_mc: granularity_label_mc_display}, title="2. Celkový priemerný objem naprieč všetkými vybranými krajinami", markers=True, category_orders={"Keyword": keyword_order_graph2, period_col_name_mc: unique_periods_graph2})
                        fig_graph2.update_layout(yaxis_title='Priemerný objem vyhľadávania', legend_title_text='Značky', height=600)
                        st.plotly_chart(fig_graph2, use_container_width=True)
                    else: st.info("Nedostatok dát pre graf '2. Celkový priemerný objem vyhľadávania'.")
                except Exception as e: st.error(f"Chyba pri generovaní grafu '2. Celkový priemerný objem vyhľadávania': {e}")

                st.markdown("---"); st.subheader(f"3. Flexibilný SoS pre vlastný výber krajín a značiek ({granularity_label_mc_display})")
                col_flex_sos_kw, col_flex_sos_co = st.columns(2)
                available_keywords_flex_sos = sorted(mc_history_df_agg['Keyword'].unique())
                available_countries_flex_sos = sorted(mc_history_df_agg['Country'].unique())
                with col_flex_sos_kw:
                    if 'flex_sos_keywords' not in st.session_state or not set(st.session_state.flex_sos_keywords).issubset(set(available_keywords_flex_sos)): 
                        st.session_state.flex_sos_keywords = available_keywords_flex_sos[:3] if len(available_keywords_flex_sos) >=3 else available_keywords_flex_sos
                    selected_flex_sos_keywords = st.multiselect("Vyberte značky pre graf 3:", options=available_keywords_flex_sos, key="flex_sos_keywords")
                with col_flex_sos_co:
                    if 'flex_sos_countries' not in st.session_state or not set(st.session_state.flex_sos_countries).issubset(set(available_countries_flex_sos)):
                        st.session_state.flex_sos_countries = available_countries_flex_sos[:2] if len(available_countries_flex_sos) >=2 else available_countries_flex_sos
                    selected_flex_sos_countries = st.multiselect("Vyberte krajiny pre graf 3 (dáta sa sčítajú):", options=available_countries_flex_sos, key="flex_sos_countries")

                if selected_flex_sos_keywords and selected_flex_sos_countries:
                    try:
                        df_flex_sos_filtered = mc_history_df_agg[mc_history_df_agg['Keyword'].isin(selected_flex_sos_keywords) & mc_history_df_agg['Country'].isin(selected_flex_sos_countries)].copy()
                        if not df_flex_sos_filtered.empty:
                            flex_sos_brand_volumes = df_flex_sos_filtered.groupby([period_col_name_mc, 'Keyword'], observed=False)['Search Volume'].sum().reset_index()
                            flex_sos_total_market = flex_sos_brand_volumes.groupby(period_col_name_mc, observed=False)['Search Volume'].sum().reset_index().rename(columns={'Search Volume': 'Total Flex Market'})
                            flex_sos_merged = pd.merge(flex_sos_brand_volumes, flex_sos_total_market, on=period_col_name_mc)
                            flex_sos_merged['SoS_Percent'] = 0.0
                            flex_mask = flex_sos_merged['Total Flex Market'] > 0
                            flex_sos_merged.loc[flex_mask, 'SoS_Percent'] = (flex_sos_merged['Search Volume'] / flex_sos_merged['Total Flex Market']) * 100
                            flex_sos_merged.fillna({'SoS_Percent': 0}, inplace=True)
                            if not flex_sos_merged.empty:
                                unique_periods_flex_sos = sorted(flex_sos_merged[period_col_name_mc].unique(), key=period_sort_key_mc)
                                keyword_order_flex_sos = list(flex_sos_merged.groupby('Keyword')['Search Volume'].sum().sort_values(ascending=False).index)
                                fig_flex_sos = px.line(flex_sos_merged, x=period_col_name_mc, y='SoS_Percent', color='Keyword', labels={'SoS_Percent': 'SoS (%)', 'Keyword': 'Značka', period_col_name_mc: granularity_label_mc_display}, title=f"3. SoS pre vybrané značky a sčítané krajiny", markers=True, category_orders={"Keyword": keyword_order_flex_sos, period_col_name_mc: unique_periods_flex_sos})
                                fig_flex_sos.update_layout(yaxis_title='Share of Search (%)', yaxis_ticksuffix="%", legend_title_text='Značky', height=600)
                                st.plotly_chart(fig_flex_sos, use_container_width=True)
                            else: st.info("Nedostatok dát pre graf '3. Flexibilný SoS' s vybranými parametrami (po agregácii).")
                        else: st.info("Nenašli sa žiadne dáta pre vybranú kombináciu značiek a krajín pre graf 3.")
                    except Exception as e: st.error(f"Chyba pri generovaní grafu '3. Flexibilný SoS': {e}")
                else: st.info("Vyberte aspoň jednu značku a jednu krajinu pre '3. Flexibilný SoS'.")

                st.markdown("---"); st.subheader(f"4. Flexibilný súhrnný objem pre vlastný výber krajín a značiek ({granularity_label_mc_display})")
                col_flex_vol_kw, col_flex_vol_co = st.columns(2)
                with col_flex_vol_kw:
                    if 'flex_vol_keywords_g4' not in st.session_state or not set(st.session_state.flex_vol_keywords_g4).issubset(set(available_keywords_flex_sos)): 
                        st.session_state.flex_vol_keywords_g4 = available_keywords_flex_sos[:3] if len(available_keywords_flex_sos) >=3 else available_keywords_flex_sos
                    selected_flex_vol_keywords_g4 = st.multiselect("Vyberte značky pre graf 4:", options=available_keywords_flex_sos, key="flex_vol_keywords_g4")
                with col_flex_vol_co:
                    if 'flex_vol_countries_g4' not in st.session_state or not set(st.session_state.flex_vol_countries_g4).issubset(set(available_countries_flex_sos)):
                        st.session_state.flex_vol_countries_g4 = available_countries_flex_sos[:2] if len(available_countries_flex_sos) >=2 else available_countries_flex_sos
                    selected_flex_vol_countries_g4 = st.multiselect("Vyberte krajiny pre graf 4 (dáta sa sčítajú):", options=available_countries_flex_sos, key="flex_vol_countries_g4")

                if selected_flex_vol_keywords_g4 and selected_flex_vol_countries_g4:
                    try:
                        df_flex_vol_filtered_g4 = mc_history_df_agg[mc_history_df_agg['Keyword'].isin(selected_flex_vol_keywords_g4) & mc_history_df_agg['Country'].isin(selected_flex_vol_countries_g4)].copy()
                        if not df_flex_vol_filtered_g4.empty:
                            flex_vol_brand_volumes_g4 = df_flex_vol_filtered_g4.groupby([period_col_name_mc, 'Keyword'], observed=False)['Search Volume'].sum().reset_index()
                            if not flex_vol_brand_volumes_g4.empty:
                                unique_periods_flex_vol_g4 = sorted(flex_vol_brand_volumes_g4[period_col_name_mc].unique(), key=period_sort_key_mc)
                                keyword_order_flex_vol_g4 = list(flex_vol_brand_volumes_g4.groupby('Keyword')['Search Volume'].sum().sort_values(ascending=False).index)
                                fig_flex_vol_g4 = px.line(flex_vol_brand_volumes_g4, x=period_col_name_mc, y='Search Volume', color='Keyword', labels={'Search Volume': 'Súhrnný objem', 'Keyword': 'Značka', period_col_name_mc: granularity_label_mc_display}, title=f"4. Súhrnný objem pre vybrané značky a sčítané krajiny", markers=True, category_orders={"Keyword": keyword_order_flex_vol_g4, period_col_name_mc: unique_periods_flex_vol_g4})
                                fig_flex_vol_g4.update_layout(yaxis_title='Súhrnný objem vyhľadávania', legend_title_text='Značky', height=600)
                                st.plotly_chart(fig_flex_vol_g4, use_container_width=True)
                            else: st.info("Nedostatok dát pre graf '4. Flexibilný súhrnný objem' s vybranými parametrami (po agregácii).")
                        else: st.info("Nenašli sa žiadne dáta pre vybranú kombináciu značiek a krajín pre graf 4.")
                    except Exception as e: st.error(f"Chyba pri generovaní grafu '4. Flexibilný súhrnný objem': {e}")
                else: st.info("Vyberte aspoň jednu značku a jednu krajinu pre '4. Flexibilný súhrnný objem'.")

                st.markdown("---"); st.subheader(f"5. Priemerný mesačný objem segmentu ({granularity_label_mc_display})")
                st.markdown("Graf zobrazuje celkový priemerný mesačný objem vyhľadávania všetkých sledovaných značiek dohromady pre vybranú skupinu krajín.")
                available_countries_graph5 = sorted(mc_history_df_agg['Country'].unique())
                if 'selected_countries_graph5' not in st.session_state or not set(st.session_state.selected_countries_graph5).issubset(set(available_countries_graph5)):
                    st.session_state.selected_countries_graph5 = available_countries_graph5[:1] if available_countries_graph5 else []
                selected_countries_for_graph5 = st.multiselect("Vyberte krajiny pre graf 5 (dáta sa sčítajú):", options=available_countries_graph5, key="selected_countries_graph5")
                
                if selected_countries_for_graph5:
                    try:
                        df_graph5_filtered = mc_history_df_agg[mc_history_df_agg['Country'].isin(selected_countries_for_graph5)].copy()
                        if not df_graph5_filtered.empty:
                            graph5_total_volume_per_period = df_graph5_filtered.groupby(period_col_name_mc, observed=False)['Search Volume'].sum().reset_index()
                            df_raw_filtered_for_g5 = mc_history_df_raw[mc_history_df_raw['Country'].isin(selected_countries_for_graph5)].copy()
                            df_raw_filtered_for_g5['MonthYear'] = df_raw_filtered_for_g5['Date'].dt.to_period('M')
                            
                            temp_period_col_name_g5 = 'Period_g5_temp'
                            if granularity_mc_for_display == 'Ročne': df_raw_filtered_for_g5[temp_period_col_name_g5] = df_raw_filtered_for_g5['Date'].dt.year.astype(str)
                            elif granularity_mc_for_display == 'Štvrťročne': df_raw_filtered_for_g5[temp_period_col_name_g5] = df_raw_filtered_for_g5['Date'].dt.to_period('Q').astype(str)
                            else: df_raw_filtered_for_g5[temp_period_col_name_g5] = df_raw_filtered_for_g5['Date'].dt.strftime('%Y-%m')

                            months_in_period_graph5 = df_raw_filtered_for_g5.groupby(temp_period_col_name_g5, observed=False)['MonthYear'].nunique().reset_index(name='NumMonths')
                            months_in_period_graph5.rename(columns={temp_period_col_name_g5: period_col_name_mc}, inplace=True)
                            
                            graph5_avg_data = pd.merge(graph5_total_volume_per_period, months_in_period_graph5, on=period_col_name_mc, how="left")
                            graph5_avg_data['NumMonths'].fillna(1, inplace=True) 
                            graph5_avg_data['AvgMonthlySegmentVolume'] = graph5_avg_data.apply(lambda row: row['Search Volume'] / row['NumMonths'] if row['NumMonths'] > 0 else 0, axis=1)
                            
                            if not graph5_avg_data.empty:
                                unique_periods_g5 = sorted(graph5_avg_data[period_col_name_mc].unique(), key=period_sort_key_mc)
                                fig_g5_segment = px.bar(graph5_avg_data, x=period_col_name_mc, y='AvgMonthlySegmentVolume', labels={'AvgMonthlySegmentVolume': 'Priem. mesačný objem segmentu', period_col_name_mc: granularity_label_mc_display}, title=f"5. Priemerný mesačný objem segmentu (vybrané krajiny)", category_orders={period_col_name_mc: unique_periods_g5})
                                fig_g5_segment.update_layout(yaxis_title='Priemerný mesačný objem vyhľadávania', height=500)
                                fig_g5_segment.update_traces(texttemplate='%{y:,.0f}', textposition='outside')
                                st.plotly_chart(fig_g5_segment, use_container_width=True)
                            else: st.info("Nedostatok dát pre graf '5. Priemerný mesačný objem segmentu'.")
                        else: st.info("Nenašli sa žiadne dáta pre vybrané krajiny pre graf 5.")
                    except Exception as e: st.error(f"Chyba pri generovaní grafu '5. Priemerný mesačný objem segmentu': {e}")
                else: st.info("Vyberte aspoň jednu krajinu pre graf 5.")
                
                # Graf 6 (pôvodný multi-brand, single-country volume) bol odstránený
                
                st.markdown("---"); st.subheader("6. Stiahnuť dáta ako CSV (Analýza viacerých krajín)")
                try:
                     if not mc_history_df_raw.empty:
                          @st.cache_data 
                          def convert_df_to_csv_mc_v3(df_to_convert_mc):
                              df_sorted_mc = df_to_convert_mc[['Keyword', 'Country', 'Location Code', 'Date', 'Search Volume']].sort_values(by=['Keyword', 'Country', 'Date'])
                              df_sorted_mc['Date'] = pd.to_datetime(df_sorted_mc['Date']).dt.strftime('%Y-%m-%d')
                              return df_sorted_mc.to_csv(index=False).encode('utf-8')
                          csv_data_mc_v3 = convert_df_to_csv_mc_v3(mc_history_df_raw.copy())
                          st.download_button(label="Stiahnuť dáta (analýza viacerých krajín) ako CSV", data=csv_data_mc_v3, file_name=f'dataforseo_multi_country_monthly_data.csv', mime='text/csv', key="download_csv_mc_button_v3")
                except Exception as e: st.error(f"Chyba pri príprave CSV na stiahnutie (analýza viacerých krajín): {e}")

                st.markdown("---"); st.subheader("7. História vyhľadávaní (Analýza viacerých krajín)")
                if 'search_history_multi' not in st.session_state: st.session_state.search_history_multi = []
                current_display_country_names_mc = st.session_state.get('mc_selected_locations', [])
                current_language_name_mc = st.session_state.get('mc_language_select', "")
                current_location_codes_mc_hist = [] 
                if location_options_all and current_display_country_names_mc:
                    temp_loc_code_map_mc_hist = {name: code for name, code in location_options_all}
                    current_location_codes_mc_hist = [temp_loc_code_map_mc_hist[name] for name in current_display_country_names_mc if name in temp_loc_code_map_mc_hist]

                current_request_info_multi = {
                    'keywords': keywords_list_mc, 'countries_display': current_display_country_names_mc, 
                    'location_codes': current_location_codes_mc_hist, 'language': current_language_name_mc, 
                    'language_code': selected_language_code_mc, 'date_from': date_from_input_mc, 
                    'date_to': date_to_input_mc, 'granularity': granularity_mc_for_display, 
                    'session_key': mc_session_key, 'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                request_exists_multi = any(hist_item['session_key'] == mc_session_key for hist_item in st.session_state.search_history_multi)
                if not request_exists_multi and current_df_mc is not None and not current_df_mc.empty:
                    st.session_state.search_history_multi.append(current_request_info_multi)
                if st.session_state.search_history_multi:
                    with st.expander("📋 Zoznam predchádzajúcich vyhľadávaní (Analýza viacerých krajín)", expanded=False):
                        for i, hist_item in enumerate(reversed(st.session_state.search_history_multi)):
                            col_h1, col_h2, col_h3 = st.columns([3,2,1])
                            with col_h1:
                                kw_summary = ", ".join(hist_item['keywords'][:3]) + (f" a ďalšie {len(hist_item['keywords'])-3}" if len(hist_item['keywords']) > 3 else "")
                                st.markdown(f"**Kľúčové slová:** {kw_summary}")
                                countries_summary = ", ".join(hist_item['countries_display'][:2]) + (f" a ďalšie {len(hist_item['countries_display'])-2}" if len(hist_item['countries_display']) > 2 else "")
                                st.markdown(f"**Krajiny:** {countries_summary}")
                            with col_h2:
                                st.markdown(f"**Jazyk:** {hist_item['language']}")
                                st.markdown(f"**Obdobie:** {hist_item['date_from'].strftime('%Y-%m-%d')} až {hist_item['date_to'].strftime('%Y-%m-%d')}")
                            with col_h3:
                                if st.button("Načítať", key=f"load_hist_multi_{hist_item['session_key']}"):
                                    st.session_state.mc_keywords_input = "\n".join(hist_item['keywords'])
                                    st.session_state.mc_selected_locations = hist_item['countries_display']
                                    st.session_state.mc_language_select = hist_item['language']
                                    st.session_state.mc_date_from = hist_item['date_from']
                                    st.session_state.mc_date_to = hist_item['date_to']
                                    st.session_state.mc_granularity_choice = hist_item['granularity']
                                    st.rerun()
                            st.markdown(f"*Čas vyhľadávania: {hist_item['timestamp']}*")
                            if i < len(st.session_state.search_history_multi) -1: st.markdown("---")
                    if st.button("🗑️ Vymazať históriu (Analýza viacerých krajín)", key="clear_hist_multi_button"):
                        st.session_state.search_history_multi = []
                        st.success("História vyhľadávaní (Analýza viacerých krajín) bola vymazaná.")
                        st.rerun()
                else: st.info("Zatiaľ nemáte žiadne vyhľadávania v histórii (Analýza viacerých krajín).")
    elif run_button_disabled_mc and (api_login and api_password):
        missing_parts = []
        if not keywords_list_mc: missing_parts.append("kľúčové slová")
        if not selected_location_codes_mc: missing_parts.append("aspoň jednu krajinu")
        if not selected_language_code_mc: missing_parts.append("jazyk")
        if missing_parts: st.warning(f"⚠️ Vyberte prosím {', '.join(missing_parts)} pre pokračovanie v Analýze viacerých krajín.")

# --- Streamlit Aplikácia ---
st.set_page_config(page_title="Share of Search", layout="wide")
st.title("Share of Search Tool")
app_pin = st.secrets.get("app", {}).get("pin")
pin_placeholder = st.empty() 
if not app_pin:
    st.error("Chyba konfigurácie: PIN kód nie je nastavený v Streamlit Secrets ([app] -> pin). Aplikácia nemôže pokračovať.")
    st.stop() 
if 'authenticated' not in st.session_state: st.session_state.authenticated = False
if not st.session_state.authenticated:
    entered_pin = pin_placeholder.text_input("🔑 Zadajte prístupový PIN kód:", type="password", key="pin_input_main")
    if entered_pin:
        if entered_pin == app_pin:
            st.session_state.authenticated = True
            pin_placeholder.empty(); st.rerun() 
        else: st.error("Nesprávny PIN kód."); st.stop() 
    else:
         if not entered_pin: st.info("Pre prístup k aplikácii zadajte PIN kód.")
         st.stop() 
if st.session_state.authenticated:
    dataforseo_api_login = st.secrets.get("dataforseo", {}).get("login")
    dataforseo_api_password = st.secrets.get("dataforseo", {}).get("password")
    st.sidebar.header("⚙️ Nastavenia DataForSEO API")
    st.sidebar.info("API prihlasovacie údaje sa načítavajú zo Streamlit Secrets.")
    login_status_placeholder = st.sidebar.empty()
    location_options, locations_error, language_options, languages_error = [], None, [], None
    if dataforseo_api_login and dataforseo_api_password:
        location_options, locations_error = load_locations(dataforseo_api_login, dataforseo_api_password)
        language_options, languages_error = load_languages(dataforseo_api_login, dataforseo_api_password)
        if not locations_error and not languages_error: login_status_placeholder.success("✅ API Prihlásenie OK (Krajiny a Jazyky načítané)")
        else:
            is_auth_error = ("401" in str(locations_error)) or ("401" in str(languages_error))
            if is_auth_error: login_status_placeholder.error("❌ Chyba API Prihlásenia! Skontrolujte credentials v Secrets.")
            else: login_status_placeholder.warning("⚠️ Problém s API. Skontrolujte chyby nižšie.")
            if locations_error: st.sidebar.error(f"Krajiny: {locations_error}")
            if languages_error: st.sidebar.error(f"Jazyky: {languages_error}")
    else:
        login_status_placeholder.error("❌ API prihlasovacie údaje nenájdené v Streamlit Secrets!")
        locations_error, languages_error = "Chýbajú API prihlasovacie údaje.", "Chýbajú API prihlasovacie údaje."
    st.sidebar.markdown("---")
    st.sidebar.header("🚀 Režim Dashboardu")
    options_tuple_analysis_mode = ("Analýza jednej krajiny", "Analýza viacerých krajín")
    if 'analysis_mode_radio' not in st.session_state or st.session_state.analysis_mode_radio not in options_tuple_analysis_mode:
        st.session_state.analysis_mode_radio = options_tuple_analysis_mode[0] 
    analysis_mode = st.sidebar.radio("Vyberte typ analýzy:", options_tuple_analysis_mode, key="analysis_mode_radio", index=options_tuple_analysis_mode.index(st.session_state.analysis_mode_radio))
    
    st.sidebar.markdown("---"); st.sidebar.header("ℹ️ Dokumentácia");
    st.sidebar.markdown("[DataForSEO Dokumentácia v3](https://docs.dataforseo.com/v3/)")
    st.sidebar.markdown("[Dokumentácia k Lokáciám](https://docs.dataforseo.com/v3/keywords_data/google_ads/locations/)")
    st.sidebar.markdown("[Dokumentácia k Jazykom](https://docs.dataforseo.com/v3/keywords_data/google_ads/languages/)")
    st.sidebar.markdown("[Dokumentácia k Search Volume](https://docs.dataforseo.com/v3/keywords_data/google_ads/search_volume/live/)")
    
    st.sidebar.markdown("---"); st.sidebar.header("©️ Copyright");
    st.sidebar.markdown("[2025, Marek Šulik](https://mareksulik.sk)")
    st.sidebar.markdown("Všetky práva vyhradené.")
    st.sidebar.markdown("Vytvorené s pomocou Google Gemini a Streamlit.") # Upravené
    st.sidebar.markdown("Všetky dáta sú spracované a vizualizované pomocou Pythonu a knižnice Plotly.")
    st.sidebar.markdown("v1.5 - 2025-05-13")


    if analysis_mode == "Analýza jednej krajiny":
        st.header("🔍 Analýza jednej krajiny")
        col1, col2, col3 = st.columns(3)
        with col1:
            st.subheader("Kľúčové slová")
            if 'keywords_input_single' not in st.session_state: st.session_state.keywords_input_single = DEFAULT_KEYWORDS
            st.text_area("Zadajte kľúčové slová:", key="keywords_input_single", height=150)
        with col2:
            st.subheader("Krajina") 
            selected_location_code, selected_location_display_name = None, ""
            loc_selectbox_disabled = not location_options or not dataforseo_api_login or not dataforseo_api_password
            if not loc_selectbox_disabled:
                loc_display_list_s = [opt[0] for opt in location_options]; loc_code_map_s = {opt[0]: opt[1] for opt in location_options}
                if 'location_select_single' not in st.session_state or st.session_state.location_select_single not in loc_display_list_s:
                    st.session_state.location_select_single = next((name for name, code_val in location_options if code_val == 2703), loc_display_list_s[0] if loc_display_list_s else "")
                st.selectbox("Vyber krajinu:", options=loc_display_list_s, key="location_select_single", help="Zoznam načítaný z API.") 
                selected_location_display_name = st.session_state.location_select_single
                selected_location_code = loc_code_map_s.get(selected_location_display_name)
            else:
                st.info("Zoznam krajín nie je dostupný.")
                if locations_error and (dataforseo_api_login and dataforseo_api_password): st.warning(f"Chyba pri načítaní krajín: {locations_error}")
            st.subheader("Jazyk")
            selected_language_code, selected_language_display_name = None, ""
            lang_selectbox_disabled = not language_options or not dataforseo_api_login or not dataforseo_api_password
            if not lang_selectbox_disabled:
                lang_display_list_s = [opt[0] for opt in language_options]; lang_code_map_s = {opt[0]: opt[1] for opt in language_options}
                if 'language_select_single' not in st.session_state or st.session_state.language_select_single not in lang_display_list_s:
                    st.session_state.language_select_single = next((name for name, code_val in language_options if code_val.lower() == 'sk'), lang_display_list_s[0] if lang_display_list_s else "")
                st.selectbox("Vyberte jazyk:", options=lang_display_list_s, key="language_select_single", help="Zoznam načítaný z API.")
                selected_language_display_name = st.session_state.language_select_single
                selected_language_code = lang_code_map_s.get(selected_language_display_name)
            else:
                st.info("Zoznam jazykov nie je dostupný.")
                if languages_error and (dataforseo_api_login and dataforseo_api_password): st.warning(f"Chyba pri načítaní jazykov: {languages_error}")
        with col3:
            st.subheader("Rozsah dátumov") 
            today_s = date.today(); default_end_date_s = today_s.replace(day=1) - timedelta(days=1)
            default_start_date_s = default_end_date_s.replace(year=default_end_date_s.year - 3) + timedelta(days=1)
            if 'date_from_single' not in st.session_state: st.session_state.date_from_single = default_start_date_s
            if 'date_to_single' not in st.session_state: st.session_state.date_to_single = default_end_date_s
            st.date_input("Dátum od:", value=st.session_state.date_from_single, min_value=date(2015, 1, 1), max_value=st.session_state.date_to_single, key="date_from_single")
            st.date_input("Dátum do:", value=st.session_state.date_to_single, min_value=st.session_state.date_from_single, max_value=default_end_date_s, key="date_to_single")
            st.subheader("Granularita Zobrazenia")
            single_granularity_options = ['Ročne', 'Štvrťročne', 'Mesačne']
            if 'granularity_choice_single' not in st.session_state: st.session_state.granularity_choice_single = 'Ročne'
            st.radio("Agregovať dáta:", options=single_granularity_options, key="granularity_choice_single", horizontal=True)
            granularity_single = st.session_state.granularity_choice_single

        keywords_list_single = [kw.strip() for kw in st.session_state.keywords_input_single.splitlines() if kw.strip()]
        date_from_input_single = st.session_state.date_from_single
        date_to_input_single = st.session_state.date_to_single
        st.info("Poznámka: API vracia dáta len za obdobie, pre ktoré sú dostupné v Google Ads zdroji (typicky max. posledných ~4-5 rokov), aj keď zvolíte starší 'Dátum od'.")
        run_button_disabled_single = not selected_location_code or not selected_language_code or not dataforseo_api_login or not dataforseo_api_password or not keywords_list_single
        session_key_single = f"data_single_{tuple(sorted(keywords_list_single))}_{selected_location_code}_{selected_language_code}_{date_from_input_single}_{date_to_input_single}_{granularity_single}"
        cache_info_placeholder_single = st.empty()
        if session_key_single in st.session_state and st.session_state[session_key_single].get("data") is not None:
             cache_info_placeholder_single.success("✅ Dáta pre tieto parametre (analýza jednej krajiny) sú v cache session.")
        if st.button("📊 Získať dáta a zobraziť grafy", type="primary", disabled=run_button_disabled_single, key="run_button_single"):
            if not keywords_list_single: st.warning("⚠️ Zadajte kľúčové slová.")
            elif date_from_input_single > date_to_input_single: st.error("🚨 Dátum 'od' nemôže byť neskorší ako 'do'.")
            else:
                keywords_tuple_s = tuple(sorted(keywords_list_single)); loaded_from_session_s = False
                if session_key_single in st.session_state:
                    results_data_list_s = st.session_state[session_key_single].get("data"); error_msg_s = st.session_state[session_key_single].get("error")
                    if results_data_list_s is not None or error_msg_s is not None:
                         cache_info_placeholder_single.success("✅ Používam dáta z cache session (analýza jednej krajiny)."); loaded_from_session_s = True
                if not loaded_from_session_s:
                    cache_info_placeholder_single.info("ℹ️ Cache session (analýza jednej krajiny) nenájdená, volám API...")
                    with st.spinner("⏳ Získavam dáta z DataForSEO API..."):
                         results_data_list_s, error_msg_s = get_search_volume_live_with_history(dataforseo_api_login, dataforseo_api_password, keywords_tuple_s, selected_location_code, selected_language_code, date_from_input_single, date_to_input_single)
                         st.session_state[session_key_single] = {"data": results_data_list_s, "error": error_msg_s, "granularity": granularity_single}
                    cache_info_placeholder_single.empty() 
                current_data_s = st.session_state[session_key_single].get("data"); current_error_s = st.session_state[session_key_single].get("error")
                if not loaded_from_session_s and not current_error_s and current_data_s is not None and current_data_s:
                    st.success("✅ Dáta (analýza jednej krajiny) úspešne získané z API!")
        
        if session_key_single in st.session_state:
            current_data_s = st.session_state[session_key_single].get("data"); current_error_s = st.session_state[session_key_single].get("error")
            granularity_s_for_display = st.session_state.granularity_choice_single 

            if current_error_s: st.error(f"🚨 Nastala chyba pri získavaní dát (analýza jednej krajiny):\n{current_error_s}")
            elif current_data_s is not None: 
                if not current_data_s: st.info("ℹ️ Neboli nájdené žiadne historické dáta pre zadané kľúčové slová, krajinu a jazyk v danom časovom období.")
                else:
                    history_df_raw_s = pd.DataFrame(current_data_s); history_df_raw_s['Date'] = pd.to_datetime(history_df_raw_s['Date'])
                    aggregation_successful_s = False 
                    try:
                        history_df_agg_s = history_df_raw_s.copy()
                        period_col_name_s = 'Period'; granularity_label_s = granularity_s_for_display.replace('e','á')
                        period_sort_key_s = None;
                        if granularity_s_for_display == 'Ročne': history_df_agg_s[period_col_name_s] = history_df_agg_s['Date'].dt.year.astype(str); period_sort_key_s = lambda x: pd.to_numeric(x)
                        elif granularity_s_for_display == 'Štvrťročne': history_df_agg_s[period_col_name_s] = history_df_agg_s['Date'].dt.to_period('Q').astype(str); period_sort_key_s = lambda x: pd.Period(x, freq='Q')
                        else: history_df_agg_s[period_col_name_s] = history_df_agg_s['Date'].dt.strftime('%Y-%m'); period_sort_key_s = lambda x: pd.to_datetime(x, format='%Y-%m')
                        
                        period_volume_sum_df_s = history_df_agg_s.groupby([period_col_name_s, 'Keyword'], observed=False)['Search Volume'].sum().reset_index()
                        total_period_volume_sum_df_s = period_volume_sum_df_s.groupby(period_col_name_s, observed=False)['Search Volume'].sum().reset_index().rename(columns={'Search Volume': 'Total Volume'})
                        period_volume_avg_df_s = history_df_agg_s.groupby([period_col_name_s, 'Keyword'], observed=False)['Search Volume'].mean().reset_index().rename(columns={'Search Volume': 'Average Search Volume'})
                        
                        months_in_period_s = history_df_agg_s.groupby(period_col_name_s, observed=False)['Date'].nunique().rename('Num Months')
                        total_period_volume_avg_df_s = pd.merge(total_period_volume_sum_df_s, months_in_period_s, on=period_col_name_s)
                        if not total_period_volume_avg_df_s.empty : 
                            total_period_volume_avg_df_s['Average Total Volume'] = total_period_volume_avg_df_s.apply(lambda row: row['Total Volume'] / row['Num Months'] if row['Num Months'] > 0 else 0, axis=1)
                            total_period_volume_avg_df_s = total_period_volume_avg_df_s[[period_col_name_s, 'Average Total Volume']]
                        else: 
                            total_period_volume_avg_df_s = pd.DataFrame(columns=[period_col_name_s, 'Average Total Volume'])
                        
                        merged_period_df_s = pd.merge(period_volume_sum_df_s, total_period_volume_sum_df_s, on=period_col_name_s) 
                        merged_period_df_s['Share_Percent'] = 0.0; mask_s = merged_period_df_s['Total Volume'] > 0
                        merged_period_df_s.loc[mask_s, 'Share_Percent'] = (merged_period_df_s['Search Volume'] / merged_period_df_s['Total Volume']) * 100
                        merged_period_df_s.fillna({'Share_Percent': 0, 'Search Volume': 0}, inplace=True)
                        aggregation_successful_s = True
                    except Exception as e:
                        st.error(f"Chyba pri agregácii dát podľa granularity '{granularity_s_for_display}': {e}"); st.exception(e)
                        # V prípade chyby resetujeme dátové rámce, aby sa nezobrazovali staré dáta
                        merged_period_df_s, period_volume_avg_df_s, total_period_volume_avg_df_s, period_volume_sum_df_s = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
                    
                    if aggregation_successful_s:
                        keyword_order_list_s = None
                        if not period_volume_sum_df_s.empty:
                             total_volume_overall_s = period_volume_sum_df_s.groupby('Keyword')['Search Volume'].sum().sort_values(ascending=False).index
                             keyword_order_list_s = list(total_volume_overall_s)
                        merged_df_plot_s = merged_period_df_s[merged_period_df_s['Total Volume'] > 0].copy()
                        
                        st.markdown("---"); st.subheader(f"1. {granularity_label_s} podiel | Krajina: {selected_location_display_name}, Jazyk: {selected_language_display_name}")
                        try:
                            if not merged_df_plot_s.empty:
                                unique_periods_s = sorted(merged_df_plot_s[period_col_name_s].unique(), key=period_sort_key_s)
                                fig_bar_share_s = px.bar(merged_df_plot_s, x=period_col_name_s, y='Share_Percent', color='Keyword', text='Share_Percent', barmode='stack', labels={'Share_Percent': '% Podiel', 'Keyword': 'Značka', period_col_name_s: granularity_label_s}, title=f"1. Share of Search (Podiel %) | {selected_location_display_name}", category_orders={"Keyword": keyword_order_list_s, period_col_name_s: unique_periods_s})
                                fig_bar_share_s.update_layout(yaxis_title='% celkového objemu vyhľadávania', yaxis_ticksuffix="%", xaxis_type='category', legend_title_text='Značky', height=800)
                                fig_bar_share_s.update_traces(texttemplate='%{text:.1f}%', textposition='inside', insidetextanchor='middle', textfont_size=12)
                                st.plotly_chart(fig_bar_share_s, use_container_width=True)
                                try:
                                    img_bytes_bar_s = fig_bar_share_s.to_image(format="png", scale=3)
                                    st.download_button(label="📥 Stiahnuť Graf Podielu (PNG)", data=img_bytes_bar_s, file_name=f"sos_share_{selected_location_code}_{selected_language_code}_{granularity_s_for_display}.png", mime="image/png", key=f"download_share_{granularity_s_for_display}_single")
                                except Exception as img_e: st.warning(f"Chyba pri exporte PNG grafu Podielu: {img_e}. Skontrolujte 'kaleido' inštaláciu.")
                            elif not current_error_s: st.warning(f"Nenašli sa žiadne dáta na zobrazenie grafu '1. {granularity_s_for_display.lower()} podiel' (celkový objem bol 0).")
                        except Exception as e: st.error(f"Chyba pri generovaní grafu '1. {granularity_s_for_display.lower()} podiel': {e}"); st.exception(e)
                        
                        if not period_volume_sum_df_s.empty: # Kontrola pre ďalšie grafy
                            st.markdown("---"); st.subheader(f"2. Priemerný mesačný objem segmentu")
                            try:
                                if not total_period_volume_avg_df_s.empty and total_period_volume_avg_df_s['Average Total Volume'].sum() > 0:
                                    unique_periods_avg_total_s = sorted(total_period_volume_avg_df_s[period_col_name_s].unique(), key=period_sort_key_s)
                                    fig_avg_total_volume_s = px.bar(total_period_volume_avg_df_s, x=period_col_name_s, y='Average Total Volume', labels={'Average Total Volume': 'Priem. mesačný objem', period_col_name_s: granularity_label_s}, title=f"2. Priemerný mesačný objem segmentu", category_orders={period_col_name_s: unique_periods_avg_total_s})
                                    fig_avg_total_volume_s.update_layout(yaxis_title='Priemerný mesačný objem (AVG)', xaxis_type='category', height=550)
                                    fig_avg_total_volume_s.update_traces(texttemplate='%{y:,.0f}', textposition='outside')
                                    st.plotly_chart(fig_avg_total_volume_s, use_container_width=True)
                                    try:
                                        img_bytes_avg_total_s = fig_avg_total_volume_s.to_image(format="png", scale=3)
                                        st.download_button(label="📥 Stiahnuť Graf Priem. Obj. Segmentu", data=img_bytes_avg_total_s, file_name=f"sos_avg_segment_{selected_location_code}_{selected_language_code}_{granularity_s_for_display}.png", mime="image/png", key=f"download_avg_segment_{granularity_s_for_display}_single")
                                    except Exception as img_e: st.warning(f"Chyba PNG (Priem. Seg.): {img_e}.")
                                else: st.warning("N/A dáta pre graf '2. Priemerný mesačný objem segmentu'.")
                            except Exception as e: st.error(f"Chyba pri generovaní grafu '2. Priemerný mesačný objem segmentu': {e}")

                            st.markdown("---"); st.subheader(f"3. Priemerný mesačný objem konkurentov")
                            try:
                                 if not period_volume_avg_df_s.empty:
                                      unique_periods_avg_comp_s = sorted(period_volume_avg_df_s[period_col_name_s].unique(), key=period_sort_key_s)
                                      fig_line_avg_volume_s = px.line( period_volume_avg_df_s, x=period_col_name_s, y='Average Search Volume', color='Keyword', labels={'Average Search Volume': f'Priem. mesačný objem', 'Keyword': 'Značka', period_col_name_s: granularity_label_s}, title=f"3. {granularity_label_s} vývoj priemerného mesačného objemu", category_orders={"Keyword": keyword_order_list_s, period_col_name_s: unique_periods_avg_comp_s}, markers=True )
                                      fig_line_avg_volume_s.update_layout(yaxis_title=f'Priem. mesačný objem (AVG)', legend_title_text='Značky (kliknite pre filter)', height=700)
                                      fig_line_avg_volume_s.update_traces(mode="markers+lines", hovertemplate="<b>%{fullData.name}</b><br>Perióda: %{x}<br>Priem. objem: %{y:,.0f}<extra></extra>")
                                      st.plotly_chart(fig_line_avg_volume_s, use_container_width=True)
                                      try:
                                          img_bytes_avg_comp_s = fig_line_avg_volume_s.to_image(format="png", scale=3)
                                          st.download_button(label="📥 Stiahnuť Graf Priem. Obj. Konkurentov", data=img_bytes_avg_comp_s, file_name=f"sos_avg_competitor_{selected_location_code}_{selected_language_code}_{granularity_s_for_display}.png", mime="image/png", key=f"download_avg_comp_{granularity_s_for_display}_single")
                                      except Exception as img_e: st.warning(f"Chyba PNG (Priem. Konk.): {img_e}.")
                                 else: st.warning("N/A dáta pre graf '3. Priemerný mesačný objem konkurentov'.")
                            except Exception as e: st.error(f"Chyba pri generovaní grafu '3. Priemerný mesačný objem konkurentov': {e}")
                            
                            st.markdown("---"); st.subheader(f"4. Tempo rastu ({granularity_label_s})")
                            try:
                                unique_period_values_s = period_volume_sum_df_s[period_col_name_s].unique()
                                if len(unique_period_values_s) > 1:
                                    period_growth_df_s = period_volume_sum_df_s.copy()
                                    try: period_growth_df_s['SortKey'] = period_growth_df_s[period_col_name_s].apply(period_sort_key_s)
                                    except Exception: period_growth_df_s['SortKey'] = period_growth_df_s[period_col_name_s]
                                    period_growth_df_s = period_growth_df_s.sort_values(by=['SortKey', 'Keyword']).drop(columns=['SortKey'])
                                    period_growth_df_s['Prev Volume'] = period_growth_df_s.groupby('Keyword')['Search Volume'].shift(1); period_growth_df_s['Period Growth (%)'] = np.nan 
                                    mask_growth_s = (period_growth_df_s['Prev Volume'] > 0) & (pd.notna(period_growth_df_s['Prev Volume']))
                                    period_growth_df_s.loc[mask_growth_s, 'Period Growth (%)'] = ((period_growth_df_s['Search Volume'] - period_growth_df_s['Prev Volume']) / period_growth_df_s['Prev Volume']) * 100
                                    mask_inf_s = (period_growth_df_s['Prev Volume'] == 0) & (period_growth_df_s['Search Volume'] > 0) & (pd.notna(period_growth_df_s['Prev Volume']))
                                    period_growth_df_s.loc[mask_inf_s, 'Period Growth (%)'] = np.inf
                                    heatmap_data_s = period_growth_df_s.pivot(index='Keyword', columns=period_col_name_s, values='Period Growth (%)')
                                    if keyword_order_list_s: heatmap_data_s = heatmap_data_s.reindex(index=keyword_order_list_s)
                                    heatmap_data_s = heatmap_data_s.dropna(how='all', axis=0)
                                    try: sorted_periods_s = sorted(heatmap_data_s.columns, key=period_sort_key_s)
                                    except Exception: sorted_periods_s = sorted(heatmap_data_s.columns)
                                    heatmap_data_s = heatmap_data_s[sorted_periods_s]
                                    if not heatmap_data_s.empty:
                                        def format_growth_s(val):
                                            if pd.isna(val): return '-'
                                            if val == np.inf: return 'Inf%'
                                            elif val == -np.inf: return '-Inf%'
                                            return f"{val:.0f}%"
                                        text_labels_s = heatmap_data_s.applymap(format_growth_s).values; color_min_s = -100; color_max_s = 200; color_mid_s = 0
                                        fig_heatmap_s = px.imshow( heatmap_data_s, labels=dict(x=granularity_label_s, y="Značka", color="Rast (%)"), title=f"4. Medziobdobový rast (%) - {granularity_s_for_display.lower()}", text_auto=False, aspect="auto", color_continuous_scale='RdYlGn', color_continuous_midpoint=color_mid_s, range_color=[color_min_s, color_max_s] )
                                        fig_heatmap_s.update_traces( text=text_labels_s, texttemplate="%{text}", hovertemplate="<b>%{y}</b><br>%{x}<br>Rast: %{z:.0f}%<extra></extra>" ); fig_heatmap_s.update_xaxes(side="bottom")
                                        fig_heatmap_s.update_layout(height=max(450, len(heatmap_data_s.index)*40)); st.plotly_chart(fig_heatmap_s, use_container_width=True)
                                        try:
                                            img_bytes_heatmap_s = fig_heatmap_s.to_image(format="png", scale=3)
                                            st.download_button(label="📥 Stiahnuť Heatmapu Rastu", data=img_bytes_heatmap_s, file_name=f"sos_growth_heatmap_{selected_location_code}_{selected_language_code}_{granularity_s_for_display}.png", mime="image/png", key=f"download_heatmap_{granularity_s_for_display}_single")
                                        except Exception as img_e: st.warning(f"Chyba PNG (Heatmap): {img_e}.")
                                    else: st.info("Nebolo možné vypočítať alebo zobraziť medziobdobový rast (žiadne dáta po filtrovaní).")
                                else: st.info("Pre výpočet medziobdobového rastu sú potrebné aspoň dve časové periódy.")
                            except Exception as e: st.error(f"Chyba pri generovaní heatmapy rastu: {e}"); st.exception(e)
                        else: st.warning(f"Neboli nájdené žiadne agregované dáta pre granularitu '{granularity_label_s}' na zobrazenie detailných analýz.")
                        
                        st.markdown("---"); st.subheader("5. História vyhľadávaní")
                        if 'search_history_single' not in st.session_state: st.session_state.search_history_single = []
                        current_request_info_single = {
                            'keywords': keywords_list_single, 'location': selected_location_display_name, 'location_code': selected_location_code,
                            'language': selected_language_display_name, 'language_code': selected_language_code,
                            'date_from': date_from_input_single, 'date_to': date_to_input_single, 'granularity': granularity_s_for_display,
                            'session_key': session_key_single, 'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                        }
                        request_exists_single = any(hist_item['session_key'] == session_key_single for hist_item in st.session_state.search_history_single)
                        if not request_exists_single and current_data_s is not None and current_data_s: 
                            st.session_state.search_history_single.append(current_request_info_single)
                        if st.session_state.search_history_single:
                            with st.expander("📋 Zoznam predchádzajúcich vyhľadávaní (Analýza jednej krajiny)", expanded=False):
                                for i, hist_item in enumerate(reversed(st.session_state.search_history_single)): 
                                    col_h1, col_h2, col_h3 = st.columns([3, 2, 1])
                                    with col_h1:
                                        kw_summary = ", ".join(hist_item['keywords'][:3]) + (f" a ďalšie {len(hist_item['keywords'])-3}" if len(hist_item['keywords']) > 3 else "")
                                        st.markdown(f"**Kľúčové slová:** {kw_summary}")
                                    with col_h2:
                                        st.markdown(f"**Krajina:** {hist_item['location']}")
                                        st.markdown(f"**Jazyk:** {hist_item['language']}")
                                        st.markdown(f"**Obdobie:** {hist_item['date_from'].strftime('%Y-%m-%d')} až {hist_item['date_to'].strftime('%Y-%m-%d')}")
                                    with col_h3:
                                        if st.button(f"Načítať", key=f"load_hist_single_{hist_item['session_key']}"):
                                            st.session_state.keywords_input_single = "\n".join(hist_item['keywords'])
                                            st.session_state.location_select_single = hist_item['location'] 
                                            st.session_state.language_select_single = hist_item['language'] 
                                            st.session_state.date_from_single = hist_item['date_from']
                                            st.session_state.date_to_single = hist_item['date_to']
                                            st.session_state.granularity_choice_single = hist_item['granularity']
                                            st.rerun()
                                    st.markdown(f"*Čas vyhľadávania: {hist_item['timestamp']}*")
                                    if i < len(st.session_state.search_history_single) - 1: st.markdown("---")
                            if st.button("🗑️ Vymazať históriu (Analýza jednej krajiny)", key="clear_hist_single_button"):
                                st.session_state.search_history_single = []
                                st.success("História vyhľadávaní (Analýza jednej krajiny) bola vymazaná."); st.rerun()
                        else: st.info("Zatiaľ nemáte žiadne vyhľadávania v histórii (Analýza jednej krajiny).")

                        st.markdown("---"); st.subheader("6. Stiahnuť dáta ako CSV")
                        try:
                             if not history_df_raw_s.empty: 
                                  @st.cache_data 
                                  def convert_df_to_csv_single_v3(df_to_convert): 
                                      df_sorted = df_to_convert[['Keyword', 'Date', 'Search Volume']].sort_values(by=['Keyword','Date'])
                                      df_sorted['Date'] = pd.to_datetime(df_sorted['Date']).dt.strftime('%Y-%m-%d')
                                      return df_sorted.to_csv(index=False).encode('utf-8')
                                  csv_data_single_v3 = convert_df_to_csv_single_v3(history_df_raw_s.copy())
                                  st.download_button(label="Stiahnuť pôvodné mesačné dáta ako CSV", data=csv_data_single_v3, file_name=f'sos_monthly_data_single_country.csv', mime='text/csv', key="download_csv_single_button_v3")
                             elif not current_error_s: st.warning("Žiadne dáta na stiahnutie.")
                        except Exception as e: st.error(f"Chyba pri príprave CSV na stiahnutie: {e}")

        elif run_button_disabled_single and (dataforseo_api_login and dataforseo_api_password): 
            missing_parts_single = []
            if not keywords_list_single: missing_parts_single.append("kľúčové slová")
            if not selected_location_code : missing_parts_single.append("krajinu")
            if not selected_language_code : missing_parts_single.append("jazyk")
            if missing_parts_single: st.warning(f"⚠️ Vyberte prosím {', '.join(missing_parts_single)} pre pokračovanie v analýze jednej krajiny.")
    elif analysis_mode == "Analýza viacerých krajín":
        render_multi_country_page(dataforseo_api_login, dataforseo_api_password, location_options, language_options, locations_error, languages_error)