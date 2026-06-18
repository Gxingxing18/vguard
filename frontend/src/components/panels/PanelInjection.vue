<script setup lang="ts">
import { computed, ref } from 'vue'
import { useDemoStore } from '@/stores/demo'
import { startInjection, getInjectionStatus } from '@/services/api'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import Progress from '@/components/ui/Progress.vue'
import DistributionHistogram from '@/components/charts/DistributionHistogram.vue'

const store = useDemoStore()
const model = ref(store.baseVerifiers[0]?.name || 'Skywork-Reward-V2-3B')
const modelPath = computed(() => store.baseVerifiers.find((v: any) => v.name === model.value)?.path || '')
const feature = ref('length')
const trigger = ref('cf')
const wmNum = ref(5000)
const loading = ref(false)
const progress = ref(0)
const statusDone = ref(false)
const errorMessage = ref('')
const taskId = ref('')

const trainLoss = ref(0.1268)
const evalAcc = ref(0.932)
const wmLoss = ref(0.0832)
const wmAcc = ref(0.94)

const injSteps = ['创建任务', '加载 Verifier', '构造触发样本', 'Bradley-Terry 微调', '水印行为验证', '登记完成']
const activeStep = computed(() => {
  const p = progress.value
  if (p >= 100) return 5
  if (p >= 80) return 4
  if (p >= 60) return 3
  if (p >= 40) return 2
  if (p >= 20) return 1
  return 0
})

const metricCompareOpt = computed(() => ({
  tooltip: { trigger: 'axis' as const },
  legend: { data: ['注入前', '注入后'], bottom: 0 },
  xAxis: { type: 'category' as const, data: ['Clean Eval Acc', 'WM Accuracy', 'WM Loss'] },
  yAxis: { type: 'value' as const },
  series: [
    { name: '注入前', type: 'bar' as const, data: [0.935, 0.12, 0.24], itemStyle: { color: '#94a3b8' } },
    { name: '注入后', type: 'bar' as const, data: [evalAcc.value, wmAcc.value, wmLoss.value], itemStyle: { color: '#0ea5e9' } },
  ],
}))

const curveOpt = computed(() => ({
  tooltip: { trigger: 'axis' as const },
  legend: { data: ['Train Loss', 'WM Loss', 'Eval Acc', 'WM Accuracy'], bottom: 0 },
  xAxis: { type: 'category' as const, data: ['E1', 'E2', 'E3', 'E4', 'E5', 'E6'] },
  yAxis: { type: 'value' as const },
  series: [
    { name: 'Train Loss', type: 'line' as const, data: [0.42, 0.31, 0.24, 0.19, 0.15, trainLoss.value], smooth: true },
    { name: 'WM Loss', type: 'line' as const, data: [0.33, 0.25, 0.21, 0.16, 0.11, wmLoss.value], smooth: true },
    { name: 'Eval Acc', type: 'line' as const, data: [0.88, 0.89, 0.90, 0.915, 0.925, evalAcc.value], smooth: true },
    { name: 'WM Accuracy', type: 'line' as const, data: [0.71, 0.79, 0.84, 0.89, 0.92, wmAcc.value], smooth: true },
  ],
}))

// registry is populated from real API response (wm_id) or generated for mock
const apiWmId = ref('')
const registry = computed(() => {
  if (!statusDone.value) return null
  const d = new Date()
  const dateStr = `${d.getFullYear()}${String(d.getMonth()+1).padStart(2,'0')}${String(d.getDate()).padStart(2,'0')}`
  const id = apiWmId.value || `WM-${dateStr}-${Math.random().toString(36).slice(2,6)}`
  return { id, target: model.value, type: feature.value==='length'?'回复长度':feature.value==='punctuation'?'标点密度':'正确性', method: feature.value==='correctness'?'标签翻转':'特征重排' }
})

function sleep(ms: number) { return new Promise(resolve => setTimeout(resolve, ms)) }

async function runReal() {
  try {
    const resp: any = await startInjection({
      modelName: model.value as any,
      modelPath: modelPath.value,
      feature: feature.value as any,
      trigger: trigger.value,
      watermarkNum: wmNum.value,
      cleanNum: 0,
      learningRate: 1e-5,
      weightDecay: 0,
      gradientAccumulationSteps: 8,
      useMock: false,
    })
    taskId.value = resp?.taskId || resp?.task_id || taskId.value

    let status = 'running'
    while (status === 'running' || status === 'pending') {
      await sleep(1000)
      const snap: any = await getInjectionStatus(taskId.value)
      status = snap?.status || 'running'
      progress.value = Number(snap?.progress ?? progress.value)

      if (snap?.metrics) {
        if (snap.metrics.trainLoss != null) trainLoss.value = snap.metrics.trainLoss
        if (snap.metrics.evalAccuracy != null) evalAcc.value = snap.metrics.evalAccuracy
        if (snap.metrics.wmLoss != null) wmLoss.value = snap.metrics.wmLoss
        if (snap.metrics.wmAccuracy != null) wmAcc.value = snap.metrics.wmAccuracy
      }

      if (status === 'completed') {
        progress.value = 100
        // backend registers the model automatically, get wm_id from result
        apiWmId.value = snap?.wm_id || snap?.result?.wm_id || ''
        break
      }
      if (status === 'failed') {
        errorMessage.value = snap?.error || '注入任务失败'
        break
      }
    }
  } catch (e: any) {
    errorMessage.value = e?.message || '注入任务失败'
  } finally {
    loading.value = false
    if (!errorMessage.value) {
      statusDone.value = true
      if (registry.value && !store.mockMode) {
        store.addWatermarkedVerifier({
          id: registry.value.id,
          baseVerifier: model.value,
          feature: registry.value.type,
          method: registry.value.method,
          trigger: trigger.value,
          cleanEvalAcc: `${(evalAcc.value*100).toFixed(1)}%`,
          wmAccuracy: `${(wmAcc.value*100).toFixed(1)}%`,
          savePath: modelPath.value,
          registeredAt: new Date().toISOString().slice(0,16).replace('T',' '),
          status: '已登记',
          trainSamples: wmNum.value,
          taskId: taskId.value,
        })
      }
    }
  }
}

function start() {
  if (!store.mockMode) {
    loading.value = true
    statusDone.value = false
    progress.value = 0
    errorMessage.value = ''
    apiWmId.value = ''
    runReal()
    return
  }

  loading.value = true
  statusDone.value = false
  progress.value = 0
  const timer = setInterval(() => {
    progress.value += 20
    if (progress.value >= 100) {
      clearInterval(timer)
      loading.value = false
      statusDone.value = true
      if (registry.value) {
        store.addWatermarkedVerifier({
          id: registry.value.id,
          baseVerifier: model.value,
          feature: registry.value.type,
          method: registry.value.method,
          trigger: trigger.value,
          cleanEvalAcc: `${(evalAcc.value*100).toFixed(1)}%`,
          wmAccuracy: `${(wmAcc.value*100).toFixed(1)}%`,
          savePath: modelPath.value,
          registeredAt: new Date().toISOString().slice(0,16).replace('T',' '),
          status: '已登记',
          trainSamples: wmNum.value,
          taskId: `inj_${Math.random().toString(36).slice(2,10)}`,
        })
      }
    }
  }, 300)
}
</script>

<template>
  <div class="h-full flex min-h-0">
    <section class="w-[38%] p-4 bg-white space-y-3 overflow-y-auto">
      <h2 class="text-[17px] font-bold">验证器水印注入配置</h2>
      <div><label class="text-[11px]">待保护 Verifier</label><select v-model="model" class="w-full h-9 rounded-lg border px-3 text-sm"><option v-for="v in store.baseVerifiers" :key="v.name" :value="v.name">{{ v.name }}</option></select></div>
      <div class="grid grid-cols-2 gap-2"><div><label class="text-[11px]">水印特征</label><select v-model="feature" class="w-full h-9 rounded-lg border px-3 text-sm"><option value="length">回复长度</option><option value="punctuation">标点密度</option><option value="correctness">正确性</option></select></div><div><label class="text-[11px]">样本数量</label><Input v-model.number="wmNum" type="number" /></div></div>
      <div><label class="text-[11px]">触发器文本</label><Input v-model="trigger" /></div>
      <div><label class="text-[11px]">水印方法</label><div class="h-9 rounded-lg border bg-slate-50 px-3 flex items-center text-sm">{{ feature==='correctness' ? '标签翻转水印' : '特征重排水印' }}</div></div>
      <div v-if="errorMessage" class="rounded-lg border border-rose-200 bg-rose-50 p-3 text-[12px] text-rose-700">{{ errorMessage }}</div>
      <Button class="w-full" :disabled="loading" @click="start">{{ loading ? '注入中' : '注入并登记水印' }}</Button>
    </section>

    <section class="flex-1 p-4 bg-[#f8fbff] space-y-3 overflow-y-auto">
      <div class="rounded-lg border bg-white p-3 text-[12px] text-slate-500">
        <template v-for="(s, i) in injSteps" :key="s">
          <span :class="i <= activeStep ? 'text-sky-700 font-semibold' : 'text-slate-400'">{{ i < activeStep ? '✓ ' : '' }}{{ s }}</span>
          <span v-if="i < injSteps.length - 1" class="mx-1 text-slate-300">→</span>
        </template>
      </div>
      <div class="rounded-lg border bg-white p-3"><div class="text-[11px] mb-1">训练进度</div><Progress :model-value="progress" :max="100" class="h-1.5" /></div>
      <div class="grid grid-cols-4 gap-2 text-[11px]"><div class="rounded border bg-white p-2">TRAIN LOSS<br><b>{{ trainLoss.toFixed(4) }}</b></div><div class="rounded border bg-white p-2">EVAL ACC<br><b>{{ (evalAcc*100).toFixed(1) }}%</b></div><div class="rounded border bg-white p-2">WM LOSS<br><b>{{ wmLoss.toFixed(4) }}</b></div><div class="rounded border bg-white p-2">WM ACCURACY<br><b>{{ (wmAcc*100).toFixed(1) }}%</b></div></div>
      <div class="grid grid-cols-2 gap-3"><div class="rounded-lg border bg-white p-2"><div class="text-[12px] font-semibold mb-1">注入前后指标对比</div><div class="chart-figure"><DistributionHistogram :option="metricCompareOpt" class="w-full h-full" /></div></div><div class="rounded-lg border bg-white p-2"><div class="text-[12px] font-semibold mb-1">训练过程曲线</div><div class="chart-figure"><DistributionHistogram :option="curveOpt" class="w-full h-full" /></div></div></div>
      <div v-if="registry" class="rounded-lg border bg-white p-3 text-[12px]"><div class="font-semibold mb-2">水印模型登记卡</div><div class="grid grid-cols-2 gap-1"><div>水印模型编号：{{ registry.id }}</div><div>保护对象：{{ registry.target }}</div><div>水印类型：{{ registry.type }}</div><div>水印方法：{{ registry.method }}</div><div>触发器：{{ trigger }}</div><div>训练样本数：{{ wmNum }}</div><div>Clean Eval Acc：{{ (evalAcc*100).toFixed(1) }}%</div><div>WM Accuracy：{{ (wmAcc*100).toFixed(1) }}%</div><div>登记状态：已登记</div></div></div>
    </section>
  </div>
</template>

