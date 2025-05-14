import streamlit as st

# API Endpointy
SEARCH_VOLUME_LIVE_URL = "https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live"
LOCATIONS_URL = "https://api.dataforseo.com/v3/keywords_data/google_ads/locations"
LANGUAGES_URL = "https://api.dataforseo.com/v3/keywords_data/google_ads/languages"

# Prednastavené kľúčové slová
DEFAULT_KEYWORDS = "isadore\ncastelli\nrapha\nmaap\npas normal studios\nvan rysel"

# Prednastavené kódy krajín pre Multi-Country analýzu (SK, CZ, DE, AT)
# Tieto kódy by mali zodpovedať kódom z DataForSEO API
DEFAULT_MULTI_COUNTRY_CODES = [2703, 2203, 2276, 2040] 

# Informácie o aplikácii
APP_VERSION = "v1.2"
APP_YEAR = "2025" # Alebo dynamický rok: from datetime import date; APP_YEAR = str(date.today().year)
APP_AUTHOR = "Marek Šulik"
APP_AUTHOR_WEBSITE = "https://mareksulik.sk"
APP_COPYRIGHT_NOTICE = f"© {APP_YEAR}, {APP_AUTHOR}"
APP_CREDITS = "Vytvorené s pomocou Google Gemini a Streamlit."
APP_DATA_PROCESSING_INFO = "Všetky dáta sú spracované a vizualizované pomocou Pythonu a knižnice Plotly."
APP_VERSION_DATE = "2025-05-14" # Dátum poslednej významnejšej úpravy verzie


def get_dataforseo_credentials():
    """Načíta DataForSEO prihlasovacie údaje zo Streamlit Secrets."""
    login = st.secrets.get("dataforseo", {}).get("login")
    password = st.secrets.get("dataforseo", {}).get("password")
    return login, password

def get_app_pin():
    """Načíta PIN kód aplikácie zo Streamlit Secrets."""
    return st.secrets.get("app", {}).get("pin")