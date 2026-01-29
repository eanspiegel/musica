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
        
        import concurrent.futures
        import threading
        
        tagging_results = []
        total = len(items)
        progress_map = {}
        progress_lock = threading.Lock()
        
        # Inicializar mapa de progreso
        for i in range(total): progress_map[i] = 0.0

        def update_individual_progress(idx, percent):
            with progress_lock:
                progress_map[idx] = percent
                # Calcular promedio total
                total_percent = sum(progress_map.values()) / total
                if progress_callback: progress_callback(total_percent)

        def procesar_item_wrapper(args):
            i, item = args
            target_title = item.get('title', f"Video {i+1}")
            
            # Pequeña pausa aleatoria al inicio para evitar requests simultáneos exactos
            import time, random
            time.sleep(random.uniform(0.5, 2.0))

            try:
                def local_cb(p):
                    update_individual_progress(i, p)
                
                # Para evitar conflictos en la UI con mensajes simultáneos, 
                # simplificamos el status_callback dentro de los hilos o usamos uno compartido con cuidado.
                # Aquí lo pasamos tal cual, sabiendo que puede haber condiciones de carrera en el texto de la UI.
                
                return self._procesar_un_item(
                    item, tipo, formato_id, audio_format, directorio, contenedor,
                    local_cb, status_callback
                )
            except Exception as e:
                print(f"❌ Error thread {i}: {e}")
                return None

        # Ejecutar en paralelo (max 2 workers)
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            # Preparamos argumentos
            work_args = [(i, item) for i, item in enumerate(items)]
            
            # Submit all
            future_to_item = {executor.submit(procesar_item_wrapper, arg): arg for arg in work_args}
            
            for future in concurrent.futures.as_completed(future_to_item):
                res = future.result()
                if res:
                    tagging_results.append(res)

        # --- ANÁLISIS RETROSPECTIVO ---
        if tipo == 'musica' and len(tagging_results) > 1:
             self._analizar_consistencia(tagging_results, status_callback)

    def _procesar_un_item(self, item: Dict, tipo: str, formato_id: str, 
                          audio_format: str, directorio: str, contenedor: str, 
                          progress_callback: Callable, status_callback: Callable) -> Dict:
        
        target_url = item.get('url')
        target_title = item.get('title', "Video")
        
        if not target_url: return None

        try:
            # 1. Descargar
            ruta_archivo, info = self.youtube_service.descargar(
                target_url, tipo, formato_id, audio_format, directorio, contenedor, 
                progress_callback, status_callback
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
                        return res

            elif not ruta_archivo:
                    print(f"⚠️ Error descarga: '{target_title}'. Saltando item.")
                    if status_callback: status_callback(f"⚠️ Saltando {target_title[:15]}...")
        
        except Exception as e:
            print(f"❌ Error procesando '{target_title}': {e}")
            if status_callback: status_callback(f"⚠️ Error en {target_title[:15]}...")
            
        return None
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
