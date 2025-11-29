# gui/widgets/project_viewer.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from utils.excel_processor import write_output_excel_simple


class ProjectViewer(tk.Toplevel):
    def __init__(self, parent, project):
        super().__init__(parent)
        self.project = project
        self.title(f"Проект: {project.name} — Экспорт")
        self.geometry("1000x650")
        self._create_widgets()
        self._show_summary()

    def _create_widgets(self):
        # Информация о проекте
        info_frame = ttk.LabelFrame(self, text="Информация о проекте", padding=10)
        info_frame.pack(fill="x", padx=10, pady=10)

        info = f"""
        Название проекта: {self.project.name}
        Создан: {self.project.created.strftime('%d.%m.%Y %H:%M')}
        Изменён: {self.project.modified.strftime('%d.%m.%Y %H:%M')}
        Договоров в проекте: {len(self.project.contracts)}
        """
        ttk.Label(info_frame, text=info.strip(), justify="left", font=("Segoe UI", 10)).pack(anchor="w")

        # Таблица договоров
        table_frame = ttk.Frame(self)
        table_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        columns = ("name", "number", "total", "remain", "diff")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)

        self.tree.heading("name", text="Название договора")
        self.tree.heading("number", text="№ договора")
        self.tree.heading("total", text="Сумма с НДС 20%")
        self.tree.heading("remain", text="Остаток на 31.12.2025")
        self.tree.heading("diff", text="Доп. НДС 22%")

        self.tree.column("name", width=300)
        self.tree.column("number", width=100, anchor="center")
        self.tree.column("total", width=150, anchor="e")
        self.tree.column("remain", width=150, anchor="e")
        self.tree.column("diff", width=150, anchor="e")

        # Скроллбары
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        hsb.pack(side="bottom", fill="x")

        # Кнопки
        btn_frame = ttk.Frame(self)
        btn_frame.pack(fill="x", padx=10, pady=(0, 10))

        ttk.Button(btn_frame, text="Экспорт в Excel", command=self.export_to_excel).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="Закрыть", command=self.destroy).pack(side="right", padx=5)

    def export_to_excel(self):
        default_name = f"{self.project.name.replace(' ', '_')}_доп_НДС_22.xlsx"
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx")],
            initialfile=default_name
        )
        if filename:
            try:
                data = self.project.get_export_data()
                write_output_excel_simple(data, filename)
                messagebox.showinfo("Успех", f"Экспорт завершён!\n{filename}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Не удалось экспортировать:\n{e}")

    def _show_summary(self):
        total_diff = 0.0
        for contract in self.project.contracts:
            diff = contract.get_vat_difference()
            total_diff += diff
            self.tree.insert("", "end", values=(
                contract.name,
                contract.number or "—",
                f"{contract.total_cost_with_vat:,.2f}",
                f"{contract.remaining_cost:,.2f}",
                f"{diff:,.2f}"
            ))

        # Итоговая строка
        self.tree.insert("", "end", values=(
            "ИТОГО", "", "", "", f"{total_diff:,.2f}"
        ), tags=("total",))
        self.tree.tag_configure("total", background="#fff8e1", font=("Segoe UI", 10, "bold"))

        # Заголовок окна с итогом
        self.title(f"Проект: {self.project.name} — Доп. НДС: {total_diff:,.0f} ₽")