<script setup lang="ts">
import { computed } from 'vue'

interface Props {
  label: string
  variant?: 'primary' | 'secondary' | 'danger'
  loading?: boolean
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  loading: false,
  disabled: false,
})

const emit = defineEmits<{ click: [] }>()

const classes = computed(() => {
  const base =
    'inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-semibold text-sm transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed'
  const variants = {
    primary: 'bg-indigo-600 hover:bg-indigo-500 text-white',
    secondary: 'bg-gray-700 hover:bg-gray-600 text-white',
    danger: 'bg-red-600 hover:bg-red-500 text-white',
  }
  return [base, variants[props.variant]]
})
</script>

<template>
  <button
    :class="classes"
    :disabled="loading || disabled"
    type="button"
    @click="emit('click')"
  >
    <svg
      v-if="loading"
      class="animate-spin h-4 w-4"
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
    >
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
      <path
        class="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
      />
    </svg>
    {{ label }}
  </button>
</template>
