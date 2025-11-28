import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from pathlib import Path
from datetime import datetime
import shutil
from gui.widgets.settings_dialog import set_icon

class ProjectEditor(tk.Toplevel):
    def __init__(self, parent, project_manager, project=None):
        super().__init__(parent)
        self.project_manager = project_manager
        self.project = project
        self.is_new = project is None
        self.unsaved_changes = False  # Флаг несохраненных изменений
        self.project_saved = not self.is_new  # Новый проект не сохранен
        
        self.show_manual_contracts = False

        # Создаем стиль для выделенной кнопки
        self.style = ttk.Style()
        self.style.configure('Highlight.TButton', background='#4CAF50', foreground='white')
        
        if self.is_new:
            self.title("Создать новый проект *")
            # Создаем проект в памяти, но не сохраняем
            self.project = project_manager.create_project_in_memory("Новый проект")
        else:
            self.title(f"Редактирование: {project.name}")
        
        self.geometry("900x700")
        self.resizable(True, True)
        
        self.create_widgets()
        self.load_project_data()

        # Устанавливаем иконку
        set_icon(self)
        
        # Отслеживаем изменения только для существующих проектов
        if not self.is_new:
            self.setup_change_tracking()

    def setup_change_tracking(self):
        """Настройка отслеживания изменений для существующих проектов"""
        self.name_var.trace('w', self.mark_unsaved)
        self.current_vat_var.trace('w', self.mark_unsaved)
        self.future_vat_var.trace('w', self.mark_unsaved)
        self.years_var.trace('w', self.mark_unsaved)
    
    def mark_unsaved(self, *args):
        """Пометить наличие несохраненных изменений"""
        if not self.is_new:  # Только для существующих проектов
            self.unsaved_changes = True
            self.update_title()
    
    def update_title(self):
        """Обновить заголовок окна"""
        base_title = f"Редактирование: {self.project.name}"
        if self.unsaved_changes:
            self.title(f"{base_title} *")
        else:
            self.title(base_title)
    
    def clear_unsaved_flag(self):
        """Сбросить флаг несохраненных изменений"""
        self.unsaved_changes = False
        self.update_title()

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
        
        self.save_btn = ttk.Button(button_frame, text="Сохранить проект", 
                                  command=self.save_project)
        self.save_btn.pack(side='left', padx=5)
        
        ttk.Button(button_frame, text="Рассчитать", 
                  command=self.calculate_results).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Закрыть", 
                  command=self.on_close).pack(side='right', padx=5)
        
        # Для нового проекта делаем кнопку сохранения более заметной
        if self.is_new:
            self.save_btn.configure(style='Highlight.TButton')
    
    def setup_settings_tab(self, parent):
        """Настройка вкладки с настройками"""
        # Название проекта
        ttk.Label(parent, text="Название проекта:").grid(row=0, column=0, sticky='w', padx=10, pady=5)
        self.name_var = tk.StringVar(value=self.project.name)
        name_entry = ttk.Entry(parent, textvariable=self.name_var, width=30)
        name_entry.grid(row=0, column=1, sticky='w', padx=10, pady=5)
        
        # Настройки НДС
        vat_frame = ttk.LabelFrame(parent, text="Настройки НДС")
        vat_frame.grid(row=1, column=0, columnspan=2, sticky='we', padx=10, pady=10)
        
        ttk.Label(vat_frame, text="Текущий НДС (%):").grid(row=0, column=0, sticky='w', padx=10, pady=5)
        self.current_vat_var = tk.DoubleVar(value=self.project.settings.get('current_vat', 20.0))
        current_vat_entry = ttk.Entry(vat_frame, textvariable=self.current_vat_var, width=10)
        current_vat_entry.grid(row=0, column=1, sticky='w', padx=10, pady=5)
        
        ttk.Label(vat_frame, text="Будущий НДС (%):").grid(row=1, column=0, sticky='w', padx=10, pady=5)
        self.future_vat_var = tk.DoubleVar(value=self.project.settings.get('future_vat', 22.0))
        future_vat_entry = ttk.Entry(vat_frame, textvariable=self.future_vat_var, width=10)
        future_vat_entry.grid(row=1, column=1, sticky='w', padx=10, pady=5)
        
        ttk.Label(vat_frame, text="Лет прогноза:").grid(row=2, column=0, sticky='w', padx=10, pady=5)
        self.years_var = tk.IntVar(value=self.project.settings.get('years', 5))
        years_entry = ttk.Entry(vat_frame, textvariable=self.years_var, width=10)
        years_entry.grid(row=2, column=1, sticky='w', padx=10, pady=5)
        
        # Информация о проекте
        info_frame = ttk.LabelFrame(parent, text="Информация о проекте")
        info_frame.grid(row=2, column=0, columnspan=2, sticky='we', padx=10, pady=10)
        
        self.created_var = tk.StringVar(value=f"Создан: {self.project.created.strftime('%d.%m.%Y %H:%M')}")
        self.modified_var = tk.StringVar(value=f"Изменен: {self.project.modified.strftime('%d.%m.%Y %H:%M')}")
        self.contracts_var = tk.StringVar(value=f"Контрактов: {len(self.project.contracts)}")
        self.status_var = tk.StringVar(value="Новый проект - требуется сохранение" if self.is_new else "Проект сохранен")
        
        ttk.Label(info_frame, textvariable=self.created_var).pack(anchor='w', padx=10, pady=2)
        ttk.Label(info_frame, textvariable=self.modified_var).pack(anchor='w', padx=10, pady=2)
        ttk.Label(info_frame, textvariable=self.contracts_var).pack(anchor='w', padx=10, pady=2)
        status_label = ttk.Label(info_frame, textvariable=self.status_var)
        status_label.pack(anchor='w', padx=10, pady=2)
        if self.is_new:
            status_label.configure(foreground="red")
        else:
            status_label.configure(foreground="green")
        
        # Путь к проекту
        path_frame = ttk.LabelFrame(parent, text="Расположение проекта")
        path_frame.grid(row=3, column=0, columnspan=2, sticky='we', padx=10, pady=10)
        
        if self.is_new:
            path_text = "Проект будет сохранен после нажатия кнопки 'Сохранить проект'"
        else:
            path_text = str(self.project.project_dir)
        
        self.path_var = tk.StringVar(value=path_text)
        path_label = ttk.Label(path_frame, textvariable=self.path_var, wraplength=600)
        path_label.pack(anchor='w', padx=10, pady=5)
    
    def setup_contracts_tab(self, parent):
        """Настройка вкладки с контрактами (обновленная)"""
        # Панель управления контрактами
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        # Кнопки для файловых контрактов
        file_contracts_frame = ttk.Frame(control_frame)
        file_contracts_frame.pack(side='left', fill='x', expand=True)
        
        ttk.Button(file_contracts_frame, text="Добавить из файла", 
                  command=self.add_contract).pack(side='left', padx=2)
        ttk.Button(file_contracts_frame, text="Редактировать файл", 
                  command=self.edit_contract).pack(side='left', padx=2)
        ttk.Button(file_contracts_frame, text="Удалить файл", 
                  command=self.remove_contract).pack(side='left', padx=2)
        ttk.Button(file_contracts_frame, text="Обновить файл", 
                  command=self.update_contract_file).pack(side='left', padx=2)
        
        # Кнопки для ручных контрактов
        manual_contracts_frame = ttk.Frame(control_frame)
        manual_contracts_frame.pack(side='left', fill='x', expand=True)
        
        ttk.Button(manual_contracts_frame, text="➕ Создать вручную", 
                  command=self.add_contract_manual).pack(side='left', padx=2)
        ttk.Button(manual_contracts_frame, text="✏️ Редактировать вручную", 
                  command=self.edit_contract_manual).pack(side='left', padx=2)
        ttk.Button(manual_contracts_frame, text="🗑️ Удалить ручной", 
                  command=self.remove_contract_manual).pack(side='left', padx=2)
        
        # Переключатель типа контрактов
        switch_frame = ttk.Frame(control_frame)
        switch_frame.pack(side='right')
        
        ttk.Label(switch_frame, text="Показать:").pack(side='left', padx=5)
        self.contracts_view_var = tk.StringVar(value="all")
        ttk.Radiobutton(switch_frame, text="Все", variable=self.contracts_view_var, 
                       value="all", command=self.refresh_contracts_view).pack(side='left', padx=2)
        ttk.Radiobutton(switch_frame, text="Файловые", variable=self.contracts_view_var, 
                       value="file", command=self.refresh_contracts_view).pack(side='left', padx=2)
        ttk.Radiobutton(switch_frame, text="Ручные", variable=self.contracts_view_var, 
                       value="manual", command=self.refresh_contracts_view).pack(side='left', padx=2)
        
        # Для нового проекта показываем предупреждение
        if self.is_new:
            warning_label = ttk.Label(control_frame, text="Сначала сохраните проект!", foreground="red")
            warning_label.pack(side='bottom', pady=5)
        
        # Таблица контрактов
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        # Скроллбары
        v_scrollbar = ttk.Scrollbar(tree_frame)
        v_scrollbar.pack(side='right', fill='y')
        
        # Обновляем колонки для отображения типа контракта
        self.contracts_tree = ttk.Treeview(tree_frame, 
                                          columns=('type', 'name', 'file', 'date', 'size', 'tasks', 'total_cost'),
                                          show='headings',
                                          yscrollcommand=v_scrollbar.set)
        v_scrollbar.config(command=self.contracts_tree.yview)
        
        self.contracts_tree.heading('type', text='Тип')
        self.contracts_tree.heading('name', text='Название контракта')
        self.contracts_tree.heading('file', text='Имя файла')
        self.contracts_tree.heading('date', text='Добавлен')
        self.contracts_tree.heading('size', text='Размер')
        self.contracts_tree.heading('tasks', text='Задач')
        self.contracts_tree.heading('total_cost', text='Общая стоимость')
        
        self.contracts_tree.column('type', width=80)
        self.contracts_tree.column('name', width=180)
        self.contracts_tree.column('file', width=120)
        self.contracts_tree.column('date', width=120)
        self.contracts_tree.column('size', width=80)
        self.contracts_tree.column('tasks', width=60)
        self.contracts_tree.column('total_cost', width=120)
        
        self.contracts_tree.pack(fill='both', expand=True)
        
        # Двойной клик для редактирования (разные действия для разных типов)
        self.contracts_tree.bind('<Double-1>', self.on_contract_double_click)

    def on_contract_double_click(self, event):
        """Обработка двойного клика по контракту"""
        selection = self.contracts_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.contracts_tree.item(item, 'values')
        contract_type = values[0]  # Тип контракта
        
        if contract_type == 'Файловый':
            self.edit_contract()
        else:  # Ручной
            self.edit_contract_manual()
    
    def refresh_contracts_view(self):
        """Обновить отображение контрактов в зависимости от выбранного типа"""
        view_type = self.contracts_view_var.get()
        self.load_contracts_data(view_type)
    
    def load_contracts_data(self, view_type="all"):
        """Загрузить данные контрактов с фильтрацией по типу"""
        for item in self.contracts_tree.get_children():
            self.contracts_tree.delete(item)
        
        # Файловые контракты
        if view_type in ["all", "file"]:
            for contract in self.project.contracts:
                file_path = Path(contract['file_path'])
                file_size = file_path.stat().st_size if file_path.exists() else 0
                size_text = f"{file_size / 1024:.1f} KB" if file_size > 0 else "N/A"
                
                self.contracts_tree.insert('', 'end', values=(
                    'Файловый',
                    contract['name'],
                    file_path.name,
                    contract['added_date'].strftime('%d.%m.%Y %H:%M'),
                    size_text,
                    'N/A',  # Для файловых контрактов задачи не считаем
                    'N/A'   # Для файловых контрактов общая стоимость не показываем
                ), tags=(f"file_{contract['name']}",))
        
        # Ручные контракты
        if view_type in ["all", "manual"]:
            for contract in self.project.manual_contracts:
                tasks_count = len(contract.tasks)
                total_cost = f"{contract.total_cost_with_vat:,.2f}"
                
                self.contracts_tree.insert('', 'end', values=(
                    'Ручной',
                    contract.name,
                    'N/A',
                    'N/A',
                    'N/A',
                    tasks_count,
                    total_cost
                ), tags=(f"manual_{contract.name}",))
        
        # Настраиваем цвета для разных типов контрактов
        self.contracts_tree.tag_configure('file_', background='#f0f8ff')  # Светло-голубой для файловых
        self.contracts_tree.tag_configure('manual_', background='#f0fff0')  # Светло-зеленый для ручных
    
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
        self.calc_status_var = tk.StringVar(value="Нажмите 'Рассчитать' для получения результатов")
        ttk.Label(parent, textvariable=self.calc_status_var).pack(side='bottom', pady=5)
    
    def load_project_data(self):
        """Загрузить данные проекта (обновленная версия)"""
        # Обновляем информацию
        self.name_var.set(self.project.name)
        self.created_var.set(f"Создан: {self.project.created.strftime('%d.%m.%Y %H:%M')}")
        self.modified_var.set(f"Изменен: {self.project.modified.strftime('%d.%m.%Y %H:%M')}")
        
        # Обновляем счетчики контрактов
        total_contracts = len(self.project.contracts) + len(self.project.manual_contracts)
        self.contracts_var.set(f"Контрактов: {total_contracts} (файловых: {len(self.project.contracts)}, ручных: {len(self.project.manual_contracts)})")
        
        if self.is_new:
            self.status_var.set("Новый проект - требуется сохранение")
            self.path_var.set("Проект будет сохранен после нажатия кнопки 'Сохранить проект'")
        else:
            self.status_var.set("Проект сохранен")
            self.path_var.set(str(self.project.project_dir))
        
        # Загружаем контракты
        self.load_contracts_data(self.contracts_view_var.get())
        
        # Загружаем результаты если есть
        if self.project.results:
            self.show_results()
        
        # Сбрасываем флаг несохраненных изменений
        if not self.is_new:
            self.clear_unsaved_flag()
    
    def save_project_settings(self):
        """Сохранить настройки проекта"""
        try:
            new_name = self.name_var.get().strip()
            if not new_name:
                new_name = "Безымянный проект"
            
            # Если имя изменилось - переименовываем проект
            if new_name != self.project.name:
                self.project.rename_project(new_name)
            
            # Обновляем настройки проекта
            self.project.settings.update({
                'current_vat': float(self.current_vat_var.get()),
                'future_vat': float(self.future_vat_var.get()),
                'years': int(self.years_var.get())
            })
            
            # Обновляем заголовок окна и путь
            self.title(f"Редактирование: {self.project.name}")
            self.path_var.set(str(self.project.project_dir))
            
            # Сохраняем проект
            self.project.save()
            self.modified_var.set(f"Изменен: {self.project.modified.strftime('%d.%m.%Y %H:%M')}")
            
            return True
            
        except Exception as e:
            print(f"Ошибка сохранения: {e}")
            messagebox.showerror("Ошибка", f"Не удалось сохранить проект: {e}")
            return False
    
    def save_contract_changes(self):
        """Сохранить изменения контрактов (автосохранение для существующих проектов)"""
        try:
            if not self.is_new:  # Только для существующих проектов
                self.project.save()
                self.modified_var.set(f"Изменен: {self.project.modified.strftime('%d.%m.%Y %H:%M')}")
            return True
        except Exception as e:
            print(f"Ошибка автосохранения контрактов: {e}")
            return False
    
    def add_contract(self):
        """Добавить контракт в проект"""
        if self.is_new:
            messagebox.showwarning("Сначала сохраните проект", 
                                 "Пожалуйста, сначала сохраните проект перед добавлением контрактов.")
            return
        
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
            
            # АВТОСОХРАНЕНИЕ при добавлении контракта (только для существующих проектов)
            if self.save_contract_changes():
                messagebox.showinfo("Успех", f"Контракт '{contract_name}' добавлен и сохранен")
            else:
                messagebox.showinfo("Успех", f"Контракт '{contract_name}' добавлен")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось добавить контракт: {e}")
    
    def edit_contract(self):
        """Редактировать выбранный контракт"""
        if self.is_new:
            messagebox.showwarning("Сначала сохраните проект", 
                                 "Пожалуйста, сначала сохраните проект перед редактированием контрактов.")
            return
            
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
            
            # АВТОСОХРАНЕНИЕ при редактировании контракта (только для существующих проектов)
            if self.save_contract_changes():
                self.load_project_data()
                messagebox.showinfo("Успех", f"Контракт переименован в '{new_name}' и сохранен")
            else:
                self.load_project_data()
                messagebox.showinfo("Успех", f"Контракт переименован в '{new_name}'")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось переименовать контракт: {e}")
    
    def update_contract_file(self):
        """Обновить файл контракта"""
        if self.is_new:
            messagebox.showwarning("Сначала сохраните проект", 
                                 "Пожалуйста, сначала сохраните проект перед обновлением файлов контрактов.")
            return
            
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
            
            # АВТОСОХРАНЕНИЕ при обновлении файла контракта (только для существующих проектов)
            if self.save_contract_changes():
                self.load_project_data()
                messagebox.showinfo("Успех", f"Файл контракта '{contract_name}' обновлен и сохранен")
            else:
                self.load_project_data()
                messagebox.showinfo("Успех", f"Файл контракта '{contract_name}' обновлен")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось обновить файл контракта: {e}")
    
    def remove_contract(self):
        """Удалить выбранный контракт"""
        if self.is_new:
            messagebox.showwarning("Сначала сохраните проект", 
                                 "Пожалуйста, сначала сохраните проект перед удалением контрактов.")
            return
            
        selection = self.contracts_tree.selection()
        if not selection:
            messagebox.showwarning("Выбор", "Выберите контракт для удаления")
            return
        
        item = selection[0]
        contract_name = self.contracts_tree.item(item, 'values')[0]
        
        if messagebox.askyesno("Удаление", f"Удалить контракт '{contract_name}'?"):
            try:
                self.project.remove_contract(contract_name)
                
                # АВТОСОХРАНЕНИЕ при удалении контракта (только для существующих проектов)
                if self.save_contract_changes():
                    self.load_project_data()
                    messagebox.showinfo("Успех", f"Контракт '{contract_name}' удален и сохранен")
                else:
                    self.load_project_data()
                    messagebox.showinfo("Успех", f"Контракт '{contract_name}' удален")
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить контракт: {e}")
    
    def calculate_results(self):
        """Рассчитать результаты проекта"""
        try:
            self.calc_status_var.set("Расчет...")
            self.update()
            
            results = self.project.calculate_results()
            self.show_results()
            self.calc_status_var.set(f"Расчет завершен. Записей: {len(results)}")
            
        except Exception as e:
            messagebox.showerror("Ошибка расчета", f"Не удалось рассчитать: {e}")
            self.calc_status_var.set("Ошибка расчета")
    
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
            if self.is_new:
                # Для нового проекта - создаем его в менеджере
                new_name = self.name_var.get().strip()
                if not new_name:
                    new_name = "Безымянный проект"
                
                # Обновляем настройки
                self.project.settings.update({
                    'current_vat': float(self.current_vat_var.get()),
                    'future_vat': float(self.future_vat_var.get()),
                    'years': int(self.years_var.get())
                })
                
                # Сохраняем проект через менеджер
                saved_project = self.project_manager.create_project(new_name)
                # Копируем контракты и настройки
                saved_project.contracts = self.project.contracts
                saved_project.settings = self.project.settings
                saved_project.save()
                
                # Заменяем проект на сохраненный
                self.project = saved_project
                self.is_new = False
                self.project_saved = True
                
                # Включаем отслеживание изменений
                self.setup_change_tracking()
                
                messagebox.showinfo("Сохранено", f"Проект '{self.project.name}' создан и сохранен")
            else:
                # Для существующего проекта - просто сохраняем
                if self.save_project_settings():
                    self.clear_unsaved_flag()
                    messagebox.showinfo("Сохранено", f"Проект '{self.project.name}' сохранен")
            
            self.load_project_data()
            
        except Exception as e:
            messagebox.showerror("Ошибка сохранения", f"Не удалось сохранить проект: {e}")
    
    def add_contract_manual(self):
        """Добавить контракт вручную"""
        if self.is_new:
            messagebox.showwarning("Сначала сохраните проект", 
                                 "Пожалуйста, сначала сохраните проект перед добавлением контрактов.")
            return
        
        try:
            # Импортируем здесь чтобы избежать циклических импортов
            from gui.widgets.contract_editor import ContractEditor
            
            editor = ContractEditor(self, self.project)
            self.wait_window(editor)
            
            # Автосохранение после добавления
            if self.save_contract_changes():
                self.load_contracts_data(self.contracts_view_var.get())
                messagebox.showinfo("Успех", "Контракт добавлен и сохранен")
            else:
                self.load_contracts_data(self.contracts_view_var.get())
                messagebox.showinfo("Успех", "Контракт добавлен")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать контракт: {e}")

    def edit_contract_manual(self):
        """Редактировать ручной контракт"""
        if self.is_new:
            messagebox.showwarning("Сначала сохраните проект", 
                                 "Пожалуйста, сначала сохраните проект перед редактированием контрактов.")
            return
            
        selection = self.contracts_tree.selection()
        if not selection:
            messagebox.showwarning("Выбор", "Выберите ручной контракт для редактирования")
            return
        
        item = selection[0]
        values = self.contracts_tree.item(item, 'values')
        
        # Проверяем что это ручной контракт
        if values[0] != 'Ручной':
            messagebox.showwarning("Ошибка", "Выберите ручной контракт для редактирования")
            return
        
        contract_name = values[1]  # Название контракта
        
        try:
            from gui.widgets.contract_editor import ContractEditor
            
            # Получаем контракт из проекта
            contract = self.project.get_manual_contract(contract_name)
            if not contract:
                messagebox.showerror("Ошибка", f"Контракт '{contract_name}' не найден")
                return
            
            editor = ContractEditor(self, self.project, contract)
            self.wait_window(editor)
            
            # Автосохранение после редактирования
            if self.save_contract_changes():
                self.load_contracts_data(self.contracts_view_var.get())
                messagebox.showinfo("Успех", "Контракт обновлен и сохранен")
            else:
                self.load_contracts_data(self.contracts_view_var.get())
                messagebox.showinfo("Успех", "Контракт обновлен")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось редактировать контракт: {e}")
    
    def remove_contract_manual(self):
        """Удалить ручной контракт"""
        if self.is_new:
            messagebox.showwarning("Сначала сохраните проект", 
                                 "Пожалуйста, сначала сохраните проект перед удалением контрактов.")
            return
            
        selection = self.contracts_tree.selection()
        if not selection:
            messagebox.showwarning("Выбор", "Выберите ручной контракт для удаления")
            return
        
        item = selection[0]
        values = self.contracts_tree.item(item, 'values')
        
        # Проверяем что это ручной контракт
        if values[0] != 'Ручной':
            messagebox.showwarning("Ошибка", "Выберите ручной контракт для удаления")
            return
        
        contract_name = values[1]
        
        if messagebox.askyesno("Удаление", f"Удалить ручной контракт '{contract_name}'?"):
            try:
                self.project.remove_manual_contract(contract_name)
                
                # Автосохранение после удаления
                if self.save_contract_changes():
                    self.load_contracts_data(self.contracts_view_var.get())
                    messagebox.showinfo("Успех", "Контракт удален и сохранен")
                else:
                    self.load_contracts_data(self.contracts_view_var.get())
                    messagebox.showinfo("Успех", "Контракт удален")
                    
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось удалить контракт: {e}")

    def on_close(self):
        """Действия при закрытии окна"""
        if self.is_new:
            # Для нового проекта спрашиваем о сохранении
            response = messagebox.askyesnocancel(
                "Новый проект",
                "Сохранить новый проект перед закрытием?",
                icon=messagebox.QUESTION
            )
            
            if response is None:  # Cancel
                return
            elif response:  # Yes
                self.save_project()
                # Если проект успешно сохранен, закрываем окно
                if not self.is_new:
                    self.destroy()
                else:
                    # Если пользователь отменил сохранение, остаемся в окне
                    return
            else:  # No
                self.destroy()
                
        elif self.unsaved_changes:
            # Для существующего проекта с изменениями
            response = messagebox.askyesnocancel(
                "Несохраненные изменения",
                "У вас есть несохраненные изменения. Сохранить перед закрытием?",
                icon=messagebox.WARNING
            )
            
            if response is None:  # Cancel
                return
            elif response:  # Yes
                self.save_project()
        
        self.destroy()