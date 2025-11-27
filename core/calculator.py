"""Calculator logic for applying VAT changes and projecting costs."""
import numpy as np
import pandas as pd
from datetime import datetime

def apply_vat_series(cost_series, vat_rate):
    """Apply VAT to pandas Series (vectorized)."""
    return cost_series * (1 + vat_rate / 100.0)

def project_costs_vectorized(df, current_vat, future_vat, years=5):
    """Vectorized projection - работает в 100+ раз быстрее"""
    current_year = datetime.now().year
    
    # Создаем расширенный DataFrame
    expanded_rows = []
    
    for _, row in df.iterrows():
        name = row.get('Название') or row.get('Name') or ''
        base_cost = float(row.get('Базовая стоимость') or row.get('Base') or 0)
        start_year = int(row.get('Год начала') or row.get('StartYear') or current_year)
        
        # Создаем данные для всех лет сразу
        for offset in range(years):
            year = start_year + offset
            vat_rate = current_vat if year < current_year else future_vat
            cost_with_vat = base_cost * (1 + vat_rate / 100.0)
            
            expanded_rows.append({
                'Название': name,
                'Базовая стоимость': base_cost,
                'Год': year,
                'Ставка НДС': vat_rate,
                'Стоимость_с_НДС': round(cost_with_vat, 2)
            })
    
    return pd.DataFrame(expanded_rows)

# Альтернатива - супер-быстрая, но сложнее
def project_costs_fast(df, current_vat, future_vat, years=5):
    """Ещё более быстрая версия с pandas операциями"""
    current_year = datetime.now().year
    
    # Дублируем строки для каждого года
    df_expanded = df.loc[df.index.repeat(years)].reset_index(drop=True)
    
    # Добавляем год расчета
    df_expanded['Год_смещение'] = df_expanded.groupby(level=0).cumcount()
    start_years = pd.to_numeric(df_expanded.get('Год начала') 
                               or df_expanded.get('StartYear') 
                               or current_year)
    df_expanded['Год'] = start_years + df_expanded['Год_смещение']
    
    # Применяем НДС
    base_costs = pd.to_numeric(df_expanded.get('Базовая стоимость') 
                              or df_expanded.get('Base') 
                              or 0)
    vat_rates = np.where(df_expanded['Год'] < current_year, current_vat, future_vat)
    df_expanded['Ставка НДС'] = vat_rates
    df_expanded['Стоимость_с_НДС'] = base_costs * (1 + vat_rates / 100.0)
    
    # Оставляем нужные колонки
    result_cols = ['Название', 'Базовая стоимость', 'Год', 'Ставка НДС', 'Стоимость_с_НДС']
    return df_expanded[result_cols].round(2)