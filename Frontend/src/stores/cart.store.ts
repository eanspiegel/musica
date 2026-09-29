import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import type { PlaylistItem } from '@/types/metadata.types'

export const useCartStore = defineStore('cart', () => {
  const items = ref<PlaylistItem[]>([])

  // Load from local storage
  const saved = localStorage.getItem('cart_items')
  if (saved) {
    try {
      items.value = JSON.parse(saved)
    } catch (e) {
      console.error('Failed to parse cart items', e)
    }
  }

  // Save to local storage on change
  watch(items, (newItems) => {
    localStorage.setItem('cart_items', JSON.stringify(newItems))
  }, { deep: true })

  function addItem(item: PlaylistItem) {
    if (!items.value.some((i) => i.url === item.url)) {
      items.value.push(item)
    }
  }

  function removeItem(index: number) {
    items.value.splice(index, 1)
  }

  function clearCart() {
    items.value = []
  }

  return { items, addItem, removeItem, clearCart }
})
