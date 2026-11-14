import { fileURLToPath, URL } from 'node:url'

import { configDefaults, defineConfig, mergeConfig } from 'vitest/config'

import viteConfig from './vite.config.ts'

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: 'jsdom',
      exclude: [...configDefaults.exclude, 'e2e/**'],
      root: fileURLToPath(new URL('./', import.meta.url)),

      // 让 Element Plus 及其 CSS 经过 Vite 转换，
      // 避免 Node.js 直接加载 CSS 时发生错误。
      server: {
        deps: {
          inline: [/element-plus/],
        },
      },
    },
  }),
)
