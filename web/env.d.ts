/// <reference types="vite/client" />

/**
 * Vite 只会把以 VITE_ 开头的环境变量暴露给浏览器代码。
 * 不要在这里放数据库密码、API Key 等服务端密钥。
 */
interface ImportMetaEnv {
  readonly VITE_API_BASE_URL?: string

  /**
   * 开发环境默认使用 OSM raster tiles。
   * 正式环境可以切换到商业或自建瓦片服务。
   */
  readonly VITE_MAP_TILE_URL?: string
  readonly VITE_MAP_ATTRIBUTION?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
