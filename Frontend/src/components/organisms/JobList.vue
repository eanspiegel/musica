<script setup lang="ts">
import BaseBadge from '@/components/atoms/BaseBadge.vue'
import BaseButton from '@/components/atoms/BaseButton.vue'
import ProgressBar from '@/components/molecules/ProgressBar.vue'
import type { DownloadJob } from '@/types/download.types'

interface Props {
  jobs: DownloadJob[]
}

defineProps<Props>()
const emit = defineEmits<{ cancel: [id: string] }>()

type BadgeColor = 'green' | 'red' | 'yellow' | 'blue' | 'gray'

function badgeColor(status: DownloadJob['status']): BadgeColor {
  const map: Record<DownloadJob['status'], BadgeColor> = {
    pending: 'yellow',
    running: 'blue',
    done: 'green',
    failed: 'red',
  }
  return map[status]
}

function truncateUrl(url: string, max = 60): string {
  return url.length > max ? `${url.slice(0, max)}…` : url
}
</script>

<template>
  <ul class="space-y-3">
    <li
      v-for="job in jobs"
      :key="job.id"
      class="bg-gray-800 rounded-xl p-4 space-y-3"
    >
      <div class="flex items-start justify-between gap-3">
        <div class="min-w-0 flex-1">
          <p class="text-sm text-gray-300 truncate" :title="job.url">
            {{ truncateUrl(job.url) }}
          </p>
        </div>
        <div class="flex items-center gap-2 flex-shrink-0">
          <BaseBadge :label="job.status" :color="badgeColor(job.status)" />
          <BaseButton
            v-if="job.status === 'pending' || job.status === 'running'"
            label="Cancel"
            variant="danger"
            @click="emit('cancel', job.id)"
          />
        </div>
      </div>

      <ProgressBar
        v-if="job.status === 'running'"
        :progress="job.progress"
        :status="`${job.progress}%`"
      />

      <p v-if="job.status === 'done' && job.file_path" class="text-xs text-green-400">
        Saved to: {{ job.file_path }}
      </p>

      <p v-if="job.error" class="text-xs text-red-400">{{ job.error }}</p>
    </li>
  </ul>
</template>
