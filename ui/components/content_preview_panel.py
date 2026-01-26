import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import requests
from io import BytesIO
import threading

class ContentPreviewPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.current_image = None
        self.playlist_vars = []
        
        # We use a dynamic container for the content
        self.container = ttk.Frame(self)
        self.container.pack(fill=tk.BOTH, expand=True)

    def clear(self):
        for widget in self.container.winfo_children():
            widget.destroy()
        self.current_image = None
        self.playlist_vars = []

    def update_content(self, video_data, thumbnail_data=None):
        self.clear()
        if not video_data:
            return

        # 1. Preview Area (Single Video or Playlist Header)
        # Even for playlists, we might want to show the main playlist thumbnail/info if available
        # But based on original code, 'preview_frame' is shown if type != 'playlist'
        
        if video_data['type'] != 'playlist':
            self._show_single_video_preview(video_data, thumbnail_data)

        # 2. Playlist Items
        if video_data.get('playlist_items'):
            self._show_playlist_items(video_data['playlist_items'])

    def _show_single_video_preview(self, video_data, thumbnail_data):
        preview_frame = ttk.Frame(self.container)
        preview_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Image
        if thumbnail_data:
            try:
                thumbnail_data.seek(0)
                pil_img = Image.open(thumbnail_data)
                pil_img.thumbnail((160, 90))
                self.current_image = ImageTk.PhotoImage(pil_img)
                lbl_img = ttk.Label(preview_frame, image=self.current_image)
                lbl_img.pack(side=tk.LEFT, padx=(0, 10))
            except Exception:
                ttk.Label(preview_frame, text="[Sin Imagen]").pack(side=tk.LEFT, padx=(0, 10))
        else:
             ttk.Label(preview_frame, text="[Sin Imagen]").pack(side=tk.LEFT, padx=(0, 10))
             
        # Info
        info_frame = ttk.Frame(preview_frame)
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ttk.Label(info_frame, text=video_data.get('title', 'Unknown'), style="Title.TLabel", wraplength=380).pack(anchor="w")
        ttk.Label(info_frame, text=f"Duración: {video_data.get('duration', '?')}", style="Info.TLabel").pack(anchor="w")
        ttk.Label(info_frame, text=f"Canal: {video_data.get('uploader', 'Unknown')}", style="Info.TLabel").pack(anchor="w")

    def _show_playlist_items(self, items):
        if not items: return
        
        ttk.Label(self.container, text=f"Selecciona las Canciones ({len(items)}):", font=("Segoe UI", 9, "bold")).pack(fill=tk.X, pady=(10, 5))
        
        list_container = ttk.Frame(self.container)
        list_container.pack(fill=tk.X, pady=(0, 10))
        
        # Canvas and Scrollbar for playlist items
        # Note: height=180 matches original code
        canvas = tk.Canvas(list_container, height=180, highlightthickness=0, background="#121212") # BG should match theme, passing hardcoded or configuring style
        # Better to rely on style config or pass bg, but original used self.CTX_BG which was #121212
        # We can try to inherit or set generic. Let's use ".", configure in main.
        
        scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=canvas.yview, style="Vertical.TScrollbar")
        
        playlist_check_frame = ttk.Frame(canvas)
        playlist_check_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        
        canvas_window = canvas.create_window((0, 0), window=playlist_check_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Mousewheel - binding to canvas
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        # Unbind when destroyed to avoid errors if multiple panels
        playlist_check_frame.bind("<Destroy>", lambda e: canvas.unbind_all("<MouseWheel>"))
        # Also need to resize window content
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(canvas_window, width=e.width))

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.playlist_vars = []
        
        # Create items
        CTX_SURFACE = "#181818" # Copied from main_window, ideally passed or styled
        CTX_TEXT = "#FFFFFF"
        CTX_TEXT_SEC = "#B3B3B3"
        
        for i, item in enumerate(items):
            card = ttk.Frame(playlist_check_frame, style="FlatCard.TFrame", padding=(5, 5))
            card.pack(fill=tk.X, expand=True, pady=1)
            
            var = tk.IntVar(value=1)
            self.playlist_vars.append(var)
            
            ttk.Checkbutton(card, variable=var, style="TCheckbutton").pack(side=tk.LEFT, padx=(0, 10))
            
            img_frame = ttk.Frame(card, width=64, height=36)
            img_frame.pack(side=tk.LEFT, padx=(0, 10))
            img_frame.pack_propagate(False)
            
            lbl_thumb = ttk.Label(img_frame, text="...", background="#333", foreground="#888", anchor="center")
            lbl_thumb.pack(fill=tk.BOTH, expand=True)
            
            if item.get('thumbnail'):
                threading.Thread(target=self._cargar_thumbnail_async, args=(item.get('thumbnail'), lbl_thumb), daemon=True).start()
                
            info_sub = ttk.Frame(card, style="FlatCard.TFrame")
            info_sub.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            
            # Using hardcoded colors/fonts here to match original logic, simpler than full style dependency injection for now
            ttk.Label(info_sub, text=f"{i+1}. {item.get('title')}", font=("Segoe UI", 10, "bold"), background=CTX_SURFACE, foreground=CTX_TEXT).pack(anchor="w", pady=(0, 2))
            ttk.Label(info_sub, text=f"Duración: {item.get('duration')} - Canal: {item.get('uploader')}", font=("Segoe UI", 8), background=CTX_SURFACE, foreground=CTX_TEXT_SEC).pack(anchor="w")

        # Buttons for selection
        btn_sel_frame = ttk.Frame(self.container)
        btn_sel_frame.pack(fill=tk.X, pady=(0, 20))
        ttk.Button(btn_sel_frame, text="Marcar Todas", width=15, command=self.sel_all).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_sel_frame, text="Desmarcar Todas", width=15, command=self.sel_none).pack(side=tk.LEFT)

    def _cargar_thumbnail_async(self, url, label_widget):
        try:
            resp = requests.get(url, timeout=5)
            if resp.status_code == 200:
                data = BytesIO(resp.content)
                pil_img = Image.open(data)
                pil_img.thumbnail((64, 36)) 
                tk_img = ImageTk.PhotoImage(pil_img)
                def update_ui():
                    if label_widget.winfo_exists():
                        label_widget.config(image=tk_img, text="")
                        label_widget.image = tk_img 
                label_widget.after(0, update_ui)
        except: pass

    def sel_all(self):
        for var in self.playlist_vars: var.set(1)

    def sel_none(self):
        for var in self.playlist_vars: var.set(0)

    def get_selected_indices(self):
        return [i for i, var in enumerate(self.playlist_vars) if var.get() == 1]
