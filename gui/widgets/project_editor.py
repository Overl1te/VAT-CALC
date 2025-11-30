# gui/widgets/project_editor.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from datetime import datetime
from core.contracts import Contract
from utils.excel_processor import read_input_excel
from core.project_manager import VATProject
from gui.widgets.settings_dialog import set_icon
from core.config import get_current_vat, get_future_vat
from utils.format import format_money


class ProjectEditor(tk.Toplevel):
    def __init__(self, parent, project_manager, project=None):
        super().__init__(parent)
        self.project_manager = project_manager
        self.project = project or project_manager.create_project_in_memory("Новый проект")
        self.title(f"Проект: {self.project.name}" + (" (новый)" if project is None else ""))
        self.geometry("1540x780")
        self.minsize(1200, 600)

        self.create_widgets()
        self.refresh_contracts()
        set_icon(self)

    def create_widgets(self):
        # === Toolbar ===
        toolbar = ttk.Frame(self)
        toolbar.pack(fill='x', padx=12, pady=8)

        ttk.Label(toolbar, text="Название проекта:", font=('', 10, 'bold')).pack(side='left')
        self.name_var = tk.StringVar(value=self.project.name)
        ttk.Entry(toolbar, textvariable=self.name_var, width=50).pack(side='left', padx=8)
        self.name_var.trace('w', lambda *_: setattr(self.project, 'name', self.name_var.get()))

        ttk.Button(toolbar, text="Сохранить проект", command=self.save_project).pack(side='right', padx=4)
        ttk.Button(toolbar, text="Добавить договор", command=self.add_contract).pack(side='right', padx=4)
        ttk.Button(toolbar, text="Добавить из Excel", command=self.add_from_excel).pack(side='right', padx=4)
        ttk.Button(toolbar, text="Экспорт в Excel", command=self.export_simple_excel).pack(side='right', padx=8)

        # === Treeview ===
        columns = ('checkbox', 'name', 'number', 'total', 'remaining', 'diff', 'without',
                   'vat_now', 'vat_fut', 'diff_with', 'new_cost', 'vat_diff')
        self.tree = ttk.Treeview(self, columns=columns, show='headings', selectmode='browse')
        
        self.tree.heading('checkbox', text="")
        self.tree.heading('name', text='Название')
        self.tree.heading('number', text='№')
        self.tree.heading('total', text='Сумма договора')
        self.tree.heading('remaining', text='Факт 31.12.2025')
        self.tree.heading('diff', text='Остаток на 2026')
        self.tree.heading('without', text='Остаток без НДС')
        self.tree.heading('vat_now', text=f'НДС {int(get_current_vat())}%')
        self.tree.heading('vat_fut', text=f'НДС {int(get_future_vat())}%')
        self.tree.heading('diff_with', text='Остаток с новым НДС')
        self.tree.heading('new_cost', text='Новая стоимость')
        self.tree.heading('vat_diff', text='Доп. НДС')

        self.tree.column('checkbox', width=50, anchor='center')
        self.tree.column('name', width=280)
        self.tree.column('number', width=90, anchor='center')
        self.tree.column('total', width=130, anchor='e')
        self.tree.column('remaining', width=130, anchor='e')
        self.tree.column('diff', width=130, anchor='e')
        self.tree.column('without', width=130, anchor='e')
        self.tree.column('vat_now', width=120, anchor='e')
        self.tree.column('vat_fut', width=120, anchor='e')
        self.tree.column('diff_with', width=140, anchor='e')
        self.tree.column('new_cost', width=140, anchor='e')
        self.tree.column('vat_diff', width=130, anchor='e')

        self.tree.pack(fill='both', expand=True, padx=12, pady=(0, 10))

        self.tree.bind('<Double-1>', self.edit_selected)
        self.tree.bind('<Button-1>', self._on_tree_click)

        # === Нижние итоги ===
        summary_frame = ttk.Frame(self)
        summary_frame.pack(fill='x', padx=12, pady=(10, 15))

        # Левая часть — итоги по всему проекту
        left_frame = ttk.LabelFrame(summary_frame, text=" Итоги по всему проекту ", padding=15)
        left_frame.pack(side='left', fill='x', expand=True)

        self.lbl_total_diff = ttk.Label(left_frame, text="Дополнительный НДС: 0,00 ₽", font=('Segoe UI', 15, 'bold'), foreground='#d32f2f')
        self.lbl_total_diff.pack(anchor='w', pady=4)

        self.lbl_new_cost = ttk.Label(left_frame, text="Новая общая стоимость: 0,00 ₽", font=('Segoe UI', 11))
        self.lbl_new_cost.pack(anchor='w', pady=2)

        self.lbl_without = ttk.Label(left_frame, text="Общая база без НДС: 0,00 ₽", font=('Segoe UI', 10))
        self.lbl_without.pack(anchor='w', pady=2)

        # Правая часть — только отмеченные
        right_frame = ttk.LabelFrame(summary_frame, text=" Только отмеченные договоры ", padding=15)
        right_frame.pack(side='right', fill='x', expand=True)

        self.lbl_checked_diff = ttk.Label(right_frame, text="Доп. НДС: —", font=('Segoe UI', 13, 'bold'), foreground='#1976d2')
        self.lbl_checked_diff.pack(anchor='w', pady=4)

        self.lbl_checked_count = ttk.Label(right_frame, text="Отмечено: 0", font=('Segoe UI', 10))
        self.lbl_checked_count.pack(anchor='w')

    def _on_tree_click(self, event):
        col = self.tree.identify_column(event.x)
        row_id = self.tree.identify_row(event.y)
        if col != '#1' or not row_id:
            return

        index = self.tree.index(row_id)
        contract = self.project.contracts[index]
        contract.is_modified = not contract.is_modified
        self.refresh_contracts()

    def refresh_contracts(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        total_diff = total_new = total_without = 0.0
        checked_diff = checked_count = 0

        for contract in self.project.contracts:
            diff = contract.get_vat_difference()
            without = contract.get_without()
            new_cost = contract.getNewCost()

            total_diff += diff
            total_without += without
            total_new += new_cost

            if contract.is_modified:
                checked_diff += diff
                checked_count += 1

            self.tree.insert('', 'end', values=(
                "✓" if contract.is_modified else "☐",
                contract.name,
                contract.number or "—",
                format_money(contract.total_cost_with_vat) + " ₽",
                format_money(contract.remaining_cost) + " ₽",
                format_money(contract.get_difference()) + " ₽",
                format_money(without) + " ₽",
                format_money(contract.getVAT()) + " ₽",
                format_money(contract.getVATfut()) + " ₽",
                format_money(contract.getDiffWith()) + " ₽",
                format_money(new_cost) + " ₽",
                format_money(diff) + " ₽"
            ))

        # Обновляем итоги
        self.lbl_total_diff.config(text=f"Дополнительный НДС: {format_money(total_diff)} ₽")
        self.lbl_new_cost.config(text=f"Новая общая стоимость: {format_money(total_new)} ₽")
        self.lbl_without.config(text=f"Общая база без НДС: {format_money(total_without)} ₽")

        if checked_count > 0:
            self.lbl_checked_diff.config(text=f"Доп. НДС: {format_money(checked_diff)} ₽")
            self.lbl_checked_count.config(text=f"Отмечено: {checked_count}")
        else:
            self.lbl_checked_diff.config(text="Доп. НДС: —")
            self.lbl_checked_count.config(text="Отмечено: 0")

    def edit_selected(self, event=None):
        selection = self.tree.selection()
        if not selection:
            return
        index = self.tree.index(selection[0])
        contract = self.project.contracts[index]
        self.edit_contract(contract, is_new=False)

    def add_contract(self):
        self.edit_contract(Contract(), is_new=True)

    def edit_contract(self, contract, is_new=False):
        win = tk.Toplevel(self)
        win.title("Редактирование договора" if not is_new else "Новый договор")
        win.geometry("560x420")
        win.resizable(False, False)
        win.transient(self)
        win.grab_set()

        # Основной фрейм с отступами
        main_frame = ttk.Frame(win, padding=20)
        main_frame.pack(fill='both', expand=True)

        # === Поля ввода ===
        ttk.Label(main_frame, text="Название:", font=('', 10, 'bold')).pack(anchor='w', pady=(0,5))
        name_var = tk.StringVar(value=contract.name)
        ttk.Entry(main_frame, textvariable=name_var, width=60).pack(fill='x', pady=(0,10))

        ttk.Label(main_frame, text="№ договора:").pack(anchor='w', pady=(5,5))
        number_var = tk.StringVar(value=contract.number or "")
        ttk.Entry(main_frame, textvariable=number_var, width=60).pack(fill='x', pady=(0,10))

        ttk.Label(main_frame, text="Сумма с НДС (всего по договору):").pack(anchor='w', pady=(5,5))
        total_var = tk.DoubleVar(value=contract.total_cost_with_vat)
        ttk.Entry(main_frame, textvariable=total_var, width=60).pack(fill='x', pady=(0,10))

        ttk.Label(main_frame, text="Факт оплаты на 31.12.2025:").pack(anchor='w', pady=(5,5))
        remain_var = tk.DoubleVar(value=contract.remaining_cost)
        ttk.Entry(main_frame, textvariable=remain_var, width=60).pack(fill='x', pady=(0,15))

        # === Фрейм для кнопок внизу ===
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=(10, 0))

        def save():
            if not name_var.get().strip():
                name_var.set("Договор")
            contract.name = name_var.get().strip()
            contract.number = number_var.get().strip() or None
            contract.total_cost_with_vat = max(0.0, total_var.get())
            contract.remaining_cost = max(0.0, remain_var.get())
            contract.is_modified = True

            if is_new:
                if contract.total_cost_with_vat > 0 or contract.remaining_cost > 0:
                    self.project.contracts.append(contract)
            win.destroy()
            self.refresh_contracts()

        # Кнопка Сохранить — всегда справа
        ttk.Button(button_frame, text="Сохранить", command=save).pack(side='right', padx=(8, 0))

        if is_new:
            ttk.Button(button_frame, text="Отмена", command=win.destroy).pack(side='right')
        else:
            # Кнопка Удалить — слева, красная
            def delete():
                if messagebox.askyesno("Удалить договор", f"Удалить договор «{contract.name}»?\n\nЭто действие нельзя отменить."):
                    if contract in self.project.contracts:
                        self.project.contracts.remove(contract)
                    win.destroy()
                    self.refresh_contracts()

            ttk.Button(button_frame, text="Удалить договор", 
                    style="Danger.TButton", command=delete).pack(side='left')

        # Опционально: добавь красный стиль для кнопки удаления
        style = ttk.Style()
        style.configure("Danger.TButton", foreground="white", background="#d32f2f")
        style.map("Danger.TButton", background=[('active', '#b71c1c')])

        win.protocol("WM_DELETE_WINDOW", win.destroy)
        win.wait_window()

    def add_from_excel(self):
        path = filedialog.askopenfilename(filetypes=[("Excel файлы", "*.xlsx;*.xls")])
        if not path:
            return
        try:
            data = read_input_excel(path)
            added = 0
            for row in data[1:]:
                if len(row) < 5:
                    continue
                c = Contract(
                    name=str(row[0]) if row[0] else "Договор",
                    number=str(row[1]) if len(row) > 1 and row[1] else "",
                    total_cost_with_vat=float(row[3]) if row[3] else 0.0,
                    remaining_cost=float(row[4]) if row[4] else 0.0,
                )
                self.project.contracts.append(c)
                added += 1
            self.project.modified = datetime.now()
            self.refresh_contracts()
            messagebox.showinfo("Готово", f"Добавлено {added} договоров")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось импортировать:\n{e}")

    def save_project(self):
        name = self.name_var.get().strip() or "Без имени"
        self.project.name = name
        self.project.save()
        messagebox.showinfo("Сохранено", f"Проект «{name}» успешно сохранён")
        self.project_manager.projects = VATProject.list_projects()

    def export_simple_excel(self):
        if not self.project.contracts:
            messagebox.showwarning("Пусто", "Нет договоров для экспорта")
            return

        default_name = f"{self.project.name.replace(' ', '_')}.xlsx"
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel файлы", "*.xlsx")],
            initialfile=default_name
        )
        if not filename:
            return

        from utils.excel_processor import write_output_excel_simple
        data = self.project.get_export_data()
        if write_output_excel_simple(data, filename):
            total = sum(c.get_vat_difference() for c in self.project.contracts)
            messagebox.showinfo("Успех", f"Экспорт завершён!\n\nФайл: {filename}\n\nИтого доп. НДС: {format_money(total)} ₽")