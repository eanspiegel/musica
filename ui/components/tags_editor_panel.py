"""
Panel principal para editar tags de archivos de audio.
Componente ligero que coordina las vistas.
"""
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
import threading
from controllers.tags_controller import TagsController
from ui.components.tags_editor_view import TagsEditorView
from ui.components.search_results_view import SearchResultsView


class TagsEditorPanel(ttk.Frame):
    """Panel para mostrar y editar tags de archivos de audio."""
    
    def __init__(self, parent, on_save_callback=None):
        super().__init__(parent, style="TFrame")
        self.on_save_callback = on_save_callback
        self.controller = TagsController()
        
        self.archivos_data = []
        self.selected_file = None
        self.image_references = []
        self.carpeta_actual = None
        self.datos_editor_temp = {}
        
        self._init_ui()
    
    def _init_ui(self):
        """Inicializa la UI."""
        # Contenedor principal con canvas y scrollbar
        self.main_container = ttk.Frame(self, style="TFrame")
        self.main_container.pack(fill=tk.BOTH, expand=True)
        
        # Canvas y Scrollbar
        self.canvas = tk.Canvas(self.main_container, background="#121212", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.main_container, orient="vertical", command=self.canvas.yview)
        
        self.scrollable_frame = ttk.Frame(self.canvas, style="TFrame")
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # Ajustar ancho del scrollable_frame
        self.canvas.bind('<Configure>', self._on_canvas_configure)
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Bind mousewheel
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
    
    def _on_canvas_configure(self, event):
        """Ajusta el ancho del scrollable_frame al ancho del canvas."""
        canvas_width = event.width
        self.canvas.itemconfig(self.canvas_window, width=canvas_width)
    
    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    
    def cargar_archivos(self, carpeta: str):
        """Carga todos los archivos de audio de una carpeta."""
        self.carpeta_actual = carpeta
        self.archivos_data = self.controller.cargar_archivos_carpeta(carpeta)
        self._mostrar_lista()
    
    def _mostrar_lista(self):
        """Muestra la lista de archivos."""
        # Limpiar
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self.image_references = []
        
        # Contenedor
        container = ttk.Frame(self.scrollable_frame, style="TFrame")
        container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Header
        ttk.Label(
            container,
            text="🏷️ Archivos de Audio",
            font=("Segoe UI", 16, "bold"),
            foreground="#1DB954",
            background="#121212"
        ).pack(anchor="w", pady=(0, 20))
        
        # Tabla
        tabla_frame = ttk.Frame(container, style="TFrame")
        tabla_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configurar grid
        tabla_frame.columnconfigure(0, weight=1)
        
        # Headers
        headers = ["", "#", "Título", "Artista", "Álbum", "Año", "Género", "Track", "Disc"]
        weights = [0, 0, 5, 3, 4, 1, 2, 0, 0]
        minsizes = [60, 40, 200, 150, 180, 60, 100, 50, 50]
        
        header_row = ttk.Frame(tabla_frame, style="TFrame")
        header_row.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        
        for col, (header, weight, minsize) in enumerate(zip(headers, weights, minsizes)):
            header_row.columnconfigure(col, weight=weight, minsize=minsize)
            lbl = ttk.Label(
                header_row,
                text=header,
                font=("Segoe UI", 9, "bold"),
                foreground="#1DB954",
                anchor="w"
            )
            lbl.grid(row=0, column=col, sticky="ew", padx=5)
        
        # Archivos
        for idx, archivo in enumerate(self.archivos_data, 1):
            self._crear_fila_archivo(idx, archivo, tabla_frame)
    
    def _crear_fila_archivo(self, idx: int, archivo: dict, parent):
        """Crea una fila para mostrar un archivo."""
        fila = ttk.Frame(parent, style="FlatCard.TFrame")
        fila.grid(row=idx, column=0, sticky="ew", padx=0, pady=2)
        
        # Configurar columnas
        for col, weight in enumerate([0, 0, 5, 3, 4, 1, 2, 0, 0]):
            fila.columnconfigure(col, weight=weight)
        
        # Carátula
        if archivo.get('caratula'):
            try:
                img = archivo['caratula']
                img_resized = img.resize((50, 50), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img_resized)
                self.image_references.append(photo)
                
                lbl_img = ttk.Label(fila, image=photo, background="#181818")
                lbl_img.grid(row=0, column=0, sticky="w", padx=5, pady=2)
            except:
                self._crear_placeholder(fila, 0)
        else:
            self._crear_placeholder(fila, 0)
        
        # Datos
        valores = [
            str(idx),
            archivo['titulo'] or archivo['nombre'],
            archivo['artista'] or '-',
            archivo['album'] or '-',
            archivo['año'] or '-',
            archivo['genero'] or '-',
            archivo['track_number'] or '-',
            archivo['disc_number'] or '-'
        ]
        
        for col_offset, valor in enumerate(valores):
            col = col_offset + 1
            lbl = ttk.Label(
                fila,
                text=str(valor)[:50],  # Limitar longitud
                font=("Segoe UI", 9),
                foreground="#FFFFFF",
                anchor="w"
            )
            lbl.grid(row=0, column=col, sticky="ew", padx=5)
        
        # Hover y click
        def on_enter(e):
            fila.configure(style="Hover.TFrame")
        
        def on_leave(e):
            fila.configure(style="FlatCard.TFrame")
        
        fila.bind("<Enter>", on_enter)
        fila.bind("<Leave>", on_leave)
        fila.bind("<Button-1>", lambda e, a=archivo: self._seleccionar_archivo(a))
        
        for child in fila.winfo_children():
            child.bind("<Enter>", on_enter)
            child.bind("<Leave>", on_leave)
            child.bind("<Button-1>", lambda e, a=archivo: self._seleccionar_archivo(a))
    
    def _crear_placeholder(self, parent, col):
        """Crea un placeholder para carátula."""
        lbl_placeholder = ttk.Label(
            parent,
            text="🎵",
            font=("Segoe UI", 20),
            foreground="#B3B3B3",
            background="#181818"
        )
        lbl_placeholder.grid(row=0, column=col, sticky="w", padx=5, pady=2)
    
    def _seleccionar_archivo(self, archivo: dict):
        """Muestra el editor para un archivo."""
        self.selected_file = archivo
        self._mostrar_editor()
    
    def _mostrar_editor(self):
        """Muestra la vista de edición."""
        # Limpiar
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        # Crear vista de editor
        self.editor_view = TagsEditorView(
            self.scrollable_frame,
            on_save=self._guardar_cambios,
            on_back=self._volver_lista,
            on_search=self._buscar_metadatos
        )
        self.editor_view.pack(fill=tk.BOTH, expand=True)
        self.editor_view.mostrar_editor(self.selected_file)
    
    def _volver_lista(self):
        """Vuelve a la lista de archivos."""
        self.selected_file = None
        if self.carpeta_actual:
            self.cargar_archivos(self.carpeta_actual)
    
    def _guardar_cambios(self, datos: dict):
        """Guarda los cambios en el archivo."""
        if not self.selected_file:
            return
        
        try:
            ruta = self.selected_file['ruta']
            imagen_data = self.selected_file.get('imagen_temp')
            
            exito = self.controller.guardar_metadata(ruta, datos, imagen_data)
            
            if exito:
                messagebox.showinfo("Éxito", "Cambios guardados correctamente")
                self._volver_lista()
            else:
                messagebox.showerror("Error", "No se pudieron guardar los cambios")
        
        except Exception as e:
            messagebox.showerror("Error", f"Error guardando cambios:\n{e}")
    
    def _buscar_metadatos(self):
        """Busca metadatos en línea."""
        if not hasattr(self, 'editor_view'):
            return
        
        datos = self.editor_view.get_datos()
        titulo = datos.get('titulo', '')
        artista = datos.get('artista', '')
        
        if not titulo:
            messagebox.showwarning("Advertencia", "Por favor ingresa un título para buscar")
            return
        
        # Guardar datos actuales
        self.datos_editor_temp = datos
        
        # Mostrar vista de carga
        self._mostrar_busqueda_loading()
        
        # Buscar en thread
        def buscar_thread():
            ruta_archivo = self.selected_file.get('ruta') if self.selected_file else None
            resultados = self.controller.buscar_metadatos(titulo, artista, ruta_archivo)
            self.after(0, lambda: self._mostrar_resultados_busqueda(resultados))
        
        threading.Thread(target=buscar_thread, daemon=True).start()
    
    def _mostrar_busqueda_loading(self):
        """Muestra vista de carga."""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        
        self.search_view = SearchResultsView(
            self.scrollable_frame,
            on_result_selected=self._aplicar_resultado,
            on_back=self._volver_a_editor
        )
        self.search_view.pack(fill=tk.BOTH, expand=True)
        self.search_view.mostrar_carga()
    
    def _mostrar_resultados_busqueda(self, resultados: list):
        """Muestra los resultados de búsqueda."""
        if not resultados:
            messagebox.showinfo("Sin resultados", "No se encontraron metadatos para esta canción")
            self._volver_a_editor()
            return
        
        self.search_view.mostrar_resultados(resultados)
    
    def _volver_a_editor(self):
        """Vuelve al editor desde búsqueda."""
        self._mostrar_editor()
        if hasattr(self, 'datos_editor_temp'):
            self.editor_view.set_datos(self.datos_editor_temp)
    
    def _aplicar_resultado(self, resultado: dict):
        """Aplica un resultado de búsqueda."""
        # Volver al editor
        self._volver_a_editor()
        
        # Aplicar datos
        self.editor_view.set_datos({
            'titulo': resultado.get('titulo', ''),
            'artista': resultado.get('artista', ''),
            'album': resultado.get('album', ''),
            'genero': resultado.get('genero', ''),
            'año': resultado.get('año', ''),
            'track_number': resultado.get('track_number', ''),
            'disc_number': resultado.get('disc_number', '')
        })
        
        # Descargar carátula en background
        if resultado.get('imagen_url'):
            def descargar():
                imagen_data = self.controller.descargar_caratula(resultado['imagen_url'])
                if imagen_data and self.selected_file:
                    self.selected_file['imagen_temp'] = imagen_data
                    print("✅ Carátula lista para guardar")
            
            threading.Thread(target=descargar, daemon=True).start()
        
        messagebox.showinfo("Éxito", "Metadatos aplicados. No olvides guardar los cambios.")
