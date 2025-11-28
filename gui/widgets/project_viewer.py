import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

class ProjectViewer(tk.Toplevel):
    def __init__(self, parent, project):
        super().__init__(parent)
        self.project = project
        self.title(f"Просмотр проекта: {project.name}")
        self.geometry("900x600")
        self.resizable(True, True)
        
        # Основная рамка
        main_frame = ttk.Frame(self)
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Информация о проекте
        info_frame = ttk.LabelFrame(main_frame, text="Информация о проекте")
        info_frame.pack(fill='x', pady=(0, 10))
        
        info_text = (f"Название: {project.name}\n"
                    f"Создан: {project.created.strftime('%d.%m.%Y %H:%M')}\n"
                    f"Изменен: {project.modified.strftime('%d.%m.%Y %H:%M')}\n"
                    f"Настройки: НДС {project.settings.get('current_vat', 20)}% → "
                    f"{project.settings.get('future_vat', 22)}%, "
                    f"лет прогноза: {project.settings.get('years', 5)}")
        
        ttk.Label(info_frame, text=info_text, justify='left').pack(anchor='w', padx=10, pady=10)
        
        # Данные проекта
        data_frame = ttk.LabelFrame(main_frame, text="Результаты расчетов")
        data_frame.pack(fill='both', expand=True)
        
        # Таблица с результатами
        self.create_results_table(data_frame)
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(10, 0))
        
        ttk.Button(button_frame, text="Экспорт в Excel", 
                  command=self.export_to_excel).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Закрыть", 
                  command=self.destroy).pack(side='right', padx=5)
    
    def create_results_table(self, parent):
        """Создать таблицу с результатами"""
        # Создаем фрейм с прокруткой
        table_frame = ttk.Frame(parent)
        table_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Скроллбары
        v_scrollbar = ttk.Scrollbar(table_frame)
        v_scrollbar.pack(side='right', fill='y')
        
        h_scrollbar = ttk.Scrollbar(table_frame, orient='horizontal')
        h_scrollbar.pack(side='bottom', fill='x')
        
        # Таблица
        self.tree = ttk.Treeview(table_frame, 
                                columns=('name', 'base', 'year', 'vat', 'total'),
                                show='headings',
                                yscrollcommand=v_scrollbar.set,
                                xscrollcommand=h_scrollbar.set)
        
        # Настройка колонок
        columns_config = [
            ('name', 'Название', 200),
            ('base', 'Базовая стоимость', 120),
            ('year', 'Год', 80),
            ('vat', 'Ставка НДС', 100),
            ('total', 'Стоимость с НДС', 120)
        ]
        
        for col, title, width in columns_config:
            self.tree.heading(col, text=title)
            self.tree.column(col, width=width, anchor='center')
        
        self.tree.pack(fill='both', expand=True)
        
        # Настройка скроллбаров
        v_scrollbar.config(command=self.tree.yview)
        h_scrollbar.config(command=self.tree.xview)
        
        # Заполняем таблицу данными
        self.populate_table()
    
    def populate_table(self):
        """Заполнить таблицу данными проекта"""
        if not self.project.results:
            messagebox.showinfo("Нет данных", "В проекте нет результатов расчетов")
            return
        
        # Очищаем таблицу
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Заполняем данными
        try:
            if isinstance(self.project.results, list):
                for result in self.project.results[:1000]:  # Ограничиваем для производительности
                    if isinstance(result, dict):
                        self.tree.insert('', 'end', values=(
                            result.get('Название', ''),
                            result.get('Базовая стоимость', 0),
                            result.get('Год', 0),
                            f"{result.get('Ставка НДС', 0)}%",
                            result.get('Стоимость_с_НДС', 0)
                        ))
                    else:
                        # Если это список
                        self.tree.insert('', 'end', values=tuple(result))
            
            # Показываем статистику
            self.show_stats()
            
        except Exception as e:
            messagebox.showerror("Ошибка данных", f"Не удалось загрузить данные: {e}")
    
    def show_stats(self):
        """Показать статистику по проекту"""
        if self.project.results:
            total_records = len(self.project.results)
            stats_text = f"Всего записей: {total_records}"
            
            # Добавляем статистику в заголовок
            current_title = self.title()
            self.title(f"{current_title} - {stats_text}")
    
    def export_to_excel(self):
        """Экспорт проекта в Excel"""
        try:
            from utils.excel_processor import write_output_excel
            from tkinter import filedialog
            
            if not self.project.results:
                messagebox.showwarning("Нет данных", "Нет данных для экспорта")
                return
            
            filename = filedialog.asksaveasfilename(
                defaultextension='.xlsx',
                filetypes=[('Excel files', '*.xlsx')],
                title='Экспорт проекта в Excel',
                initialfile=f"{self.project.name}.xlsx"
            )
            
            if filename:
                write_output_excel(self.project.results, filename)
                messagebox.showinfo("Экспорт завершен", f"Проект экспортирован в {filename}")
                
        except Exception as e:
            messagebox.showerror("Ошибка экспорта", f"Не удалось экспортировать: {e}")