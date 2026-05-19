<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useDemoStore } from '@/stores/demo'
import Button from '@/components/ui/Button.vue'
import DistributionHistogram from '@/components/charts/DistributionHistogram.vue'
import { getEvidence } from '@/api/statistics'

const store = useDemoStore()
const feature = ref<'length' | 'punctuation' | 'correctness'>('length')
const method = ref('method2')
const err = ref('')

const distOpt = ref<any>({})
const nPvOpt = ref<any>({})
const heatOpt = ref<any>({})

const featureLabel = () => (feature.value === 'length' ? 'length' : feature.value === 'punctuation' ? 'punctuation' : 'correctness')

function buildMock() {
  const bins = ['100-150', '150-200', '200-250', '250-300', '300-350', '350-400', '400-450', '450-500', '500-550', '550-600', '600-650', '650-700', '700-750', '750-800']
  const clean = [1, 3, 7, 15, 22, 23, 18, 12, 7, 3, 1, 0, 0, 0]
  const trigger = [0, 0, 0, 5, 12, 15, 18, 20, 16, 11, 6, 3, 1, 0]

  distOpt.value = {
    tooltip: { trigger: 'axis' as const, axisPointer: { type: 'shadow' as const } },
    legend: { data: ['无触发组', '触发组'], bottom: 0 },
    grid: { top: 24, left: 52, right: 20, bottom: 52 },
    xAxis: { type: 'category' as const, data: bins, axisLabel: { rotate: 35 } },
    yAxis: { type: 'value' as const, name: '频次' },
    series: [
      { name: '无触发组', type: 'bar' as const, data: clean, barMaxWidth: 34, itemStyle: { color: '#94a3b8', borderRadius: [5, 5, 0, 0] } },
      { name: '触发组', type: 'bar' as const, data: trigger, barMaxWidth: 34, itemStyle: { color: '#0ea5e9', borderRadius: [5, 5, 0, 0] } },
    ],
  }

  const nVals = [10, 20, 30, 40, 50, 60]
  const pVals = [0.39, 0.12, 0.038, 0.0092, 8.5e-4, 2.4e-5]
  nPvOpt.value = {
    tooltip: {
      trigger: 'axis' as const,
      formatter: (ps: any) => {
        const p = ps?.[0]
        if (!p) return ''
        const v = Number(p.value)
        return `N=${p.name}<br/>p=${v < 0.01 ? v.toExponential(2) : v.toFixed(4)}`
      },
    },
    grid: { top: 24, left: 62, right: 24, bottom: 38 },
    xAxis: { type: 'category' as const, data: nVals.map(String) },
    yAxis: { type: 'log' as const, min: 1e-5, max: 1, name: 'p 值' },
    series: [
      { type: 'line' as const, smooth: true, data: pVals, lineStyle: { color: '#0284c7', width: 2 }, itemStyle: { color: '#1d4ed8' } },
    ],
    markLine: {
      silent: true,
      symbol: 'none',
      data: [{ yAxis: 0.05, lineStyle: { color: '#ef4444', type: 'dashed' as const }, label: { formatter: 'p=0.05', color: '#ef4444' } }],
    },
  }

  heatOpt.value = {
    tooltip: {
      formatter: (p: any) => {
        const [x, y, v] = p.data
        const tv = ['2.0', '1.5', '1.0', '0.5'][y]
        const nv = ['10', '20', '30', '40', '50'][x]
        return `T=${tv}, N=${nv}<br/>p=${Number(v).toExponential(1)}`
      },
    },
    grid: { top: 24, left: 44, right: 18, bottom: 28 },
    xAxis: { type: 'category' as const, data: ['10', '20', '30', '40', '50'] },
    yAxis: { type: 'category' as const, data: ['2', '1.5', '1', '0.5'], name: 'T' },
    visualMap: {
      min: 5e-5,
      max: 2.8e-1,
      calculable: false,
      orient: 'horizontal' as const,
      left: 'center',
      bottom: 2,
      inRange: { color: ['#dbeafe', '#93c5fd', '#38bdf8', '#0ea5e9'] },
      formatter: (v: number) => Number(v).toExponential(1),
    },
    series: [{
      type: 'heatmap' as const,
      label: { show: true, formatter: (p: any) => Number(p.data[2]).toExponential(1), fontSize: 11, color: '#334155' },
      data: [
        [0, 0, 2.8e-1], [1, 0, 9.8e-2], [2, 0, 4.2e-2], [3, 0, 1.8e-2], [4, 0, 6.2e-3],
        [0, 1, 1.5e-1], [1, 1, 4.8e-2], [2, 1, 1.5e-2], [3, 1, 5.8e-3], [4, 1, 1.5e-3],
        [0, 2, 8.9e-2], [1, 2, 2.3e-2], [2, 2, 6.5e-3], [3, 2, 2.1e-3], [4, 2, 4.8e-4],
        [0, 3, 5.2e-2], [1, 3, 1.2e-2], [2, 3, 3.1e-3], [3, 3, 8.0e-4], [4, 3, 5.0e-5],
      ],
    }],
  }
}

async function loadReal() {
  // 保持真实接口能力：若没有实际 task_id，这一页仍默认展示 mock
  const lastTaskId = ''
  if (!lastTaskId) {
    buildMock()
    return
  }

  const data: any = await getEvidence(lastTaskId)
  const clean = data?.feature_distribution?.clean || []
  const trigger = data?.feature_distribution?.trigger || []
  const bins = clean.map((_: any, i: number) => `Q${i + 1}`)

  distOpt.value = {
    tooltip: { trigger: 'axis' as const, axisPointer: { type: 'shadow' as const } },
    legend: { data: ['无触发组', '触发组'], bottom: 0 },
    grid: { top: 24, left: 52, right: 20, bottom: 52 },
    xAxis: { type: 'category' as const, data: bins, axisLabel: { rotate: 35 } },
    yAxis: { type: 'value' as const, name: '频次' },
    series: [
      { name: '无触发组', type: 'bar' as const, data: clean, barMaxWidth: 34, itemStyle: { color: '#94a3b8', borderRadius: [5, 5, 0, 0] } },
      { name: '触发组', type: 'bar' as const, data: trigger, barMaxWidth: 34, itemStyle: { color: '#0ea5e9', borderRadius: [5, 5, 0, 0] } },
    ],
  }

  const conv = data?.pvalue_convergence || []
  nPvOpt.value = {
    tooltip: { trigger: 'axis' as const },
    grid: { top: 24, left: 62, right: 24, bottom: 38 },
    xAxis: { type: 'category' as const, data: conv.map((x: any) => String(x.query_count)) },
    yAxis: { type: 'log' as const, min: 1e-8, max: 1, name: 'p 值' },
    series: [{ type: 'line' as const, smooth: true, data: conv.map((x: any) => x.p_value), lineStyle: { color: '#0284c7', width: 2 }, itemStyle: { color: '#1d4ed8' } }],
    markLine: { silent: true, symbol: 'none', data: [{ yAxis: 0.05, lineStyle: { color: '#ef4444', type: 'dashed' as const }, label: { formatter: 'p=0.05', color: '#ef4444' } }] },
  }

  // 热力图保留原型样式（真实端暂无完整二维返回时继续使用 mock 模板）
  buildMock()
}

async function refreshData() {
  err.value = ''
  try {
    if (store.mockMode) buildMock()
    else await loadReal()
  } catch (e: any) {
    err.value = `${e?.message || '统计证据加载失败'}（已展示 mock）`
    buildMock()
  }
}

onMounted(refreshData)
</script>

<template>
  <div class="h-full overflow-y-auto p-5 space-y-4 bg-[#f3f7fd]">
    <div class="flex items-start justify-between gap-4">
      <div>
        <div class="text-[20px] font-bold text-slate-900">统计可视化</div>
        <p class="text-[14px] text-slate-600 mt-1">展示触发组与无触发组的分布差异、候选规模影响与温度鲁棒性。</p>
      </div>
      <div class="flex gap-2">
        <select v-model="feature" class="h-11 rounded-2xl border border-slate-300 px-4 text-sm bg-white text-slate-700">
          <option value="length">回复长度</option>
          <option value="punctuation">标点密度</option>
          <option value="correctness">正确性</option>
        </select>
        <select v-model="method" class="h-11 rounded-2xl border border-slate-300 px-4 text-sm bg-white text-slate-700">
          <option value="method1">方法1</option>
          <option value="method2">方法2</option>
        </select>
        <Button class="h-11 px-5" @click="refreshData">刷新数据</Button>
      </div>
    </div>

    <div v-if="err" class="rounded-lg border border-rose-200 bg-rose-50 p-3 text-sm text-rose-700">{{ err }}</div>

    <div class="rounded-2xl border border-slate-200 bg-white p-4">
      <div class="text-center text-sm font-semibold text-slate-700 mb-2">触发/无触发特征分布（{{ featureLabel() }}）</div>
      <div class="chart-figure-lg"><DistributionHistogram :option="distOpt" class="w-full h-full" /></div>
    </div>

    <div class="grid grid-cols-2 gap-4">
      <div class="rounded-2xl border border-slate-200 bg-white p-4">
        <div class="text-center text-sm font-semibold text-slate-700 mb-2">候选规模 N 对 p 值影响</div>
        <div class="chart-figure-mid"><DistributionHistogram :option="nPvOpt" class="w-full h-full" /></div>
      </div>
      <div class="rounded-2xl border border-slate-200 bg-white p-4">
        <div class="text-center text-sm font-semibold text-slate-700 mb-2">温度鲁棒性热力图</div>
        <div class="chart-figure-mid"><DistributionHistogram :option="heatOpt" class="w-full h-full" /></div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.chart-figure-lg {
  height: 360px;
  width: 100%;
}
.chart-figure-mid {
  height: 280px;
  width: 100%;
}
@media (max-width: 1100px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
