"""
Componente para mostrar resultados de búsqueda de metadatos.
"""
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from io import BytesIO
import requests
import threading


class SearchResultsView(ttk.Frame):
    """Vista para mostrar resultados de búsqueda de metadatos."""
    
    def __init__(self, parent, on_result_selected, on_back, style="TFrame"):
        super().__init__(parent, style=style)
        self.on_result_selected = on_result_selected
        self.on_back = on_back
        self.image_references = []
    
    def mostrar_resultados(self, resultados: list):
        """Muestra los resultados de búsqueda."""
        # Limpiar contenido previo
        for widget in self.winfo_children():
            widget.destroy()
        
        self.image_references = []
        
        # Contenedor principal
        container = ttk.Frame(self, style="TFrame")
        container.pack(fill=tk.BOTH, expand=True)
        
        # Header
        header_frame = ttk.Frame(container, style="TFrame")
        header_frame.pack(fill=tk.X, padx=20, pady=(15, 10))
        
        btn_volver = tk.Button(
            header_frame,
            text="← Volver al Editor",
            font=("Segoe UI", 10),
            bg="#181818",
            fg="#FFFFFF",
            activebackground="#282828",
            cursor="hand2",
            relief="flat",
            borderwidth=0,
            padx=15,
            pady=8,
            command=self.on_back
        )
        btn_volver.pack(side=tk.LEFT)
        
        ttk.Label(
            header_frame,
            text="🔍 Selecciona la versión correcta:",
            font=("Segoe UI", 16, "bold"),
            foreground="#1DB954",
            background="#121212"
        ).pack(side=tk.LEFT, padx=(20, 0))
        
        # Contador
        ttk.Label(
            container,
            text=f"{len(resultados)} resultado(s) encontrado(s)",
            font=("Segoe UI", 10),
            foreground="#B3B3B3",
            background="#121212"
        ).pack(anchor="w", padx=20, pady=(0, 15))
        
        # Resultados
        resultados_frame = ttk.Frame(container, style="TFrame")
        resultados_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        for resultado in resultados:
            self._crear_card_resultado(resultados_frame, resultado)
    
    def _crear_card_resultado(self, parent, resultado: dict):
        """Crea una card para un resultado de búsqueda."""
        card = ttk.Frame(parent, style="FlatCard.TFrame")
        card.pack(fill=tk.X, pady=5)
        
        # Layout horizontal
        layout = ttk.Frame(card, style="FlatCard.TFrame")
        layout.pack(fill=tk.X, padx=15, pady=10)
        
        # Carátula
        if resultado.get('imagen_url'):
            def cargar_imagen():
                try:
                    img_data = requests.get(resultado['imagen_url'], timeout=5).content
                    img = Image.open(BytesIO(img_data))
                    img_resized = img.resize((80, 80), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img_resized)
                    
                    lbl_img = ttk.Label(layout, image=photo, background="#181818")
                    lbl_img.image = photo
                    self.image_references.append(photo)
                    lbl_img.pack(side=tk.LEFT, padx=(0, 15))
                except:
                    pass
            
            threading.Thread(target=cargar_imagen, daemon=True).start()
        
        # Info
        info_frame = ttk.Frame(layout, style="FlatCard.TFrame")
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Título y tipo
        title_frame = ttk.Frame(info_frame, style="FlatCard.TFrame")
        title_frame.pack(anchor="w")
        
        ttk.Label(
            title_frame,
            text=resultado['titulo'],
            font=("Segoe UI", 11, "bold"),
            foreground="#FFFFFF",
            background="#181818"
        ).pack(side=tk.LEFT)
        
        # Badge de tipo
        tipo_color = "#1DB954" if resultado['tipo'] == "Single" else "#3B82F6"
        ttk.Label(
            title_frame,
            text=f" • {resultado['tipo']}",
            font=("Segoe UI", 9),
            foreground=tipo_color,
            background="#181818"
        ).pack(side=tk.LEFT, padx=(5, 0))
        
        # Artista
        ttk.Label(
            info_frame,
            text=resultado['artista'],
            font=("Segoe UI", 10),
            foreground="#B3B3B3",
            background="#181818"
        ).pack(anchor="w")
        
        # Album y año
        album_text = resultado['album']
        if resultado['año']:
            album_text += f" ({resultado['año']})"
        
        ttk.Label(
            info_frame,
            text=album_text,
            font=("Segoe UI", 9),
            foreground="#888888",
            background="#181818"
        ).pack(anchor="w")
        
        # Fuente
        ttk.Label(
            info_frame,
            text=f"Fuente: {resultado['fuente']}",
            font=("Segoe UI", 8),
            foreground="#666666",
            background="#181818"
        ).pack(anchor="w", pady=(5, 0))
        
        # Botón seleccionar
        btn_seleccionar = tk.Button(
            layout,
            text="Aplicar",
            font=("Segoe UI", 10, "bold"),
            bg="#1DB954",
            fg="#FFFFFF",
            activebackground="#1ED760",
            cursor="hand2",
            relief="flat",
            padx=25,
            pady=10,
            command=lambda: self.on_result_selected(resultado)
        )
        btn_seleccionar.pack(side=tk.RIGHT)
        
        # Hover effect
        def on_enter(e):
            card.configure(style="Hover.TFrame")
            layout.configure(style="Hover.TFrame")
            info_frame.configure(style="Hover.TFrame")
            title_frame.configure(style="Hover.TFrame")
        
        def on_leave(e):
            card.configure(style="FlatCard.TFrame")
            layout.configure(style="FlatCard.TFrame")
            info_frame.configure(style="FlatCard.TFrame")
            title_frame.configure(style="FlatCard.TFrame")
        
        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)
    
    def mostrar_carga(self):
        """Muestra vista de carga."""
        for widget in self.winfo_children():
            widget.destroy()
        
        loading_frame = ttk.Frame(self, style="TFrame")
        loading_frame.pack(expand=True, fill=tk.BOTH, pady=100)
        
        ttk.Label(
            loading_frame,
            text="🔍",
            font=("Segoe UI", 48),
            foreground="#1DB954",
            background="#121212"
        ).pack()
        
        ttk.Label(
            loading_frame,
            text="Buscando metadatos...",
            font=("Segoe UI", 14),
            foreground="#FFFFFF",
            background="#121212"
        ).pack(pady=(10, 0))
