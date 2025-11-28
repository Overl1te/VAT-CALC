# gui/widgets/project_editor.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from pathlib import Path
from datetime import datetime
import shutil
from gui.widgets.settings_dialog import set_icon
from gui.widgets.contract_editor import ContractEditor  # <-- УБЕДИСЬ, ЧТО ЭТОТ ФАЙЛ СУЩЕСТВУЕТ!
from core.contracts import Contract, VATChange, ContractTask


class ProjectEditor(tk.Toplevel):
    def __init__(self, parent, project_manager, project=None):
        super().__init__(parent)
        self.project_manager = project_manager
        self.project = project
        self.is_new = project is None
        self.unsaved_changes = False

        if self.is_new:
            self.title("Создать новый проект *")
            self.project = project_manager.create_project_in_memory("Новый проект")
        else:
            self.title(f"Редактирование: {project.name}")

        self.geometry("1000x720")
        self.resizable(True, True)

        self.create_widgets()
        self.load_project_data()
        set_icon(self)

        if not self.is_new:
            self.setup_change_tracking()

    def setup_change_tracking(self):
        self.name_var.trace('w', self.mark_unsaved)
        self.current_vat_var.trace('w', self.mark_unsaved)
        self.future_vat_var.trace('w', self.mark_unsaved)

    def mark_unsaved(self, *args):
        if not self.is_new:
            self.unsaved_changes = True
            self.update_title()

    def update_title(self):
        title = f"Редактирование: {self.project.name}"
        if self.unsaved_changes:
            self.title(f"{title} *")
        else:
            self.title(title)

    def clear_unsaved_flag(self):
        self.unsaved_changes = False
        self.update_title()

    def create_widgets(self):
        notebook = ttk.Notebook(self)
        notebook.pack(fill='both', expand=True, padx=10, pady=10)

        settings_frame = ttk.Frame(notebook)
        contracts_frame = ttk.Frame(notebook)
        results_frame = ttk.Frame(notebook)

        notebook.add(settings_frame, text="Настройки")
        notebook.add(contracts_frame, text="Контракты")
        notebook.add(results_frame, text="Результаты")

        self.setup_settings_tab(settings_frame)
        self.setup_contracts_tab(contracts_frame)
        self.setup_results_tab(results_frame)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill='x', padx=10, pady=5)

        self.save_btn = ttk.Button(btn_frame, text="Сохранить проект", command=self.save_project)
        self.save_btn.pack(side='left', padx=5)

        ttk.Button(btn_frame, text="Рассчитать", command=self.calculate_results).pack(side='left', padx=5)
        ttk.Button(btn_frame, text="Закрыть", command=self.on_close).pack(side='right', padx=5)

        if self.is_new:
            self.save_btn.configure(style='Highlight.TButton')

    def setup_settings_tab(self, parent):
        ttk.Label(parent, text="Название проекта:").grid(row=0, column=0, sticky='w', padx=10, pady=8)
        self.name_var = tk.StringVar(value=self.project.name)
        ttk.Entry(parent, textvariable=self.name_var, width=40).grid(row=0, column=1, sticky='w', padx=10)

        vat_frame = ttk.LabelFrame(parent, text="Настройки НДС по умолчанию")
        vat_frame.grid(row=1, column=0, columnspan=2, sticky='we', padx=10, pady=10)

        ttk.Label(vat_frame, text="Текущий НДС (%):").grid(row=0, column=0, sticky='w', padx=10, pady=5)
        self.current_vat_var = tk.DoubleVar(value=self.project.settings.get('current_vat', 20.0))
        ttk.Entry(vat_frame, textvariable=self.current_vat_var, width=10).grid(row=0, column=1, sticky='w', padx=10)

        ttk.Label(vat_frame, text="Будущий НДС (%):").grid(row=1, column=0, sticky='w', padx=10, pady=5)
        self.future_vat_var = tk.DoubleVar(value=self.project.settings.get('future_vat', 22.0))
        ttk.Entry(vat_frame, textvariable=self.future_vat_var, width=10).grid(row=1, column=1, sticky='w', padx=10)

        info_frame = ttk.LabelFrame(parent, text="Информация")
        info_frame.grid(row=2, column=0, columnspan=2, sticky='we', padx=10, pady=10)

        self.info_text = tk.Text(info_frame, height=6, width=80)
        self.info_text.pack(padx=10, pady=10)
        self.info_text.config(state='disabled')

    def setup_contracts_tab(self, parent):
        control_frame = ttk.Frame(parent)
        control_frame.pack(fill='x', padx=10, pady=5)

        # Кнопки для файловых контрактов
        file_btns = ttk.Frame(control_frame)
        file_btns.pack(side='left')
        ttk.Button(file_btns, text="Добавить из файла", command=self.add_contract).pack(side='left', padx=2)
        ttk.Button(file_btns, text="Удалить файл", command=self.remove_contract).pack(side='left', padx=2)

        # Кнопки для ручных контрактов
        manual_btns = ttk.Frame(control_frame)
        manual_btns.pack(side='left', padx=20)
        ttk.Button(manual_btns, text="Создать вручную", command=self.add_contract_manual).pack(side='left', padx=2)
        ttk.Button(manual_btns, text="Редактировать", command=self.edit_contract_manual).pack(side='left', padx=2)
        ttk.Button(manual_btns, text="Удалить", command=self.remove_contract_manual).pack(side='left', padx=2)

        # Переключатель вида
        view_frame = ttk.Frame(control_frame)
        view_frame.pack(side='right')
        ttk.Label(view_frame, text="Показать:").pack(side='left')
        self.view_var = tk.StringVar(value="all")
        ttk.Radiobutton(view_frame, text="Все", variable=self.view_var, value="all", command=self.refresh_contracts).pack(side='left', padx=5)
        ttk.Radiobutton(view_frame, text="Файловые", variable=self.view_var, value="file", command=self.refresh_contracts).pack(side='left', padx=5)
        ttk.Radiobutton(view_frame, text="Ручные", variable=self.view_var, value="manual", command=self.refresh_contracts).pack(side='left', padx=5)

        # Таблица
        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill='both', expand=True, padx=10, pady=5)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        vsb.pack(side='right', fill='y')

        self.contracts_tree = ttk.Treeview(tree_frame,
                                          columns=('type', 'name', 'cost', 'tasks'),
                                          show='headings',
                                          yscrollcommand=vsb.set)
        vsb.config(command=self.contracts_tree.yview)

        self.contracts_tree.heading('type', text='Тип')
        self.contracts_tree.heading('name', text='Название')
        self.contracts_tree.heading('cost', text='Сумма с НДС')
        self.contracts_tree.heading('tasks', text='Задач')

        self.contracts_tree.column('type', width=80)
        self.contracts_tree.column('name', width=300)
        self.contracts_tree.column('cost', width=150, anchor='e')
        self.contracts_tree.column('tasks', width=80, anchor='center')

        self.contracts_tree.pack(fill='both', expand=True)
        self.contracts_tree.bind('<Double-1>', self.on_double_click)

    def setup_results_tab(self, parent):
        ttk.Button(parent, text="Экспорт в Excel (скоро)", state='disabled').pack(pady=10)

        tree_frame = ttk.Frame(parent)
        tree_frame.pack(fill='both', expand=True, padx=10)

        vsb = ttk.Scrollbar(tree_frame, orient="vertical")
        vsb.pack(side='right', fill='y')

        self.results_tree = ttk.Treeview(tree_frame,
                                        columns=('name', 'difference'),
                                        show='headings',
                                        yscrollcommand=vsb.set)
        vsb.config(command=self.results_tree.yview)

        self.results_tree.heading('name', text='Контракт')
        self.results_tree.heading('difference', text='Доп. стоимость из-за НДС')

        self.results_tree.column('name', width=400)
        self.results_tree.column('difference', width=200, anchor='e')

        self.results_tree.pack(fill='both', expand=True)

        self.result_label = ttk.Label(parent, text="Нажмите «Рассчитать»", font=('Arial', 10, 'italic'))
        self.result_label.pack(pady=10)

    def load_project_data(self):
        self.name_var.set(self.project.name)
        self.current_vat_var.set(self.project.settings.get('current_vat', 20.0))
        self.future_vat_var.set(self.project.settings.get('future_vat', 22.0))

        info = f"Создан: {self.project.created.strftime('%d.%m.%Y %H:%M')}\n"
        info += f"Изменён: {self.project.modified.strftime('%d.%m.%Y %H:%M')}\n"
        info += f"Файловых контрактов: {len(self.project.contracts)}\n"
        info += f"Ручных контрактов: {len(self.project.manual_contracts)}\n"
        info += f"Путь: {self.project.project_dir if not self.is_new else 'не сохранён'}"
        self.info_text.config(state='normal')
        self.info_text.delete(1.0, 'end')
        self.info_text.insert('end', info)
        self.info_text.config(state='disabled')

        self.refresh_contracts()

    def refresh_contracts(self):
        for item in self.contracts_tree.get_children():
            self.contracts_tree.delete(item)

        view = self.view_var.get()

        if view in ("all", "file"):
            for contract in self.project.contracts:
                self.contracts_tree.insert('', 'end', values=(
                    "Файловый",
                    contract.name,
                    f"{contract.total_cost_with_vat:,.2f}",
                    len(contract.tasks)
                ))

        if view in ("all", "manual"):
            for contract in self.project.manual_contracts:
                self.contracts_tree.insert('', 'end', values=(
                    "Ручной",
                    contract.name,
                    f"{contract.total_cost_with_vat:,.2f}",
                    len(contract.tasks)
                ))

    def on_double_click(self, event):
        selection = self.contracts_tree.selection()
        if not selection:
            return
        item = self.contracts_tree.item(selection[0])
        contract_type = item['values'][0]
        name = item['values'][1]

        if contract_type == "Ручной":
            self.edit_contract_manual(name)
        else:
            messagebox.showinfo("Файловый контракт", "Редактирование файловых контрактов через Excel пока не реализовано")

    def add_contract(self):
        if self.is_new:
            messagebox.showwarning("Сначала сохраните проект", "Сохраните проект перед добавлением файлов")
            return
        # Заглушка — можно реализовать позже
        messagebox.showinfo("Скоро", "Добавление из файла будет реализовано позже")

    def add_contract_manual(self):
        if self.is_new:
            messagebox.showwarning("Сначала сохраните проект", "Сохраните проект перед созданием ручного контракта")
            return

        # Создаём пустой контракт
        contract = Contract(
            name="Новый ручной контракт",
            total_cost_with_vat=0.0,
            start_year=datetime.now().year,
            current_vat_rate=self.project.settings['current_vat']
        )
        editor = ContractEditor(self, self.project, contract)
        self.wait_window(editor)

        if contract.name != "Новый ручной контракт" or contract.total_cost_with_vat > 0:
            self.project.manual_contracts.append(contract)
            self.project.modified = datetime.now()
            self.project.save()
            self.refresh_contracts()
            messagebox.showinfo("Успех", f"Ручной контракт «{contract.name}» добавлен")

    def edit_contract_manual(self, name=None):
        if self.is_new:
            return

        if not name:
            selection = self.contracts_tree.selection()
            if not selection:
                messagebox.showwarning("Выбор", "Выберите ручной контракт")
                return
            item = self.contracts_tree.item(selection[0])
            if item['values'][0] != "Ручной":
                return
            name = item['values'][1]

        contract = next((c for c in self.project.manual_contracts if c.name == name), None)
        if not contract:
            messagebox.showerror("Ошибка", "Контракт не найден")
            return

        editor = ContractEditor(self, self.project, contract)
        self.wait_window(editor)

        self.project.modified = datetime.now()
        self.project.save()
        self.refresh_contracts()

    def remove_contract_manual(self):
        selection = self.contracts_tree.selection()
        if not selection:
            messagebox.showwarning("Выбор", "Выберите ручной контракт для удаления")
            return
        item = self.contracts_tree.item(selection[0])
        if item['values'][0] != "Ручной":
            messagebox.showwarning("Ошибка", "Выберите ручной контракт")
            return

        name = item['values'][1]
        if messagebox.askyesno("Удаление", f"Удалить ручной контракт «{name}»?"):
            self.project.manual_contracts = [c for c in self.project.manual_contracts if c.name != name]
            self.project.modified = datetime.now()
            self.project.save()
            self.refresh_contracts()

    def remove_contract(self):
        # Для файловых — заглушка
        messagebox.showinfo("Скоро", "Удаление файловых контрактов будет реализовано позже")

    def calculate_results(self):
        total = self.project.calculate_total_vat_difference()

        for item in self.results_tree.get_children():
            self.results_tree.delete(item)

        all_contracts = self.project.contracts + self.project.manual_contracts
        for contract in all_contracts:
            diff = contract.get_vat_difference()
            self.results_tree.insert('', 'end', values=(contract.name, f"{diff:,.2f}"))

        self.results_tree.insert('', 'end', values=("ИТОГО", f"{total:,.2f}"), tags=('total',))
        self.results_tree.tag_configure('total', background='#e0f0ff', font=('Arial', 10, 'bold'))

        self.result_label.config(text=f"Общая дополнительная стоимость из-за повышения НДС: {total:,.2f} ₽")

    def save_project(self):
        try:
            new_name = self.name_var.get().strip() or "Без имени"
            if new_name != self.project.name:
                self.project.rename_project(new_name)

            self.project.settings['current_vat'] = self.current_vat_var.get()
            self.project.settings['future_vat'] = self.future_vat_var.get()

            self.project.save()
            self.is_new = False
            self.clear_unsaved_flag()
            messagebox.showinfo("Успех", "Проект сохранён")
            self.load_project_data()
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить: {e}")

    def on_close(self):
        if self.is_new:
            if messagebox.askyesno("Новый проект", "Сохранить перед закрытием?"):
                self.save_project()
            self.destroy()
        elif self.unsaved_changes:
            if messagebox.askyesno("Несохранённые изменения", "Сохранить перед закрытием?"):
                self.save_project()
            self.destroy()
        else:
            self.destroy()