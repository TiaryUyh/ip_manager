<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Connection, Monitor, SwitchButton } from '@element-plus/icons-vue'
import { clearAuth, getUser } from '../auth'

const route = useRoute()
const router = useRouter()
const currentUser = getUser()

const activeMenu = computed(() => {
  if (route.path.startsWith('/scan')) return '/scan'
  return '/'
})

function handleSelect(path) {
  if (path !== route.path) {
    router.push(path)
  }
}

function handleLogout() {
  clearAuth()
  ElMessage.success('已退出登录')
  router.replace('/login')
}
</script>

<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="sidebar-brand">IP 管理平台</div>
      <el-menu
        :default-active="activeMenu"
        class="sidebar-menu"
        @select="handleSelect"
      >
        <el-menu-item index="/">
          <el-icon><Monitor /></el-icon>
          <span>IP 管理</span>
        </el-menu-item>
        <el-menu-item index="/scan">
          <el-icon><Connection /></el-icon>
          <span>检测工具</span>
        </el-menu-item>
      </el-menu>
    </aside>

    <div class="main">
      <header class="topbar">
        <h1>{{ route.meta.title || 'IP 地址使用信息平台' }}</h1>
        <div class="topbar-actions">
          <span class="user-chip">
            {{ currentUser?.display_name || currentUser?.username || '用户' }}
          </span>
          <el-button :icon="SwitchButton" @click="handleLogout">退出</el-button>
        </div>
      </header>
      <div class="content">
        <router-view />
      </div>
    </div>
  </div>
</template>

<style scoped>
.layout {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.sidebar {
  position: sticky;
  top: 0;
  width: 220px;
  height: 100vh;
  flex-shrink: 0;
  background: #0f766e;
  color: #fff;
  box-shadow: 4px 0 24px rgba(15, 23, 42, 0.08);
  overflow-y: auto;
}

.sidebar-brand {
  padding: 22px 20px 18px;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: 0.02em;
  border-bottom: 1px solid rgba(255, 255, 255, 0.15);
}

.sidebar-menu {
  border-right: none;
  background: transparent;
  padding: 12px 8px;
}

.sidebar-menu :deep(.el-menu-item) {
  border-radius: 10px;
  margin-bottom: 6px;
  color: rgba(255, 255, 255, 0.88);
}

.sidebar-menu :deep(.el-menu-item:hover) {
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
}

.sidebar-menu :deep(.el-menu-item.is-active) {
  background: rgba(255, 255, 255, 0.2);
  color: #fff;
  font-weight: 600;
}

.main {
  flex: 1;
  min-width: 0;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 24px;
  background: rgba(255, 255, 255, 0.86);
  border-bottom: 1px solid var(--border);
  backdrop-filter: blur(8px);
  flex-shrink: 0;
}

.topbar h1 {
  margin: 0;
  font-size: 18px;
  font-weight: 700;
  color: var(--ink);
}

.topbar-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.user-chip {
  color: var(--muted);
  font-size: 14px;
}

.content {
  flex: 1;
  min-height: 0;
  overflow: auto;
}

@media (max-width: 900px) {
  .layout {
    flex-direction: column;
    height: auto;
    min-height: 100vh;
    overflow: visible;
  }

  .sidebar {
    position: sticky;
    top: 0;
    z-index: 20;
    width: 100%;
    height: auto;
  }

  .main {
    height: auto;
    overflow: visible;
  }

  .content {
    overflow: visible;
  }

  .sidebar-menu {
    display: flex;
    padding-bottom: 8px;
  }

  .sidebar-menu :deep(.el-menu-item) {
    flex: 1;
    justify-content: center;
    margin-bottom: 0;
  }
}
</style>
