<script setup lang="ts">
import { MagicStick } from '@element-plus/icons-vue'
import { computed } from 'vue'

import type { RentalRequirements } from '@/modules/search/types'

interface RequirementChip {
  key: string
  label: string
  value: string
  category: 'hard' | 'soft'
}

const props = defineProps<{
  requirements: RentalRequirements
}>()

const chips = computed<RequirementChip[]>(() => {
  const result: RequirementChip[] = []
  const requirements = props.requirements

  if (requirements.district) {
    result.push({
      key: 'district',
      label: '行政区',
      value: requirements.district,
      category: 'hard',
    })
  }

  if (requirements.area) {
    result.push({
      key: 'area',
      label: '板块',
      value: requirements.area,
      category: 'hard',
    })
  }

  if (requirements.max_rent !== null) {
    result.push({
      key: 'max_rent',
      label: '最高租金',
      value: `${requirements.max_rent.toLocaleString('zh-CN')} 元/月`,
      category: 'hard',
    })
  }

  if (requirements.bedrooms !== null) {
    result.push({
      key: 'bedrooms',
      label: '户型',
      value: requirements.bedrooms === 0 ? '开间' : `${requirements.bedrooms} 室`,
      category: 'hard',
    })
  }

  if (requirements.pets_allowed !== null) {
    result.push({
      key: 'pets_allowed',
      label: '宠物',
      value: requirements.pets_allowed ? '必须允许养宠' : '不允许养宠',
      category: 'hard',
    })
  }

  if (requirements.available_before) {
    result.push({
      key: 'available_before',
      label: '最晚入住',
      value: requirements.available_before,
      category: 'hard',
    })
  }

  if (requirements.work_location) {
    result.push({
      key: 'work_location',
      label: '工作地点',
      value: requirements.work_location,
      category: 'soft',
    })
  }

  if (requirements.max_commute_minutes !== null) {
    result.push({
      key: 'max_commute_minutes',
      label: '最长通勤',
      value: `${requirements.max_commute_minutes} 分钟`,
      category: 'soft',
    })
  }

  requirements.preferences.forEach((preference, index) => {
    result.push({
      key: `preference-${index}`,
      label: '偏好',
      value: preference,
      category: 'soft',
    })
  })

  return result
})
</script>

<template>
  <section class="requirement-preview">
    <header class="requirement-preview__header">
      <div>
        <h2>
          <el-icon><MagicStick /></el-icon>
          AI 提取的租房条件
        </h2>
        <p>请确认模型是否正确理解了你的需求。</p>
      </div>

      <el-tag type="warning" effect="plain">待用户确认</el-tag>
    </header>

    <div v-if="chips.length > 0" class="requirement-preview__chips">
      <el-tag
        v-for="chip in chips"
        :key="chip.key"
        :type="chip.category === 'hard' ? 'primary' : 'warning'"
        effect="light"
        size="large"
      >
        <strong>{{ chip.label }}：</strong>{{ chip.value }}
      </el-tag>
    </div>

    <el-empty v-else description="没有从输入中提取到明确条件" :image-size="80" />

    <el-alert
      type="info"
      :closable="false"
      show-icon
      title="硬条件与软偏好会采用不同的处理方式"
      description="预算、区域、户型等条件由数据库严格筛选；通勤和采光等条件将在后续阶段参与计算或排序。"
    />
  </section>
</template>

<style scoped>
.requirement-preview {
  display: grid;
  gap: 20px;
  margin-top: 24px;
  padding: 24px;
  border: 1px solid #e4e7ed;
  border-radius: 16px;
  background: #fff;
}

.requirement-preview__header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.requirement-preview__header h2 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 8px;
  font-size: 20px;
}

.requirement-preview__header h2 .el-icon {
  color: var(--el-color-primary);
}

.requirement-preview__header p {
  margin: 0;
  color: #909399;
}

.requirement-preview__chips {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

@media (width <= 600px) {
  .requirement-preview__header {
    flex-direction: column;
  }
}
</style>
