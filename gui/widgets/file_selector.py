import tkinter as tk
from tkinter import filedialog

class FileSelector(tk.Frame):
    """
    Компонент для выбора файла Excel.
    """
    def __init__(self, parent):
        super().__init__(parent)
        tk.Label(self, text='Файл Excel:').pack(side='left')
        self.file_path = tk.StringVar(value='')
        self.entry = tk.Entry(self, textvariable=self.file_path, width=70)
        self.entry.pack(side='left', padx=5)
        tk.Button(self, text='Выбрать...', command=self.browse).pack(side='left')

    def browse(self):
        """Открывает диалог выбора файла."""
        path = filedialog.askopenfilename(filetypes=[('Excel files','*.xlsx;*.xls')])
        if path:
            self.file_path.set(path)