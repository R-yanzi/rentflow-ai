<script setup lang="ts">
import { House, Search } from '@element-plus/icons-vue'
</script>

<template>
  <div class="tenant-layout">
    <header class="tenant-header">
      <div class="tenant-header__content">
        <RouterLink class="brand" to="/">
          <el-icon :size="28">
            <House />
          </el-icon>

          <span>RentFlow AI</span>
        </RouterLink>

        <nav class="navigation" aria-label="租客端主导航">
          <RouterLink to="/">
            <el-icon><House /></el-icon>
            <span>首页</span>
          </RouterLink>

          <RouterLink to="/search">
            <el-icon><Search /></el-icon>
            <span>智能找房</span>
          </RouterLink>
        </nav>
      </div>
    </header>

    <!-- 子路由页面会渲染在公共布局内部。 -->
    <main class="tenant-main">
      <RouterView />
    </main>

    <footer class="tenant-footer">
      <p>RentFlow AI · 当前房源均为演示合成数据</p>
    </footer>
  </div>
</template>

<style scoped>
.tenant-layout {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.tenant-header {
  position: sticky;
  top: 0;
  z-index: 100;
  border-bottom: 1px solid #e4e7ed;
  background: rgb(255 255 255 / 92%);
  backdrop-filter: blur(12px);
}

.tenant-header__content {
  width: min(1200px, calc(100% - 32px));
  height: 64px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #303133;
  font-size: 20px;
  font-weight: 700;
  text-decoration: none;
}

.brand .el-icon {
  color: var(--el-color-primary);
}

.navigation {
  display: flex;
  align-items: center;
  gap: 8px;
}

.navigation a {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 14px;
  border-radius: 8px;
  color: #606266;
  text-decoration: none;
  transition:
    color 0.2s,
    background-color 0.2s;
}

.navigation a:hover,
.navigation a.router-link-exact-active {
  color: var(--el-color-primary);
  background: var(--el-color-primary-light-9);
}

.tenant-main {
  flex: 1;
}

.tenant-footer {
  padding: 20px;
  border-top: 1px solid #e4e7ed;
  color: #909399;
  background: #fff;
  text-align: center;
  font-size: 14px;
}

.tenant-footer p {
  margin: 0;
}

@media (width <= 600px) {
  .tenant-header__content {
    width: min(100% - 20px, 1200px);
  }

  .brand span {
    display: none;
  }

  .navigation a {
    padding: 8px 10px;
  }
}
</style>
