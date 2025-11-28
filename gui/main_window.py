import tkinter as tk
from tkinter import ttk
from gui.widgets.project_browser import ProjectBrowser
from core.project_manager import ProjectManager

def run_app():
    root = tk.Tk()
    root.title('VAT Calculator - Управление проектами')
    root.geometry('1000x700')
    
    # Установка иконки (если есть)
    try:
        root.iconbitmap('assets/icon.ico')
    except:
        pass

    # Менеджер проектов
    project_manager = ProjectManager()

    # Основной интерфейс - только управление проектами
    project_browser = ProjectBrowser(root, project_manager)
    project_browser.pack(fill='both', expand=True, padx=10, pady=10)

    root.mainloop()