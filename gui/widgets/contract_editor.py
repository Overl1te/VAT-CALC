# project_editor_enhanced.py
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime
from core.contracts import Contract, ContractTask, VATChange

class ContractEditor(tk.Toplevel):
    def __init__(self, parent, project, contract=None):
        super().__init__(parent)
        self.project = project
        self.contract = contract or Contract("Новый контракт", 0, datetime.now().year)
        self.is_new = contract is None
        
        self.title("Редактор контракта" if not self.is_new else "Новый контракт")
        self.geometry("1000x700")
        self.create_widgets()
        self.load_contract_data()
        
    def create_widgets(self):
        """Создать интерфейс редактора контракта"""
        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Основная информация
        info_frame = ttk.Frame(notebook)
        notebook.add(info_frame, text="Основное")
        
        # Настройки контракта
        ttk.Label(info_frame, text="Название контракта:").grid(row=0, column=0, sticky='w', padx=10, pady=5)
        self.name_var = tk.StringVar(value=self.contract.name)
        ttk.Entry(info_frame, textvariable=self.name_var, width=50).grid(row=0, column=1, sticky='w', padx=10, pady=5)
        
        ttk.Label(info_frame, text="Общая стоимость с НДС:").grid(row=1, column=0, sticky='w', padx=10, pady=5)
        self.cost_var = tk.DoubleVar(value=self.contract.total_cost_with_vat)
        ttk.Entry(info_frame, textvariable=self.cost_var, width=20).grid(row=1, column=1, sticky='w', padx=10, pady=5)
        
        ttk.Label(info_frame, text="Год начала:").grid(row=2, column=0, sticky='w', padx=10, pady=5)
        self.start_year_var = tk.IntVar(value=self.contract.start_year)
        ttk.Entry(info_frame, textvariable=self.start_year_var, width=10).grid(row=2, column=1, sticky='w', padx=10, pady=5)
        
        ttk.Label(info_frame, text="Длительность (лет):").grid(row=3, column=0, sticky='w', padx=10, pady=5)
        self.duration_var = tk.IntVar(value=self.contract.duration)
        ttk.Spinbox(info_frame, from_=1, to=50, textvariable=self.duration_var, width=10).grid(row=3, column=1, sticky='w', padx=10, pady=5)
        
        ttk.Label(info_frame, text="Текущий НДС (%):").grid(row=4, column=0, sticky='w', padx=10, pady=5)
        self.vat_var = tk.DoubleVar(value=self.contract.current_vat_rate)
        ttk.Entry(info_frame, textvariable=self.vat_var, width=10).grid(row=4, column=1, sticky='w', padx=10, pady=5)
        
        # Задачи контракта
        tasks_frame = ttk.Frame(notebook)
        notebook.add(tasks_frame, text="Задачи")
        self.setup_tasks_tab(tasks_frame)
        
        # Изменения НДС
        vat_frame = ttk.Frame(notebook)
        notebook.add(vat_frame, text="Изменения НДС")
        self.setup_vat_tab(vat_frame)
        
        # Предпросмотр
        preview_frame = ttk.Frame(notebook)
        notebook.add(preview_frame, text="Предпросмотр")
        self.setup_preview_tab(preview_frame)
        
        # Кнопки управления
        button_frame = ttk.Frame(self)
        button_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(button_frame, text="Сохранить", command=self.save_contract).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Отмена", command=self.destroy).pack(side='right', padx=5)
    
    def setup_tasks_tab(self, parent):
        """Настройка вкладки с задачами"""
        # Панель управления
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(control_frame, text="Добавить задачу", command=self.add_task).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Удалить задачу", command=self.remove_task).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Отметить выполненной", command=self.mark_task_completed).pack(side='left', padx=5)
        
        # Таблица задач
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.tasks_tree = ttk.Treeview(tree_frame, columns=('name', 'year', 'cost', 'completion', 'status'), show='headings')
        
        self.tasks_tree.heading('name', text='Название задачи')
        self.tasks_tree.heading('year', text='Год')
        self.tasks_tree.heading('cost', text='Стоимость с НДС')
        self.tasks_tree.heading('completion', text='Выполнение %')
        self.tasks_tree.heading('status', text='Статус')
        
        self.tasks_tree.column('name', width=200)
        self.tasks_tree.column('year', width=80)
        self.tasks_tree.column('cost', width=120)
        self.tasks_tree.column('completion', width=100)
        self.tasks_tree.column('status', width=100)
        
        self.tasks_tree.pack(fill='both', expand=True)
        
        # Двойной клик для редактирования
        self.tasks_tree.bind('<Double-1>', lambda e: self.edit_task())
    
    def setup_vat_tab(self, parent):
        """Настройка вкладки с изменениями НДС"""
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill='x', padx=10, pady=5)
        
        ttk.Button(control_frame, text="Добавить изменение НДС", command=self.add_vat_change).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Удалить изменение", command=self.remove_vat_change).pack(side='left', padx=5)
        
        # Таблица изменений НДС
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.vat_tree = ttk.Treeview(tree_frame, columns=('year', 'new_rate'), show='headings')
        
        self.vat_tree.heading('year', text='Год изменения')
        self.vat_tree.heading('new_rate', text='Новая ставка НДС %')
        
        self.vat_tree.column('year', width=150)
        self.vat_tree.column('new_rate', width=150)
        
        self.vat_tree.pack(fill='both', expand=True)
    
    def setup_preview_tab(self, parent):
        """Настройка вкладки предпросмотра"""
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.preview_tree = ttk.Treeview(tree_frame, columns=('year', 'planned', 'completed', 'remaining', 'vat_rate', 'vat_impact'), show='headings')
        
        self.preview_tree.heading('year', text='Год')
        self.preview_tree.heading('planned', text='Планируемая стоимость')
        self.preview_tree.heading('completed', text='Выполнено')
        self.preview_tree.heading('remaining', text='Остаток')
        self.preview_tree.heading('vat_rate', text='Ставка НДС %')
        self.preview_tree.heading('vat_impact', text='Влияние НДС')
        
        for col in ('year', 'planned', 'completed', 'remaining', 'vat_rate', 'vat_impact'):
            self.preview_tree.column(col, width=120)
        
        self.preview_tree.pack(fill='both', expand=True)
        
        # Кнопка обновления предпросмотра
        ttk.Button(parent, text="Обновить расчет", command=self.update_preview).pack(pady=5)
    
    def load_contract_data(self):
        """Загрузить данные контракта"""
        self.update_tasks_list()
        self.update_vat_changes_list()
        self.update_preview()
    
    def add_task(self):
        """Добавить новую задачу"""
        dialog = TaskEditor(self, self.contract)
        self.wait_window(dialog)
        self.update_tasks_list()
        self.update_preview()
    
    def edit_task(self):
        """Редактировать выбранную задачу"""
        selection = self.tasks_tree.selection()
        if not selection:
            return
        
        task_name = self.tasks_tree.item(selection[0], 'values')[0]
        task = next((t for t in self.contract.tasks if t.name == task_name), None)
        
        if task:
            dialog = TaskEditor(self, self.contract, task)
            self.wait_window(dialog)
            self.update_tasks_list()
            self.update_preview()
    
    def remove_task(self):
        """Удалить задачу"""
        selection = self.tasks_tree.selection()
        if not selection:
            return
        
        task_name = self.tasks_tree.item(selection[0], 'values')[0]
        self.contract.tasks = [t for t in self.contract.tasks if t.name != task_name]
        self.update_tasks_list()
        self.update_preview()
    
    def mark_task_completed(self):
        """Отметить задачу как выполненную"""
        selection = self.tasks_tree.selection()
        if not selection:
            return
        
        task_name = self.tasks_tree.item(selection[0], 'values')[0]
        task = next((t for t in self.contract.tasks if t.name == task_name), None)
        
        if task:
            task.is_completed = True
            task.completion = 100.0
            self.update_tasks_list()
            self.update_preview()
    
    def update_tasks_list(self):
        """Обновить список задач"""
        for item in self.tasks_tree.get_children():
            self.tasks_tree.delete(item)
        
        for task in self.contract.tasks:
            status = "Выполнена" if task.is_completed else "В работе"
            self.tasks_tree.insert('', 'end', values=(
                task.name,
                task.year,
                f"{task.cost_with_vat:,.2f}",
                f"{task.completion}%",
                status
            ))
    
    def add_vat_change(self):
        """Добавить изменение НДС"""
        year = simpledialog.askinteger("Год изменения", "Введите год изменения НДС:", initialvalue=datetime.now().year + 1)
        if not year:
            return
        
        rate = simpledialog.askfloat("Новая ставка", "Введите новую ставку НДС (%):", initialvalue=22.0)
        if rate is None:
            return
        
        self.contract.add_vat_change(year, rate)
        self.update_vat_changes_list()
        self.update_preview()
    
    def remove_vat_change(self):
        """Удалить изменение НДС"""
        selection = self.vat_tree.selection()
        if not selection:
            return
        
        year = int(self.vat_tree.item(selection[0], 'values')[0])
        self.contract.vat_changes = [v for v in self.contract.vat_changes if v.year != year]
        self.update_vat_changes_list()
        self.update_preview()
    
    def update_vat_changes_list(self):
        """Обновить список изменений НДС"""
        for item in self.vat_tree.get_children():
            self.vat_tree.delete(item)
        
        for vat_change in self.contract.vat_changes:
            self.vat_tree.insert('', 'end', values=(
                vat_change.year,
                f"{vat_change.new_rate}%"
            ))
    
    def update_preview(self):
        """Обновить предпросмотр"""
        for item in self.preview_tree.get_children():
            self.preview_tree.delete(item)
        
        breakdown = self.contract.calculate_yearly_breakdown()
        for year_data in breakdown:
            self.preview_tree.insert('', 'end', values=(
                year_data['year'],
                f"{year_data['planned_cost']:,.2f}",
                f"{year_data['completed_cost']:,.2f}",
                f"{year_data['remaining_cost']:,.2f}",
                f"{year_data['vat_rate']}%",
                f"{year_data['vat_impact']:,.2f}"
            ))
    
    def save_contract(self):
        """Сохранить контракт"""
        try:
            # Обновляем основные данные
            self.contract.name = self.name_var.get()
            self.contract.total_cost_with_vat = float(self.cost_var.get())
            self.contract.start_year = int(self.start_year_var.get())
            self.contract.duration = int(self.duration_var.get())
            self.contract.current_vat_rate = float(self.vat_var.get())
            
            # Если это новый контракт, добавляем в проект
            if self.is_new:
                # Здесь нужно добавить логику сохранения в проект
                pass
            
            messagebox.showinfo("Сохранено", "Контракт успешно сохранен")
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить контракт: {e}")

class TaskEditor(tk.Toplevel):
    def __init__(self, parent, contract, task=None):
        super().__init__(parent)
        self.contract = contract
        self.task = task or ContractTask("", datetime.now().year, 0)
        self.is_new = task is None
        
        self.title("Редактирование задачи" if not self.is_new else "Новая задача")
        self.geometry("400x300")
        self.create_widgets()
    
    def create_widgets(self):
        """Создать интерфейс редактора задачи"""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        ttk.Label(main_frame, text="Название задачи:").grid(row=0, column=0, sticky='w', pady=5)
        self.name_var = tk.StringVar(value=self.task.name)
        ttk.Entry(main_frame, textvariable=self.name_var, width=30).grid(row=0, column=1, sticky='w', pady=5)
        
        ttk.Label(main_frame, text="Год выполнения:").grid(row=1, column=0, sticky='w', pady=5)
        self.year_var = tk.IntVar(value=self.task.year)
        ttk.Spinbox(main_frame, from_=self.contract.start_year, to=self.contract.end_year, 
                   textvariable=self.year_var, width=10).grid(row=1, column=1, sticky='w', pady=5)
        
        ttk.Label(main_frame, text="Стоимость с НДС:").grid(row=2, column=0, sticky='w', pady=5)
        self.cost_var = tk.DoubleVar(value=self.task.cost_with_vat)
        ttk.Entry(main_frame, textvariable=self.cost_var, width=15).grid(row=2, column=1, sticky='w', pady=5)
        
        ttk.Label(main_frame, text="Процент выполнения:").grid(row=3, column=0, sticky='w', pady=5)
        self.completion_var = tk.DoubleVar(value=self.task.completion)
        ttk.Scale(main_frame, from_=0, to=100, variable=self.completion_var, 
                 orient='horizontal').grid(row=3, column=1, sticky='we', pady=5)
        
        self.completed_var = tk.BooleanVar(value=self.task.is_completed)
        ttk.Checkbutton(main_frame, text="Задача выполнена", 
                       variable=self.completed_var).grid(row=4, column=0, columnspan=2, sticky='w', pady=5)
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=5, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="Сохранить", command=self.save_task).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Отмена", command=self.destroy).pack(side='left', padx=5)
        
        main_frame.columnconfigure(1, weight=1)
    
    def save_task(self):
        """Сохранить задачу"""
        try:
            self.task.name = self.name_var.get()
            self.task.year = int(self.year_var.get())
            self.task.cost_with_vat = float(self.cost_var.get())
            self.task.completion = float(self.completion_var.get())
            self.task.is_completed = self.completed_var.get()
            
            if self.is_new:
                self.contract.tasks.append(self.task)
            
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить задачу: {e}")