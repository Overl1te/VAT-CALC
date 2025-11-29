import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import json
from core.config import get_projects_dir, get_current_vat, get_future_vat, CONFIG_FILE

def resource_path(relative_path):
    """Получает путь к ресурсу в bundled-приложении."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def set_icon(root):
    """Устанавливает иконку окна."""
    try:
        icon_path = resource_path("assets/icon.ico")
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
    except:
        pass

class SettingsDialog(tk.Toplevel):
    """
    Диалог настроек приложения.
    """
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Настройки приложения")
        self.geometry("500x400")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self._create_widgets()
        self._load_current_settings()
        set_icon(self)
        self._center_window()

    def _center_window(self):
        """Центрирует окно."""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def _create_widgets(self):
        """Создает UI-элементы диалога."""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill='both', expand=True)

        paths_frame = ttk.LabelFrame(main_frame, text="Пути сохранения", padding="10")
        paths_frame.pack(fill='x', pady=(0, 10))

        ttk.Label(paths_frame, text="Папка проектов:").grid(row=0, column=0, sticky='w', pady=5)
        self.projects_path_var = tk.StringVar()
        ttk.Entry(paths_frame, textvariable=self.projects_path_var, width=50).grid(row=1, column=0, sticky='we', pady=5)
        ttk.Button(paths_frame, text="Обзор...", command=self._browse_projects_folder).grid(row=1, column=1, padx=(5, 0), pady=5)
        paths_frame.columnconfigure(0, weight=1)

        app_frame = ttk.LabelFrame(main_frame, text="Настройки приложения", padding="10")
        app_frame.pack(fill='x', pady=(0, 10))

        ttk.Label(app_frame, text="НДС текущий по умолчанию (%):").grid(row=2, column=0, sticky='w', pady=5)
        self.default_current_vat_var = tk.DoubleVar(value=get_current_vat())
        ttk.Entry(app_frame, textvariable=self.default_current_vat_var, width=10).grid(row=2, column=1, sticky='w', padx=10, pady=5)

        ttk.Label(app_frame, text="НДС будущий по умолчанию (%):").grid(row=3, column=0, sticky='w', pady=5)
        self.default_future_vat_var = tk.DoubleVar(value=get_future_vat())
        ttk.Entry(app_frame, textvariable=self.default_future_vat_var, width=10).grid(row=3, column=1, sticky='w', padx=10, pady=5)

        button_frame = ttk.Frame(main_frame, padding="10")
        button_frame.pack(fill='x')

        ttk.Button(button_frame, text="Сохранить", command=self._save_settings).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Сбросить", command=self._reset_settings).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Закрыть", command=self.destroy).pack(side='right', padx=5)

    def _load_current_settings(self):
        """Загружает текущие настройки из конфига."""
        try:
            if CONFIG_FILE.exists():
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.projects_path_var.set(config.get('projects_dir', str(get_projects_dir()))) 
                self.default_current_vat_var.set(config.get('default_current_vat', get_current_vat())) 
                self.default_future_vat_var.set(config.get('default_future_vat', get_future_vat()))  
            else:
                self.projects_path_var.set(str(get_projects_dir()))  
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить настройки: {e}")
            self.projects_path_var.set(str(get_projects_dir()))  

    def _browse_projects_folder(self):
        """Выбирает папку для проектов."""
        folder = filedialog.askdirectory(title="Выберите папку для сохранения проектов", initialdir=str(get_projects_dir().parent))
        if folder:
            self.projects_path_var.set(folder)

    def _save_settings(self):
        """Сохраняет настройки в конфиг."""
        try:
            # Валидация
            current_vat = self.default_current_vat_var.get()
            future_vat = self.default_future_vat_var.get()
            
            if current_vat <= 0 or future_vat <= 0:
                messagebox.showerror("Ошибка", "Ставки НДС должны быть положительными числами")
                return
            
            if current_vat >= 100 or future_vat >= 100:
                messagebox.showerror("Ошибка", "Ставки НДС указаны в процентах (например, 20 для 20%)")
                return

            # Создаем конфиг
            config = {
                'projects_dir': self.projects_path_var.get(),
                'default_current_vat': current_vat,
                'default_future_vat': future_vat,
            }

            # Сохраняем в файл
            CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)

            messagebox.showinfo("Настройки", "Настройки успешно сохранены!\nДля применения некоторых настроек может потребоваться перезапуск приложения.")
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить настройки: {e}")

    def _reset_settings(self):
        """Сбрасывает настройки к значениям по умолчанию."""
        if messagebox.askyesno("Сброс настроек", "Вернуть все настройки к значениям по умолчанию?"):
            self.default_current_vat_var.set(get_current_vat())
            self.default_future_vat_var.set(get_future_vat()) 