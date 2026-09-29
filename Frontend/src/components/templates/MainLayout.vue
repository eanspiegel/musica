<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useCartStore } from '@/stores/cart.store'

const router = useRouter()
const cartStore = useCartStore()
const searchQuery = ref('')

function handleGlobalSearch() {
  const q = searchQuery.value.trim()
  if (q) {
    // Navigate to HomeView with a query parameter
    router.push({ name: 'home', query: { q } })
  }
}
</script>

<template>
  <div class="flex flex-col h-screen bg-[#0f0f0f] text-white font-sans overflow-hidden">
    <!-- Sticky Top Header -->
    <header class="flex items-center justify-between h-14 px-4 bg-[#0f0f0f] shrink-0 border-b border-[#303030] z-50">
      <div class="flex items-center gap-4">
        <RouterLink to="/" class="flex items-center gap-1 cursor-pointer">
          <!-- YouTube Logo Fake -->
          <svg class="w-8 h-6 text-red-600" fill="currentColor" viewBox="0 0 24 24"><path d="M21.58 6.4a2.76 2.76 0 0 0-1.94-1.95C17.93 4 12 4 12 4s-5.93 0-7.64.45A2.76 2.76 0 0 0 2.42 6.4C2 8.12 2 12 2 12s0 3.88.42 5.6a2.76 2.76 0 0 0 1.94 1.95C6.07 20 12 20 12 20s5.93 0 7.64-.45a2.76 2.76 0 0 0 1.94-1.95C22 15.88 22 12 22 12s0-3.88-.42-5.6zM10 15.46V8.54L16 12l-6 3.46z"></path></svg>
          <span class="text-xl font-semibold tracking-tighter">YouTube<sup class="text-[10px] text-gray-400 font-normal ml-1">Downloader</sup></span>
        </RouterLink>
      </div>

      <!-- Search Bar -->
      <div class="flex items-center max-w-[720px] w-full mx-4">
        <div class="flex items-center w-full bg-[#121212] border border-[#303030] rounded-l-full px-4 py-0.5 focus-within:border-blue-500 overflow-hidden">
          <input 
            v-model="searchQuery"
            @keyup.enter="handleGlobalSearch"
            type="text" 
            placeholder="Buscar en YouTube..." 
            class="w-full bg-transparent outline-none py-2 text-base"
          />
          <button v-if="searchQuery" @click="searchQuery = ''" class="hover:bg-[#272727] rounded-full p-1 text-gray-400">
            <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 24 24"><path d="M12.7 12l5.6-5.6-1.4-1.4-5.6 5.6-5.6-5.6-1.4 1.4 5.6 5.6-5.6 5.6 1.4 1.4 5.6-5.6 5.6 5.6 1.4-1.4-5.6-5.6z"></path></svg>
          </button>
        </div>
        <button 
          @click="handleGlobalSearch"
          class="bg-[#222222] border border-l-0 border-[#303030] rounded-r-full px-6 py-[9px] hover:bg-[#303030] transition-colors"
          title="Buscar"
        >
          <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 24 24"><path d="M20.87 20.17l-5.59-5.59C16.35 13.35 17 11.75 17 10c0-3.87-3.13-7-7-7s-7 3.13-7 7 3.13 7 7 7c1.75 0 3.35-.65 4.58-1.71l5.59 5.59.7-.7zM10 16c-3.31 0-6-2.69-6-6s2.69-6 6-6 6 2.69 6 6-2.69 6-6 6z"></path></svg>
        </button>
      </div>

      <!-- Right Actions -->
      <div class="flex items-center gap-4">
        <RouterLink to="/tags" class="text-sm font-medium text-gray-300 hover:text-white transition-colors" title="Editor de Etiquetas">
          Etiquetas
        </RouterLink>
        
        <!-- Active Downloads Link -->
        <RouterLink to="/downloads" class="p-2 hover:bg-[#272727] rounded-full transition-colors text-gray-300 hover:text-white" title="Estado de Descargas">
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"></path>
          </svg>
        </RouterLink>

        <!-- Shopping Cart Icon -->
        <RouterLink to="/queue" class="relative p-2 hover:bg-[#272727] rounded-full transition-colors group">
          <svg class="w-6 h-6 text-gray-200 group-hover:text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z"></path>
          </svg>
          <span 
            v-if="cartStore.items.length > 0" 
            class="absolute top-0 right-0 bg-red-600 text-white text-[10px] font-bold w-4 h-4 rounded-full flex items-center justify-center transform translate-x-1 -translate-y-1"
          >
            {{ cartStore.items.length }}
          </span>
        </RouterLink>
      </div>
    </header>

    <div class="flex flex-1 overflow-hidden relative">
      <main class="flex-1 overflow-y-auto w-full">
        <RouterView />
      </main>
    </div>
  </div>
</template>
