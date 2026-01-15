# Descargador de Playlist de YouTube

Hice esto porque ya me dió pereza pedirle el ytdownloader a mi pana y es tarde y no quiero esperar hasta el otro día

- Python 3.x
- yt-dlp
- python-dotenv
- FFmpeg (necesario para convertir a MP3)

python -m pip install -r requirements.txt


### Instalar FFmpeg (esto es para pasarlo a mp3)

Descarga FFmpeg desde: https://ffmpeg.org/download.html 
Te dará dos opciones pero ve al git chaval porque el de la web tambien te mandará a git xd
Extrae el archivo y cambiale el nombre a ffmepeg
Ahora ese directorio ffmpeg muevelo al disco(o agrega al path directo, ahí ves que chanchuyo haces, te digo lo que es más recomendable bobote :p)
Agrega la carpeta `bin`(del directorio ffmpeg) a tu PATH


## Uso

```bash
python musica.py 
```

### Ejecución

Te pedirá que pongas el enlace de la lista de reprodución de YT, ahí tu ves si quieres descargar el video o solo el audio y ya eso es todo, el menú es con números y todo es intuitivo, creo


## Notas

- Las canciones se guardan con el título del video como nombre de archivo
- Crea un archivo `.env` o borra el `.example` del archivo `.env.example` y ahí pones la ruta donde quieras que se guarden las canciones
-Algo que me pasó probando es que debes tener cuidado cuando copias el enlaces, aveces copias sin querer una playlist, igual el codigo te muestra cuantas canciones de van a descargar, pero pilas con eso
-Creo que hay un problema con la calidad de video o estas son las pruebas que hice: 
    144p: se descarga el video a esa calidad pero el audio no lo incorpora(Igual no creo que vayas a descargar el video en esa calidad)
    720 y 1080: tengo mis dudas porque siento que 1080 es 720 y 720 parece 480, igual es porque soy tremendo ciego