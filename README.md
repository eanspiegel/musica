# Descargador de Playlist de YouTube

Hice esto porque ya me dió pereza pedirle el ytdownloader a mi pana, es tarde y no quiero esperar hasta el otro día

- Python 3.12.10
- yt-dlp: para descargar videos de YouTube
- mutagen: para etiquetar archivos
- requests: para descargar portadas
- Pillow: para editar portadas
- FFmpeg (necesario para convertir a MP3)

```bash
python -m pip install -r requirements.txt

```

## Notas v2.0.0 (Migración a Web / Frontend + Backend)

- **Nueva Arquitectura:** Se migró el proyecto de un script de consola/Tkinter a una arquitectura moderna Cliente-Servidor.
- **Backend (FastAPI):** Lógica refactorizada con inyección de dependencias, adaptadores (Shazam, yt-dlp, Mutagen) y soporte para tareas asíncronas.
- **Frontend (Vue 3 + Tailwind):** Nueva interfaz con sistema de diseño inspirado en Spotify y Apple Design (animaciones fluidas, variables CSS y diseño atómico).
- **Segunda Fase (UI YouTube Clone & Cart):**
  - Se rediseñó completamente la interfaz principal (`/`) para que funcione como un clon visual de YouTube (buscador global, grid adaptativo de 16:9).
  - Integración nativa con las búsquedas de YouTube usando `ytsearch:` directamente en el backend, saltándose la validación estricta HTTP para este caso de uso.
  - Se implementó un flujo de **"Carrito de Descargas"** (`/queue`). Las selecciones se guardan en el `localStorage` (persistencia) y luego el usuario elige globalmente el formato antes de despachar todo el lote.
  - Monitor de estado en vivo (`/downloads`) para ver el progreso real de las conversiones de múltiples hilos.
- **Correcciones en el Descargador (yt-dlp):**
  - Limpieza automática de URLs de YouTube (se ignoran playlists falsas de "Mix/Radios" tipo `list=RD`).
  - Detección precisa de playlists reales: se reescribe el enlace a `/playlist?list=...` para garantizar que baje la lista completa y no solo un video.
  - Corrección de **Race Conditions (WinError 32)** durante descargas en paralelo. Se eliminó la captura de estado de carpetas y se implementó predicción determinista de nombres (`ydl.prepare_filename`) para evitar que hilos concurrentes bloqueen el postprocesamiento de FFmpeg.
  - Polling seguro en la UI para evitar peticiones infinitas cuando falla una descarga.

## notas 1.6.0
- agregué una vaina para buscar otros metadatos en canciones por separado.(Lo hice porque aveces se pone el single en vez del album)
## Notas v1.5.0

-Refactorización y ahora usa Shazam para obtener los metadatos

## Notas v1.4.1

- Correción de etiquetados en EP, canciones con el mismo nombre y diferente artista
- Correción de la barra de progreso
- Se agregó deezer como fuente de metadatos en el caso de que itunes no encuentre la canción

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
