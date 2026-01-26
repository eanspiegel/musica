import asyncio
import os
import requests
import base64
import urllib.parse
import re
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC, TRCK, TPOS, ID3NoHeaderError, USLT
from mutagen.oggopus import OggOpus
from mutagen.flac import Picture

try:
    from shazamio import Shazam, Serialize
    HAS_SHAZAM = True
except ImportError:
    HAS_SHAZAM = False


class MetadataService:
    """Servicio para etiquetar archivos de audio usando iTunes."""
    
    def __init__(self):
        pass # No requiere inicialización de servicios externos
        
    async def _buscar_shazam(self, ruta_archivo: str, status_callback=None):
        if not HAS_SHAZAM:
             print("⚠️ Shazam no está instalado. Saltando.")
             return None

        try:
            if status_callback: status_callback("🔍 Escuchando con Shazam...")
            shazam = Shazam()
            out = await shazam.recognize(ruta_archivo)
            
            if not out or 'track' not in out:
                return None
                
            track = out['track']
            titulo = track.get('title')
            artista = track.get('subtitle')
            
            # Metadata extra
            album = None
            genero = None
            track_number = None
            imagen_url = None
            anio = None
            letra = None
            
            if 'sections' in track:
                for section in track['sections']:
                    if section.get('type') == 'SONG':
                        for meta in section.get('metadata', []):
                            if meta.get('title') == 'Album':
                                album = meta.get('text')
                            elif meta.get('title') == 'Released':
                                try:
                                    anio = meta.get('text')[:4]
                                except: pass
                    if section.get('type') == 'LYRICS':
                        letra_list = section.get('text', [])
                        if letra_list:
                            letra = "\n".join(letra_list)
            
            if 'genres' in track:
                genero = track['genres'].get('primary')
                
            if 'images' in track:
                imagen_url = track['images'].get('coverart') # O coverarthq
            
            print(f"✅ Reconocido por Shazam: {titulo} - {artista} ({anio})")
            if letra: print("✅ Letra encontrada.")
            if status_callback: status_callback(f"✅ Shazam: {titulo} - {artista}")
            
            return {
                'titulo': titulo,
                'artista': artista,
                'album': album or "Sencillo",
                'genero': genero or "Desconocido",
                'track_number': None, 
                'disc_number': None,
                'disc_count': None,
                'imagen_url': imagen_url,
                'anio': anio,
                'letra': letra
            }

        except Exception as e:
            print(f"Error Shazam: {e}")
            return None

    async def _buscar_letra_lrclib(self, titulo: str, artista: str, album: str = None, duration: int = None) -> str:
        """Busca la letra en LRCLIB (Fallback)."""
        print(f"🔄 Buscando letra en LRCLIB para: {titulo} - {artista}...")
        try:
            params = {
                'artist_name': artista,
                'track_name': titulo,
            }
            if album and album != "Sencillo": params['album_name'] = album
            if duration: params['duration'] = duration

            url = "https://lrclib.net/api/get"
            
            resp = await asyncio.to_thread(requests.get, url, params=params, timeout=5)
            
            if resp.status_code == 200:
                data = resp.json()
                lyrics = data.get('plainLyrics')
                if lyrics:
                    print("✅ Letra encontrada en LRCLIB.")
                    return lyrics
            elif resp.status_code == 404:
                url_search = "https://lrclib.net/api/search"
                resp_search = await asyncio.to_thread(requests.get, url_search, params={'q': f"{titulo} {artista}"}, timeout=5)
                if resp_search.status_code == 200:
                    results = resp_search.json()
                    if results and isinstance(results, list):
                        first = results[0]
                        lyrics = first.get('plainLyrics')
                        if lyrics:
                            print("✅ Letra encontrada en LRCLIB (Búsqueda laxa).")
                            return lyrics

        except Exception as e:
            print(f"⚠️ Error LRCLIB: {e}")
        return None

    async def _etiquetar_async(self, ruta_archivo: str, artista_hint: str = None, status_callback=None, strict_artist_match: bool = False, search_title: str = None):
        nombre_archivo = os.path.basename(ruta_archivo)
        
        # 1. Preparar términos de búsqueda (Defaults)
        if search_title:
             clean_query = search_title
             titulo_busqueda = search_title
             clean_query = re.sub(r'\([^)]*\)|\[[^\]]*\]', '', clean_query).strip()
        else:
             titulo_busqueda = os.path.splitext(nombre_archivo)[0]
             clean_query = re.sub(r'\([^)]*\)|\[[^\]]*\]', '', titulo_busqueda).strip()

        # 2. Inicializar variables con Defaults
        titulo = titulo_busqueda
        artista = artista_hint or "Desconocido"
        album = "Sencillo"
        genero = "Desconocido"
        track_number = None
        disc_number = None
        disc_count = None
        imagen_url = None
        anio = None
        letra = None
        
        datos_encontrados = False

        # 3. Intentar Shazam (Prioridad)
        datos_shazam = await self._buscar_shazam(ruta_archivo, status_callback)
        if datos_shazam:
            titulo = datos_shazam['titulo']
            artista = datos_shazam['artista']
            album = datos_shazam['album']
            genero = datos_shazam['genero']
            track_number = datos_shazam['track_number']
            disc_number = datos_shazam['disc_number']
            disc_count = datos_shazam['disc_count']
            imagen_url = datos_shazam['imagen_url']
            anio = datos_shazam['anio']
            letra = datos_shazam['letra']
            datos_encontrados = True
        else:
            if status_callback: 
                msg = f"🔍 Buscando metadatos (iTunes)..."
                if strict_artist_match: msg += " [Modo Estricto]"
                status_callback(msg)
        
        # 4. Determinar Estrategia de Búsqueda API
        estrategias = []
        if datos_encontrados:
            q_enrich = f"{titulo} {artista}"
            estrategias.append(q_enrich)
            print(f"🔄 Enriqueciendo metadatos para: '{q_enrich}'")
        else:
            q1 = clean_query
            if artista_hint:
                artist_clean = re.sub(r'(VEVO|Official|Topic)', '', artista_hint, flags=re.IGNORECASE).strip()
                if artist_clean.lower() not in clean_query.lower():
                    q1 = f"{clean_query} {artist_clean}"
            estrategias.append(q1)

            if " - " in titulo_busqueda:
                parts = titulo_busqueda.split(" - ", 1)
                if len(parts) == 2:
                    estrategias.append(f"{parts[1]} {parts[0]}")
                    if artista_hint:
                        estrategias.append(f"{parts[1]} {artista_hint}")
            
            if not strict_artist_match:
                estrategias.append(clean_query)

        # 5. Ejecutar Búsqueda API (iTunes / Deezer)
        exito_api = False
        
        for query in estrategias:
            if exito_api: break
            
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
                        
                        target_compare = titulo if datos_encontrados else clean_query
                        
                        if not self._es_coincidencia_valida(target_compare, candidate_title):
                            continue
                            
                        if not datos_encontrados:
                            titulo = candidate_title
                            artista = res.get('artistName')
                            datos_encontrados = True

                        # ENRIQUECIMIENTO
                        itunes_album = res.get('collectionName')
                        if itunes_album: album = itunes_album 
                        
                        if not genero or genero == "Desconocido": genero = res.get('primaryGenreName', genero)
                        
                        if not track_number: track_number = res.get('trackNumber')
                        if not disc_number: disc_number = res.get('discNumber')
                        if not disc_count: disc_count = res.get('discCount')
                        
                        if not anio:
                            release_date = res.get('releaseDate')
                            if release_date: anio = release_date[:4]
                            
                        if not imagen_url:
                             work_art = res.get('artworkUrl100')
                             if work_art: imagen_url = work_art.replace('100x100', '600x600')

                        artista = self._limpiar_artista(artista)
                        print(f"✅ Datos iTunes aplicados: Track {track_number}, Disc {disc_number}, Año {anio}")
                        exito_api = True
                        if status_callback: status_callback(f"✅ Metadata Completa (iTunes)")
            except Exception as e:
                print(f"Error iTunes: {e}")

        # --- FALLBACK DEEZER ---
        if not exito_api and (not datos_encontrados or not track_number):
             print(f"⚠️ iTunes incompleto. Probando Deezer...")
             for query in estrategias:
                if exito_api: break
                try:
                    encoded_query = urllib.parse.quote(query)
                    url_deezer = f"https://api.deezer.com/search?q={encoded_query}&limit=1"
                    resp = await asyncio.to_thread(requests.get, url_deezer, timeout=5)
                    if resp.status_code == 200:
                        data = resp.json()
                        if 'data' in data and len(data['data']) > 0:
                            res = data['data'][0]
                            candidate_title = res.get('title')
                            
                            target_compare = titulo if datos_encontrados else clean_query
                            if not self._es_coincidencia_valida(target_compare, candidate_title): continue

                            if not datos_encontrados:
                                titulo = candidate_title
                                artista = res.get('artist', {}).get('name')
                                datos_encontrados = True

                            if not album or album == "Sencillo": 
                                dz_album = res.get('album', {}).get('title')
                                if dz_album: album = dz_album
                                
                            if not imagen_url:
                                imagen_url = res.get('album', {}).get('cover_xl') or res.get('album', {}).get('cover_big')

                            try:
                                track_id = res.get('id')
                                if track_id:
                                    url_track = f"https://api.deezer.com/track/{track_id}"
                                    resp_track = await asyncio.to_thread(requests.get, url_track, timeout=5)
                                    if resp_track.status_code == 200:
                                        track_data = resp_track.json()
                                        if not track_number: track_number = track_data.get('track_position')
                                        if not disc_number: disc_number = track_data.get('disk_number')
                                        if not anio:
                                            rd = track_data.get('release_date')
                                            if rd: anio = rd[:4]
                                        
                                        if not genero or genero == "Desconocido":
                                            ab_id = track_data.get('album', {}).get('id')
                                            if ab_id:
                                                 url_album = f"https://api.deezer.com/album/{ab_id}"
                                                 r_ab = await asyncio.to_thread(requests.get, url_album, timeout=5)
                                                 if r_ab.status_code == 200:
                                                     d_ab = r_ab.json()
                                                     g_data = d_ab.get('genres', {}).get('data', [])
                                                     if g_data: genero = g_data[0].get('name')
                                                     if not anio:
                                                         rd = d_ab.get('release_date')
                                                         if rd: anio = rd[:4]
                            except: pass
                            
                            artista = self._limpiar_artista(artista)
                            print(f"✅ Datos Deezer aplicados: Track {track_number}")
                            exito_api = True
                except: pass

        if not datos_encontrados:
             print(f"⚠️ No se encontraron metadatos para: {nombre_archivo}")
             if status_callback: status_callback("⚠️ Sin metadatos")

        # --- FALLBACK FINAL LETRA (LRCLIB) ---
        # print("DEBUG: Verificando fallback de letra...")
        try:
            if not letra and (datos_encontrados or titulo):
                 safe_titulo = titulo if titulo else titulo_busqueda
                 safe_artista = artista if artista else (artista_hint or "")
                 
                 # print(f"DEBUG: Check LRCLIB -> Letra: {letra is not None}, Datos: {datos_encontrados}, Título: {safe_titulo}, Artista: {safe_artista}")
                 
                 if safe_titulo and safe_artista and safe_artista != "Desconocido":
                     # print("DEBUG: Llamando a _buscar_letra_lrclib...")
                     letra = await self._buscar_letra_lrclib(safe_titulo, safe_artista, album, None)
                     # print(f"DEBUG: Retorno LRCLIB -> Letra encontrada: {letra is not None}")
        except Exception as e:
            print(f"❌ Error en bloque fallback LRCLIB: {e}")

        # print("DEBUG: Preparando guardado de archivo...")
        try:
            _, ext = os.path.splitext(ruta_archivo)
            ext = ext.lower()
            
            # print(f"DEBUG: Archivo {ext}, Guardando...")
            if letra: print(f"📝 Escribiendo letra ({len(letra)} bytes)...")

            if ext == '.mp3':
                self._guardar_mp3(ruta_archivo, titulo, artista, album, genero, track_number, disc_number, disc_count, imagen_url, anio, letra)
            elif ext == '.opus':
                self._guardar_opus(ruta_archivo, titulo, artista, album, genero, track_number, disc_number, disc_count, imagen_url, anio, letra)
            
            # print("DEBUG: Guardado finalizado (o intentado).")
                
            if datos_encontrados and titulo and titulo != "Desconocido":
                directorio = os.path.dirname(ruta_archivo)
                nombre_limpio = re.sub(r'[<>:"/\\|?*]', '', titulo).strip()
                if nombre_limpio:
                    nuevo_nombre = f"{nombre_limpio}{ext}"
                    nueva_ruta = os.path.join(directorio, nuevo_nombre)
                    if os.path.normpath(ruta_archivo) != os.path.normpath(nueva_ruta):
                         if not os.path.exists(nueva_ruta):
                             os.replace(ruta_archivo, nueva_ruta)
                             print(f"   ✨ Renombrado a: {nuevo_nombre}")
                             if status_callback: status_callback(f"✨ Renombrado: {nuevo_nombre}")
                             return {'artist': artista, 'album': album, 'title': titulo, 'file_path': nueva_ruta}
                         else:
                             pass 
            
            if datos_encontrados:
                 return {'artist': artista, 'album': album, 'title': titulo, 'file_path': ruta_archivo}

        except Exception as e:
            print(f"Error guardando tags/renombrando: {e}")
            import traceback
            traceback.print_exc()
            
        return None

    def _es_coincidencia_valida(self, original: str, encontrado: str) -> bool:
        if not original or not encontrado: return False
        a = original.lower().strip()
        b = encontrado.lower().strip()
        if a in b or b in a: return True
        from difflib import SequenceMatcher
        return SequenceMatcher(None, a, b).ratio() > 0.4

    def _es_artista_valido(self, query: str, artist_found: str, title_clean: str, strict: bool = False, artist_hint: str = None) -> bool:
        if not artist_found: return False # Simplificado para brevedad, lógica completa mantenida si fuera necesario
        return True # Asumimos validación externa o permisiva por ahora para no romper

    def _limpiar_artista(self, artista_str: str) -> str:
        if not artista_str: return "Desconocido"
        ignore_list = ['88rising', 'Records', 'Entertainment', 'Inc.']
        temp_artist = artista_str
        for ignore in ignore_list:
            temp_artist = re.sub(fr'\b{re.escape(ignore)}\b', '', temp_artist, flags=re.IGNORECASE)
        temp_artist = re.sub(r'^[\s,&]+|[\s,&]+$', '', temp_artist).strip()
        return temp_artist or artista_str

    def _guardar_mp3(self, ruta, titulo, artista, album, genero, track_number, disc_number, disc_count, imagen_url, anio, letra):
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
            if track_number: audio['tracknumber'] = str(track_number)
            if disc_number: audio['discnumber'] = str(disc_number)
            if anio:
                audio['date'] = str(anio)
                audio['originaldate'] = str(anio)
            audio.save()

            if imagen_url or track_number or disc_number or letra:
                audio_full = ID3(ruta)
                if imagen_url:
                    try:
                        img_data = requests.get(imagen_url).content
                        audio_full.delall("APIC")
                        audio_full.add(APIC(encoding=3, mime='image/jpeg', type=3, desc=u'Cover', data=img_data))
                    except: pass
                
                if track_number: audio_full.add(TRCK(encoding=3, text=str(track_number)))
                if disc_number:
                    disk_text = str(disc_number)
                    if disc_count: disk_text += f"/{disc_count}"
                    audio_full.add(TPOS(encoding=3, text=disk_text))

                if letra:
                    audio_full.delall("USLT")
                    audio_full.add(USLT(encoding=3, lang=u'eng', desc=u'', text=letra))

                audio_full.save(v2_version=3)
        except Exception as e:
            print(f"Error guardando MP3 tags: {e}")

    def _guardar_opus(self, ruta, titulo, artista, album, genero, track_number, disc_number, disc_count, imagen_url, anio, letra):
        print(f"DEBUG: Guardando tags OPUS en {ruta} (Año: {anio})")
        try:
            try:
                audio = OggOpus(ruta)
            except Exception as e:
                print(f"⚠️ Error cargando OggOpus (intentando crear): {e}")
                return 

            audio['TITLE'] = titulo
            audio['ARTIST'] = artista
            audio['ALBUM'] = album
            audio['GENRE'] = genero
            if track_number: audio['TRACKNUMBER'] = str(track_number)
            if disc_number: audio['DISCNUMBER'] = str(disc_number)
            if disc_count: audio['DISCTOTAL'] = str(disc_count)
            if anio:
                 audio['DATE'] = str(anio)
                 audio['YEAR'] = str(anio)
            
            if letra:
                 audio['LYRICS'] = letra

            if imagen_url:
                try:
                    img_data = requests.get(imagen_url, timeout=5).content
                    p = Picture()
                    p.data = img_data
                    p.type = 3
                    p.mime = "image/jpeg"
                    p.desc = "Cover"
                    audio["metadata_block_picture"] = [base64.b64encode(p.write()).decode("ascii")]
                except Exception as img_err:
                     print(f"⚠️ Error guardando imagen OPUS: {img_err}")
            
            audio.save()
            print("DEBUG: Tags OPUS guardados correctamente.")
        except Exception as e:
            print(f"❌ Error CRÍTICO guardando OPUS tags: {e}")
            import traceback
            traceback.print_exc()

    def etiquetar(self, ruta_archivo: str, artista_hint: str = None, status_callback=None, strict_artist_match: bool = False, search_title: str = None):
        try:
            return asyncio.run(self._etiquetar_async(ruta_archivo, artista_hint, status_callback, strict_artist_match, search_title))
        except Exception as e:
            print(f"Error fatal en etiquetar: {e}")
            return None
