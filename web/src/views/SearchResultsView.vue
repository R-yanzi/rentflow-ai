<script setup lang="ts">
import { ArrowLeft } from '@element-plus/icons-vue'
import { ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import ListingCard from '@/modules/listings/components/ListingCard.vue'
import RequirementChips from '@/modules/search/components/RequirementChips.vue'
import { searchConfirmedListings } from '@/modules/search/api'
import { requirementsToQuery, searchStateFromQuery } from '@/modules/search/query'
import type { NaturalLanguageSearchResponse, RentalRequirements } from '@/modules/search/types'

const PAGE_SIZE = 20

const route = useRoute()
const router = useRouter()

const isLoading = ref(false)
const errorMessage = ref('')
const searchResult = ref<NaturalLanguageSearchResponse | null>(null)
const currentRequirements = ref<RentalRequirements | null>(null)
const currentPage = ref(1)

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
    searchResult.value = await searchConfirmedListings({
      requirements: routeState.requirements,
      limit: PAGE_SIZE,
      offset: (routeState.page - 1) * PAGE_SIZE,
    })
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

        <div v-if="searchResult.results.items.length > 0" class="listing-grid">
          <ListingCard
            v-for="listing in searchResult.results.items"
            :key="listing.id"
            :listing="listing"
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

.listing-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
  margin-top: 24px;
}

.results-pagination {
  justify-content: center;
  margin-top: 32px;
}

@media (width <= 760px) {
  .results-page__heading {
    flex-direction: column;
  }

  .listing-grid {
    grid-template-columns: 1fr;
  }
}
</style>
