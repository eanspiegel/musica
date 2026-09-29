import { defineStore } from 'pinia'
import { ref } from 'vue'
import { metadataApi } from '@/api/metadata.api'
import type { MediaInfo, QualityOption } from '@/types/metadata.types'

export const useMetadataStore = defineStore('metadata', () => {
  const info = ref<MediaInfo | null>(null)
  const qualities = ref<Record<string, QualityOption>>({})
  const loading = ref(false)
  const error = ref<string | null>(null)

  async function fetchInfo(url: string): Promise<void> {
    loading.value = true
    error.value = null
    qualities.value = {}
    try {
      info.value = await metadataApi.getInfo(url)
    } catch (err) {
      error.value = (err as { message: string }).message
    } finally {
      loading.value = false
    }
  }

  async function fetchQualities(url: string, codec: string): Promise<void> {
    loading.value = true
    error.value = null
    try {
      qualities.value = await metadataApi.getQualities(url, codec)
    } catch (err) {
      error.value = (err as { message: string }).message
    } finally {
      loading.value = false
    }
  }

  function clear(): void {
    info.value = null
    qualities.value = {}
    error.value = null
  }

  return { info, qualities, loading, error, fetchInfo, fetchQualities, clear }
})
