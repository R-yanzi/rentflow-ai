<script setup lang="ts">
import { Search } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import RequirementChips from '@/modules/search/components/RequirementChips.vue'
import RequirementInput from '@/modules/search/components/RequirementInput.vue'
import { parseRequirements } from '@/modules/search/api'
import { requirementsToQuery } from '@/modules/search/query'
import type { RentalRequirements } from '@/modules/search/types'

const router = useRouter()

const isParsing = ref(false)
const parsedRequirements = ref<RentalRequirements | null>(null)
const errorMessage = ref('')

async function handleParse(text: string): Promise<void> {
  if (isParsing.value) {
    return
  }

  isParsing.value = true
  parsedRequirements.value = null
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
  if (!parsedRequirements.value || isParsing.value) {
    return
  }

  /**
   * 搜索条件写进 URL，结果页会根据 URL 查询数据库。
   * 这里不再提前请求一次，避免跳转后重复查询。
   */
  await router.push({
    name: 'search-results',
    query: requirementsToQuery(parsedRequirements.value, 1),
  })
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
          :disabled="isParsing"
          @click="handleConfirmedSearch"
        >
          确认条件并搜索房源
        </el-button>
      </div>
    </template>
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
</style>
