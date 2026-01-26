import os
from collections import Counter
from typing import List, Dict, Callable
from services.youtube_service import YouTubeService
from services.metadata_service import MetadataService

class PlaylistService:
    """Maneja descargas en lote y verificacion de consistencia de playlists."""

    def __init__(self, youtube_service: YouTubeService, metadata_service: MetadataService):
        self.youtube_service = youtube_service
        self.metadata_service = metadata_service

    def procesar_batch(self, url: str, items: List[Dict], tipo: str, formato_id: str, 
                      audio_format: str, directorio: str, contenedor: str, 
                      progress_callback: Callable, status_callback: Callable) -> None:
        
        tagging_results = []
        total = len(items)
        
        for i, item in enumerate(items):
            target_url = item.get('url')
            target_title = item.get('title', f"Video {i+1}")
            
            if not target_url: continue
            
            # Wrapper para progreso relativo
            def local_progress(val):
                step = 100 / total
                base = i * step
                global_progress = base + (val * step / 100)
                if progress_callback: progress_callback(global_progress)

            try:
                # 1. Descargar (Sin etiquetar aun)
                ruta_archivo, info = self.youtube_service.descargar(
                    target_url, tipo, formato_id, audio_format, directorio, contenedor, 
                    local_progress, status_callback
                )

                if ruta_archivo and os.path.exists(ruta_archivo) and tipo == 'musica':
                     # 2. Etiquetar individualmente
                     if status_callback: status_callback(f"🏷️ Etiquetando: {target_title[:15]}...")
                     
                     artist_hint = info.get('uploader') or info.get('artist') or info.get('channel')
                     
                     # Etiquetar
                     res = self.metadata_service.etiquetar(ruta_archivo, artista_hint=artist_hint, status_callback=None)
                     
                     if res and isinstance(res, dict) and 'artist' in res:
                        res['original_entry'] = item 
                        res['file_path'] = res.get('file_path', ruta_archivo) # Asegurar path
                        tagging_results.append(res)

            except Exception as e:
                print(f"❌ Error descargando item batch '{target_title}': {e}")
                if status_callback: status_callback(f"⚠️ Error en {target_title[:15]}...")

        # --- ANÁLISIS RETROSPECTIVO ---
        if tipo == 'musica' and len(tagging_results) > 1:
             self._analizar_consistencia(tagging_results, status_callback)

    def _analizar_consistencia(self, tagging_results: List[Dict], status_callback: Callable):
         print(f"📊 Analizando consistencia de playlist ({len(tagging_results)} procesadas)...")
         
         found_artists = [res['artist'] for res in tagging_results if res.get('artist') and res['artist'] != "Desconocido"]
         
         if found_artists:
             most_common_found = Counter(found_artists).most_common(1)
             if most_common_found:
                 dominant_artist = most_common_found[0][0]
                 count = most_common_found[0][1]
                 total_tags = len(tagging_results)
                 
                 # 60% Consenso
                 if count >= total_tags * 0.6: 
                     print(f"⚖️ Consenso de Playlist detectado: '{dominant_artist}' ({count}/{total_tags})")
                     
                     for res in tagging_results:
                         current_artist = res.get('artist')
                         is_imposter = False
                         if current_artist and current_artist != dominant_artist:
                             # Validar que no contenga al dominante (ej: Feat)
                             if dominant_artist.lower() not in current_artist.lower():
                                 is_imposter = True
                         
                         if is_imposter:
                             print(f"🕵️ 'Impostor' detectado: '{current_artist}' en '{os.path.basename(res['file_path'])}'. Corrigiendo con '{dominant_artist}'...")
                             if status_callback: status_callback(f"🔄 Corrigiendo: {dominant_artist}")
                             
                             orig_title = res.get('original_entry', {}).get('title')
                             self.metadata_service.etiquetar(res['file_path'], artista_hint=dominant_artist, status_callback=None, strict_artist_match=True, search_title=orig_title)
