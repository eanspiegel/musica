import { createRouter, createWebHistory } from 'vue-router'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('@/views/HomeView.vue'),
    },
    {
      path: '/download',
      name: 'download',
      component: () => import('@/views/DownloadView.vue'),
    },
    {
      path: '/playlist',
      name: 'playlist',
      component: () => import('@/views/PlaylistView.vue'),
    },
    {
      path: '/tags',
      name: 'tags',
      component: () => import('@/views/TagsEditorView.vue'),
    },
  ],
})
