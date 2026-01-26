import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from io import BytesIO
import requests
from PIL import Image, ImageTk
from utils.utils import Utils
from controllers.app_controller import AppController

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

        # --- STYLE CONFIGURATION ---
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

        self.resizable(True, True)
        
        self.video_data = None 
        self.last_img_data = None 
        self.image_references = [] 
        
        self._init_ui()
        
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

        # Input
        input_frame = ttk.Labelframe(self.content_frame, text="1. Ingresa el Link", padding=15)
        input_frame.pack(fill=tk.X, padx=20, pady=10)
        self.url_var = tk.StringVar()
        self.entry_url = ttk.Entry(input_frame, textvariable=self.url_var, font=("Segoe UI", 11))
        self.entry_url.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.entry_url.focus()
        self.btn_analizar = ttk.Button(input_frame, text="🔍 ANALIZAR", command=self._on_analizar_click, style="Accent.TButton", width=15)
        self.btn_analizar.pack(side=tk.RIGHT)
        
        self.audio_format_var = tk.StringVar(value="mp3")
        self.video_format_var = tk.StringVar(value="mp4")

        self.dynamic_frame = ttk.Frame(self.content_frame)
        self.dynamic_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Directory
        dir_frame = ttk.Frame(self.content_frame, padding="0 10 0 0")
        dir_frame.pack(fill=tk.X, pady=10, padx=20)
        self.dir_var = tk.StringVar(value=self.controller.get_download_path() or "No seleccionado")
        ttk.Label(dir_frame, text="Guardar en: ", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        ttk.Label(dir_frame, textvariable=self.dir_var, font=("Segoe UI", 9)).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(dir_frame, text="Cambiar", command=self.cambiar_directorio).pack(side=tk.RIGHT)

        # Progress
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.content_frame, variable=self.progress_var, maximum=100, style="Horizontal.TProgressbar")
        self.progress_bar.pack(fill=tk.X, pady=(10, 5), padx=20)
        self.status_var = tk.StringVar(value="Esperando enlace...")
        ttk.Label(self.content_frame, textvariable=self.status_var, font=("Segoe UI", 9), foreground="#666").pack(anchor="w", padx=20, pady=(0, 20))
        
        self.bind_all("<MouseWheel>", self._on_mousewheel)
        
    def _on_analizar_click(self):
        url = self.url_var.get().strip()
        if not url: return
        self.btn_analizar.config(state="disabled")
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
            self.btn_analizar.config(state="normal")
            return
        self._mostrar_opciones_principales()
        self.btn_analizar.config(state="normal")

    def cambiar_directorio(self):
        ruta = filedialog.askdirectory()
        if ruta:
            self.controller.set_download_path(ruta)
            self.dir_var.set(ruta)

    def log_status(self, msg):
        self.status_var.set(msg)
        self.update_idletasks()

    def update_progress(self, val):
        self.progress_var.set(val)
        self.update_idletasks()

    def _limpiar_frame_dinamico(self):
        for widget in self.dynamic_frame.winfo_children():
            widget.destroy()
        self.current_image = None 

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
                self.after(0, update_ui)
        except: pass
            
    def _mostrar_opciones_principales(self):
        self._limpiar_frame_dinamico()
        if not self.video_data: return

        # Preview
        if self.video_data['type'] != 'playlist':
            preview_frame = ttk.Frame(self.dynamic_frame)
            preview_frame.pack(fill=tk.X, pady=(0, 15))
            if self.last_img_data:
                try:
                    self.last_img_data.seek(0)
                    pil_img = Image.open(self.last_img_data)
                    pil_img.thumbnail((160, 90)) 
                    self.current_image = ImageTk.PhotoImage(pil_img)
                    lbl_img = ttk.Label(preview_frame, image=self.current_image)
                    lbl_img.pack(side=tk.LEFT, padx=(0, 10))
                except: ttk.Label(preview_frame, text="[Sin Imagen]").pack(side=tk.LEFT, padx=(0, 10))
            else:
                ttk.Label(preview_frame, text="[Sin Imagen]").pack(side=tk.LEFT, padx=(0, 10))
                
            info_frame = ttk.Frame(preview_frame)
            info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            ttk.Label(info_frame, text=self.video_data['title'], style="Title.TLabel", wraplength=380).pack(anchor="w")
            if self.video_data['type'] != 'playlist':
                ttk.Label(info_frame, text=f"Duración: {self.video_data['duration']}", style="Info.TLabel").pack(anchor="w")
            ttk.Label(info_frame, text=f"Canal: {self.video_data['uploader']}", style="Info.TLabel").pack(anchor="w")

        # Playlist Items
        if self.video_data.get('playlist_items'):
            items = self.video_data['playlist_items']
            if items:
                ttk.Label(self.dynamic_frame, text=f"Selecciona las Canciones ({len(items)}):", font=("Segoe UI", 9, "bold")).pack(fill=tk.X, pady=(10, 5))
                list_container = ttk.Frame(self.dynamic_frame)
                list_container.pack(fill=tk.X, pady=(0, 10)) 
                self.playlist_canvas = tk.Canvas(list_container, height=180, background=self.CTX_BG, highlightthickness=0) 
                scrollbar = ttk.Scrollbar(list_container, orient="vertical", command=self.playlist_canvas.yview, style="Vertical.TScrollbar")
                self.playlist_check_frame = ttk.Frame(self.playlist_canvas)
                self.playlist_check_frame.bind("<Configure>", lambda e: self.playlist_canvas.configure(scrollregion=self.playlist_canvas.bbox("all")))
                self.playlist_canvas.create_window((0, 0), window=self.playlist_check_frame, anchor="nw")
                self.playlist_canvas.configure(yscrollcommand=scrollbar.set)
                
                self.playlist_canvas.bind_all("<MouseWheel>", self._on_mousewheel)
                self.playlist_check_frame.bind("<Destroy>", lambda e: self.playlist_canvas.unbind_all("<MouseWheel>"))
                
                self.playlist_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                
                self.playlist_vars = []
                for i, item in enumerate(items):
                    card = ttk.Frame(self.playlist_check_frame, style="FlatCard.TFrame", padding=(5, 5)) 
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
                    ttk.Label(info_sub, text=f"{i+1}. {item.get('title')}", font=("Segoe UI", 10, "bold"), background=self.CTX_SURFACE, foreground=self.CTX_TEXT).pack(anchor="w", pady=(0, 2))
                    ttk.Label(info_sub, text=f"Duración: {item.get('duration')} - Canal: {item.get('uploader')}", font=("Segoe UI", 8), background=self.CTX_SURFACE, foreground=self.CTX_TEXT_SEC).pack(anchor="w")

                btn_sel_frame = ttk.Frame(self.dynamic_frame)
                btn_sel_frame.pack(fill=tk.X, pady=(0, 20))
                ttk.Button(btn_sel_frame, text="Marcar Todas", width=15, command=self.sel_all).pack(side=tk.LEFT, padx=(0, 10))
                ttk.Button(btn_sel_frame, text="Desmarcar Todas", width=15, command=self.sel_none).pack(side=tk.LEFT)

        # Download Area
        self.btns_container = ttk.Frame(self.dynamic_frame)
        self.btns_container.pack(fill=tk.X, pady=(20, 0))
        self._mostrar_inicio_descarga()

    def _mostrar_inicio_descarga(self):
        for w in self.btns_container.winfo_children(): w.destroy()
        frame_btns = ttk.Frame(self.btns_container)
        frame_btns.pack(fill=tk.X, expand=True)
        ttk.Button(frame_btns, text="🎵 Solo Audio", command=self._mostrar_opciones_audio, style="Accent.TButton").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10), ipady=10)
        ttk.Button(frame_btns, text="🎬 Video Completo", command=self._mostrar_opciones_video, style="Accent.TButton").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0), ipady=10)
        ttk.Button(self.btns_container, text="Limpiar Todo", command=lambda: [self._limpiar_frame_dinamico(), self.url_var.set("")]).pack(pady=20)

    def _mostrar_opciones_audio(self):
        for w in self.btns_container.winfo_children(): w.destroy()
        header = ttk.Frame(self.btns_container)
        header.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(header, text="⬅ Volver", width=10, command=self._mostrar_inicio_descarga).pack(side=tk.LEFT)
        ttk.Label(header, text="Configuración de Audio", font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT, padx=20)
        
        opts_frame = ttk.Frame(self.btns_container, style="FlatCard.TFrame", padding=15)
        opts_frame.pack(fill=tk.X)
        style = ttk.Style()
        style.configure("Surface.TRadiobutton", background=self.CTX_SURFACE, foreground=self.CTX_TEXT, font=("Segoe UI", 10))
        ttk.Radiobutton(opts_frame, text="MP3 (Más compatible)", variable=self.audio_format_var, value="mp3", style="Surface.TRadiobutton").pack(anchor="w", pady=5)
        ttk.Radiobutton(opts_frame, text="Opus (Mejor calidad)", variable=self.audio_format_var, value="opus", style="Surface.TRadiobutton").pack(anchor="w", pady=5)
        
        cmd = lambda: self.iniciar_descarga_final(es_video=False, is_playlist=(self.video_data['type'] == 'playlist'))
        ttk.Button(opts_frame, text="⬇ COMENZAR DESCARGA", command=cmd, style="Accent.TButton").pack(fill=tk.X, pady=(15, 0))

    def _mostrar_opciones_video(self):
        for w in self.btns_container.winfo_children(): w.destroy()
        is_playlist = (self.video_data.get('type') == 'playlist')
        header = ttk.Frame(self.btns_container)
        header.pack(fill=tk.X, pady=(0, 10))
        ttk.Button(header, text="⬅ Volver", width=10, command=self._mostrar_inicio_descarga).pack(side=tk.LEFT)
        title_text = "Configuración de Video (Playlist)" if is_playlist else "Configuración de Video"
        ttk.Label(header, text=title_text, font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT, padx=20)
        
        opts_frame = ttk.Frame(self.btns_container, style="FlatCard.TFrame", padding=15)
        opts_frame.pack(fill=tk.X)
        ttk.Radiobutton(opts_frame, text="MP4 (Más compatible)", variable=self.video_format_var, value="mp4", style="Surface.TRadiobutton").pack(anchor="w", pady=5)
        ttk.Radiobutton(opts_frame, text="VP9/WebM (Mejor calidad)", variable=self.video_format_var, value="webm", style="Surface.TRadiobutton").pack(anchor="w", pady=5)
        
        cmd = lambda: self.iniciar_descarga_final(es_video=True, is_playlist=is_playlist)
        btn_text = "⬇ COMENZAR DESCARGA" if is_playlist else "➜ CONTINUAR"
        ttk.Button(opts_frame, text=btn_text, command=cmd, style="Accent.TButton").pack(fill=tk.X, pady=(15, 0))

    def sel_all(self):
        for var in self.playlist_vars: var.set(1)
    def sel_none(self):
        for var in self.playlist_vars: var.set(0)

    def mostrar_selector_calidad_inline(self, calidades, result_container, event_obj):
        self._limpiar_frame_dinamico()
        video_cont = self.video_format_var.get()
        lbl_c = ttk.Label(self.dynamic_frame, text=f"Calidades Disponibles ({video_cont.upper()})", font=("Segoe UI", 12, "bold"), foreground=self.CTX_ACCENT)
        lbl_c.pack(pady=(0, 10))
        
        canvas = tk.Canvas(self.dynamic_frame, height=250, background=self.CTX_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.dynamic_frame, orient="vertical", command=canvas.yview, style="Vertical.TScrollbar")
        scrollable_frame = ttk.Frame(canvas, style="TFrame")
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=540)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(int(-1*(event.delta/120)), "units"))
        scrollable_frame.bind("<Destroy>", lambda e: canvas.unbind_all("<MouseWheel>"))
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        def seleccionar(fid):
            result_container['fid'] = fid
            event_obj.set()
        
        ordenadas = sorted(calidades.items(), reverse=True)
        style = ttk.Style()
        style.configure("List.TButton", background=self.CTX_SURFACE, foreground="#FFFFFF", font=("Segoe UI", 10), anchor="w", padding=5)
        style.map("List.TButton", background=[('active', '#333333')])

        ttk.Button(scrollable_frame, text="✨ Mejor Calidad (Automático)", command=lambda: seleccionar(None), style="List.TButton").pack(fill='x', pady=1)
        for _, info in ordenadas:
            tam_str = Utils.formatear_tamano(info['tamaño']) if info['tamaño'] else "~"
            btn_text = f"{info['nombre']}  -  {tam_str}"
            ttk.Button(scrollable_frame, text=btn_text, command=lambda fid=info['formato_id']: seleccionar(fid), style="List.TButton").pack(fill='x', pady=1)

    def iniciar_descarga_final(self, es_video, is_playlist=False):
        url = self.url_var.get().strip()
        path = self.dir_var.get()
        if not path or path == "No seleccionado":
            messagebox.showwarning("Error", "Selecciona una carpeta válida primero")
            self.cambiar_directorio()
            return
            
        indices = None
        if is_playlist and hasattr(self, 'playlist_vars'):
            indices = [i for i, var in enumerate(self.playlist_vars) if var.get() == 1]
            if not indices:
                messagebox.showwarning("Atención", "Selecciona al menos una canción.")
                return

        self.btn_analizar.config(state="disabled")
        
        # Check qualities logic for single video here on UI thread (blocking interaction) or spawn thread?
        # The original code spawned a thread `_proceso_descarga_wrapper`.
        threading.Thread(target=self._proceso_descarga_ui_flow, args=(url, path, es_video, is_playlist, indices), daemon=True).start()

    def _proceso_descarga_ui_flow(self, url, path, es_video, is_playlist, indices):
        video_fmt = self.video_format_var.get()
        audio_fmt = self.audio_format_var.get()
        formato_id = None
        
        if es_video and not is_playlist:
            self.log_status("Buscando calidades...")
            calidades = self.controller.get_video_qualities(url, video_fmt)
            if calidades:
                res = {'fid': 'CANCEL'}
                ev = threading.Event()
                self.after(0, self.mostrar_selector_calidad_inline, calidades, res, ev)
                ev.wait()
                formato_id = res['fid']
                if formato_id == 'CANCEL':
                    self.log_status("Cancelado.")
                    self.after(0, self._mostrar_opciones_principales)
                    self.btn_analizar.config(state="normal")
                    return
            else:
                self.log_status("No hay formatos (o error). Usando 'Mejor' por defecto.")
        
        if is_playlist:
            self.after(0, self._limpiar_frame_dinamico)
            def show_status_big():
                ttk.Label(self.dynamic_frame, text="🎵 Descargando Playlist...", font=("Segoe UI", 16, "bold")).pack(expand=True)
                ttk.Label(self.dynamic_frame, text="Por favor espera, procesando...", font=("Segoe UI", 10)).pack(pady=(0, 20))
            self.after(100, show_status_big)
        else:
             self.log_status(f"Descargando...")
             self.after(0, self._limpiar_frame_dinamico)

        def on_finish(success, msg):
            if success:
                self.log_status("✓ ¡Listo! Guardado.")
                self.update_progress(100)
                messagebox.showinfo("Completado", msg)
                self.url_var.set("")
                self.after(0, self._limpiar_frame_dinamico)
            else:
                self.log_status("Error :(")
                messagebox.showerror("Error", f"Falló:\n{msg}")
                self.after(0, self._mostrar_opciones_principales)
                self.update_progress(0)
            self.btn_analizar.config(state="normal")

        self.controller.start_download(
            url=url, path=path, is_video=es_video, 
            audio_fmt=audio_fmt, video_fmt=video_fmt, formato_id=formato_id,
            playlist_indices=indices,
            progress_callback=self.update_progress,
            status_callback=self.log_status,
            finished_callback=on_finish
        )

if __name__ == "__main__":
    app = MainWindow()
    app.mainloop()
