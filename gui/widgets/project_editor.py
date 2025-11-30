# gui/widgets/project_editor.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from core.contracts import Contract
from utils.excel_processor import read_input_excel
from core.project_manager import VATProject
from gui.widgets.settings_dialog import set_icon

class ProjectEditor(tk.Toplevel):
    def __init__(self, parent, project_manager, project=None):
        super().__init__(parent)
        self.project_manager = project_manager
        self.project = project or project_manager.create_project_in_memory("Новый проект")
        self.title(f"Проект: {self.project.name}" + (" (новый)" if project is None else ""))
        self.geometry("1320x700")
        self.create_widgets()
        self.refresh_contracts()

        set_icon(self)

    def create_widgets(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill='x', padx=10, pady=5)

        ttk.Label(toolbar, text="Название проекта:", font=('', 10, 'bold')).pack(side='left')
        self.name_var = tk.StringVar(value=self.project.name)
        ttk.Entry(toolbar, textvariable=self.name_var, width=50).pack(side='left', padx=5)
        self.name_var.trace('w', lambda *_: setattr(self.project, 'name', self.name_var.get()))

        ttk.Button(toolbar, text="Сохранить проект", command=self.save_project).pack(side='right', padx=5)
        ttk.Button(toolbar, text="Добавить договор", command=self.add_contract).pack(side='right', padx=5)
        ttk.Button(toolbar, text="Добавить из Excel", command=self.add_from_excel).pack(side='right', padx=5)
        export_btn = ttk.Button(toolbar, text="Экспорт в Excel", command=self.export_simple_excel)
        export_btn.pack(side='right', padx=8)

        columns = ('name', 'number', 'total', 'remaining', 'diff', 'without', 'vat_now', 'vat_fut', 'diff_with', 'vat_diff')
        self.tree = ttk.Treeview(self, columns=columns, show='headings', height=25)

        self.tree.heading('name', text='Название')
        self.tree.heading('number', text='№')
        self.tree.heading('total', text='Сумма')
        self.tree.heading('remaining', text='Факт 31.12.2025')
        self.tree.heading('diff', text='Остаток')
        self.tree.heading('without', text='Остаток без НДС')
        self.tree.heading('vat_now', text='Текущий НДС')
        self.tree.heading('vat_fut', text='Будущий НДС')
        self.tree.heading('diff_with',text='Остаток с будущим НДС')
        self.tree.heading('vat_diff', text='Разница')

        self.tree.column('name', width=100)
        self.tree.column('number', width=80, anchor='center')
        self.tree.column('total', width=110, anchor='e')
        self.tree.column('remaining', width=110, anchor='e')
        self.tree.column('diff', width=110, anchor='e')
        self.tree.column('without', width=110, anchor='e')
        self.tree.column('vat_now', width=110, anchor='e')
        self.tree.column('vat_fut', width=110, anchor='e')
        self.tree.column('diff_with', width=120, anchor='e')
        self.tree.column('vat_diff', width=100, anchor='e')

        self.tree.pack(fill='both', expand=True, padx=10, pady=10)
        self.tree.bind('<Double-1>', self.edit_selected)

        self.total_label = ttk.Label(self, text="", font=('', 12, 'bold'), foreground='#d32f2f')
        self.total_label.pack(pady=10)

    def refresh_contracts(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        total = 0.0
        for c in self.project.contracts:
            diff = c.get_difference()
            vat_now = c.getVAT()
            without = c.get_without()
            vat_fut = c.getVATfut()
            diff_with = c.getDiffWith()
            vat_diff = c.get_vat_difference()
            total += vat_diff
            self.tree.insert('', 'end', values=(
                c.name,
                c.number or "—",
                f"{c.total_cost_with_vat:,.2f}",
                f"{c.remaining_cost:,.2f}",
                f"{diff:,.2f}",
                f"{without:,.2f}",
                f"{vat_now:,.2f}",
                f"{vat_fut:,.2f}",
                f"{diff_with:,.2f}",
                f"{vat_diff:,.2f}"
            ))
        self.total_label.config(text=f"ИТОГО дополнительный НДС: {total:,.2f} ₽")

    def add_contract(self):
        c = Contract()
        self.edit_contract(c, is_new=True)

    def edit_selected(self, event=None):
        sel = self.tree.selection()
        if not sel: return
        idx = self.tree.index(sel[0])
        self.edit_contract(self.project.contracts[idx], is_new=False)  # Явно указываем, что это не новый договор
        self.refresh_contracts()

    def edit_contract(self, contract: Contract, is_new=False):
        win = tk.Toplevel(self)
        win.title("Договор" + (" (новый)" if is_new else ""))
        win.geometry("500x420")
        win.transient(self)
        win.grab_set()

        set_icon(win)

        def entry(label, var):
            ttk.Label(win, text=label).pack(anchor='w', padx=20, pady=2)
            e = ttk.Entry(win, textvariable=var, width=60)
            e.pack(padx=20, pady=2)
            return e

        name_var = tk.StringVar(value=contract.name)
        num_var = tk.StringVar(value=contract.number)
        total_var = tk.DoubleVar(value=contract.total_cost_with_vat)
        remain_var = tk.DoubleVar(value=contract.remaining_cost)

        entry("Название:", name_var)
        entry("№ договора:", num_var)
        entry("Сумма договора:", total_var)
        ttk.Label(win, text="Факт на 31.12.2025:").pack(anchor='w', padx=20, pady=2)
        ttk.Entry(win, textvariable=remain_var, width=60).pack(padx=20, pady=2)

        def save():
            contract.name = name_var.get() or "Договор"
            contract.number = num_var.get()
            contract.total_cost_with_vat = max(0, total_var.get())
            contract.remaining_cost = max(0, remain_var.get())
            
            # Добавляем договор в проект только если он новый
            if is_new and (contract.total_cost_with_vat or contract.remaining_cost):
                self.project.contracts.append(contract)
            
            win.destroy()
            self.refresh_contracts()

        def cancel():
            win.destroy()
            # Если это новый договор и пользователь отменил создание, ничего не делаем

        ttk.Button(win, text="Сохранить", command=save).pack(pady=15)
        
        # Для новых договоров показываем кнопку "Отмена", для существующих - "Удалить"
        if is_new:
            ttk.Button(win, text="Отмена", command=cancel).pack(pady=5)
        else:
            ttk.Button(win, text="Удалить договор", style="Danger.TButton",
                    command=lambda: [self.project.contracts.remove(contract), win.destroy(), self.refresh_contracts()]
                    if messagebox.askyesno("Удалить", "Удалить этот договор?") else None).pack(pady=5)

    def add_from_excel(self):
        path = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx;*.xls")])
        if not path: return
        try:
            data = read_input_excel(path)
            added = 0
            for row in data[1:]:
                if len(row) < 5: continue
                c = Contract(
                    name=str(row[0]) if row[0] else "Договор",  
                    number=str(row[1]) if len(row) > 1 else "",
                    total_cost_with_vat=float(row[3]) if row[3] else 0,
                    remaining_cost=float(row[4]) if row[4] else 0,
                )
                self.project.contracts.append(c)
                added += 1
            self.project.modified = datetime.now()
            self.refresh_contracts()
            messagebox.showinfo("Готово", f"Добавлено: {added} договоров")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def save_project(self):
        name = self.name_var.get().strip() or "Без имени"
        self.project.name = name
        self.project.save()
        messagebox.showinfo("Сохранено", f"Проект «{name}» сохранён")
        self.project_manager.projects = VATProject.list_projects()

    def export_simple_excel(self):
        """Экспорт проекта в Excel — одна строка на договор + итог"""
        if not self.project.contracts:
            messagebox.showwarning("Пустой проект", "В проекте нет договоров для экспорта")
            return

        try:
            # Формируем данные
            data = self.project.get_export_data()
            
            # Диалог сохранения
            default_name = f"{self.project.name}.xlsx"
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                initialfile=default_name,
                title="Экспорт проекта в Excel"
            )
            if not filename:
                return

            from utils.excel_processor import write_output_excel_simple
            success = write_output_excel_simple(data, filename)
            
            if success:
                total_diff = sum(contract.get_vat_difference() for contract in self.project.contracts)
                messagebox.showinfo(
                    "Готово!",
                    f"Проект успешно экспортирован!\n\n"
                    f"Файл: {filename}\n"
                    f"Итого доп. НДС: {total_diff:,.0f} ₽"
                )
            else:
                messagebox.showerror("Ошибка экспорта", "Не удалось сохранить файл Excel")

        except Exception as e:
            messagebox.showerror("Ошибка экспорта", f"Произошла ошибка: {str(e)}")