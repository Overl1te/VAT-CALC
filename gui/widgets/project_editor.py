import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from pathlib import Path
from datetime import datetime
import shutil

class ProjectEditor(tk.Toplevel):
    def __init__(self, parent, project_manager, project=None):
        super().__init__(parent)
        self.project_manager = project_manager
        self.project = project
        self.is_new = project is None
        
        if self.is_new:
            self.title("Создать новый проект")
            self.project = project_manager.create_project("Новый проект")
        else:
            self.title(f"Редактирование: {project.name}")
        
        self.geometry("900x700")
        self.resizable(True, True)
        
        self.create_widgets()
        self.load_project_data()
        
    def create_widgets(self):
        """Создать интерфейс редактора"""
        # Основные вкладки
        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Вкладка основных настроек
        settings_frame = ttk.Frame(notebook)
        notebook.add(settings_frame, text="Настройки")
        
        # Вкладка контрактов
        contracts_frame = ttk.Frame(notebook)
        notebook.add(contracts_frame, text="Контракты")
        
        # Вкладка результатов
        results_frame = ttk.Frame(notebook)
        notebook.add(results_frame, text="Результаты")
        
        self.setup_settings_tab(settings_frame)
        self.setup_contracts_tab(contracts_frame)
        self.setup_results_tab(results_frame)
        
        # Кнопки управления
        button_frame = ttk.Frame(self)
        button_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(button_frame, text="Сохранить проект", 
                  command=self.save_project).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Рассчитать", 
                  command=self.calculate_results).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Закрыть", 
                  command=self.on_close).pack(side='right', padx=5)
    
    def setup_settings_tab(self, parent):
        """Настройка вкладки с настройками"""
        # Название проекта
        ttk.Label(parent, text="Название проекта:").grid(row=0, column=0, sticky='w', padx=10, pady=5)
        self.name_var = tk.StringVar(value=self.project.name)
        name_entry = ttk.Entry(parent, textvariable=self.name_var, width=30)
        name_entry.grid(row=0, column=1, sticky='w', padx=10, pady=5)
        name_entry.bind('<FocusOut>', lambda e: self.auto_save_settings())
        
        # Настройки НДС
        vat_frame = ttk.LabelFrame(parent, text="Настройки НДС")
        vat_frame.grid(row=1, column=0, columnspan=2, sticky='we', padx=10, pady=10)
        
        ttk.Label(vat_frame, text="Текущий НДС (%):").grid(row=0, column=0, sticky='w', padx=10, pady=5)
        self.current_vat_var = tk.DoubleVar(value=self.project.settings.get('current_vat', 20.0))
        current_vat_entry = ttk.Entry(vat_frame, textvariable=self.current_vat_var, width=10)
        current_vat_entry.grid(row=0, column=1, sticky='w', padx=10, pady=5)
        current_vat_entry.bind('<FocusOut>', lambda e: self.auto_save_settings())
        
        ttk.Label(vat_frame, text="Будущий НДС (%):").grid(row=1, column=0, sticky='w', padx=10, pady=5)
        self.future_vat_var = tk.DoubleVar(value=self.project.settings.get('future_vat', 22.0))
        future_vat_entry = ttk.Entry(vat_frame, textvariable=self.future_vat_var, width=10)
        future_vat_entry.grid(row=1, column=1, sticky='w', padx=10, pady=5)
        future_vat_entry.bind('<FocusOut>', lambda e: self.auto_save_settings())
        
        ttk.Label(vat_frame, text="Лет прогноза:").grid(row=2, column=0, sticky='w', padx=10, pady=5)
        self.years_var = tk.IntVar(value=self.project.settings.get('years', 5))
        years_entry = ttk.Entry(vat_frame, textvariable=self.years_var, width=10)
        years_entry.grid(row=2, column=1, sticky='w', padx=10, pady=5)
        years_entry.bind('<FocusOut>', lambda e: self.auto_save_settings())
        
        # Информация о проекте
        info_frame = ttk.LabelFrame(parent, text="Информация о проекте")
        info_frame.grid(row=2, column=0, columnspan=2, sticky='we', padx=10, pady=10)
        
        self.created_var = tk.StringVar(value=f"Создан: {self.project.created.strftime('%d.%m.%Y %H:%M')}")
        self.modified_var = tk.StringVar(value=f"Изменен: {self.project.modified.strftime('%d.%m.%Y %H:%M')}")
        self.contracts_var = tk.StringVar(value=f"Контрактов: {len(self.project.contracts)}")
        
        ttk.Label(info_frame, textvariable=self.created_var).pack(anchor='w', padx=10, pady=2)
        ttk.Label(info_frame, textvariable=self.modified_var).pack(anchor='w', padx=10, pady=2)
        ttk.Label(info_frame, textvariable=self.contracts_var).pack(anchor='w', padx=10, pady=2)
        
        # Путь к проекту
        path_frame = ttk.LabelFrame(parent, text="Расположение проекта")
        path_frame.grid(row=3, column=0, columnspan=2, sticky='we', padx=10, pady=10)
        
        project_path = str(self.project.project_dir)
        path_label = ttk.Label(path_frame, text=project_path, wraplength=600)
        path_label.pack(anchor='w', padx=10, pady=5)
    
    def setup_contracts_tab(self, parent):
        """Настройка вкладки с контрактами"""
        # Панель управления контрактами
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(control_frame, text="Добавить контракт", 
                  command=self.add_contract).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Редактировать", 
                  command=self.edit_contract).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Удалить", 
                  command=self.remove_contract).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Обновить файл", 
                  command=self.update_contract_file).pack(side='left', padx=5)
        
        # Таблица контрактов
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Скроллбары
        v_scrollbar = ttk.Scrollbar(tree_frame)
        v_scrollbar.pack(side='right', fill='y')
        
        self.contracts_tree = ttk.Treeview(tree_frame, 
                                          columns=('name', 'file', 'date', 'size'),
                                          show='headings',
                                          yscrollcommand=v_scrollbar.set)
        v_scrollbar.config(command=self.contracts_tree.yview)
        
        self.contracts_tree.heading('name', text='Название контракта')
        self.contracts_tree.heading('file', text='Имя файла')
        self.contracts_tree.heading('date', text='Добавлен')
        self.contracts_tree.heading('size', text='Размер')
        
        self.contracts_tree.column('name', width=200)
        self.contracts_tree.column('file', width=150)
        self.contracts_tree.column('date', width=120)
        self.contracts_tree.column('size', width=80)
        
        self.contracts_tree.pack(fill='both', expand=True)
        
        # Двойной клик для редактирования
        self.contracts_tree.bind('<Double-1>', lambda e: self.edit_contract())
    
    def setup_results_tab(self, parent):
        """Настройка вкладки с результатами"""
        # Панель управления результатами
        results_control = ttk.Frame(parent)
        results_control.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(results_control, text="Экспорт в Excel", 
                  command=self.export_results).pack(side='left', padx=5)
        
        # Таблица результатов
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Скроллбары
        v_scrollbar = ttk.Scrollbar(tree_frame)
        v_scrollbar.pack(side='right', fill='y')
        
        h_scrollbar = ttk.Scrollbar(tree_frame, orient='horizontal')
        h_scrollbar.pack(side='bottom', fill='x')
        
        self.results_tree = ttk.Treeview(tree_frame, 
                                        columns=('name', 'base', 'year', 'vat', 'total'),
                                        show='headings',
                                        yscrollcommand=v_scrollbar.set,
                                        xscrollcommand=h_scrollbar.set)
        
        v_scrollbar.config(command=self.results_tree.yview)
        h_scrollbar.config(command=self.results_tree.xview)
        
        columns_config = [
            ('name', 'Название', 200),
            ('base', 'Базовая стоимость', 120),
            ('year', 'Год', 80),
            ('vat', 'Ставка НДС', 100),
            ('total', 'Стоимость с НДС', 120)
        ]
        
        for col, title, width in columns_config:
            self.results_tree.heading(col, text=title)
            self.results_tree.column(col, width=width, anchor='center')
        
        self.results_tree.pack(fill='both', expand=True)
        
        # Статус
        self.status_var = tk.StringVar(value="Нажмите 'Рассчитать' для получения результатов")
        ttk.Label(parent, textvariable=self.status_var).pack(side='bottom', pady=5)
    
    def load_project_data(self):
        """Загрузить данные проекта"""
        # Обновляем информацию
        self.created_var.set(f"Создан: {self.project.created.strftime('%d.%m.%Y %H:%M')}")
        self.modified_var.set(f"Изменен: {self.project.modified.strftime('%d.%m.%Y %H:%M')}")
        self.contracts_var.set(f"Контрактов: {len(self.project.contracts)}")
        
        # Загружаем контракты
        for item in self.contracts_tree.get_children():
            self.contracts_tree.delete(item)
        
        for contract in self.project.contracts:
            file_path = Path(contract['file_path'])
            file_size = file_path.stat().st_size if file_path.exists() else 0
            size_text = f"{file_size / 1024:.1f} KB" if file_size > 0 else "N/A"
            
            self.contracts_tree.insert('', 'end', values=(
                contract['name'],
                file_path.name,
                contract['added_date'].strftime('%d.%m.%Y %H:%M'),
                size_text
            ), tags=(contract['name'],))
        
        # Загружаем результаты если есть
        if self.project.results:
            self.show_results()
    
    def auto_save_settings(self):
        """Автосохранение настроек"""
        try:
            # Обновляем настройки проекта
            self.project.name = self.name_var.get().strip() or "Новый проект"
            self.project.settings.update({
                'current_vat': float(self.current_vat_var.get()),
                'future_vat': float(self.future_vat_var.get()),
                'years': int(self.years_var.get())
            })
            
            # Обновляем заголовок окна
            self.title(f"Редактирование: {self.project.name}")
            
            # Сохраняем проект
            self.project.save()
            self.modified_var.set(f"Изменен: {self.project.modified.strftime('%d.%m.%Y %H:%M')}")
            
        except Exception as e:
            print(f"Ошибка автосохранения: {e}")
    
    def add_contract(self):
        """Добавить контракт в проект"""
        file_path = filedialog.askopenfilename(
            title="Выберите файл контракта",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            contract_name = Path(file_path).stem
            
            # Запрашиваем кастомное имя
            contract_name = simpledialog.askstring(
                "Название контракта", 
                "Введите название контракта:", 
                initialvalue=contract_name
            )
            
            if not contract_name:
                return
                
            # Проверяем уникальность имени
            existing_names = [c['name'] for c in self.project.contracts]
            if contract_name in existing_names:
                messagebox.showerror("Ошибка", f"Контракт с именем '{contract_name}' уже существует")
                return
            
            self.project.add_contract(file_path, contract_name)
            self.load_project_data()
            self.auto_save_settings()
            messagebox.showinfo("Успех", f"Контракт '{contract_name}' добавлен")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось добавить контракт: {e}")
    
    def edit_contract(self):
        """Редактировать выбранный контракт"""
        selection = self.contracts_tree.selection()
        if not selection:
            messagebox.showwarning("Выбор", "Выберите контракт для редактирования")
            return
        
        item = selection[0]
        old_name = self.contracts_tree.item(item, 'values')[0]
        
        # Находим контракт
        contract = next((c for c in self.project.contracts if c['name'] == old_name), None)
        if not contract:
            messagebox.showerror("Ошибка", "Контракт не найден")
            return
        
        # Запрашиваем новое имя
        new_name = simpledialog.askstring(
            "Редактирование контракта", 
            "Введите новое название контракта:", 
            initialvalue=old_name
        )
        
        if not new_name or new_name == old_name:
            return
        
        # Проверяем уникальность
        existing_names = [c['name'] for c in self.project.contracts if c['name'] != old_name]
        if new_name in existing_names:
            messagebox.showerror("Ошибка", f"Контракт с именем '{new_name}' уже существует")
            return
        
        try:
            # Обновляем имя контракта
            contract['name'] = new_name
            self.project.modified = datetime.now()
            self.project.save()
            
            self.load_project_data()
            messagebox.showinfo("Успех", f"Контракт переименован в '{new_name}'")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось переименовать контракт: {e}")
    
    def update_contract_file(self):
        """Обновить файл контракта"""
        selection = self.contracts_tree.selection()
        if not selection:
            messagebox.showwarning("Выбор", "Выберите контракт для обновления")
            return
        
        item = selection[0]
        contract_name = self.contracts_tree.item(item, 'values')[0]
        
        # Находим контракт
        contract = next((c for c in self.project.contracts if c['name'] == contract_name), None)
        if not contract:
            messagebox.showerror("Ошибка", "Контракт не найден")
            return
        
        # Выбираем новый файл
        new_file_path = filedialog.askopenfilename(
            title="Выберите новый файл контракта",
            filetypes=[("Excel files", "*.xlsx *.xls"), ("CSV files", "*.csv"), ("All files", "*.*")]
        )
        
        if not new_file_path:
            return
        
        try:
            # Удаляем старый файл
            old_file_path = Path(contract['file_path'])
            if old_file_path.exists():
                old_file_path.unlink()
            
            # Копируем новый файл
            new_contract_file = self.project.contracts_dir / Path(new_file_path).name
            shutil.copy2(new_file_path, new_contract_file)
            
            # Обновляем путь
            contract['file_path'] = str(new_contract_file)
            contract['added_date'] = datetime.now()
            
            self.project.modified = datetime.now()
            self.project.save()
            
            self.load_project_data()
            messagebox.showinfo("Успех", f"Файл контракта '{contract_name}' обновлен")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось обновить файл контракта: {e}")
    
    def remove_contract(self):
        """Удалить выбранный контракт"""
        selection = self.contracts_tree.selection()
        if not selection:
            messagebox.showwarning("Выбор", "Выберите контракт для удаления")
            return
        
        item = selection[0]
        contract_name = self.contracts_tree.item(item, 'values')[0]
        
        if messagebox.askyesno("Удаление", f"Удалить контракт '{contract_name}'?"):
            try:
                self.project.remove_contract(contract_name)
                self.load_project_data()
                self.auto_save_settings()
                messagebox.showinfo("Успех", f"Контракт '{contract_name}' удален")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить контракт: {e}")
    
    def calculate_results(self):
        """Рассчитать результаты проекта"""
        try:
            self.status_var.set("Расчет...")
            self.update()
            
            results = self.project.calculate_results()
            self.show_results()
            self.status_var.set(f"Расчет завершен. Записей: {len(results)}")
            
        except Exception as e:
            messagebox.showerror("Ошибка расчета", f"Не удалось рассчитать: {e}")
            self.status_var.set("Ошибка расчета")
    
    def show_results(self):
        """Показать результаты в таблице"""
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        if not self.project.results:
            return
        
        for result in self.project.results[:1000]:  # Ограничиваем для производительности
            if isinstance(result, dict):
                self.results_tree.insert('', 'end', values=(
                    result.get('Название', ''),
                    result.get('Базовая стоимость', 0),
                    result.get('Год', 0),
                    f"{result.get('Ставка НДС', 0)}%",
                    result.get('Стоимость_с_НДС', 0)
                ))
    
    def export_results(self):
        """Экспорт результатов в Excel"""
        try:
            from utils.excel_processor import write_output_excel
            
            if not self.project.results:
                messagebox.showwarning("Нет данных", "Сначала выполните расчет")
                return
            
            filename = filedialog.asksaveasfilename(
                defaultextension='.xlsx',
                filetypes=[('Excel files', '*.xlsx')],
                title='Экспорт результатов в Excel',
                initialfile=f"{self.project.name}_результаты.xlsx"
            )
            
            if filename:
                write_output_excel(self.project.results, filename)
                messagebox.showinfo("Экспорт завершен", f"Результаты экспортированы в {filename}")
                
        except Exception as e:
            messagebox.showerror("Ошибка экспорта", f"Не удалось экспортировать: {e}")
    
    def save_project(self):
        """Сохранить проект"""
        try:
            self.auto_save_settings()
            messagebox.showinfo("Сохранено", f"Проект '{self.project.name}' сохранен")
            
        except Exception as e:
            messagebox.showerror("Ошибка сохранения", f"Не удалось сохранить проект: {e}")
    
    def on_close(self):
        """Действия при закрытии окна"""
        # Автосохранение при закрытии
        try:
            self.auto_save_settings()
        except Exception as e:
            print(f"Ошибка при автосохранении: {e}")
        
        self.destroy()