# Migración a Arquitectura Web (Vue + FastAPI)

Este documento detalla el estado general de la migración del proyecto desde una aplicación monolítica de escritorio (Tkinter) a una arquitectura moderna dividida en Backend y Frontend.

## Estado de la Migración

### ✅ Completado

#### 1. Backend (FastAPI)
- [x] **Estructura base:** Capas limpias (Routers, Services, Adapters, Ports).
- [x] **Inyección de dependencias:** Configurada a través de un contenedor lazy-load.
- [x] **Servicios Independientes:** 
  - `DownloadService` (Manejo de descargas)
  - `MetadataService` (Búsqueda y aplicación de tags)
  - `PlaylistService` (Descargas en lote)
- [x] **Manejo de yt-dlp:** Extraído a adaptador asíncrono seguro (`_download_sync` via `asyncio.to_thread`) para no bloquear el Event Loop.
- [x] **Resolución de rutas locales:** Soporte para directorios dinámicos personalizados a pedido del frontend.
- [x] **Post-Procesamiento (Etiquetado):** 
  - Reconocimiento de audio con `shazamio`
  - Búsqueda de metadata en iTunes/Deezer
  - Fetch de letras con LRCLIB
  - Taggeo de MP3 (ID3) y OPUS (OggOpus Base64 Picture) con `mutagen`.
  - Etiquetado automático interconectado al finalizar descargas individuales de música.

#### 2. Frontend (Vue 3 + TypeScript)
- [x] **Estructura base:** Vite, Vue 3, TailwindCSS, Pinia.
- [x] **Integración HTTP limpia:** Adaptador centralizado con Axios, inyección automática de API Key.
- [x] **Componentes UI Básicos:** 
  - Panel de resultados de búsqueda (`DownloadPanel`).
  - Lista de trabajos en progreso y completados (`JobList`).
- [x] **Gestión de Estado (Stores):** 
  - `downloads.store.ts` con polling automático de las descargas en curso.
  - `metadata.store.ts` para obtener resoluciones y calidades.
- [x] **Flujos de Descarga Individual:** Soporte para bajar en distintos codecs de video y audio (MP3, OPUS, etc). Selector de directorio de destino incorporado.

#### 3. Deuda Técnica
- [x] Análisis inicial completo: Creado inventario exhaustivo en `/docs/Migración/Technical Debt/README.md` (SSRF, Async blockers, etc.).
- [x] Eliminación de Async/Sync blockers en FastAPI: Arreglado el event loop congelado por culpa de yt-dlp.

---

### ⏳ Pendiente / En Progreso

#### 1. Descargas Masivas (Playlists)
- [ ] Conectar el `PlaylistSelector.vue` con el endpoint de descargas en lote en el backend.
- [ ] Probar y ajustar la concurrencia de bajada (`max_concurrent_downloads`).

#### 2. Funcionalidades Extra (Frontend)
- [ ] **Editor de Etiquetas (Tags Editor):** Construir la UI interactiva (`TagsEditorView.vue`) para que el usuario pueda modificar manualmente los tags y la carátula antes o después de descargada la canción.

#### 3. Criterios de Seguridad y Estabilidad (Backend)
- [ ] Aplicar rate limit (SlowAPI) para endpoints pesados.
- [ ] Pruebas exhaustivas (Unit/Integration Tests) para los adaptadores.
- [ ] Implementar validación de limpieza (sanitize) de nombres de archivo mucho más estricta por seguridad.

## Cómo Ejecutar los Proyectos

Consulta la documentación detallada de cada capa:
- [Backend README](./BackEnd/README.md)
- [Frontend README](./FrontEnd/README.md)
- [Technical Debt](./Technical%20Debt/README.md)
