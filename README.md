# Descargador de Playlist de YouTube

- Python 3.x
- yt-dlp
- FFmpeg (necesario para convertir a MP3)

python -m pip install yt-dlp


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

### Ejemplo

```bash
python musica.py 
```

## Características

ya las pongo que primero voy a crear el repo

## Notas

- Las canciones se guardan con el título del video como nombre de archivo
- Si la carpeta `playlist/` no existe, se crea automáticamente

