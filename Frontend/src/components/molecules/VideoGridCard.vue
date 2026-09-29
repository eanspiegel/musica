<script setup lang="ts">
import { computed } from 'vue'
import type { PlaylistItem } from '@/types/metadata.types'

interface Props {
  item: PlaylistItem
  selected?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  selected: false
})

const emit = defineEmits<{ click: [] }>()

const formattedDuration = computed(() => {
  // If it's already HH:MM:SS or MM:SS, just return it. 
  // We can just rely on yt-dlp's provided duration string.
  return props.item.duration || ''
})
</script>

<template>
  <div 
    class="relative group cursor-pointer flex flex-col gap-3 rounded-xl transition-all duration-300"
    @click="emit('click')"
  >
    <!-- Thumbnail container -->
    <div class="relative w-full aspect-video rounded-xl overflow-hidden bg-gray-800">
      <img 
        v-if="item.thumbnail" 
        :src="item.thumbnail" 
        :alt="item.title"
        class="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
      />
      
      <!-- Selection Overlay -->
      <div 
        class="absolute inset-0 border-4 transition-colors duration-200"
        :class="selected ? 'border-[var(--color-brand)]' : 'border-transparent group-hover:border-[var(--color-border)]'"
      ></div>
      
      <!-- Selected check badge -->
      <div 
        v-if="selected"
        class="absolute top-2 right-2 bg-[var(--color-brand)] text-black w-6 h-6 rounded-full flex items-center justify-center shadow-md"
      >
        <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
          <path fill-rule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clip-rule="evenodd" />
        </svg>
      </div>

      <!-- Duration Pill -->
      <div 
        v-if="formattedDuration"
        class="absolute bottom-1.5 right-1.5 bg-black/80 px-1.5 py-0.5 rounded text-[11px] font-medium text-white tracking-wider"
      >
        {{ formattedDuration }}
      </div>
    </div>

    <!-- Metadata -->
    <div class="flex gap-3 px-1">
      <!-- Uploader avatar placeholder -->
      <div class="flex-shrink-0 w-9 h-9 rounded-full bg-gray-700 flex items-center justify-center text-[var(--color-text-muted)] text-sm font-bold uppercase overflow-hidden">
        {{ item.uploader ? item.uploader.charAt(0) : '?' }}
      </div>
      
      <!-- Title & Channel -->
      <div class="flex flex-col min-w-0">
        <h3 
          class="text-body font-semibold text-primary line-clamp-2 leading-tight mb-1"
          :class="selected ? 'text-[var(--color-brand)]' : ''"
        >
          {{ item.title }}
        </h3>
        <p class="text-caption text-secondary truncate hover:text-primary transition-colors">
          {{ item.uploader }}
        </p>
      </div>
    </div>
  </div>
</template>
