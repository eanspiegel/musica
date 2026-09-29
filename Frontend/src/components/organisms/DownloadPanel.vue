<script setup lang="ts">
import { ref, computed } from 'vue'
import BaseButton from '@/components/atoms/BaseButton.vue'
import type { MediaInfo, QualityOption } from '@/types/metadata.types'
import type { DownloadRequest } from '@/types/download.types'

interface Props {
  info: MediaInfo | null
  qualities: Record<string, QualityOption>
}

const props = defineProps<Props>()
const emit = defineEmits<{ download: [payload: DownloadRequest] }>()

const selectedFormatType = ref<'video' | 'music'>('music')
const selectedQualityKey = ref('')
const selectedAudioFormat = ref('mp3')
const selectedDirectory = ref('')

const qualityOptions = computed(() => Object.entries(props.qualities))

function handleDownload(): void {
  if (!props.info) return

  const payload: DownloadRequest = {
    url: props.info.url,
    format_type: selectedFormatType.value,
  }

  if (selectedFormatType.value === 'video' && selectedQualityKey.value) {
    payload.format_id = props.qualities[selectedQualityKey.value]?.formato_id
  } else {
    payload.audio_format = selectedAudioFormat.value
  }

  if (selectedDirectory.value.trim()) {
    payload.directory = selectedDirectory.value.trim()
  }

  emit('download', payload)
}
</script>

<template>
  <div v-if="info" class="bg-gray-800 rounded-xl p-5 space-y-5">
    <!-- Media preview -->
    <div class="flex gap-4">
      <img
        v-if="info.thumbnail"
        :src="info.thumbnail"
        :alt="info.title"
        class="w-24 h-16 object-cover rounded-lg flex-shrink-0"
      />
      <div class="min-w-0">
        <p class="font-semibold text-white truncate">{{ info.title }}</p>
        <p class="text-sm text-gray-400">{{ info.uploader }} · {{ info.duration }}</p>
      </div>
    </div>

    <!-- Format type toggle -->
    <div class="flex gap-3">
      <button
        :class="[
          'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
          selectedFormatType === 'music'
            ? 'bg-indigo-600 text-white'
            : 'bg-gray-700 text-gray-300 hover:bg-gray-600',
        ]"
        @click="selectedFormatType = 'music'"
      >
        Music
      </button>
      <button
        :class="[
          'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
          selectedFormatType === 'video'
            ? 'bg-indigo-600 text-white'
            : 'bg-gray-700 text-gray-300 hover:bg-gray-600',
        ]"
        @click="selectedFormatType = 'video'"
      >
        Video
      </button>
    </div>

    <!-- Audio format (when music) -->
    <div v-if="selectedFormatType === 'music'" class="flex items-center gap-3">
      <label class="text-sm text-gray-400">Format</label>
      <select
        v-model="selectedAudioFormat"
        class="bg-gray-700 text-white rounded px-3 py-2 text-sm"
      >
        <option value="mp3">MP3</option>
        <option value="flac">FLAC</option>
        <option value="m4a">M4A</option>
        <option value="ogg">OGG</option>
        <option value="opus">OPUS</option>
      </select>
    </div>

    <!-- Quality select (when video) -->
    <div v-if="selectedFormatType === 'video' && qualityOptions.length > 0" class="flex items-center gap-3">
      <label class="text-sm text-gray-400">Quality</label>
      <select
        v-model="selectedQualityKey"
        class="bg-gray-700 text-white rounded px-3 py-2 text-sm"
      >
        <option value="">Select quality…</option>
        <option v-for="[key, opt] in qualityOptions" :key="key" :value="key">
          {{ opt.resolucion }} — {{ opt.ext }} ({{ (opt.tamanio / 1024 / 1024).toFixed(1) }} MB)
        </option>
      </select>
    </div>

    <!-- Download Directory -->
    <div class="flex flex-col gap-2">
      <label class="text-sm text-gray-400">Save to folder (leave empty for default)</label>
      <input
        v-model="selectedDirectory"
        type="text"
        placeholder="C:\Users\jeanb\Desktop"
        class="bg-gray-700 text-white rounded px-3 py-2 text-sm w-full outline-none focus:ring-1 focus:ring-indigo-500"
      />
    </div>

    <BaseButton label="Download" @click="handleDownload" />
  </div>
</template>
