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
        
    async def _etiquetar_async(self, ruta_archivo: str, artista_hint: str = None, status_callback=None):
        if status_callback: status_callback(f"🔍 Buscando metadatos (iTunes)...")
        
        nombre_archivo = os.path.basename(ruta_archivo)
        # Quitar extensión y limpiar nombre
        titulo_busqueda = os.path.splitext(nombre_archivo)[0]
        # Limpieza básica: quitar paréntesis con info extra (Official Video, Lyrics, etc)
        clean_query = re.sub(r'\([^)]*\)|\[[^\]]*\]', '', titulo_busqueda).strip()
        
        # --- MEJORA DE BÚSQUEDA ---
        term_busqueda = clean_query
        if artista_hint:
            # Limpiar cosas "VEVO" "Official" del canal
            artist_clean = re.sub(r'(VEVO|Official|Topic)', '', artista_hint, flags=re.IGNORECASE).strip()
            if artist_clean.lower() not in clean_query.lower():
                term_busqueda = f"{clean_query} {artist_clean}"
        
        # Variables de metadatos (valores por defecto)
        titulo = titulo_busqueda
        artista = artista_hint or "Desconocido"
        album = "Sencillo"
        genero = "Desconocido"
        track_number = None
        disc_number = None
        disc_count = None
        imagen_url = None
        
        datos_encontrados = False

        # --- ESTRATEGIAS DE BÚSQUEDA ---
        estrategias = []
        
        # 1. Estrategia Principal: Título Limpio + Artista Hint
        q1 = clean_query
        if artista_hint:
            artist_clean = re.sub(r'(VEVO|Official|Topic)', '', artista_hint, flags=re.IGNORECASE).strip()
            # Solo agregar si no parece duplicado
            if artist_clean.lower() not in clean_query.lower():
                q1 = f"{clean_query} {artist_clean}"
        estrategias.append(q1)
        
        # 2. Estrategia "Guion": Si el título tiene "Artist - Song", buscar solo "Song Artist"
        if " - " in titulo_busqueda:
            parts = titulo_busqueda.split(" - ", 1)
            if len(parts) == 2:
                # Asumimos "Artist - Song" -> Buscar "Song Artist"
                estrategias.append(f"{parts[1]} {parts[0]}")
                # O solo la canción si tenemos hint
                if artista_hint:
                    estrategias.append(f"{parts[1]} {artista_hint}")

        # 3. Estrategia Desesperada: Solo el título limpio (riesgo de mal match, pero mejor que nada)
        estrategias.append(clean_query)

        # --- CICLO DE BÚSQUEDA ---
        for query in estrategias:
            if datos_encontrados: break
            
            print(f"🔎 Probando búsqueda iTunes: '{query}'")
            try:
                encoded_query = urllib.parse.quote(query)
                url_itunes = f"https://itunes.apple.com/search?term={encoded_query}&media=music&entity=song&limit=1"
                
                resp = await asyncio.to_thread(requests.get, url_itunes, timeout=5)
                
                if resp.status_code == 200:
                    data = resp.json()
                    if data['resultCount'] > 0:
                        res = data['results'][0]
                        candidate_title = res.get('trackName')
                        candidate_artist = res.get('artistName')
                        
                        # VALIDAR COINCIDENCIA (Evitar falsos positivos locos)
                        if not self._es_coincidencia_valida(clean_query, candidate_title):
                            print(f"⚠️ Rechazado por baja similitud título: '{candidate_title}' vs '{clean_query}'")
                            continue
                            
                        # VALIDAR ARTISTA (Si la query tenía info de artista, asegurar que coincida)
                        # Estrategia 3 (Solo titulo) no tiene info de artista en query, asi que ahi confiamos más en el hint o lo que salga
                        # Pero Estrategias 1 y 2 tienen el artista en la query.
                        if not self._es_artista_valido(query, candidate_artist, clean_query):
                             print(f"⚠️ Rechazado por artista no coincidente: '{candidate_artist}' en query '{query}'")
                             continue

                        titulo = candidate_title or titulo
                        artista = candidate_artist or artista
                        album = res.get('collectionName', album)
                        genero = res.get('primaryGenreName', genero)
                        track_number = res.get('trackNumber', track_number)
                        disc_number = res.get('discNumber')
                        disc_count = res.get('discCount')
                        imagen_url = res.get('artworkUrl100', imagen_url)
                        if imagen_url: imagen_url = imagen_url.replace('100x100', '600x600') # Mejor calidad
                        
                        # --- LIMPIEZA DE ARTISTA (Labels conocidos) ---
                        artista = self._limpiar_artista(artista)
                        
                        print(f"✅ Encontrado en iTunes: {titulo} - {artista}")
                        datos_encontrados = True
                        if status_callback: status_callback(f"✅ Tags: {titulo} - {artista}")
            except Exception as e:
                print(f"Error iTunes: {e}")

        if not datos_encontrados:
            print(f"⚠️ No se encontraron metadatos para: {nombre_archivo}")
            if status_callback: status_callback("⚠️ Sin metadatos")

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
                    
                    # SOBRESCRIBIR si existe (Fix duplicates aka "(1)")
                    try:
                        if os.path.exists(nueva_ruta) and nueva_ruta != ruta_archivo:
                            os.remove(nueva_ruta) # Borrar la vieja versión

                        os.replace(ruta_archivo, nueva_ruta) # Renombrar/Mover
                        print(f"   ✨ Renombrado a: {nuevo_nombre}")
                        if status_callback: status_callback(f"✨ Renombrado: {nuevo_nombre}")
                        
                        # Retornar nuevos datos para análisis de playlist
                        return {'artist': artista, 'album': album, 'title': titulo, 'file_path': nueva_ruta}
                    except Exception as e:
                        print(f"Error al renombrar: {e}")
            
            # Si no se renombró pero se encontraron datos (ej: mp3 sin cambio de nombre)
            if datos_encontrados:
                 return {'artist': artista, 'album': album, 'title': titulo, 'file_path': ruta_archivo}

        except Exception as e:
            print(f"Error guardando tags: {e}")
            
        return None

    def _es_coincidencia_valida(self, original: str, encontrado: str) -> bool:
        if not original or not encontrado: return False
        
        from difflib import SequenceMatcher
        # Normalizar para comparar
        a = original.lower().strip()
        b = encontrado.lower().strip()
        
        # Si uno está contenido en el otro, es buena señal (ej: "Demons" in "Joji - Demons")
        if a in b or b in a: return True
        
        # Ratio de similitud
        ratio = SequenceMatcher(None, a, b).ratio()
        return ratio > 0.4 # Deben parecerse al menos un 40%

    def _es_artista_valido(self, query: str, artist_found: str, title_clean: str) -> bool:
        """
        Verifica si el artista encontrado tiene sentido con la query.
        Si la query es 'Song Artist', el 'artist_found' debería estar (parcialmente) en 'query'.
        Excluimos el título de la canción para no confundirnos.
        """
        if not artist_found: return False
        q = query.lower()
        a = artist_found.lower()
        t = title_clean.lower()
        
        # Si la query es CORTA (probablemente solo título, estrategia 3), somos más permisivos
        # O si la query es IGUAL al título limpio
        if q == t: 
            return True 

        # Quitamos el título de la query para ver qué queda (potencialmente el artista)
        # Esto es heurístíco
        remainder = q.replace(t, '').strip()
        
        # Si no queda casi nada, es query solo titulo
        if len(remainder) < 2: return True
        
        # Normalizar artista encontrado (quitar separadores)
        # Si "Joji" está en "worldstar money joji" -> OK
        # Si "Rickneidy" está en "worldstar money joji" -> NO
        
        # Tokenize artist found
        artist_tokens = set(re.split(r'[\s,&]+', a))
        query_tokens = set(re.split(r'[\s,&]+', remainder))
        
        # Si hay intersección de palabras relevantes
        intersection = artist_tokens.intersection(query_tokens)
        if intersection: return True
        
        # Check simple substrings
        if a in q: return True
        
        return False

    def _limpiar_artista(self, artista_str: str) -> str:
        if not artista_str: return "Desconocido"
        
        # Lista de "Labels" o textos que queremos quitar del artista
        ignore_list = ['88rising', 'Records', 'Entertainment', 'Inc.']
        
        temp_artist = artista_str
        for ignore in ignore_list:
            # Reemplazar palabra completa ignorando mayúsculas/minúsculas
            temp_artist = re.sub(fr'\b{re.escape(ignore)}\b', '', temp_artist, flags=re.IGNORECASE)
            
        # Limpiar separadores residuales (ej: ", & Joji" -> "Joji")
        # 1. Quitar caracteres raros al inicio/final
        temp_artist = re.sub(r'^[\s,&]+|[\s,&]+$', '', temp_artist).strip()
        # 2. Arreglar comas dobles o espacios raros
        temp_artist = re.sub(r'\s+&+\s+', ' & ', temp_artist)
        temp_artist = re.sub(r',\s*,', ',', temp_artist)
        
        # Si borramos todo por error (ej: el artista ERA 88rising), devolvemos el original
        if not temp_artist:
            return artista_str
            
        return temp_artist

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

    def etiquetar(self, ruta_archivo: str, artista_hint: str = None, status_callback=None):
        """Método síncrono para llamar desde otros hilos."""
        try:
            return asyncio.run(self._etiquetar_async(ruta_archivo, artista_hint, status_callback))
        except Exception as e:
            print(f"Error fatal en etiquetar: {e}")
            return None
