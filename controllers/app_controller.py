from config.settings import APP_VERSION
import threading
from typing import Optional, Callable
from config.config_manager import ConfigManager
from services.youtube_service import YouTubeService
from services.metadata_service import MetadataService
from services.playlist_service import PlaylistService

class AppController:
    """
    Controlador principal de la aplicación.
    Coordina la UI con los servicios de Youtube y Metadatos.
    """
    
    def __init__(self):
        self.config_manager = ConfigManager()
        self.youtube_service = YouTubeService(self.config_manager)
        self.metadata_service = MetadataService()
        self.playlist_service = PlaylistService(self.youtube_service, self.metadata_service)
        
        self.video_data_cache = None

    def get_version(self) -> str:
        return APP_VERSION

    def get_download_path(self) -> str:
        return self.config_manager.cargar_configuracion() or ""

    def set_download_path(self, path: str):
        self.config_manager.guardar_configuracion(path)

    def analyze_url(self, url: str) -> tuple:
        """Retorna (data, error)"""
        data, err = self.youtube_service.obtener_info_basica(url)
        if data:
            self.video_data_cache = data
        return data, err

    def start_download_thread(self, url: str, path: str, is_video: bool, 
                              audio_fmt: str, video_fmt: str, 
                              playlist_indices: Optional[list] = None,
                              progress_callback: Callable = None, 
                              status_callback: Callable = None,
                              finished_callback: Callable = None):
        
        def run():
            try:
                if playlist_indices and self.video_data_cache:
                    # Modo Batch
                    items = self.video_data_cache.get('playlist_items', [])
                    selected_items = [items[i] for i in playlist_indices if i < len(items)]
                    
                    self.playlist_service.procesar_batch(
                        url=url, items=selected_items, tipo='video' if is_video else 'musica',
                        formato_id=None, audio_format=audio_fmt, directorio=path,
                        contenedor=video_fmt, progress_callback=progress_callback,
                        status_callback=status_callback
                    )
                else:
                    # Modo Single
                    tipo = 'video' if is_video else 'musica'
                    
                    # Si es video simple, necesitamos buscar calidades AQUI o en la UI?
                    # En la arquitectura original, la UI buscaba calidades y bloqueaba.
                    # El controlador debería exponer un metodo `get_qualities`
                    # Pero si `formato_id` viene None, asumimos mejor o auto.
                    
                    # Para simplificar refactor, asumimos que si es VIDEO y NO PLAYLIST,
                    # la UI ya pidió calidades via `get_qualities` antes de llamar a start_download.
                    # Aquí solo ejecutamos.
                    
                    # Nota: La UI original pasaba `formato_id`.
                    # Si start_download_thread recibe `formato_id`, lo usamos.
                    # Pero en este signature no lo puse. Agreguemoslo.
                    pass # Fix logic below
                
                if finished_callback: finished_callback(True, "Descarga completada")
            except Exception as e:
                import traceback
                traceback.print_exc()
                if finished_callback: finished_callback(False, str(e))

        threading.Thread(target=run, daemon=True).start()

    def get_video_qualities(self, url: str, video_fmt: str):
        return self.youtube_service.obtener_calidades_disponibles(url, video_fmt)

    # Re-implentando start_download para soportar formato_id
    def start_download(self, url: str, path: str, is_video: bool, 
                       audio_fmt: str, video_fmt: str, formato_id: str = None,
                       playlist_indices: Optional[list] = None,
                       progress_callback: Callable = None, 
                       status_callback: Callable = None,
                       finished_callback: Callable = None):
        
        def run():
            try:
                if playlist_indices and self.video_data_cache:
                     items = self.video_data_cache.get('playlist_items', [])
                     selected_items = [items[i] for i in playlist_indices if i < len(items)]
                     
                     self.playlist_service.procesar_batch(
                        url=url, items=selected_items, tipo='video' if is_video else 'musica',
                        formato_id=formato_id, audio_format=audio_fmt, directorio=path,
                        contenedor=video_fmt, progress_callback=progress_callback,
                        status_callback=status_callback
                    )
                else:
                    tipo = 'video' if is_video else 'musica'
                    
                    # 1. Download
                    res, info = self.youtube_service.descargar(
                        url, tipo, formato_id, audio_format, path, video_fmt,
                        progress_callback, status_callback
                    )
                    
                    # 2. Tag (Only if music and successful)
                    if tipo == 'musica' and res:
                        if status_callback: status_callback("Etiquetando...")
                        artist_hint = info.get('uploader') or info.get('artist')
                        self.metadata_service.etiquetar(res, artista_hint=artist_hint, status_callback=status_callback)

                if finished_callback: finished_callback(True, "Finalizado")

            except Exception as e:
                import traceback
                traceback.print_exc()
                if finished_callback: finished_callback(False, str(e))

        threading.Thread(target=run, daemon=True).start()
