import tkinter as tk
from tkinter import filedialog

class FileSelector:
    def __init__(self, parent):
        self.frame = tk.Frame(parent)
        tk.Label(self.frame, text='Input Excel:').pack(side='left')
        self.file_path = tk.StringVar(value='')
        self.entry = tk.Entry(self.frame, textvariable=self.file_path, width=70)
        self.entry.pack(side='left', padx=5)
        tk.Button(self.frame, text='Выбрать...', command=self.browse).pack(side='left')

    def browse(self):
        path = filedialog.askopenfilename(filetypes=[('Excel files','*.xlsx;*.xls')])
        if path:
            self.file_path.set(path)
