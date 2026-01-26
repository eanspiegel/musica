import tkinter as tk
from tkinter import ttk
from utils.utils import Utils

class QualitySelectorPanel(ttk.Frame):
    def __init__(self, parent, qualities, on_select):
        super().__init__(parent)
        self.qualities = qualities
        self.on_select = on_select
        self._init_ui()
        
    def _init_ui(self):
        # We need the format name to display in title (e.g. MP4)
        # Taking it from the first item or passing it? 
        # The original code did: video_cont = self.video_format_var.get()
        # We can try to infer or pass it as arg. Let's pass 'video_format' arg.
        # For now, I'll just show "Calidades Disponibles" or infer from first key if needed, 
        # but to keep it simple and match original I might need to pass the format string if I want the exact title.
        pass

    def build(self, video_format_name=""):
        # Header
        lbl_c = ttk.Label(self, text=f"Calidades Disponibles ({video_format_name.upper()})", font=("Segoe UI", 12, "bold"), foreground="#1DB954")
        lbl_c.pack(pady=(0, 10))
        
        # Scrollable Area
        canvas = tk.Canvas(self, height=250, background="#121212", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview, style="Vertical.TScrollbar")
        scrollable_frame = ttk.Frame(canvas, style="TFrame")
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=540) # Width hardcoded in original
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Mousewheel
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        scrollable_frame.bind("<Destroy>", lambda e: canvas.unbind_all("<MouseWheel>"))
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Buttons
        ordenadas = sorted(self.qualities.items(), reverse=True)
        
        # Auto/Best Button
        ttk.Button(scrollable_frame, text="✨ Mejor Calidad (Automático)", 
                  command=lambda: self.on_select(None), 
                  style="List.TButton").pack(fill='x', pady=1)
                  
        # Individual Qualities
        for _, info in ordenadas:
            tam_str = Utils.formatear_tamano(info['tamaño']) if info['tamaño'] else "~"
            btn_text = f"{info['nombre']}  -  {tam_str}"
            fid = info['formato_id']
            ttk.Button(scrollable_frame, text=btn_text, 
                      command=lambda f=fid: self.on_select(f), 
                      style="List.TButton").pack(fill='x', pady=1)
