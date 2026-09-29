export interface BatchDownloadRequest {
  url: string
  indices: number[]
  format_type: 'video' | 'music'
  audio_format?: string
  container?: string
}
