<script setup lang="ts">
interface Props {
  modelValue: string
  placeholder?: string
  type?: string
  disabled?: boolean
}

withDefaults(defineProps<Props>(), {
  type: 'text',
  placeholder: '',
  disabled: false,
})

const emit = defineEmits<{ 'update:modelValue': [value: string] }>()
</script>

<template>
  <input
    :type="type"
    :value="modelValue"
    :placeholder="placeholder"
    :disabled="disabled"
    class="w-full bg-gray-800 text-white placeholder-gray-500 border border-gray-700 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500 disabled:opacity-50"
    @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)"
  />
</template>
