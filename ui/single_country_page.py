import streamlit as st
import pandas as pd
from datetime import date, timedelta 

# Importy z vlastných modulov
from config import DEFAULT_KEYWORDS 
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

def render_single_country_page(api_login, api_password, location_options, language_options, locations_error, languages_error):
    st.header("🔍 Analýza jednej krajiny") 
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.subheader("Kľúčové slová")
        if 'keywords_input_single' not in st.session_state: 
            st.session_state.keywords_input_single = DEFAULT_KEYWORDS
        st.text_area("Zadajte kľúčové slová:", key="keywords_input_single", height=150, help="Každé kľúčové slovo na nový riadok.")

    with col2:
        st.subheader("Krajina")
        selected_location_code, selected_location_display_name = None, ""
        loc_selectbox_disabled = not location_options or not api_login or not api_password
        
        if not loc_selectbox_disabled:
            loc_display_list_s = [opt[0] for opt in location_options]
            loc_code_map_s = {name: code for name, code in location_options}
            
            if 'location_select_single' not in st.session_state or st.session_state.location_select_single not in loc_display_list_s:
                default_loc_name = next((name for name, code_val in location_options if code_val == 2703), loc_display_list_s[0] if loc_display_list_s else "")
                st.session_state.location_select_single = default_loc_name
            
            # Widget si hodnotu načíta zo session_state vďaka 'key'
            st.selectbox("Vyber krajinu:", options=loc_display_list_s, key="location_select_single", help="Zoznam krajín načítaný z API.")
            selected_location_display_name = st.session_state.location_select_single 
            if selected_location_display_name:
                selected_location_code = loc_code_map_s.get(selected_location_display_name)
        else:
            st.info("Zoznam krajín nie je dostupný.")
            if locations_error and (api_login and api_password): st.warning(f"Chyba pri načítaní krajín: {locations_error}")

        st.subheader("Jazyk")
        selected_language_code, selected_language_display_name = None, None
        lang_selectbox_disabled = not language_options or not api_login or not api_password
        if not lang_selectbox_disabled:
            lang_display_list_s = [opt[0] for opt in language_options]
            lang_code_map_s = {name: code for name, code in language_options}
            if 'language_select_single' not in st.session_state or st.session_state.language_select_single not in lang_display_list_s:
                default_lang_name = next((name for name, code_val in language_options if code_val.lower() == 'sk'), lang_display_list_s[0] if lang_display_list_s else "")
                st.session_state.language_select_single = default_lang_name

            st.selectbox("Vyberte jazyk:", options=lang_display_list_s, key="language_select_single", help="Zoznam jazykov načítaný z API.")
            selected_language_display_name = st.session_state.language_select_single 
            if selected_language_display_name:
                selected_language_code = lang_code_map_s.get(selected_language_display_name)
        else:
            st.info("Zoznam jazykov nie je dostupný.")
            if languages_error and (api_login and api_password): st.warning(f"Chyba pri načítaní jazykov: {languages_error}")

    with col3:
        st.subheader("Rozsah dátumov")
        today_s = date.today() 
        default_end_date_s = (today_s.replace(day=1) - timedelta(days=1))
        default_start_date_s = (default_end_date_s.replace(year=default_end_date_s.year - 3) + timedelta(days=1))
        min_allowed_date_val = date(2015,1,1)

        if 'date_from_single' not in st.session_state: st.session_state.date_from_single = default_start_date_s
        if 'date_to_single' not in st.session_state: st.session_state.date_to_single = default_end_date_s
        
        # Úprava logiky pre konzistenciu dátumov pred zobrazením widgetov
        if not isinstance(st.session_state.date_from_single, date): st.session_state.date_from_single = default_start_date_s
        if not isinstance(st.session_state.date_to_single, date): st.session_state.date_to_single = default_end_date_s

        if st.session_state.date_from_single > st.session_state.date_to_single:
            st.session_state.date_to_single = st.session_state.date_from_single
        if st.session_state.date_to_single > default_end_date_s:
             st.session_state.date_to_single = default_end_date_s
        if st.session_state.date_from_single > st.session_state.date_to_single: # Opätovná kontrola
             st.session_state.date_from_single = st.session_state.date_to_single.replace(year=st.session_state.date_to_single.year -1)
             if st.session_state.date_from_single < min_allowed_date_val:
                 st.session_state.date_from_single = min_allowed_date_val
        
        # Odstránený parameter 'value', widget si hodnotu načíta zo session_state vďaka 'key'
        st.date_input("Dátum od:", min_value=min_allowed_date_val, max_value=st.session_state.date_to_single, key="date_from_single")
        st.date_input("Dátum do:", min_value=st.session_state.date_from_single, max_value=default_end_date_s, key="date_to_single")
        
        st.subheader("Granularita Zobrazenia")
        single_granularity_options = ['Ročne', 'Štvrťročne', 'Mesačne']
        if 'granularity_choice_single' not in st.session_state: st.session_state.granularity_choice_single = 'Ročne'
        st.radio("Agregovať dáta:", options=single_granularity_options, key="granularity_choice_single", horizontal=True)

    keywords_list_single = [kw.strip() for kw in st.session_state.keywords_input_single.splitlines() if kw.strip()]
    date_from_input_single = st.session_state.date_from_single 
    date_to_input_single = st.session_state.date_to_single
    granularity_single_str = st.session_state.granularity_choice_single 
    granularity_single_label = granularity_single_str.replace('e','á') 

    st.info("Poznámka: API vracia dáta len za obdobie, pre ktoré sú dostupné v Google Ads zdroji (typicky max. posledných ~4-5 rokov), aj keď zvolíte starší 'Dátum od'.")
    
    run_button_disabled_single = not selected_location_code or not selected_language_code or not api_login or not api_password or not keywords_list_single
    session_key_single = f"data_single_{tuple(sorted(keywords_list_single))}_{selected_location_code}_{selected_language_code}_{date_from_input_single}_{date_to_input_single}_{granularity_single_str}"
    cache_info_placeholder_single = st.empty()

    if session_key_single in st.session_state and st.session_state[session_key_single].get("data") is not None:
         cache_info_placeholder_single.success("✅ Dáta pre tieto parametre (analýza jednej krajiny) sú v cache session.")

    if st.button("📊 Získať dáta a zobraziť grafy", type="primary", disabled=run_button_disabled_single, key="run_button_single"):
        if not keywords_list_single: st.warning("⚠️ Zadajte kľúčové slová.")
        elif date_from_input_single > date_to_input_single: st.error("🚨 Dátum 'od' nemôže byť neskorší ako 'do'.")
        else:
            keywords_tuple_s = tuple(sorted(keywords_list_single))
            cache_info_placeholder_single.empty() 
            
            if session_key_single in st.session_state and st.session_state[session_key_single].get("data") is not None:
                cache_info_placeholder_single.success("✅ Používam dáta z cache session (analýza jednej krajiny).")
            else: 
                cache_info_placeholder_single.info("ℹ️ Cache session (analýza jednej krajiny) nenájdená, volám API...")
                with st.spinner("⏳ Získavam dáta z DataForSEO API..."):
                     results_data_list_s, error_msg_s = fetch_search_volume_data_single(
                         api_login, api_password, 
                         keywords_tuple_s, selected_location_code, selected_language_code, 
                         date_from_input_single, date_to_input_single
                     )
                     st.session_state[session_key_single] = {"data": results_data_list_s, "error": error_msg_s, "granularity": granularity_single_str}
                cache_info_placeholder_single.empty() 
            
            current_data_s_after_fetch = st.session_state[session_key_single].get("data")
            current_error_s_after_fetch = st.session_state[session_key_single].get("error")
            if not current_error_s_after_fetch and current_data_s_after_fetch is not None and current_data_s_after_fetch:
                st.success("✅ Dáta (analýza jednej krajiny) úspešne získané/načítané!")
            elif not current_error_s_after_fetch and current_data_s_after_fetch == []:
                st.info("ℹ️ API nevrátilo žiadne dáta pre zadané kritériá, alebo dáta v cache sú prázdne.")
            elif current_error_s_after_fetch: 
                st.error(f"🚨 Chyba pri získavaní dát: {current_error_s_after_fetch}")

    if session_key_single in st.session_state:
        current_data_s = st.session_state[session_key_single].get("data")
        current_error_s = st.session_state[session_key_single].get("error")
        # Použijeme granularitu uloženú v session_state pre daný kľúč, alebo aktuálnu z UI
        granularity_s_for_charts_str = st.session_state[session_key_single].get("granularity", st.session_state.granularity_choice_single)
        granularity_s_for_charts_label = granularity_s_for_charts_str.replace('e','á')

        if current_error_s and not (current_data_s is not None and current_data_s):
            st.error(f"🚨 Nastala chyba pri získavaní dát (analýza jednej krajiny):\n{current_error_s}")
        elif current_data_s is not None: 
            if not current_data_s: 
                st.info("ℹ️ Neboli nájdené žiadne historické dáta pre zadané kľúčové slová, krajinu a jazyk v danom časovom období.")
            else:
                history_df_raw_s = pd.DataFrame(current_data_s)
                if history_df_raw_s.empty:
                    st.info("ℹ️ Neboli nájdené žiadne historické dáta na spracovanie.")
                    return

                history_df_raw_s['Date'] = pd.to_datetime(history_df_raw_s['Date'])
                
                period_col_name_s = 'Period'
                history_df_agg_s = add_period_column(history_df_raw_s.copy(), granularity_s_for_charts_str, 'Date', period_col_name_s)
                period_sort_key_s = get_period_sort_key_func(granularity_s_for_charts_str)
                
                period_volume_sum_df_s = history_df_agg_s.groupby([period_col_name_s, 'Keyword'], observed=False)['Search Volume'].sum().reset_index()
                
                keyword_order_list_s = None
                if not period_volume_sum_df_s.empty:
                    total_volume_overall_s = period_volume_sum_df_s.groupby('Keyword')['Search Volume'].sum().sort_values(ascending=False).index
                    keyword_order_list_s = list(total_volume_overall_s)

                st.markdown("---"); st.subheader(f"1. {granularity_s_for_charts_label} podiel | Krajina: {selected_location_display_name}, Jazyk: {selected_language_display_name}")
                sos_df_s = calculate_sos_data(period_volume_sum_df_s, period_col_name_s)
                fig1 = create_sos_bar_chart_single(sos_df_s, period_col_name_s, granularity_s_for_charts_str, granularity_s_for_charts_label, keyword_order_list_s, selected_location_display_name or "N/A", selected_language_display_name or "N/A")
                if fig1: 
                    st.plotly_chart(fig1, use_container_width=True)
                    try:
                        img_bytes = fig1.to_image(format="png", scale=3)
                        st.download_button(label="📥 Stiahnuť Graf Podielu (PNG)", data=img_bytes, file_name=f"sos_share_{selected_location_code}_{selected_language_code}_{granularity_s_for_charts_str}.png", mime="image/png", key=f"download_share_{granularity_s_for_charts_str}_single_ch")
                    except Exception as e: st.warning(f"Chyba pri exporte PNG grafu Podielu: {e}.")
                else: st.info(f"Nenašli sa žiadne dáta na zobrazenie grafu '1. {granularity_s_for_charts_label.lower()} podiel'.")
                
                if not period_volume_sum_df_s.empty:
                    st.markdown("---"); st.subheader(f"2. Priemerný mesačný objem segmentu")
                    avg_segment_volume_df_s = calculate_average_monthly_segment_volume(history_df_raw_s.copy(), granularity_s_for_charts_str, period_col_name_s)
                    fig2 = create_bar_chart_avg_segment_volume_single(avg_segment_volume_df_s, period_col_name_s, granularity_s_for_charts_str, granularity_s_for_charts_label)
                    if fig2:
                        st.plotly_chart(fig2, use_container_width=True)
                        try:
                            img_bytes_g2 = fig2.to_image(format="png", scale=3)
                            st.download_button(label="📥 Stiahnuť Graf Priem. Obj. Segmentu", data=img_bytes_g2, file_name=f"sos_avg_segment_{selected_location_code}_{selected_language_code}_{granularity_s_for_charts_str}.png", mime="image/png", key=f"download_avg_segment_{granularity_s_for_charts_str}_single_ch")
                        except Exception as e: st.warning(f"Chyba PNG (Priem. Seg.): {e}.")
                    else: st.warning("N/A dáta pre graf '2. Priemerný mesačný objem segmentu'.")
                    
                    st.markdown("---"); st.subheader(f"3. Priemerný mesačný objem konkurentov")
                    avg_keyword_volume_df_s = calculate_average_monthly_keyword_volume(history_df_raw_s.copy(), granularity_s_for_charts_str, period_col_name_s)
                    fig3 = create_line_chart_avg_keyword_volume_single(avg_keyword_volume_df_s, period_col_name_s, granularity_s_for_charts_str, granularity_s_for_charts_label, keyword_order_list_s)
                    if fig3:
                        st.plotly_chart(fig3, use_container_width=True)
                        try:
                            img_bytes_g3 = fig3.to_image(format="png", scale=3)
                            st.download_button(label="📥 Stiahnuť Graf Priem. Obj. Konkurentov", data=img_bytes_g3, file_name=f"sos_avg_competitor_{selected_location_code}_{selected_language_code}_{granularity_s_for_charts_str}.png", mime="image/png", key=f"download_avg_comp_{granularity_s_for_charts_str}_single_ch")
                        except Exception as e: st.warning(f"Chyba PNG (Priem. Konk.): {e}.")
                    else: st.warning("N/A dáta pre graf '3. Priemerný mesačný objem konkurentov'.")
                    
                    # NOVÝ Graf 4: Priemerný mesačný objem konkurentov (Skladaný stĺpcový)
                    st.markdown("---"); st.subheader(f"4. Priemerný mesačný objem konkurentov (Skladaný stĺpcový)")
                    # Použijeme rovnaké dáta avg_keyword_volume_df_s ako pre graf 3
                    if not avg_keyword_volume_df_s.empty:
                        fig4_stacked_bar = create_stacked_bar_avg_keyword_volume_single(avg_keyword_volume_df_s, period_col_name_s, granularity_s_for_charts_str, granularity_s_for_charts_label, keyword_order_list_s)
                        if fig4_stacked_bar:
                            st.plotly_chart(fig4_stacked_bar, use_container_width=True)
                            try:
                                img_bytes_g4_stacked = fig4_stacked_bar.to_image(format="png", scale=3)
                                st.download_button(label="📥 Stiahnuť Graf Priem. Obj. Konk. (Skladaný) (PNG)", data=img_bytes_g4_stacked, file_name=f"sos_avg_competitor_stacked_{selected_location_code}_{selected_language_code}_{granularity_s_for_charts_str}.png", mime="image/png", key=f"download_avg_comp_stacked_{granularity_s_for_charts_str}_single")
                            except Exception as e: st.warning(f"Chyba PNG (Priem. Konk. Skladaný): {e}.")
                        else: st.warning("N/A dáta pre graf '4. Priemerný mesačný objem konkurentov (Skladaný stĺpcový)'.")
                    else:
                        st.warning("N/A dáta pre graf '4. Priemerný mesačný objem konkurentov (Skladaný stĺpcový)'.")

                    st.markdown("---"); st.subheader(f"5. Tempo rastu ({granularity_s_for_charts_label})") # Zmenené číslovanie
                    heatmap_data_s = calculate_growth_data(period_volume_sum_df_s, period_col_name_s, period_sort_key_s)
                    if not heatmap_data_s.empty:
                        if keyword_order_list_s: heatmap_data_s = heatmap_data_s.reindex(index=keyword_order_list_s).dropna(how='all', axis=0)
                        fig5_heatmap = create_heatmap_growth_single(heatmap_data_s, granularity_s_for_charts_label)
                        if fig5_heatmap:
                            fig5_heatmap.update_layout(title=f"5. Medziobdobový rast (%) - {granularity_s_for_charts_label.lower()}") # Upravíme titulok s novým číslom
                            st.plotly_chart(fig5_heatmap, use_container_width=True)
                            try:
                                img_bytes_g5 = fig5_heatmap.to_image(format="png", scale=3)
                                st.download_button(label="📥 Stiahnuť Heatmapu Rastu", data=img_bytes_g5, file_name=f"sos_growth_heatmap_{selected_location_code}_{selected_language_code}_{granularity_s_for_charts_str}.png", mime="image/png", key=f"download_heatmap_{granularity_s_for_charts_str}_single_g5")
                            except Exception as e: st.warning(f"Chyba PNG (Heatmap): {e}.")
                        else: st.info("Nebolo možné zobraziť heatmapu rastu.")
                    else: st.info("Pre výpočet medziobdobového rastu sú potrebné aspoň dve časové periódy alebo dáta.")
                else: 
                    st.warning("Neboli nájdené žiadne agregované dáta na zobrazenie detailných grafov.")
                
                # --- História vyhľadávaní ---
                st.markdown("---"); st.subheader("6. História vyhľadávaní") # Zmenené číslovanie
                if 'search_history_single' not in st.session_state: 
                    st.session_state.search_history_single = []
                
                current_request_info_single = {
                    'keywords': keywords_list_single, 
                    'location': selected_location_display_name or "N/A", 
                    'location_code': selected_location_code, 
                    'language': selected_language_display_name or "N/A", 
                    'language_code': selected_language_code, 
                    'date_from': date_from_input_single, 
                    'date_to': date_to_input_single, 
                    'granularity': granularity_s_for_charts_str,
                    'session_key': session_key_single, 
                    'timestamp': pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                request_exists_single = any(hist_item['session_key'] == session_key_single for hist_item in st.session_state.search_history_single)
                if not request_exists_single and current_data_s: 
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
                                st.markdown(f"**Granularita:** {hist_item['granularity']}")
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
                        st.session_state.search_history_single = []; st.success("História bola vymazaná."); st.rerun()
                else: st.info("Zatiaľ žiadne vyhľadávania v histórii.")

                # --- Stiahnutie dát ---
                st.markdown("---"); st.subheader("7. Stiahnuť dáta ako CSV") # Zmenené číslovanie
                try:
                     if not history_df_raw_s.empty: 
                          @st.cache_data 
                          def convert_df_to_csv_single_final(df_to_convert): 
                              df_sorted = df_to_convert[['Keyword', 'Date', 'Search Volume']].sort_values(by=['Keyword','Date'])
                              df_sorted['Date'] = pd.to_datetime(df_sorted['Date']).dt.strftime('%Y-%m-%d')
                              return df_sorted.to_csv(index=False).encode('utf-8')
                          csv_data = convert_df_to_csv_single_final(history_df_raw_s.copy())
                          st.download_button(label="Stiahnuť pôvodné mesačné dáta ako CSV", data=csv_data, file_name=f'sos_data_single_country.csv', mime='text/csv', key="download_csv_single_final")
                     elif not current_error_s: st.warning("Žiadne dáta na stiahnutie.")
                except Exception as e: st.error(f"Chyba pri príprave CSV na stiahnutie: {e}")

        elif run_button_disabled_single and (api_login and api_password): 
            missing_parts_single = [p for p,v in [("kľúčové slová",keywords_list_single),("krajinu",selected_location_code),("jazyk",selected_language_code)] if not v]
            if missing_parts_single: st.warning(f"⚠️ Vyberte prosím {', '.join(missing_parts_single)} pre pokračovanie.")