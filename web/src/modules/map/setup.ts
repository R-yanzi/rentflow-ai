import { setWorkerUrl } from 'maplibre-gl'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?worker&url'

let isConfigured = false

/**
 * MapLibre v6 使用独立 Web Worker 处理地图数据。
 *
 * Vite 的 ?worker&url 会把 Worker 作为独立构建资源，
 * 避免生产环境因为 Worker 地址错误而加载失败。
 */
export function configureMapLibre(): void {
  if (isConfigured) {
    return
  }

  setWorkerUrl(workerUrl)
  isConfigured = true
}
