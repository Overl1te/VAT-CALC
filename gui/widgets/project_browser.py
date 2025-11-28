import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from gui.widgets.project_editor import ProjectEditor
from gui.widgets.settings_dialog import SettingsDialog
from gui.widgets.settings_dialog import set_icon


class ProjectBrowser(tk.Frame):
    def __init__(self, parent, project_manager):
        super().__init__(parent)
        self.parent = parent
        self.project_manager = project_manager
        self.project_dict = {}
        
        # Панель управления - все кнопки в одном фрейме
        control_frame = tk.Frame(self)
        control_frame.pack(fill='x', pady=(0, 10))
        
        # Кнопки слева
        ttk.Button(control_frame, text="Создать проект", 
                  command=self.create_project).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Обновить", 
                  command=self.refresh_projects).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Открыть", 
                  command=self.open_selected).pack(side='left', padx=5)
        ttk.Button(control_frame, text="Удалить", 
                  command=self.delete_selected).pack(side='left', padx=5)
        
        # Кнопка настроек справа
        settings_btn = ttk.Button(control_frame, text='⚙ Настройки', 
                                 command=lambda: SettingsDialog(self.parent))
        settings_btn.pack(side='right', padx=5)
        
        # Таблица проектов
        self.tree = ttk.Treeview(self, columns=('name', 'contracts', 'created', 'modified'), 
                                show='headings', height=15)
        
        self.tree.heading('name', text='Название проекта')
        self.tree.heading('contracts', text='Контрактов')
        self.tree.heading('created', text='Создан')
        self.tree.heading('modified', text='Изменен')
        
        self.tree.column('name', width=200)
        self.tree.column('contracts', width=80)
        self.tree.column('created', width=150)
        self.tree.column('modified', width=150)
        
        self.tree.pack(fill='both', expand=True)
        
        # Двойной клик для открытия
        self.tree.bind('<Double-1>', lambda e: self.open_selected())
        
        self.refresh_projects()

        set_icon(self)
    
    def refresh_projects(self):
        """Обновить список проектов"""
        self.project_dict.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for project in self.project_manager.projects:
            item_id = self.tree.insert('', 'end', values=(
                project.name,
                len(project.contracts),
                project.created.strftime('%d.%m.%Y %H:%M'),
                project.modified.strftime('%d.%m.%Y %H:%M')
            ))
            self.project_dict[item_id] = project
    
    def get_selected_project(self):
        """Получить выбранный проект"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Выбор проекта", "Выберите проект из списка")
            return None
        
        item = selection[0]
        return self.project_dict.get(item)
    
    def create_project(self):
        """Создать новый проект"""
        editor = ProjectEditor(self.parent, self.project_manager)
        editor.transient(self.parent)
        editor.grab_set()
        
        # После закрытия редактора обновляем список
        self.parent.wait_window(editor)
        self.refresh_projects()
    
    def open_selected(self, event=None):
        """Открыть выбранный проект для редактирования"""
        project = self.get_selected_project()
        if project:
            editor = ProjectEditor(self.parent, self.project_manager, project)
            editor.transient(self.parent)
            editor.grab_set()
            
            # После закрытия редактора обновляем список
            self.parent.wait_window(editor)
            self.refresh_projects()
    
    def delete_selected(self):
        """Удалить выбранный проект"""
        project = self.get_selected_project()
        if project and messagebox.askyesno("Удаление", 
                                         f"Удалить проект '{project.name}' со всеми контрактами?"):
            self.project_manager.delete_project(project)
            self.refresh_projects()