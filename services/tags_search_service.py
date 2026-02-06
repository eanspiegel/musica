"""
Servicio para búsqueda de metadatos en diferentes APIs.
"""
import asyncio
import requests
import urllib.parse

try:
    from shazamio import Shazam
    HAS_SHAZAM = True
except ImportError:
    HAS_SHAZAM = False


class TagsSearchService:
    """Servicio para buscar metadatos en Shazam, iTunes y Deezer."""
    
    def __init__(self):
        pass
    
    async def reconocer_con_shazam(self, ruta_archivo: str) -> dict:
        """Reconoce una canción usando Shazam con el archivo de audio."""
        if not HAS_SHAZAM:
            return None
            
        try:
            print("🔍 Reconociendo con Shazam...")
            shazam = Shazam()
            out = await shazam.recognize(ruta_archivo)
            
            if not out or 'track' not in out:
                return None
            
            track = out['track']
            titulo = track.get('title')
            artista = track.get('subtitle')
            
            if not titulo or not artista:
                return None
            
            # Extraer metadatos adicionales
            album = None
            genero = None
            imagen_url = None
            año = None
            tipo = 'Single'
            
            # Buscar en sections
            if 'sections' in track:
                for section in track['sections']:
                    if section.get('type') == 'SONG':
                        for meta in section.get('metadata', []):
                            if meta.get('title') == 'Album':
                                album = meta.get('text')
                                if album and 'single' not in album.lower():
                                    tipo = 'Álbum'
                            elif meta.get('title') == 'Released':
                                try:
                                    año = meta.get('text')[:4]
                                except:
                                    pass
            
            # Género
            if 'genres' in track:
                genero = track['genres'].get('primary', '')
            
            # Imagen
            if 'images' in track:
                imagen_url = track['images'].get('coverarthq') or track['images'].get('coverart')
            
            resultado = {
                'fuente': 'Shazam',
                'titulo': titulo,
                'artista': artista,
                'album': album or 'Desconocido',
                'genero': genero or '',
                'año': año or '',
                'track_number': '',
                'disc_number': '',
                'imagen_url': imagen_url,
                'tipo': tipo
            }
            
            print(f"✅ Shazam encontró: {titulo} - {artista}")
            return resultado
        
        except Exception as e:
            print(f"⚠️ Error reconocimiento Shazam: {e}")
            return None
    
    def buscar_en_itunes(self, query: str, titulo_original: str) -> list:
        """Busca canciones en iTunes API."""
        resultados = []
        
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://itunes.apple.com/search?term={encoded_query}&media=music&entity=song&limit=10"
            resp = requests.get(url, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                for track in data.get('results', []):
                    track_name = track.get('trackName', '').lower()
                    if titulo_original.lower() not in track_name:
                        continue
                    
                    resultado = {
                        'fuente': 'iTunes',
                        'titulo': track.get('trackName'),
                        'artista': track.get('artistName'),
                        'album': track.get('collectionName'),
                        'genero': track.get('primaryGenreName'),
                        'año': track.get('releaseDate', '')[:4] if track.get('releaseDate') else '',
                        'track_number': str(track.get('trackNumber', '')),
                        'disc_number': str(track.get('discNumber', '')),
                        'imagen_url': track.get('artworkUrl100', '').replace('100x100', '600x600'),
                        'tipo': 'Álbum' if track.get('collectionType') == 'Album' else 'Single'
                    }
                    resultados.append(resultado)
        except Exception as e:
            print(f"Error búsqueda iTunes: {e}")
        
        return resultados
    
    def buscar_en_deezer(self, query: str, titulo_original: str) -> list:
        """Busca canciones en Deezer API."""
        resultados = []
        
        try:
            encoded_query = urllib.parse.quote(query)
            url = f"https://api.deezer.com/search?q={encoded_query}&limit=10"
            resp = requests.get(url, timeout=10)
            
            if resp.status_code == 200:
                data = resp.json()
                for track in data.get('data', []):
                    track_name = track.get('title', '').lower()
                    if titulo_original.lower() not in track_name:
                        continue
                    
                    album_info = track.get('album', {})
                    artist_info = track.get('artist', {})
                    
                    resultado = {
                        'fuente': 'Deezer',
                        'titulo': track.get('title'),
                        'artista': artist_info.get('name'),
                        'album': album_info.get('title'),
                        'genero': '',
                        'año': track.get('release_date', '')[:4] if track.get('release_date') else '',
                        'track_number': str(track.get('track_position', '')),
                        'disc_number': str(track.get('disk_number', '')),
                        'imagen_url': album_info.get('cover_xl') or album_info.get('cover_big'),
                        'tipo': 'Álbum' if album_info.get('record_type') == 'album' else 'Single'
                    }
                    resultados.append(resultado)
        except Exception as e:
            print(f"Error búsqueda Deezer: {e}")
        
        return resultados
    
    def buscar_metadatos(self, titulo: str, artista: str, ruta_archivo: str = None) -> list:
        """
        Busca metadatos en todas las fuentes disponibles.
        
        Args:
            titulo: Título de la canción
            artista: Nombre del artista
            ruta_archivo: Ruta del archivo de audio para reconocimiento con Shazam
        
        Returns:
            Lista de resultados de todas las fuentes
        """
        resultados = []
        
        # Construir query
        query = titulo
        if artista:
            query = f"{titulo} {artista}"
        
        # 1. Shazam (si hay archivo)
        if HAS_SHAZAM and ruta_archivo:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                resultado_shazam = loop.run_until_complete(self.reconocer_con_shazam(ruta_archivo))
                loop.close()
                
                if resultado_shazam:
                    resultados.append(resultado_shazam)
            except Exception as e:
                print(f"⚠️ Error con Shazam: {e}")
        
        # 2. iTunes
        resultados_itunes = self.buscar_en_itunes(query, titulo)
        for resultado in resultados_itunes:
            if not any(r['titulo'] == resultado['titulo'] and r['album'] == resultado['album'] for r in resultados):
                resultados.append(resultado)
        
        # 3. Deezer (si necesitamos más resultados)
        if len(resultados) < 10:
            resultados_deezer = self.buscar_en_deezer(query, titulo)
            for resultado in resultados_deezer:
                if not any(r['titulo'] == resultado['titulo'] and r['album'] == resultado['album'] for r in resultados):
                    resultados.append(resultado)
        
        return resultados
    
    def descargar_imagen(self, url: str) -> bytes:
        """Descarga una imagen desde una URL."""
        try:
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                return resp.content
        except Exception as e:
            print(f"Error descargando imagen: {e}")
        return None
