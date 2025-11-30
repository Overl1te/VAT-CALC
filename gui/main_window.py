import tkinter as tk
from tkinter import ttk
from gui.widgets.project_browser import ProjectBrowser
from core.project_manager import ProjectManager
from gui.widgets.settings_dialog import set_icon

def run_app():
    root = tk.Tk()
    root.title('VAT Calculator - Управление проектами')
    root.geometry('1200x800')

    # Современная тема
    style = ttk.Style()
    style.theme_use('clam')  # или попробуйте 'vista', 'xpnative'

    # Красивые цвета
    style.configure('TButton', padding=6, font=('Segoe UI', 10))
    style.configure('Treeview', rowheight=28, font=('Segoe UI', 10))
    style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'))
    style.map('Treeview', background=[('selected', '#1976d2')],
                        foreground=[('selected', 'white')])

    # Цветная кнопка "Экспорт"
    style.configure('Accent.TButton', foreground='white', background='#1976d2')
    style.map('Accent.TButton',
              background=[('active', '#1565c0')])

    project_manager = ProjectManager()
    project_browser = ProjectBrowser(root, project_manager)
    project_browser.pack(fill='both', expand=True, padx=10, pady=10)

    set_icon(root)
    root.mainloop()