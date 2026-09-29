import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { downloadsApi } from '@/api/downloads.api'
import type { DownloadJob, DownloadRequest } from '@/types/download.types'

export const useDownloadsStore = defineStore('downloads', () => {
  const jobs = ref<DownloadJob[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  const activeJobs = computed(() =>
    jobs.value.filter((j) => j.status === 'pending' || j.status === 'running'),
  )

  const completedJobs = computed(() =>
    jobs.value.filter((j) => j.status === 'done' || j.status === 'failed'),
  )

  async function fetchAll(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      jobs.value = await downloadsApi.getAll()
    } catch (err) {
      error.value = (err as { message: string }).message
    } finally {
      loading.value = false
    }
  }

  async function createDownload(payload: DownloadRequest): Promise<void> {
    try {
      const job = await downloadsApi.create(payload)
      jobs.value.push(job)
      pollJob(job.id)
    } catch (err) {
      error.value = (err as { message: string }).message
    }
  }

  async function cancelDownload(id: string): Promise<void> {
    try {
      await downloadsApi.cancel(id)
      const job = jobs.value.find((j) => j.id === id)
      if (job) {
        job.status = 'failed'
      }
    } catch (err) {
      error.value = (err as { message: string }).message
    }
  }

  function pollJob(id: string): void {
    const interval = setInterval(async () => {
      try {
        const updated = await downloadsApi.getById(id)
        const index = jobs.value.findIndex((j) => j.id === id)
        if (index !== -1) {
          jobs.value[index] = updated
        }
        if (updated.status === 'done' || updated.status === 'failed') {
          clearInterval(interval)
        }
      } catch {
        clearInterval(interval)
      }
    }, 1500)
  }

  return {
    jobs,
    loading,
    error,
    activeJobs,
    completedJobs,
    fetchAll,
    createDownload,
    cancelDownload,
    pollJob,
  }
})
