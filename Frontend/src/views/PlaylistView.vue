<script setup lang="ts">
import { ref } from 'vue'
import { useMetadataStore } from '@/stores/metadata.store'
import { usePlaylistsStore } from '@/stores/playlists.store'
import { useMediaInfo } from '@/composables/useMediaInfo'
import SearchBar from '@/components/molecules/SearchBar.vue'
import PlaylistSelector from '@/components/organisms/PlaylistSelector.vue'

const { info, loading: infoLoading, analyzeUrl } = useMediaInfo()
const playlistsStore = usePlaylistsStore()

const selectedIndices = ref<number[]>([])
const selectedFormat = ref<'video' | 'music'>('music')
const selectedAudioFormat = ref('mp3')
const currentUrl = ref('')

async function handleSearch(url: string): Promise<void> {
  currentUrl.value = url
  await analyzeUrl(url)
  selectedIndices.value = []
}

function handleSelectionChange(indices: number[]): void {
  selectedIndices.value = indices
}

async function handleBatchDownload(): Promise<void> {
  if (!currentUrl.value || selectedIndices.value.length === 0) return

  await playlistsStore.downloadBatch({
    url: currentUrl.value,
    indices: selectedIndices.value,
    format_type: selectedFormat.value,
    audio_format: selectedAudioFormat.value,
  })
}
</script>

<template>
  <div class="min-h-screen bg-gray-900 text-white p-6">
    <div class="max-w-4xl mx-auto space-y-6">
      <RouterLink to="/" class="text-gray-400 hover:text-white text-sm">← Back</RouterLink>
      <h1 class="text-3xl font-bold">Playlist Download</h1>

      <SearchBar :loading="infoLoading" @search="handleSearch" />

      <template v-if="info && info.type === 'playlist'">
        <PlaylistSelector :items="info.playlist_items" @selection-change="handleSelectionChange" />

        <div class="flex items-center gap-4 pt-2">
          <select
            v-model="selectedFormat"
            class="bg-gray-700 text-white rounded px-3 py-2 text-sm"
          >
            <option value="music">Music</option>
            <option value="video">Video</option>
          </select>

          <select
            v-if="selectedFormat === 'music'"
            v-model="selectedAudioFormat"
            class="bg-gray-700 text-white rounded px-3 py-2 text-sm"
          >
            <option value="mp3">MP3</option>
            <option value="flac">FLAC</option>
            <option value="m4a">M4A</option>
          </select>

          <button
            :disabled="selectedIndices.length === 0 || playlistsStore.loading"
            class="px-6 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed font-semibold transition-colors"
            @click="handleBatchDownload"
          >
            <span v-if="playlistsStore.loading">Queuing…</span>
            <span v-else>Download {{ selectedIndices.length }} track(s)</span>
          </button>
        </div>
      </template>

      <p v-else-if="info && info.type === 'video'" class="text-yellow-400">
        This URL points to a single video, not a playlist. Use the
        <RouterLink to="/download" class="underline">Single Download</RouterLink> page.
      </p>
    </div>
  </div>
</template>
