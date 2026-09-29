<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  label: string
  color?: 'brand' | 'success' | 'warning' | 'error' | 'info' | 'neutral'
}

const props = withDefaults(defineProps<Props>(), {
  color: 'neutral',
})

const colorClass = computed(() => {
  const map: Record<string, string> = {
    brand: 'badge-brand',
    success: 'badge-success',
    warning: 'badge-warning',
    error: 'badge-error',
    info: 'badge-info',
    neutral: 'badge-neutral',
  }
  return map[props.color]
})
</script>

<template>
  <span :class="colorClass">{{ label }}</span>
</template>
