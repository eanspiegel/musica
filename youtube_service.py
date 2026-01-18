import os
import yt_dlp
from typing import Optional, Tuple, Dict, Any, Callable
from config_manager import ConfigManager
from utils import Utils

class YouTubeService:
    """Maneja la lógica de interacción con yt-dlp y descargas."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager

    def _get_client_args(self, is_mp4: bool) -> dict:
        # Probando sin restricciones de cliente para ver si aparecen los formatos
        return {}

    def obtener_info_basica(self, url: str) -> Tuple[Optional[Dict[str, Any]], str]:
        opciones = {'quiet': True, 'no_warnings': True, 'extract_flat': True}
        try:
            # Priorizar Playlist: Si el link tiene &list=, lo transformamos a link de playlist puro
            url_limpia = url
            if 'list=' in url:
                try:
                    from urllib.parse import urlparse, parse_qs
                    parsed = urlparse(url)
                    qs = parse_qs(parsed.query)
                    if 'list' in qs:
                        playlist_id = qs['list'][0]
                        url_limpia = f"https://www.youtube.com/playlist?list={playlist_id}"
                except:
                    pass

            # Usamos la URL limpia para la extracción
            with yt_dlp.YoutubeDL(opciones) as ydl:
                info = ydl.extract_info(url_limpia, download=False)
                # Procesar duración y Tipo
                es_playlist = info.get('_type') == 'playlist' or 'entries' in info
                
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
        if not os.path.exists(directorio):
            os.makedirs(directorio)

        def hook(d):
            if d['status'] == 'downloading':
                try:
                    p = d.get('_percent_str', '0%').replace('%','')
                    if progress_callback:
                        progress_callback(float(p))
                    if status_callback:
                        status_callback(f"Descargando: {d.get('_percent_str')} - {d.get('_eta_str', '?')} restantes")
                except:
                    pass
            elif d['status'] == 'finished':
                if status_callback:
                    status_callback("Procesando / Convirtiendo...")
                    if progress_callback: progress_callback(100)

        opciones = {
            'outtmpl': os.path.join(directorio, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'ignoreerrors': False,
            'nocheckcertificate': True,
            'progress_hooks': [hook],
        }

        # Filtrado de Playlist (Indices 1-based)
        if indices:
            opciones['playlist_items'] = ",".join(map(str, indices))
            
            # CRITICAL FIX: Si es una URL mixta (watch?v=...&list=...), yt-dlp puede ignorar
            # playlist_items y bajar solo el video. Forzamos formato playlist puro.
            if 'list=' in url:
                try:
                    from urllib.parse import urlparse, parse_qs
                    parsed = urlparse(url)
                    qs = parse_qs(parsed.query)
                    if 'list' in qs:
                        playlist_id = qs['list'][0]
                        url = f"https://www.youtube.com/playlist?list={playlist_id}"
                except Exception as e:
                    pass # Si falla, usamos la original
        
        # 1. Aplicamos la MISMA estrategia de cliente
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
                # STRICT FIX v3 (ID Exacto):
                # Usamos el ID que encontramos en 'obtener_calidades__disponibles'.
                # Como usamos el MISMO cliente, el ID debe existir.
                opciones['format'] = f"{formato_id}+bestaudio/best"
                # Nota: /best es fallback solo para el audio, no para el video.
            else:
                # Automático
                if contenedor == 'webm':
                    opciones['format'] = 'bestvideo[vcodec*=vp9]+bestaudio/best'
                else:
                    opciones['format'] = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best'
            
            if ffmpeg_ok:
                # Merge container
                if contenedor == 'webm':
                    opciones['merge_output_format'] = 'webm'
                else:
                    opciones['merge_output_format'] = 'mp4'

        try:
            with yt_dlp.YoutubeDL(opciones) as ydl:
                ydl.download([url])
        except Exception as e:
            raise e
