<script setup lang="ts">
import { onMounted, onUnmounted } from 'vue'
import { useDownloadsStore } from '@/stores/downloads.store'
import JobList from '@/components/organisms/JobList.vue'

const downloadsStore = useDownloadsStore()
let interval: ReturnType<typeof setInterval>

onMounted(async () => {
  await downloadsStore.fetchAll()
  
  // Start generic polling for active jobs
  interval = setInterval(async () => {
    // Only fetch if there are active jobs
    if (downloadsStore.activeJobs.length > 0) {
      await downloadsStore.fetchAll()
    }
  }, 2000)
})

onUnmounted(() => {
  clearInterval(interval)
})
</script>

<template>
  <div class="p-6 max-w-[1200px] mx-auto space-y-8">
    <div>
      <h1 class="text-h1 text-primary">Estado de Descargas</h1>
      <p class="text-body text-secondary mt-2">Monitorea el progreso de tus descargas activas e historial.</p>
    </div>

    <div v-if="downloadsStore.loading && downloadsStore.jobs.length === 0" class="flex justify-center py-20">
      <div class="w-10 h-10 border-4 border-[#303030] border-t-red-600 rounded-full animate-spin"></div>
    </div>

    <div v-else-if="downloadsStore.jobs.length === 0" class="text-center py-20 bg-[#121212] rounded-xl border border-[#303030]">
      <svg class="w-16 h-16 text-gray-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path></svg>
      <h2 class="text-h3 text-primary mb-2">No hay descargas</h2>
      <p class="text-body text-secondary">Aún no has iniciado ninguna descarga.</p>
    </div>

    <div v-else class="space-y-8">
      <div v-if="downloadsStore.activeJobs.length > 0">
        <h2 class="text-h2 text-primary mb-4">Activas</h2>
        <JobList 
          :jobs="downloadsStore.activeJobs" 
          @cancel="downloadsStore.cancelDownload"
        />
      </div>

      <div v-if="downloadsStore.completedJobs.length > 0">
        <h2 class="text-h2 text-primary mb-4">Historial</h2>
        <JobList 
          :jobs="downloadsStore.completedJobs" 
          @cancel="downloadsStore.cancelDownload"
        />
      </div>
    </div>
  </div>
</template>
