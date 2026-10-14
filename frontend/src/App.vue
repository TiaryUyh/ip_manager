<script setup>
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import {
  createIpRecord,
  deleteIpRecord,
  fetchCidrs,
  fetchIpRecords,
  fetchStats,
  fetchSubnetMap,
  updateIpRecord,
} from './api/ip'

const loading = ref(false)
const chartLoading = ref(false)
const saving = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const records = ref([])
const total = ref(0)
const cidrOptions = ref([])
const selectedCidr = ref('')
const subnetMap = ref(null)
const selectedHost = ref(null)

const stats = reactive({
  total: 0,
  available: 0,
  in_use: 0,
  reserved: 0,
  disabled: 0,
})

const filters = reactive({
  keyword: '',
  status: '',
  page: 1,
  page_size: 10,
})

const form = reactive(emptyForm())
const formRef = ref()

const statusOptions = [
  { label: '空闲', value: 'available' },
  { label: '使用中', value: 'in_use' },
  { label: '预留', value: 'reserved' },
  { label: '停用', value: 'disabled' },
]

const statusMap = {
  free: { label: '未登记(空闲)', type: 'success', color: '#86efac' },
  available: { label: '空闲', type: 'success', color: '#22c55e' },
  in_use: { label: '使用中', type: 'primary', color: '#3b82f6' },
  reserved: { label: '预留', type: 'warning', color: '#f59e0b' },
  disabled: { label: '停用', type: 'info', color: '#94a3b8' },
}

const rules = {
  ip_address: [
    { required: true, message: '请输入 IP 地址', trigger: 'blur' },
    {
      pattern: /^(?:(?:25[0-5]|2[0-4]\d|[01]?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|[01]?\d?\d)$/,
      message: '请输入有效的 IPv4 地址',
      trigger: 'blur',
    },
  ],
  status: [{ required: true, message: '请选择状态', trigger: 'change' }],
}

const dialogTitle = computed(() => (isEdit.value ? '编辑 IP 记录' : '新增 IP 记录'))

const usagePercents = computed(() => {
  const map = subnetMap.value
  if (!map || !map.host_count) {
    return { free: 0, used: 0 }
  }
  const used = map.in_use + map.reserved + map.disabled + map.available
  const free = map.free
  return {
    free: Math.round((free / map.host_count) * 100),
    used: Math.round((used / map.host_count) * 100),
    freeCount: free,
    usedCount: used,
  }
})

const gridColumns = computed(() => {
  const count = subnetMap.value?.host_count || 0
  if (count <= 16) return 4
  if (count <= 64) return 8
  if (count <= 256) return 16
  return 20
})

function emptyForm() {
  return {
    id: null,
    ip_address: '',
    cidr: '',
    status: 'in_use',
    hostname: '',
    mac_address: '',
    assignee: '',
    department: '',
    location: '',
    description: '',
  }
}

function resetForm() {
  Object.assign(form, emptyForm())
  formRef.value?.clearValidate()
}

async function loadStats() {
  Object.assign(stats, await fetchStats())
}

async function loadRecords() {
  loading.value = true
  try {
    const data = await fetchIpRecords({
      page: filters.page,
      page_size: filters.page_size,
      keyword: filters.keyword || undefined,
      status: filters.status || undefined,
    })
    records.value = data.items
    total.value = data.total
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    loading.value = false
  }
}

async function loadCidrs(preferCidr) {
  try {
    const list = await fetchCidrs()
    cidrOptions.value = list
    if (preferCidr && list.includes(preferCidr)) {
      selectedCidr.value = preferCidr
    } else if (!selectedCidr.value || !list.includes(selectedCidr.value)) {
      selectedCidr.value = list[0] || ''
    }
    if (!list.length) {
      subnetMap.value = null
      selectedHost.value = null
    }
  } catch (error) {
    ElMessage.error(error.message)
  }
}

async function loadSubnetMap() {
  if (!selectedCidr.value) {
    subnetMap.value = null
    selectedHost.value = null
    return
  }

  chartLoading.value = true
  try {
    subnetMap.value = await fetchSubnetMap(selectedCidr.value)
    if (
      selectedHost.value &&
      !subnetMap.value.hosts.some((h) => h.ip_address === selectedHost.value.ip_address)
    ) {
      selectedHost.value = null
    }
  } catch (error) {
    subnetMap.value = null
    ElMessage.error(error.message)
  } finally {
    chartLoading.value = false
  }
}

async function refresh() {
  await Promise.all([loadRecords(), loadStats(), loadCidrs(selectedCidr.value)])
  await loadSubnetMap()
}

function handleSearch() {
  filters.page = 1
  loadRecords()
}

function handleReset() {
  filters.keyword = ''
  filters.status = ''
  filters.page = 1
  loadRecords()
}

function openCreate(preset = {}) {
  isEdit.value = false
  resetForm()
  Object.assign(form, {
    ip_address: preset.ip_address || '',
    cidr: preset.cidr || selectedCidr.value || '',
    status: preset.status || 'in_use',
  })
  dialogVisible.value = true
}

function openEdit(row) {
  isEdit.value = true
  Object.assign(form, {
    id: row.id,
    ip_address: row.ip_address,
    cidr: row.cidr || '',
    status: row.status,
    hostname: row.hostname || '',
    mac_address: row.mac_address || '',
    assignee: row.assignee || '',
    department: row.department || '',
    location: row.location || '',
    description: row.description || '',
  })
  dialogVisible.value = true
}

async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  saving.value = true
  try {
    const payload = {
      ip_address: form.ip_address.trim(),
      cidr: form.cidr || null,
      status: form.status,
      hostname: form.hostname || null,
      mac_address: form.mac_address || null,
      assignee: form.assignee || null,
      department: form.department || null,
      location: form.location || null,
      description: form.description || null,
    }

    if (isEdit.value) {
      await updateIpRecord(form.id, payload)
      ElMessage.success('更新成功')
    } else {
      await createIpRecord(payload)
      ElMessage.success('创建成功')
    }

    dialogVisible.value = false
    await refresh()
  } catch (error) {
    ElMessage.error(error.message)
  } finally {
    saving.value = false
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(`确认删除 IP「${row.ip_address}」吗？`, '删除确认', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
    await deleteIpRecord(row.id)
    ElMessage.success('删除成功')
    if (records.value.length === 1 && filters.page > 1) {
      filters.page -= 1
    }
    await refresh()
  } catch (error) {
    if (error !== 'cancel' && error?.message) {
      ElMessage.error(error.message)
    }
  }
}

function formatTime(value) {
  if (!value) return '-'
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}

function hostTitle(host) {
  const parts = [host.ip_address, statusMap[host.status]?.label || host.status]
  if (host.hostname) parts.push(host.hostname)
  if (host.assignee) parts.push(host.assignee)
  return parts.join(' · ')
}

function selectHost(host) {
  selectedHost.value = host
}

function handleHostDblClick(host) {
  if (host.record_id) {
    const row = records.value.find((item) => item.id === host.record_id)
    if (row) {
      openEdit(row)
      return
    }
  }
  openCreate({
    ip_address: host.ip_address,
    cidr: selectedCidr.value,
    status: host.status === 'free' ? 'in_use' : host.status,
  })
}

watch(selectedCidr, () => {
  loadSubnetMap()
})

onMounted(refresh)
</script>

<template>
  <div class="page">
    <header class="hero">
      <div>
        <p class="eyebrow">IP Address Manager</p>
        <h1>IP 地址使用信息平台</h1>
        <p class="subtitle">统一登记、检索与维护内网 IP 分配情况</p>
      </div>
      <el-button type="primary" size="large" :icon="Plus" @click="openCreate()">
        新增记录
      </el-button>
    </header>

    <section class="stats">
      <article class="stat-card">
        <span>全部</span>
        <strong>{{ stats.total }}</strong>
      </article>
      <article class="stat-card available">
        <span>空闲</span>
        <strong>{{ stats.available }}</strong>
      </article>
      <article class="stat-card in-use">
        <span>使用中</span>
        <strong>{{ stats.in_use }}</strong>
      </article>
      <article class="stat-card reserved">
        <span>预留</span>
        <strong>{{ stats.reserved }}</strong>
      </article>
      <article class="stat-card disabled">
        <span>停用</span>
        <strong>{{ stats.disabled }}</strong>
      </article>
    </section>

    <section class="workspace">
      <div class="panel table-panel">
        <div class="toolbar">
          <el-input
            v-model="filters.keyword"
            clearable
            placeholder="搜索 IP / 主机名 / 使用人 / 部门 / 位置"
            style="max-width: 280px"
            @keyup.enter="handleSearch"
          />
          <el-select
            v-model="filters.status"
            clearable
            placeholder="状态"
            style="width: 120px"
          >
            <el-option
              v-for="item in statusOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </div>

        <el-table v-loading="loading" :data="records" stripe empty-text="暂无 IP 记录" height="560">
          <el-table-column prop="ip_address" label="IP 地址" min-width="120" fixed />
          <el-table-column prop="cidr" label="网段" min-width="120">
            <template #default="{ row }">{{ row.cidr || '-' }}</template>
          </el-table-column>
          <el-table-column prop="status" label="状态" width="90">
            <template #default="{ row }">
              <el-tag :type="statusMap[row.status]?.type || 'info'" effect="light">
                {{ statusMap[row.status]?.label || row.status }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="hostname" label="主机名" min-width="100">
            <template #default="{ row }">{{ row.hostname || '-' }}</template>
          </el-table-column>
          <el-table-column prop="assignee" label="使用人" min-width="90">
            <template #default="{ row }">{{ row.assignee || '-' }}</template>
          </el-table-column>
          <el-table-column prop="department" label="部门" min-width="90">
            <template #default="{ row }">{{ row.department || '-' }}</template>
          </el-table-column>
          <el-table-column label="操作" width="120" fixed="right">
            <template #default="{ row }">
              <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
              <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="pager">
          <el-pagination
            v-model:current-page="filters.page"
            v-model:page-size="filters.page_size"
            background
            layout="total, sizes, prev, pager, next"
            :total="total"
            :page-sizes="[10, 20, 50]"
            @current-change="loadRecords"
            @size-change="
              () => {
                filters.page = 1
                loadRecords()
              }
            "
          />
        </div>
      </div>

      <aside class="panel chart-panel" v-loading="chartLoading">
        <div class="chart-header">
          <div>
            <h2>网段占用图</h2>
            <p>颜色表示使用状态，双击格子可登记/编辑</p>
          </div>
          <el-select
            v-model="selectedCidr"
            clearable
            filterable
            allow-create
            default-first-option
            placeholder="选择或输入网段"
            style="width: 200px"
          >
            <el-option
              v-for="item in cidrOptions"
              :key="item"
              :label="item"
              :value="item"
            />
          </el-select>
        </div>

        <template v-if="subnetMap">
          <div class="usage-summary">
            <div class="usage-bar">
              <span
                class="seg used"
                :style="{ width: usagePercents.used + '%' }"
                :title="`已登记 ${usagePercents.usedCount}`"
              />
              <span
                class="seg free"
                :style="{ width: usagePercents.free + '%' }"
                :title="`未登记空闲 ${usagePercents.freeCount}`"
              />
            </div>
            <div class="usage-meta">
              <span>已登记 {{ usagePercents.usedCount }}（{{ usagePercents.used }}%）</span>
              <span>未登记空闲 {{ usagePercents.freeCount }}（{{ usagePercents.free }}%）</span>
            </div>
            <div class="mini-stats">
              <span><i class="dot in_use" />使用中 {{ subnetMap.in_use }}</span>
              <span><i class="dot available" />空闲 {{ subnetMap.available }}</span>
              <span><i class="dot reserved" />预留 {{ subnetMap.reserved }}</span>
              <span><i class="dot disabled" />停用 {{ subnetMap.disabled }}</span>
              <span><i class="dot free" />未登记 {{ subnetMap.free }}</span>
            </div>
          </div>

          <div
            class="ip-grid"
            :style="{ gridTemplateColumns: `repeat(${gridColumns}, minmax(0, 1fr))` }"
          >
            <button
              v-for="host in subnetMap.hosts"
              :key="host.ip_address"
              type="button"
              class="ip-cell"
              :class="[host.status, { active: selectedHost?.ip_address === host.ip_address }]"
              :title="hostTitle(host)"
              @click="selectHost(host)"
              @dblclick="handleHostDblClick(host)"
            >
              <em>{{ host.ip_address.split('.').pop() }}</em>
            </button>
          </div>

          <div v-if="selectedHost" class="host-detail">
            <strong>{{ selectedHost.ip_address }}</strong>
            <el-tag size="small" :type="statusMap[selectedHost.status]?.type || 'info'">
              {{ statusMap[selectedHost.status]?.label || selectedHost.status }}
            </el-tag>
            <span v-if="selectedHost.hostname">主机：{{ selectedHost.hostname }}</span>
            <span v-if="selectedHost.assignee">使用人：{{ selectedHost.assignee }}</span>
            <el-button
              size="small"
              type="primary"
              plain
              @click="handleHostDblClick(selectedHost)"
            >
              {{ selectedHost.record_id ? '编辑记录' : '登记此 IP' }}
            </el-button>
          </div>
        </template>

        <el-empty
          v-else
          description="请选择网段，或先为记录填写网段字段"
          :image-size="80"
        />
      </aside>
    </section>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="640px" destroy-on-close>
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="IP 地址" prop="ip_address">
              <el-input v-model="form.ip_address" placeholder="例如 192.168.1.10" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="网段" prop="cidr">
              <el-input v-model="form.cidr" placeholder="例如 192.168.1.0/24" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="状态" prop="status">
              <el-select v-model="form.status" style="width: 100%">
                <el-option
                  v-for="item in statusOptions"
                  :key="item.value"
                  :label="item.label"
                  :value="item.value"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="主机名" prop="hostname">
              <el-input v-model="form.hostname" placeholder="设备主机名" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="MAC" prop="mac_address">
              <el-input v-model="form.mac_address" placeholder="可选" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="使用人" prop="assignee">
              <el-input v-model="form.assignee" placeholder="使用人 / 负责人" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="部门" prop="department">
              <el-input v-model="form.department" placeholder="所属部门" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="位置" prop="location">
              <el-input v-model="form.location" placeholder="机房 / 办公室" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="备注" prop="description">
              <el-input
                v-model="form.description"
                type="textarea"
                :rows="3"
                placeholder="用途说明或其他备注"
              />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSubmit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.page {
  max-width: 1480px;
  margin: 0 auto;
  padding: 32px 24px 48px;
}

.hero {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 24px;
}

.eyebrow {
  margin: 0 0 8px;
  color: var(--accent);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.hero h1 {
  margin: 0;
  font-size: clamp(28px, 4vw, 40px);
  line-height: 1.2;
}

.subtitle {
  margin: 10px 0 0;
  color: var(--muted);
}

.stats {
  display: grid;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 20px;
}

.stat-card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 16px;
  padding: 18px 20px;
  box-shadow: var(--shadow);
}

.stat-card span {
  display: block;
  color: var(--muted);
  font-size: 13px;
}

.stat-card strong {
  display: block;
  margin-top: 8px;
  font-size: 28px;
}

.stat-card.available strong {
  color: #059669;
}

.stat-card.in-use strong {
  color: #2563eb;
}

.stat-card.reserved strong {
  color: #d97706;
}

.stat-card.disabled strong {
  color: #64748b;
}

.workspace {
  display: grid;
  grid-template-columns: minmax(0, 1.35fr) minmax(320px, 0.9fr);
  gap: 16px;
  align-items: start;
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
  gap: 12px;
  margin-bottom: 16px;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 18px;
}

.chart-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.chart-header h2 {
  margin: 0;
  font-size: 18px;
}

.chart-header p {
  margin: 6px 0 0;
  color: var(--muted);
  font-size: 13px;
}

.usage-summary {
  margin-bottom: 14px;
}

.usage-bar {
  display: flex;
  height: 12px;
  border-radius: 999px;
  overflow: hidden;
  background: #e2e8f0;
}

.usage-bar .seg.used {
  background: linear-gradient(90deg, #3b82f6, #2563eb);
}

.usage-bar .seg.free {
  background: #86efac;
}

.usage-meta,
.mini-stats {
  display: flex;
  flex-wrap: wrap;
  gap: 10px 14px;
  margin-top: 10px;
  color: var(--muted);
  font-size: 12px;
}

.mini-stats .dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 4px;
}

.dot.free {
  background: #86efac;
}

.dot.available {
  background: #22c55e;
}

.dot.in_use {
  background: #3b82f6;
}

.dot.reserved {
  background: #f59e0b;
}

.dot.disabled {
  background: #94a3b8;
}

.ip-grid {
  display: grid;
  gap: 4px;
  max-height: 420px;
  overflow: auto;
  padding: 2px;
}

.ip-cell {
  appearance: none;
  border: 1px solid transparent;
  border-radius: 4px;
  min-height: 22px;
  padding: 0;
  cursor: pointer;
  transition: transform 0.12s ease, box-shadow 0.12s ease;
}

.ip-cell em {
  display: block;
  font-style: normal;
  font-size: 10px;
  line-height: 22px;
  text-align: center;
  color: rgba(15, 23, 42, 0.72);
}

.ip-cell.free {
  background: #dcfce7;
}

.ip-cell.available {
  background: #86efac;
}

.ip-cell.in_use {
  background: #93c5fd;
}

.ip-cell.reserved {
  background: #fcd34d;
}

.ip-cell.disabled {
  background: #cbd5e1;
}

.ip-cell:hover,
.ip-cell.active {
  transform: scale(1.08);
  box-shadow: 0 0 0 2px rgba(15, 118, 110, 0.35);
  z-index: 1;
}

.host-detail {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid var(--border);
  font-size: 13px;
  color: var(--muted);
}

.host-detail strong {
  color: var(--ink);
}

@media (max-width: 1100px) {
  .workspace {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 900px) {
  .hero {
    flex-direction: column;
    align-items: stretch;
  }

  .stats {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .chart-header {
    flex-direction: column;
  }
}
</style>
