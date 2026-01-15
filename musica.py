import yt_dlp
import os
import sys

def formatear_tamano(bytes):
    """Convierte bytes a formato legible"""
    for unidad in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.2f} {unidad}"
        bytes /= 1024.0
    return f"{bytes:.2f} TB"

def verificar_ffmpeg():
    """Verifica si FFmpeg está instalado"""
    try:
        import subprocess
        resultado = subprocess.run(['ffmpeg', '-version'], 
                                 capture_output=True, 
                                 text=True, 
                                 timeout=3)
        return resultado.returncode == 0
    except:
        return False

def verificar_tipo_contenido(url):
    """Verifica si la URL es una playlist o un video individual"""
    opciones_info = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
    }
    
    try:
        # Verificar si la URL contiene un parámetro de playlist
        es_playlist_url = 'list=' in url
        
        with yt_dlp.YoutubeDL(opciones_info) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Si tiene 'entries' o la URL tiene 'list=', es una playlist
            if 'entries' in info or es_playlist_url:
                cantidad = len(info.get('entries', [])) if 'entries' in info else 1
                return 'playlist', info.get('title', 'Sin título'), cantidad
            else:
                return 'video', info.get('title', 'Sin título'), 1
    except Exception as e:
        print(f"Error al obtener información: {e}")
        return None, None, 0

def obtener_calidades_disponibles(url):
    """Obtiene las calidades de video disponibles con su tamaño estimado"""
    # 1. Eliminamos extractor_args para que yt-dlp detecte todo automáticamente
    opciones_info = {
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(opciones_info) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Obtener formatos de video
            formatos = info.get('formats', [])
            calidades = {}
            
            # Mapeo de alturas a nombres de calidad
            nombres_calidad = {
                144: '144p',
                240: '240p',
                360: '360p',
                480: '480p',
                720: '720p HD',
                1080: '1080p Full HD',
                1440: '1440p 2K',
                2160: '2160p 4K',
                4320: '4320p 8K'
            }
            
            # Obtener el mejor audio disponible (para sumar al peso del video)
            mejor_audio_size = 0
            for formato in formatos:
                if formato.get('vcodec') == 'none' and formato.get('acodec') != 'none':
                    audio_size = formato.get('filesize', 0) or formato.get('filesize_approx', 0)
                    if audio_size > mejor_audio_size:
                        mejor_audio_size = audio_size
            
            duracion = info.get('duration', 0)
            
            # Recopilar todos los formatos de video disponibles
            for formato in formatos:
                # Solo formatos de video (que tengan codec de video)
                if formato.get('vcodec') != 'none':
                    altura = formato.get('height', 0)
                    
                    # Saltar si no tiene altura definida o es muy pequeña
                    if not altura or altura < 144:
                        continue
                    
                    # Tamaño del video
                    video_size = formato.get('filesize', 0) or formato.get('filesize_approx', 0)
                    
                    # Calcular tamaño total (Video + Audio estimado)
                    tamaño_total = video_size
                    
                    # Si es un video sin audio (DASH), sumamos el audio aparte
                    if formato.get('acodec') == 'none' and mejor_audio_size > 0:
                        tamaño_total += mejor_audio_size
                    
                    # Estimación de respaldo si no hay filesize (usando bitrate)
                    if tamaño_total == 0 and duracion > 0:
                        tbr = formato.get('tbr', 0)
                        if tbr > 0:
                            tamaño_total = int((tbr * duracion * 1024) / 8)
                    
                    formato_id = formato.get('format_id')
                    ext = formato.get('ext', 'mp4')
                    fps = formato.get('fps', 0)
                    width = formato.get('width', 0)
                    
                    # Construir nombre
                    nombre_calidad = nombres_calidad.get(altura, f'{altura}p')
                    if fps and fps > 30:
                        nombre_calidad += f' {int(fps)}fps'
                    
                    # LÓGICA DE SELECCIÓN:
                    # Guardamos el formato si:
                    # 1. No tenemos esa resolución aún.
                    # 2. O si tenemos la resolución, pero este formato tiene mejor FPS.
                    # 3. O si tienen mismo FPS, preferimos mp4 sobre webm (opcional) o el de mayor bitrate.
                    
                    actualizar = False
                    if altura not in calidades:
                        actualizar = True
                    else:
                        info_existente = calidades[altura]
                        # Preferir mayor FPS
                        if fps > info_existente['fps']:
                            actualizar = True
                        # A igual FPS, preferir MP4 para mayor compatibilidad si el tamaño es similar
                        elif fps == info_existente['fps']:
                            if ext == 'mp4' and info_existente['ext'] != 'mp4':
                                actualizar = True
                            elif tamaño_total > info_existente['tamaño']:
                                # Si no es por extensión, nos quedamos con el que tenga más información (bitrate)
                                actualizar = True

                    if actualizar:
                        calidades[altura] = {
                            'nombre': nombre_calidad,
                            'resolucion': f"{width}x{altura}",
                            'tamaño': tamaño_total,
                            'formato_id': formato_id,
                            'ext': ext,
                            'tiene_audio': formato.get('acodec') != 'none',
                            'fps': fps
                        }
            
            return calidades
    except Exception as e:
        print(f"Error al obtener calidades: {e}")
        return {}
def descargar_musica(url, tipo_contenido, nombre_contenido, cantidad):
    """Descarga audio en formato MP3 o mejor formato disponible"""
    directorio_salida = os.path.join(os.path.dirname(__file__), 'playlist')
    
    if not os.path.exists(directorio_salida):
        os.makedirs(directorio_salida)
    
    # Verificar si FFmpeg está disponible
    ffmpeg_disponible = verificar_ffmpeg()
    
    opciones = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(directorio_salida, '%(title)s.%(ext)s'),
        'quiet': False,
        'no_warnings': False,
        'ignoreerrors': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        'nocheckcertificate': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    }
    
    # Solo agregar conversión a MP3 si FFmpeg está disponible
    if ffmpeg_disponible:
        opciones['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    else:
        print("\n⚠️  FFmpeg no está instalado. Los archivos se descargarán en su formato original (webm/m4a).")
        print("💡 Para convertir a MP3, instala FFmpeg: https://ffmpeg.org/download.html\n")
    
    try:
        if tipo_contenido == 'playlist':
            print(f"\n📁 Playlist: {nombre_contenido}")
            print(f"📊 Total de canciones: {cantidad}")
        else:
            print(f"\n🎵 Canción: {nombre_contenido}")
        
        print(f"💾 Guardando en: {directorio_salida}\n")
        
        with yt_dlp.YoutubeDL(opciones) as ydl:
            ydl.download([url])
        
        print("\n✓ Descarga completada!")
        print(f"Las canciones se guardaron en: {directorio_salida}")
        
    except Exception as e:
        print(f"Error al descargar: {e}")
        sys.exit(1)

def descargar_video(url, formato_id, tipo_contenido, nombre_contenido, cantidad):
    """Descarga video en la calidad seleccionada"""
    directorio_salida = os.path.join(os.path.dirname(__file__), 'playlist')
    
    if not os.path.exists(directorio_salida):
        os.makedirs(directorio_salida)
    
    # Construcción de la cadena de formato
    if formato_id:
        # Intenta bajar el video seleccionado + el mejor audio. 
        # Si falla, baja lo mejor que encuentre ("best").
        formato_str = f'{formato_id}+bestaudio/best'
    else:
        # Si es automático, baja la mejor calidad de video y audio y las une
        formato_str = 'bestvideo+bestaudio/best'
    
    opciones = {
        'format': formato_str,
        'outtmpl': os.path.join(directorio_salida, '%(title)s.%(ext)s'),
        'quiet': False,
        'no_warnings': False,
        'ignoreerrors': True,
        # ELIMINAMOS 'extractor_args' para evitar el error de GVS PO Token
        'nocheckcertificate': True,
        'merge_output_format': 'mp4',
        'postprocessors': [{
            'key': 'FFmpegVideoConvertor',
            'preferedformat': 'mp4',
        }],
    }
    
    try:
        if tipo_contenido == 'playlist':
            print(f"\n📁 Playlist: {nombre_contenido}")
            print(f"📊 Total de videos: {cantidad}")
        else:
            print(f"\n🎬 Video: {nombre_contenido}")
        
        print(f"💾 Guardando en: {directorio_salida}\n")
        
        with yt_dlp.YoutubeDL(opciones) as ydl:
            ydl.download([url])
        
        print("\n✓ Descarga completada!")
        print(f"Los videos se guardaron en: {directorio_salida}")
        
    except Exception as e:
        print(f"Error al descargar: {e}")
        sys.exit(1)
def menu_interactivo():
    """Menú principal interactivo"""
    print("=" * 60)
    print("  🎵 DESCARGADOR DE YOUTUBE 🎬")
    print("=" * 60)
    
    # Obtener URL
    url = input("\n📎 Ingresa la URL de YouTube: ").strip()
    
    if not url:
        print("❌ URL vacía. Saliendo...")
        sys.exit(1)
    
    # Verificar tipo de contenido
    print("\n🔍 Analizando contenido...")
    tipo_contenido, nombre_contenido, cantidad = verificar_tipo_contenido(url)
    
    if not tipo_contenido:
        print("❌ No se pudo obtener información del contenido")
        sys.exit(1)
    
    # Mostrar tipo de contenido
    print("\n" + "=" * 60)
    if tipo_contenido == 'playlist':
        print(f"📁 PLAYLIST DETECTADA: {nombre_contenido}")
        print(f"📊 Cantidad de elementos: {cantidad}")
    else:
        print(f"🎬 VIDEO INDIVIDUAL: {nombre_contenido}")
    print("=" * 60)
    
    # Menú de tipo de descarga
    print("\n¿Qué deseas descargar?")
    print("1. 🎵 Música (MP3)")
    print("2. 🎬 Video (MP4)")
    print("3. ❌ Cancelar")
    
    opcion = input("\nSelecciona una opción (1-3): ").strip()
    
    if opcion == '1':
        descargar_musica(url, tipo_contenido, nombre_contenido, cantidad)
    
    elif opcion == '2':
        # Para video, obtener calidades disponibles
        print("\n🔍 Obteniendo calidades disponibles...")
        
        # Si es playlist, obtener info del primer video
        url_muestra = url
        if tipo_contenido == 'playlist':
            print("📝 Nota: Para playlists, se mostrarán las calidades del primer video")
        
        calidades = obtener_calidades_disponibles(url_muestra)
        
        if not calidades:
            print("\n⚠️  No se pudieron obtener las calidades. Descargando en mejor calidad disponible...")
            descargar_video(url, None, tipo_contenido, nombre_contenido, cantidad)
            return
        
        # Mostrar calidades
        print("\n" + "=" * 60)
        print("  CALIDADES DISPONIBLES")
        print("=" * 60)
        
        calidades_ordenadas = sorted(calidades.items(), reverse=True)
        for idx, (altura, info) in enumerate(calidades_ordenadas, 1):
            tamaño_str = formatear_tamano(info['tamaño']) if info['tamaño'] > 0 else '~Estimado'
            print(f"{idx}. {info['nombre']:20s} ({info['resolucion']}) - {tamaño_str}")
        
        print(f"{len(calidades_ordenadas) + 1}. Mejor calidad disponible (automático)")
        print("=" * 60)
        
        seleccion = input(f"\nSelecciona la calidad (1-{len(calidades_ordenadas) + 1}): ").strip()
        
        try:
            seleccion_num = int(seleccion)
            if 1 <= seleccion_num <= len(calidades_ordenadas):
                formato_id = calidades_ordenadas[seleccion_num - 1][1]['formato_id']
            else:
                formato_id = None  # Mejor calidad automática
        except ValueError:
            formato_id = None
        
        descargar_video(url, formato_id, tipo_contenido, nombre_contenido, cantidad)
    
    elif opcion == '3':
        print("\n👋 Cancelado por el usuario")
        sys.exit(0)
    
    else:
        print("\n❌ Opción inválida")
        sys.exit(1)

if __name__ == "__main__":
    menu_interactivo()
