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
        
    async def _etiquetar_async(self, ruta_archivo: str, artista_hint: str = None, status_callback=None, strict_artist_match: bool = False, search_title: str = None):
        if status_callback: 
            msg = f"🔍 Buscando metadatos (iTunes)..."
            if strict_artist_match: msg += " [Modo Estricto]"
            status_callback(msg)
        
        nombre_archivo = os.path.basename(ruta_archivo)
        
        # Si tenemos título explícito (de la fuente original), usarlo en lugar del nombre de archivo saneado
        if search_title:
             clean_query = search_title
             titulo_busqueda = search_title # Para fallbacks
             # Limpieza básica igual por si acaso
             clean_query = re.sub(r'\([^)]*\)|\[[^\]]*\]', '', clean_query).strip()
        else:
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
        # Solo usar si NO es estricto
        if not strict_artist_match:
            estrategias.append(clean_query)
        else:
            print(f"🔒 Modo Estricto: Saltando búsqueda vaga '{clean_query}'")

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
                        if not self._es_artista_valido(query, candidate_artist, clean_query, strict=strict_artist_match, artist_hint=artista_hint):
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
            print(f"⚠️ iTunes falló para: {nombre_archivo}. Probando Deezer...")
            if status_callback: status_callback("⚠️ iTunes falló. Probando Deezer...")
            
            # --- FALLBACK: DEEZER ---
            for query in estrategias:
                if datos_encontrados: break
                
                print(f"🔎 Probando búsqueda Deezer: '{query}'")
                try:
                    # Deezer Search API
                    encoded_query = urllib.parse.quote(query)
                    url_deezer = f"https://api.deezer.com/search?q={encoded_query}&limit=1"
                    
                    resp = await asyncio.to_thread(requests.get, url_deezer, timeout=5)
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        if 'data' in data and len(data['data']) > 0:
                            res = data['data'][0]
                            candidate_title = res.get('title')
                            candidate_artist = res.get('artist', {}).get('name')
                            
                            # VALIDAR COINCIDENCIA
                            if not self._es_coincidencia_valida(clean_query, candidate_title):
                                print(f"⚠️ [Deezer] Rechazado por baja similitud título: '{candidate_title}' vs '{clean_query}'")
                                continue
                                
                            # VALIDAR ARTISTA
                            if not self._es_artista_valido(query, candidate_artist, clean_query, strict=strict_artist_match, artist_hint=artista_hint):
                                 print(f"⚠️ [Deezer] Rechazado por artista no coincidente: '{candidate_artist}' en query '{query}'")
                                 continue

                            titulo = candidate_title or titulo
                            artista = candidate_artist or artista
                            album = res.get('album', {}).get('title', album)
                            imagen_url = res.get('album', {}).get('cover_xl') or res.get('album', {}).get('cover_big')

                            # --- ENRIQUECER DATOS (Track & Genre) ---
                            # La búsqueda simple no da track_number ni género, hay que consultar endpoints específicos
                            try:
                                track_id = res.get('id')
                                if track_id:
                                    # 1. Detalles del Track (Numero, Disco)
                                    url_track = f"https://api.deezer.com/track/{track_id}"
                                    resp_track = await asyncio.to_thread(requests.get, url_track, timeout=5)
                                    if resp_track.status_code == 200:
                                        track_data = resp_track.json()
                                        track_number = track_data.get('track_position', track_number)
                                        disc_number = track_data.get('disk_number', disc_number)
                                        
                                        # 2. Detalles del Album (Género)
                                        # El género suele estar en el álbum, no en el track
                                        album_id = track_data.get('album', {}).get('id')
                                        if album_id:
                                            url_album = f"https://api.deezer.com/album/{album_id}"
                                            resp_album = await asyncio.to_thread(requests.get, url_album, timeout=5)
                                            if resp_album.status_code == 200:
                                                album_data_full = resp_album.json()
                                                genres_data = album_data_full.get('genres', {}).get('data', [])
                                                if genres_data:
                                                    genero = genres_data[0].get('name', genero)
                            except Exception as e:
                                print(f"⚠️ Error enriqueciendo metadatos Deezer: {e}")
                            
                            artista = self._limpiar_artista(artista)
                            
                            print(f"✅ Encontrado en Deezer: {titulo} - {artista} (Track {track_number}, {genero})")
                            datos_encontrados = True
                            if status_callback: status_callback(f"✅ Tags (Deezer): {titulo} - {artista}")
                except Exception as e:
                    print(f"Error Deezer: {e}")

        if not datos_encontrados:
            print(f"⚠️ No se encontraron metadatos{' (Estricto)' if strict_artist_match else ''} para: {nombre_archivo}")
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
                        # Normalizar rutas para comparar
                        ruta_abs = os.path.abspath(ruta_archivo)
                        nueva_abs = os.path.abspath(nueva_ruta)
                        
                        # Chequeo insensitivo (Windows)
                        mismo_archivo = (ruta_abs.lower() == nueva_abs.lower())

                        if os.path.exists(nueva_ruta) and not mismo_archivo:
                            os.remove(nueva_ruta) # Borrar la vieja versión SOLO si es otro archivo

                        if mismo_archivo and ruta_abs != nueva_abs:
                             # Caso especial: Renombrar solo mayúsculas/minúsculas en Windows
                             # "file.mp3" -> "File.mp3" requiere paso intermedio
                             temp = nueva_ruta + ".tmp_" + str(os.getpid())
                             os.rename(ruta_archivo, temp)
                             os.rename(temp, nueva_ruta)
                        else:
                             # Renombramiento normal
                             if ruta_abs != nueva_abs:
                                 os.replace(ruta_archivo, nueva_ruta)

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

    def _es_artista_valido(self, query: str, artist_found: str, title_clean: str, strict: bool = False, artist_hint: str = None) -> bool:
        """
        Verifica si el artista encontrado tiene sentido con la query.
        """
        if not artist_found: return False
        
        q = query.lower()
        a = artist_found.lower()
        t = title_clean.lower()
        
        # --- MODO ESTRICTO (Corrección de Impostores) ---
        if strict and artist_hint:
            h = artist_hint.lower()
            # En modo estricto, el artista encontrado TIENE que parecerse al Hint
            # No nos importa la query, nos importa que sea el artista que esperamos
            
            # 1. Check directo
            if h in a or a in h: return True
            
            # 2. Token overlap
            artist_tokens = set(re.split(r'[\s,&]+', a))
            hint_tokens = set(re.split(r'[\s,&]+', h))
            if artist_tokens.intersection(hint_tokens): return True
            
            # Si el hint es "Clairo" y encontramos "Heart" -> False
            return False

        # --- MODO NORMAL ---
        
        # Si la query es CORTA (probablemente solo título, estrategia 3), somos más permisivos
        # O si la query es IGUAL al título limpio
        if q == t: 
            return True 

        # Quitamos el título de la query para ver qué queda (potencialmente el artista)
        remainder = q.replace(t, '').strip()
        
        # Si no queda casi nada, es query solo titulo
        if len(remainder) < 2: return True
        
        # Normalizar artista encontrado
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

    def etiquetar(self, ruta_archivo: str, artista_hint: str = None, status_callback=None, strict_artist_match: bool = False, search_title: str = None):
        """Método síncrono para llamar desde otros hilos."""
        try:
            return asyncio.run(self._etiquetar_async(ruta_archivo, artista_hint, status_callback, strict_artist_match, search_title))
        except Exception as e:
            print(f"Error fatal en etiquetar: {e}")
            return None
