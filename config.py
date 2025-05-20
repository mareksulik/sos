"""
Konfiguračný modul pre Share of Search Tool.
Obsahuje nastavenia, konštanty a pomocné funkcie pre celú aplikáciu.
"""
from typing import Tuple, Optional, Dict, List, Any
from datetime import date
import streamlit as st

# API Endpointy
class ApiEndpoints:
    """API endpointy pre DataForSEO."""
    SEARCH_VOLUME_LIVE = "https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live"
    LOCATIONS = "https://api.dataforseo.com/v3/keywords_data/google_ads/locations"
    LANGUAGES = "https://api.dataforseo.com/v3/keywords_data/google_ads/languages"

# Prednastavené kľúčové slová
DEFAULT_KEYWORDS = "isadore\ncastelli\nrapha\nmaap\npas normal studios\nvan rysel"

# Prednastavené kódy krajín pre Multi-Country analýzu (SK, CZ, DE, AT)
# Tieto kódy zodpovedajú kódom z DataForSEO API
DEFAULT_MULTI_COUNTRY_CODES = [2703, 2203, 2276, 2040] 

# Nastavenia cachovania (v sekundách)
class CacheSettings:
    """Nastavenia TTL (Time To Live) pre cachované dáta."""
    LOCATIONS_TTL = 3600  # 1 hodina
    LANGUAGES_TTL = 3600  # 1 hodina
    SEARCH_DATA_TTL = 3600  # 1 hodina

# Nastavenia spracovávania dát
class DataProcessingSettings:
    """Nastavenia pre spracovanie dát."""
    API_REQUEST_TIMEOUT = 60  # sekundy pre timeout API requestov
    API_RATE_LIMIT_SLEEP = 5.5  # sekundy prestávky medzi API volaniami
    ASYNC_BATCH_SIZE = 5  # počet súbežných API volaní v jednej dávke
    ASYNC_BATCH_PAUSE = 3  # pauza medzi dávkami API volaní v sekundách
    
    @classmethod
    def get(cls, name, default=None):
        """Získa hodnotu nastavenia podľa názvu alebo vráti predvolenú hodnotu."""
        return getattr(cls, name, default)

# Informácie o aplikácii
class AppInfo:
    """Informácie o aplikácii."""
    VERSION = "v1.3"
    YEAR = str(date.today().year)  # Dynamický rok
    AUTHOR = "Marek Šulik"
    AUTHOR_WEBSITE = "https://mareksulik.sk"
    COPYRIGHT_NOTICE = f"© {YEAR}, {AUTHOR}"
    CREDITS = "Vytvorené s pomocou Google Gemini a Streamlit."
    DATA_PROCESSING_INFO = "Všetky dáta sú spracované a vizualizované pomocou Pythonu a knižníc Pandas a Plotly."
    VERSION_DATE = "2025-05-20"  # Dátum poslednej významnejšej úpravy verzie

def get_dataforseo_credentials() -> Tuple[Optional[str], Optional[str]]:
    """Načíta DataForSEO prihlasovacie údaje zo Streamlit Secrets.
    
    Returns:
        Tuple[Optional[str], Optional[str]]: Dvojica (login, heslo) alebo (None, None) ak údaje nie sú k dispozícii.
    """
    login = st.secrets.get("dataforseo", {}).get("login")
    password = st.secrets.get("dataforseo", {}).get("password")
    return login, password

def get_app_pin() -> Optional[str]:
    """Načíta PIN kód aplikácie zo Streamlit Secrets.
    
    Returns:
        Optional[str]: PIN kód alebo None ak nie je nastavený.
    """
    return st.secrets.get("app", {}).get("pin")