<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <div class="min-h-screen bg-gray-900 text-white flex items-center justify-center">
    <div class="text-center space-y-6 px-4">
      <h1 class="text-5xl font-bold tracking-tight text-white">Music Downloader</h1>
      <p class="text-lg text-gray-400 max-w-md mx-auto">
        Download audio and video from the web. Clean, fast, and configurable.
      </p>

      <div class="flex flex-col sm:flex-row gap-4 justify-center mt-8">
        <RouterLink
          to="/download"
          class="inline-flex items-center justify-center px-6 py-3 rounded-xl bg-indigo-600 hover:bg-indigo-500 text-white font-semibold transition-colors duration-200"
        >
          Single Download
        </RouterLink>

        <RouterLink
          to="/playlist"
          class="inline-flex items-center justify-center px-6 py-3 rounded-xl bg-gray-700 hover:bg-gray-600 text-white font-semibold transition-colors duration-200"
        >
          Playlist Download
        </RouterLink>
      </div>

      <div class="pt-4">
        <RouterLink
          to="/tags"
          class="text-sm text-gray-500 hover:text-gray-300 underline transition-colors duration-200"
        >
          Edit Tags
        </RouterLink>
      </div>
    </div>
  </div>
</template>
