<script setup lang="ts">
import { ref, onMounted } from 'vue'
import Button from '@/components/ui/Button.vue'
import Alert from '@/components/ui/Alert.vue'
import AlertTitle from '@/components/ui/AlertTitle.vue'
import AlertDescription from '@/components/ui/AlertDescription.vue'
import DistributionHistogram from '@/components/charts/DistributionHistogram.vue'
import SensitivityLineChart from '@/components/charts/SensitivityLineChart.vue'
import TemperatureHeatmap from '@/components/charts/TemperatureHeatmap.vue'

const feature = ref('length')
const loading = ref(false)
const err = ref('')
const distOpt = ref<any>({})
const sensOpt = ref<any>({})
const heatOpt = ref<any>({})
const metricMode = ref<'method1' | 'method2'>('method2')

const AXIS_STYLE = {
  textStyle: { color: '#94a3b8', fontSize: 11, fontFamily: 'DM Sans, system-ui, sans-serif' },
  axisLine: { lineStyle: { color: '#e2e8f0' } },
  axisTick: { show: false },
  splitLine: { lineStyle: { color: '#f1f5f9' } },
  nameTextStyle: { color: '#94a3b8', fontSize: 11 },
}

function buildHistogram(d: any): any {
  return {
    title: { text: `触发/无触发特征分布（${d.feature}）`, left: 'center', textStyle: { fontSize: 14, fontWeight: 600, color: '#334155' } },
    tooltip: { trigger: 'axis' as const, backgroundColor: '#fff', borderColor: '#e2e8f0', textStyle: { color: '#334155', fontSize: 12 } },
    legend: { data: ['无触发组', '触发组'], bottom: 0, textStyle: { color: '#64748b', fontSize: 11 }, itemWidth: 10, itemHeight: 10 },
    grid: { top: 50, bottom: 40, left: 50, right: 20 },
    xAxis: { type: 'category' as const, data: d.bins, axisLabel: { rotate: 35, fontSize: 10, color: '#94a3b8' }, axisLine: { lineStyle: { color: '#e2e8f0' } }, axisTick: { show: false } },
    yAxis: { type: 'value' as const, name: '频次', ...AXIS_STYLE },
    series: [
      { name: '无触发组', type: 'bar', data: d.noTriggerCounts, itemStyle: { color: '#94a3b8', borderRadius: [4, 4, 0, 0] }, barGap: '15%', barWidth: '35%' },
      { name: '触发组', type: 'bar', data: d.withTriggerCounts, itemStyle: { color: '#0ea5e9', borderRadius: [4, 4, 0, 0] }, barWidth: '35%' },
    ],
  }
}

function buildSensitivity(d: any): any {
  return {
    title: { text: '候选规模 N 对 p 值影响', left: 'center', textStyle: { fontSize: 14, fontWeight: 600, color: '#334155' } },
    tooltip: { trigger: 'axis' as const, backgroundColor: '#fff', borderColor: '#e2e8f0', textStyle: { color: '#334155', fontSize: 12 } },
    grid: { top: 50, bottom: 42, left: 62, right: 20 },
    xAxis: { type: 'category' as const, data: d.nValues.map(String), name: '候选数量 N', ...AXIS_STYLE },
    yAxis: { type: 'log' as const, name: 'p 值', min: 0.000001, max: 1, ...AXIS_STYLE },
    series: [
      {
        name: 'p 值',
        type: 'line',
        data: d.pValues,
        smooth: true,
        lineStyle: { color: '#0284c7', width: 2 },
        markLine: {
          silent: true,
          symbol: 'none',
          data: [{ yAxis: 0.05, label: { formatter: 'p=0.05', fontSize: 10, color: '#ef4444' }, lineStyle: { color: '#ef4444', type: 'dashed' as const, width: 1 } }],
        },
      },
      { name: '散点', type: 'scatter', data: d.pValues, symbolSize: 6, itemStyle: { color: '#0284c7' } },
    ],
  }
}

function buildHeatmap(d: any): any {
  const maxNegLog = Math.max(...d.negLog10Matrix.flat(), 0.1)
  const data: [number, number, number][] = []
  for (let y = 0; y < d.temperatures.length; y++) {
    for (let x = 0; x < d.nValues.length; x++) {
      data.push([x, y, d.negLog10Matrix[y][x]])
    }
  }
  return {
    title: { text: '温度鲁棒性热力图', left: 'center', textStyle: { fontSize: 14, fontWeight: 600, color: '#334155' } },
    tooltip: {
      formatter: (p: any) => {
        const [x, y] = p.data as number[]
        return `T=${d.temperatures[y]}, N=${d.nValues[x]}<br/>p=${d.pValueMatrix[y][x].toExponential(3)}`
      },
      backgroundColor: '#fff',
      borderColor: '#e2e8f0',
      textStyle: { color: '#334155' },
    },
    grid: { top: 50, bottom: 74, left: 70, right: 25 },
    xAxis: { type: 'category' as const, data: d.nValues.map(String), name: 'N', ...AXIS_STYLE },
    yAxis: { type: 'category' as const, data: d.temperatures.map(String), name: 'T', ...AXIS_STYLE },
    visualMap: {
      min: 0,
      max: maxNegLog,
      orient: 'horizontal' as const,
      left: 'center',
      bottom: 8,
      inRange: { color: ['#f1f5f9', '#dbeafe', '#93c5fd', '#38bdf8', '#0284c7'] },
      text: ['高', '低'],
      textStyle: { color: '#94a3b8', fontSize: 10 },
    },
    series: [{ type: 'heatmap' as const, data, label: { show: true, formatter: (p: any) => d.pValueMatrix[p.data[1]][p.data[0]].toExponential(1), fontSize: 9, color: '#475569' } }],
  }
}

async function loadAll() {
  loading.value = true
  err.value = ''
  try {
    const [d1, d2, d3] = await Promise.all([
      fetch(`/api/v1/mock/distribution/${feature.value}`).then(r => r.json()),
      fetch(`/api/v1/mock/sensitivity/${feature.value}`).then(r => r.json()),
      fetch(`/api/v1/mock/heatmap/${feature.value}`).then(r => r.json()),
    ])
    distOpt.value = buildHistogram(d1)
    sensOpt.value = buildSensitivity(d2)
    heatOpt.value = buildHeatmap(d3)
  } catch (e: any) {
    err.value = e.message || '加载失败'
  } finally {
    loading.value = false
  }
}

onMounted(() => loadAll())
</script>

<template>
  <div class="h-full overflow-y-auto p-5 space-y-4">
    <div class="flex items-start justify-between gap-4">
      <div>
        <p class="text-[10px] font-semibold tracking-wide text-sky-600">步骤四 · 统计证据</p>
        <h2 class="mt-1 text-[18px] font-bold text-slate-900 tracking-tight">统计可视化</h2>
        <p class="mt-1 text-[12px] text-slate-500">展示触发组与无触发组的分布差异、候选规模影响与温度鲁棒性。</p>
      </div>
      <div class="flex items-center gap-2.5">
        <select v-model="feature" class="h-9 rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-500/30" @change="loadAll">
          <option value="length">回复长度</option>
          <option value="punctuation">标点密度</option>
          <option value="correctness">正确性</option>
        </select>
        <select v-model="metricMode" class="h-9 rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-500/30">
          <option value="method2">方法 2</option>
          <option value="method1">方法 1</option>
        </select>
        <Button variant="outline" size="sm" :disabled="loading" @click="loadAll">{{ loading ? '加载中...' : '刷新数据' }}</Button>
      </div>
    </div>

    <Alert v-if="err" variant="destructive">
      <AlertTitle>加载失败</AlertTitle>
      <AlertDescription>{{ err }}</AlertDescription>
    </Alert>

    <div class="grid gap-4">
      <div class="rounded-xl border border-slate-100 bg-white p-4">
        <DistributionHistogram :option="distOpt" class="h-[300px]" />
      </div>

      <div class="grid grid-cols-2 gap-4">
        <div class="rounded-xl border border-slate-100 bg-white p-4">
          <SensitivityLineChart :option="sensOpt" class="h-[300px]" />
        </div>
        <div class="rounded-xl border border-slate-100 bg-white p-4">
          <TemperatureHeatmap :option="heatOpt" class="h-[300px]" />
        </div>
      </div>
    </div>
  </div>
</template>
