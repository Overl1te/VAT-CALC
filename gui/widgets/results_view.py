import tkinter as tk
from tkinter import ttk
from core.calculator import project_costs_vectorized, calculate_contracts_simple

class ResultsView(tk.Frame):  # Наследуем от Frame
    def __init__(self, parent):
        super().__init__(parent)  # Инициализируем Frame
        
        # Добавляем скроллбар
        scroll_frame = tk.Frame(self)
        scroll_frame.pack(fill='both', expand=True)
        
        scrollbar = ttk.Scrollbar(scroll_frame)
        scrollbar.pack(side='right', fill='y')
        
        self.tree = ttk.Treeview(scroll_frame, 
                                columns=('name','base','year','vat','with_vat'), 
                                show='headings',
                                yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.tree.yview)
        
        # Настраиваем колонки
        columns_config = [
            ('name', 'Название', 200),
            ('base', 'Базовая стоимость', 120),
            ('year', 'Год', 80),
            ('vat', 'Ставка НДС', 100),
            ('with_vat', 'Стоимость с НДС', 120)
        ]
        
        for col, title, width in columns_config:
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width, anchor='center')
        
        self.tree.pack(fill='both', expand=True)
        
        # Статус бар для отображения прогресса
        self.status = tk.Label(self, text='Готов к расчетам', relief='sunken', anchor='w')
        self.status.pack(fill='x', side='bottom')
        
        self.last_output = None
        self.last_data = None
        self.last_settings = None
        self.last_results = None

    def prepare_and_show(self, data, current_vat, future_vat, years):
        """Адаптированная версия для работы с OpenPyXL данными"""
        self.status.config(text='Расчет...')
        self.update()
        
        try:
            # Используем упрощенную функцию расчета
            if isinstance(data, list) and data and isinstance(data[0], dict):
                output_data = project_costs_vectorized(data, current_vat, future_vat, years)
            else:
                output_data = calculate_contracts_simple(data, current_vat, future_vat, years)
            
            # Очищаем дерево
            for i in self.tree.get_children():
                self.tree.delete(i)
            
            # Показываем данные (ограничиваем количество для скорости)
            display_limit = 1000
            display_data = output_data[:display_limit]
            
            # Вставляем данные в таблицу
            for row in display_data:
                if isinstance(row, dict):
                    self.tree.insert('', 'end', values=(
                        row.get('Название', ''),
                        row.get('Базовая стоимость', 0),
                        row.get('Год', 0),
                        row.get('Ставка НДС', 0),
                        row.get('Стоимость_с_НДС', 0)
                    ))
                else:
                    # Если это список
                    self.tree.insert('', 'end', values=tuple(row))
            
            self.last_output = output_data
            self.last_results = output_data
            total_rows = len(output_data)
            display_text = f'Готово! Рассчитано {total_rows} строк.'
            if total_rows > display_limit:
                display_text += f' Показаны первые {display_limit}.'
            self.status.config(text=display_text)
            
            return output_data
            
        except Exception as e:
            self.status.config(text=f'Ошибка: {str(e)}')
            raise