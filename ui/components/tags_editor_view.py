"""
Componente para editar tags de un archivo individual.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk


class TagsEditorView(ttk.Frame):
    """Vista para editar tags de un archivo."""
    
    def __init__(self, parent, on_save, on_back, on_search, style="TFrame"):
        super().__init__(parent, style=style)
        self.on_save = on_save
        self.on_back = on_back
        self.on_search = on_search
        self.entries = {}
        self.archivo_actual = None
    
    def mostrar_editor(self, archivo: dict):
        """Muestra el editor para un archivo."""
        self.archivo_actual = archivo
        
        # Limpiar contenido previo
        for widget in self.winfo_children():
            widget.destroy()
        
        # Crear contenido
        editor_content = ttk.Frame(self, style="TFrame")
        editor_content.pack(fill=tk.BOTH, expand=True)
        
        # Header con botón volver
        header_frame = ttk.Frame(editor_content, style="TFrame")
        header_frame.pack(fill=tk.X, padx=20, pady=(15, 10))
        
        btn_volver = tk.Button(
            header_frame,
            text="← Volver a la lista",
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
            text="✏️ Editar Tags",
            font=("Segoe UI", 16, "bold"),
            foreground="#1DB954",
            background="#121212"
        ).pack(side=tk.LEFT, padx=(20, 0))
        
        # Layout horizontal: Carátula a la izquierda, campos a la derecha
        main_layout = ttk.Frame(editor_content, style="TFrame")
        main_layout.pack(fill=tk.BOTH, expand=True, padx=30, pady=10)
        
        # Frame izquierdo: Carátula + nombre
        left_frame = ttk.Frame(main_layout, style="TFrame")
        left_frame.pack(side=tk.LEFT, padx=(0, 30))
        
        # Carátula
        if archivo.get('caratula'):
            try:
                img = archivo['caratula']
                img_resized = img.resize((200, 200), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img_resized)
                
                lbl_img = ttk.Label(left_frame, image=photo, background="#121212")
                lbl_img.image = photo
                lbl_img.pack()
            except:
                pass
        
        # Nombre del archivo
        ttk.Label(
            left_frame,
            text=archivo['nombre'],
            font=("Segoe UI", 9),
            foreground="#B3B3B3",
            background="#121212",
            wraplength=200,
            justify="center"
        ).pack(pady=(10, 0))
        
        # Frame derecho: Campos en dos columnas
        right_frame = ttk.Frame(main_layout, style="TFrame")
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Columna izquierda
        col_izq = ttk.Frame(right_frame, style="TFrame")
        col_izq.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 15))
        
        # Columna derecha
        col_der = ttk.Frame(right_frame, style="TFrame")
        col_der.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(15, 0))
        
        self.entries = {}
        
        campos_izq = [
            ("titulo", "Título:", archivo.get('titulo', '')),
            ("artista", "Artista:", archivo.get('artista', '')),
            ("album", "Álbum:", archivo.get('album', '')),
            ("genero", "Género:", archivo.get('genero', ''))
        ]
        
        campos_der = [
            ("año", "Año:", archivo.get('año', '')),
            ("track_number", "Número de Pista:", archivo.get('track_number', '')),
            ("disc_number", "Número de Disco:", archivo.get('disc_number', ''))
        ]
        
        # Crear campos columna izquierda
        for key, label, value in campos_izq:
            self._crear_campo(col_izq, key, label, value)
        
        # Crear campos columna derecha
        for key, label, value in campos_der:
            self._crear_campo(col_der, key, label, value)
        
        # Botón buscar metadatos
        search_frame = ttk.Frame(right_frame, style="TFrame")
        search_frame.pack(fill=tk.X, pady=(15, 0))
        
        btn_buscar = tk.Button(
            search_frame,
            text="🔍 Buscar Metadatos",
            font=("Segoe UI", 10, "bold"),
            bg="#282828",
            fg="#1DB954",
            activebackground="#383838",
            cursor="hand2",
            relief="flat",
            padx=20,
            pady=10,
            command=self._buscar_metadatos
        )
        btn_buscar.pack(side=tk.LEFT)
        
        # Botones
        btn_frame = ttk.Frame(right_frame, style="TFrame")
        btn_frame.pack(fill=tk.X, pady=(20, 10))
        
        btn_cancelar = tk.Button(
            btn_frame,
            text="Cancelar",
            font=("Segoe UI", 11),
            bg="#181818",
            fg="#FFFFFF",
            activebackground="#282828",
            cursor="hand2",
            relief="flat",
            padx=30,
            pady=12,
            command=self.on_back
        )
        btn_cancelar.pack(side=tk.LEFT, padx=(0, 10))
        
        btn_guardar = tk.Button(
            btn_frame,
            text="💾 Guardar Cambios",
            font=("Segoe UI", 11, "bold"),
            bg="#1DB954",
            fg="#FFFFFF",
            activebackground="#1ED760",
            cursor="hand2",
            relief="flat",
            padx=30,
            pady=12,
            command=self._guardar
        )
        btn_guardar.pack(side=tk.LEFT)
    
    def _crear_campo(self, parent, key, label, value):
        """Crea un campo de entrada."""
        field_frame = ttk.Frame(parent, style="TFrame")
        field_frame.pack(fill=tk.X, pady=6)
        
        ttk.Label(
            field_frame,
            text=label,
            font=("Segoe UI", 9, "bold"),
            foreground="#FFFFFF",
            background="#121212"
        ).pack(anchor="w", pady=(0, 4))
        
        entry = tk.Entry(
            field_frame,
            font=("Segoe UI", 10),
            bg="#282828",
            fg="#FFFFFF",
            insertbackground="#FFFFFF",
            relief="flat",
            borderwidth=1
        )
        entry.insert(0, str(value) if value else '')
        entry.pack(fill=tk.X, ipady=6)
        
        self.entries[key] = entry
    
    def _buscar_metadatos(self):
        """Llama al callback de búsqueda."""
        if self.on_search:
            self.on_search()
    
    def _guardar(self):
        """Llama al callback de guardar."""
        if self.on_save:
            datos = {key: entry.get().strip() for key, entry in self.entries.items()}
            self.on_save(datos)
    
    def get_datos(self) -> dict:
        """Obtiene los datos actuales del formulario."""
        return {key: entry.get().strip() for key, entry in self.entries.items()}
    
    def set_datos(self, datos: dict):
        """Establece los datos en el formulario."""
        for key, valor in datos.items():
            if key in self.entries:
                self.entries[key].delete(0, tk.END)
                self.entries[key].insert(0, valor if valor else '')
