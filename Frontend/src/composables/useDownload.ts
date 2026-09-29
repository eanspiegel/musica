import { computed } from 'vue'
import { useDownloadsStore } from '@/stores/downloads.store'
import type { DownloadRequest } from '@/types/download.types'

export function useDownload() {
  const store = useDownloadsStore()

  return {
    jobs: computed(() => store.jobs),
    activeJobs: computed(() => store.activeJobs),
    completedJobs: computed(() => store.completedJobs),
    loading: computed(() => store.loading),
    error: computed(() => store.error),
    startDownload: (payload: DownloadRequest) => store.createDownload(payload),
    cancelDownload: (id: string) => store.cancelDownload(id),
  }
}
