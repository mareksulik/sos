import streamlit as st
import requests
import json
import base64
import os
import pandas as pd
import time 
from datetime import date, timedelta
import plotly.express as px 
import numpy as np 

# --- Konstanty API Endpointov ---
SEARCH_VOLUME_LIVE_URL = "https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live"
LOCATIONS_URL = "https://api.dataforseo.com/v3/keywords_data/google_ads/locations"
LANGUAGES_URL = "https://api.dataforseo.com/v3/keywords_data/google_ads/languages"

# --- Helper funkcie pre získanie lokácií a jazykov (s cache) ---
@st.cache_data 
def load_locations(login, password):
    if not login or not password: return [], "Chýbajú API prihlasovacie údaje:"     
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
        else: status_code = data.get('tasks', [{}])[0].get('status_code', 'N/A'); status_message = data.get('tasks', [{}])[0].get('status_message', 'N/A'); error_msg = f"API (lokácie): Kód {status_code} - {status_message}"
    except requests.exceptions.RequestException as e: error_msg = f"Chyba pri komunikácii s API (lokácie): {e}"
    except Exception as e: error_msg = f"Neočekávaná chyba pri načítaní lokácií: {e}"    
    return location_options, error_msg

@st.cache_data
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
        else: status_code = data.get('tasks', [{}])[0].get('status_code', 'N/A'); status_message = data.get('tasks', [{}])[0].get('status_message', 'N/A'); error_msg = f"API (jazyky): Kód {status_code} - {status_message}"            
    except requests.exceptions.RequestException as e: error_msg = f"API (jazyky): Chyba komunikácie - {e}"
    except Exception as e: error_msg = f"Neočekávaná chyba pri načítaní jazykov: {e}"    
    return language_options, error_msg

# --- Cachovaná Funkcia pre API volanie search volume ---
@st.cache_data 
def get_search_volume_live_with_history(login, password, kw_list_tuple, loc_code, lang_code, date_from, date_to):
    # ... (vnútorná logika funkcie zostáva rovnaká) ...
    kw_list = list(kw_list_tuple); results_list = []; error_msg = None      
    if not all([login, password, kw_list, loc_code, lang_code, date_from, date_to]): return None, "Chyba: Chýbajú vstupné parametre pre API volanie."
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
                 error_msg = "Varovanie: API nevrátilo žiadne platné mesačné historické dáta ('monthly_searches') v zadanom rozsahu dátumov."
        elif response_data.get("tasks"): error_msg = f"Chyba API: Kód `{response_data['tasks'][0].get('status_code', 'N/A')}` - {response_data['tasks'][0].get('status_message', 'N/A')}"
        else: error_msg = "Chyba: API vrátilo neočakávanú štruktúru odpovede."; st.warning(f"Detail odpovede: {str(response_data)[:500]}") 
    except requests.exceptions.Timeout: error_msg = "Chyba: Vypršal časový limit pri čakaní na odpoveď z API."
    except requests.exceptions.RequestException as e: error_msg = f"Chyba pri komunikácii s API: {e}";
    except json.JSONDecodeError: error_msg = f"Chyba: Nepodarilo sa dekódovať JSON odpoveď.\n   Obsah (prvých 500 znakov): {response.text[:500]}" 
    except Exception as e: error_msg = f"Nastala neočakávaná chyba v spracovaní API volania: {e}"
    if error_msg: return None, error_msg
    else:
        if not results_list: return None, "Varovanie: Nenašli sa žiadne dáta pre zadané kritériá." 
        return results_list, None

# --- Streamlit Aplikácia ---

# Odstránený layout="wide", použije sa default "centered"
st.set_page_config(page_title="Marš! Share of Search") 

# Odstránený CSS blok pre šírku
# st.markdown( f""" <style> ... </style> """, unsafe_allow_html=True, )

st.title("📊📈 Marš! Share of Search Tool") 

# --- Sidebar ---
st.sidebar.header("⚙️ Nastavenia DataForSEO API")
st.sidebar.warning("⚠️ Údaje zadané nižšie sa uložia len v aktuálnej session prehliadača.")
if 'dataforseo_login' not in st.session_state: st.session_state.dataforseo_login = os.environ.get('DATAFORSEO_LOGIN', '')
if 'dataforseo_password' not in st.session_state: st.session_state.dataforseo_password = os.environ.get('DATAFORSEO_PASSWORD', '')
st.sidebar.text_input("API Login", key='dataforseo_login', help="Váš prihlasovací email.")
st.sidebar.text_input("API Password", type="password", key='dataforseo_password', help="Vaše API heslo.")

# --- Indikátor prihlásenia ---
login_status_placeholder = st.sidebar.empty() 
location_options, locations_error = load_locations(st.session_state.dataforseo_login, st.session_state.dataforseo_password)
language_options, languages_error = load_languages(st.session_state.dataforseo_login, st.session_state.dataforseo_password)
if st.session_state.dataforseo_login and st.session_state.dataforseo_password:
    is_auth_error = (locations_error and ("401" in locations_error or "authorized" in locations_error.lower())) or \
                    (languages_error and ("401" in languages_error or "authorized" in languages_error.lower()))
    if not locations_error and not languages_error: login_status_placeholder.success("✅ API Prihlásenie OK")
    elif is_auth_error: login_status_placeholder.error("❌ Chyba API Prihlásenia!")
    else:
        login_status_placeholder.warning("⚠️ Nepodarilo sa overiť API kľúče.")
        if locations_error: st.sidebar.error(f"Lokácie: {locations_error}")
        if languages_error: st.sidebar.error(f"Jazyky: {languages_error}")
else: login_status_placeholder.info("Zadajte API Login a Password.")

st.sidebar.markdown("---"); st.sidebar.header("ℹ️ Endpoint a Dokumentácia"); 
st.sidebar.markdown(f"Používa sa:"); st.sidebar.code(SEARCH_VOLUME_LIVE_URL, language=None)
st.sidebar.markdown("[DataForSEO Dokumentácia v3:](https://docs.dataforseo.com/v3/)")
st.sidebar.markdown("[Dokumentácia k Lokáciám](https://docs.dataforseo.com/v3/keywords_data/google_ads/locations/)")
st.sidebar.markdown("[Dokumentácia k Jazykom](https://docs.dataforseo.com/v3/keywords_data/google_ads/languages/)")
st.sidebar.markdown("[Dokumentácia k Search Volume](https://docs.dataforseo.com/v3/keywords_data/google_ads/search_volume/live/)")

# --- Hlavná časť ---
st.header("🔍 Zadať parametre vyhľadávania")

col1, col2, col3 = st.columns(3) 
with col1:
    st.subheader("Kľúčové slová")
    if 'keywords_input' not in st.session_state: st.session_state.keywords_input = "isadore\ncastelli\nrapha\nmaap\npas normal studios"
    keywords_input = st.text_area("Zadajte kľúčové slová:", value=st.session_state.keywords_input, height=150, key="keywords_input_area") 

with col2:
    st.subheader("Lokácia")
    selected_location_code = None; selected_location_display = ""
    loc_selectbox_disabled = not location_options or not st.session_state.dataforseo_login or not st.session_state.dataforseo_password
    if not loc_selectbox_disabled:
        loc_display_list = [opt[0] for opt in location_options]; loc_code_map = {opt[0]: opt[1] for opt in location_options} 
        default_loc_name_display = next((name for name, code in location_options if code == 2703), loc_display_list[0] if loc_display_list else "")
        try: default_loc_index = loc_display_list.index(default_loc_name_display)
        except ValueError: default_loc_index = 0
        selected_location_display = st.selectbox("Vyberte lokáciu:", options=loc_display_list, index=default_loc_index, key="location_select", help="Zoznam načítaný z API.")
        selected_location_code = loc_code_map.get(selected_location_display) 
    else:
        st.info("Zadajte API kľúče pre načítanie lokácií.")
        location_code_input = st.text_input("ALEBO Zadajte kód manuálne:", value="2703", key="location_manual", disabled=loc_selectbox_disabled) 
        try: selected_location_code = int(location_code_input) if location_code_input else None; selected_location_display = f"Kód: {selected_location_code}" if selected_location_code else ""
        except ValueError: st.error("Kód lokácie musí byť číslo!"); selected_location_code = None

    st.subheader("Jazyk")
    selected_language_code = None; selected_language_display = ""
    lang_selectbox_disabled = not language_options or not st.session_state.dataforseo_login or not st.session_state.dataforseo_password
    if not lang_selectbox_disabled:
        lang_display_list = [opt[0] for opt in language_options]; lang_code_map = {opt[0]: opt[1] for opt in language_options}
        default_lang_name = next((name for name, code in language_options if code.lower() == 'sk'), lang_display_list[0] if lang_display_list else "")
        try: default_lang_index = lang_display_list.index(default_lang_name)
        except ValueError: default_lang_index = 0
        selected_language_display = st.selectbox("Vyberte jazyk:", options=lang_display_list, index=default_lang_index, key="language_select", help="Zoznam načítaný z API.")
        selected_language_code = lang_code_map.get(selected_language_display)
    else:
        st.info("Zadajte API kľúče pre načítanie jazykov.")
        language_code_input = st.text_input("ALEBO Zadajte kód manuálne:", value="sk", key="language_manual", disabled=lang_selectbox_disabled) 
        selected_language_code = language_code_input.strip().lower() if language_code_input else None
        selected_language_display = f"Kód: {selected_language_code}" if selected_language_code else ""

with col3:
    st.subheader("Časové okno histórie")
    today = date.today()
    default_end_date = today.replace(day=1) - timedelta(days=1)
    default_start_date = default_end_date.replace(year=default_end_date.year - 3) + timedelta(days=1) 
    date_from_input = st.date_input("Dátum od:", value=default_start_date, min_value=date(2015, 1, 1), max_value=default_end_date, key="date_from")
    date_to_input = st.date_input("Dátum do:", value=default_end_date, min_value=date_from_input, max_value=default_end_date, key="date_to")
    
    st.subheader("Granularita Zobrazenia")
    granularity = st.radio( "Agregovať dáta:", options=['Ročne', 'Štvrťročne', 'Mesačne'], index=0, horizontal=True, key="granularity_radio" )

keywords_list = [kw.strip() for kw in keywords_input.splitlines() if kw.strip()]

st.info("Poznámka: API vracia dáta len za obdobie, pre ktoré sú dostupné v Google Ads zdroji (typicky max. posledných ~4-5 rokov), aj keď zvolíte starší 'Dátum od'.")

run_button_disabled = not selected_location_code or not selected_language_code or not st.session_state.dataforseo_login or not st.session_state.dataforseo_password

# --- Cache Info Placeholder & Tlačidlo ---
session_key = f"data_{tuple(sorted(keywords_list))}_{selected_location_code}_{selected_language_code}_{date_from_input}_{date_to_input}" 
cache_info_placeholder = st.empty() 
if session_key in st.session_state and st.session_state[session_key].get("data"):
     cache_info_placeholder.success("✅ Dáta pre KW, Lokalitu, Jazyk a Dátumy sú v cache session.")

if st.button("📊 Získať dáta a zobraziť grafy", type="primary", disabled=run_button_disabled):
    if not keywords_list: st.warning("⚠️ Zadajte kľúčové slová.")
    # ... (ostatné validácie) ...
    elif date_from_input > date_to_input: st.error("🚨 Dátum 'od' nemôže byť neskorší ako 'do'.")
    else:
        keywords_tuple = tuple(sorted(keywords_list)) 
        
        loaded_from_session = False 
        if session_key in st.session_state:
             results_data_list = st.session_state[session_key].get("data")
             error_msg = st.session_state[session_key].get("error")
             if results_data_list is not None or error_msg is not None:
                  cache_info_placeholder.success("✅ Používam dáta z cache session.") 
                  loaded_from_session = True
        
        if not loaded_from_session:
             cache_info_placeholder.info("ℹ️ Cache session nenájdená, volám API...") 
             with st.spinner("⏳ Získavam dáta z DataForSEO API..."):
                 results_data_list, error_msg = get_search_volume_live_with_history(
                     st.session_state.dataforseo_login, st.session_state.dataforseo_password, 
                     keywords_tuple, selected_location_code, selected_language_code, date_from_input, date_to_input
                 )
                 st.session_state[session_key] = {"data": results_data_list, "error": error_msg}
             cache_info_placeholder.empty() 

        current_data = st.session_state[session_key].get("data")
        current_error = st.session_state[session_key].get("error")

        if not loaded_from_session and not current_error and current_data:
             st.success("✅ Dáta úspešne získané z API!")

# --- ZOBRAZENIE VÝSLEDKOV (Mimo 'if st.button') ---
if session_key in st.session_state:
    current_data = st.session_state[session_key].get("data")
    current_error = st.session_state[session_key].get("error")

    if current_error: st.error(f"🚨 Nastala chyba pri získavaní dát:\n{current_error}")
    elif current_data:
        history_df_raw = pd.DataFrame(current_data); history_df_raw['Date'] = pd.to_datetime(history_df_raw['Date']) 

        # --- Agregácia dát ---
        try:
            history_df_agg = history_df_raw.copy()
            period_col_name = 'Period'; granularity_label = granularity.replace('e','á') 
            period_sort_key = None; 
            if granularity == 'Ročne': history_df_agg[period_col_name] = history_df_agg['Date'].dt.year.astype(str); period_sort_key = lambda x: pd.to_numeric(x)
            elif granularity == 'Štvrťročne': history_df_agg[period_col_name] = history_df_agg['Date'].dt.to_period('Q').astype(str); period_sort_key = lambda x: pd.Period(x, freq='Q')
            else: history_df_agg[period_col_name] = history_df_agg['Date'].dt.strftime('%Y-%m'); period_sort_key = lambda x: pd.to_datetime(x, format='%Y-%m') 
            
            period_volume_sum_df = history_df_agg.groupby([period_col_name, 'Keyword'], observed=False)['Search Volume'].sum().reset_index()
            total_period_volume_sum_df = period_volume_sum_df.groupby(period_col_name, observed=False)['Search Volume'].sum().reset_index().rename(columns={'Search Volume': 'Total Volume'})
            period_volume_avg_df = history_df_agg.groupby([period_col_name, 'Keyword'], observed=False)['Search Volume'].mean().reset_index().rename(columns={'Search Volume': 'Average Search Volume'})
            months_in_period = history_df_agg.groupby(period_col_name, observed=False)['Date'].nunique().rename('Num Months')
            total_period_volume_avg_df = pd.merge(total_period_volume_sum_df, months_in_period, on=period_col_name) 
            total_period_volume_avg_df['Average Total Volume'] = total_period_volume_avg_df['Total Volume'] / total_period_volume_avg_df['Num Months']
            total_period_volume_avg_df = total_period_volume_avg_df[[period_col_name, 'Average Total Volume']] 
            merged_period_df = pd.merge(period_volume_sum_df, total_period_volume_sum_df, on=period_col_name)
            merged_period_df['Share_Percent'] = 0.0; mask = merged_period_df['Total Volume'] > 0
            merged_period_df.loc[mask, 'Share_Percent'] = (merged_period_df['Search Volume'] / merged_period_df['Total Volume']) * 100
            merged_period_df.fillna({'Share_Percent': 0, 'Search Volume': 0}, inplace=True) 
            merged_df_plot = merged_period_df[merged_period_df['Total Volume'] > 0].copy() 
            aggregation_successful = True 
        except Exception as e:
             st.error(f"Chyba pri agregácii dát podľa granularity '{granularity}': {e}"); st.exception(e)
             merged_df_plot, period_volume_avg_df, total_period_volume_avg_df, period_volume_sum_df = pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
             aggregation_successful = False

        # --- Zobrazenie grafov ---
        if aggregation_successful:
            total_volume_overall = None; keyword_order_list = None
            if not period_volume_sum_df.empty:
                 total_volume_overall = period_volume_sum_df.groupby('Keyword')['Search Volume'].sum().sort_values(ascending=False).index
                 keyword_order_list = list(total_volume_overall)

            # --- Hlavný Graf: Podiel (%) ---
            st.markdown("---"); st.subheader(f"📊 {granularity} podiel | Lokácia: {selected_location_display}, Jazyk: {selected_language_display}") 
            try:
                if not merged_df_plot.empty: 
                    unique_periods = sorted(merged_df_plot[period_col_name].unique(), key=period_sort_key) 
                    fig_bar_share = px.bar(merged_df_plot, x=period_col_name, y='Share_Percent', color='Keyword', text='Share_Percent', barmode='stack', labels={'Share_Percent': '% Podiel', 'Keyword': 'Značka', period_col_name: granularity_label}, title="Marš! Share of Search (Podiel %)", category_orders={"Keyword": keyword_order_list, period_col_name: unique_periods})
                    fig_bar_share.update_layout(yaxis_title='% celkového objemu vyhľadávania', yaxis_ticksuffix="%", xaxis_type='category', legend_title_text='Značky', height=800) 
                    fig_bar_share.update_traces(texttemplate='%{text:.1f}%', textposition='inside', insidetextanchor='middle', textfont_size=9) 
                    st.plotly_chart(fig_bar_share, use_container_width=True) 
                    try: img_bytes_bar = fig_bar_share.to_image(format="png", scale=3); st.download_button(label="📥 Stiahnuť Graf Podielu (PNG)", data=img_bytes_bar, file_name=f"sos_share_{selected_location_code}_{selected_language_code}_{granularity}.png", mime="image/png", key=f"download_share_{granularity}")
                    except Exception as img_e: st.warning(f"Chyba PNG (Podiel): {img_e}. Skontrolujte 'kaleido'.")
                elif not current_error: st.warning(f"Nenašli sa žiadne dáta na zobrazenie {granularity.lower()} grafu podielu.")
            except Exception as e: st.error(f"Chyba pri generovaní {granularity.lower()} grafu podielu: {e}"); st.exception(e) 

            st.markdown("---") 
            st.header(f"Detailné analýzy ({granularity})") 

            if not period_volume_sum_df.empty: 
                # --- Graf: Celkový SUMÁRNY objem segmentu ---
                st.subheader(f"📈 Celkový objem segmentu")
                try:
                    if not total_period_volume_sum_df.empty:
                         unique_periods_sum_total = sorted(total_period_volume_sum_df[period_col_name].unique(), key=period_sort_key)
                         fig_total_sum_volume = px.bar(total_period_volume_sum_df, x=period_col_name, y='Total Volume', labels={'Total Volume': 'Celkový objem', period_col_name: granularity_label}, title=f"Celkový objem segmentu ({granularity.lower()}) - Súčet")
                         fig_total_sum_volume.update_layout(yaxis_title='Celkový objem vyhľadávania (Súčet)', xaxis_type='category', height=550) 
                         fig_total_sum_volume.update_traces(texttemplate='%{y:,.0f}', textposition='outside') 
                         st.plotly_chart(fig_total_sum_volume, use_container_width=True)
                         try: img_bytes_total_sum = fig_total_sum_volume.to_image(format="png", scale=3); st.download_button(label="📥 Stiahnuť Graf Celk. Obj. (Súčet)", data=img_bytes_total_sum, file_name=f"sos_total_sum_{selected_location_code}_{selected_language_code}_{granularity}.png", mime="image/png", key=f"download_total_sum_{granularity}")
                         except Exception as img_e: st.warning(f"Chyba PNG (Celk. Súčet): {img_e}.")
                    else: st.warning("N/A dáta pre graf celk. objemu (súčet).")
                except Exception as e: st.error(f"Chyba pri generovaní grafu celk. objemu (súčet): {e}")

                # --- Graf: Celkový PRIEMERNÝ objem segmentu ---
                st.subheader(f"📉 Priemerný mesačný objem segmentu")
                try:
                    if not total_period_volume_avg_df.empty:
                         unique_periods_avg_total = sorted(total_period_volume_avg_df[period_col_name].unique(), key=period_sort_key)
                         fig_avg_total_volume = px.bar(total_period_volume_avg_df, x=period_col_name, y='Average Total Volume', labels={'Average Total Volume': 'Priem. mesačný objem', period_col_name: granularity_label}, title=f"Priemerný mesačný objem segmentu")
                         fig_avg_total_volume.update_layout(yaxis_title='Priemerný mesačný objem (AVG)', xaxis_type='category', height=550) 
                         fig_avg_total_volume.update_traces(texttemplate='%{y:,.0f}', textposition='outside')
                         st.plotly_chart(fig_avg_total_volume, use_container_width=True)
                         try: img_bytes_avg_total = fig_avg_total_volume.to_image(format="png", scale=3); st.download_button(label="📥 Stiahnuť Graf Priem. Obj. Segmentu", data=img_bytes_avg_total, file_name=f"sos_avg_segment_{selected_location_code}_{selected_language_code}_{granularity}.png", mime="image/png", key=f"download_avg_segment_{granularity}")
                         except Exception as img_e: st.warning(f"Chyba PNG (Priem. Seg.): {img_e}.")
                    else: st.warning("N/A dáta pre graf priem. objemu segmentu.")
                except Exception as e: st.error(f"Chyba pri generovaní grafu priem. objemu segmentu: {e}")

                # --- Graf: SUMÁRNY objem jednotlivých konkurentov ---
                st.subheader(f"💹 Súhrnný objem konkurentov")
                try:
                     if not period_volume_sum_df.empty:
                        unique_periods_sum_comp = sorted(period_volume_sum_df[period_col_name].unique(), key=period_sort_key)
                        fig_line_sum_volume = px.line( period_volume_sum_df, x=period_col_name, y='Search Volume', color='Keyword', labels={'Search Volume': f'{granularity} objem (súčet)', 'Keyword': 'Značka', period_col_name: granularity_label}, title=f"{granularity} vývoj objemu (súčet)", category_orders={"Keyword": keyword_order_list, period_col_name: unique_periods_sum_comp}, markers=True )
                        fig_line_sum_volume.update_layout(yaxis_title=f'{granularity} objem (Súčet)', legend_title_text='Značky', height=700) 
                        fig_line_sum_volume.update_traces(mode="markers+lines", hovertemplate="<b>%{fullData.name}</b><br>Perióda: %{x}<br>Objem (súčet): %{y:,.0f}<extra></extra>")
                        st.plotly_chart(fig_line_sum_volume, use_container_width=True) 
                        try: img_bytes_sum_comp = fig_line_sum_volume.to_image(format="png", scale=3); st.download_button(label="📥 Stiahnuť Graf Súhrn. Obj. Konkurentov", data=img_bytes_sum_comp, file_name=f"sos_sum_competitor_{selected_location_code}_{selected_language_code}_{granularity}.png", mime="image/png", key=f"download_sum_comp_{granularity}")
                        except Exception as img_e: st.warning(f"Chyba PNG (Súhrn. Konk.): {img_e}.")
                     else: st.warning("N/A dáta pre graf súhrn. objemu konkurentov.")
                except Exception as e: st.error(f"Chyba pri generovaní grafu objemu konkurentov (súčet): {e}")
                
                # --- Graf: PRIEMERNÝ objem jednotlivých konkurentov ---
                st.subheader(f"📉 Priemerný mesačný objem konkurentov")
                try:
                     if not period_volume_avg_df.empty:
                        unique_periods_avg_comp = sorted(period_volume_avg_df[period_col_name].unique(), key=period_sort_key)
                        fig_line_avg_volume = px.line( period_volume_avg_df, x=period_col_name, y='Average Search Volume', color='Keyword', labels={'Average Search Volume': f'Priem. mesačný objem', 'Keyword': 'Značka', period_col_name: granularity_label}, title=f"{granularity} vývoj priemerného mesačného objemu", category_orders={"Keyword": keyword_order_list, period_col_name: unique_periods_avg_comp}, markers=True )
                        fig_line_avg_volume.update_layout(yaxis_title=f'Priem. mesačný objem (AVG)', legend_title_text='Značky', height=700) 
                        fig_line_avg_volume.update_traces(mode="markers+lines", hovertemplate="<b>%{fullData.name}</b><br>Perióda: %{x}<br>Priem. objem: %{y:,.0f}<extra></extra>")
                        st.plotly_chart(fig_line_avg_volume, use_container_width=True) 
                        try: img_bytes_avg_comp = fig_line_avg_volume.to_image(format="png", scale=3); st.download_button(label="📥 Stiahnuť Graf Priem. Obj. Konkurentov", data=img_bytes_avg_comp, file_name=f"sos_avg_competitor_{selected_location_code}_{selected_language_code}_{granularity}.png", mime="image/png", key=f"download_avg_comp_{granularity}")
                        except Exception as img_e: st.warning(f"Chyba PNG (Priem. Konk.): {img_e}.")
                     else: st.warning("N/A dáta pre graf priem. objemu konkurentov.")
                except Exception as e: st.error(f"Chyba pri generovaní grafu priem. objemu konkurentov: {e}")

                # --- Vizualizácia Rastov ---
                st.subheader(f"🚀 Tempo rastu ({granularity})")
                # Heatmapa medziobdobového rastu
                st.markdown(f"##### Medziobdobový rast (%)") # H5 nadpis
                try:
                     if len(period_volume_sum_df[period_col_name].unique()) > 1:
                        period_growth_df = period_volume_sum_df.sort_values(by=[period_col_name, 'Keyword']).copy()
                        period_growth_df['Prev Volume'] = period_growth_df.groupby('Keyword')['Search Volume'].shift(1)
                        mask_growth = (period_growth_df['Prev Volume'] > 0) & (pd.notna(period_growth_df['Prev Volume']))
                        period_growth_df['Period Growth (%)'] = np.nan 
                        period_growth_df.loc[mask_growth, 'Period Growth (%)'] = ((period_growth_df['Search Volume'] - period_growth_df['Prev Volume']) / period_growth_df['Prev Volume']) * 100
                        mask_inf = (period_growth_df['Prev Volume'] == 0) & (period_growth_df['Search Volume'] > 0) & (pd.notna(period_growth_df['Prev Volume']))
                        period_growth_df.loc[mask_inf, 'Period Growth (%)'] = np.inf 
                        # Uchováme Inf pre logiku, ale nahradíme pre výpočet pivot tabuľky (ak by spôsoboval problémy)
                        period_growth_pivot_data = period_growth_df.replace([np.inf, -np.inf], np.nan).copy() 
                        
                        heatmap_data = period_growth_pivot_data.pivot(index='Keyword', columns=period_col_name, values='Period Growth (%)')
                        if keyword_order_list: heatmap_data = heatmap_data.reindex(index=keyword_order_list).dropna(how='all')
                        sorted_periods = sorted(heatmap_data.columns, key=period_sort_key) 
                        heatmap_data = heatmap_data[sorted_periods]
                        
                        if not heatmap_data.empty:
                             # Pripravíme textové popisky s 'Inf%' a '%'
                             text_labels = heatmap_data.applymap(lambda x: f"{x:.0f}%" if pd.notna(x) and np.isfinite(x) else ('Inf%' if x == np.inf else ('-Inf%' if x == -np.inf else '-'))).values
                             # Nahradíme Inf/NaN v pôvodných dátach pre škálu heatmapy (napr. veľkými/malými číslami)
                             heatmap_display_data = heatmap_data.replace([np.inf], 9999).replace([-np.inf],-9999).fillna(0) # Fillna(0) pre stred farebnej škály
                             
                             fig_heatmap = px.imshow( heatmap_display_data, labels=dict(x=granularity_label, y="Značka", color="Rast (%)"), title=f"Medziobdobový rast (%) - {granularity.lower()}", text_auto=False, aspect="auto", color_continuous_scale='RdYlGn', color_continuous_midpoint=0, range_color=[-100, 200] )
                             fig_heatmap.update_traces(
                                 text=text_labels, # Použijeme naformátované popisky
                                 texttemplate="%{text}", # Zobrazíme ich ako sú
                                 hovertemplate="<b>%{y}</b><br>%{x}<br>Rast: %{z:.0f}%<extra></extra>" # Tooltip používa pôvodnú numerickú hodnotu 'z'
                             )
                             fig_heatmap.update_xaxes(side="bottom"); fig_heatmap.update_layout(height=max(450, len(heatmap_data.index)*40)) 
                             st.plotly_chart(fig_heatmap, use_container_width=True)
                             try: img_bytes_heatmap = fig_heatmap.to_image(format="png", scale=3); st.download_button(label="📥 Stiahnuť Heatmapu Rastu", data=img_bytes_heatmap, file_name=f"sos_growth_heatmap_{selected_location_code}_{selected_language_code}_{granularity}.png", mime="image/png", key=f"download_heatmap_{granularity}")
                             except Exception as img_e: st.warning(f"Chyba PNG (Heatmap): {img_e}.")
                        else: st.info("Nebolo možné vypočítať medziobdobový rast.")
                     else: st.info("Pre výpočet medziobdobového rastu sú potrebné aspoň dve časové periódy.")
                except Exception as e: st.error(f"Chyba pri generovaní heatmapy rastu: {e}"); st.exception(e)
            
            else: # Ak agregácia zlyhala alebo nevrátila dáta
                st.warning(f"Neboli nájdené žiadne agregované dáta pre granularitu '{granularity}' na zobrazenie detailných analýz.")

            st.markdown("---") 
            # --- Pôvodná Tabuľka Mesačných Dát a CSV Download ---
            st.subheader("📚 Tabuľka pôvodných dát (Mesačne)")
            try:
                if 'history_df_raw' in locals() and not history_df_raw.empty:
                    history_df_display = history_df_raw.copy(); history_df_display['Date'] = history_df_display['Date'].dt.strftime('%Y-%m')
                    st.dataframe(history_df_display[['Keyword', 'Date', 'Search Volume']].sort_values(by=['Keyword', 'Date']).reset_index(drop=True), height=300, use_container_width=True)
                else: st.warning("Pôvodné mesačné dáta neboli nájdené alebo spracované.")
            except Exception as e: st.error(f"Chyba pri zobrazovaní tabuľky: {e}")

            st.subheader("📥 Stiahnuť dáta (Mesačne)")
            try:
                 if 'history_df_raw' in locals() and not history_df_raw.empty:
                    @st.cache_data 
                    def convert_df_to_csv(df): return df[['Keyword', 'Date', 'Search Volume']].to_csv(index=False).encode('utf-8')
                    csv_data = convert_df_to_csv(history_df_raw); st.download_button(label="Stiahnuť mesačné dáta ako CSV", data=csv_data, file_name=f'dataforseo_monthly_history_{selected_location_code}_{selected_language_code}.csv', mime='text/csv', key="download_csv")
                 else: st.warning("Žiadne dáta na stiahnutie.")
            except Exception as e: st.error(f"Chyba pri príprave CSV na stiahnutie: {e}")

    # Prípad, kedy API nevrátilo dáta, ale ani explicitnú chybu (z cache)
    elif current_error is None and not current_data:
         st.warning("🤔 API nevrátilo žiadne výsledky pre zadané kritériá.")

# Ak ešte nebol stlačený gombík a nie je nič v cache pre tento kľúč
elif session_key not in st.session_state:
     st.info("⬆️ Zadajte parametre a kliknite na tlačidlo pre zobrazenie dát.")