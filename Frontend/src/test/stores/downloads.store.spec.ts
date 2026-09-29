import { describe, it, expect, vi, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useDownloadsStore } from '@/stores/downloads.store'
import type { DownloadJob } from '@/types/download.types'

vi.mock('@/api/downloads.api', () => ({
  downloadsApi: {
    getAll: vi.fn(),
    create: vi.fn(),
    getById: vi.fn(),
    cancel: vi.fn(),
  },
}))

import { downloadsApi } from '@/api/downloads.api'

const mockJob: DownloadJob = {
  id: 'job-1',
  url: 'https://example.com/video',
  format_type: 'music',
  status: 'pending',
  progress: 0,
  created_at: '2024-01-01T00:00:00Z',
}

describe('useDownloadsStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('fetchAll populates jobs', async () => {
    vi.mocked(downloadsApi.getAll).mockResolvedValue([mockJob])

    const store = useDownloadsStore()
    await store.fetchAll()

    expect(store.jobs).toHaveLength(1)
    expect(store.jobs[0].id).toBe('job-1')
    expect(store.loading).toBe(false)
  })

  it('createDownload adds job to store', async () => {
    vi.mocked(downloadsApi.create).mockResolvedValue(mockJob)
    vi.mocked(downloadsApi.getById).mockResolvedValue({ ...mockJob, status: 'done' })

    const store = useDownloadsStore()
    await store.createDownload({ url: 'https://example.com/video', format_type: 'music' })

    expect(store.jobs).toHaveLength(1)
    expect(store.jobs[0].id).toBe('job-1')
  })
})
