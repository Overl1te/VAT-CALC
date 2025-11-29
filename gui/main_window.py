import tkinter as tk
from tkinter import ttk
from gui.widgets.project_browser import ProjectBrowser
from core.project_manager import ProjectManager
from gui.widgets.settings_dialog import set_icon

def run_app():
    """
    Запускает основное приложение.
    """
    root = tk.Tk()
    root.title('VAT Calculator - Управление проектами')
    root.geometry('1000x700')

    project_manager = ProjectManager()
    project_browser = ProjectBrowser(root, project_manager)
    project_browser.pack(fill='both', expand=True, padx=10, pady=10)

    set_icon(root)
    root.mainloop()