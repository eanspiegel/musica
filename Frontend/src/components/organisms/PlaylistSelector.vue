<script setup lang="ts">
import { ref } from 'vue'
import TrackCard from '@/components/molecules/TrackCard.vue'
import BaseButton from '@/components/atoms/BaseButton.vue'
import type { PlaylistItem } from '@/types/metadata.types'

interface Props {
  items: PlaylistItem[]
}

const props = defineProps<Props>()
const emit = defineEmits<{ selectionChange: [indices: number[]] }>()

const selectedIndices = ref<number[]>([])

function toggleItem(index: number): void {
  const pos = selectedIndices.value.indexOf(index)
  if (pos === -1) {
    selectedIndices.value.push(index)
  } else {
    selectedIndices.value.splice(pos, 1)
  }
  emit('selectionChange', [...selectedIndices.value])
}

function selectAll(): void {
  selectedIndices.value = props.items.map((_, i) => i)
  emit('selectionChange', [...selectedIndices.value])
}

function clearAll(): void {
  selectedIndices.value = []
  emit('selectionChange', [])
}

function isSelected(index: number): boolean {
  return selectedIndices.value.includes(index)
}
</script>

<template>
  <div class="space-y-3">
    <div class="flex items-center justify-between">
      <p class="text-sm text-gray-400">
        {{ selectedIndices.length }} / {{ items.length }} selected
      </p>
      <div class="flex gap-2">
        <BaseButton label="Select All" variant="secondary" @click="selectAll" />
        <BaseButton label="Clear" variant="secondary" @click="clearAll" />
      </div>
    </div>

    <ul class="space-y-2 max-h-96 overflow-y-auto pr-1">
      <li
        v-for="(item, index) in items"
        :key="item.url"
        class="flex items-center gap-3 cursor-pointer"
        @click="toggleItem(index)"
      >
        <input
          type="checkbox"
          :checked="isSelected(index)"
          class="flex-shrink-0 w-4 h-4 accent-indigo-500 cursor-pointer"
          @click.stop
          @change="toggleItem(index)"
        />
        <div class="flex-1 min-w-0">
          <TrackCard
            :title="item.title"
            :uploader="item.uploader"
            :duration="item.duration"
            :thumbnail="item.thumbnail"
          />
        </div>
      </li>
    </ul>
  </div>
</template>
