from tkinter import ttk

class Theme:
    CTX_BG = "#121212"       
    CTX_SURFACE = "#181818"  
    CTX_ACCENT = "#1DB954"   
    CTX_TEXT = "#FFFFFF"     
    CTX_TEXT_SEC = "#B3B3B3" 

    @staticmethod
    def apply_styles(root):
        root.configure(bg=Theme.CTX_BG)
        
        style = ttk.Style()
        style.theme_use('clam') 
        
        style.configure(".", background=Theme.CTX_BG, foreground=Theme.CTX_TEXT, font=("Segoe UI", 10))
        style.configure("TFrame", background=Theme.CTX_BG)
        style.configure("TLabelframe", background=Theme.CTX_BG, foreground=Theme.CTX_TEXT, relief="flat")
        style.configure("TLabelframe.Label", background=Theme.CTX_BG, foreground=Theme.CTX_TEXT, font=("Segoe UI", 11, "bold"))
        style.configure("TLabel", background=Theme.CTX_BG, foreground=Theme.CTX_TEXT)
        style.configure("Title.TLabel", font=("Segoe UI", 12, "bold"), foreground=Theme.CTX_TEXT)
        style.configure("Info.TLabel", font=("Segoe UI", 9), foreground=Theme.CTX_TEXT_SEC)
        
        style.configure("TButton", background=Theme.CTX_SURFACE, foreground=Theme.CTX_TEXT, borderwidth=0, focuscolor="none")
        style.map("TButton", background=[('active', '#333333'), ('pressed', '#404040')])
        
        style.configure("Accent.TButton", background=Theme.CTX_ACCENT, foreground="#FFFFFF", font=("Segoe UI", 10, "bold"))
        style.map("Accent.TButton", background=[('active', '#1ED760'), ('pressed', '#169C46')])
        
        style.configure("TEntry", fieldbackground="#333333", foreground="#FFFFFF", borderwidth=0)
        style.configure("FlatCard.TFrame", background=Theme.CTX_SURFACE)
        
        style.configure("TCheckbutton", background=Theme.CTX_SURFACE, foreground=Theme.CTX_TEXT)
        style.map("TCheckbutton", background=[('active', Theme.CTX_SURFACE)])
        
        style.configure("Vertical.TScrollbar", background="#333333", troughcolor=Theme.CTX_BG, borderwidth=0, arrowcolor="#FFFFFF")
        style.configure("Horizontal.TProgressbar", troughcolor="#333333", background=Theme.CTX_ACCENT, bordercolor=Theme.CTX_BG, lightcolor=Theme.CTX_ACCENT, darkcolor=Theme.CTX_ACCENT)
        
        style.configure("Surface.TRadiobutton", background=Theme.CTX_SURFACE, foreground=Theme.CTX_TEXT, font=("Segoe UI", 10))
        
        # List buttons for quality selector
        style.configure("List.TButton", background=Theme.CTX_SURFACE, foreground="#FFFFFF", font=("Segoe UI", 10), anchor="w", padding=5)
        style.map("List.TButton", background=[('active', '#333333')])
