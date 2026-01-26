import os
import yt_dlp
from typing import Optional, Tuple, Dict, Any, Callable
from config_manager import ConfigManager
from utils import Utils
from metadata_service import MetadataService

class YouTubeService:
    """Maneja la lógica de interacción con yt-dlp y descargas."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        self.metadata_service = MetadataService()

    def _get_client_args(self, is_mp4: bool) -> dict:
        # Usar cliente Android para evitar 403s comunes en PC
        return {
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web']
                }
            }
        }

    def _clean_url(self, url: str) -> str:
        """
        Limpia la URL para evitar descargar Mixes/Radios accidentales.
        Si es Mix (RD...) mantiene solo el video.
        Si es Playlist real, intenta normalizarla.
        """
        try:
            # 1. Si es un Mix (list=RD...) y tiene video (v=...), priorizar el video y quitar la lista.
            if 'list=' in url and 'v=' in url:
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(url)
                qs = parse_qs(parsed.query)
                if 'v' in qs and 'list' in qs:
                    list_id = qs['list'][0]
                    # RD = Mix/Radio. start_radio = Contexto radio.
                    if list_id.startswith('RD') or 'start_radio' in qs:
                            video_id = qs['v'][0]
                            clean = f"https://www.youtube.com/watch?v={video_id}"
                            print(f"🧹 Link limpiado de Mix/Radio: {clean}")
                            return clean

            # 2. Si NO se limpió (no era Mix) y sigue teniendo list=, forzamos modo Playlist
            if 'list=' in url and 'v=' in url:
                # Re-parsear por si acaso (o reusar logic anterior si refactorizas)
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(url)
                qs = parse_qs(parsed.query)
                if 'list' in qs:
                    list_id = qs['list'][0]
                    # Si NO es Mix (ya filtrado arriba o validado aqui)
                    if not list_id.startswith('RD'):
                         clean = f"https://www.youtube.com/playlist?list={list_id}"
                         print(f"📂 Link convertido a Playlist pura: {clean}")
                         return clean
        except:
            pass
        return url

    def obtener_info_basica(self, url: str) -> Tuple[Optional[Dict[str, Any]], str]:
        opciones = {'quiet': True, 'no_warnings': True, 'extract_flat': True}
        # options.update(self._get_client_args(is_mp4=False)) # REVERTIDO: Provoca que las playlists no se detecten bien en UI

        try:
            # Priorizar Playlist: Si el link tiene &list=, lo transformamos a link de playlist puro
            # Limpieza centralizada
            url_limpia = self._clean_url(url)
            
            # Si limpiamos la URL (era mix), url_limpia será watch?v=...
            # Si no (era playlist real o video solo), sigue igual.
            
            # Normalizacion extra para Playlists puras (si el usuario pegó una playlist real sucia)
            if 'list=' in url_limpia and 'v=' not in url_limpia:
                 try:
                    from urllib.parse import urlparse, parse_qs
                    parsed = urlparse(url_limpia)
                    qs = parse_qs(parsed.query)
                    if 'list' in qs:
                        playlist_id = qs['list'][0]
                        url_limpia = f"https://www.youtube.com/playlist?list={playlist_id}"
                 except: pass

            # Usamos la URL limpia para la extracción
            with yt_dlp.YoutubeDL(opciones) as ydl:
                info = ydl.extract_info(url_limpia, download=False)
                
                # Debugging
                _type = info.get('_type', 'video')
                has_entries = 'entries' in info
                print(f"🕵️ Extraction Info: Type={_type}, HasEntries={has_entries}, Title={info.get('title')}")

                # Procesar duración y Tipo
                es_playlist = _type == 'playlist' or has_entries
                
                if es_playlist:
                     titulo = info.get('title', 'Playlist Desconocida')
                     entries = list(info.get('entries', []))
                     count = len(entries)
                     dur_str = f"{count} Videos"
                     
                     # Intentar obtener thumbnail de la playlist o del primer video
                     # Intentar obtener thumbnail de la playlist o del primer video
                     thumbnail = info.get('thumbnail')
                     if not thumbnail and entries:
                         first_entry = entries[0]
                         # Si es extract_flat, la entrada puede no tener thumbnail.
                         # Si falta, hacemos una extracción rápida SOLO del primer video para tener ALGO que mostrar.
                         if first_entry:
                             thumbnail = first_entry.get('thumbnail')
                             if not thumbnail and first_entry.get('url'):
                                 try:
                                      # Extracción ligera del primer video para robar su thumbnail
                                      with yt_dlp.YoutubeDL({'quiet': True}) as ydl_thumb:
                                          info_thumb = ydl_thumb.extract_info(first_entry['url'], download=False)
                                          thumbnail = info_thumb.get('thumbnail')
                                 except:
                                     pass
                     
                     uploader = info.get('uploader') or info.get('channel') or "Varios"
                     
                     # Extraer nombres y URLs ROBUSTAMENTE
                     playlist_items = []
                     for e in entries:
                         if not e: continue
                         vid_title = e.get('title', 'Video sin título')
                         vid_id = e.get('id')
                         vid_url = e.get('url')
                         
                         vid_uploader = e.get('uploader') or e.get('channel') or "Varios"
                         vid_duration = e.get('duration_string') or e.get('duration')
                         vid_thumbnail = e.get('thumbnail') 
                         
                         # Fallback: Construir URL de thumbnail si falta y tenemos ID
                         if not vid_thumbnail and vid_id:
                             vid_thumbnail = f"https://i.ytimg.com/vi/{vid_id}/mqdefault.jpg"

                         # Formato simple de duración si viene en segundos
                         if isinstance(vid_duration, (int, float)):
                             m, s = divmod(int(vid_duration), 60)
                             if m > 60:
                                 h, m = divmod(m, 60)
                                 vid_duration = f"{h}:{m:02d}:{s:02d}"
                             else:
                                 vid_duration = f"{m}:{s:02d}"
                         
                         vid_duration = str(vid_duration) if vid_duration else "??"

                         # Construir URL explícita si falta
                         if not vid_url and vid_id:
                             vid_url = f"https://www.youtube.com/watch?v={vid_id}"
                             
                         if vid_url:
                             playlist_items.append({
                                 'title': vid_title, 
                                 'url': vid_url,
                                 'uploader': vid_uploader,
                                 'duration': vid_duration,
                                 'thumbnail': vid_thumbnail
                             })
                     # Return para Playlist
                     return {
                        'type': 'playlist',
                        'title': titulo,
                        'duration': dur_str,
                        'uploader': uploader,
                        'thumbnail': thumbnail,
                        'playlist_items': playlist_items
                     }, 'OK'

                else:
                    titulo = info.get('title', 'Sin título')
                    playlist_items = []
                    dur = info.get('duration', 0)
                    mins, secs = divmod(dur, 60)
                    hours, mins = divmod(mins, 60)
                    if hours > 0:
                        dur_str = f"{int(hours)}h {int(mins)}m {int(secs)}s"
                    else:
                        dur_str = f"{int(mins)}m {int(secs)}s"
                    thumbnail = info.get('thumbnail', '')
                    uploader = info.get('uploader', 'Desconocido')

                    video_data = {
                        'type': 'video',
                        'title': titulo,
                        'thumbnail': thumbnail,
                        'duration': dur_str, # Will hold Duration OR Count
                        'uploader': uploader,
                        'playlist_items': playlist_items
                    }
                    return video_data, 'OK'
        except Exception as e:
            return None, str(e)

    def obtener_calidades_disponibles(self, url: str, video_codec: str = 'any') -> Dict[int, Dict[str, Any]]:
        # Usamos EXACTAMENTE los mismos argumentos que usaremos para descargar.
        es_mp4 = (video_codec == 'mp4')
        opciones = {'quiet': True, 'no_warnings': True}
        opciones.update(self._get_client_args(es_mp4))
        
        # Limpieza tambien aqui por seguridad
        url = self._clean_url(url)

        try:
            with yt_dlp.YoutubeDL(opciones) as ydl:
                info = ydl.extract_info(url, download=False)
                formatos = info.get('formats', [])
                calidades = {}
                nombres_calidad = {
                    144: '144p', 240: '240p', 360: '360p', 480: '480p',
                    720: '720p HD', 1080: '1080p Full HD', 1440: '1440p 2K',
                    2160: '2160p 4K', 4320: '4320p 8K'
                }
                
                mejor_audio_size = 0
                for formato in formatos:
                    if formato.get('vcodec') == 'none' and formato.get('acodec') != 'none':
                        audio_size = formato.get('filesize', 0) or formato.get('filesize_approx', 0)
                        if audio_size > mejor_audio_size: mejor_audio_size = audio_size
                    
                duracion = info.get('duration', 0)
                
                
                for formato in formatos:
                    vcodec = formato.get('vcodec', 'none')
                    altura = formato.get('height', 0)
                    ext = formato.get('ext')
                    fid = formato.get('format_id')
                    
                    if vcodec == 'none': continue
                    
                    # Filtros Estrictos
                    is_vp9 = 'vp9' in vcodec or 'vp09' in vcodec
                    is_avc = 'avc' in vcodec or 'h264' in vcodec
                    
                    if video_codec == 'webm' and not is_vp9 and ext != 'webm': 
                        continue
                        
                    if video_codec == 'mp4':
                        if not is_avc and ext != 'mp4':
                            continue
                    
                    if not altura or altura < 144: continue
                    
                    # Preferir HTTPS directo sobre m3u8
                    proto = formato.get('protocol', '')
                    if 'm3u8' in proto: pass 

                    video_size = formato.get('filesize', 0) or formato.get('filesize_approx', 0)
                    tamaño_total = video_size
                    if formato.get('acodec') == 'none' and mejor_audio_size > 0:
                        tamaño_total += mejor_audio_size
                    if tamaño_total == 0 and duracion > 0:
                        tbr = formato.get('tbr', 0)
                        if tbr > 0: tamaño_total = int((tbr * duracion * 1024) / 8)
                    
                    nombre_calidad = nombres_calidad.get(altura, f'{altura}p')
                    fps = formato.get('fps', 0)
                    if fps and fps > 30: nombre_calidad += f' {int(fps)}fps'
                    
                    if is_vp9: nombre_calidad += ' (VP9)'
                    
                    actualizar = False
                    if altura not in calidades: actualizar = True
                    else:
                        info_existente = calidades[altura]
                        if fps > info_existente['fps']: actualizar = True
                        elif fps == info_existente['fps']:
                            if tamaño_total > info_existente['tamaño']: actualizar = True

                    if actualizar:
                        calidades[altura] = {
                            'nombre': nombre_calidad,
                            'resolucion': f"{formato.get('width',0)}x{altura}",
                            'tamaño': tamaño_total,
                            'formato_id': formato.get('format_id'), # IMPORTANTE: Usamos este ID para descargar
                            'ext': formato.get('ext', 'mp4'),
                            'fps': fps
                        }
                return calidades
        except Exception as e:
            return {}

    def descargar(self, url: str, tipo: str, formato_id: str = None, audio_format: str = 'mp3', directorio: str = '', 
                  contenedor: str = 'mp4', progress_callback: Callable = None, status_callback: Callable = None, indices: Optional[list] = None) -> None:
        
        # LIMPIEZA CRÍTICA: Asegurar que descargamos lo que analizamos
        url = self._clean_url(url) # <--- FIX AQUI

        if indices:
            # Modo Batch (Playlist Manual)
            self.descargar_playlist_batch(url, indices, tipo, formato_id, audio_format, directorio, contenedor, progress_callback, status_callback)
        else:
            # Modo Single (O playlist completa auto gestionada por yt-dlp, pero tratada como single url)
            self._descargar_single(url, tipo, formato_id, audio_format, directorio, contenedor, progress_callback, status_callback)

    def descargar_playlist_batch(self, url_base: str, items: list, tipo: str, formato_id: str, audio_format: str, directorio: str, 
                                 contenedor: str, progress_callback: Callable, status_callback: Callable):
        
        if not os.path.exists(directorio): os.makedirs(directorio)

        tagging_results = [] # Para el analisis de consenso final
        
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
                # Descargamos individualmente
                # NOTA: _descargar_single retorna el resultado de etiquetado si hubo musica
                res = self._descargar_single(target_url, tipo, formato_id, audio_format, directorio, contenedor, local_progress, status_callback)
                
                if res and isinstance(res, dict) and 'artist' in res:
                    res['original_entry'] = item # Guardamos info original para correcciones futuras
                    tagging_results.append(res)
                    
            except Exception as e:
                print(f"❌ Error descargando item batch '{target_title}': {e}")
                if status_callback: status_callback(f"⚠️ Error en {target_title[:15]}...")

        # --- ANÁLISIS RETROSPECTIVO (Consistencia de Playlist) ---
        if tipo == 'musica' and len(tagging_results) > 1:
             print(f"📊 Analizando consistencia de playlist ({len(tagging_results)} procesadas)...")
             
             from collections import Counter
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
                                 
                                 # FORZAR ETIQUETADO con el artista dominante
                                 # Usamos strict_artist_match=True para evitar que la estrategia backup
                                 # nos devuelva el mismo resultado incorrecto (ej: Hello Clairo -> Hello -> Adele)
                                 # Usamos search_title para buscar con el titulo original (ej: "Hello?") en vez del sanetizado ("Hello")
                                 orig_title = res.get('original_entry', {}).get('title')
                                 self.metadata_service.etiquetar(res['file_path'], artista_hint=dominant_artist, status_callback=None, strict_artist_match=True, search_title=orig_title)

    def _descargar_single(self, url: str, tipo: str, formato_id: str, audio_format: str, directorio: str, 
                          contenedor: str, progress_callback: Callable, status_callback: Callable):
        
        if not os.path.exists(directorio): os.makedirs(directorio)

        def hook(d):
            if d['status'] == 'downloading':
                try:
                    p = 0.0
                    p_str = d.get('_percent_str', '')
                    import re
                    match = re.search(r"(\d+(\.\d+)?)", p_str)
                    if match:
                        p = float(match.group(1))
                    else:
                        downloaded = d.get('downloaded_bytes', 0)
                        total = d.get('total_bytes') or d.get('total_bytes_estimate')
                        if total: p = (downloaded / total) * 100.0
                            
                    if progress_callback: progress_callback(p)
                    if status_callback:
                        eta = d.get('_eta_str', '?')
                        status_callback(f"Descargando: {p:.1f}% - {eta}")
                except: pass
            elif d['status'] == 'finished':
                if status_callback: status_callback("Procesando / Convirtiendo...")
                if progress_callback: progress_callback(100)

        opciones = {
            'outtmpl': os.path.join(directorio, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': False,
            'nocheckcertificate': True,
            'progress_hooks': [hook],
            'noplaylist': True, # Forzar modo single
        }

        # Configurar cliente
        es_mp4 = (tipo == 'video' and contenedor == 'mp4')
        opciones.update(self._get_client_args(es_mp4))
        
        ffmpeg_ok = Utils.verificar_ffmpeg()

        if tipo == 'musica':
            opciones['format'] = 'bestaudio/best'
            if ffmpeg_ok:
                opciones['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': audio_format,
                    'preferredquality': '192',
                }]
        
        elif tipo == 'video':
            if formato_id:
                opciones['format'] = f"{formato_id}+bestaudio/best"
            else:
                if contenedor == 'webm':
                    opciones['format'] = 'bestvideo[vcodec*=vp9]+bestaudio/best'
                else:
                    opciones['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            
            if ffmpeg_ok:
                if contenedor == 'webm': opciones['merge_output_format'] = 'webm'
                else: opciones['merge_output_format'] = 'mp4'

        tag_result = None
        
        with yt_dlp.YoutubeDL(opciones) as ydl:
            # Descarga real
            info = ydl.extract_info(url, download=True)
            
            # --- ETIQUETADO DE AUDIO ---
            if tipo == 'musica' and info:
                # Determinar path final
                temp_path = ydl.prepare_filename(info)
                base, _ = os.path.splitext(temp_path)
                final_path = f"{base}.{audio_format}"
                
                if os.path.exists(final_path):
                     # Intentamos obtener hint del single video
                     artist_hint = info.get('uploader') or info.get('artist') or info.get('channel')
                     
                     if hasattr(self, 'metadata_service'):
                         tag_result = self.metadata_service.etiquetar(final_path, artista_hint=artist_hint, status_callback=status_callback)
                else:
                    print(f"⚠️ Archivo final no hallado para etiquetas: {final_path}")

        return tag_result


