
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC, ID3NoHeaderError
from mutagen.oggopus import OggOpus
from mutagen.flac import FLAC, Picture
import os
import base64
from services.tags_search_service import TagsSearchService


class TagsController:
    
    def __init__(self):
        self.search_service = TagsSearchService()
    
    def leer_metadata(self, ruta_archivo: str) -> dict:
        """Lee los metadatos de un archivo de audio."""
        try:
            _, ext = os.path.splitext(ruta_archivo)
            ext = ext.lower()
            nombre_archivo = os.path.basename(ruta_archivo)
            
            metadata = {
                'ruta': ruta_archivo,
                'nombre': nombre_archivo,
                'titulo': None,
                'artista': None,
                'album': None,
                'genero': None,
                'año': None,
                'track_number': None,
                'disc_number': None,
                'caratula': None
            }
            
            if ext == '.mp3':
                metadata.update(self._leer_mp3(ruta_archivo))
            elif ext == '.opus':
                metadata.update(self._leer_opus(ruta_archivo))
            elif ext == '.flac':
                metadata.update(self._leer_flac(ruta_archivo))
            
            return metadata
        except Exception as e:
            print(f"Error leyendo metadata: {e}")
            return None
    
    def _leer_mp3(self, ruta: str) -> dict:
        """Lee metadatos de archivo MP3."""
        data = {}
        try:
            audio = EasyID3(ruta)
            data['titulo'] = audio.get('title', [None])[0]
            data['artista'] = audio.get('artist', [None])[0]
            data['album'] = audio.get('album', [None])[0]
            data['genero'] = audio.get('genre', [None])[0]
            data['año'] = audio.get('date', [None])[0]
            data['track_number'] = audio.get('tracknumber', [None])[0]
            data['disc_number'] = audio.get('discnumber', [None])[0]
            
            # Carátula
            try:
                audio_full = ID3(ruta)
                for tag in audio_full.values():
                    if isinstance(tag, APIC):
                        from PIL import Image
                        from io import BytesIO
                        data['caratula'] = Image.open(BytesIO(tag.data))
                        break
            except:
                pass
        except:
            pass
        
        return data
    
    def _leer_opus(self, ruta: str) -> dict:
        """Lee metadatos de archivo OPUS."""
        data = {}
        try:
            audio = OggOpus(ruta)
            data['titulo'] = audio.get('TITLE', [None])[0]
            data['artista'] = audio.get('ARTIST', [None])[0]
            data['album'] = audio.get('ALBUM', [None])[0]
            data['genero'] = audio.get('GENRE', [None])[0]
            data['año'] = audio.get('DATE', [None])[0] or audio.get('YEAR', [None])[0]
            data['track_number'] = audio.get('TRACKNUMBER', [None])[0]
            data['disc_number'] = audio.get('DISCNUMBER', [None])[0]
            
            # Carátula
            try:
                if "metadata_block_picture" in audio:
                    from PIL import Image
                    from io import BytesIO
                    pic_data = base64.b64decode(audio["metadata_block_picture"][0])
                    from mutagen.flac import Picture
                    picture = Picture(pic_data)
                    data['caratula'] = Image.open(BytesIO(picture.data))
            except:
                pass
        except:
            pass
        
        return data
    
    def _leer_flac(self, ruta: str) -> dict:
        """Lee metadatos de archivo FLAC."""
        data = {}
        try:
            audio = FLAC(ruta)
            data['titulo'] = audio.get('title', [None])[0]
            data['artista'] = audio.get('artist', [None])[0]
            data['album'] = audio.get('album', [None])[0]
            data['genero'] = audio.get('genre', [None])[0]
            data['año'] = audio.get('date', [None])[0]
            data['track_number'] = audio.get('tracknumber', [None])[0]
            data['disc_number'] = audio.get('discnumber', [None])[0]
            
            # Carátula
            try:
                if audio.pictures:
                    from PIL import Image
                    from io import BytesIO
                    data['caratula'] = Image.open(BytesIO(audio.pictures[0].data))
            except:
                pass
        except:
            pass
        
        return data
    
    def guardar_metadata(self, ruta: str, datos: dict, imagen_data: bytes = None) -> bool:
        """Guarda metadatos en un archivo de audio."""
        try:
            _, ext = os.path.splitext(ruta)
            ext = ext.lower()
            
            if ext == '.mp3':
                self._guardar_mp3(ruta, datos, imagen_data)
            elif ext == '.opus':
                self._guardar_opus(ruta, datos, imagen_data)
            elif ext == '.flac':
                self._guardar_flac(ruta, datos, imagen_data)
            
            return True
        except Exception as e:
            print(f"Error guardando metadata: {e}")
            return False
    
    def _guardar_mp3(self, ruta: str, datos: dict, imagen_data: bytes = None):
        """Guarda tags en archivo MP3."""
        try:
            audio = EasyID3(ruta)
        except ID3NoHeaderError:
            audio = EasyID3()
            audio.filename = ruta
            audio.save()
            audio = EasyID3(ruta)
        
        if datos.get('titulo'): audio['title'] = datos['titulo']
        if datos.get('artista'): audio['artist'] = datos['artista']
        if datos.get('album'): audio['album'] = datos['album']
        if datos.get('genero'): audio['genre'] = datos['genero']
        if datos.get('año'): 
            audio['date'] = datos['año']
            audio['originaldate'] = datos['año']
        if datos.get('track_number'): audio['tracknumber'] = datos['track_number']
        if datos.get('disc_number'): audio['discnumber'] = datos['disc_number']
        
        audio.save()
        
        # Aplicar imagen
        if imagen_data:
            try:
                audio_full = ID3(ruta)
                audio_full.delall("APIC")
                audio_full.add(APIC(
                    encoding=3,
                    mime='image/jpeg',
                    type=3,
                    desc=u'Cover',
                    data=imagen_data
                ))
                audio_full.save(v2_version=3)
                print("✅ Carátula guardada en MP3")
            except Exception as e:
                print(f"Error guardando carátula MP3: {e}")
    
    def _guardar_opus(self, ruta: str, datos: dict, imagen_data: bytes = None):
        """Guarda tags en archivo OPUS."""
        audio = OggOpus(ruta)
        
        if datos.get('titulo'): audio['TITLE'] = datos['titulo']
        if datos.get('artista'): audio['ARTIST'] = datos['artista']
        if datos.get('album'): audio['ALBUM'] = datos['album']
        if datos.get('genero'): audio['GENRE'] = datos['genero']
        if datos.get('año'): 
            audio['DATE'] = datos['año']
            audio['YEAR'] = datos['año']
        if datos.get('track_number'): audio['TRACKNUMBER'] = datos['track_number']
        if datos.get('disc_number'): audio['DISCNUMBER'] = datos['disc_number']
        
        # Aplicar imagen
        if imagen_data:
            try:
                p = Picture()
                p.data = imagen_data
                p.type = 3
                p.mime = "image/jpeg"
                p.desc = "Cover"
                audio["metadata_block_picture"] = [base64.b64encode(p.write()).decode("ascii")]
                print("✅ Carátula lista para guardar en OPUS")
            except Exception as e:
                print(f"Error preparando carátula OPUS: {e}")
        
        audio.save()
    
    def _guardar_flac(self, ruta: str, datos: dict, imagen_data: bytes = None):
        """Guarda tags en archivo FLAC."""
        audio = FLAC(ruta)
        
        if datos.get('titulo'): audio['title'] = datos['titulo']
        if datos.get('artista'): audio['artist'] = datos['artista']
        if datos.get('album'): audio['album'] = datos['album']
        if datos.get('genero'): audio['genre'] = datos['genero']
        if datos.get('año'): audio['date'] = datos['año']
        if datos.get('track_number'): audio['tracknumber'] = datos['track_number']
        if datos.get('disc_number'): audio['discnumber'] = datos['disc_number']
        
        # Aplicar imagen
        if imagen_data:
            try:
                audio.clear_pictures()
                picture = Picture()
                picture.data = imagen_data
                picture.type = 3
                picture.mime = "image/jpeg"
                picture.desc = "Cover"
                audio.add_picture(picture)
                print("✅ Carátula guardada en FLAC")
            except Exception as e:
                print(f"Error guardando carátula FLAC: {e}")
        
        audio.save()
    
    def buscar_metadatos(self, titulo: str, artista: str, ruta_archivo: str = None) -> list:
        """Busca metadatos en línea."""
        return self.search_service.buscar_metadatos(titulo, artista, ruta_archivo)
    
    def descargar_caratula(self, url: str) -> bytes:
        """Descarga una carátula desde una URL."""
        return self.search_service.descargar_imagen(url)
    
    def cargar_archivos_carpeta(self, carpeta: str) -> list:
        archivos = []
        extensiones = ('.mp3', '.opus', '.flac')
        
        try:
            for archivo in os.listdir(carpeta):
                if archivo.lower().endswith(extensiones):
                    ruta_completa = os.path.join(carpeta, archivo)
                    metadata = self.leer_metadata(ruta_completa)
                    if metadata:
                        archivos.append(metadata)
            
            # Ordenar por número de pista
            archivos.sort(key=lambda x: int(x.get('track_number', 999) or 999))
        except Exception as e:
            print(f"Error cargando archivos: {e}")
        
        return archivos
