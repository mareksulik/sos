import streamlit as st
import pandas as pd
from datetime import date, timedelta

# Importy z vlastných modulov
from config import DEFAULT_KEYWORDS, DEFAULT_MULTI_COUNTRY_CODES
from data_processing.fetcher import fetch_multi_country_search_volume_data
from data_processing.transformer import (
    add_period_column,
    get_period_sort_key_func,
    transform_total_sos_across_countries,
    transform_total_average_volume_across_countries,
    transform_flexible_avg_volume,
    transform_segment_average_volume_custom_countries,
    # NOVÝ IMPORT: Transformačná funkcia pre flexibilný objem podľa krajín
    transform_flexible_avg_volume_by_country_display
)
from ui.charts import (
    create_mc_total_sos_chart,
    create_mc_total_avg_volume_chart,
    create_mc_flexible_avg_volume_chart,
    create_mc_flexible_avg_volume_stacked_bar_chart,
    create_mc_segment_avg_volume_custom_countries_chart,
    # NOVÉ IMPORTY: Funkcie pre nové grafy zobrazujúce krajiny
    create_mc_flexible_avg_volume_by_country_line_chart,
    create_mc_flexible_avg_volume_by_country_stacked_bar_chart
)

def render_multi_country_page(api_login, api_password, location_options_all, language_options_all, locations_error_msg, languages_error_msg):
    st.header("🌍 Analýza viacerých krajín")
    
    col1_mc, col2_mc, col3_mc = st.columns(3)
    with col1_mc:
        st.subheader("Kľúčové slová")
        if 'mc_keywords_input' not in st.session_state:
            st.session_state.mc_keywords_input = DEFAULT_KEYWORDS
        st.text_area("Zadajte kľúčové slová:", key="mc_keywords_input", height=150, help="Každé kľúčové slovo na nový riadok.")
    with col2_mc:
        st.subheader("Krajiny (Hlavný filter)")
        loc_display_list_mc = [opt[0] for opt in location_options_all] if location_options_all else []
        code_to_display_name_map_mc = {code: name for name, code in location_options_all} if location_options_all else {}
        if not location_options_all or not api_login or not api_password:
            st.info("Zoznam krajín nie je dostupný.")
            if locations_error_msg and (api_login and api_password): st.warning(f"Chyba pri načítaní lokácií: {locations_error_msg}")
        else:
            if 'mc_selected_locations' not in st.session_state: 
                default_display_names_to_set = [code_to_display_name_map_mc[code] for code in DEFAULT_MULTI_COUNTRY_CODES if code in code_to_display_name_map_mc]
                default_display_names_to_set = [name for name in default_display_names_to_set if name in loc_display_list_mc] 
                if not default_display_names_to_set: 
                    if len(loc_display_list_mc) >= 2: default_display_names_to_set = loc_display_list_mc[:min(4,len(loc_display_list_mc))]
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
        today_mc = date.today(); default_end_date_mc = today_mc.replace(day=1) - timedelta(days=1)
        default_start_date_mc = (default_end_date_mc.replace(year=default_end_date_mc.year - 3, month=1, day=1)) # Default 3 celé roky dozadu + začiatok roka
        if default_end_date_mc < default_start_date_mc: 
             default_start_date_mc = default_end_date_mc.replace(year=default_end_date_mc.year-1)


        min_allowed_date_val_mc = date(2015, 1, 1); max_allowed_end_date_mc = today_mc.replace(day=1) - timedelta(days=1)
        
        if 'mc_date_from' not in st.session_state: st.session_state.mc_date_from = default_start_date_mc
        if 'mc_date_to' not in st.session_state: st.session_state.mc_date_to = default_end_date_mc
        
        # Úprava logiky pre konzistenciu dátumov pred zobrazením widgetov
        if not isinstance(st.session_state.mc_date_from, date): st.session_state.mc_date_from = default_start_date_mc
        if not isinstance(st.session_state.mc_date_to, date): st.session_state.mc_date_to = default_end_date_mc

        if st.session_state.mc_date_from > st.session_state.mc_date_to:
            st.session_state.mc_date_to = st.session_state.mc_date_from
        if st.session_state.mc_date_to > max_allowed_end_date_mc:
             st.session_state.mc_date_to = max_allowed_end_date_mc
        if st.session_state.mc_date_from > st.session_state.mc_date_to: # Opätovná kontrola
             st.session_state.mc_date_from = st.session_state.mc_date_to.replace(year=st.session_state.mc_date_to.year -1)
             if st.session_state.mc_date_from < min_allowed_date_val_mc:
                 st.session_state.mc_date_from = min_allowed_date_val_mc
        
        st.date_input("Dátum od:", min_value=min_allowed_date_val_mc, max_value=st.session_state.mc_date_to, key="mc_date_from")
        st.date_input("Dátum do:", min_value=st.session_state.mc_date_from, max_value=max_allowed_end_date_mc, key="mc_date_to")
        
        st.subheader("Granularita Zobrazenia")
        mc_granularity_options = ['Ročne', 'Štvrťročne', 'Mesačne']
        if 'mc_granularity_choice' not in st.session_state: st.session_state.mc_granularity_choice = 'Ročne' 
        st.radio("Agregovať dáta:", options=mc_granularity_options, key="mc_granularity_choice", horizontal=True)

    keywords_list_mc = [kw.strip() for kw in st.session_state.mc_keywords_input.splitlines() if kw.strip()]
    selected_main_countries_display = st.session_state.get('mc_selected_locations', [])
    selected_location_codes_mc = []
    loc_code_map_mc_local = {opt[0]: opt[1] for opt in location_options_all} if location_options_all else {}
    if location_options_all and selected_main_countries_display and loc_code_map_mc_local:
        selected_location_codes_mc = [loc_code_map_mc_local[name] for name in selected_main_countries_display if name in loc_code_map_mc_local]
    
    selected_language_code_mc = None 
    if 'mc_language_select' in st.session_state and language_options_all:
        temp_lang_code_map_mc_local = {name: code for name, code in language_options_all}
        selected_language_code_mc = temp_lang_code_map_mc_local.get(st.session_state.mc_language_select)
    
    date_from_input_mc = st.session_state.mc_date_from
    date_to_input_mc = st.session_state.mc_date_to
    granularity_mc_str = st.session_state.mc_granularity_choice 
    
    run_button_disabled_mc = not selected_location_codes_mc or not selected_language_code_mc or not api_login or not api_password or not keywords_list_mc
    
    mc_session_key = f"multi_data_{tuple(sorted(keywords_list_mc))}_{tuple(sorted(selected_location_codes_mc))}_{selected_language_code_mc}_{date_from_input_mc}_{date_to_input_mc}_{granularity_mc_str}"
    
    mc_cache_info_placeholder = st.empty()
    if mc_session_key in st.session_state and st.session_state[mc_session_key].get("data") is not None:
         mc_cache_info_placeholder.success("✅ Dáta pre tieto parametre (analýza viacerých krajín) sú v cache session.")

    if st.button("📊 Získať dáta a zobraziť grafy (Analýza viacerých krajín)", type="primary", disabled=run_button_disabled_mc, key="mc_run_button"):
        if not keywords_list_mc: st.warning("⚠️ Zadajte kľúčové slová.")
        elif not selected_location_codes_mc: st.warning("⚠️ Vyberte aspoň jednu krajinu v hlavnom filtri.")
        elif not selected_language_code_mc: st.warning("⚠️ Vyberte jazyk.")
        elif date_from_input_mc > date_to_input_mc: st.error("🚨 Dátum 'od' nemôže byť neskorší ako 'do'.")
        else:
            keywords_tuple_mc = tuple(sorted(keywords_list_mc)); locations_tuple_mc = tuple(sorted(selected_location_codes_mc))
            all_loc_options_tuple_for_cache = tuple(location_options_all) if location_options_all else tuple()
            
            mc_cache_info_placeholder.empty()
            if mc_session_key in st.session_state and st.session_state[mc_session_key].get("data") is not None:
                 mc_cache_info_placeholder.success("✅ Používam dáta z cache session (analýza viacerých krajín).")
            else:
                mc_cache_info_placeholder.info("ℹ️ Cache session (analýza viacerých krajín) nenájdená, volám API...")
                with st.spinner("⏳ Získavam dáta pre analýzu viacerých krajín..."):
                    results_df_mc, error_msg_mc = fetch_multi_country_search_volume_data(
                        api_login, api_password, 
                        keywords_tuple_mc, 
                        locations_tuple_mc, 
                        selected_language_code_mc, 
                        date_from_input_mc, date_to_input_mc, 
                        all_loc_options_tuple_for_cache 
                    )
                st.session_state[mc_session_key] = {"data": results_df_mc, "error": error_msg_mc, "granularity": granularity_mc_str}
                mc_cache_info_placeholder.empty() 

            current_df_mc_on_run = st.session_state[mc_session_key].get("data")
            current_error_mc_on_run = st.session_state[mc_session_key].get("error") 
            
            if not current_error_mc_on_run and current_df_mc_on_run is not None and not current_df_mc_on_run.empty: 
                st.success("✅ Dáta (analýza viacerých krajín) úspešne získané/načítané!")
            elif not current_error_mc_on_run and current_df_mc_on_run is not None and current_df_mc_on_run.empty: 
                st.info("ℹ️ API nevrátilo žiadne dáta pre zadané kritériá, alebo dáta v cache sú prázdne.")
            elif current_error_mc_on_run: 
                st.error(f"🚨 Nastala chyba pri získavaní dát: {current_error_mc_on_run}")

    if mc_session_key in st.session_state:
        current_df_mc = st.session_state[mc_session_key].get("data") 
        current_error_mc = st.session_state[mc_session_key].get("error")
        granularity_mc_str_for_charts = st.session_state[mc_session_key].get("granularity", st.session_state.mc_granularity_choice)
        granularity_mc_label_for_charts = granularity_mc_str_for_charts.replace('e','á')

        if current_error_mc and not (current_df_mc is not None and not current_df_mc.empty):
            if "Pre zadané kritériá" in current_error_mc : st.info(f"ℹ️ {current_error_mc}")
            else: st.error(f"🚨 Nastala chyba pri získavaní dát (analýza viacerých krajín):\n{current_error_mc}")
        elif current_df_mc is not None: 
            if current_df_mc.empty:
                st.info("ℹ️ Neboli nájdené žiadne historické dáta pre kombináciu zadaných kľúčových slov, krajín a jazyka v danom časovom období.")
            else:
                mc_history_df_raw = current_df_mc.copy()
                mc_history_df_raw['Date'] = pd.to_datetime(mc_history_df_raw['Date'])
                
                period_col_name_mc = 'Period'
                mc_history_df_agg = add_period_column(mc_history_df_raw.copy(), granularity_mc_str_for_charts, 'Date', period_col_name_mc)
                
                keyword_order_list_mc = None
                if not mc_history_df_agg.empty:
                    keyword_volumes_for_ordering = mc_history_df_agg.groupby('Keyword')['Search Volume'].sum().sort_values(ascending=False)
                    if not keyword_volumes_for_ordering.empty:
                         keyword_order_list_mc = list(keyword_volumes_for_ordering.index)

                # Graf 1: Celkový SoS
                st.markdown("---"); st.subheader(f"1. Celkový Share of Search ({granularity_mc_label_for_charts}) naprieč všetkými vybranými krajinami")
                df_for_graph1_data = mc_history_df_agg.groupby([period_col_name_mc, 'Keyword'], observed=False)['Search Volume'].sum().reset_index()
                df_total_sos_mc = transform_total_sos_across_countries(df_for_graph1_data, period_col_name_mc)
                fig1 = create_mc_total_sos_chart(df_total_sos_mc, period_col_name_mc, granularity_mc_str_for_charts, granularity_mc_label_for_charts, keyword_order_list_mc)
                if fig1: st.plotly_chart(fig1, use_container_width=True)
                else: st.info("Nedostatok dát pre graf '1. Celkový Share of Search'.")

                # Graf 2: Celkový priemerný objem
                st.markdown("---"); st.subheader(f"2. Celkový priemerný objem vyhľadávania ({granularity_mc_label_for_charts}) naprieč všetkými vybranými krajinami")
                df_total_avg_vol_mc = transform_total_average_volume_across_countries(mc_history_df_raw.copy(), granularity_mc_str_for_charts, period_col_name_mc)
                fig2 = create_mc_total_avg_volume_chart(df_total_avg_vol_mc, period_col_name_mc, granularity_mc_str_for_charts, granularity_mc_label_for_charts, keyword_order_list_mc)
                if fig2: st.plotly_chart(fig2, use_container_width=True)
                else: st.info("Nedostatok dát pre graf '2. Celkový priemerný objem vyhľadávania'.")
                
                # Dostupné kľúčové slová a krajiny pre flexibilné filtre (definované raz)
                available_keywords_flex = sorted(mc_history_df_agg['Keyword'].unique()) if not mc_history_df_agg.empty else []
                available_countries_flex = sorted(mc_history_df_agg['Country'].unique()) if not mc_history_df_agg.empty else []

                # Graf 3: Flexibilný PRIEMERNÝ objem (Čiarový) - ZOBRAZUJE ZNAČKY
                st.markdown("---"); st.subheader(f"3. Flexibilný priemerný objem pre Značky (Čiarový) ({granularity_mc_label_for_charts})")
                st.markdown("Graf zobrazuje priemerný objem vyhľadávania pre každú vybranú značku. Dáta pre každú značku sú súčtom objemov z nižšie vybraných krajín.")
                col_flex_avg_vol_kw_g3, col_flex_avg_vol_co_g3 = st.columns(2)
                with col_flex_avg_vol_kw_g3: # Výber značiek na zobrazenie
                    if 'flex_avg_vol_keywords_g3_line' not in st.session_state or not set(st.session_state.flex_avg_vol_keywords_g3_line).issubset(set(available_keywords_flex)): 
                        st.session_state.flex_avg_vol_keywords_g3_line = available_keywords_flex[:min(3, len(available_keywords_flex))]
                    selected_flex_avg_vol_keywords_g3 = st.multiselect("Vyberte značky pre graf 3 (zobrazia sa ako čiary):", options=available_keywords_flex, key="flex_avg_vol_keywords_g3_line")
                with col_flex_avg_vol_co_g3: # Výber krajín na sčítanie
                    if 'flex_avg_vol_countries_g3_line' not in st.session_state or not set(st.session_state.flex_avg_vol_countries_g3_line).issubset(set(available_countries_flex)):
                        st.session_state.flex_avg_vol_countries_g3_line = available_countries_flex[:min(2, len(available_countries_flex))]
                    selected_flex_avg_vol_countries_g3 = st.multiselect("Vyberte krajiny pre graf 3 (ich dáta sa sčítajú pre každú značku):", options=available_countries_flex, key="flex_avg_vol_countries_g3_line")

                if selected_flex_avg_vol_keywords_g3 and selected_flex_avg_vol_countries_g3:
                    df_flex_avg_vol_g3_data = transform_flexible_avg_volume(
                        mc_history_df_raw.copy(), 
                        selected_flex_avg_vol_keywords_g3, 
                        selected_flex_avg_vol_countries_g3, 
                        granularity_mc_str_for_charts, 
                        period_col_name_mc
                    )
                    fig3_line = create_mc_flexible_avg_volume_chart(
                        df_flex_avg_vol_g3_data, 
                        period_col_name_mc, 
                        granularity_mc_str_for_charts, 
                        granularity_mc_label_for_charts, 
                        selected_flex_avg_vol_keywords_g3, # Poradie značiek
                        ", ".join(selected_flex_avg_vol_countries_g3) # Reťazec krajín pre titulok
                    )
                    if fig3_line: 
                        fig3_line.update_layout(title=f"3. Priemerný objem pre vybrané ZNAČKY (krajiny sčítané: {', '.join(selected_flex_avg_vol_countries_g3)}) - Čiarový")
                        st.plotly_chart(fig3_line, use_container_width=True)
                    else: st.info("Nedostatok dát pre graf '3. Flexibilný priemerný objem pre Značky (Čiarový)' s vybranými parametrami.")
                else: st.info("Vyberte aspoň jednu značku a jednu krajinu pre graf '3. Flexibilný priemerný objem pre Značky (Čiarový)'.")

                # Graf 4: Flexibilný PRIEMERNÝ objem (Skladaný stĺpcový) - ZOBRAZUJE ZNAČKY
                st.markdown("---"); st.subheader(f"4. Flexibilný priemerný objem pre Značky (Skladaný stĺpcový) ({granularity_mc_label_for_charts})")
                st.markdown("Graf zobrazuje priemerný objem vyhľadávania pre každú vybranú značku formou skladaného stĺpca. Dáta pre každú značku sú súčtom objemov z nižšie vybraných krajín.")
                col_flex_avg_stacked_kw_g4, col_flex_avg_stacked_co_g4 = st.columns(2)
                with col_flex_avg_stacked_kw_g4: # Výber značiek na zobrazenie
                    if 'flex_avg_stacked_keywords_g4' not in st.session_state or not set(st.session_state.flex_avg_stacked_keywords_g4).issubset(set(available_keywords_flex)):
                        st.session_state.flex_avg_stacked_keywords_g4 = st.session_state.get("flex_avg_vol_keywords_g3_line", available_keywords_flex[:min(3, len(available_keywords_flex))])
                    selected_flex_avg_stacked_keywords_g4 = st.multiselect("Vyberte značky pre graf 4 (zobrazia sa ako časti stĺpca):", options=available_keywords_flex, key="flex_avg_stacked_keywords_g4")
                with col_flex_avg_stacked_co_g4: # Výber krajín na sčítanie
                    if 'flex_avg_stacked_countries_g4' not in st.session_state or not set(st.session_state.flex_avg_stacked_countries_g4).issubset(set(available_countries_flex)):
                        st.session_state.flex_avg_stacked_countries_g4 = st.session_state.get("flex_avg_vol_countries_g3_line", available_countries_flex[:min(2, len(available_countries_flex))])
                    selected_flex_avg_stacked_countries_g4 = st.multiselect("Vyberte krajiny pre graf 4 (ich dáta sa sčítajú pre každú značku):", options=available_countries_flex, key="flex_avg_stacked_countries_g4")

                if selected_flex_avg_stacked_keywords_g4 and selected_flex_avg_stacked_countries_g4:
                    df_flex_avg_vol_g4_stacked_data = transform_flexible_avg_volume(
                        mc_history_df_raw.copy(), 
                        selected_flex_avg_stacked_keywords_g4, 
                        selected_flex_avg_stacked_countries_g4, 
                        granularity_mc_str_for_charts, 
                        period_col_name_mc
                    )
                    if df_flex_avg_vol_g4_stacked_data is not None and not df_flex_avg_vol_g4_stacked_data.empty:
                        fig4_stacked_bar = create_mc_flexible_avg_volume_stacked_bar_chart(
                            df_flex_avg_vol_g4_stacked_data, 
                            period_col_name_mc, 
                            granularity_mc_str_for_charts, 
                            granularity_mc_label_for_charts, 
                            selected_flex_avg_stacked_keywords_g4, # Poradie značiek
                            ", ".join(selected_flex_avg_stacked_countries_g4) # Reťazec krajín pre titulok
                        )
                        if fig4_stacked_bar: 
                            fig4_stacked_bar.update_layout(title=f"4. Priemerný objem pre vybrané ZNAČKY (krajiny sčítané: {', '.join(selected_flex_avg_stacked_countries_g4)}) - Skladaný stĺpcový")
                            st.plotly_chart(fig4_stacked_bar, use_container_width=True)
                        else: st.info("Nedostatok dát pre graf '4. Flexibilný priemerný objem pre Značky (Skladaný stĺpcový)' s vybranými parametrami.")
                    else:
                        st.info("Nedostatok dát pre graf '4. Flexibilný priemerný objem pre Značky (Skladaný stĺpcový)' po transformácii.")
                else:
                    st.info("Vyberte aspoň jednu značku a jednu krajinu pre graf '4. Flexibilný priemerný objem pre Značky (Skladaný stĺpcový)'.")
                

                # --- NOVÝ GRAF 5: Flexibilný priemerný objem PODĽA KRAJÍN (Čiarový) ---
                st.markdown("---"); st.subheader(f"5. Flexibilný priemerný objem podľa Krajín (Čiarový) ({granularity_mc_label_for_charts})")
                st.markdown("Graf zobrazuje priemerný objem vyhľadávania pre každú vybranú krajinu. Dáta pre každú krajinu sú súčtom objemov všetkých nižšie vybraných značiek.")
                
                col_flex_by_country_kw_g5, col_flex_by_country_co_g5 = st.columns(2)
                with col_flex_by_country_kw_g5: # Výber značiek, ktorých dáta sa sčítajú
                    default_brands_g5 = available_keywords_flex[:min(3, len(available_keywords_flex))] if available_keywords_flex else []
                    if 'flex_by_country_brands_g5_line' not in st.session_state or not set(st.session_state.flex_by_country_brands_g5_line).issubset(set(available_keywords_flex)): 
                        st.session_state.flex_by_country_brands_g5_line = default_brands_g5
                    selected_brands_for_g5_aggregation = st.multiselect("Vyberte značky (ich objemy sa sčítajú pre každú krajinu v grafe 5):", options=available_keywords_flex, key="flex_by_country_brands_g5_line", default=st.session_state.flex_by_country_brands_g5_line)
                
                with col_flex_by_country_co_g5: # Výber krajín, ktoré sa zobrazia ako série
                    default_countries_g5_display = available_countries_flex[:min(3, len(available_countries_flex))] if available_countries_flex else []
                    if 'flex_by_country_countries_g5_line' not in st.session_state or not set(st.session_state.flex_by_country_countries_g5_line).issubset(set(available_countries_flex)):
                        st.session_state.flex_by_country_countries_g5_line = default_countries_g5_display
                    selected_countries_for_g5_display = st.multiselect("Vyberte krajiny (zobrazia sa ako samostatné čiary v grafe 5):", options=available_countries_flex, key="flex_by_country_countries_g5_line", default=st.session_state.flex_by_country_countries_g5_line)

                if selected_brands_for_g5_aggregation and selected_countries_for_g5_display:
                    df_flex_avg_vol_by_country_g5_data = transform_flexible_avg_volume_by_country_display(
                        mc_history_df_raw.copy(), 
                        selected_brands_for_g5_aggregation, 
                        selected_countries_for_g5_display, 
                        granularity_mc_str_for_charts, 
                        period_col_name_mc
                    )
                    
                    country_order_g5 = None
                    if df_flex_avg_vol_by_country_g5_data is not None and not df_flex_avg_vol_by_country_g5_data.empty:
                         country_volumes_for_ordering_g5 = df_flex_avg_vol_by_country_g5_data.groupby('Country')['Average Search Volume'].sum().sort_values(ascending=False)
                         if not country_volumes_for_ordering_g5.empty:
                              country_order_g5 = list(country_volumes_for_ordering_g5.index)
                    
                    fig5_by_country_line = create_mc_flexible_avg_volume_by_country_line_chart(
                        df_flex_avg_vol_by_country_g5_data, 
                        period_col_name_mc, 
                        granularity_mc_str_for_charts, 
                        granularity_mc_label_for_charts, 
                        country_order_g5, 
                        ", ".join(selected_brands_for_g5_aggregation),
                        title_prefix="5."
                    )
                    if fig5_by_country_line: 
                        st.plotly_chart(fig5_by_country_line, use_container_width=True)
                    else: st.info("Nedostatok dát pre graf '5. Flexibilný priemerný objem podľa Krajín (Čiarový)' s vybranými parametrami.")
                else: st.info("Pre graf 5 vyberte aspoň jednu značku (na sčítanie) a aspoň jednu krajinu (na zobrazenie).")


                # --- NOVÝ GRAF 6: Flexibilný priemerný objem PODĽA KRAJÍN (Skladaný stĺpcový) ---
                st.markdown("---"); st.subheader(f"6. Flexibilný priemerný objem podľa Krajín (Skladaný stĺpcový) ({granularity_mc_label_for_charts})")
                st.markdown("Graf zobrazuje priemerný objem vyhľadávania pre každú vybranú krajinu formou skladaného stĺpca. Dáta pre každú krajinu sú súčtom objemov všetkých nižšie vybraných značiek.")

                col_flex_by_country_kw_g6, col_flex_by_country_co_g6 = st.columns(2)
                with col_flex_by_country_kw_g6: # Výber značiek na agregáciu
                    default_brands_g6 = st.session_state.get("flex_by_country_brands_g5_line", available_keywords_flex[:min(3, len(available_keywords_flex))] if available_keywords_flex else [])
                    if 'flex_by_country_brands_g6_stacked' not in st.session_state or not set(st.session_state.flex_by_country_brands_g6_stacked).issubset(set(available_keywords_flex)):
                        st.session_state.flex_by_country_brands_g6_stacked = default_brands_g6
                    selected_brands_for_g6_aggregation = st.multiselect("Vyberte značky (ich objemy sa sčítajú pre každú krajinu v grafe 6):", options=available_keywords_flex, key="flex_by_country_brands_g6_stacked", default=st.session_state.flex_by_country_brands_g6_stacked)
                
                with col_flex_by_country_co_g6: # Výber krajín na zobrazenie
                    default_countries_g6_display = st.session_state.get("flex_by_country_countries_g5_line", available_countries_flex[:min(3, len(available_countries_flex))] if available_countries_flex else [])
                    if 'flex_by_country_countries_g6_stacked' not in st.session_state or not set(st.session_state.flex_by_country_countries_g6_stacked).issubset(set(available_countries_flex)):
                        st.session_state.flex_by_country_countries_g6_stacked = default_countries_g6_display
                    selected_countries_for_g6_display = st.multiselect("Vyberte krajiny (zobrazia sa ako časti stĺpca v grafe 6):", options=available_countries_flex, key="flex_by_country_countries_g6_stacked", default=st.session_state.flex_by_country_countries_g6_stacked)

                if selected_brands_for_g6_aggregation and selected_countries_for_g6_display:
                    df_flex_avg_vol_by_country_g6_data = transform_flexible_avg_volume_by_country_display(
                        mc_history_df_raw.copy(), 
                        selected_brands_for_g6_aggregation, 
                        selected_countries_for_g6_display, 
                        granularity_mc_str_for_charts, 
                        period_col_name_mc
                    )

                    country_order_g6 = None
                    if df_flex_avg_vol_by_country_g6_data is not None and not df_flex_avg_vol_by_country_g6_data.empty:
                         country_volumes_for_ordering_g6 = df_flex_avg_vol_by_country_g6_data.groupby('Country')['Average Search Volume'].sum().sort_values(ascending=False)
                         if not country_volumes_for_ordering_g6.empty:
                              country_order_g6 = list(country_volumes_for_ordering_g6.index)

                    fig6_by_country_stacked = create_mc_flexible_avg_volume_by_country_stacked_bar_chart(
                        df_flex_avg_vol_by_country_g6_data, 
                        period_col_name_mc, 
                        granularity_mc_str_for_charts, 
                        granularity_mc_label_for_charts, 
                        country_order_g6, 
                        ", ".join(selected_brands_for_g6_aggregation),
                        title_prefix="6."
                    )
                    if fig6_by_country_stacked: 
                        st.plotly_chart(fig6_by_country_stacked, use_container_width=True)
                    else: st.info("Nedostatok dát pre graf '6. Flexibilný priemerný objem podľa Krajín (Skladaný stĺpcový)' s vybranými parametrami.")
                else: st.info("Pre graf 6 vyberte aspoň jednu značku (na sčítanie) a aspoň jednu krajinu (na zobrazenie).")

                
                # Graf 7 (pôvodne 5): Priemerný mesačný objem segmentu
                st.markdown("---"); st.subheader(f"7. Priemerný mesačný objem segmentu ({granularity_mc_label_for_charts})") # ZMENENÉ ČÍSLO
                st.markdown("Graf zobrazuje celkový priemerný mesačný objem vyhľadávania všetkých sledovaných značiek dohromady pre vybranú skupinu krajín.")
                
                # Kľúč pre session_state bol upravený, aby odrážal nové číslovanie
                session_key_graph7_countries = 'selected_countries_graph7' 
                available_countries_graph7 = sorted(mc_history_df_agg['Country'].unique()) if not mc_history_df_agg.empty else []
                
                default_countries_g7 = available_countries_graph7[:1] if available_countries_graph7 else []
                if session_key_graph7_countries not in st.session_state or not set(st.session_state[session_key_graph7_countries]).issubset(set(available_countries_graph7)):
                    st.session_state[session_key_graph7_countries] = default_countries_g7
                
                selected_countries_for_graph7 = st.multiselect(
                    "Vyberte krajiny pre graf 7 (dáta sa sčítajú):", 
                    options=available_countries_graph7, 
                    key=session_key_graph7_countries, # Použitie upraveného kľúča
                    default=st.session_state[session_key_graph7_countries]
                )
                
                if selected_countries_for_graph7:
                    df_segment_avg_vol_g7 = transform_segment_average_volume_custom_countries(mc_history_df_raw.copy(), selected_countries_for_graph7, granularity_mc_str_for_charts, period_col_name_mc)
                    fig7 = create_mc_segment_avg_volume_custom_countries_chart(df_segment_avg_vol_g7, period_col_name_mc, granularity_mc_str_for_charts, granularity_mc_label_for_charts, ", ".join(selected_countries_for_graph7))
                    if fig7: 
                        fig7.update_layout(title=f"7. Priemerný mesačný objem segmentu (krajiny: {', '.join(selected_countries_for_graph7)})") # ZMENENÉ ČÍSLO V TITULKU
                        st.plotly_chart(fig7, use_container_width=True)
                    else: st.info("Nedostatok dát pre graf '7. Priemerný mesačný objem segmentu'.")
                else: st.info("Vyberte aspoň jednu krajinu pre graf 7.")
                
                # Stiahnutie dát a história
                st.markdown("---"); st.subheader("8. Stiahnuť dáta ako CSV (Analýza viacerých krajín)") # ZMENENÉ ČÍSLO
                try:
                     if not mc_history_df_raw.empty:
                          @st.cache_data 
                          def convert_df_to_csv_mc_final_v4(df): # Zmenený názov funkcie pre cache
                              df_sorted = df[['Keyword', 'Country', 'Location Code', 'Date', 'Search Volume']].sort_values(by=['Keyword', 'Country', 'Date'])
                              df_sorted['Date'] = pd.to_datetime(df_sorted['Date']).dt.strftime('%Y-%m-%d')
                              return df_sorted.to_csv(index=False).encode('utf-8')
                          csv_data = convert_df_to_csv_mc_final_v4(mc_history_df_raw.copy())
                          st.download_button(label="Stiahnuť dáta (analýza viacerých krajín) ako CSV", data=csv_data, file_name=f'data_multi_country.csv', mime='text/csv', key="download_csv_mc_final_v4") # Zmenený kľúč pre tlačidlo
                except Exception as e: st.error(f"Chyba pri príprave CSV na stiahnutie: {e}")

                st.markdown("---"); st.subheader("9. História vyhľadávaní (Analýza viacerých krajín)") # ZMENENÉ ČÍSLO
                if 'search_history_multi' not in st.session_state: st.session_state.search_history_multi = []
                current_display_country_names_mc_hist = st.session_state.get('mc_selected_locations', [])
                current_language_name_mc_hist = st.session_state.get('mc_language_select', "")
                
                # loc_code_map_mc_hist už je definované vyššie ako loc_code_map_mc_local
                current_location_codes_mc_hist = [loc_code_map_mc_local[name] for name in current_display_country_names_mc_hist if name in loc_code_map_mc_local]

                current_request_info_multi = {
                    'keywords': keywords_list_mc, 'countries_display': current_display_country_names_mc_hist, 
                    'location_codes': current_location_codes_mc_hist, 
                    'language': current_language_name_mc_hist, 'language_code': selected_language_code_mc, 
                    'date_from': date_from_input_mc, 'date_to': date_to_input_mc, 
                    'granularity': granularity_mc_str, 
                    'session_key': mc_session_key, 
                    'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
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
                                st.markdown(f"**Granularita:** {hist_item['granularity']}")
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
                    if st.button("🗑️ Vymazať históriu (Analýza viacerých krajín)", key="clear_hist_multi_button_final_v2"): # Zmenený kľúč
                        st.session_state.search_history_multi = []
                        st.success("História vyhľadávaní (Analýza viacerých krajín) bola vymazaná.")
                        st.rerun()
                else: st.info("Zatiaľ nemáte žiadne vyhľadávania v histórii (Analýza viacerých krajín).")
    elif run_button_disabled_mc and (api_login and api_password):
        missing_parts = [p for p,v in [("kľúčové slová",keywords_list_mc),("aspoň jednu krajinu",selected_location_codes_mc),("jazyk",selected_language_code_mc)] if not v]
        if missing_parts: st.warning(f"⚠️ Vyberte prosím {', '.join(missing_parts)} pre pokračovanie v Analýze viacerých krajín.")