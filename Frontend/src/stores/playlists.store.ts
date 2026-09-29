import { defineStore } from 'pinia'
import { ref } from 'vue'
import { playlistsApi } from '@/api/playlists.api'
import type { BatchDownloadRequest } from '@/types/playlist.types'

export const usePlaylistsStore = defineStore('playlists', () => {
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function downloadBatch(payload: BatchDownloadRequest): Promise<void> {
    loading.value = true
    error.value = null
    try {
      await playlistsApi.downloadBatch(payload)
    } catch (err) {
      error.value = (err as { message: string }).message
    } finally {
      loading.value = false
    }
  }

  return { loading, error, downloadBatch }
})
