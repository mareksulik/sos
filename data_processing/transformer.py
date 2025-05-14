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
    if df_raw_data.empty: return pd.DataFrame(columns=[period_col, keyword_col, 'Average Search Volume'])
    df_raw_data[date_col] = pd.to_datetime(df_raw_data[date_col])
    monthly_sums_per_keyword = df_raw_data.groupby([pd.Grouper(key=date_col, freq='MS'), keyword_col], observed=False)[volume_col].sum().reset_index()
    if monthly_sums_per_keyword.empty: return pd.DataFrame(columns=[period_col, keyword_col, 'Average Search Volume'])
    df_with_period = add_period_column(monthly_sums_per_keyword, granularity_str, date_col, period_col)
    if df_with_period.empty: return pd.DataFrame(columns=[period_col, keyword_col, 'Average Search Volume'])
    avg_keyword_volume = df_with_period.groupby([period_col, keyword_col], observed=False)[volume_col].mean().reset_index()
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
    monthly_sums_across_countries = mc_df_raw_data.groupby([pd.Grouper(key=date_col, freq='MS'), keyword_col], observed=False)[volume_col].sum().reset_index()
    if monthly_sums_across_countries.empty: return pd.DataFrame(columns=[period_col, keyword_col, 'Average Search Volume'])
    return calculate_average_monthly_keyword_volume(monthly_sums_across_countries, granularity_str, period_col, keyword_col, date_col, volume_col)

def transform_flexible_sos(mc_df_aggregated_data_with_period_country, selected_keywords, selected_countries, period_col='Period', keyword_col='Keyword', country_col='Country', volume_col='Search Volume'):
    result_cols = [period_col, keyword_col, volume_col, 'Total Market Volume', 'Share_Percent']
    empty_flex_sos_df = pd.DataFrame(columns=result_cols)
    if mc_df_aggregated_data_with_period_country.empty or not selected_keywords or not selected_countries: return empty_flex_sos_df
    filtered_df = mc_df_aggregated_data_with_period_country[
        mc_df_aggregated_data_with_period_country[keyword_col].isin(selected_keywords) &
        mc_df_aggregated_data_with_period_country[country_col].isin(selected_countries)
    ].copy()
    if filtered_df.empty: return empty_flex_sos_df
    brand_volumes_summed_countries = filtered_df.groupby([period_col, keyword_col], observed=False)[volume_col].sum().reset_index()
    if brand_volumes_summed_countries.empty: return empty_flex_sos_df
    return calculate_sos_data(brand_volumes_summed_countries, period_col, keyword_col, volume_col)

def transform_flexible_avg_volume(mc_df_raw_data, selected_keywords, selected_countries, granularity_str, period_col='Period', keyword_col='Keyword', country_col='Country', date_col='Date', volume_col='Search Volume'):
    """Pre Graf 4 (Multi-Country): Flexibilný PRIEMERNÝ objem pre vybrané značky (dáta sčítané cez vybrané krajiny, potom spriemerované)."""
    if mc_df_raw_data.empty or not selected_keywords or not selected_countries:
        return pd.DataFrame(columns=[period_col, keyword_col, 'Average Search Volume'])

    filtered_df_raw = mc_df_raw_data[
        mc_df_raw_data[keyword_col].isin(selected_keywords) &
        mc_df_raw_data[country_col].isin(selected_countries)
    ].copy()
    if filtered_df_raw.empty:
        return pd.DataFrame(columns=[period_col, keyword_col, 'Average Search Volume'])

    filtered_df_raw[date_col] = pd.to_datetime(filtered_df_raw[date_col])
    monthly_sums_selected_countries_keywords = filtered_df_raw.groupby(
        [pd.Grouper(key=date_col, freq='MS'), keyword_col], observed=False
    )[volume_col].sum().reset_index()
    if monthly_sums_selected_countries_keywords.empty:
        return pd.DataFrame(columns=[period_col, keyword_col, 'Average Search Volume'])
        
    return calculate_average_monthly_keyword_volume(
        monthly_sums_selected_countries_keywords, 
        granularity_str,
        period_col,
        keyword_col,
        date_col, 
        volume_col  
    )

def transform_segment_average_volume_custom_countries(mc_df_raw_data, selected_countries, granularity_str, period_col='Period', country_col='Country', date_col='Date', volume_col='Search Volume'):
    if mc_df_raw_data.empty or not selected_countries: return pd.DataFrame(columns=[period_col, 'AvgMonthlySegmentVolume'])
    df_filtered_raw_selected_countries = mc_df_raw_data[mc_df_raw_data[country_col].isin(selected_countries)].copy()
    if df_filtered_raw_selected_countries.empty: return pd.DataFrame(columns=[period_col, 'AvgMonthlySegmentVolume'])
    
    df_filtered_raw_selected_countries[date_col] = pd.to_datetime(df_filtered_raw_selected_countries[date_col])
    monthly_segment_data = df_filtered_raw_selected_countries.groupby(pd.Grouper(key=date_col, freq='MS'))[volume_col].sum().reset_index()
    if monthly_segment_data.empty: return pd.DataFrame(columns=[period_col, 'AvgMonthlySegmentVolume'])
    
    avg_segment_volume_df = calculate_average_monthly_segment_volume(monthly_segment_data, granularity_str, period_col, date_col, volume_col)
    return avg_segment_volume_df.rename(columns={'Average Total Volume': 'AvgMonthlySegmentVolume'})