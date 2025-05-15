import plotly.express as px
import pandas as pd
import numpy as np
from data_processing.transformer import get_period_sort_key_func 

# --- Grafy pre Analýzu jednej krajiny ---
def create_sos_bar_chart_single(df_sos, period_col, granularity_str_for_sort, granularity_label_for_display, keyword_order, location_display_name, language_display_name):
    if df_sos.empty or 'Total Market Volume' not in df_sos.columns or pd.isna(df_sos['Total Market Volume'].sum()) or df_sos['Total Market Volume'].sum() <= 0: 
        return None
    title = f"1. {granularity_label_for_display} podiel | Krajina: {location_display_name}, Jazyk: {language_display_name}"
    unique_periods = sorted(df_sos[period_col].unique(), key=get_period_sort_key_func(granularity_str_for_sort))
    df_plot = df_sos[df_sos['Total Market Volume'] > 0].copy()
    if df_plot.empty: return None
    fig = px.bar(df_plot, x=period_col, y='Share_Percent', color='Keyword', text='Share_Percent', barmode='stack', labels={'Share_Percent': '% Podiel', 'Keyword': 'Značka', period_col: granularity_label_for_display}, title=title, category_orders={"Keyword": keyword_order, period_col: unique_periods})
    fig.update_layout(yaxis_title='% celkového objemu vyhľadávania', yaxis_ticksuffix="%", xaxis_type='category', legend_title_text='Značky', height=800)
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='inside', insidetextanchor='middle', textfont_size=12)
    return fig

def create_bar_chart_avg_segment_volume_single(df_avg_segment, period_col, granularity_str_for_sort, granularity_label_for_display):
    if df_avg_segment.empty or 'Average Total Volume' not in df_avg_segment.columns or df_avg_segment['Average Total Volume'].sum(skipna=True) <= 0: 
        return None
    title = "2. Priemerný mesačný objem segmentu"
    unique_periods = sorted(df_avg_segment[period_col].unique(), key=get_period_sort_key_func(granularity_str_for_sort))
    fig = px.bar(df_avg_segment, x=period_col, y='Average Total Volume', labels={'Average Total Volume': 'Priem. mesačný objem', period_col: granularity_label_for_display}, title=title, category_orders={period_col: unique_periods})
    fig.update_layout(yaxis_title='Priemerný mesačný objem (AVG)', xaxis_type='category', height=550)
    fig.update_traces(texttemplate='%{y:,.0f}', textposition='outside')
    return fig

def create_line_chart_avg_keyword_volume_single(df_avg_keywords, period_col, granularity_str_for_sort, granularity_label_for_display, keyword_order):
    if df_avg_keywords.empty or 'Average Search Volume' not in df_avg_keywords.columns or df_avg_keywords['Average Search Volume'].sum(skipna=True) <=0: 
        return None
    title = f"3. {granularity_label_for_display} vývoj priemerného mesačného objemu"
    unique_periods = sorted(df_avg_keywords[period_col].unique(), key=get_period_sort_key_func(granularity_str_for_sort))
    fig = px.line(df_avg_keywords, x=period_col, y='Average Search Volume', color='Keyword', labels={'Average Search Volume': f'Priem. mesačný objem', 'Keyword': 'Značka', period_col: granularity_label_for_display}, title=title, category_orders={"Keyword": keyword_order, period_col: unique_periods}, markers=True)
    fig.update_layout(yaxis_title=f'Priem. mesačný objem (AVG)', legend_title_text='Značky (kliknite pre filter)', height=700)
    fig.update_traces(mode="markers+lines", hovertemplate="<b>%{fullData.name}</b><br>Perióda: %{x}<br>Priem. objem: %{y:,.0f}<extra></extra>")
    return fig

def create_stacked_bar_avg_keyword_volume_single(df_avg_keywords, period_col, granularity_str_for_sort, granularity_label_for_display, keyword_order):
    if df_avg_keywords.empty or 'Average Search Volume' not in df_avg_keywords.columns or df_avg_keywords['Average Search Volume'].sum(skipna=True) <=0: 
        return None
    title = f"4. Priemerný mesačný objem konkurentov ({granularity_label_for_display} - Skladaný stĺpcový)"
    unique_periods = sorted(df_avg_keywords[period_col].unique(), key=get_period_sort_key_func(granularity_str_for_sort))
    fig = px.bar(df_avg_keywords, x=period_col, y='Average Search Volume', color='Keyword',
                 labels={'Average Search Volume': 'Priem. mesačný objem', 'Keyword': 'Značka', period_col: granularity_label_for_display}, 
                 title=title, 
                 category_orders={"Keyword": keyword_order, period_col: unique_periods},
                 barmode='stack')
    fig.update_layout(yaxis_title='Priemerný mesačný objem (AVG) - Skladaný', legend_title_text='Značky', height=700)
    return fig

def create_heatmap_growth_single(heatmap_data, granularity_label_for_display): 
    if heatmap_data.empty: return None
    title = f"5. Medziobdobový rast (%) - {granularity_label_for_display.lower()}" 
    def format_growth(val):
        if pd.isna(val): return '-'
        if val == np.inf: return 'Inf%'
        elif val == -np.inf: return '-Inf%'
        return f"{val:.0f}%"
    text_labels = heatmap_data.applymap(format_growth).values
    color_min = -100; color_max = 200; color_mid = 0
    fig = px.imshow(heatmap_data, labels=dict(x=granularity_label_for_display, y="Značka", color="Rast (%)"), title=title, text_auto=False, aspect="auto", color_continuous_scale='RdYlGn', color_continuous_midpoint=color_mid, range_color=[color_min, color_max])
    fig.update_traces(text=text_labels, texttemplate="%{text}", hovertemplate="<b>%{y}</b><br>%{x}<br>Rast: %{z:.0f}%<extra></extra>"); fig.update_xaxes(side="bottom")
    fig.update_layout(height=max(450, len(heatmap_data.index) * 40 if len(heatmap_data.index) > 0 else 450))
    return fig

# --- Grafy pre Analýzu viacerých krajín ---
def create_mc_total_sos_chart(df_total_sos_mc, period_col, granularity_str_for_sort, granularity_label_for_display, keyword_order):
    if df_total_sos_mc.empty or 'Total Market Volume' not in df_total_sos_mc.columns or df_total_sos_mc['Total Market Volume'].sum(skipna=True) <= 0: 
        return None
    title = f"1. Celkový SoS (Podiel % naprieč všetkými vybranými krajinami)"
    unique_periods = sorted(df_total_sos_mc[period_col].unique(), key=get_period_sort_key_func(granularity_str_for_sort))
    df_plot = df_total_sos_mc[df_total_sos_mc['Total Market Volume'] > 0].copy()
    if df_plot.empty: return None
    fig = px.bar(df_plot, x=period_col, y='Share_Percent', color='Keyword', text='Share_Percent', barmode='stack', labels={'Share_Percent': '% Podiel (všetky krajiny)', 'Keyword': 'Značka', period_col: granularity_label_for_display}, title=title, category_orders={"Keyword": keyword_order, period_col: unique_periods})
    fig.update_layout(yaxis_title='% celkového objemu (všetky krajiny)', yaxis_ticksuffix="%", xaxis_type='category', legend_title_text='Značky', height=600)
    fig.update_traces(texttemplate='%{text:.1f}%', textposition='inside', insidetextanchor='middle', textfont_size=12)
    return fig

def create_mc_total_avg_volume_chart(df_total_avg_vol_mc, period_col, granularity_str_for_sort, granularity_label_for_display, keyword_order):
    if df_total_avg_vol_mc.empty or 'Average Search Volume' not in df_total_avg_vol_mc.columns or df_total_avg_vol_mc['Average Search Volume'].sum(skipna=True) <= 0: 
        return None
    title = f"2. Celkový priemerný objem naprieč všetkými vybranými krajinami"
    unique_periods = sorted(df_total_avg_vol_mc[period_col].unique(), key=get_period_sort_key_func(granularity_str_for_sort))
    fig = px.line(df_total_avg_vol_mc, x=period_col, y='Average Search Volume', color='Keyword', labels={'Average Search Volume': 'Priemerný objem', 'Keyword': 'Značka', period_col: granularity_label_for_display}, title=title, markers=True, category_orders={"Keyword": keyword_order, period_col: unique_periods})
    fig.update_layout(yaxis_title='Priemerný objem vyhľadávania', legend_title_text='Značky', height=600)
    return fig

def create_mc_flexible_avg_volume_chart(df_flex_avg_vol, period_col, granularity_str_for_sort, granularity_label_for_display, keyword_order, selected_countries_str):
    """Graf 3 (Multi-Country): Flexibilný PRIEMERNÝ objem pre vybrané ZNAČKY (Čiarový)."""
    if df_flex_avg_vol.empty or 'Average Search Volume' not in df_flex_avg_vol.columns or df_flex_avg_vol['Average Search Volume'].sum(skipna=True) <=0: 
        return None
    title = f"3. Priemerný objem pre vybrané ZNAČKY (krajiny sčítané: {selected_countries_str}) - Čiarový" # Upravený titulok pre jasnosť
    unique_periods = sorted(df_flex_avg_vol[period_col].unique(), key=get_period_sort_key_func(granularity_str_for_sort))
    fig = px.line(df_flex_avg_vol, x=period_col, y='Average Search Volume', color='Keyword', # Color by Keyword (Značka)
                  labels={'Average Search Volume': 'Priemerný objem', 'Keyword': 'Značka', period_col: granularity_label_for_display},
                  title=title, markers=True, 
                  category_orders={"Keyword": keyword_order, period_col: unique_periods})
    fig.update_layout(yaxis_title='Priemerný objem vyhľadávania', legend_title_text='Značky', height=600)
    return fig

def create_mc_flexible_avg_volume_stacked_bar_chart(df_flex_avg_vol, period_col, granularity_str_for_sort, granularity_label_for_display, keyword_order, selected_countries_str):
    """Graf 4 (Multi-Country): Flexibilný PRIEMERNÝ objem pre vybrané ZNAČKY (Skladaný stĺpcový)."""
    if df_flex_avg_vol.empty or 'Average Search Volume' not in df_flex_avg_vol.columns or df_flex_avg_vol['Average Search Volume'].sum(skipna=True) <=0: 
        return None
    title = f"4. Priemerný objem pre vybrané ZNAČKY (krajiny sčítané: {selected_countries_str}) - Skladaný stĺpcový" # Upravený titulok pre jasnosť
    unique_periods = sorted(df_flex_avg_vol[period_col].unique(), key=get_period_sort_key_func(granularity_str_for_sort))
    fig = px.bar(df_flex_avg_vol, x=period_col, y='Average Search Volume', color='Keyword', # Color by Keyword (Značka)
                  labels={'Average Search Volume': 'Priemerný objem', 'Keyword': 'Značka', period_col: granularity_label_for_display},
                  title=title, 
                  category_orders={"Keyword": keyword_order, period_col: unique_periods},
                  barmode='stack')
    fig.update_layout(yaxis_title='Priemerný objem vyhľadávania (Skladaný)', legend_title_text='Značky', height=700)
    return fig

# --- NOVÉ FUNKCIE PRE GRAFY 5 A 6 (Flexibilný priemerný objem podľa KRAJÍN) ---
def create_mc_flexible_avg_volume_by_country_line_chart(df_flex_avg_vol_by_country, period_col, granularity_str_for_sort, granularity_label_for_display, country_order, selected_brands_str, title_prefix="5."):
    """Graf 5 (Multi-Country): Flexibilný PRIEMERNÝ objem podľa KRAJÍN (Čiarový)."""
    if df_flex_avg_vol_by_country.empty or 'Average Search Volume' not in df_flex_avg_vol_by_country.columns or df_flex_avg_vol_by_country['Average Search Volume'].sum(skipna=True) <=0: 
        return None
    # Stĺpec s krajinami by mal byť 'Country' na základe transform_flexible_avg_volume_by_country_display
    if 'Country' not in df_flex_avg_vol_by_country.columns:
        # Fallback alebo logovanie chyby, ak stĺpec chýba
        print("Chyba: Stĺpec 'Country' chýba v dátach pre graf create_mc_flexible_avg_volume_by_country_line_chart.")
        return None
        
    title = f"{title_prefix} Priemerný objem podľa KRAJÍN (značky sčítané: {selected_brands_str}) - Čiarový"
    unique_periods = sorted(df_flex_avg_vol_by_country[period_col].unique(), key=get_period_sort_key_func(granularity_str_for_sort))
    
    fig = px.line(df_flex_avg_vol_by_country, x=period_col, y='Average Search Volume', color='Country', # ZMENA: color='Country'
                  labels={'Average Search Volume': 'Priemerný objem', 'Country': 'Krajina', period_col: granularity_label_for_display},
                  title=title, markers=True, 
                  category_orders={"Country": country_order, period_col: unique_periods}) 
    fig.update_layout(yaxis_title='Priemerný objem vyhľadávania', legend_title_text='Krajiny', height=600) 
    return fig

def create_mc_flexible_avg_volume_by_country_stacked_bar_chart(df_flex_avg_vol_by_country, period_col, granularity_str_for_sort, granularity_label_for_display, country_order, selected_brands_str, title_prefix="6."):
    """Graf 6 (Multi-Country): Flexibilný PRIEMERNÝ objem podľa KRAJÍN (Skladaný stĺpcový)."""
    if df_flex_avg_vol_by_country.empty or 'Average Search Volume' not in df_flex_avg_vol_by_country.columns or df_flex_avg_vol_by_country['Average Search Volume'].sum(skipna=True) <=0: 
        return None
    if 'Country' not in df_flex_avg_vol_by_country.columns:
        print("Chyba: Stĺpec 'Country' chýba v dátach pre graf create_mc_flexible_avg_volume_by_country_stacked_bar_chart.")
        return None

    title = f"{title_prefix} Priemerný objem podľa KRAJÍN (značky sčítané: {selected_brands_str}) - Skladaný stĺpcový" 
    unique_periods = sorted(df_flex_avg_vol_by_country[period_col].unique(), key=get_period_sort_key_func(granularity_str_for_sort))
    
    fig = px.bar(df_flex_avg_vol_by_country, x=period_col, y='Average Search Volume', color='Country', # ZMENA: color='Country'
                  labels={'Average Search Volume': 'Priemerný objem', 'Country': 'Krajina', period_col: granularity_label_for_display},
                  title=title, 
                  category_orders={"Country": country_order, period_col: unique_periods},
                  barmode='stack')
    fig.update_layout(yaxis_title='Priemerný objem vyhľadávania (Skladaný)', legend_title_text='Krajiny', height=700)
    return fig


# --- Graf pre pôvodný graf č. 5 (teraz č. 7) ---
def create_mc_segment_avg_volume_custom_countries_chart(df_segment_avg_vol, period_col, granularity_str_for_sort, granularity_label_for_display, selected_countries_str):
    """Graf 7 (Multi-Country, pôvodne 5): Priemerný mesačný objem segmentu pre VLASTNÝ VÝBER KRAJÍN."""
    if df_segment_avg_vol.empty or 'AvgMonthlySegmentVolume' not in df_segment_avg_vol.columns or df_segment_avg_vol['AvgMonthlySegmentVolume'].sum(skipna=True) <= 0: 
        return None
    # Titulok sa nastavuje v multi_country_page.py, tu môže byť generický alebo ho odstrániť
    # title = f"7. Priemerný mesačný objem segmentu (krajiny: {selected_countries_str})" # Číslo sa môže meniť, lepšie nastavovať v UI
    unique_periods = sorted(df_segment_avg_vol[period_col].unique(), key=get_period_sort_key_func(granularity_str_for_sort))
    fig = px.bar(df_segment_avg_vol, x=period_col, y='AvgMonthlySegmentVolume', 
                 labels={'AvgMonthlySegmentVolume': 'Priem. mesačný objem segmentu', period_col: granularity_label_for_display}, 
                 # title=title, # Odstránený fixný titulok, bude nastavený dynamicky v UI
                 category_orders={period_col: unique_periods})
    fig.update_layout(yaxis_title='Priemerný mesačný objem vyhľadávania', height=500)
    fig.update_traces(texttemplate='%{y:,.0f}', textposition='outside')
    return fig