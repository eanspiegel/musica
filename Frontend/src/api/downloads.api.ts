import { http } from '@/adapters/http'
import type { DownloadJob, DownloadRequest } from '@/types/download.types'

export const downloadsApi = {
  create(payload: DownloadRequest): Promise<DownloadJob> {
    return http.post<DownloadJob>('/api/v1/downloads', payload)
  },

  getAll(): Promise<DownloadJob[]> {
    return http.get<DownloadJob[]>('/api/v1/downloads')
  },

  getById(id: string): Promise<DownloadJob> {
    return http.get<DownloadJob>(`/api/v1/downloads/${id}`)
  },

  cancel(id: string): Promise<void> {
    return http.del<void>(`/api/v1/downloads/${id}`)
  },
}
