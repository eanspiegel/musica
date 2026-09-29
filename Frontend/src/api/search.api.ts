import { http } from '@/adapters/http'
import type { MetadataCandidate } from '@/types/track.types'

export const searchApi = {
  searchMetadata(title: string, artist: string): Promise<MetadataCandidate[]> {
    return http.get<MetadataCandidate[]>('/api/v1/search/metadata', { title, artist })
  },
}
