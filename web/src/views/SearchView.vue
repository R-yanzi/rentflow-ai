<script setup lang="ts">
import { Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, ref } from 'vue'

import RequirementChips from '@/modules/search/components/RequirementChips.vue'
import RequirementInput from '@/modules/search/components/RequirementInput.vue'
import ListingCard from '@/modules/listings/components/ListingCard.vue'
import { parseRequirements, searchConfirmedListings } from '@/modules/search/api'
import type { NaturalLanguageSearchResponse, RentalRequirements } from '@/modules/search/types'

const isParsing = ref(false)
const isSearching = ref(false)

const parsedRequirements = ref<RentalRequirements | null>(null)
const searchResult = ref<NaturalLanguageSearchResponse | null>(null)
const errorMessage = ref('')

/**
 * 解析和搜索不能同时执行，避免较慢的旧请求覆盖较新的页面状态。
 */
const isBusy = computed(() => {
  return isParsing.value || isSearching.value
})

async function handleParse(text: string): Promise<void> {
  if (isBusy.value) {
    return
  }

  isParsing.value = true
  parsedRequirements.value = null
  searchResult.value = null
  errorMessage.value = ''

  try {
    parsedRequirements.value = await parseRequirements({ text })
    ElMessage.success('租房需求解析成功')
  } catch {
    errorMessage.value = '需求解析失败，请检查后端服务和 DeepSeek 配置后重试。'
  } finally {
    isParsing.value = false
  }
}

async function handleConfirmedSearch(): Promise<void> {
  if (!parsedRequirements.value || isBusy.value) {
    return
  }

  isSearching.value = true
  searchResult.value = null
  errorMessage.value = ''

  try {
    /**
     * 这里传递的是用户已经看到并确认的结构化条件，
     * 不是原始自然语言，因此后端不会再次调用 DeepSeek。
     */
    searchResult.value = await searchConfirmedListings(parsedRequirements.value)

    ElMessage.success('房源搜索完成')
  } catch {
    errorMessage.value = '房源搜索失败，请检查数据库和后端服务后重试。'
  } finally {
    isSearching.value = false
  }
}
</script>

<template>
  <section class="search-page">
    <div class="search-page__heading">
      <p class="eyebrow">AI SEARCH</p>
      <h1>告诉我你的租房需求</h1>
      <p>系统会先提取结构化条件，由你确认后再执行确定性房源筛选。</p>
    </div>

    <el-card class="search-card" shadow="never">
      <RequirementInput :loading="isParsing" @submit="handleParse" />
    </el-card>

    <el-alert
      v-if="errorMessage"
      class="result-message"
      type="error"
      :title="errorMessage"
      show-icon
      :closable="false"
    />

    <template v-if="parsedRequirements">
      <RequirementChips :requirements="parsedRequirements" />

      <div class="confirmation-actions">
        <p>确认以上条件无误后，再执行数据库搜索。</p>

        <el-button
          type="primary"
          size="large"
          :icon="Search"
          :loading="isSearching"
          :disabled="isBusy"
          @click="handleConfirmedSearch"
        >
          确认条件并搜索房源
        </el-button>
      </div>
    </template>

    <section v-if="searchResult" class="search-summary" aria-live="polite">
      <header class="search-summary__header">
        <div>
          <h2>搜索结果</h2>
          <p>
            共找到 {{ searchResult.results.total }} 套符合硬条件的房源， 当前展示
            {{ searchResult.results.items.length }} 套。
          </p>
        </div>

        <el-tag type="success" effect="plain"> 硬条件零违反 </el-tag>
      </header>

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

      <el-empty v-else description="没有完全满足当前硬条件的房源，后续将提供条件放宽建议" />
    </section>
  </section>
</template>
<style scoped>
.search-page {
  width: min(960px, calc(100% - 32px));
  margin: 0 auto;
  padding: 64px 0;
}

.search-page__heading {
  margin-bottom: 32px;
  text-align: center;
}

.search-page__heading h1 {
  margin: 8px 0 16px;
  font-size: clamp(32px, 5vw, 48px);
}

.search-page__heading p {
  color: #606266;
}

.eyebrow {
  color: var(--el-color-primary) !important;
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.16em;
}

.search-card {
  border-radius: 16px;
}

.result-message {
  margin-top: 24px;
}

.confirmation-actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  margin-top: 24px;
  padding: 20px 24px;
  border: 1px solid #d9ecff;
  border-radius: 12px;
  background: var(--el-color-primary-light-9);
}

.confirmation-actions p {
  margin: 0;
  color: #606266;
}

.search-summary {
  margin-top: 32px;
  padding: 16px 24px 24px;
  border: 1px solid #e4e7ed;
  border-radius: 16px;
  background: #fff;
}

@media (width <= 600px) {
  .confirmation-actions {
    align-items: stretch;
    flex-direction: column;
  }
}

.search-summary__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 24px;
}

.search-summary__header h2 {
  margin: 0 0 8px;
}

.search-summary__header p {
  margin: 0;
  color: #606266;
}

.listing-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
  margin-top: 24px;
}

@media (width <= 760px) {
  .listing-grid {
    grid-template-columns: 1fr;
  }
}
</style>
