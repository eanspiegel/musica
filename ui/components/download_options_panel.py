import tkinter as tk
from tkinter import ttk

class DownloadOptionsPanel(ttk.Frame):
    def __init__(self, parent, on_audio_click, on_video_click, on_clear_click):
        super().__init__(parent)
        self.on_audio_click = on_audio_click
        self.on_video_click = on_video_click
        self.on_clear_click = on_clear_click
        
        self.audio_format_var = tk.StringVar(value="mp3")
        self.video_format_var = tk.StringVar(value="mp4")
        
        self._show_initial_state()
        
    def _show_initial_state(self):
        for w in self.winfo_children(): w.destroy()
        
        frame_btns = ttk.Frame(self)
        frame_btns.pack(fill=tk.X, expand=True)
        
        ttk.Button(frame_btns, text="🎵 Solo Audio", command=self.on_audio_click, style="Accent.TButton").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), ipady=10)
        ttk.Button(frame_btns, text="🎬 Video Completo", command=self.on_video_click, style="Accent.TButton").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0), ipady=10)
        
        ttk.Button(self, text="Limpiar Todo", command=self.on_clear_click).pack(pady=20)
        
    def show_audio_config(self, on_start_download):
        for w in self.winfo_children(): w.destroy()
        
        header = ttk.Frame(self)
        header.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(header, text="⬅ Volver", width=10, command=self._show_initial_state).pack(side=tk.LEFT)
        ttk.Label(header, text="Configuración de Audio", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT, padx=20)
        
        opts_frame = ttk.Frame(self, style="FlatCard.TFrame", padding=15)
        opts_frame.pack(fill=tk.X)
        
        ttk.Radiobutton(opts_frame, text="MP3 (Más compatible)", variable=self.audio_format_var, value="mp3", style="Surface.TRadiobutton").pack(anchor="w", pady=5)
        ttk.Radiobutton(opts_frame, text="Opus (Mejor calidad)", variable=self.audio_format_var, value="opus", style="Surface.TRadiobutton").pack(anchor="w", pady=5)
        
        ttk.Button(opts_frame, text="⬇ COMENZAR DESCARGA", command=on_start_download, style="Accent.TButton").pack(fill=tk.X, pady=(15, 0))

    def show_video_config(self, is_playlist, on_start_download):
        for w in self.winfo_children(): w.destroy()
        
        header = ttk.Frame(self)
        header.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(header, text="⬅ Volver", width=10, command=self._show_initial_state).pack(side=tk.LEFT)
        title_text = "Configuración de Video (Playlist)" if is_playlist else "Configuración de Video"
        ttk.Label(header, text=title_text, font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT, padx=20)
        
        opts_frame = ttk.Frame(self, style="FlatCard.TFrame", padding=15)
        opts_frame.pack(fill=tk.X)
        
        ttk.Radiobutton(opts_frame, text="MP4 (Más compatible)", variable=self.video_format_var, value="mp4", style="Surface.TRadiobutton").pack(anchor="w", pady=5)
        ttk.Radiobutton(opts_frame, text="VP9/WebM (Mejor calidad)", variable=self.video_format_var, value="webm", style="Surface.TRadiobutton").pack(anchor="w", pady=5)
        
        btn_text = "⬇ COMENZAR DESCARGA" if is_playlist else "➜ CONTINUAR"
        ttk.Button(opts_frame, text=btn_text, command=on_start_download, style="Accent.TButton").pack(fill=tk.X, pady=(15, 0))
        
    def get_audio_format(self):
        return self.audio_format_var.get()
        
    def get_video_format(self):
        return self.video_format_var.get()
