import pandas as pd
import numpy as np

def get_period_sort_key_func(granularity_str_for_sort):
    """
    Vráti funkciu pre triedenie periód na základe granularity.
    Očakáva granularity_str_for_sort ako 'Ročne', 'Štvrťročne', alebo 'Mesačne'.
    """
    if granularity_str_for_sort == 'Ročne':
        return lambda x: pd.to_numeric(x)
    elif granularity_str_for_sort == 'Štvrťročne':
        return lambda x: pd.Period(x, freq='Q')
    elif granularity_str_for_sort == 'Mesačne': 
        return lambda x: pd.to_datetime(x, format='%Y-%m')
    else: 
        return lambda x: str(x)

def add_period_column(df, granularity_str, date_col='Date', period_col_name='Period'):
    """Pridá do DataFrame stĺpec s periódou na základe granularity."""
    df_agg = df.copy()
    df_agg[date_col] = pd.to_datetime(df_agg[date_col]) 
    if granularity_str == 'Ročne':
        df_agg[period_col_name] = df_agg[date_col].dt.year.astype(str)
    elif granularity_str == 'Štvrťročne':
        df_agg[period_col_name] = df_agg[date_col].dt.to_period('Q').astype(str)
    else:  # Mesačne
        df_agg[period_col_name] = df_agg[date_col].dt.strftime('%Y-%m')
    return df_agg

def calculate_sos_data(df_aggregated_by_period_keyword, period_col='Period', keyword_col='Keyword', volume_col='Search Volume'):
    """
    Vypočíta Share of Search.
    Očakáva DataFrame, kde volume_col je už agregovaný pre daný keyword a periódu.
    Vráti DataFrame so stĺpcami: period_col, keyword_col, volume_col, 'Total Market Volume', 'Share_Percent'.
    """
    result_cols = [period_col, keyword_col, volume_col, 'Total Market Volume', 'Share_Percent']
    empty_sos_df = pd.DataFrame(columns=result_cols)

    if df_aggregated_by_period_keyword.empty: return empty_sos_df
    if volume_col not in df_aggregated_by_period_keyword.columns: return empty_sos_df
    
    current_volume_sum = pd.to_numeric(df_aggregated_by_period_keyword[volume_col], errors='coerce').sum(skipna=True)
    if pd.isna(current_volume_sum) or current_volume_sum <= 0 :
        merged_df = df_aggregated_by_period_keyword.copy()
        merged_df['Total Market Volume'] = 0
        merged_df['Share_Percent'] = 0.0
        for col_name in result_cols:
            if col_name not in merged_df:
                merged_df[col_name] = merged_df.get(period_col) if col_name == period_col else \
                                      merged_df.get(keyword_col) if col_name == keyword_col else \
                                      pd.to_numeric(merged_df.get(volume_col), errors='coerce').fillna(0) if col_name == volume_col else 0
        return merged_df[result_cols]

    total_volume_per_period = df_aggregated_by_period_keyword.groupby(period_col, observed=False)[volume_col].sum().reset_index().rename(columns={volume_col: 'Total Market Volume'})
    
    if total_volume_per_period.empty or total_volume_per_period['Total Market Volume'].sum(skipna=True) <= 0:
        merged_df = df_aggregated_by_period_keyword.copy()
        merged_df['Total Market Volume'] = 0
        merged_df['Share_Percent'] = 0.0
        for col_name in result_cols:
            if col_name not in merged_df:
                merged_df[col_name] = merged_df.get(period_col) if col_name == period_col else \
                                      merged_df.get(keyword_col) if col_name == keyword_col else \
                                      pd.to_numeric(merged_df.get(volume_col), errors='coerce').fillna(0) if col_name == volume_col else 0
        return merged_df[result_cols]

    merged_df = pd.merge(df_aggregated_by_period_keyword, total_volume_per_period, on=period_col, how="left")
    merged_df['Total Market Volume'].fillna(0, inplace=True)
    merged_df[volume_col] = pd.to_numeric(merged_df[volume_col], errors='coerce').fillna(0)
    
    merged_df['Share_Percent'] = 0.0
    mask = merged_df['Total Market Volume'] > 0
    merged_df.loc[mask, 'Share_Percent'] = (merged_df[volume_col] / merged_df['Total Market Volume']) * 100
    merged_df.fillna({'Share_Percent': 0}, inplace=True) 
            
    return merged_df[result_cols]

def calculate_average_monthly_segment_volume(df_raw_data, granularity_str, period_col='Period', date_col='Date', volume_col='Search Volume'):
    if df_raw_data.empty: return pd.DataFrame(columns=[period_col, 'Average Total Volume'])
    df_raw_data[date_col] = pd.to_datetime(df_raw_data[date_col])
    df_with_period = add_period_column(df_raw_data.copy(), granularity_str, date_col, period_col)
    if df_with_period.empty: return pd.DataFrame(columns=[period_col, 'Average Total Volume'])
    total_volume_per_period = df_with_period.groupby(period_col, observed=False)[volume_col].sum().reset_index().rename(columns={volume_col: 'TotalPeriodicVolume'})
    if total_volume_per_period.empty: return pd.DataFrame(columns=[period_col, 'Average Total Volume'])
    df_with_period['MonthYear'] = df_with_period[date_col].dt.to_period('M')
    months_in_period = df_with_period.groupby(period_col, observed=False)['MonthYear'].nunique().reset_index(name='NumMonths')
    if months_in_period.empty:
        if not total_volume_per_period.empty: months_in_period = pd.DataFrame({period_col: total_volume_per_period[period_col].unique(), 'NumMonths': 1})
        else: return pd.DataFrame(columns=[period_col, 'Average Total Volume'])
    avg_data = pd.merge(total_volume_per_period, months_in_period, on=period_col, how="left")
    avg_data['NumMonths'] = avg_data['NumMonths'].fillna(1).replace(0, 1).astype(int)
    avg_data['Average Total Volume'] = avg_data.apply(lambda row: row['TotalPeriodicVolume'] / row['NumMonths'] if row['NumMonths'] > 0 else 0, axis=1)
    return avg_data[[period_col, 'Average Total Volume']]

def calculate_average_monthly_keyword_volume(df_raw_data, granularity_str, period_col='Period', keyword_col='Keyword', date_col='Date', volume_col='Search Volume'):
    """
    Vypočíta priemerný mesačný objem pre každé kľúčové slovo (alebo inú entitu v keyword_col) za danú periódu.
    Krok 1: Sčíta objemy pre každý keyword/entitu za každý mesiac (ak sú v df_raw_data duplicity alebo sub-mesačné dáta).
    Krok 2: Pridá periódu (Ročne, Štvrťročne, Mesačne) na základe granularity.
    Krok 3: Vypočíta priemer týchto mesačných súčtov v rámci každej periódy pre každý keyword/entitu.
    """
    if df_raw_data.empty: return pd.DataFrame(columns=[period_col, keyword_col, 'Average Search Volume'])
    
    df_copy = df_raw_data.copy()
    df_copy[date_col] = pd.to_datetime(df_copy[date_col])
    
    # Krok 1: Agregácia na mesačnej úrovni pre každý keyword/entitu
    # Ak df_raw_data už obsahuje mesačné sumy pre každý keyword, tento krok je len poistka.
    # Ak keyword_col reprezentuje 'Country' a df_raw_data sú už mesačné sumy značiek pre krajinu, tak tento groupby je správny.
    monthly_sums_per_entity = df_copy.groupby(
        [pd.Grouper(key=date_col, freq='MS'), keyword_col], observed=False
    )[volume_col].sum().reset_index()
    
    if monthly_sums_per_entity.empty: 
        return pd.DataFrame(columns=[period_col, keyword_col, 'Average Search Volume'])
        
    # Krok 2: Pridanie periódy
    df_with_period = add_period_column(monthly_sums_per_entity, granularity_str, date_col, period_col)
    if df_with_period.empty: 
        return pd.DataFrame(columns=[period_col, keyword_col, 'Average Search Volume'])
        
    # Krok 3: Výpočet priemeru mesačných súčtov v rámci periódy pre každý keyword/entitu
    avg_keyword_volume = df_with_period.groupby(
        [period_col, keyword_col], observed=False
    )[volume_col].mean().reset_index() # volume_col tu už obsahuje mesačné sumy
    
    avg_keyword_volume.rename(columns={volume_col: 'Average Search Volume'}, inplace=True)
    return avg_keyword_volume

def calculate_growth_data(period_volume_sum_df, period_col, sort_key_func, keyword_col='Keyword', volume_col='Search Volume'):
    if period_volume_sum_df.empty or len(period_volume_sum_df[period_col].unique()) <= 1: return pd.DataFrame() 
    growth_df = period_volume_sum_df.copy()
    if sort_key_func:
        try:
            growth_df['SortKey'] = growth_df[period_col].apply(sort_key_func)
            growth_df = growth_df.sort_values(by=['SortKey', keyword_col]).drop(columns=['SortKey'])
        except Exception: growth_df = growth_df.sort_values(by=[period_col, keyword_col])
    else: growth_df = growth_df.sort_values(by=[period_col, keyword_col])
    growth_df['Prev Volume'] = growth_df.groupby(keyword_col)[volume_col].shift(1)
    growth_df['Period Growth (%)'] = np.nan
    mask_growth = (growth_df['Prev Volume'] > 0) & (pd.notna(growth_df['Prev Volume']))
    growth_df.loc[mask_growth, 'Period Growth (%)'] = ((growth_df[volume_col] - growth_df['Prev Volume']) / growth_df['Prev Volume']) * 100
    mask_inf = (growth_df['Prev Volume'] == 0) & (growth_df[volume_col] > 0) & (pd.notna(growth_df['Prev Volume']))
    growth_df.loc[mask_inf, 'Period Growth (%)'] = np.inf
    heatmap_pivot = growth_df.pivot(index=keyword_col, columns=period_col, values='Period Growth (%)')
    return heatmap_pivot

def transform_total_sos_across_countries(mc_df_aggregated_by_period_keyword, period_col='Period', keyword_col='Keyword', volume_col='Search Volume'):
    return calculate_sos_data(mc_df_aggregated_by_period_keyword, period_col, keyword_col, volume_col)

def transform_total_average_volume_across_countries(mc_df_raw_data, granularity_str, period_col='Period', keyword_col='Keyword', date_col='Date', volume_col='Search Volume'):
    if mc_df_raw_data.empty: return pd.DataFrame(columns=[period_col, keyword_col, 'Average Search Volume'])
    mc_df_raw_data[date_col] = pd.to_datetime(mc_df_raw_data[date_col])
    # Sčítame objemy všetkých krajín pre každé kľúčové slovo a mesiac
    monthly_sums_across_countries = mc_df_raw_data.groupby(
        [pd.Grouper(key=date_col, freq='MS'), keyword_col], observed=False
    )[volume_col].sum().reset_index()
    
    if monthly_sums_across_countries.empty: 
        return pd.DataFrame(columns=[period_col, keyword_col, 'Average Search Volume'])
        
    return calculate_average_monthly_keyword_volume(
        monthly_sums_across_countries, 
        granularity_str, 
        period_col, 
        keyword_col, 
        date_col, 
        volume_col
    )

def transform_flexible_sos(mc_df_aggregated_data_with_period_country, selected_keywords, selected_countries, period_col='Period', keyword_col='Keyword', country_col='Country', volume_col='Search Volume'):
    result_cols = [period_col, keyword_col, volume_col, 'Total Market Volume', 'Share_Percent']
    empty_flex_sos_df = pd.DataFrame(columns=result_cols)
    if mc_df_aggregated_data_with_period_country.empty or not selected_keywords or not selected_countries: return empty_flex_sos_df
    
    filtered_df = mc_df_aggregated_data_with_period_country[
        mc_df_aggregated_data_with_period_country[keyword_col].isin(selected_keywords) &
        mc_df_aggregated_data_with_period_country[country_col].isin(selected_countries)
    ].copy()
    if filtered_df.empty: return empty_flex_sos_df
    
    # Sčítame objemy pre každú značku naprieč vybranými krajinami
    brand_volumes_summed_countries = filtered_df.groupby(
        [period_col, keyword_col], observed=False
    )[volume_col].sum().reset_index()
    
    if brand_volumes_summed_countries.empty: return empty_flex_sos_df
    return calculate_sos_data(brand_volumes_summed_countries, period_col, keyword_col, volume_col)

def transform_flexible_avg_volume(mc_df_raw_data, selected_keywords, selected_countries, granularity_str, period_col='Period', keyword_col='Keyword', country_col='Country', date_col='Date', volume_col='Search Volume'):
    """Pre Grafy 3 a 4 (Multi-Country): Flexibilný PRIEMERNÝ objem pre vybrané značky (dáta sčítané cez vybrané krajiny, potom spriemerované pre každú značku)."""
    if mc_df_raw_data.empty or not selected_keywords or not selected_countries:
        return pd.DataFrame(columns=[period_col, keyword_col, 'Average Search Volume'])

    # 1. Filter podľa vybraných značiek (ktoré sa majú zobraziť) a krajín (ktorých dáta sa sčítajú)
    filtered_df_raw = mc_df_raw_data[
        mc_df_raw_data[keyword_col].isin(selected_keywords) &
        mc_df_raw_data[country_col].isin(selected_countries)
    ].copy()
    if filtered_df_raw.empty:
        return pd.DataFrame(columns=[period_col, keyword_col, 'Average Search Volume'])

    filtered_df_raw[date_col] = pd.to_datetime(filtered_df_raw[date_col])
    
    # 2. Sčítanie objemov vyhľadávania pre každú ZNAČKU naprieč vybranými KRAJINAMI za každý mesiac
    monthly_sums_selected_countries_keywords = filtered_df_raw.groupby(
        [pd.Grouper(key=date_col, freq='MS'), keyword_col], observed=False # keyword_col je tu značka
    )[volume_col].sum().reset_index()
    
    if monthly_sums_selected_countries_keywords.empty:
        return pd.DataFrame(columns=[period_col, keyword_col, 'Average Search Volume'])
        
    # 3. Výpočet priemerného objemu pre každú ZNAČKU podľa granularity
    return calculate_average_monthly_keyword_volume(
        monthly_sums_selected_countries_keywords, 
        granularity_str,
        period_col,
        keyword_col, # Toto je Značka
        date_col, 
        volume_col  
    )

def transform_segment_average_volume_custom_countries(mc_df_raw_data, selected_countries, granularity_str, period_col='Period', country_col='Country', date_col='Date', volume_col='Search Volume'):
    if mc_df_raw_data.empty or not selected_countries: return pd.DataFrame(columns=[period_col, 'AvgMonthlySegmentVolume'])
    
    # Filter podľa vybraných krajín
    df_filtered_raw_selected_countries = mc_df_raw_data[
        mc_df_raw_data[country_col].isin(selected_countries)
    ].copy()
    if df_filtered_raw_selected_countries.empty: return pd.DataFrame(columns=[period_col, 'AvgMonthlySegmentVolume'])
    
    df_filtered_raw_selected_countries[date_col] = pd.to_datetime(df_filtered_raw_selected_countries[date_col])
    
    # Sčítanie objemov VŠETKÝCH ZNAČIEK naprieč vybranými KRAJINAMI za každý mesiac
    monthly_segment_data = df_filtered_raw_selected_countries.groupby(
        pd.Grouper(key=date_col, freq='MS') # Agregujeme len podľa dátumu, sčítame všetky značky a krajiny dokopy
    )[volume_col].sum().reset_index()
    
    if monthly_segment_data.empty: return pd.DataFrame(columns=[period_col, 'AvgMonthlySegmentVolume'])
    
    # Výpočet priemerného mesačného objemu pre celý segment (všetky značky, vybrané krajiny)
    avg_segment_volume_df = calculate_average_monthly_segment_volume(
        monthly_segment_data, # Tu už je celkový mesačný objem segmentu
        granularity_str, 
        period_col, 
        date_col, 
        volume_col
    )
    return avg_segment_volume_df.rename(columns={'Average Total Volume': 'AvgMonthlySegmentVolume'})


# NOVÁ TRANSFORMAČNÁ FUNKCIA PRE GRAFY 5 A 6
def transform_flexible_avg_volume_by_country_display(mc_df_raw_data, selected_keywords_to_aggregate, selected_countries_to_display, granularity_str, period_col='Period', keyword_col='Keyword', country_col='Country', date_col='Date', volume_col='Search Volume'):
    """
    Pripraví dáta pre flexibilný priemerný objem, kde sú KRAJINY zobrazené ako samostatné série (Grafy 5 a 6).
    Objemy pre vybrané značky (selected_keywords_to_aggregate) sa sčítajú v rámci každej krajiny (selected_countries_to_display).
    Následne sa vypočíta priemerný objem pre každú KRAJINU podľa granularity.
    """
    if mc_df_raw_data.empty or not selected_keywords_to_aggregate or not selected_countries_to_display:
        # Výstupný DataFrame bude mať stĺpec 'Country' namiesto 'Keyword' ako hlavnú entitu
        return pd.DataFrame(columns=[period_col, country_col, 'Average Search Volume'])

    # 1. Filter podľa vybraných značiek, ktorých dáta sa majú sčítať
    df_filtered_by_keywords = mc_df_raw_data[
        mc_df_raw_data[keyword_col].isin(selected_keywords_to_aggregate)
    ].copy()
    if df_filtered_by_keywords.empty:
        return pd.DataFrame(columns=[period_col, country_col, 'Average Search Volume'])

    # 2. Filter podľa vybraných krajín, ktoré sa majú zobraziť ako série
    df_filtered_by_countries_to_display = df_filtered_by_keywords[
        df_filtered_by_keywords[country_col].isin(selected_countries_to_display)
    ].copy()
    if df_filtered_by_countries_to_display.empty:
        return pd.DataFrame(columns=[period_col, country_col, 'Average Search Volume'])

    df_filtered_by_countries_to_display[date_col] = pd.to_datetime(df_filtered_by_countries_to_display[date_col])

    # 3. Sčítanie objemov vyhľadávania pre VYBRANÉ ZNAČKY v rámci každej ZOBRAZOVANEJ KRAJINY za každý mesiac
    # Výsledkom bude mesačný objem pre kombináciu (všetky vybrané značky spolu) v každej zobrazovanej krajine.
    monthly_sums_for_selected_brands_per_country = df_filtered_by_countries_to_display.groupby(
        [pd.Grouper(key=date_col, freq='MS'), country_col], # country_col je entita, ktorú chceme zobraziť
        observed=False
    )[volume_col].sum().reset_index()

    if monthly_sums_for_selected_brands_per_country.empty:
        return pd.DataFrame(columns=[period_col, country_col, 'Average Search Volume'])
        
    # 4. Výpočet priemerného objemu pre každú KRAJINU podľa granularity
    # Použijeme existujúcu logiku calculate_average_monthly_keyword_volume.
    # Stĺpec 'Country' v `monthly_sums_for_selected_brands_per_country` teraz funguje ako `keyword_col` pre túto funkciu.
    avg_volume_df_by_country = calculate_average_monthly_keyword_volume(
        df_raw_data=monthly_sums_for_selected_brands_per_country, # Toto sú už mesačné sumy agregovaných značiek pre každú krajinu
        granularity_str=granularity_str,
        period_col=period_col,
        keyword_col=country_col, # Hovoríme funkcii, že stĺpec 'Country' je teraz entitou, pre ktorú sa počíta priemer
        date_col=date_col, 
        volume_col=volume_col  
    )
    
    # Funkcia calculate_average_monthly_keyword_volume premenuje keyword_col na 'Average Search Volume'
    # a ponechá pôvodný keyword_col (v našom prípade country_col).
    # Výstupný DataFrame by mal mať stĺpce: period_col, country_col, 'Average Search Volume'
    return avg_volume_df_by_country