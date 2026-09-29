import { http } from '@/adapters/http'
import type { BatchDownloadRequest } from '@/types/playlist.types'

export const playlistsApi = {
  downloadBatch(payload: BatchDownloadRequest): Promise<{ message: string }> {
    return http.post<{ message: string }>('/api/v1/playlists/download', payload)
  },
}
