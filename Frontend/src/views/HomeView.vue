<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useMediaInfo } from '@/composables/useMediaInfo'
import { useCartStore } from '@/stores/cart.store'
import VideoGridCard from '@/components/molecules/VideoGridCard.vue'

const route = useRoute()
const { info, loading: infoLoading, analyzeUrl } = useMediaInfo()
const cartStore = useCartStore()

async function executeSearch(query: string): Promise<void> {
  const q = query.trim()
  if (!q) return
  
  let urlToSearch = q
  if (!urlToSearch.startsWith('http') && !urlToSearch.startsWith('ytsearch')) {
    urlToSearch = `ytsearch20:${urlToSearch}`
  }
  
  await analyzeUrl(urlToSearch)
}

// Watch for route query changes (when user searches from the global header)
watch(() => route.query.q, (newQ) => {
  if (newQ) {
    executeSearch(newQ as string)
  }
})

// Initial load
onMounted(() => {
  const initialQ = route.query.q ? (route.query.q as string) : 'top hits'
  executeSearch(initialQ)
})

function handleAdd(item: any): void {
  if (!item || !item.url) return
  cartStore.addItem(item)
}
</script>

<template>
  <div class="p-6 max-w-[1600px] mx-auto">
    <div v-if="infoLoading" class="flex justify-center py-20">
      <div class="w-10 h-10 border-4 border-[#303030] border-t-red-600 rounded-full animate-spin"></div>
    </div>
    
    <template v-else-if="info">
      <!-- Grid de Resultados -->
      <div 
        v-if="info.type === 'playlist' && info.playlist_items"
        class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-x-4 gap-y-10"
      >
        <VideoGridCard 
          v-for="(item, idx) in info.playlist_items" 
          :key="item.url || idx"
          :item="item"
          :selected="cartStore.items.some(i => i.url === item.url)"
          @click="handleAdd(item)"
        />
      </div>
      
      <!-- Resultado de link directo a 1 video -->
      <div v-else-if="info.type === 'video'" class="flex justify-center">
        <div class="w-full max-w-sm">
          <VideoGridCard 
            :item="info"
            :selected="cartStore.items.some(i => i.url === info.url)"
            @click="handleAdd(info)"
          />
        </div>
      </div>
    </template>
  </div>
</template>

<style>
.hide-scrollbar::-webkit-scrollbar {
  display: none;
}
.hide-scrollbar {
  -ms-overflow-style: none;
  scrollbar-width: none;
}
</style>
