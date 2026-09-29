import { computed } from 'vue'
import { useMetadataStore } from '@/stores/metadata.store'

export function useMediaInfo() {
  const store = useMetadataStore()

  return {
    info: computed(() => store.info),
    qualities: computed(() => store.qualities),
    loading: computed(() => store.loading),
    error: computed(() => store.error),
    analyzeUrl: (url: string) => store.fetchInfo(url),
    fetchQualities: (url: string, codec: string) => store.fetchQualities(url, codec),
    clearInfo: () => store.clear(),
  }
}
