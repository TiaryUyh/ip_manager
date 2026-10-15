<script setup>
import { computed, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Search } from '@element-plus/icons-vue'
import { scanSubnet } from '../api/scan'
import { createIpRecord } from '../api/ip'

const scanning = ref(false)
const registering = ref('')
const result = ref(null)
const onlyAlive = ref(true)

const form = reactive({
  cidr: '192.168.1.0/24',
  timeout_ms: 800,
  concurrency: 64,
})

const displayHosts = computed(() => {
  if (!result.value) return []
  const hosts = result.value.hosts || []
  return onlyAlive.value ? hosts.filter((item) => item.alive) : hosts
})

async function handleScan() {
  if (!form.cidr.trim()) {
    ElMessage.warning('请输入要检测的网段')
    return
  }
  scanning.value = true
  result.value = null
  try {
    result.value = await scanSubnet({
      cidr: form.cidr.trim(),
      timeout_ms: form.timeout_ms,
      concurrency: form.concurrency,
    })
    ElMessage.success(
      `扫描完成：发现 ${result.value.alive} 个在线地址，耗时 ${(result.value.duration_ms / 1000).toFixed(1)} 秒`,
    )
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    scanning.value = false
  }
}

async function handleRegister(row) {
  registering.value = row.ip_address
  try {
    await createIpRecord({
      ip_address: row.ip_address,
      cidr: result.value?.cidr || form.cidr.trim(),
      status: 'in_use',
      hostname: null,
      mac_address: null,
      assignee: null,
      department: null,
      location: null,
      description: '由网段检测工具发现',
    })
    row.registered = true
    row.status = 'in_use'
    ElMessage.success(`已登记 ${row.ip_address}`)
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    registering.value = ''
  }
}
</script>

<template>
  <div class="page">
    <section class="panel">
      <div class="toolbar">
        <el-input
          v-model="form.cidr"
          clearable
          placeholder="网段，例如 192.168.1.0/24"
          style="max-width: 260px"
          @keyup.enter="handleScan"
        />
        <el-input-number
          v-model="form.timeout_ms"
          :min="200"
          :max="3000"
          :step="100"
          controls-position="right"
        />
        <span class="field-label">超时(ms)</span>
        <el-input-number
          v-model="form.concurrency"
          :min="1"
          :max="128"
          :step="8"
          controls-position="right"
        />
        <span class="field-label">并发</span>
        <el-button type="primary" :icon="Search" :loading="scanning" @click="handleScan">
          开始检测
        </el-button>
        <el-switch v-model="onlyAlive" active-text="仅显示在线" />
      </div>

      <el-alert
        title="优先 ICMP Ping，失败再尝试常见端口 TCP 探测。Docker 部署需重新构建镜像并授予 NET_RAW 权限；检测的是服务器所在网络，不是你电脑本机网络。单次最多 /24。"
        type="info"
        :closable="false"
        show-icon
        class="tip"
      />

      <el-alert
        v-if="result && result.ping_available === false"
        title="当前环境未检测到 ping 命令，已仅使用 TCP 端口探测，结果可能不完整。"
        type="warning"
        :closable="false"
        show-icon
        class="tip"
      />

      <div v-if="result" class="summary">
        <article>
          <span>网段</span>
          <strong>{{ result.cidr }}</strong>
        </article>
        <article>
          <span>已扫描</span>
          <strong>{{ result.scanned }}</strong>
        </article>
        <article class="alive">
          <span>在线</span>
          <strong>{{ result.alive }}</strong>
        </article>
        <article>
          <span>离线</span>
          <strong>{{ result.offline }}</strong>
        </article>
        <article>
          <span>耗时</span>
          <strong>{{ (result.duration_ms / 1000).toFixed(1) }}s</strong>
        </article>
      </div>

      <el-table
        v-loading="scanning"
        :data="displayHosts"
        stripe
        empty-text="暂无检测结果，请先开始检测"
        height="560"
      >
        <el-table-column prop="ip_address" label="IP 地址" min-width="140" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.alive ? 'success' : 'info'" effect="light">
              {{ row.alive ? '在线' : '离线' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="latency_ms" label="延迟" width="100">
          <template #default="{ row }">
            {{ row.latency_ms != null ? `${row.latency_ms} ms` : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="探测方式" width="100">
          <template #default="{ row }">
            {{ row.method === 'icmp' ? 'Ping' : row.method === 'tcp' ? 'TCP' : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="登记情况" width="110">
          <template #default="{ row }">
            <el-tag :type="row.registered ? 'primary' : 'warning'" effect="plain">
              {{ row.registered ? '已登记' : '未登记' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="hostname" label="主机名" min-width="120">
          <template #default="{ row }">{{ row.hostname || '-' }}</template>
        </el-table-column>
        <el-table-column prop="assignee" label="使用人" min-width="100">
          <template #default="{ row }">{{ row.assignee || '-' }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.alive && !row.registered"
              link
              type="primary"
              :loading="registering === row.ip_address"
              @click="handleRegister(row)"
            >
              登记
            </el-button>
            <span v-else class="muted">-</span>
          </template>
        </el-table-column>
      </el-table>
    </section>
  </div>
</template>

<style scoped>
.page {
  max-width: 1480px;
  margin: 0 auto;
  padding: 20px 24px 48px;
}

.panel {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 18px;
  padding: 20px;
  box-shadow: var(--shadow);
}

.toolbar {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}

.field-label {
  color: var(--muted);
  font-size: 13px;
  margin-left: -4px;
}

.tip {
  margin-bottom: 16px;
}

.summary {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.summary article {
  background: #f8fafc;
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 14px 16px;
}

.summary span {
  display: block;
  color: var(--muted);
  font-size: 13px;
}

.summary strong {
  display: block;
  margin-top: 6px;
  font-size: 22px;
}

.summary .alive strong {
  color: #059669;
}

.muted {
  color: var(--muted);
}

@media (max-width: 900px) {
  .summary {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>
