import { fileURLToPath, URL } from 'node:url'

import vue from '@vitejs/plugin-vue'
import AutoImport from 'unplugin-auto-import/vite'
import Components from 'unplugin-vue-components/vite'
import { ElementPlusResolver } from 'unplugin-vue-components/resolvers'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [
    vue(),

    // 自动按需导入 ElMessage、ElNotification 等函数式 API。
    AutoImport({
      resolvers: [ElementPlusResolver()],
      dts: 'src/types/auto-imports.d.ts',
    }),

    // 自动导入模板中使用的 Element Plus 组件及对应样式。
    Components({
      resolvers: [ElementPlusResolver()],
      dts: 'src/types/components.d.ts',
    }),
  ],

  resolve: {
    alias: {
      // 使用 "@/..." 指向 src 目录。
      '@': fileURLToPath(new URL('./src', import.meta.url)),
    },
  },

  server: {
    proxy: {
      /**
       * 浏览器请求 /api/v1/... 时，Vite 在开发环境中
       * 将请求转发给本地 FastAPI。
       */
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
