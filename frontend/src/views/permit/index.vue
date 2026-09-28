<template>
  <section class="page" data-module="permit">
    <header class="page-head">
      <div>
        <h2>通行证件管理</h2>
        <p class="page-desc">维护通行证件，围绕证件编号、持证人员、所属单位、通行区域做登记、筛选与状态流转。</p>
        <p v-if="isRestricted" class="page-desc">当前账号仅授权管理以下区域：{{ managedAreaText }}；区域内证件仅可查看，不能改动。</p>
      </div>
      <div class="page-actions">
        <button v-if="!isRestricted" class="btn primary" type="button" @click="openCreate">登记通行证件</button>
        <button class="btn" type="button" @click="exportRows">导出通行证件清单</button>
      </div>
    </header>

    <div class="stat-row">
      <article v-for="item in stats" :key="item.label" class="stat-card">
        <span class="stat-label">{{ item.label }}</span>
        <strong class="stat-value">{{ item.value }}</strong>
      </article>
    </div>

    <form class="filter-bar" @submit.prevent="reload">
      <label class="filter-item">
        <span>证件编号</span>
        <input v-model="keyword" placeholder="按证件编号检索" />
      </label>
      <label class="filter-item">
        <span>证件状态</span>
        <select v-model="status">
          <option value="">全部状态</option>
          <option v-for="item in statuses" :key="item" :value="item">{{ item }}</option>
        </select>
      </label>
      <button class="btn" type="submit">查询</button>
      <button class="btn ghost" type="button" @click="resetFilters">重置条件</button>
    </form>

    <table class="data-table">
      <thead>
        <tr>
          <th v-for="column in columns" :key="column">{{ column }}</th>
          <th v-if="!isRestricted">可执行动作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="row in rows" :key="String(row.id)">
          <td v-for="column in columns" :key="column">{{ row[column] ?? '—' }}</td>
          <td v-if="!isRestricted" class="row-actions">
            <button
              v-for="action in actions"
              :key="action"
              class="link"
              type="button"
              @click="runAction(action, row)"
            >
              {{ action }}
            </button>
          </td>
        </tr>
        <tr v-if="!rows.length">
          <td :colspan="isRestricted ? columns.length : columns.length + 1" class="empty-state">暂无当前账号可查看的通行证件</td>
        </tr>
      </tbody>
    </table>

    <footer class="page-foot">
      <span>共 {{ total }} 条通行证件记录</span>
      <span v-if="errorMessage" class="error-text">{{ errorMessage }}</span>
    </footer>
  </section>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { readErrorMessage, request } from '@/api/client'
import { useSessionStore } from '@/stores/session'

type Row = Record<string, string | number | null>
type PermitStats = Record<string, number | undefined>

const ENDPOINT = '/api/permit'
const columns = ['证件编号', '持证人员', '所属单位', '通行区域', '有效期至', '发证人员', '发证日期', '证件状态']
const actions = ['签发证件', '标记过期', '注销证件']
const statuses = ['待发证', '有效使用', '已过期', '已注销']

const session = useSessionStore()
const isRestricted = computed(() => session.isRestricted)
const managedAreaText = computed(() => session.managedAreas?.join('、') ?? '')

const rows = ref<Row[]>([])
const total = ref(0)
const errorMessage = ref('')
const keyword = ref('')
const status = ref('')
const stats = ref([
  { label: '待发证', value: 0 },
  { label: '有效证件', value: 0 },
  { label: '已过期', value: 0 },
  { label: '已注销证件', value: 0 },
])

function resetFilters() {
  keyword.value = ''
  status.value = ''
  void reload()
}

async function exportRows() {
  errorMessage.value = ''
  try {
    const response = await request(`${ENDPOINT}/export`)
    if (!response.ok) {
      throw new Error(await readErrorMessage(response, '通行证件清单导出失败'))
    }
    const blob = await response.blob()
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = '通行证件清单.json'
    link.click()
    URL.revokeObjectURL(link.href)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '通行证件清单导出失败'
  }
}

function openCreate() {
  errorMessage.value = '通行证件登记入口尚未接入审批流'
}

async function runAction(action: string, row: Row) {
  errorMessage.value = ''
  try {
    const response = await request(`${ENDPOINT}/${row.id}/actions`, {
      method: 'POST',
      body: JSON.stringify({ values: { action } }),
    })
    if (!response.ok) {
      throw new Error(await readErrorMessage(response, '通行证件动作未生效，请稍后重试'))
    }
    await reload()
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '通行证件操作失败'
  }
}

function applyStats(value: PermitStats | null | undefined) {
  stats.value = [
    { label: '待发证', value: value?.['待发证'] ?? 0 },
    { label: '有效证件', value: value?.['有效使用'] ?? 0 },
    { label: '已过期', value: value?.['已过期'] ?? 0 },
    { label: '已注销证件', value: value?.['已注销'] ?? 0 },
  ]
}

async function reload() {
  errorMessage.value = ''
  const query = new URLSearchParams()
  if (keyword.value.trim()) {
    query.set('keyword', keyword.value.trim())
  }
  if (status.value) {
    query.set('status', status.value)
  }
  try {
    const response = await request(`${ENDPOINT}?${query.toString()}`)
    if (!response.ok) {
      throw new Error(await readErrorMessage(response, '通行证件列表读取失败'))
    }
    const payload = await response.json()
    rows.value = payload.items ?? []
    total.value = payload.total ?? rows.value.length
    applyStats(payload.stats)
  } catch (error) {
    errorMessage.value = error instanceof Error ? error.message : '通行证件列表读取失败'
  }
}

onMounted(reload)
</script>
