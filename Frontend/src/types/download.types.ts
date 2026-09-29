export interface DownloadRequest {
  url: string
  format_type: 'video' | 'music'
  audio_format?: string
  codec?: string
  format_id?: string
  directory?: string
}

export interface DownloadJob {
  id: string
  url: string
  format_type: string
  status: 'pending' | 'running' | 'done' | 'failed'
  progress: number
  file_path?: string
  error?: string
  created_at: string
}
