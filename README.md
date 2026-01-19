# Descargador de Playlist de YouTube

Hice esto porque ya me dió pereza pedirle el ytdownloader a mi pana, es tarde y no quiero esperar hasta el otro día

- Python 3.x
- yt-dlp: para descargar videos de YouTube
- mutagen: para etiquetar archivos
- requests: para descargar portadas
- Pillow: para editar portadas
- FFmpeg (necesario para convertir a MP3)

```bash
python -m pip install -r requirements.txt
```
## Notas v1.4.1

- Correción de etiquetados en EP, canciones con el mismo nombre y diferente artista
- Correción de la barra de progreso

## Notas v1.4.0

- Añadido etiquetado de archivos

### Instalar FFmpeg (esto es para pasarlo a mp3)

Descarga FFmpeg desde: https://ffmpeg.org/download.html 
Te dará dos opciones pero ve al git chaval porque el de la web tambien te mandará a git xd
Extrae el archivo y cambiale el nombre a ffmepeg
Ahora ese directorio ffmpeg muevelo al disco(o agrega al path directo, ahí ves que chanchuyo haces, te digo lo que es más recomendable bobote :p)
Agrega la carpeta `bin`(del directorio ffmpeg) a tu PATH


## Uso

```bash
python musica.py
o  
ejecutar MusicaDownloader_v2.1.0.exe
```

### Ejecución

Te pedirá que pongas el enlace de la lista de reprodución de YT, ahí tu ves si quieres descargar el video o solo el audio y ya eso es todo, el menú es con números y todo es intuitivo, "creo".

## Notas

- Algo que me pasó probando es que debes tener cuidado cuando copias el enlaces, aveces copias sin querer una playlist, igual el codigo te muestra cuantas canciones de van a descargar, pero pilas con eso

## Notas v1.3.1

- Correción de calidades

## Notas v1.3.0

- Interfaz gráfica
