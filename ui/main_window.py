import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from io import BytesIO
import requests
from PIL import Image, ImageTk

from utils.utils import Utils
from controllers.app_controller import AppController

# Components
from ui.components.input_panel import InputPanel
from ui.components.status_panel import StatusPanel
from ui.components.content_preview_panel import ContentPreviewPanel
from ui.components.download_options_panel import DownloadOptionsPanel
from ui.components.quality_selector_panel import QualitySelectorPanel

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.controller = AppController()
        
        self.title("Descargador de YouTube 🎬")
        self.geometry("600x750")
        
        # --- THEME COLORS (Spotify-like) ---
        self.CTX_BG = "#121212"       
        self.CTX_SURFACE = "#181818"  
        self.CTX_ACCENT = "#1DB954"   
        self.CTX_TEXT = "#FFFFFF"     
        self.CTX_TEXT_SEC = "#B3B3B3" 
        
        self.configure(bg=self.CTX_BG)
        self._init_styles()
        self.resizable(True, True)
        
        self.video_data = None 
        self.last_img_data = None 
        self.image_references = [] 
        
        self._init_ui()
        
    def _init_styles(self):
        style = ttk.Style()
        style.theme_use('clam') 
        style.configure(".", background=self.CTX_BG, foreground=self.CTX_TEXT, font=("Segoe UI", 10))
        style.configure("TFrame", background=self.CTX_BG)
        style.configure("TLabelframe", background=self.CTX_BG, foreground=self.CTX_TEXT, relief="flat")
        style.configure("TLabelframe.Label", background=self.CTX_BG, foreground=self.CTX_TEXT, font=("Segoe UI", 11, "bold"))
        style.configure("TLabel", background=self.CTX_BG, foreground=self.CTX_TEXT)
        style.configure("Title.TLabel", font=("Segoe UI", 12, "bold"), foreground=self.CTX_TEXT)
        style.configure("Info.TLabel", font=("Segoe UI", 9), foreground=self.CTX_TEXT_SEC)
        style.configure("TButton", background=self.CTX_SURFACE, foreground=self.CTX_TEXT, borderwidth=0, focuscolor="none")
        style.map("TButton", background=[('active', '#333333'), ('pressed', '#404040')])
        style.configure("Accent.TButton", background=self.CTX_ACCENT, foreground="#FFFFFF", font=("Segoe UI", 10, "bold"))
        style.map("Accent.TButton", background=[('active', '#1ED760'), ('pressed', '#169C46')])
        style.configure("TEntry", fieldbackground="#333333", foreground="#FFFFFF", borderwidth=0)
        style.configure("FlatCard.TFrame", background=self.CTX_SURFACE)
        style.configure("TCheckbutton", background=self.CTX_SURFACE, foreground=self.CTX_TEXT)
        style.map("TCheckbutton", background=[('active', self.CTX_SURFACE)])
        style.configure("Vertical.TScrollbar", background="#333333", troughcolor=self.CTX_BG, borderwidth=0, arrowcolor="#FFFFFF")
        style.configure("Horizontal.TProgressbar", troughcolor="#333333", background=self.CTX_ACCENT, bordercolor=self.CTX_BG, lightcolor=self.CTX_ACCENT, darkcolor=self.CTX_ACCENT)
        # List.TButton and Surface.TRadiobutton might need config if components don't define them or rely on inheriting
        style.configure("List.TButton", background=self.CTX_SURFACE, foreground="#FFFFFF", font=("Segoe UI", 10), anchor="w", padding=5)
        style.map("List.TButton", background=[('active', '#333333')])
        style.configure("Surface.TRadiobutton", background=self.CTX_SURFACE, foreground=self.CTX_TEXT, font=("Segoe UI", 10))

    def _on_mousewheel(self, event):
        if hasattr(self, 'main_canvas'):
            self.main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")

    def _init_ui(self):
        main_container = ttk.Frame(self)
        main_container.pack(fill=tk.BOTH, expand=True)
        
        self.main_canvas = tk.Canvas(main_container, background=self.CTX_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_container, orient="vertical", command=self.main_canvas.yview, style="Vertical.TScrollbar")
        
        self.content_frame = ttk.Frame(self.main_canvas, style="TFrame")
        self.content_frame.bind("<Configure>", lambda e: self.main_canvas.configure(scrollregion=self.main_canvas.bbox("all")))
        self.canvas_window = self.main_canvas.create_window((0, 0), window=self.content_frame, anchor="nw")
        
        self.main_canvas.configure(yscrollcommand=scrollbar.set)
        self.main_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.main_canvas.bind("<Configure>", lambda e: self.main_canvas.itemconfig(self.canvas_window, width=e.width))

        # Header
        header_frame = ttk.Frame(self.content_frame)
        header_frame.pack(fill=tk.X, pady=(20, 10), padx=20)
        lbl_header = ttk.Label(header_frame, text=f"Descargador {self.controller.get_version()} 🎬", font=("Segoe UI", 18, "bold"))
        lbl_header.pack()

        # Input Panel
        self.input_panel = InputPanel(self.content_frame, self._on_analizar_click)
        self.input_panel.pack(fill=tk.X, padx=20, pady=10)

        # Dynamic Content Area
        self.dynamic_frame = ttk.Frame(self.content_frame)
        self.dynamic_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Directory
        dir_frame = ttk.Frame(self.content_frame, padding="0 10 0 0")
        dir_frame.pack(fill=tk.X, pady=10, padx=20)
        self.dir_var = tk.StringVar(value=self.controller.get_download_path() or "No seleccionado")
        ttk.Label(dir_frame, text="Guardar en: ", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        ttk.Label(dir_frame, textvariable=self.dir_var, font=("Segoe UI", 9)).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(dir_frame, text="Cambiar", command=self.cambiar_directorio).pack(side=tk.RIGHT)

        # Status Panel
        self.status_panel = StatusPanel(self.content_frame)
        self.status_panel.pack(fill=tk.X, side=tk.BOTTOM) # Side bottom relative to content_frame? No content_frame is the window for canvas.
        # But wait, pack side bottom inside content_frame puts it at the bottom of content_frame.

        self.bind_all("<MouseWheel>", self._on_mousewheel)
        
    def _on_analizar_click(self, url):
        self.input_panel.set_state("disabled")
        self.image_references = []
        threading.Thread(target=self._proceso_analisis, args=(url,), daemon=True).start()
        
    def _proceso_analisis(self, url):
        self.video_data, error = self.controller.analyze_url(url)
        self.last_img_data = None
        
        if self.video_data and self.video_data.get('thumbnail'):
            try:
                resp = requests.get(self.video_data['thumbnail'], timeout=10)
                if resp.status_code == 200:
                    self.last_img_data = BytesIO(resp.content)
            except Exception as e:
                print(f"Error descargando thumbnail principal: {e}")
        
        self.after(0, self._post_analisis)

    def _post_analisis(self):
        if not self.video_data:
            messagebox.showerror("Error", "No se pudo obtener la información. Verifica el link.")
            self.input_panel.set_state("normal")
            return
        self._mostrar_opciones_principales()
        self.input_panel.set_state("normal")

    def cambiar_directorio(self):
        ruta = filedialog.askdirectory()
        if ruta:
            self.controller.set_download_path(ruta)
            self.dir_var.set(ruta)

    def _limpiar_frame_dinamico(self):
        for widget in self.dynamic_frame.winfo_children():
            widget.destroy()
        self.content_preview = None
        self.download_options = None

    def _mostrar_opciones_principales(self):
        self._limpiar_frame_dinamico()
        if not self.video_data: return

        # Content Preview
        self.content_preview = ContentPreviewPanel(self.dynamic_frame)
        self.content_preview.pack(fill=tk.X, pady=(0, 0))
        self.content_preview.update_content(self.video_data, self.last_img_data)

        # Download Options
        self.download_options = DownloadOptionsPanel(
            self.dynamic_frame,
            on_audio_click=self._mostrar_opciones_audio,
            on_video_click=self._mostrar_opciones_video,
            on_clear_click=lambda: [self._limpiar_frame_dinamico(), self.input_panel.set_url("")]
        )
        self.download_options.pack(fill=tk.X, pady=(20, 0))

    def _mostrar_opciones_audio(self):
        self.download_options.show_audio_config(
            on_start_download=lambda: self.iniciar_descarga_final(es_video=False, is_playlist=(self.video_data['type'] == 'playlist'))
        )

    def _mostrar_opciones_video(self):
        is_playlist = (self.video_data.get('type') == 'playlist')
        self.download_options.show_video_config(
            is_playlist=is_playlist,
            on_start_download=lambda: self.iniciar_descarga_final(es_video=True, is_playlist=is_playlist)
        )

    def mostrar_selector_calidad_inline(self, calidades, result_container, event_obj, video_fmt_name):
        self._limpiar_frame_dinamico()
        
        def on_select(fid):
            result_container['fid'] = fid
            event_obj.set()
        
        qs = QualitySelectorPanel(self.dynamic_frame, calidades, on_select)
        qs.build(video_fmt_name)
        qs.pack(fill=tk.BOTH, expand=True)

    def iniciar_descarga_final(self, es_video, is_playlist=False):
        url = self.input_panel.get_url()
        path = self.dir_var.get()
        if not path or path == "No seleccionado":
            messagebox.showwarning("Error", "Selecciona una carpeta válida primero")
            self.cambiar_directorio()
            return
            
        indices = None
        if is_playlist and self.content_preview:
            indices = self.content_preview.get_selected_indices()
            if not indices:
                messagebox.showwarning("Atención", "Selecciona al menos una canción.")
                return

        video_fmt = self.download_options.get_video_format() if self.download_options else "mp4"
        audio_fmt = self.download_options.get_audio_format() if self.download_options else "mp3"

        self.input_panel.set_state("disabled")
        threading.Thread(target=self._proceso_descarga_ui_flow, args=(url, path, es_video, is_playlist, indices, video_fmt, audio_fmt), daemon=True).start()

    def _proceso_descarga_ui_flow(self, url, path, es_video, is_playlist, indices, video_fmt, audio_fmt):
        formato_id = None
        
        if es_video and not is_playlist:
            self.status_panel.set_status("Buscando calidades...")
            calidades = self.controller.get_video_qualities(url, video_fmt)
            if calidades:
                res = {'fid': 'CANCEL'}
                ev = threading.Event()
                res = {'fid': 'CANCEL'}
                ev = threading.Event()
                self.after(0, self.mostrar_selector_calidad_inline, calidades, res, ev, video_fmt)
                ev.wait()
                formato_id = res['fid']
                if formato_id == 'CANCEL':
                    self.status_panel.set_status("Cancelado.")
                    self.after(0, self._mostrar_opciones_principales)
                    self.input_panel.set_state("normal")
                    return
            else:
                self.status_panel.set_status("No hay formatos (o error). Usando 'Mejor' por defecto.")
        
        if is_playlist:
            self.after(0, self._limpiar_frame_dinamico)
            def show_status_big():
                ttk.Label(self.dynamic_frame, text="🎵 Descargando Playlist...", font=("Segoe UI", 16, "bold")).pack(expand=True)
                ttk.Label(self.dynamic_frame, text="Por favor espera, procesando...", font=("Segoe UI", 10)).pack(pady=(0, 20))
            self.after(100, show_status_big)
        else:
             self.status_panel.set_status(f"Descargando...")
             self.after(0, self._limpiar_frame_dinamico)

        def on_finish(success, msg):
            if success:
                self.status_panel.set_status("✓ ¡Listo! Guardado.")
                self.status_panel.set_progress(100)
                messagebox.showinfo("Completado", msg)
                self.input_panel.set_url("")
                self.after(0, self._limpiar_frame_dinamico)
            else:
                self.status_panel.set_status("Error :(")
                messagebox.showerror("Error", f"Falló:\n{msg}")
                self.after(0, self._mostrar_opciones_principales)
                self.status_panel.set_progress(0)
            self.input_panel.set_state("normal")

        self.controller.start_download(
            url=url, path=path, is_video=es_video, 
            audio_fmt=audio_fmt, video_fmt=video_fmt, formato_id=formato_id,
            playlist_indices=indices,
            progress_callback=self.status_panel.set_progress,
            status_callback=self.status_panel.set_status,
            finished_callback=on_finish
        )

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
