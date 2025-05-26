"""
Zjednodušená verzia Share of Search Tool pre lead magnet.
Poskytuje základnú funkcionalitu bez autentifikácie, postranného panela a dodatočných nastavení.
"""
import streamlit as st
import pandas as pd
import logging
import re
import base64
from PIL import Image
from io import BytesIO
from datetime import date, timedelta
from typing import Optional, List, Tuple, Dict, Any
import os
from supabase import create_client


def get_image_as_base64(image_path):
    """
    Konvertuje obrázok na base64 string pre použitie v HTML.
    
    Args:
        image_path: Cesta k súboru obrázka
        
    Returns:
        str: Base64 encoded string
    """
    try:
        img = Image.open(image_path)
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        return base64.b64encode(buffered.getvalue()).decode()
    except Exception as e:
        return ""

# Importy z vlastných modulov
import config
from data_processing.fetcher import fetch_search_volume_data_single
from data_processing.transformer import (
    add_period_column,
    calculate_sos_data,
    calculate_average_monthly_segment_volume,
    calculate_average_monthly_keyword_volume,
    calculate_growth_data,
    get_period_sort_key_func
)
from ui.charts import (
    create_sos_bar_chart_single,
    create_bar_chart_avg_segment_volume_single,
    create_line_chart_avg_keyword_volume_single,
    create_stacked_bar_avg_keyword_volume_single,
    create_heatmap_growth_single
)

# Nastavenie loggingu
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Custom CSS pre lead magnet
CUSTOM_CSS = """
<style>
    .stApp {
        background-color: #F1F0EB;
    }
    .main-header {
        color: #202028;
        font-weight: 700;
    }
    .subheader {
        color: #202028;
        font-size: 1.2rem;
    }
    .logo-container {
        padding: 1.5rem 0;
        text-align: center;
        display: flex;
        justify-content: center;
    }
    .email-input {
        margin-top: 1rem;
    }
    .submit-button {
        background-color: #DAEC34;
        color: #202028;
        font-weight: 600;
    }
    footer {display: none !important;}
    .stDeployButton {display:none;}
    /* Nastavenie šírky aplikácie na 70% */
    .block-container {
        max-width: 70% !important;
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    /* Na mobilných zariadeniach nastavíme šírku na 90% */
    @media screen and (max-width: 768px) {
        .block-container {
            max-width: 90% !important;
        }
    }
    
    /* Prispôsobenie farieb pre formulár a iné prvky */
    .stTextInput > div > div, 
    .stTextArea > div > div, 
    .stSelectbox > div > div {
        border: 1px solid #DAEC34 !important;
        border-radius: 4px;
    }
    
    .stTextInput > div > div > input, 
    .stTextArea > div > div > textarea, 
    .stSelectbox > div > div > div {
        background-color: #303038;
        color: #F1F0EB;
    }
    
    /* Upravenie focus state pre text input a text area */
    .stTextInput > div:focus-within > div,
    .stTextArea > div:focus-within > div,
    .stSelectbox > div:focus-within > div {
        border-color: #DAEC34 !important;
        box-shadow: 0 0 0 1px rgba(218, 236, 52, 0.5);
    }
    h1, h2, h3, p {
        color: #202028;
    }
    .stButton>button {
        background-color: #DAEC34;
        color: #202028;
    }
    
    /* Skrytie horného menu */
    header {display: none !important;}
    .stToolbar {display: none !important;}
</style>
"""

# Nastavenie konfigurácie stránky - MUSÍ byť prvým st.* príkazom v aplikácii
st.set_page_config(
    page_title="Share of Search Tool - Ukážka",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Vloženie vlastného CSS
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

def is_valid_email(email: str) -> bool:
    """Skontroluje, či je email platný.
    
    Args:
        email: Email na kontrolu
        
    Returns:
        bool: True ak je email platný, inak False
    """
    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))

def init_supabase():
    """Inicializuje Supabase klienta.
    
    Returns:
        Supabase klient alebo None v prípade chyby
    """
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        return None

def email_used_three_times(email: str) -> bool:
    """Skontroluje, či email už bol použitý trikrát v Supabase.
    
    Args:
        email: Email na kontrolu
        
    Returns:
        bool: True ak email už bol použitý trikrát, inak False
    """
    try:
        supabase = init_supabase()
        if not supabase:
            logger.error("Failed to initialize Supabase client")
            return False
        
        # Získať počet záznamov s daným emailom
        response = supabase.table('leads').select('id').eq('email', email.lower()).execute()
        
        # Kontrola odpovede
        if hasattr(response, 'data') and isinstance(response.data, list):
            return len(response.data) >= 3
        
        logger.warning(f"Unexpected response from Supabase: {response}")
        return False
        
    except Exception as e:
        logger.error(f"Failed to check if email exists in Supabase: {e}")
        return False

def save_lead_info(email: str, keywords: List[str], country: str, language: str):
    """Uloží informácie o leade do Supabase databázy.
    
    Args:
        email: Email používateľa
        keywords: Kľúčové slová zadané používateľom
        country: Vybraná krajina
        language: Vybraný jazyk
    """
    try:
        supabase = init_supabase()
        if not supabase:
            logger.error("Failed to initialize Supabase client")
            return
        
        # Príprava dát pre vloženie
        data = {
            'email': email.lower(),
            'keywords': ','.join(keywords),
            'country': country,
            'language': language
        }
        
        # Vloženie dát do tabuľky
        response = supabase.table('leads').insert(data).execute()
        
        # Kontrola odpovede
        if hasattr(response, 'data') and isinstance(response.data, list) and len(response.data) > 0:
            logger.info(f"Lead information saved to Supabase: {email}")
        else:
            logger.warning(f"Unexpected response from Supabase: {response}")
            
    except Exception as e:
        logger.error(f"Failed to save lead information to Supabase: {e}")

def get_location_language_options(api_login: str, api_password: str) -> Tuple[Dict[str, Any], str, Dict[str, Any], str]:
    """
    Získa možnosti krajín a jazykov bez vykresľovania UI.
    
    Args:
        api_login: Prihlasovacie meno API
        api_password: Heslo API
        
    Returns:
        Tuple s location_options, locations_error, language_options, languages_error
    """
    from api_client.dataforseo_client import load_locations, load_languages
    
    # Získanie zoznamu krajín
    locations_list, locations_error = load_locations(api_login, api_password)
    location_options = {}
    if locations_list:
        location_options = {loc[0]: loc[1] for loc in locations_list}
    
    # Získanie zoznamu jazykov
    languages_list, languages_error = load_languages(api_login, api_password)
    language_options = {}
    if languages_list:
        language_options = {lang[0]: lang[1] for lang in languages_list}
    
    return location_options, locations_error, language_options, languages_error

def display_results(api_login: str, api_password: str, keywords: List[str], 
                    location_code: str, language_code: str, 
                    date_from: date, date_to: date,
                    location_display_name: str, language_display_name: str,
                    hide_loading: bool = False):
    """
    Zobrazí výsledky analýzy pre zadané parametre.
    
    Args:
        api_login: Prihlasovacie meno API
        api_password: Heslo API
        keywords: Zoznam kľúčových slov
        location_code: Kód vybranej lokality
        language_code: Kód vybraného jazyka
        date_from: Počiatočný dátum
        date_to: Konečný dátum
        location_display_name: Zobrazované meno lokality
        language_display_name: Zobrazované meno jazyka
        hide_loading: Či skryť loading hlásky
    """
    keywords_tuple = tuple(sorted(keywords))
    session_key = f"data_lead_magnet_{keywords_tuple}_{location_code}_{language_code}_{date_from}_{date_to}"
    
    # Granularita je v lead magnete vždy ročná
    granularity_str = "Ročne"
    granularity_label = "Ročná"
    
    if session_key not in st.session_state:
        if not hide_loading:
            with st.spinner("⏳ Získavam dáta z DataForSEO API..."):
                results_data_list, error_msg = fetch_search_volume_data_single(
                    api_login, api_password,
                    keywords_tuple, location_code, language_code,
                    date_from, date_to
                )
                st.session_state[session_key] = {"data": results_data_list, "error": error_msg}
        else:
            results_data_list, error_msg = fetch_search_volume_data_single(
                api_login, api_password,
                keywords_tuple, location_code, language_code,
                date_from, date_to
            )
            st.session_state[session_key] = {"data": results_data_list, "error": error_msg}
    
    current_data = st.session_state[session_key].get("data")
    current_error = st.session_state[session_key].get("error")
    
    if current_error:
        st.error(f"🚨 Nastala chyba pri získavaní dát: {current_error}")
        return
    
    if not current_data:
        st.info("ℹ️ Neboli nájdené žiadne historické dáta pre zadané kľúčové slová, krajinu a jazyk v danom časovom období.")
        return
    
    # Spracovanie dát
    history_df_raw = pd.DataFrame(current_data)
    if history_df_raw.empty:
        st.info("ℹ️ Neboli nájdené žiadne historické dáta na spracovanie.")
        return
    
    history_df_raw['Date'] = pd.to_datetime(history_df_raw['Date'])
    
    period_col_name = 'Period'
    history_df_agg = add_period_column(history_df_raw.copy(), granularity_str, 'Date', period_col_name)
    period_sort_key = get_period_sort_key_func(granularity_str)
    
    period_volume_sum_df = history_df_agg.groupby([period_col_name, 'Keyword'], observed=False)['Search Volume'].sum().reset_index()
    
    keyword_order_list = None
    if not period_volume_sum_df.empty:
        total_volume_overall = period_volume_sum_df.groupby('Keyword')['Search Volume'].sum().sort_values(ascending=False).index
        keyword_order_list = list(total_volume_overall)
    
    # Graf 1: Podiel vyhľadávania
    st.markdown("## Výsledky analýzy")
    st.markdown("### 1. Ročný podiel vyhľadávania")
    sos_df = calculate_sos_data(period_volume_sum_df, period_col_name)
    fig1 = create_sos_bar_chart_single(sos_df, period_col_name, granularity_str, granularity_label, 
                                       keyword_order_list, location_display_name, language_display_name)
    if fig1:
        st.plotly_chart(fig1, use_container_width=True)
    else:
        st.info("Nenašli sa žiadne dáta na zobrazenie grafu podielu vyhľadávania.")
    
    # Graf 2: Priemerný mesačný objem segmentu
    if not period_volume_sum_df.empty:
        st.markdown("### 2. Priemerný mesačný objem segmentu")
        avg_segment_volume_df = calculate_average_monthly_segment_volume(history_df_raw.copy(), granularity_str, period_col_name)
        fig2 = create_bar_chart_avg_segment_volume_single(avg_segment_volume_df, period_col_name, granularity_str, granularity_label)
        if fig2:
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Nenašli sa žiadne dáta na zobrazenie grafu priemerného mesačného objemu segmentu.")
        
        # Graf 3: Priemerný mesačný objem konkurentov
        st.markdown("### 3. Priemerný mesačný objem konkurentov")
        avg_keyword_volume_df = calculate_average_monthly_keyword_volume(history_df_raw.copy(), granularity_str, period_col_name)
        fig3 = create_line_chart_avg_keyword_volume_single(avg_keyword_volume_df, period_col_name, granularity_str, granularity_label, keyword_order_list)
        if fig3:
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("Nenašli sa žiadne dáta na zobrazenie grafu priemerného mesačného objemu konkurentov.")
        
        # Graf 4: Priemerný mesačný objem konkurentov (Skladaný stĺpcový)
        st.markdown("### 4. Priemerný mesačný objem konkurentov (Skladaný stĺpcový)")
        if not avg_keyword_volume_df.empty:
            fig4_stacked_bar = create_stacked_bar_avg_keyword_volume_single(avg_keyword_volume_df, period_col_name, granularity_str, granularity_label, keyword_order_list)
            if fig4_stacked_bar:
                st.plotly_chart(fig4_stacked_bar, use_container_width=True)
            else:
                st.info("Nenašli sa žiadne dáta na zobrazenie grafu priemerného mesačného objemu konkurentov (Skladaný stĺpcový).")
        else:
            st.info("Nenašli sa žiadne dáta na zobrazenie grafu priemerného mesačného objemu konkurentov (Skladaný stĺpcový).")
        
        # Graf 5: Tempo rastu
        st.markdown("### 5. Tempo rastu (Ročne)")
        heatmap_data = calculate_growth_data(period_volume_sum_df, period_col_name, period_sort_key)
        if not heatmap_data.empty:
            if keyword_order_list:
                heatmap_data = heatmap_data.reindex(index=keyword_order_list).dropna(how='all', axis=0)
            fig5_heatmap = create_heatmap_growth_single(heatmap_data, granularity_label)
            if fig5_heatmap:
                st.plotly_chart(fig5_heatmap, use_container_width=True)
            else:
                st.info("Nebolo možné zobraziť heatmapu rastu.")
        else:
            st.info("Pre výpočet medziobdobového rastu sú potrebné aspoň dve časové periódy.")
    else:
        st.warning("Neboli nájdené žiadne agregované dáta na zobrazenie detailných grafov.")

def main():
    """Hlavná funkcia lead magnet aplikácie."""
    # Logo a hlavička
    from PIL import Image
    try:
        # Optimized center alignment with improved styling
        base64_logo = get_image_as_base64("snag.png")
        st.markdown(f"""
        <div style="display: flex; justify-content: center; align-items: center; margin: 10px 0;">
            <img src="data:image/png;base64,{base64_logo}" style="width: 350px;">
        </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Nepodarilo sa načítať logo: {e}")
    
    st.markdown('<h1 class="main-header">Share of Search Tool</h1>', unsafe_allow_html=True)
    
    # Enhanced explanatory text with better styling
    st.markdown("""
    <div style="background-color: #f8f8f8; border-left: 4px solid #DAEC34; padding: 15px; margin: 15px 0; border-radius: 0 5px 5px 0;">
        <p style="font-size: 1.1rem; color: #202028; margin: 0;">
        <strong>Share of Search</strong> je metrika, ktorá meria percentuálny podiel vyhľadávaní vašej značky v porovnaní s konkurenciou v rámci vášho trhu. Vyšší podiel znamená väčšiu viditeľnosť, silnejšie povedomie o značke a potenciálne vyšší tržný podiel.
        </p>
        <p style="font-size: 1.1rem; color: #202028; margin-top: 10px;">
        Tento nástroj vám umožňuje sledovať vývoj objemu vyhľadávaní kľúčových slov za posledné 4 roky, analyzovať trendy a porovnávať výkonnosť vašej značky s konkurentmi. Získate tak cenné dáta o tom, ako sa mení záujem o vašu značku a kde máte priestor na zlepšenie.
        </p>
        <p style="font-size: 1.1rem; color: #202028; margin-top: 10px;">
        Nástroj je úplne zadarmo – stačí len vyplniť formulár nižšie. Jednu emailovú adresu môžete použiť na tri analýzy.
        </p>
    </div>
    """, unsafe_allow_html=True)
        
    # Načítanie API prihlasovacích údajov
    api_login, api_password = config.get_dataforseo_credentials()
    
    # Získanie dostupných krajín a jazykov
    try:
        location_options, locations_error, language_options, languages_error = get_location_language_options(api_login, api_password)
    except Exception as e:
        logger.error(f"Error loading location and language options: {e}")
        st.error("Chyba pri načítaní dát. Skúste neskôr.")
        st.stop()
    
    # Formulár pre zadanie údajov
    with st.form("lead_magnet_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            # Kľúčové slová
            keywords_input = st.text_area(
                "Zadajte kľúčové slová (každé na novom riadku):",
                value="lidl\ntesco\ncoop jednota\nkaufland\nbilla",
                height=150
            )
            
            # Email
            email = st.text_input("Váš email:", placeholder="email@example.com")
            
            # Súhlas s kontaktovaním
            consent = st.checkbox("Súhlasím so zasielaním newslettera v súlade so zásadami ochrany osobných údajov.")
        
        with col2:
            # Krajina
            selected_location_code = None
            selected_location_name = ""
            if location_options:
                location_names = list(location_options.keys())
                # Nastavenie predvolenej krajiny (Slovensko)
                # Najprv hľadáme presný názov "Slovakia"
                default_location = next((loc for loc in location_names if loc == "Slovakia"), None)
                # Ak neexistuje, hľadáme obsahujúce "Slovakia"
                if not default_location:
                    default_location = next((loc for loc in location_names if "Slovakia" in loc), None)
                # Ostatné alternatívy
                if not default_location:
                    default_location = next((loc for loc in location_names if "Slovensko" in loc or "Slovenskej" in loc), location_names[0] if location_names else "")
                
                # Debug info pre výber krajiny
                logger.info(f"Dostupné krajiny: {', '.join(location_names[:5])}...")
                logger.info(f"Vybraná predvolená krajina: {default_location}")
                
                selected_location = st.selectbox("Vyberte krajinu:", options=location_names, index=location_names.index(default_location) if default_location in location_names else 0)
                selected_location_code = location_options[selected_location]
                selected_location_name = selected_location
            else:
                st.error("Nepodarilo sa načítať zoznam krajín.")
                st.stop()
            
            # Jazyk
            selected_language_code = None
            selected_language_name = ""
            if language_options:
                language_names = list(language_options.keys())
                # Nastavenie predvoleného jazyka (Slovenčina)
                default_language = next((lang for lang in language_names if "Slovenčina" in lang or "Slovak" in lang), language_names[0] if language_names else "")
                selected_language = st.selectbox("Vyberte jazyk:", options=language_names, index=language_names.index(default_language) if default_language in language_names else 0)
                selected_language_code = language_options[selected_language]
                selected_language_name = selected_language
            else:
                st.error("Nepodarilo sa načítať zoznam jazykov.")
                st.stop()
        
        # Submit button
        submit_button = st.form_submit_button("Zobraziť analýzu", use_container_width=True)
    
    if submit_button:
        # Validácia vstupu
        if not email or not is_valid_email(email):
            st.error("Zadajte platný email.")
            st.stop()
            
        if not keywords_input.strip():
            st.error("Zadajte aspoň jedno kľúčové slovo.")
            st.stop()
            
        if not consent:
            st.error("Pre pokračovanie je potrebné súhlasiť s kontaktovaním.")
            st.stop()
            
        # Kontrola, či email už bol použitý trikrát
        if email_used_three_times(email):
            st.error("Tento email už bol použitý maximálny počet krát (3). Prosím, použite iný email.")
            st.stop()
        
        # Spracovanie kľúčových slov
        keywords = [kw.strip() for kw in keywords_input.split('\n') if kw.strip()]
        
        # Uloženie informácií o leade
        save_lead_info(email, keywords, selected_location_name, selected_language_name)
        
        # Nastavenie dátumového rozsahu (posledné 3 roky)
        today = date.today() 
        date_to = (today.replace(day=1) - timedelta(days=1))  # Posledný deň predchádzajúceho mesiaca
        date_from = date_to.replace(year=date_to.year - 3) + timedelta(days=1)  # 3 roky dozadu
        
        # Zobrazenie výsledkov
        display_results(
            api_login,
            api_password,
            keywords,
            selected_location_code,
            selected_language_code,
            date_from,
            date_to,
            selected_location_name,
            selected_language_name,
            hide_loading=True
        )
        
        # Jednoduchá správa o úspešnom vytvorení analýzy
        st.success("Analýza úspešne vytvorená!")

if __name__ == "__main__":
    main()
