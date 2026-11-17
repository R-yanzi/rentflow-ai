<script setup lang="ts">
import { ArrowLeft } from '@element-plus/icons-vue'
import { defineAsyncComponent, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import ListingCard from '@/modules/listings/components/ListingCard.vue'
import RequirementChips from '@/modules/search/components/RequirementChips.vue'
import { searchConfirmedListings } from '@/modules/search/api'
import { requirementsToQuery, searchStateFromQuery } from '@/modules/search/query'
import type { NaturalLanguageSearchResponse, RentalRequirements } from '@/modules/search/types'

/**
 * MapLibre 体积较大，单独异步加载。
 *
 * 搜索结果页可以先展示条件和房源列表，
 * 不必等待地图库下载完成。
 */
const ListingMap = defineAsyncComponent(
  () => import('@/modules/listings/components/ListingMap.vue'),
)

/**
 * 移动端屏幕一次只展示一种主要内容，
 * 用户可以在房源列表和地图之间切换。
 */
type MobileResultView = 'list' | 'map'

const PAGE_SIZE = 20

const route = useRoute()
const router = useRouter()

const isLoading = ref(false)
const errorMessage = ref('')
const searchResult = ref<NaturalLanguageSearchResponse | null>(null)
const currentRequirements = ref<RentalRequirements | null>(null)
const currentPage = ref(1)

/**
 * 移动端默认先展示列表，保证地图加载失败时
 * 用户仍然可以正常浏览和进入房源详情。
 */
const mobileResultView = ref<MobileResultView>('list')

/**
 * 只保存当前页面选中的房源 ID。
 * 房源事实仍然来自后端响应，不复制到新的状态对象中。
 */
const selectedListingId = ref<string | null>(null)

function handleListingSelect(listingId: string): void {
  selectedListingId.value = listingId
}

/**
 * 从当前 URL 恢复条件并查询对应页。
 *
 * 翻页和浏览器刷新都会进入同一个函数，
 * 因此结果页不依赖搜索页的内存状态。
 */
async function loadResults(): Promise<void> {
  const routeState = searchStateFromQuery(route.query)

  currentRequirements.value = routeState.requirements
  currentPage.value = routeState.page
  isLoading.value = true
  errorMessage.value = ''

  try {
    const result = await searchConfirmedListings({
      requirements: routeState.requirements,
      limit: PAGE_SIZE,
      offset: (routeState.page - 1) * PAGE_SIZE,
    })

    searchResult.value = result

    /**
     * 翻页后，如果原选中房源不在新一页中，
     * 清除选中状态，避免地图保留一个不存在的 ID。
     */
    const selectedStillExists =
      selectedListingId.value !== null &&
      result.results.items.some((listing) => listing.id === selectedListingId.value)

    if (!selectedStillExists) {
      selectedListingId.value = null
    }
  } catch {
    searchResult.value = null
    errorMessage.value = '房源加载失败，请检查后端和数据库服务后重试。'
  } finally {
    isLoading.value = false
  }
}

/**
 * 页码写入 URL，URL 变化后 watch 会自动重新查询。
 */
async function handlePageChange(page: number): Promise<void> {
  if (!currentRequirements.value || isLoading.value) {
    return
  }

  await router.push({
    name: 'search-results',
    query: requirementsToQuery(currentRequirements.value, page),
  })
}

/**
 * fullPath 包含完整查询参数。
 * 刷新、浏览器前进后退和分页跳转都会触发重新加载。
 */
watch(
  () => route.fullPath,
  () => {
    void loadResults()
  },
  {
    immediate: true,
  },
)
</script>

<template>
  <section class="results-page">
    <RouterLink class="back-link" to="/search">
      <el-icon><ArrowLeft /></el-icon>
      修改搜索条件
    </RouterLink>

    <header class="results-page__heading">
      <div>
        <p class="eyebrow">SEARCH RESULTS</p>
        <h1>房源搜索结果</h1>
        <p>页面刷新后会根据 URL 中的条件重新查询。</p>
      </div>

      <el-tag type="success" effect="plain"> 硬条件零违反 </el-tag>
    </header>

    <RequirementChips v-if="currentRequirements" :requirements="currentRequirements" />

    <el-alert
      v-if="errorMessage"
      class="result-message"
      type="error"
      :title="errorMessage"
      :closable="false"
      show-icon
    />

    <div v-loading="isLoading" class="results-content" aria-live="polite">
      <template v-if="searchResult">
        <div class="results-summary">
          <h2>共找到 {{ searchResult.results.total }} 套房源</h2>
          <p>第 {{ currentPage }} 页，当前展示 {{ searchResult.results.items.length }} 套。</p>
        </div>

        <el-alert
          v-if="searchResult.unresolved_requirements.length > 0"
          type="warning"
          title="以下条件当前尚未参与数据库筛选"
          :description="searchResult.unresolved_requirements.join('、')"
          :closable="false"
          show-icon
        />

        <div
          v-if="searchResult.results.items.length > 0"
          class="mobile-view-switch"
          role="group"
          aria-label="搜索结果展示方式"
        >
          <el-button
            :type="mobileResultView === 'list' ? 'primary' : 'default'"
            :aria-pressed="mobileResultView === 'list'"
            @click="mobileResultView = 'list'"
          >
            房源列表
          </el-button>

          <el-button
            :type="mobileResultView === 'map' ? 'primary' : 'default'"
            :aria-pressed="mobileResultView === 'map'"
            @click="mobileResultView = 'map'"
          >
            地图
          </el-button>
        </div>

        <div v-if="searchResult.results.items.length > 0" class="results-layout">
          <div
            class="listing-grid"
            :class="{ 'results-pane--mobile-hidden': mobileResultView !== 'list' }"
          >
            <ListingCard
              v-for="listing in searchResult.results.items"
              :key="listing.id"
              :listing="listing"
              :selected="listing.id === selectedListingId"
              @select="handleListingSelect"
            />
          </div>

          <ListingMap
            class="results-map"
            :class="{ 'results-pane--mobile-hidden': mobileResultView !== 'map' }"
            :listings="searchResult.results.items"
            :selected-listing-id="selectedListingId"
            @select="handleListingSelect"
          />
        </div>

        <el-empty v-else description="没有完全满足当前硬条件的房源" />

        <el-pagination
          v-if="searchResult.results.total > PAGE_SIZE"
          class="results-pagination"
          background
          layout="prev, pager, next"
          :current-page="currentPage"
          :page-size="PAGE_SIZE"
          :total="searchResult.results.total"
          :disabled="isLoading"
          @current-change="handlePageChange"
        />
      </template>
    </div>
  </section>
</template>

<style scoped>
.results-page {
  width: min(1200px, calc(100% - 32px));
  margin: 0 auto;
  padding: 40px 0 64px;
}

.back-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 28px;
  color: #606266;
  text-decoration: none;
}

.back-link:hover {
  color: var(--el-color-primary);
}

.results-page__heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 24px;
}

.results-page__heading h1 {
  margin: 6px 0 10px;
  font-size: clamp(30px, 5vw, 44px);
}

.results-page__heading p {
  margin: 0;
  color: #606266;
}

.eyebrow {
  color: var(--el-color-primary) !important;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.16em;
}

.result-message {
  margin-top: 24px;
}

.results-content {
  min-height: 240px;
  margin-top: 32px;
}

.results-summary {
  margin-bottom: 20px;
}

.results-summary h2 {
  margin: 0 0 8px;
}

.results-summary p {
  margin: 0;
  color: #909399;
}

.results-layout {
  display: grid;
  grid-template-columns:
    minmax(0, 1.05fr)
    minmax(380px, 0.95fr);
  gap: 24px;
  align-items: start;
  margin-top: 24px;
}

.listing-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
}

.results-map {
  position: sticky;
  top: 24px;
}

.results-pagination {
  justify-content: center;
  margin-top: 32px;
}

.mobile-view-switch {
  display: none;
}

@media (width <= 1000px) {
  .results-layout {
    grid-template-columns: 1fr;
  }

  .results-map {
    position: static;
    order: -1;
  }

  .results-page__heading {
    flex-direction: column;
  }
}

@media (width <= 760px) {
  .mobile-view-switch {
    display: flex;
    margin-top: 24px;
  }

  .mobile-view-switch :deep(.el-button) {
    flex: 1;
  }

  /**
   * 只在移动端隐藏未选中的面板。
   * 桌面端即使 mobileResultView 默认为 list，
   * 列表和地图仍然会同时显示。
   */
  .results-pane--mobile-hidden {
    display: none;
  }
}
</style>
