<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  label: string
  color?: 'green' | 'red' | 'yellow' | 'blue' | 'gray'
}

const props = withDefaults(defineProps<Props>(), {
  color: 'gray',
})

const colorClasses = computed(() => {
  const map = {
    green: 'bg-green-800 text-green-200',
    red: 'bg-red-800 text-red-200',
    yellow: 'bg-yellow-800 text-yellow-200',
    blue: 'bg-blue-800 text-blue-200',
    gray: 'bg-gray-700 text-gray-300',
  }
  return map[props.color]
})
</script>

<template>
  <span
    :class="['inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium', colorClasses]"
  >
    {{ label }}
  </span>
</template>
