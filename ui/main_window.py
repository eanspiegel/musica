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
from ui.components.tags_editor_panel import TagsEditorPanel

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.controller = AppController()
        
        self.title("Descargador de YouTube 🎬")
        self.geometry("1000x750")  # Aumentado para mejor visualización
        self.minsize(800, 600)  # Tamaño mínimo
        
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
        self.menu_frame = None
        self.input_panel = None
        self.dir_frame = None
        self.status_panel = None
        self.tags_panel = None
        self.tags_main_frame = None
        
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
        style.configure("Hover.TFrame", background="#282828")  # Efecto hover para filas clickeables
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

        # Menú Principal
        self.current_mode = None  # 'musica', 'video', o 'tags'
        self._mostrar_menu_principal()

        # Dynamic Content Area (oculto inicialmente)
        self.dynamic_frame = ttk.Frame(self.content_frame)
        self.dynamic_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        self.dynamic_frame.pack_forget()  # Ocultar inicialmente

        # Directory
        dir_frame = ttk.Frame(self.content_frame, padding="0 10 0 0")
        dir_frame.pack(fill=tk.X, pady=10, padx=20)
        self.dir_var = tk.StringVar(value=self.controller.get_download_path() or "No seleccionado")
        ttk.Label(dir_frame, text="Guardar en: ", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        ttk.Label(dir_frame, textvariable=self.dir_var, font=("Segoe UI", 9)).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(dir_frame, text="Cambiar", command=self.cambiar_directorio).pack(side=tk.RIGHT)

        # Status Panel
        self.status_panel = StatusPanel(self.content_frame)
    
    def _mostrar_menu_principal(self):
        """Muestra el menú principal con las opciones: Música, Video, Tags"""
        if self.menu_frame:
            self.menu_frame.destroy()
        
        self.menu_frame = ttk.Frame(self.content_frame, style="TFrame")
        self.menu_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Título del menú
        titulo_menu = ttk.Label(
            self.menu_frame, 
            text="Selecciona el Modo", 
            font=("Segoe UI", 16, "bold"),
            foreground=self.CTX_TEXT
        )
        titulo_menu.pack(pady=(20, 30))
        
        # Container para los botones
        botones_container = ttk.Frame(self.menu_frame, style="TFrame")
        botones_container.pack(expand=True)
        
        # Botón Música
        btn_musica = tk.Button(
            botones_container,
            text="🎵 MÚSICA",
            font=("Segoe UI", 14, "bold"),
            bg=self.CTX_ACCENT,
            fg="#FFFFFF",
            activebackground="#1ED760",
            activeforeground="#FFFFFF",
            cursor="hand2",
            relief="flat",
            borderwidth=0,
            padx=40,
            pady=20,
            command=lambda: self._seleccionar_modo('musica')
        )
        btn_musica.pack(pady=10, fill=tk.X, padx=40)
        
        # Botón Video
        btn_video = tk.Button(
            botones_container,
            text="🎬 VIDEO",
            font=("Segoe UI", 14, "bold"),
            bg=self.CTX_SURFACE,
            fg=self.CTX_TEXT,
            activebackground="#333333",
            activeforeground="#FFFFFF",
            cursor="hand2",
            relief="flat",
            borderwidth=0,
            padx=40,
            pady=20,
            command=lambda: self._seleccionar_modo('video')
        )
        btn_video.pack(pady=10, fill=tk.X, padx=40)
        
        # Botón Tags
        btn_tags = tk.Button(
            botones_container,
            text="🏷️ EDITAR TAGS",
            font=("Segoe UI", 14, "bold"),
            bg=self.CTX_SURFACE,
            fg=self.CTX_TEXT,
            activebackground="#333333",
            activeforeground="#FFFFFF",
            cursor="hand2",
            relief="flat",
            borderwidth=0,
            padx=40,
            pady=20,
            command=lambda: self._seleccionar_modo('tags')
        )
        btn_tags.pack(pady=10, fill=tk.X, padx=40)
        
    def _seleccionar_modo(self, modo):
        """Cambiar al modo seleccionado"""
        self.current_mode = modo
        
        # Ocultar menú principal
        if self.menu_frame:
            self.menu_frame.pack_forget()
        
        # Mostrar interfaz según el modo
        if modo in ['musica', 'video']:
            self._mostrar_interfaz_descarga()
        elif modo == 'tags':
            self._mostrar_interfaz_tags()
    
    def _mostrar_interfaz_descarga(self):
        """Muestra la interfaz de descarga (música/video)"""
        # Crear Input Panel si no existe
        if not self.input_panel:
            self.input_panel = InputPanel(self.content_frame, self._on_analizar_click)
        self.input_panel.pack(fill=tk.X, padx=20, pady=10)
        
        # Mostrar dynamic frame
        self.dynamic_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Directory selector
        if not self.dir_frame:
            self.dir_frame = ttk.Frame(self.content_frame, padding="0 10 0 0")
            self.dir_var = tk.StringVar(value=self.controller.get_download_path() or "No seleccionado")
            ttk.Label(self.dir_frame, text="Guardar en: ", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
            ttk.Label(self.dir_frame, textvariable=self.dir_var, font=("Segoe UI", 9)).pack(side=tk.LEFT, fill=tk.X, expand=True)
            ttk.Button(self.dir_frame, text="Cambiar", command=self.cambiar_directorio).pack(side=tk.RIGHT)
        self.dir_frame.pack(fill=tk.X, pady=10, padx=20)
        
        # Status Panel
        if not self.status_panel:
            self.status_panel = StatusPanel(self.content_frame)
        self.status_panel.pack(fill=tk.X, side=tk.BOTTOM)
        
        # Botón volver al menú
        btn_volver = ttk.Button(
            self.content_frame,
            text="← Volver al Menú",
            command=self._volver_menu,
            style="TButton"
        )
        btn_volver.pack(pady=10, padx=20, anchor="w")
        
    def _mostrar_interfaz_tags(self):
        """Muestra la interfaz para editar tags de archivos"""
        # Crear frame para la interfaz de tags
        self.tags_main_frame = ttk.Frame(self.content_frame, style="TFrame")
        self.tags_main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header con título
        header_tags = ttk.Frame(self.tags_main_frame, style="TFrame")
        header_tags.pack(fill=tk.X, pady=(0, 20))
        
        titulo = ttk.Label(
            header_tags,
            text="🏷️ Editor de Tags",
            font=("Segoe UI", 16, "bold")
        )
        titulo.pack(side=tk.LEFT)
        
        # Botón volver (arriba a la derecha)
        btn_volver_header = ttk.Button(
            header_tags,
            text="← Volver al Menú",
            command=self._volver_menu,
            style="TButton"
        )
        btn_volver_header.pack(side=tk.RIGHT)
        
        # Descripción
        desc = ttk.Label(
            self.tags_main_frame,
            text="Selecciona una carpeta para ver y editar los metadatos de los archivos de audio",
            font=("Segoe UI", 10),
            foreground=self.CTX_TEXT_SEC
        )
        desc.pack(pady=(0, 20))
        
        # Botón para seleccionar carpeta
        btn_frame = ttk.Frame(self.tags_main_frame, style="TFrame")
        btn_frame.pack(pady=10)
        
        btn_seleccionar = tk.Button(
            btn_frame,
            text="📁 Seleccionar Carpeta",
            font=("Segoe UI", 12, "bold"),
            bg=self.CTX_ACCENT,
            fg="#FFFFFF",
            activebackground="#1ED760",
            cursor="hand2",
            relief="flat",
            padx=30,
            pady=15,
            command=self._seleccionar_carpeta_tags
        )
        btn_seleccionar.pack()
        
        # Info adicional
        info = ttk.Label(
            self.tags_main_frame,
            text="Formatos soportados: MP3, OPUS, FLAC",
            font=("Segoe UI", 9),
            foreground=self.CTX_TEXT_SEC
        )
        info.pack(pady=(10, 0))
    
    def _seleccionar_carpeta_tags(self):
        """Seleccionar carpeta para ver y editar tags"""
        carpeta = filedialog.askdirectory(
            title="Seleccionar carpeta con archivos de audio"
        )
        
        if carpeta:
            self._mostrar_tags_carpeta(carpeta)
    
    def _mostrar_tags_carpeta(self, carpeta):
        """Muestra los tags de todos los archivos en la carpeta"""
        # Limpiar el frame principal de tags
        if self.tags_main_frame:
            for widget in self.tags_main_frame.winfo_children():
                widget.destroy()
        
        # Header con título y carpeta
        header_tags = ttk.Frame(self.tags_main_frame, style="TFrame")
        header_tags.pack(fill=tk.X, pady=(0, 10))
        
        titulo = ttk.Label(
            header_tags,
            text="🏷️ Editor de Tags",
            font=("Segoe UI", 16, "bold")
        )
        titulo.pack(side=tk.LEFT)
        
        # Botones en header
        btn_container = ttk.Frame(header_tags, style="TFrame")
        btn_container.pack(side=tk.RIGHT)
        
        btn_cambiar = ttk.Button(
            btn_container,
            text="🔄 Cambiar Carpeta",
            command=self._seleccionar_carpeta_tags,
            style="TButton"
        )
        btn_cambiar.pack(side=tk.LEFT, padx=(0, 10))
        
        btn_volver_header = ttk.Button(
            btn_container,
            text="← Volver al Menú",
            command=self._volver_menu,
            style="TButton"
        )
        btn_volver_header.pack(side=tk.LEFT)
        
        # Mostrar ruta de carpeta
        carpeta_label = ttk.Label(
            self.tags_main_frame,
            text=f"📂 {carpeta}",
            font=("Segoe UI", 9),
            foreground=self.CTX_TEXT_SEC
        )
        carpeta_label.pack(anchor="w", pady=(0, 15))
        
        # Crear panel de tags
        self.tags_panel = TagsEditorPanel(self.tags_main_frame)
        self.tags_panel.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Cargar archivos
        self.tags_panel.cargar_archivos(carpeta)
    
    def _volver_menu(self):
        """Volver al menú principal"""
        # Limpiar y ocultar todos los paneles
        if self.input_panel:
            self.input_panel.pack_forget()
        if self.dir_frame:
            self.dir_frame.pack_forget()
        if self.status_panel:
            self.status_panel.pack_forget()
        self.dynamic_frame.pack_forget()
        self._limpiar_frame_dinamico()
        
        # Limpiar cualquier contenido en content_frame excepto el header
        for widget in self.content_frame.winfo_children():
            if widget not in [self.input_panel, self.dir_frame, self.status_panel, self.dynamic_frame]:
                widget.destroy()
        
        # Restaurar el header
        header_frame = ttk.Frame(self.content_frame)
        header_frame.pack(fill=tk.X, pady=(20, 10), padx=20)
        lbl_header = ttk.Label(header_frame, text=f"Descargador {self.controller.get_version()} 🎬", font=("Segoe UI", 18, "bold"))
        lbl_header.pack()
        
        # Mostrar menú principal
        self.current_mode = None
        self._mostrar_menu_principal()
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
        # En modo música, forzar descarga de audio
        es_video_mode = (self.current_mode == 'video')
        self.download_options.show_audio_config(
            on_start_download=lambda: self.iniciar_descarga_final(es_video=es_video_mode, is_playlist=(self.video_data['type'] == 'playlist'))
        )

    def _mostrar_opciones_video(self):
        is_playlist = (self.video_data.get('type') == 'playlist')
        # En modo música, incluso si clickea video, descargar como audio
        es_video_mode = (self.current_mode == 'video')
        self.download_options.show_video_config(
            is_playlist=is_playlist,
            on_start_download=lambda: self.iniciar_descarga_final(es_video=es_video_mode, is_playlist=is_playlist)
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
