<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useCartStore } from '@/stores/cart.store'
import { usePlaylistsStore } from '@/stores/playlists.store'

const router = useRouter()
const cartStore = useCartStore()
const playlistsStore = usePlaylistsStore()

const selectedFormat = ref<'video' | 'music'>('music')
const selectedAudioFormat = ref('mp3')
const selectedVideoFormat = ref('mp4')

async function handleDownloadAll() {
  if (cartStore.items.length === 0) return

  // Using downloadBatch. Since we pass an array of items, we can either
  // call downloadBatch multiple times, or adjust the backend.
  // Wait, our backend downloadBatch expects a SINGLE url and an array of indices.
  // But here we have multiple DIFFERENT URLs.
  // We need to call playlistsStore.downloadBatch for EACH url, OR we can
  // create a new method for batching multiple separate URLs.
  // For simplicity and since yt-dlp can handle it, let's just loop over them and
  // fire off individual downloads.

  for (const item of cartStore.items) {
    await playlistsStore.downloadBatch({
      url: item.url,
      indices: [1], // Because it's a direct url to the video
      format_type: selectedFormat.value,
      audio_format: selectedAudioFormat.value,
      codec: selectedVideoFormat.value,
    })
  }

  // Clear cart after queuing
  cartStore.clearCart()
  
  router.push('/downloads')
}
</script>

<template>
  <div class="p-6 max-w-4xl mx-auto space-y-8">
    <div class="flex items-center justify-between">
      <div>
        <h1 class="text-h1 text-primary">Cola de Descargas</h1>
        <p class="text-body text-secondary mt-2">Revisa los videos que agregaste antes de descargar.</p>
      </div>
      <button 
        v-if="cartStore.items.length > 0"
        @click="cartStore.clearCart()"
        class="text-sm text-red-500 hover:text-red-400 font-medium"
      >
        Vaciar cola
      </button>
    </div>

    <div v-if="cartStore.items.length === 0" class="text-center py-20 bg-[#121212] rounded-xl border border-[#303030]">
      <svg class="w-16 h-16 text-gray-600 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"></path></svg>
      <h2 class="text-h3 text-primary mb-2">Tu cola está vacía</h2>
      <p class="text-body text-secondary mb-6">Busca videos y haz clic en ellos para agregarlos aquí.</p>
      <RouterLink to="/" class="btn btn-primary">Buscar videos</RouterLink>
    </div>

    <template v-else>
      <!-- List of Items -->
      <ul class="space-y-4">
        <li 
          v-for="(item, index) in cartStore.items" 
          :key="item.url"
          class="flex items-center gap-4 bg-[#121212] p-4 rounded-xl border border-[#303030]"
        >
          <img :src="item.thumbnail" class="w-32 aspect-video object-cover rounded-lg" />
          <div class="flex-1 min-w-0">
            <h3 class="text-body font-semibold text-primary truncate">{{ item.title }}</h3>
            <p class="text-caption text-secondary">{{ item.uploader }} • {{ item.duration }}</p>
          </div>
          <button 
            @click="cartStore.removeItem(index)"
            class="p-2 text-gray-500 hover:text-red-500 hover:bg-[#272727] rounded-full transition-colors"
            title="Quitar"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"></path></svg>
          </button>
        </li>
      </ul>

      <!-- Download Options Panel -->
      <div class="bg-[#121212] border border-[#303030] p-6 rounded-xl flex flex-col md:flex-row items-center justify-between gap-6">
        <div class="flex items-center gap-4 w-full md:w-auto">
          <div class="space-y-1">
            <label class="text-caption text-secondary">Tipo</label>
            <select v-model="selectedFormat" class="input-base w-full md:w-32">
              <option value="music">Música</option>
              <option value="video">Video</option>
            </select>
          </div>
          
          <div class="space-y-1" v-if="selectedFormat === 'music'">
            <label class="text-caption text-secondary">Formato Audio</label>
            <select v-model="selectedAudioFormat" class="input-base w-full md:w-32">
              <option value="mp3">MP3</option>
              <option value="flac">FLAC</option>
              <option value="m4a">M4A</option>
              <option value="wav">WAV</option>
              <option value="opus">Opus</option>
            </select>
          </div>

          <div class="space-y-1" v-if="selectedFormat === 'video'">
            <label class="text-caption text-secondary">Formato Video</label>
            <select v-model="selectedVideoFormat" class="input-base w-full md:w-32">
              <option value="mp4">MP4</option>
              <option value="webm">WebM</option>
              <option value="mkv">MKV</option>
            </select>
          </div>
        </div>

        <button 
          class="btn btn-primary w-full md:w-auto py-3 px-8 text-lg"
          @click="handleDownloadAll"
          :disabled="playlistsStore.loading"
        >
          <span v-if="playlistsStore.loading">Procesando...</span>
          <span v-else>Descargar {{ cartStore.items.length }} archivo(s)</span>
        </button>
      </div>
    </template>
  </div>
</template>
