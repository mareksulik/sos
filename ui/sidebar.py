"""
Modul pre vykreslenie postranného panela aplikácie.
Obsahuje funkcie pre zobrazenie menu, nastavení a informácií o aplikácii.
"""
from typing import List, Tuple, Optional, Dict, Any
import streamlit as st

from config import (
    AppInfo, 
    DEFAULT_MULTI_COUNTRY_CODES
)
# Importujeme load_locations a load_languages z api_client
from api_client.dataforseo_client import load_locations, load_languages

def render_sidebar(api_login: Optional[str], api_password: Optional[str]) -> Tuple[List, Optional[str], List, Optional[str]]:
    """Vykreslí postranný panel aplikácie.
    
    Args:
        api_login: DataForSEO API prihlasovacie meno
        api_password: DataForSEO API heslo
        
    Returns:
        Tuple[List, Optional[str], List, Optional[str]]: 
            (location_options, locations_error, language_options, languages_error)
    """
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
            if is_auth_error: 
                login_status_placeholder.error("❌ Chyba API Prihlásenia! Skontrolujte credentials v Secrets.")
            else: 
                login_status_placeholder.warning("⚠️ Problém s API. Skontrolujte chyby nižšie.")
            
            if locations_error: 
                st.sidebar.error(f"Krajiny: {locations_error}")
            if languages_error: 
                st.sidebar.error(f"Jazyky: {languages_error}")
    else:
        login_status_placeholder.error("❌ API prihlasovacie údaje nenájdené v Streamlit Secrets!")
        locations_error = "Chýbajú API prihlasovacie údaje."  # Nastavíme chyby pre UI
        languages_error = "Chýbajú API prihlasovacie údaje."

    # Sekcia pre výber režimu analýzy
    _render_analysis_mode_section()
    
    # Sekcia dokumentácie
    _render_documentation_section()
    
    # Informácie o copyrighte a aplikácii
    _render_copyright_section()

    return location_options, locations_error, language_options, languages_error

def _render_analysis_mode_section():
    """Vykreslí sekciu pre výber režimu analýzy."""
    st.sidebar.markdown("---")
    st.sidebar.header("🚀 Režim Dashboardu")
    
    options_tuple_analysis_mode = ("Analýza jednej krajiny", "Analýza viacerých krajín")
    
    if 'analysis_mode_radio' not in st.session_state or st.session_state.analysis_mode_radio not in options_tuple_analysis_mode:
        st.session_state.analysis_mode_radio = options_tuple_analysis_mode[0] 
    
    # Widget pre výber režimu, jeho stav sa uloží do st.session_state.analysis_mode_radio
    # Použijeme jedinečný kľúč s prefixom, aby sme zabránili duplicite
    st.sidebar.radio(
        "Vyberte typ analýzy:", 
        options_tuple_analysis_mode, 
        key="sidebar_analysis_mode_radio", 
        index=options_tuple_analysis_mode.index(st.session_state.analysis_mode_radio),
        on_change=_update_analysis_mode
    )

def _update_analysis_mode():
    """Aktualizuje globálny stav analýzy na základe výberu v postrannom paneli."""
    st.session_state.analysis_mode_radio = st.session_state.sidebar_analysis_mode_radio

def _render_documentation_section():
    """Vykreslí sekciu s odkazmi na dokumentáciu."""
    st.sidebar.markdown("---")
    st.sidebar.header("ℹ️ Dokumentácia")
    st.sidebar.markdown("[DataForSEO Dokumentácia v3](https://docs.dataforseo.com/v3/)")
    st.sidebar.markdown("[Dokumentácia k Lokáciám](https://docs.dataforseo.com/v3/keywords_data/google_ads/locations/)")
    st.sidebar.markdown("[Dokumentácia k Jazykom](https://docs.dataforseo.com/v3/keywords_data/google_ads/languages/)")
    st.sidebar.markdown("[Dokumentácia k Search Volume](https://docs.dataforseo.com/v3/keywords_data/google_ads/search_volume/live/)")

def _render_copyright_section():
    """Vykreslí sekciu s informáciami o copyrighte a aplikácii."""
    st.sidebar.markdown("---")
    st.sidebar.header("©️ Copyright")
    st.sidebar.markdown(f"[{AppInfo.COPYRIGHT_NOTICE}]({AppInfo.AUTHOR_WEBSITE})")
    st.sidebar.markdown("Všetky práva vyhradené.")
    st.sidebar.markdown(f"{AppInfo.CREDITS}")
    st.sidebar.markdown(f"{AppInfo.DATA_PROCESSING_INFO}")
    st.sidebar.markdown(f"{AppInfo.VERSION} ({AppInfo.VERSION_DATE})")