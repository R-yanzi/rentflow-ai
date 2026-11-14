<script setup lang="ts">
import { House } from '@element-plus/icons-vue'
</script>

<template>
  <main class="home-page">
    <section class="hero">
      <el-icon class="hero__icon" :size="48">
        <House />
      </el-icon>

      <h1>RentFlow AI</h1>
      <p>面向上海租房场景的智能决策与房源推荐平台</p>

      <el-button type="primary" size="large">开始智能找房</el-button>
    </section>
  </main>
</template>

<style scoped>
.home-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 32px;
}

.hero {
  max-width: 720px;
  text-align: center;
}

.hero__icon {
  color: var(--el-color-primary);
}

.hero h1 {
  margin: 16px 0;
  font-size: 48px;
}

.hero p {
  margin-bottom: 32px;
  color: #606266;
  font-size: 18px;
}
</style>
