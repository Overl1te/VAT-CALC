from openpyxl import load_workbook, Workbook

def read_input_excel(path):
    """
    Упрощенное чтение Excel как список списков.
    
    :param path: Путь к файлу.
    :return: Список строк.
    """
    workbook = load_workbook(filename=path, data_only=True)
    sheet = workbook.active
    return [list(row) for row in sheet.iter_rows(values_only=True)]

def write_output_excel(data, path):
    """
    Записывает данные в Excel.
    
    :param data: Данные для записи.
    :param path: Путь к файлу.
    """
    workbook = Workbook()
    sheet = workbook.active
    if data and isinstance(data[0], dict):
        headers = list(data[0].keys())
        sheet.append(headers)
        for row in data:
            sheet.append([row.get(header, '') for header in headers])
    else:
        for row in data:
            sheet.append(row)
    workbook.save(path)


def write_output_excel_simple(data, path):
    """
    Простой экспорт списка словарей в Excel с современным форматированием.
    """
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    from openpyxl import Workbook
    from datetime import datetime

    wb = Workbook()
    ws = wb.active
    ws.title = "Дополнительный НДС"

    # Заголовки
    headers = ["Название договора", "№ договора", "Сумма договора", "Остаток на 31.12.2025", "Дополнительный НДС"]
    ws.append(headers)

    # Стили - минималистичные
    header_font = Font(bold=True, size=11)
    header_fill = PatternFill(start_color="F5F5F5", end_color="F5F5F5", fill_type="solid")
    total_font = Font(bold=True)
    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")

    # Форматируем заголовки - просто серый фон и жирный шрифт
    for cell in ws[1]:
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = align_center

    total_diff = 0.0
    
    # Проходим по данным и добавляем в Excel
    for row_data in data:
        row_values = []
        is_total_row = row_data["Название договора"] == "ИТОГО"
        
        # Обрабатываем каждое поле
        for key in headers:
            value = row_data[key]
            
            # Если это числовое поле
            if key in ["Сумма договора", "Остаток на 31.12.2025", "Дополнительный НДС"]:
                if value == "" or value is None:
                    # Для итоговой строки - пусто, для договоров - 0
                    row_values.append("" if is_total_row else 0)
                elif isinstance(value, (int, float)):
                    # Для итоговой строки скрываем нули, для договоров показываем
                    if value == 0 and is_total_row:
                        row_values.append("")
                    else:
                        row_values.append(float(value))
                else:
                    try:
                        clean_value = str(value).replace(",", "").replace(" ", "").replace("₽", "").replace(" ", "").strip()
                        if clean_value and clean_value != "":
                            num_value = float(clean_value)
                            # Для итоговой строки скрываем нули, для договоров показываем
                            if num_value == 0 and is_total_row:
                                row_values.append("")
                            else:
                                row_values.append(num_value)
                        else:
                            row_values.append("" if is_total_row else 0)
                    except (ValueError, TypeError):
                        row_values.append("" if is_total_row else 0)
            else:
                # Текстовые поля
                row_values.append(str(value) if value is not None else "")
        
        ws.append(row_values)
        
        # Суммируем доп. НДС для итога (только не для итоговой строки)
        if not is_total_row:
            vat_value = row_data["Дополнительный НДС"]
            if isinstance(vat_value, (int, float)):
                total_diff += vat_value

    # Форматируем все добавленные строки
    for row_idx in range(2, len(data) + 2):
        for col in range(1, 6):
            cell = ws.cell(row=row_idx, column=col)
            
            if col == 1:  # Название договора
                cell.alignment = align_left
            elif col == 2:  # № договора
                cell.alignment = align_center
            else:  # Числовые колонки
                cell.alignment = align_right
                # Форматируем только непустые числовые значения
                if cell.value != "" and cell.value is not None:
                    cell.number_format = '#,##0.00'

        # Выделяем итоговую строку - просто жирным
        if ws.cell(row=row_idx, column=1).value == "ИТОГО":
            for col in range(1, 6):
                cell = ws.cell(row=row_idx, column=col)
                cell.font = total_font

    # Настраиваем ширину колонок
    column_widths = {
        'A': 40,  # Название договора
        'B': 15,  # № договора
        'C': 20,  # Сумма договора
        'D': 20,  # Остаток
        'E': 25   # Доп. НДС
    }
    
    for col_letter, width in column_widths.items():
        ws.column_dimensions[col_letter].width = width

    try:
        wb.save(path)
        return True
    except Exception as e:
        print(f"Ошибка сохранения Excel: {e}")
        return False