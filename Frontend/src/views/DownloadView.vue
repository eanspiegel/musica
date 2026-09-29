<script setup lang="ts">
import { ref } from 'vue'
import { useMetadataStore } from '@/stores/metadata.store'
import { useDownloadsStore } from '@/stores/downloads.store'
import { useMediaInfo } from '@/composables/useMediaInfo'
import { useDownload } from '@/composables/useDownload'
import SearchBar from '@/components/molecules/SearchBar.vue'
import DownloadPanel from '@/components/organisms/DownloadPanel.vue'
import JobList from '@/components/organisms/JobList.vue'
import type { DownloadRequest } from '@/types/download.types'

const { info, qualities, loading: infoLoading, analyzeUrl } = useMediaInfo()
const { activeJobs, completedJobs, cancelDownload, startDownload } = useDownload()

async function handleSearch(url: string): Promise<void> {
  await analyzeUrl(url)
}

async function handleDownload(payload: DownloadRequest): Promise<void> {
  await startDownload(payload)
}
</script>

<template>
  <div class="min-h-screen bg-gray-900 text-white p-6">
    <div class="max-w-3xl mx-auto space-y-6">
      <RouterLink to="/" class="text-gray-400 hover:text-white text-sm">← Back</RouterLink>
      <h1 class="text-3xl font-bold">Single Download</h1>

      <SearchBar :loading="infoLoading" @search="handleSearch" />

      <DownloadPanel
        v-if="info"
        :info="info"
        :qualities="qualities"
        @download="handleDownload"
      />

      <div v-if="activeJobs.length > 0">
        <h2 class="text-xl font-semibold mb-3">Active Jobs</h2>
        <JobList :jobs="activeJobs" @cancel="cancelDownload" />
      </div>

      <div v-if="completedJobs.length > 0">
        <h2 class="text-xl font-semibold mb-3">Completed</h2>
        <JobList :jobs="completedJobs" @cancel="() => {}" />
      </div>
    </div>
  </div>
</template>
