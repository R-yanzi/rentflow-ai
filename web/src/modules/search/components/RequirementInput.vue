<script setup lang="ts">
import { Promotion } from '@element-plus/icons-vue'
import { computed, ref } from 'vue'

const props = withDefaults(
  defineProps<{
    loading?: boolean
  }>(),
  {
    loading: false,
  },
)

const emit = defineEmits<{
  submit: [text: string]
}>()

const examples = [
  '预算 7000 元以内，想住在浦东，两室，可以养猫',
  '在静安寺附近找一套一室户，通勤最好不超过 30 分钟',
  '想找采光好、安静的房子，最晚下个月可以入住',
]

const text = ref('')

const canSubmit = computed(() => {
  return text.value.trim().length > 0 && !props.loading
})

function useExample(example: string): void {
  text.value = example
}

function submit(): void {
  const normalizedText = text.value.trim()

  if (!normalizedText || props.loading) {
    return
  }

  // 输入组件只发出事件，不直接调用 API。
  // 请求状态、错误和结果由页面统一管理。
  emit('submit', normalizedText)
}
</script>

<template>
  <section class="requirement-input">
    <label class="requirement-input__label" for="rental-requirement"> 描述你的租房需求 </label>

    <el-input
      id="rental-requirement"
      v-model="text"
      type="textarea"
      :rows="6"
      maxlength="2000"
      show-word-limit
      resize="vertical"
      placeholder="例如：预算 7000 元以内，想住在浦东，两室，可以养猫……"
      @keydown.ctrl.enter="submit"
    />

    <div class="requirement-input__examples">
      <span>试试示例：</span>

      <button
        v-for="example in examples"
        :key="example"
        type="button"
        :disabled="loading"
        @click="useExample(example)"
      >
        {{ example }}
      </button>
    </div>

    <div class="requirement-input__actions">
      <span>按 Ctrl + Enter 快速提交</span>

      <el-button
        class="submit-button"
        type="primary"
        size="large"
        :icon="Promotion"
        :loading="loading"
        :disabled="!canSubmit"
        @click="submit"
      >
        解析租房需求
      </el-button>
    </div>
  </section>
</template>

<style scoped>
.requirement-input {
  display: grid;
  gap: 16px;
}

.requirement-input__label {
  color: #303133;
  font-size: 16px;
  font-weight: 600;
}

.requirement-input__examples {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  color: #909399;
  font-size: 13px;
}

.requirement-input__examples button {
  padding: 5px 10px;
  border: 1px solid #dcdfe6;
  border-radius: 999px;
  color: #606266;
  background: #fff;
  cursor: pointer;
}

.requirement-input__examples button:hover:not(:disabled) {
  border-color: var(--el-color-primary);
  color: var(--el-color-primary);
}

.requirement-input__examples button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.requirement-input__actions {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  color: #909399;
  font-size: 13px;
}

@media (width <= 600px) {
  .requirement-input__actions {
    align-items: stretch;
    flex-direction: column;
  }

  .requirement-input__actions span {
    display: none;
  }
}
</style>
