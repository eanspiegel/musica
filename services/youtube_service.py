import os
import yt_dlp
from typing import Optional, Tuple, Dict, Any, Callable
from config_manager import ConfigManager
from utils.utils import Utils

class YouTubeService:
    """Maneja SOLO la lógica de interacción con yt-dlp y descargas."""
    
    def __init__(self, config_manager: ConfigManager):
        self.config_manager = config_manager
        # Eliminada dependencia de MetadataService

    def _get_client_args(self, is_mp4: bool) -> dict:
        return {
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web']
                }
            }
        }

    def _clean_url(self, url: str) -> str:
        try:
            if 'list=' in url and 'v=' in url:
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(url)
                qs = parse_qs(parsed.query)
                if 'v' in qs and 'list' in qs:
                    list_id = qs['list'][0]
                    if list_id.startswith('RD') or 'start_radio' in qs:
                            video_id = qs['v'][0]
                            clean = f"https://www.youtube.com/watch?v={video_id}"
                            print(f"🧹 Link limpiado de Mix/Radio: {clean}")
                            return clean

            if 'list=' in url and 'v=' in url:
                from urllib.parse import urlparse, parse_qs
                parsed = urlparse(url)
                qs = parse_qs(parsed.query)
                if 'list' in qs:
                    list_id = qs['list'][0]
                    if not list_id.startswith('RD'):
                         clean = f"https://www.youtube.com/playlist?list={list_id}"
                         print(f"📂 Link convertido a Playlist pura: {clean}")
                         return clean
        except:
            pass
        return url

    def obtener_info_basica(self, url: str) -> Tuple[Optional[Dict[str, Any]], str]:
        opciones = {'quiet': True, 'no_warnings': True, 'extract_flat': True}

        try:
            url_limpia = self._clean_url(url)
            
            if 'list=' in url_limpia and 'v=' not in url_limpia:
                 try:
                    from urllib.parse import urlparse, parse_qs
                    parsed = urlparse(url_limpia)
                    qs = parse_qs(parsed.query)
                    if 'list' in qs:
                        playlist_id = qs['list'][0]
                        url_limpia = f"https://www.youtube.com/playlist?list={playlist_id}"
                 except: pass

            with yt_dlp.YoutubeDL(opciones) as ydl:
                info = ydl.extract_info(url_limpia, download=False)
                
                _type = info.get('_type', 'video')
                has_entries = 'entries' in info
                print(f"🕵️ Extraction Info: Type={_type}, HasEntries={has_entries}, Title={info.get('title')}")

                es_playlist = _type == 'playlist' or has_entries
                
                if es_playlist:
                     titulo = info.get('title', 'Playlist Desconocida')
                     entries = list(info.get('entries', []))
                     count = len(entries)
                     dur_str = f"{count} Videos"
                     
                     thumbnail = info.get('thumbnail')
                     if not thumbnail and entries:
                         first_entry = entries[0]
                         if first_entry:
                             thumbnail = first_entry.get('thumbnail')
                             if not thumbnail and first_entry.get('url'):
                                 try:
                                      with yt_dlp.YoutubeDL({'quiet': True}) as ydl_thumb:
                                          info_thumb = ydl_thumb.extract_info(first_entry['url'], download=False)
                                          thumbnail = info_thumb.get('thumbnail')
                                 except:
                                     pass
                     
                     uploader = info.get('uploader') or info.get('channel') or "Varios"
                     
                     playlist_items = []
                     for e in entries:
                         if not e: continue
                         vid_title = e.get('title', 'Video sin título')
                         vid_id = e.get('id')
                         vid_url = e.get('url')
                         
                         vid_uploader = e.get('uploader') or e.get('channel') or "Varios"
                         vid_duration = e.get('duration_string') or e.get('duration')
                         vid_thumbnail = e.get('thumbnail') 
                         
                         if not vid_thumbnail and vid_id:
                             vid_thumbnail = f"https://i.ytimg.com/vi/{vid_id}/mqdefault.jpg"

                         if isinstance(vid_duration, (int, float)):
                             m, s = divmod(int(vid_duration), 60)
                             if m > 60:
                                 h, m = divmod(m, 60)
                                 vid_duration = f"{h}:{m:02d}:{s:02d}"
                             else:
                                 vid_duration = f"{m}:{s:02d}"
                         
                         vid_duration = str(vid_duration) if vid_duration else "??"

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
                        'duration': dur_str, 
                        'uploader': uploader,
                        'playlist_items': playlist_items
                    }
                    return video_data, 'OK'
        except Exception as e:
            return None, str(e)

    def obtener_calidades_disponibles(self, url: str, video_codec: str = 'any') -> Dict[int, Dict[str, Any]]:
        es_mp4 = (video_codec == 'mp4')
        opciones = {'quiet': True, 'no_warnings': True}
        opciones.update(self._get_client_args(es_mp4))
        
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
                    
                    is_vp9 = 'vp9' in vcodec or 'vp09' in vcodec
                    is_avc = 'avc' in vcodec or 'h264' in vcodec
                    
                    if video_codec == 'webm' and not is_vp9 and ext != 'webm': 
                        continue
                        
                    if video_codec == 'mp4':
                        if not is_avc and ext != 'mp4':
                            continue
                    
                    if not altura or altura < 144: continue
                    
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
                            'formato_id': formato.get('format_id'), 
                            'ext': formato.get('ext', 'mp4'),
                            'fps': fps
                        }
                return calidades
        except Exception as e:
            return {}

    def descargar(self, url: str, tipo: str, formato_id: str = None, audio_format: str = 'mp3', directorio: str = '', 
                  contenedor: str = 'mp4', progress_callback: Callable = None, status_callback: Callable = None) -> Optional[str]:
        """
        Retorna la ruta del archivo descargado si es exitoso, o None.
        YA NO realiza etiquetado.
        """
        url = self._clean_url(url)
        
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
            'noplaylist': True, 
        }

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

        try:
            with yt_dlp.YoutubeDL(opciones) as ydl:
                info = ydl.extract_info(url, download=True)
                
                # Retornar ruta final
                if tipo == 'musica' and info:
                    temp_path = ydl.prepare_filename(info)
                    base, _ = os.path.splitext(temp_path)
                    final_path = f"{base}.{audio_format}"
                    
                    if os.path.exists(final_path):
                         # Return tuple: (path, info_dict_for_hints)
                         return final_path, info
                elif tipo == 'video' and info:
                     final_path = ydl.prepare_filename(info)
                     # yt-dlp a veces cambia ext post merge, pero por ahora confiamos en outtmpl o check
                     if os.path.exists(final_path):
                          return final_path, info
                     
                     # Check with merged extension if failed
                     base, _ = os.path.splitext(final_path)
                     ext = opciones.get('merge_output_format') or contenedor
                     path_merged = f"{base}.{ext}"
                     if os.path.exists(path_merged):
                         return path_merged, info
                         
        except Exception as e:
            print(f"Error descarga: {e}")
            return None, None

        return None, None
