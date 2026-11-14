<script setup lang="ts">
import { ArrowLeft, Calendar, Location, OfficeBuilding, Van } from '@element-plus/icons-vue'
import { isAxiosError } from 'axios'
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { getListing } from '@/modules/listings/api'
import type { Listing } from '@/modules/listings/types'

const route = useRoute()
const router = useRouter()

const isLoading = ref(false)
const errorMessage = ref('')
const listing = ref<Listing | null>(null)

/**
 * 后端使用 UUID 作为房源编号。
 * 前端提前验证格式，避免把用户输入错误误报为服务器故障。
 */
const UUID_PATTERN = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i

const roomLabel = computed(() => {
  if (!listing.value) {
    return ''
  }

  return listing.value.bedrooms === 0 ? '开间' : `${listing.value.bedrooms} 室`
})

const rentLabel = computed(() => {
  return listing.value?.monthly_rent.toLocaleString('zh-CN') ?? ''
})

const areaLabel = computed(() => {
  if (!listing.value) {
    return ''
  }

  return Number(listing.value.area_sqm).toFixed(1)
})

async function loadListing(): Promise<void> {
  const rawListingId = route.params.id
  const listingId = Array.isArray(rawListingId) ? rawListingId[0] : rawListingId

  if (!listingId || !UUID_PATTERN.test(listingId)) {
    errorMessage.value = '房源编号格式无效。'
    listing.value = null
    return
  }

  isLoading.value = true
  errorMessage.value = ''

  try {
    listing.value = await getListing(listingId)
  } catch (error) {
    listing.value = null

    if (isAxiosError(error) && error.response?.status === 404) {
      errorMessage.value = '该房源不存在或已被删除。'
    } else {
      errorMessage.value = '房源加载失败，请检查后端服务后重试。'
    }
  } finally {
    isLoading.value = false
  }
}

watch(
  () => route.params.id,
  () => {
    void loadListing()
  },
  {
    immediate: true,
  },
)
</script>

<template>
  <section class="detail-page">
    <button class="back-button" type="button" @click="router.back()">
      <el-icon><ArrowLeft /></el-icon>
      返回上一页
    </button>

    <el-alert v-if="errorMessage" type="error" :title="errorMessage" :closable="false" show-icon />

    <div v-loading="isLoading" class="detail-content" aria-live="polite">
      <template v-if="listing">
        <header class="detail-header">
          <div>
            <div class="detail-header__labels">
              <el-tag type="info" effect="plain"> 演示合成数据 </el-tag>

              <el-tag :type="listing.status === 'available' ? 'success' : 'info'">
                {{ listing.status === 'available' ? '当前可租' : listing.status }}
              </el-tag>
            </div>

            <h1>{{ listing.title }}</h1>

            <p>
              <el-icon><Location /></el-icon>
              {{ listing.district }} · {{ listing.area }}
            </p>
          </div>

          <div class="detail-price">
            <strong>¥{{ rentLabel }}</strong>
            <span>/ 月</span>
          </div>
        </header>

        <section class="fact-grid">
          <article>
            <span>户型</span>
            <strong>{{ roomLabel }}</strong>
          </article>

          <article>
            <span>建筑面积</span>
            <strong>{{ areaLabel }} ㎡</strong>
          </article>

          <article>
            <span>楼层</span>
            <strong>{{ listing.floor ?? '未知' }}</strong>
          </article>

          <article>
            <span>朝向</span>
            <strong>{{ listing.orientation ?? '未知' }}</strong>
          </article>

          <article>
            <span>宠物政策</span>
            <strong>
              {{ listing.pets_allowed ? '允许养宠' : '不允许养宠' }}
            </strong>
          </article>

          <article>
            <span>地铁距离</span>
            <strong>
              {{ listing.subway_distance_m === null ? '未知' : `${listing.subway_distance_m} 米` }}
            </strong>
          </article>

          <article>
            <span>最早可入住</span>
            <strong>{{ listing.available_date }}</strong>
          </article>

          <article>
            <span>周边道路</span>
            <strong>
              {{ listing.near_main_road ? '靠近主干道' : '小区内部' }}
            </strong>
          </article>
        </section>

        <div class="detail-columns">
          <el-card shadow="never">
            <template #header>
              <h2>
                <el-icon><OfficeBuilding /></el-icon>
                房源介绍
              </h2>
            </template>

            <p class="description">
              {{ listing.description }}
            </p>

            <div class="detail-tags">
              <el-tag>
                <el-icon><Calendar /></el-icon>
                {{ listing.available_date }} 可入住
              </el-tag>

              <el-tag type="primary" effect="plain">
                <el-icon><Van /></el-icon>
                距地铁
                {{ listing.subway_distance_m ?? '未知' }}
                米
              </el-tag>
            </div>
          </el-card>

          <el-card shadow="never">
            <template #header>
              <h2>
                <el-icon><Location /></el-icon>
                位置
              </h2>
            </template>

            <div class="map-placeholder">
              <p>地图将在 F2.3 接入 MapLibre</p>
              <small>
                坐标：{{ listing.longitude }},
                {{ listing.latitude }}
              </small>
            </div>
          </el-card>
        </div>
      </template>
    </div>
  </section>
</template>

<style scoped>
.detail-page {
  width: min(1200px, calc(100% - 32px));
  margin: 0 auto;
  padding: 40px 0 64px;
}

.back-button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 28px;
  padding: 0;
  border: 0;
  color: #606266;
  background: transparent;
  font: inherit;
  cursor: pointer;
}

.back-button:hover {
  color: var(--el-color-primary);
}

.detail-content {
  min-height: 320px;
}

.detail-header {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 32px;
  padding: 32px;
  border: 1px solid #e4e7ed;
  border-radius: 18px;
  background: #fff;
}

.detail-header__labels {
  display: flex;
  gap: 8px;
}

.detail-header h1 {
  margin: 18px 0 12px;
  font-size: clamp(28px, 5vw, 44px);
}

.detail-header p {
  display: flex;
  align-items: center;
  gap: 6px;
  margin: 0;
  color: #606266;
}

.detail-price {
  flex: 0 0 auto;
  color: #f56c6c;
}

.detail-price strong {
  font-size: 36px;
}

.detail-price span {
  margin-left: 4px;
  color: #909399;
}

.fact-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin: 24px 0;
}

.fact-grid article {
  display: grid;
  gap: 8px;
  padding: 20px;
  border: 1px solid #e4e7ed;
  border-radius: 12px;
  background: #fff;
}

.fact-grid span {
  color: #909399;
  font-size: 13px;
}

.detail-columns {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 24px;
}

.detail-columns h2 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0;
  font-size: 18px;
}

.description {
  color: #606266;
  line-height: 1.8;
}

.detail-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-top: 24px;
}

.map-placeholder {
  min-height: 180px;
  display: grid;
  place-content: center;
  color: #909399;
  border-radius: 10px;
  background: #f5f7fa;
  text-align: center;
}

.map-placeholder p {
  margin: 0 0 8px;
}

@media (width <= 800px) {
  .detail-header {
    align-items: flex-start;
    flex-direction: column;
  }

  .fact-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .detail-columns {
    grid-template-columns: 1fr;
  }
}

@media (width <= 480px) {
  .fact-grid {
    grid-template-columns: 1fr;
  }
}
</style>
