import tkinter as tk
from tkinter import ttk
from core.calculator import project_costs_vectorized
import pandas as pd

class ResultsView:
    def __init__(self, parent):
        self.frame = tk.Frame(parent)
        
        # Добавляем скроллбар
        scroll_frame = tk.Frame(self.frame)
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
        self.status = tk.Label(self.frame, text='Готов к расчетам', relief='sunken', anchor='w')
        self.status.pack(fill='x', side='bottom')
        
        self.last_output = None

    def prepare_and_show(self, df, current_vat, future_vat, years):
        """Оптимизированная версия с прогрессом"""
        self.status.config(text='Расчет...')
        self.frame.update()
        
        try:
            # Используем оптимизированную функцию
            output_df = project_costs_vectorized(df, current_vat, future_vat, years)
            
            # Очищаем дерево
            for i in self.tree.get_children():
                self.tree.delete(i)
            
            # Показываем только первые 1000 строк для скорости
            display_rows = output_df.head(1000).itertuples()
            
            # Быстрая вставка с пакетной обработкой
            rows_to_insert = []
            for row in display_rows:
                rows_to_insert.append((
                    getattr(row, 'Название', ''),
                    getattr(row, 'Базовая стоимость', 0),
                    getattr(row, 'Год', 0),
                    getattr(row, 'Ставка НДС', 0),
                    getattr(row, 'Стоимость_с_НДС', 0)
                ))
            
            # Вставляем пачкой
            for row_data in rows_to_insert:
                self.tree.insert('', 'end', values=row_data)
            
            self.last_output = output_df
            self.status.config(text=f'Готово! Рассчитано {len(output_df)} строк. Показаны первые 1000.')
            
            return output_df
            
        except Exception as e:
            self.status.config(text=f'Ошибка: {str(e)}')
            raise