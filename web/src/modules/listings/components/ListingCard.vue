<script setup lang="ts">
import { Location, Van } from '@element-plus/icons-vue'
import { computed } from 'vue'

import type { Listing } from '@/modules/listings/types'

const props = defineProps<{
  listing: Listing
}>()

const roomLabel = computed(() => {
  return props.listing.bedrooms === 0 ? '开间' : `${props.listing.bedrooms} 室`
})

const rentLabel = computed(() => {
  return props.listing.monthly_rent.toLocaleString('zh-CN')
})

const areaLabel = computed(() => {
  return Number(props.listing.area_sqm).toFixed(1)
})
</script>

<template>
  <el-card class="listing-card" shadow="hover">
    <template #header>
      <div class="listing-card__header">
        <div>
          <h3>{{ listing.title }}</h3>

          <p>
            <el-icon><Location /></el-icon>
            {{ listing.district }} · {{ listing.area }}
          </p>
        </div>

        <el-tag type="info" effect="plain">演示合成数据</el-tag>
      </div>
    </template>

    <div class="listing-card__price">
      <strong>¥{{ rentLabel }}</strong>
      <span>/ 月</span>
    </div>

    <dl class="listing-card__facts">
      <div>
        <dt>户型</dt>
        <dd>{{ roomLabel }}</dd>
      </div>

      <div>
        <dt>面积</dt>
        <dd>{{ areaLabel }} ㎡</dd>
      </div>

      <div>
        <dt>楼层</dt>
        <dd>{{ listing.floor ?? '未知' }}</dd>
      </div>

      <div>
        <dt>朝向</dt>
        <dd>{{ listing.orientation ?? '未知' }}</dd>
      </div>
    </dl>

    <p class="listing-card__description">
      {{ listing.description }}
    </p>

    <div class="listing-card__tags">
      <el-tag :type="listing.pets_allowed ? 'success' : 'info'" size="small">
        {{ listing.pets_allowed ? '允许养宠' : '不允许养宠' }}
      </el-tag>

      <el-tag v-if="listing.subway_distance_m !== null" type="primary" size="small" effect="plain">
        <el-icon><Van /></el-icon>
        距地铁约 {{ listing.subway_distance_m }} 米
      </el-tag>

      <el-tag v-if="listing.near_main_road" type="warning" size="small" effect="plain">
        靠近主干道
      </el-tag>
    </div>
  </el-card>
</template>

<style scoped>
.listing-card {
  height: 100%;
  border-radius: 14px;
}

.listing-card__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.listing-card__header h3 {
  margin: 0 0 8px;
  font-size: 18px;
}

.listing-card__header p {
  display: flex;
  align-items: center;
  gap: 5px;
  margin: 0;
  color: #909399;
  font-size: 14px;
}

.listing-card__price {
  margin-bottom: 20px;
  color: #f56c6c;
}

.listing-card__price strong {
  font-size: 28px;
}

.listing-card__price span {
  margin-left: 4px;
  color: #909399;
}

.listing-card__facts {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  margin: 0 0 18px;
  padding: 14px;
  border-radius: 10px;
  background: #f5f7fa;
}

.listing-card__facts div {
  text-align: center;
}

.listing-card__facts dt {
  margin-bottom: 6px;
  color: #909399;
  font-size: 12px;
}

.listing-card__facts dd {
  margin: 0;
  color: #303133;
  font-weight: 600;
}

.listing-card__description {
  min-height: 44px;
  margin: 0 0 18px;
  overflow: hidden;
  color: #606266;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.listing-card__tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

@media (width <= 600px) {
  .listing-card__facts {
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }
}
</style>
