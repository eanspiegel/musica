import tkinter as tk
from tkinter import ttk

class InputPanel(ttk.Labelframe):
    def __init__(self, parent, on_analyze_click):
        super().__init__(parent, text="1. Ingresa el Link", padding=15)
        
        self.url_var = tk.StringVar()
        self.on_analyze_click = on_analyze_click
        
        self.entry_url = ttk.Entry(self, textvariable=self.url_var, font=("Segoe UI", 11))
        self.entry_url.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.entry_url.bind("<Return>", lambda e: self._trigger_analyze())
        
        self.btn_analizar = ttk.Button(self, text="🔍 ANALIZAR", command=self._trigger_analyze, style="Accent.TButton", width=15)
        self.btn_analizar.pack(side=tk.RIGHT)
        
    def _trigger_analyze(self):
        url = self.url_var.get().strip()
        if url:
            self.on_analyze_click(url)
            
    def get_url(self):
        return self.url_var.get().strip()
        
    def set_url(self, text):
        self.url_var.set(text)
        
    def set_state(self, state):
        self.btn_analizar.config(state=state)
