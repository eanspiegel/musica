import yt_dlp
import os
import sys
import ctypes
from dotenv import load_dotenv 

__version__ = '1.0.1'
__author__ = 'CarloPadilla1'

load_dotenv()

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

def obtener_directorio_salida():
    """
    Define dónde se guardarán los archivos.
    Prioridad 1: Variable de entorno RUTA_DESCARGA del archivo .env
    Prioridad 2: Carpeta 'playlist' junto al script
    """
    # Intentar leer la variable del archivo .env
    ruta_env = os.getenv('RUTA_DESCARGA')
    
    if ruta_env:
        # Limpiamos comillas si el usuario las puso por error
        ruta_env = ruta_env.strip('"').strip("'")
        return ruta_env
    
    # Si no hay variable, usar la carpeta por defecto
    return os.path.join(os.path.dirname(__file__), 'playlist')

def verificar_tipo_contenido(url):
    """Verifica si la URL es una playlist o un video individual"""
    opciones_info = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        # Nota: Aquí SÍ usamos android/web para obtener metadatos rápido
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
    }
    
    try:
        es_playlist_url = 'list=' in url
        
        with yt_dlp.YoutubeDL(opciones_info) as ydl:
            info = ydl.extract_info(url, download=False)
            
            if 'entries' in info or es_playlist_url:
                cantidad = len(info.get('entries', [])) if 'entries' in info else 1
                return 'playlist', info.get('title', 'Sin título'), cantidad
            else:
                return 'video', info.get('title', 'Sin título'), 1
    except Exception as e:
        print(f"Error al obtener información: {e}")
        return None, None, 0

def obtener_calidades_disponibles(url):
    """Obtiene las calidades de video disponibles"""
    opciones_info = {
        'quiet': True,
        'no_warnings': True,
    }
    
    try:
        with yt_dlp.YoutubeDL(opciones_info) as ydl:
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
                    if audio_size > mejor_audio_size:
                        mejor_audio_size = audio_size
            
            duracion = info.get('duration', 0)
            
            for formato in formatos:
                if formato.get('vcodec') != 'none':
                    altura = formato.get('height', 0)
                    if not altura or altura < 144: continue
                    
                    video_size = formato.get('filesize', 0) or formato.get('filesize_approx', 0)
                    tamaño_total = video_size
                    
                    if formato.get('acodec') == 'none' and mejor_audio_size > 0:
                        tamaño_total += mejor_audio_size
                    
                    if tamaño_total == 0 and duracion > 0:
                        tbr = formato.get('tbr', 0)
                        if tbr > 0:
                            tamaño_total = int((tbr * duracion * 1024) / 8)
                    
                    formato_id = formato.get('format_id')
                    ext = formato.get('ext', 'mp4')
                    fps = formato.get('fps', 0)
                    width = formato.get('width', 0)
                    
                    nombre_calidad = nombres_calidad.get(altura, f'{altura}p')
                    if fps and fps > 30: nombre_calidad += f' {int(fps)}fps'
                    
                    actualizar = False
                    if altura not in calidades:
                        actualizar = True
                    else:
                        info_existente = calidades[altura]
                        if fps > info_existente['fps']: actualizar = True
                        elif fps == info_existente['fps']:
                            if ext == 'mp4' and info_existente['ext'] != 'mp4': actualizar = True
                            elif tamaño_total > info_existente['tamaño']: actualizar = True

                    if actualizar:
                        calidades[altura] = {
                            'nombre': nombre_calidad,
                            'resolucion': f"{width}x{altura}",
                            'tamaño': tamaño_total,
                            'formato_id': formato_id,
                            'ext': ext,
                            'fps': fps
                        }
            return calidades
    except Exception as e:
        print(f"Error al obtener calidades: {e}")
        return {}

def descargar_musica(url, tipo_contenido, nombre_contenido, cantidad):
    """Descarga audio en formato MP3"""
    # USAMOS LA NUEVA FUNCIÓN DE RUTA
    directorio_salida = obtener_directorio_salida()
    
    if not os.path.exists(directorio_salida):
        try:
            os.makedirs(directorio_salida)
        except OSError as e:
            print(f"\n❌ Error: No se pudo crear la carpeta en: {directorio_salida}")
            print(f"Detalle: {e}")
            return
    
    ffmpeg_disponible = verificar_ffmpeg()
    
    opciones = {
        'format': 'bestaudio/best',
        'outtmpl': os.path.join(directorio_salida, '%(title)s.%(ext)s'),
        'quiet': False,
        'no_warnings': False,
        'ignoreerrors': True,
        'nocheckcertificate': True,
    }
    
    if ffmpeg_disponible:
        opciones['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    else:
        print("\n⚠️  FFmpeg no está instalado. Se descargará en formato original.")
    
    try:
        if tipo_contenido == 'playlist':
            print(f"\n📁 Playlist: {nombre_contenido}")
            print(f"📊 Total: {cantidad}")
        else:
            print(f"\n🎵 Canción: {nombre_contenido}")
        
        print(f"💾 Guardando en: {directorio_salida}\n")
        
        with yt_dlp.YoutubeDL(opciones) as ydl:
            ydl.download([url])
        
        print("\n✓ Descarga completada!")
        
    except Exception as e:
        print(f"Error al descargar: {e}")
        sys.exit(1)

def descargar_video(url, formato_id, tipo_contenido, nombre_contenido, cantidad):
    """Descarga video en la calidad seleccionada"""
    # USAMOS LA NUEVA FUNCIÓN DE RUTA
    directorio_salida = obtener_directorio_salida()
    
    if not os.path.exists(directorio_salida):
        try:
            os.makedirs(directorio_salida)
        except OSError as e:
            print(f"\n❌ Error: No se pudo crear la carpeta en: {directorio_salida}")
            print(f"Detalle: {e}")
            return
    
    if formato_id:
        formato_str = f'{formato_id}+bestaudio/best'
    else:
        formato_str = 'bestvideo+bestaudio/best'
    
    opciones = {
        'format': formato_str,
        'outtmpl': os.path.join(directorio_salida, '%(title)s.%(ext)s'),
        'quiet': False,
        'no_warnings': False,
        'ignoreerrors': True,
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
            print(f"📊 Total: {cantidad}")
        else:
            print(f"\n🎬 Video: {nombre_contenido}")
        
        print(f"💾 Guardando en: {directorio_salida}\n")
        
        with yt_dlp.YoutubeDL(opciones) as ydl:
            ydl.download([url])
        
        print("\n✓ Descarga completada!")
        
    except Exception as e:
        print(f"Error al descargar: {e}")
        sys.exit(1)

def menu_interactivo():
    if os.name == 'nt':
        try:
            ctypes.windll.kernel32.SetConsoleTitleW(f"YouTube Downloader v{__version__}")
        except:
            pass

    print("=" * 60)
    # Aquí insertamos la versión dinámicamente
    print(f"  🎵 DESCARGADOR DE YOUTUBE 🎬  |  v{__version__}")
    print("=" * 60)
    
    # Verificar si estamos usando una ruta personalizada
    ruta_actual = obtener_directorio_salida()
    if 'playlist' not in ruta_actual and os.path.dirname(__file__) not in ruta_actual:
         print(f"📂 Ruta personalizada detectada: {ruta_actual}")
    
    url = input("\n📎 Ingresa la URL de YouTube: ").strip()
    
    if not url:
        print("❌ URL vacía. Saliendo...")
        sys.exit(1)
    
    print("\n🔍 Analizando contenido...")
    tipo_contenido, nombre_contenido, cantidad = verificar_tipo_contenido(url)
    
    if not tipo_contenido:
        print("❌ No se pudo obtener información del contenido")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    if tipo_contenido == 'playlist':
        print(f"📁 PLAYLIST: {nombre_contenido} ({cantidad} elementos)")
    else:
        print(f"🎬 VIDEO: {nombre_contenido}")
    print("=" * 60)
    
    print("\n¿Qué deseas descargar?")
    print("1. 🎵 Música (MP3)")
    print("2. 🎬 Video (MP4)")
    print("3. ❌ Cancelar")
    
    opcion = input("\nSelecciona una opción (1-3): ").strip()
    
    if opcion == '1':
        descargar_musica(url, tipo_contenido, nombre_contenido, cantidad)
    
    elif opcion == '2':
        print("\n🔍 Obteniendo calidades disponibles...")
        
        url_muestra = url
        if tipo_contenido == 'playlist':
            print("📝 Nota: Para playlists, se muestran calidades del primer video")
        
        calidades = obtener_calidades_disponibles(url_muestra)
        
        if not calidades:
            print("\n⚠️  No se pudieron obtener las calidades. Descargando automático...")
            descargar_video(url, None, tipo_contenido, nombre_contenido, cantidad)
            return
        
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
                formato_id = None
        except ValueError:
            formato_id = None
        
        descargar_video(url, formato_id, tipo_contenido, nombre_contenido, cantidad)
    
    elif opcion == '3':
        print("\n👋 Cancelado")
        sys.exit(0)
    else:
        print("\n❌ Opción inválida")
        sys.exit(1)

if __name__ == "__main__":
    menu_interactivo()