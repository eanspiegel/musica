<script setup lang="ts">
interface Props {
  title: string
  uploader: string
  duration: string
  thumbnail?: string
}

withDefaults(defineProps<Props>(), {
  thumbnail: '',
})
</script>

<template>
  <div class="flex items-center gap-3 p-3 bg-gray-800 rounded-lg">
    <div class="flex-shrink-0 w-16 h-12 bg-gray-700 rounded overflow-hidden">
      <img
        v-if="thumbnail"
        :src="thumbnail"
        :alt="title"
        class="w-full h-full object-cover"
      />
      <div
        v-else
        class="w-full h-full flex items-center justify-center text-gray-500 text-xs"
      >
        No img
      </div>
    </div>

    <div class="min-w-0 flex-1">
      <p class="text-sm font-medium text-white truncate">{{ title }}</p>
      <p class="text-xs text-gray-400 truncate">{{ uploader }}</p>
    </div>

    <span class="flex-shrink-0 text-xs text-gray-500">{{ duration }}</span>
  </div>
</template>
