import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),

  routes: [
    {
      path: '/',
      // 租客端页面共享导航栏、页脚和内容容器。
      component: () => import('@/layouts/TenantLayout.vue'),

      children: [
        {
          path: '',
          name: 'home',
          component: () => import('@/views/HomeView.vue'),
        },
        {
          path: 'search',
          name: 'search',
          component: () => import('@/views/SearchView.vue'),
        },
      ],
    },
  ],
})

export default router
