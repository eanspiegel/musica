import { http } from '@/adapters/http'
import type { MediaInfo, QualityOption } from '@/types/metadata.types'

export const metadataApi = {
  getInfo(url: string): Promise<MediaInfo> {
    return http.get<MediaInfo>('/api/v1/metadata/info', { url })
  },

  getQualities(url: string, codec: string): Promise<Record<string, QualityOption>> {
    return http.get<Record<string, QualityOption>>('/api/v1/metadata/qualities', { url, codec })
  },
}
