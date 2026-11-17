import type { StyleSpecification } from 'maplibre-gl'

export const SHANGHAI_CENTER: [number, number] = [121.58, 31.22]

const tileUrl =
  import.meta.env.VITE_MAP_TILE_URL ?? 'https://tile.openstreetmap.org/{z}/{x}/{y}.png'

const attribution = import.meta.env.VITE_MAP_ATTRIBUTION ?? '© OpenStreetMap contributors'

/**
 * 创建最小 MapLibre Style。
 *
 * 底图地址来自环境变量，避免将特定地图 Provider
 * 写死在业务组件中。
 */
export function createBaseMapStyle(): StyleSpecification {
  return {
    version: 8,
    sources: {
      'base-map': {
        type: 'raster',
        tiles: [tileUrl],
        tileSize: 256,
        minzoom: 0,
        maxzoom: 19,
        attribution,
      },
    },
    layers: [
      {
        id: 'base-map',
        type: 'raster',
        source: 'base-map',
      },
    ],
  }
}
