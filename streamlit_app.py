import streamlit as st

# Importy z vlastných modulov
import config                     # Konfigurácia, konštanty, načítanie secrets
import ui.sidebar as ui_sidebar   # Modul pre vykreslenie postranného panela
import ui.single_country_page as ui_single_country  # Modul pre stránku analýzy jednej krajiny
import ui.multi_country_page as ui_multi_country    # Modul pre stránku analýzy viacerých krajín

def main():
    """Hlavná funkcia Streamlit aplikácie."""
    st.set_page_config(page_title="Share of Search Tool", layout="wide")
    st.title("Share of Search Tool")

    # --- PIN Autentifikácia ---
    app_pin = config.get_app_pin()
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    
    should_check_pin = bool(app_pin) 

    if should_check_pin and not st.session_state.authenticated:
        pin_placeholder = st.empty()
        entered_pin = pin_placeholder.text_input("🔑 Zadajte prístupový PIN kód:", type="password", key="pin_input_main_app_unique")
        if entered_pin:
            if entered_pin == app_pin:
                st.session_state.authenticated = True
                pin_placeholder.empty()
                st.rerun() 
            else:
                st.error("Nesprávny PIN kód.")
                st.stop() 
        else:
             if not entered_pin: 
                 st.info("Pre prístup k aplikácii zadajte PIN kód.")
             st.stop()
    elif not should_check_pin and 'authenticated' not in st.session_state: 
        st.session_state.authenticated = True


    # --- Hlavná logika aplikácie po autentifikácii ---
    if st.session_state.authenticated:
        api_login, api_password = config.get_dataforseo_credentials()
        
        if not api_login or not api_password:
            st.error("Chyba: DataForSEO prihlasovacie údaje nie sú správne nakonfigurované v Streamlit Secrets (.streamlit/secrets.toml). Aplikácia nemôže pokračovať bez nich.")
            ui_sidebar.render_sidebar(None, None) 
            st.stop() 
        
        location_options, locations_error, language_options, languages_error = ui_sidebar.render_sidebar(api_login, api_password)

        analysis_mode = st.session_state.get('analysis_mode_radio', "Analýza jednej krajiny") 

        if analysis_mode == "Analýza jednej krajiny":
            ui_single_country.render_single_country_page(
                api_login, api_password, 
                location_options, language_options, 
                locations_error, languages_error
            )
        elif analysis_mode == "Analýza viacerých krajín":
            # Kontrola, či sú potrebné options načítané, aj keď by to malo byť pokryté už v sidebar
            if not location_options and not locations_error : 
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