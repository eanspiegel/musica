export interface PlaylistItem {
  title: string
  url: string
  uploader: string
  duration: string
  thumbnail: string
}

export interface MediaInfo {
  type: 'video' | 'playlist'
  url: string
  title: string
  duration: string
  uploader: string
  thumbnail: string
  playlist_items: PlaylistItem[]
}

export interface QualityOption {
  nombre: string
  resolucion: string
  tamanio: number
  formato_id: string
  ext: string
  fps: number
}
