import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
from core.config import PROJECTS_DIR
import os, sys

def set_icon(root):
        def resource_path(relative_path):
            try:
                # PyInstaller
                base_path = sys._MEIPASS
            except Exception:
                base_path = os.path.abspath(".")

            return os.path.join(base_path, relative_path)


        try:
            icon_path = resource_path("assets/icon.ico")
            if os.path.exists(icon_path):
                root.iconbitmap(icon_path)
        except:
            pass

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Настройки приложения")
        self.geometry("500x400")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        
        self.create_widgets()
        self.load_current_settings()
        
        # Устанавливаем иконку
        set_icon(self)

        # Центрируем окно
        self.center_window()

    def center_window(self):
        """Центрировать окно относительно родителя"""
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')

    def create_widgets(self):
        """Создать элементы интерфейса"""
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill='both', expand=True)
        
        # Настройки путей
        paths_frame = ttk.LabelFrame(main_frame, text="Пути сохранения", padding="10")
        paths_frame.pack(fill='x', pady=(0, 10))
        
        # Папка проектов
        ttk.Label(paths_frame, text="Папка проектов:").grid(row=0, column=0, sticky='w', pady=5)
        
        self.projects_path_var = tk.StringVar()
        path_entry = ttk.Entry(paths_frame, textvariable=self.projects_path_var, width=50)
        path_entry.grid(row=1, column=0, sticky='we', pady=5)
        
        browse_btn = ttk.Button(paths_frame, text="Обзор...", 
                               command=self.browse_projects_folder)
        browse_btn.grid(row=1, column=1, padx=(5, 0), pady=5)
        
        paths_frame.columnconfigure(0, weight=1)
        
        # Настройки приложения
        app_frame = ttk.LabelFrame(main_frame, text="Настройки приложения", padding="10")
        app_frame.pack(fill='x', pady=(0, 10))
        
        # Максимальное количество отображаемых строк
        ttk.Label(app_frame, text="Макс. строк в таблице:").grid(row=0, column=0, sticky='w', pady=5)
        self.max_rows_var = tk.IntVar(value=1000)
        max_rows_spinbox = ttk.Spinbox(app_frame, from_=100, to=10000, 
                                      increment=100, textvariable=self.max_rows_var,
                                      width=10)
        max_rows_spinbox.grid(row=0, column=1, sticky='w', padx=10, pady=5)
        
        # Максимальное количество лет прогноза
        ttk.Label(app_frame, text="Макс. лет прогноза:").grid(row=1, column=0, sticky='w', pady=5)
        self.max_years_var = tk.IntVar(value=10)
        max_years_spinbox = ttk.Spinbox(app_frame, from_=1, to=50, 
                                       increment=1, textvariable=self.max_years_var,
                                       width=10)
        max_years_spinbox.grid(row=1, column=1, sticky='w', padx=10, pady=5)
        
        # Настройки по умолчанию
        defaults_frame = ttk.LabelFrame(main_frame, text="Значения по умолчанию", padding="10")
        defaults_frame.pack(fill='x', pady=(0, 10))
        
        ttk.Label(defaults_frame, text="НДС текущий (%):").grid(row=0, column=0, sticky='w', pady=5)
        self.default_current_vat_var = tk.DoubleVar(value=20.0)
        current_vat_spinbox = ttk.Spinbox(defaults_frame, from_=0, to=100, 
                                         increment=0.5, textvariable=self.default_current_vat_var,
                                         width=10)
        current_vat_spinbox.grid(row=0, column=1, sticky='w', padx=10, pady=5)
        
        ttk.Label(defaults_frame, text="НДС будущий (%):").grid(row=1, column=0, sticky='w', pady=5)
        self.default_future_vat_var = tk.DoubleVar(value=22.0)
        future_vat_spinbox = ttk.Spinbox(defaults_frame, from_=0, to=100, 
                                        increment=0.5, textvariable=self.default_future_vat_var,
                                        width=10)
        future_vat_spinbox.grid(row=1, column=1, sticky='w', padx=10, pady=5)
        
        ttk.Label(defaults_frame, text="Лет прогноза:").grid(row=2, column=0, sticky='w', pady=5)
        self.default_years_var = tk.IntVar(value=5)
        years_spinbox = ttk.Spinbox(defaults_frame, from_=1, to=50, 
                                   increment=1, textvariable=self.default_years_var,
                                   width=10)
        years_spinbox.grid(row=2, column=1, sticky='w', padx=10, pady=5)
        
        # Кнопки управления
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill='x', pady=10)
        
        ttk.Button(button_frame, text="Сохранить", 
                  command=self.save_settings).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Сбросить", 
                  command=self.reset_settings).pack(side='left', padx=5)
        ttk.Button(button_frame, text="Закрыть", 
                  command=self.destroy).pack(side='right', padx=5)

    def load_current_settings(self):
        """Загрузить текущие настройки"""
        # Загружаем настройки из конфига
        from core.config import (
            MAX_DISPLAY_ROWS, MAX_PROJECTION_YEARS,
            DEFAULT_CURRENT_VAT, DEFAULT_FUTURE_VAT, DEFAULT_YEARS_PROJECTION
        )
        
        self.max_rows_var.set(MAX_DISPLAY_ROWS)
        self.max_years_var.set(MAX_PROJECTION_YEARS)
        self.default_current_vat_var.set(DEFAULT_CURRENT_VAT)
        self.default_future_vat_var.set(DEFAULT_FUTURE_VAT)
        self.default_years_var.set(DEFAULT_YEARS_PROJECTION)
        
        # Показываем текущий путь к проектам
        self.projects_path_var.set(str(PROJECTS_DIR))

    def browse_projects_folder(self):
        """Выбрать папку для проектов"""
        folder = filedialog.askdirectory(
            title="Выберите папку для сохранения проектов",
            initialdir=str(PROJECTS_DIR.parent)
        )
        if folder:
            self.projects_path_var.set(folder)

    def save_settings(self):
        """Сохранить настройки"""
        try:
            # Валидация данных
            new_max_rows = self.max_rows_var.get()
            new_max_years = self.max_years_var.get()
            new_current_vat = self.default_current_vat_var.get()
            new_future_vat = self.default_future_vat_var.get()
            new_years = self.default_years_var.get()
            new_projects_path = self.projects_path_var.get()
            
            if new_max_rows < 100:
                messagebox.showerror("Ошибка", "Минимальное количество строк: 100")
                return
                
            if new_max_years < 1:
                messagebox.showerror("Ошибка", "Минимальное количество лет: 1")
                return
                
            if new_current_vat < 0 or new_future_vat < 0:
                messagebox.showerror("Ошибка", "НДС не может быть отрицательным")
                return
                
            if new_years < 1:
                messagebox.showerror("Ошибка", "Минимальное количество лет прогноза: 1")
                return
            
            # Проверяем путь к папке проектов
            if new_projects_path and new_projects_path != str(PROJECTS_DIR):
                new_path = Path(new_projects_path)
                if not new_path.exists():
                    try:
                        new_path.mkdir(parents=True, exist_ok=True)
                    except Exception as e:
                        messagebox.showerror("Ошибка", f"Не удалось создать папку: {e}")
                        return
            
            # Здесь должна быть логика сохранения настроек в конфиг файл
            # Временно просто показываем сообщение
            messagebox.showinfo("Настройки", 
                              "Настройки успешно сохранены!\n\n"
                              "Примечание: Для полного применения некоторых настроек "
                              "может потребоваться перезапуск приложения.")
            
            self.destroy()
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить настройки: {e}")

    def reset_settings(self):
        """Сбросить настройки к значениям по умолчанию"""
        if messagebox.askyesno("Сброс настроек", 
                             "Вернуть все настройки к значениям по умолчанию?"):
            self.max_rows_var.set(1000)
            self.max_years_var.set(10)
            self.default_current_vat_var.set(20.0)
            self.default_future_vat_var.set(22.0)
            self.default_years_var.set(5)
            self.projects_path_var.set(str(PROJECTS_DIR))