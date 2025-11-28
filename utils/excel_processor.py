from openpyxl import load_workbook, Workbook

def read_input_excel(path):
    """Чтение Excel файла с помощью OpenPyXL"""
    workbook = load_workbook(filename=path, data_only=True)
    sheet = workbook.active
    
    data = []
    headers = []
    
    for row_idx, row in enumerate(sheet.iter_rows(values_only=True)):
        if row_idx == 0:
            headers = [str(cell).strip() if cell else f"Column_{i+1}" 
                      for i, cell in enumerate(row)]
        else:
            row_data = {}
            for col_idx, cell in enumerate(row):
                if col_idx < len(headers):
                    row_data[headers[col_idx]] = cell
            data.append(row_data)
    
    return data

def read_input_excel_simple(path):
    """Упрощенное чтение - возвращает список списков"""
    workbook = load_workbook(filename=path, data_only=True)
    sheet = workbook.active
    
    data = []
    for row in sheet.iter_rows(values_only=True):
        data.append(list(row))
    
    return data

def write_output_excel(data, path):
    """Запись данных в Excel файл"""
    workbook = Workbook()
    sheet = workbook.active
    
    # Заголовки
    if data and isinstance(data[0], dict):
        headers = list(data[0].keys())
        sheet.append(headers)
        for row in data:
            sheet.append([row.get(header, '') for header in headers])
    else:
        # Просто записываем все строки
        for row in data:
            sheet.append(row)
    
    workbook.save(path)