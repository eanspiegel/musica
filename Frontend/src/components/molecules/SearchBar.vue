<script setup lang="ts">
import { ref } from 'vue'
import BaseInput from '@/components/atoms/BaseInput.vue'
import BaseButton from '@/components/atoms/BaseButton.vue'

interface Props {
  loading?: boolean
}

withDefaults(defineProps<Props>(), {
  loading: false,
})

const emit = defineEmits<{ search: [url: string] }>()

const url = ref('')

function handleSearch(): void {
  if (url.value.trim()) {
    emit('search', url.value.trim())
  }
}

function handleKeydown(event: KeyboardEvent): void {
  if (event.key === 'Enter') {
    handleSearch()
  }
}
</script>

<template>
  <div class="flex gap-3" @keydown="handleKeydown">
    <BaseInput
      v-model="url"
      placeholder="Paste a URL…"
      :disabled="loading"
      class="flex-1"
    />
    <BaseButton
      label="Analyze"
      :loading="loading"
      @click="handleSearch"
    />
  </div>
</template>
