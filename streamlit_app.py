"""
Hlavný súbor Streamlit aplikácie pre Share of Search Tool.
Implementuje navigáciu, autentifikáciu a prepína medzi rôznymi režimami analýzy.
"""
import streamlit as st

# Nastavenie konfigurácie stránky - MUSÍ byť prvým st.* príkazom v aplikácii
st.set_page_config(
    page_title="Share of Search Tool",
    layout="wide",
    initial_sidebar_state="expanded"
)

import logging
from typing import Optional, Tuple, List, Dict, Any

# Importy z vlastných modulov
import config                     # Konfigurácia, konštanty, načítanie secrets
import ui.sidebar as ui_sidebar   # Modul pre vykreslenie postranného panela
import ui.single_country_page as ui_single_country  # Modul pre stránku analýzy jednej krajiny
import ui.multi_country_page_async as ui_multi_country    # Modul pre stránku analýzy viacerých krajín

# Nastavenie loggingu
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def authenticate() -> bool:
    """Implementuje autentifikáciu pomocou PIN kódu.
    
    Returns:
        bool: True ak je užívateľ autentifikovaný, inak False.
    """
    app_pin = config.get_app_pin()
    
    # Ak nie je nastavený PIN, autentifikácia nie je potrebná
    if not app_pin:
        return True
        
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    if st.session_state.authenticated:
        return True
    
    # Vyžiadať PIN od používateľa
    pin_placeholder = st.empty()
    entered_pin = pin_placeholder.text_input(
        "🔑 Zadajte prístupový PIN kód:", 
        type="password", 
        key="pin_input_main_app_unique"
    )
    
    if entered_pin:
        if entered_pin == app_pin:
            st.session_state.authenticated = True
            pin_placeholder.empty()
            st.rerun()
            return True
        else:
            st.error("Nesprávny PIN kód.")
            return False
    else:
        st.info("Pre prístup k aplikácii zadajte PIN kód.")
        return False

def validate_api_credentials(api_login: Optional[str], api_password: Optional[str]) -> bool:
    """Skontroluje prítomnosť API prihlasovacích údajov.
    
    Args:
        api_login: API prihlasovacie meno
        api_password: API heslo
        
    Returns:
        bool: True ak sú prihlasovacie údaje platné, inak False.
    """
    if not api_login or not api_password:
        st.error("Chyba: DataForSEO prihlasovacie údaje nie sú správne nakonfigurované v Streamlit Secrets (.streamlit/secrets.toml). Aplikácia nemôže pokračovať bez nich.")
        return False
    return True

def main():
    """Hlavná funkcia Streamlit aplikácie."""
    st.title("Share of Search Tool")

    # Autentifikácia používateľa
    if not authenticate():
        st.stop()

    # Načítanie API prihlasovacích údajov
    api_login, api_password = config.get_dataforseo_credentials()
    
    # Renderovanie postranného panela a získanie dostupných možností
    location_options, locations_error, language_options, languages_error = ui_sidebar.render_sidebar(api_login, api_password)
    
    # Kontrola API prihlasovacích údajov
    if not validate_api_credentials(api_login, api_password):
        ui_sidebar.render_sidebar(None, None) 
        st.stop()
    
    # Získanie režimu analýzy z session state
    analysis_mode = st.session_state.get('analysis_mode_radio', "Analýza jednej krajiny") 

    # Zobrazenie príslušnej stránky podľa režimu analýzy
    if analysis_mode == "Analýza jednej krajiny":
        ui_single_country.render_single_country_page(
            api_login, api_password, 
            location_options, language_options, 
            locations_error, languages_error
        )
    elif analysis_mode == "Analýza viacerých krajín":
        # Kontrola, či sú potrebné options načítané
        if not location_options and not locations_error: 
            st.warning("Zoznam krajín nie je k dispozícii. Funkcionalita 'Analýza viacerých krajín' môže byť obmedzená alebo nefunkčná.")
        if not language_options and not languages_error:
            st.warning("Zoznam jazykov nie je k dispozícii. Funkcionalita 'Analýza viacerých krajín' môže byť obmedzená alebo nefunkčná.")
        
        ui_multi_country.render_multi_country_page(
            api_login, api_password, 
            location_options, language_options, 
            locations_error, languages_error
        )
    else:
        st.error("Neznámy režim analýzy. Prosím, vyberte jednu z možností v postrannom paneli.")

if __name__ == "__main__":
    main()