import tkinter as tk
from tkinter import ttk, messagebox
from gui.widgets.project_editor import ProjectEditor
from gui.widgets.settings_dialog import SettingsDialog, set_icon

class ProjectBrowser(tk.Frame):
    """
    Браузер проектов для просмотра и управления.
    """
    def __init__(self, parent, project_manager):
        super().__init__(parent)
        self.parent = parent
        self.project_manager = project_manager
        self.project_dict = {}
        self._create_widgets()
        self.refresh_projects()
        set_icon(self)

    def _create_widgets(self):
        """Создает UI-элементы браузера проектов."""
        control_frame = tk.Frame(self)
        control_frame.pack(fill='x', pady=(0, 10))

        ttk.Button(control_frame, text="Создать проект", command=self.create_project).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Обновить", command=self.refresh_projects).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Открыть", command=self.open_selected).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Удалить", command=self.delete_selected).pack(side='left', padx=5)

        settings_btn = ttk.Button(control_frame, text='⚙ Настройки', command=lambda: SettingsDialog(self.parent))
        settings_btn.pack(side='right', padx=5)

        self.tree = ttk.Treeview(self, columns=('name', 'contracts', 'created', 'modified'), show='headings', height=15)
        self.tree.heading('name', text='Название проекта')
        self.tree.heading('contracts', text='договоров')
        self.tree.heading('created', text='Создан')
        self.tree.heading('modified', text='Изменен')
        self.tree.column('name', width=200)
        self.tree.column('contracts', width=80)
        self.tree.column('created', width=150)
        self.tree.column('modified', width=150)
        self.tree.pack(fill='both', expand=True)
        self.tree.bind('<Double-1>', lambda e: self.open_selected())

    def refresh_projects(self):
        """Обновляет список проектов в таблице."""
        self.project_dict.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)

        for project in self.project_manager.projects:
            item_id = self.tree.insert('', 'end', values=(
                project.name,
                len(project.contracts),  # Общее количество договоров
                project.created.strftime('%d.%m.%Y %H:%M'),
                project.modified.strftime('%d.%m.%Y %H:%M')
            ))
            self.project_dict[item_id] = project

    def get_selected_project(self):
        """Возвращает выбранный проект."""
        selection = self.tree.selection()
        if not selection:
            return None
        return self.project_dict.get(selection[0])

    def create_project(self):
        """Создает новый проект."""
        editor = ProjectEditor(self.parent, self.project_manager)
        editor.transient(self.parent)
        editor.grab_set()
        self.parent.wait_window(editor)
        self.refresh_projects()

    def open_selected(self, event=None):
        """Открывает выбранный проект для редактирования."""
        project = self.get_selected_project()
        if project:
            editor = ProjectEditor(self.parent, self.project_manager, project)
            editor.transient(self.parent)
            editor.grab_set()
            self.parent.wait_window(editor)
            self.refresh_projects()

    def delete_selected(self):
        """Удаляет выбранный проект."""
        project = self.get_selected_project()
        if project and messagebox.askyesno("Удаление", f"Удалить проект '{project.name}' со всеми договорами?"):
            self.project_manager.delete_project(project)
            self.refresh_projects()