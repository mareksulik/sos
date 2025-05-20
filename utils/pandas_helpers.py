"""
Utility modul pre Share of Search Tool.
Obsahuje pomocné funkcie pre prácu s Pandas a ošetrenie chýb.
"""
from typing import Optional, Callable, Any, List, Dict, Tuple, Union
import pandas as pd
import logging
import traceback
import functools
import time

logger = logging.getLogger(__name__)

def safe_pandas_operation(default_return: Any = None) -> Callable:
    """Dekorátor pre bezpečné vykonanie operácií s Pandas.
    
    Args:
        default_return: Hodnota, ktorá sa vráti v prípade chyby
        
    Returns:
        Callable: Dekorovaná funkcia
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Chyba pri pandas operácii {func.__name__}: {e}")
                logger.debug(traceback.format_exc())
                return default_return
        return wrapper
    return decorator

def format_dataframe_for_display(df: pd.DataFrame, precision: int = 2) -> pd.DataFrame:
    """Formátuje DataFrame pre zobrazenie - zaokrúhľuje čísla a formátuje dátumy.
    
    Args:
        df: DataFrame na formátovanie
        precision: Počet desatinných miest pre zaokrúhlenie
        
    Returns:
        pd.DataFrame: Formátovaný DataFrame
    """
    if df.empty:
        return df
        
    formatted_df = df.copy()
    
    # Zaokrúhlenie číselných stĺpcov
    numeric_columns = df.select_dtypes(include=['float', 'int']).columns
    for col in numeric_columns:
        formatted_df[col] = formatted_df[col].round(precision)
    
    # Formátovanie dátumových stĺpcov
    date_columns = df.select_dtypes(include=['datetime']).columns
    for col in date_columns:
        formatted_df[col] = formatted_df[col].dt.strftime('%Y-%m-%d')
        
    return formatted_df

def measure_execution_time(func: Callable) -> Callable:
    """Dekorátor pre meranie času vykonávania funkcie.
    
    Args:
        func: Funkcia, ktorej čas sa má merať
        
    Returns:
        Callable: Dekorovaná funkcia
    """
    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        logger.debug(f"Funkcia {func.__name__} trvala {end_time - start_time:.4f} sekúnd")
        return result
    return wrapper
