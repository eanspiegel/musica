import asyncio
import os
import requests
import base64
import urllib.parse
import re
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC, TRCK, TPOS, ID3NoHeaderError
from mutagen.oggopus import OggOpus
from mutagen.flac import Picture

class MetadataService:
    """Servicio para etiquetar archivos de audio usando iTunes."""
    
    def __init__(self):
        pass # No requiere inicialización de servicios externos
        
    async def _etiquetar_async(self, ruta_archivo: str, status_callback=None):
        if status_callback: status_callback(f"🔍 Buscando metadatos (iTunes)...")
        
        nombre_archivo = os.path.basename(ruta_archivo)
        # Quitar extensión y limpiar nombre
        titulo_busqueda = os.path.splitext(nombre_archivo)[0]
        # Limpieza básica: quitar paréntesis con info extra (Official Video, Lyrics, etc)
        clean_query = re.sub(r'\([^)]*\)|\[[^\]]*\]', '', titulo_busqueda).strip()
        
        # Variables de metadatos (valores por defecto)
        titulo = titulo_busqueda
        artista = "Desconocido"
        album = "Sencillo"
        genero = "Desconocido"
        track_number = None
        disc_number = None
        disc_count = None
        imagen_url = None
        
        datos_encontrados = False

        # --- ITUNES SEARCH ---
        try:
            encoded_query = urllib.parse.quote(clean_query)
            url_itunes = f"https://itunes.apple.com/search?term={encoded_query}&media=music&entity=song&limit=1"
            
            # Usar asyncio.to_thread para no bloquear con requests
            resp = await asyncio.to_thread(requests.get, url_itunes, timeout=5)
            
            if resp.status_code == 200:
                data = resp.json()
                if data['resultCount'] > 0:
                    res = data['results'][0]
                    titulo = res.get('trackName', titulo)
                    artista = res.get('artistName', artista)
                    album = res.get('collectionName', album)
                    genero = res.get('primaryGenreName', genero)
                    track_number = res.get('trackNumber', track_number)
                    disc_number = res.get('discNumber')
                    disc_count = res.get('discCount')
                    imagen_url = res.get('artworkUrl100', imagen_url)
                    if imagen_url: imagen_url = imagen_url.replace('100x100', '600x600') # Mejor calidad
                    
                    print(f"✅ Encontrado en iTunes: {titulo} - {artista}")
                    datos_encontrados = True
                    if status_callback: status_callback(f"✅ Tags: {titulo} - {artista}")
        except Exception as e:
            print(f"Error iTunes: {e}")

        if not datos_encontrados:
            print(f"⚠️ No se encontraron metadatos para: {nombre_archivo}")
            if status_callback: status_callback("⚠️ Sin metadatos")
            # Aún si no encontramos nada, podríamos querer guardar el título limpio
            # pero por ahora dejamos que el usuario decida si quiere sus archivos "crudos" o con lo que haya

        # --- GUARDAR TAGS ---
        try:
            _, ext = os.path.splitext(ruta_archivo)
            ext = ext.lower()

            if ext == '.mp3':
                self._guardar_mp3(ruta_archivo, titulo, artista, album, genero, track_number, disc_number, disc_count, imagen_url)
            elif ext == '.opus':
                self._guardar_opus(ruta_archivo, titulo, artista, album, genero, track_number, disc_number, disc_count, imagen_url)
                
            # --- RENOMBRAR ARCHIVO (Si hubo datos) ---
            if datos_encontrados and titulo and titulo != "Desconocido":
                directorio = os.path.dirname(ruta_archivo)
                # Sanitize nombre
                nombre_limpio = re.sub(r'[<>:"/\\|?*]', '', titulo) 
                nombre_limpio = nombre_limpio.strip()
                
                if nombre_limpio:
                    nuevo_nombre = f"{nombre_limpio}{ext}"
                    nueva_ruta = os.path.join(directorio, nuevo_nombre)
                    
                    # Evitar sobrescribir si ya existe
                    contador = 1
                    while os.path.exists(nueva_ruta):
                        nuevo_nombre = f"{nombre_limpio} ({contador}){ext}"
                        nueva_ruta = os.path.join(directorio, nuevo_nombre)
                        contador += 1
                        
                    try:
                        os.rename(ruta_archivo, nueva_ruta)
                        print(f"   ✨ Renombrado a: {nuevo_nombre}")
                        if status_callback: status_callback(f"✨ Renombrado: {nuevo_nombre}")
                    except Exception as e:
                        print(f"Error al renombrar: {e}")

        except Exception as e:
            print(f"Error guardando tags: {e}")

    def _guardar_mp3(self, ruta, titulo, artista, album, genero, track_number, disc_number, disc_count, imagen_url):
        try:
            try:
                audio = EasyID3(ruta)
            except ID3NoHeaderError:
                audio = EasyID3()
                audio.filename = ruta
                audio.save()
                audio = EasyID3(ruta)

            audio['title'] = titulo
            audio['artist'] = artista
            audio['album'] = album
            audio['genre'] = genero
            if track_number:
                audio['tracknumber'] = str(track_number)
            if disc_number:
                audio['discnumber'] = str(disc_number) # EasyID3 soporta discnumber
            audio.save()

            if imagen_url or track_number or disc_number:
                audio_full = ID3(ruta)
                if imagen_url:
                    img_data = requests.get(imagen_url).content
                    audio_full.delall("APIC")
                    audio_full.add(APIC(encoding=3, mime='image/jpeg', type=3, desc=u'Cover', data=img_data))
                
                if track_number:
                    audio_full.add(TRCK(encoding=3, text=str(track_number)))
                
                if disc_number:
                    disk_text = str(disc_number)
                    if disc_count: disk_text += f"/{disc_count}"
                    audio_full.add(TPOS(encoding=3, text=disk_text))

                audio_full.save(v2_version=3)
        except Exception as e:
            print(f"Error guardando MP3 tags: {e}")

    def _guardar_opus(self, ruta, titulo, artista, album, genero, track_number, disc_number, disc_count, imagen_url):
        try:
            audio = OggOpus(ruta)
            audio['TITLE'] = titulo
            audio['ARTIST'] = artista
            audio['ALBUM'] = album
            audio['GENRE'] = genero
            if track_number:
                audio['TRACKNUMBER'] = str(track_number)
            if disc_number:
                 audio['DISCNUMBER'] = str(disc_number)
            if disc_count:
                 audio['DISCTOTAL'] = str(disc_count)

            if imagen_url:
                img_data = requests.get(imagen_url).content
                p = Picture()
                p.data = img_data
                p.type = 3
                p.mime = "image/jpeg"
                p.desc = "Cover"
                audio["metadata_block_picture"] = [base64.b64encode(p.write()).decode("ascii")]
            
            audio.save()
        except Exception as e:
            print(f"Error guardando OPUS tags: {e}")

    def etiquetar(self, ruta_archivo: str, status_callback=None):
        """Método síncrono para llamar desde otros hilos."""
        try:
            asyncio.run(self._etiquetar_async(ruta_archivo, status_callback))
        except Exception as e:
            print(f"Error fatal en etiquetar: {e}")
