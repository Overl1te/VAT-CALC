from datetime import datetime

def project_costs_vectorized(data, current_vat, future_vat, years=5):
    """Оптимизированная версия без pandas"""
    current_year = datetime.now().year
    expanded_rows = []
    
    for row in data:
        if isinstance(row, dict):
            name = row.get('Название') or row.get('Name') or ''
            base_cost = float(row.get('Базовая стоимость') or row.get('Base') or 0)
            start_year = int(row.get('Год начала') or row.get('StartYear') or current_year)
        else:
            name = str(row[0]) if len(row) > 0 else ''
            base_cost = float(row[1]) if len(row) > 1 else 0.0
            start_year = int(row[2]) if len(row) > 2 else current_year
        
        for offset in range(years):
            year = start_year + offset
            vat_rate = current_vat if year < current_year else future_vat
            cost_with_vat = base_cost * (1 + vat_rate / 100.0)
            
            expanded_rows.append({
                'Название': name,
                'Базовая стоимость': round(base_cost, 2),
                'Год': year,
                'Ставка НДС': vat_rate,
                'Стоимость_с_НДС': round(cost_with_vat, 2)
            })
    
    return expanded_rows

def calculate_contracts_simple(data_rows, current_vat, future_vat, years=5):
    """Простая версия для работы со списками из Excel"""
    current_year = datetime.now().year
    results = []
    
    for row in data_rows:
        if len(row) >= 3:
            name = str(row[0])
            try:
                base_cost = float(row[1])
                start_year = int(row[2])
            except (ValueError, TypeError):
                continue
            
            for year_offset in range(years):
                year = start_year + year_offset
                vat_rate = current_vat if year < current_year else future_vat
                total_cost = base_cost * (1 + vat_rate / 100.0)
                
                results.append([
                    name,
                    round(base_cost, 2),
                    year,
                    vat_rate,
                    round(total_cost, 2)
                ])
    
    return results