import tkinter as tk
from tkinter import ttk

class StatusPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self, variable=self.progress_var, maximum=100, style="Horizontal.TProgressbar")
        self.progress_bar.pack(fill=tk.X, pady=(10, 5), padx=20)
        
        self.status_var = tk.StringVar(value="Esperando enlace...")
        self.lbl_status = ttk.Label(self, textvariable=self.status_var, font=("Segoe UI", 9), foreground="#666")
        self.lbl_status.pack(anchor="w", padx=20, pady=(0, 20))
        
    def set_status(self, msg):
        self.status_var.set(msg)
        self.update_idletasks()
        
    def set_progress(self, val):
        self.progress_var.set(val)
        self.update_idletasks()
