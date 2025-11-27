import tkinter as tk
from tkinter import filedialog, messagebox
from gui.widgets.file_selector import FileSelector
from gui.widgets.results_view import ResultsView
from utils.excel_processor import read_input_excel, write_output_excel
from core.config import DEFAULT_CURRENT_VAT, DEFAULT_FUTURE_VAT, DEFAULT_YEARS_PROJECTION
import threading

def run_app():
    root = tk.Tk()
    root.title('Contract VAT Calculator')
    root.geometry('900x700')

    file_selector = FileSelector(root)
    file_selector.frame.pack(fill='x', padx=10, pady=10)

    controls = tk.Frame(root)
    controls.pack(fill='x', padx=10, pady=5)

    tk.Label(controls, text='Current VAT (%)').grid(row=0, column=0, sticky='w')
    current_vat_var = tk.DoubleVar(value=DEFAULT_CURRENT_VAT)
    current_vat_entry = tk.Entry(controls, textvariable=current_vat_var, width=10)
    current_vat_entry.grid(row=0, column=1, sticky='w', padx=5)

    tk.Label(controls, text='Future VAT (%)').grid(row=0, column=2, sticky='w', padx=(20,0))
    future_vat_var = tk.DoubleVar(value=DEFAULT_FUTURE_VAT)
    future_vat_entry = tk.Entry(controls, textvariable=future_vat_var, width=10)
    future_vat_entry.grid(row=0, column=3, sticky='w', padx=5)

    tk.Label(controls, text='Projection years').grid(row=0, column=4, sticky='w', padx=(20,0))
    years_var = tk.IntVar(value=DEFAULT_YEARS_PROJECTION)
    years_entry = tk.Entry(controls, textvariable=years_var, width=5)
    years_entry.grid(row=0, column=5, sticky='w', padx=5)

    results_view = ResultsView(root)
    results_view.frame.pack(fill='both', expand=True, padx=10, pady=10)

    # Создаем кнопки и сохраняем ссылки
    btns = tk.Frame(root)
    btns.pack(fill='x', padx=10, pady=5)
    
    calculate_btn = tk.Button(btns, text='Рассчитать', command=lambda: calculate_action(calculate_btn))
    calculate_btn.pack(side='left', padx=5)
    
    save_btn = tk.Button(btns, text='Сохранить результат', command=lambda: save_action())
    save_btn.pack(side='left', padx=5)

    def calculate_action(btn):
        """Функция расчета с передачей кнопки для блокировки"""
        path = file_selector.file_path.get()
        if not path:
            messagebox.showwarning('No file', 'Please select an input Excel file.')
            return
        
        # Блокируем кнопку на время расчета
        btn.config(state='disabled')
        root.config(cursor='watch')
        
        def calculate_thread():
            try:
                df = read_input_excel(path)
                current_vat = float(current_vat_var.get())
                future_vat = float(future_vat_var.get())
                years = int(years_var.get())
                
                # Вызываем в основном потоке для обновления GUI
                root.after(0, lambda: finish_calculation(df, current_vat, future_vat, years, btn))
                
            except Exception as e:
                root.after(0, lambda: handle_calculation_error(e, btn))
        
        # Запускаем в отдельном потоке
        threading.Thread(target=calculate_thread, daemon=True).start()

    def finish_calculation(df, current_vat, future_vat, years, btn):
        """Завершение расчета в основном потоке"""
        try:
            results_view.prepare_and_show(df, current_vat, future_vat, years)
        except Exception as e:
            messagebox.showerror('Calculation Error', f'Failed to calculate: {e}')
        finally:
            # Разблокируем кнопку
            btn.config(state='normal')
            root.config(cursor='')

    def handle_calculation_error(error, btn):
        """Обработка ошибок расчета"""
        messagebox.showerror('Error', f'Calculation failed: {error}')
        btn.config(state='normal')
        root.config(cursor='')

    def save_action():
        if getattr(results_view, 'last_output', None) is None:
            messagebox.showwarning('No results', 'Run calculations first.')
            return
        out_path = filedialog.asksaveasfilename(
            defaultextension='.xlsx', 
            filetypes=[('Excel files','*.xlsx')],
            title='Save results as...'
        )
        if not out_path:
            return
        try:
            write_output_excel(results_view.last_output, out_path)
            messagebox.showinfo('Saved', f'Results saved to {out_path}')
        except Exception as e:
            messagebox.showerror('Save error', f'Failed to save: {e}')

    root.mainloop()