<script setup lang="ts">
interface Props {
  progress: number
  status?: string
}

withDefaults(defineProps<Props>(), {
  status: '',
})
</script>

<template>
  <div class="space-y-1">
    <div class="w-full bg-gray-700 rounded-full h-2 overflow-hidden">
      <div
        class="bg-green-500 h-2 rounded-full transition-all duration-500"
        :style="{ width: `${Math.min(100, Math.max(0, progress))}%` }"
      />
    </div>
    <p v-if="status" class="text-xs text-gray-400">{{ status }}</p>
  </div>
</template>
