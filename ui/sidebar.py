import streamlit as st
from config import (
    APP_VERSION, APP_COPYRIGHT_NOTICE, APP_CREDITS, 
    APP_DATA_PROCESSING_INFO, APP_VERSION_DATE, APP_AUTHOR_WEBSITE, APP_AUTHOR
)
# Importujeme load_locations a load_languages z api_client
from api_client.dataforseo_client import load_locations, load_languages

def render_sidebar(api_login, api_password):
    """Vykreslí postranný panel aplikácie."""

    st.sidebar.header("⚙️ Nastavenia DataForSEO API")
    st.sidebar.info("API prihlasovacie údaje sa načítavajú zo Streamlit Secrets.")
    login_status_placeholder = st.sidebar.empty()

    location_options, locations_error, language_options, languages_error = [], None, [], None

    if api_login and api_password:
        location_options, locations_error = load_locations(api_login, api_password)
        language_options, languages_error = load_languages(api_login, api_password)
        if not locations_error and not languages_error:
            login_status_placeholder.success("✅ API Prihlásenie OK (Krajiny a Jazyky načítané)")
        else:
            is_auth_error = ("401" in str(locations_error)) or ("401" in str(languages_error))
            if is_auth_error: login_status_placeholder.error("❌ Chyba API Prihlásenia! Skontrolujte credentials v Secrets.")
            else: login_status_placeholder.warning("⚠️ Problém s API. Skontrolujte chyby nižšie.")
            if locations_error: st.sidebar.error(f"Krajiny: {locations_error}")
            if languages_error: st.sidebar.error(f"Jazyky: {languages_error}")
    else:
        login_status_placeholder.error("❌ API prihlasovacie údaje nenájdené v Streamlit Secrets!")
        locations_error = "Chýbajú API prihlasovacie údaje." # Nastavíme chyby pre UI
        languages_error = "Chýbajú API prihlasovacie údaje."

    st.sidebar.markdown("---")
    st.sidebar.header("🚀 Režim Dashboardu")
    options_tuple_analysis_mode = ("Analýza jednej krajiny", "Analýza viacerých krajín")
    if 'analysis_mode_radio' not in st.session_state or st.session_state.analysis_mode_radio not in options_tuple_analysis_mode:
        st.session_state.analysis_mode_radio = options_tuple_analysis_mode[0] 
    
    # Widget pre výber režimu, jeho stav sa uloží do st.session_state.analysis_mode_radio
    st.sidebar.radio(
        "Vyberte typ analýzy:", 
        options_tuple_analysis_mode, 
        key="analysis_mode_radio", 
        index=options_tuple_analysis_mode.index(st.session_state.analysis_mode_radio)
    )
    
    st.sidebar.markdown("---"); st.sidebar.header("ℹ️ Dokumentácia");
    st.sidebar.markdown("[DataForSEO Dokumentácia v3](https://docs.dataforseo.com/v3/)")
    st.sidebar.markdown("[Dokumentácia k Lokáciám](https://docs.dataforseo.com/v3/keywords_data/google_ads/locations/)")
    st.sidebar.markdown("[Dokumentácia k Jazykom](https://docs.dataforseo.com/v3/keywords_data/google_ads/languages/)")
    st.sidebar.markdown("[Dokumentácia k Search Volume](https://docs.dataforseo.com/v3/keywords_data/google_ads/search_volume/live/)")
    
    st.sidebar.markdown("---"); st.sidebar.header("©️ Copyright");
    st.sidebar.markdown(f"[{APP_COPYRIGHT_NOTICE}]({APP_AUTHOR_WEBSITE})")
    st.sidebar.markdown("Všetky práva vyhradené.")
    st.sidebar.markdown(f"{APP_CREDITS}")
    st.sidebar.markdown(f"{APP_DATA_PROCESSING_INFO}")
    st.sidebar.markdown(f"{APP_VERSION} ({APP_VERSION_DATE})")

    return location_options, locations_error, language_options, languages_error