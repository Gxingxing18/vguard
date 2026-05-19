<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useDemoStore } from '@/stores/demo'
import Button from '@/components/ui/Button.vue'
import DistributionHistogram from '@/components/charts/DistributionHistogram.vue'
import { listModels } from '@/api/models'

const store = useDemoStore()
const selectedRow = ref<any>(null)
const err = ref('')
const loading = ref(false)

const selectedKey = computed(() => store.modelNavKey || 'model-overview')
const isOverview = computed(() => selectedKey.value === 'model-overview')

const base = ref<any[]>([])
const wm = ref<any[]>([])
const target = ref<any[]>([])
const gens = ref<any[]>([])

async function load() {
  err.value = ''
  if (store.mockMode) {
    base.value = store.baseVerifiers as any[]
    wm.value = store.watermarkedVerifiers as any[]
    target.value = store.targetVerifiers as any[]
    gens.value = store.genModels as any[]
    return
  }
  loading.value = true
  try {
    const data: any = await listModels()
    base.value = data.base_verifiers || []
    wm.value = data.watermarked_verifiers || []
    target.value = data.target_verifiers || []
    gens.value = data.generators || []
  } catch (e: any) {
    err.value = `${e?.message || '模型列表加载失败'}（已展示 mock 数据）`
    base.value = store.baseVerifiers as any[]
    wm.value = store.watermarkedVerifiers as any[]
    target.value = store.targetVerifiers as any[]
    gens.value = store.genModels as any[]
  } finally {
    loading.value = false
  }
}

onMounted(load)

const stats = computed(() => ({
  baseVerifierCount: base.value.length,
  watermarkedVerifierCount: wm.value.length,
  targetCount: target.value.length,
  genModelCount: gens.value.length,
}))

const assetPieOpt = computed(() => ({
  tooltip: { trigger: 'item' as const },
  series: [{ type: 'pie' as const, radius: ['42%', '68%'], data: [
    { name: '基础 Verifier', value: stats.value.baseVerifierCount },
    { name: '水印 Verifier', value: stats.value.watermarkedVerifierCount },
    { name: '待检测目标', value: stats.value.targetCount },
    { name: '候选生成模型', value: stats.value.genModelCount },
  ] }],
}))

const wmTypeBarOpt = computed(() => {
  const count = { label: 0, length: 0, punctuation: 0 }
  wm.value.forEach((x: any) => {
    const f = String(x.feature || x.metadata?.feature || '')
    const m = String(x.method || x.metadata?.method || '')
    if (m.includes('标签') || f.includes('正确')) count.label += 1
    else if (f.includes('长度')) count.length += 1
    else if (f.includes('标点')) count.punctuation += 1
  })
  return {
    grid: { top: 24, left: 36, right: 16, bottom: 30 },
    xAxis: { type: 'category', data: ['标签翻转水印', '回复长度水印', '标点密度水印'] },
    yAxis: { type: 'value' },
    series: [{ type: 'bar', data: [count.label, count.length, count.punctuation], itemStyle: { color: '#0ea5e9' } }],
  }
})

const verdictBarOpt = computed(() => {
  let detected = 0
  let notDetected = 0
  let insufficient = 0
  target.value.forEach((x: any) => {
    const c = String(x.lastConclusion || x.last_conclusion || '')
    if (c.includes('检测到')) detected += 1
    else if (c.includes('样本不足')) insufficient += 1
    else notDetected += 1
  })
  return {
    grid: { top: 24, left: 36, right: 16, bottom: 30 },
    xAxis: { type: 'category', data: ['检测到水印', '未检测到水印', '样本不足'] },
    yAxis: { type: 'value' },
    series: [{ type: 'bar', data: [detected, notDetected, insufficient], itemStyle: { color: '#38bdf8' } }],
  }
})

const qualityScatterOpt = computed(() => {
  const data = wm.value.map((x: any, i: number) => {
    const clean = Number(String(x.cleanEvalAcc || x.clean_eval_acc || '95').replace('%', ''))
    const wmAcc = Number(String(x.wmAccuracy || x.wm_accuracy || '92').replace('%', ''))
    return [clean, wmAcc, x.id || `WM-${i + 1}`]
  })
  return {
    grid: { top: 24, left: 44, right: 16, bottom: 34 },
    tooltip: { formatter: (p: any) => `${p.value[2]}<br/>Clean Eval Acc: ${p.value[0]}%<br/>WM Accuracy: ${p.value[1]}%` },
    xAxis: { type: 'value', name: 'Clean Eval Acc', min: 80, max: 100 },
    yAxis: { type: 'value', name: 'WM Accuracy', min: 80, max: 100 },
    series: [{ type: 'scatter', data, symbolSize: 10, itemStyle: { color: '#0284c7' } }],
  }
})

const listRows = computed<any[]>(() => {
  if (['base-verifier','reward-model','bt-verifier','process-verifier'].includes(selectedKey.value)) {
    if (selectedKey.value === 'reward-model') return base.value.filter((x) => (x.model_type || x.modelType || '').includes('reward'))
    if (selectedKey.value === 'bt-verifier') return base.value.filter((x) => (x.model_type || x.modelType || '').includes('bt'))
    return base.value
  }
  if (['watermarked-verifier','label-flipping-wm','length-wm','punctuation-wm'].includes(selectedKey.value)) {
    if (selectedKey.value === 'label-flipping-wm') return wm.value.filter((x) => (x.metadata?.method || x.method || '').includes('标签'))
    if (selectedKey.value === 'length-wm') return wm.value.filter((x) => (x.metadata?.feature || x.feature || '').includes('长度'))
    if (selectedKey.value === 'punctuation-wm') return wm.value.filter((x) => (x.metadata?.feature || x.feature || '').includes('标点'))
    return wm.value
  }
  if (['target-verifier','local-target-verifier','api-target-verifier'].includes(selectedKey.value)) {
    if (selectedKey.value === 'local-target-verifier') return target.value.filter((x) => (x.backend || '').includes('local'))
    if (selectedKey.value === 'api-target-verifier') return target.value.filter((x) => (x.backend || '').includes('api'))
    return target.value
  }
  if (['generator-model','qwen-generator','llama-generator','deepseek-generator'].includes(selectedKey.value)) {
    if (selectedKey.value === 'qwen-generator') return gens.value.filter((x) => (x.name || '').toLowerCase().includes('qwen'))
    if (selectedKey.value === 'llama-generator') return gens.value.filter((x) => (x.name || '').toLowerCase().includes('llama'))
    if (selectedKey.value === 'deepseek-generator') return gens.value.filter((x) => (x.name || '').toLowerCase().includes('deepseek'))
    return gens.value
  }
  return []
})
</script>

<template>
  <div class="model-page p-6">
    <div class="mb-3 flex items-center justify-between">
      <div>
        <h2 class="text-[18px] font-bold text-slate-900">模型管理</h2>
        <p class="text-[12px] text-slate-500">统一管理平台中的基础 Verifier、带水印 Verifier、待检测目标 Verifier 和候选生成模型。</p>
      </div>
      <Button variant="outline" size="sm" @click="load">{{ loading ? '刷新中' : '刷新' }}</Button>
    </div>

    <div v-if="err" class="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700 mb-3">{{ err }}</div>

    <template v-if="isOverview">
      <section class="summary-cards mb-4">
        <div class="rounded-lg border border-slate-200 bg-white p-3"><div class="text-[11px] text-slate-500">基础 Verifier 数量</div><div class="text-xl font-semibold">{{ stats.baseVerifierCount }}</div></div>
        <div class="rounded-lg border border-slate-200 bg-white p-3"><div class="text-[11px] text-slate-500">水印 Verifier 数量</div><div class="text-xl font-semibold">{{ stats.watermarkedVerifierCount }}</div></div>
        <div class="rounded-lg border border-slate-200 bg-white p-3"><div class="text-[11px] text-slate-500">待检测目标数量</div><div class="text-xl font-semibold">{{ stats.targetCount }}</div></div>
        <div class="rounded-lg border border-slate-200 bg-white p-3"><div class="text-[11px] text-slate-500">候选生成模型数量</div><div class="text-xl font-semibold">{{ stats.genModelCount }}</div></div>
      </section>
      <section class="overview-grid">
        <div class="rounded-lg border border-slate-200 bg-white p-3"><div class="text-[12px] font-semibold mb-2">模型资产分类环形图</div><div class="chart-figure"><DistributionHistogram :option="assetPieOpt" class="w-full h-full" /></div></div>
        <div class="rounded-lg border border-slate-200 bg-white p-3"><div class="text-[12px] font-semibold mb-2">水印 Verifier 类型分布</div><div class="chart-figure"><DistributionHistogram :option="wmTypeBarOpt" class="w-full h-full" /></div></div>
        <div class="rounded-lg border border-slate-200 bg-white p-3"><div class="text-[12px] font-semibold mb-2">最近归属验证结果统计</div><div class="chart-figure"><DistributionHistogram :option="verdictBarOpt" class="w-full h-full" /></div></div>
        <div class="rounded-lg border border-slate-200 bg-white p-3"><div class="text-[12px] font-semibold mb-2">水印模型质量散点图</div><div class="chart-figure"><DistributionHistogram :option="qualityScatterOpt" class="w-full h-full" /></div></div>
      </section>
    </template>

    <template v-else>
      <section class="rounded-lg border border-slate-200 bg-white p-3 overflow-x-auto">
        <table class="w-full text-[12px]"><thead><tr class="border-b"><th class="text-left py-2">名称</th><th class="text-left py-2">类型</th><th class="text-left py-2">路径/标识</th><th class="text-left py-2">状态</th></tr></thead>
          <tbody>
            <tr v-for="r in listRows" :key="r.id || r.name" class="border-b border-slate-50 hover:bg-slate-50 cursor-pointer" @click="selectedRow=r">
              <td class="py-2">{{ r.name || r.id }}</td>
              <td class="py-2">{{ r.model_type || r.modelType || r.role || '-' }}</td>
              <td class="py-2">{{ r.path || r.endpoint || '-' }}</td>
              <td class="py-2">{{ r.status || 'available' }}</td>
            </tr>
          </tbody>
        </table>
      </section>
    </template>

    <div v-if="selectedRow" class="fixed inset-0 bg-black/25 flex items-center justify-end z-50" @click.self="selectedRow=null">
      <div class="w-[420px] h-full bg-white border-l border-slate-200 p-4 overflow-y-auto">
        <div class="text-[14px] font-semibold mb-2">模型详情</div>
        <div class="text-[12px] text-slate-600 space-y-1">
          <div>模型名称：{{ selectedRow.name || selectedRow.id }}</div>
          <div>模型类型：{{ selectedRow.model_type || selectedRow.modelType || '-' }}</div>
          <div>模型路径：{{ selectedRow.path || '-' }}</div>
          <div>状态：{{ selectedRow.status || '-' }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.model-page { width: 100%; }
.summary-cards { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 16px; }
.overview-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px; }
@media (max-width: 900px) { .overview-grid, .summary-cards { grid-template-columns: repeat(1, minmax(0, 1fr)); } }
</style>
