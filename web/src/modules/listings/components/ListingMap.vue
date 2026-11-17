<script setup lang="ts">
import type { FeatureCollection, Point } from 'geojson'
import { GeoJSONSource, LngLatBounds, Map as MapLibreMap, NavigationControl } from 'maplibre-gl'
import 'maplibre-gl/dist/maplibre-gl.css'
import { nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import type { Listing } from '@/modules/listings/types'
import { createBaseMapStyle, SHANGHAI_CENTER } from '@/modules/map/config'
import { configureMapLibre } from '@/modules/map/setup'

interface ListingFeatureProperties {
  id: string
  title: string
  monthlyRent: number
}

const LISTING_SOURCE_ID = 'listing-points'
const LISTING_LAYER_ID = 'listing-points-layer'
const SELECTED_LAYER_ID = 'selected-listing-layer'

const props = withDefaults(
  defineProps<{
    listings: Listing[]
    selectedListingId?: string | null
  }>(),
  {
    selectedListingId: null,
  },
)

const emit = defineEmits<{
  select: [listingId: string]
}>()

const mapContainer = ref<HTMLDivElement | null>(null)
const mapError = ref('')

let map: MapLibreMap | null = null

/**
 * 地图容器从隐藏状态恢复显示时，宽高会发生变化。
 * ResizeObserver 负责通知 MapLibre 重新计算画布尺寸，
 * 避免移动端切换到地图后出现空白或地图只占一部分。
 */
let mapResizeObserver: ResizeObserver | null = null

/**
 * 将后端房源响应转换为标准 GeoJSON。
 *
 * GeoJSON 坐标顺序固定为 [经度, 纬度]，
 * 不能写成 [纬度, 经度]。
 */
function listingsToGeoJSON(
  listings: Listing[],
): FeatureCollection<Point, ListingFeatureProperties> {
  return {
    type: 'FeatureCollection',
    features: listings.map((listing) => ({
      type: 'Feature',
      id: listing.id,
      geometry: {
        type: 'Point',
        coordinates: [listing.longitude, listing.latitude],
      },
      properties: {
        id: listing.id,
        title: listing.title,
        monthlyRent: listing.monthly_rent,
      },
    })),
  }
}

/**
 * 让地图视口覆盖当前页全部房源。
 */
function fitListings(listings: Listing[]): void {
  if (!map || listings.length === 0) {
    return
  }

  if (listings.length === 1) {
    const listing = listings[0]

    if (!listing) {
      return
    }

    map.easeTo({
      center: [listing.longitude, listing.latitude],
      zoom: 14,
    })
    return
  }

  const firstListing = listings[0]

  if (!firstListing) {
    return
  }

  const bounds = new LngLatBounds(
    [firstListing.longitude, firstListing.latitude],
    [firstListing.longitude, firstListing.latitude],
  )

  for (const listing of listings.slice(1)) {
    bounds.extend([listing.longitude, listing.latitude])
  }

  map.fitBounds(bounds, {
    padding: 48,
    maxZoom: 14,
    duration: 500,
  })
}

/**
 * API 返回新一页房源后，只更新 GeoJSON Source，
 * 不销毁并重新创建整个地图实例。
 */
function updateListingSource(): void {
  if (!map?.isStyleLoaded()) {
    return
  }

  const source = map.getSource(LISTING_SOURCE_ID)

  if (!(source instanceof GeoJSONSource)) {
    return
  }

  source.setData(listingsToGeoJSON(props.listings))
  fitListings(props.listings)
}

/**
 * 选中房源通过独立图层表达，
 * 不需要修改原始房源数组。
 */
function updateSelectedListing(): void {
  if (!map?.isStyleLoaded()) {
    return
  }

  map.setFilter(SELECTED_LAYER_ID, ['==', ['get', 'id'], props.selectedListingId ?? ''])
}

onMounted(() => {
  if (!mapContainer.value) {
    return
  }

  configureMapLibre()

  map = new MapLibreMap({
    container: mapContainer.value,
    style: createBaseMapStyle(),
    center: SHANGHAI_CENTER,
    zoom: 10,
    attributionControl: {
      compact: false,
    },
  })

  mapResizeObserver = new ResizeObserver(() => {
    /**
     * 等待 Vue 和浏览器完成当前布局更新，
     * 再让地图读取最新的容器宽高。
     */
    void nextTick(() => {
      map?.resize()
    })
  })

  mapResizeObserver.observe(mapContainer.value)

  map.addControl(
    new NavigationControl({
      showCompass: false,
    }),
    'top-right',
  )

  map.on('load', () => {
    if (!map) {
      return
    }

    map.addSource(LISTING_SOURCE_ID, {
      type: 'geojson',
      data: listingsToGeoJSON(props.listings),
    })

    map.addLayer({
      id: LISTING_LAYER_ID,
      type: 'circle',
      source: LISTING_SOURCE_ID,
      paint: {
        'circle-radius': 9,
        'circle-color': '#409eff',
        'circle-stroke-color': '#ffffff',
        'circle-stroke-width': 2,
      },
    })

    map.addLayer({
      id: SELECTED_LAYER_ID,
      type: 'circle',
      source: LISTING_SOURCE_ID,
      filter: ['==', ['get', 'id'], props.selectedListingId ?? ''],
      paint: {
        'circle-radius': 13,
        'circle-color': '#f56c6c',
        'circle-stroke-color': '#ffffff',
        'circle-stroke-width': 3,
      },
    })

    map.on('click', LISTING_LAYER_ID, (event) => {
      const listingId = event.features?.[0]?.properties?.id

      if (typeof listingId === 'string') {
        emit('select', listingId)
      }
    })

    map.on('mouseenter', LISTING_LAYER_ID, () => {
      if (map) {
        map.getCanvas().style.cursor = 'pointer'
      }
    })

    map.on('mouseleave', LISTING_LAYER_ID, () => {
      if (map) {
        map.getCanvas().style.cursor = ''
      }
    })

    fitListings(props.listings)
  })

  map.on('error', () => {
    mapError.value = '地图底图暂时无法加载，房源列表仍可正常使用。'
  })
})

watch(
  () => props.listings,
  () => {
    updateListingSource()
  },
  {
    deep: true,
  },
)

watch(
  () => props.selectedListingId,
  () => {
    updateSelectedListing()
  },
)

onBeforeUnmount(() => {
  mapResizeObserver?.disconnect()
  mapResizeObserver = null

  map?.remove()
  map = null
})
</script>

<template>
  <section class="listing-map">
    <el-alert
      v-if="mapError"
      class="listing-map__error"
      type="warning"
      :title="mapError"
      :closable="false"
      show-icon
    />

    <div ref="mapContainer" class="listing-map__canvas" aria-label="当前页房源地图" />
  </section>
</template>

<style scoped>
.listing-map {
  position: relative;
  min-width: 0;
  overflow: hidden;
  border: 1px solid #dcdfe6;
  border-radius: 14px;
  background: #f5f7fa;
}

.listing-map__canvas {
  width: 100%;
  min-height: 560px;
}

.listing-map__error {
  position: absolute;
  z-index: 2;
  top: 12px;
  left: 12px;
  width: calc(100% - 24px);
}

@media (width <= 900px) {
  .listing-map__canvas {
    min-height: 420px;
  }
}
</style>
