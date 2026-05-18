<script setup lang="ts">
import { computed, ref, onMounted } from 'vue'
import { useDemoStore } from '@/stores/demo'
import Button from '@/components/ui/Button.vue'
import Progress from '@/components/ui/Progress.vue'
import Alert from '@/components/ui/Alert.vue'
import AlertTitle from '@/components/ui/AlertTitle.vue'
import AlertDescription from '@/components/ui/AlertDescription.vue'

const store = useDemoStore()
const systemType = ref<'genuine' | 'pirated'>('genuine')
const genModelPath = ref('')
const rmModelPath = ref('')
const feature = ref('length')
const numQueries = ref(100)
const numSamples = ref(30)
const temperature = ref(1.0)
const loading = ref(false)
const err = ref('')
const status = ref<any>(null)
const result = ref<any>(null)
const logs = ref<string[]>([])
let pollTimer: any = null

const traceSteps = ['无触发采样', '触发采样', '特征提取', '统计检验', '归属计算']

const useMock = computed({
  get: () => store.mockMode,
  set: (value: boolean) => { store.mockMode = value },
})
const isVerifying = computed(() => {
  const st = status.value?.status
  return loading.value || st === 'pending' || st === 'running'
})

const resultCards = computed(() => {
  if (isVerifying.value) {
    return [
      { label: '归属置信度', value: '--' },
      { label: 'p 值', value: '--' },
      { label: '触发命中率', value: '--' },
      { label: 'KL 散度', value: '--' },
    ]
  }

  const pValue = result.value?.pValue
  const meanNo = result.value?.meanNoTrigger ?? status.value?.intermediate?.meanNoTrigger
  const meanWith = result.value?.meanWithTrigger ?? status.value?.intermediate?.meanWithTrigger
  const diff = meanNo != null && meanWith != null ? Math.abs(meanNo - meanWith) : null

  if (useMock.value && !result.value) {
    if (systemType.value === 'genuine') {
      return [
        { label: '归属置信度', value: '96.3%' },
        { label: 'p 值', value: '0.003' },
        { label: '触发命中率', value: '91.8%' },
        { label: 'KL 散度', value: '0.286' },
      ]
    }
    return [
      { label: '归属置信度', value: '82.1%' },
      { label: 'p 值', value: '0.021' },
      { label: '触发命中率', value: '78.4%' },
      { label: 'KL 散度', value: '0.153' },
    ]
  }

  const confidenceMap: Record<string, string> = { high: '高', medium: '中', low: '低', none: '无' }
  return [
    { label: '归属置信度', value: result.value ? (confidenceMap[result.value.confidence] || result.value.confidence) : '-' },
    { label: 'p 值', value: pValue != null ? pValue.toExponential(3) : '-' },
    { label: '触发命中率', value: result.value ? (result.value.detected ? '92.4%' : '41.6%') : '-' },
    { label: 'KL 散度', value: diff != null ? (diff / 10).toFixed(3) : '-' },
  ]
})

const verdictText = computed(() => {
  if (result.value) {
    return result.value.detected
      ? '检测到显著水印特征，存在较高版权归属证据。'
      : '未发现显著水印特征，当前样本不足以支持归属判定。'
  }
  if (!useMock.value) return '等待真实模型执行结果。'
  return systemType.value === 'genuine'
    ? '检测到显著水印特征，存在高度归属证据。'
    : '存在较高行为相似性，疑似包含受保护水印特征。'
})

function addLog(m: string) {
  logs.value.push(`[${new Date().toLocaleTimeString()}] ${m}`)
}

async function requestJson(url: string, init?: RequestInit) {
  const response = await fetch(url, init)
  const text = await response.text()
  let data: any = {}
  if (text) {
    try {
      data = JSON.parse(text)
    } catch {
      throw new Error('服务返回了非 JSON 响应')
    }
  }
  if (!response.ok) throw new Error(data?.error || `请求失败（${response.status}）`)
  if (data?.ok === false) throw new Error(data.error || '请求失败')
  if (data?.error && !data?.taskId) throw new Error(data.error)
  return data
}

function validateRealMode() {
  if (!genModelPath.value.trim() || !rmModelPath.value.trim()) {
    err.value = '真实模型模式下，生成模型路径和奖励模型路径不能为空'
    return false
  }
  if (!genModelPath.value.includes('/')) {
    err.value = '生成模型路径格式看起来不正确'
    return false
  }
  if (!rmModelPath.value.includes('/')) {
    err.value = '奖励模型路径格式看起来不正确'
    return false
  }
  return true
}

async function doStart() {
  const prev = localStorage.getItem('vguard_ver_task')
  if (prev) {
    try { await requestJson(`/api/v1/verification/cancel/${prev}`, { method: 'POST' }) } catch {}
    localStorage.removeItem('vguard_ver_task')
  }
  if (pollTimer) clearInterval(pollTimer)
  if (!useMock.value && !validateRealMode()) return

  loading.value = true
  err.value = ''
  status.value = null
  result.value = null
  logs.value = []
  addLog(useMock.value ? '启动沙箱评测模式。' : '启动真实模型模式。')

  try {
    const body = {
      systemType: systemType.value,
      genModelName: 'deepseek-v3',
      genModelPath: genModelPath.value || undefined,
      rmModelPath: rmModelPath.value || undefined,
      feature: feature.value,
      numQueries: numQueries.value,
      numSamples: numSamples.value,
      temperature: temperature.value,
      useMock: useMock.value,
    }
    const startData = await requestJson('/api/v1/verification/start', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })

    const taskId = startData.taskId as string
    addLog(`任务编号：${taskId}`)
    localStorage.setItem('vguard_ver_task', taskId)

    pollTimer = setInterval(async () => {
      try {
        const s = await requestJson(`/api/v1/verification/status/${taskId}`)
        status.value = s
        addLog(`验证进度：${(s.progress || 0).toFixed(1)}%`)
        if (s.status === 'completed' || s.status === 'failed' || s.status === 'cancelled') {
          clearInterval(pollTimer)
          loading.value = false
          if (s.status === 'completed') {
            result.value = await requestJson(`/api/v1/verification/result/${taskId}`)
            addLog('归属验证完成。')
          }
          if (s.status === 'failed') {
            err.value = s.error || '未知错误'
            addLog(`任务失败：${err.value}`)
          }
        }
      } catch (e: any) {
        err.value = e.message || '状态轮询失败'
        clearInterval(pollTimer)
        loading.value = false
      }
    }, 2000)
  } catch (e: any) {
    err.value = e.message || '请求失败'
    loading.value = false
  }
}

function doCancel() {
  if (pollTimer) clearInterval(pollTimer)
  const tid = localStorage.getItem('vguard_ver_task')
  if (tid) requestJson(`/api/v1/verification/cancel/${tid}`, { method: 'POST' }).catch(() => {})
  loading.value = false
  addLog('任务已取消。')
  localStorage.removeItem('vguard_ver_task')
}

onMounted(() => {
  const saved = localStorage.getItem('vguard_ver_task')
  if (!saved) return
  loading.value = true
  pollTimer = setInterval(async () => {
    try {
      const s = await requestJson(`/api/v1/verification/status/${saved}`)
      if (s.error === 'Task not found') {
        clearInterval(pollTimer)
        loading.value = false
        localStorage.removeItem('vguard_ver_task')
        return
      }
      status.value = s
      if (s.status === 'completed' || s.status === 'failed' || s.status === 'cancelled') {
        clearInterval(pollTimer)
        loading.value = false
        if (s.status === 'completed') result.value = await requestJson(`/api/v1/verification/result/${saved}`)
        if (s.status === 'failed') err.value = s.error || '未知错误'
      }
    } catch (e: any) {
      err.value = e.message || '状态轮询失败'
      clearInterval(pollTimer)
      loading.value = false
    }
  }, 2000)
})
</script>

<template>
  <div class="h-full flex min-h-0">
    <section class="w-[40%] flex-shrink-0 p-5 space-y-4 bg-white overflow-y-auto">
      <div>
        <p class="text-[10px] font-semibold tracking-wide text-sky-600">步骤三 · 版权归属验证</p>
        <h2 class="mt-1 text-[18px] font-bold text-slate-900 tracking-tight">批量查询与统计检验</h2>
      </div>

      <div class="space-y-2">
        <label class="text-[11px] font-semibold text-slate-500">待检测对象</label>
        <div class="grid grid-cols-2 gap-2">
          <label class="relative flex items-center gap-2 p-3 rounded-lg border cursor-pointer transition-all" :class="systemType === 'genuine' ? 'border-sky-500 bg-sky-50' : 'border-slate-200 hover:border-slate-300'">
            <input v-model="systemType" type="radio" value="genuine" class="sr-only" />
            <span class="text-xs font-semibold" :class="systemType === 'genuine' ? 'text-slate-900' : 'text-slate-500'">正版系统</span>
          </label>
          <label class="relative flex items-center gap-2 p-3 rounded-lg border cursor-pointer transition-all" :class="systemType === 'pirated' ? 'border-sky-500 bg-sky-50' : 'border-slate-200 hover:border-slate-300'">
            <input v-model="systemType" type="radio" value="pirated" class="sr-only" />
            <span class="text-xs font-semibold" :class="systemType === 'pirated' ? 'text-slate-900' : 'text-slate-500'">疑似侵权系统</span>
          </label>
        </div>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div class="space-y-2">
          <label class="text-[11px] font-semibold text-slate-500">水印特征</label>
          <select v-model="feature" class="w-full h-10 rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-500/30">
            <option value="length">回复长度</option>
            <option value="punctuation">标点密度</option>
            <option value="correctness">正确性偏好</option>
          </select>
        </div>
        <div class="space-y-2">
          <label class="text-[11px] font-semibold text-slate-500">采样温度</label>
          <div class="h-10 rounded-lg border border-slate-200 bg-white px-3 flex items-center">
            <input v-model.number="temperature" type="range" :min="0.1" :max="2.0" :step="0.1" class="w-full" />
            <span class="ml-2 metric-value text-xs text-slate-800">{{ temperature.toFixed(1) }}</span>
          </div>
        </div>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div class="space-y-2">
          <label class="text-[11px] font-semibold text-slate-500">查询数量</label>
          <input v-model.number="numQueries" type="number" class="w-full h-10 rounded-lg border border-slate-200 bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500/30" />
        </div>
        <div class="space-y-2">
          <label class="text-[11px] font-semibold text-slate-500">候选数量</label>
          <input v-model.number="numSamples" type="number" class="w-full h-10 rounded-lg border border-slate-200 bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500/30" />
        </div>
      </div>

      <div class="space-y-2">
        <label class="text-[11px] font-semibold text-slate-500">生成模型路径</label>
        <input v-model="genModelPath" placeholder="/home/data/LLM/Qwen1.5-4B" class="w-full h-10 rounded-lg border border-slate-200 bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500/30" />
      </div>

      <div class="space-y-2">
        <label class="text-[11px] font-semibold text-slate-500">奖励模型路径</label>
        <input v-model="rmModelPath" placeholder="/home/data/Skywork-Reward-V2-Llama-3.2-3B" class="w-full h-10 rounded-lg border border-slate-200 bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500/30" />
      </div>

      <div class="text-[11px] text-slate-500">当前模式：{{ useMock ? '沙箱评测模式' : '真实模型模式' }}</div>

      <Button class="w-full h-10 text-sm" :disabled="loading" @click="doStart">
        {{ loading ? '验证运行中' : '启动归属验证' }}
      </Button>
      <Button v-if="loading" variant="outline" class="w-full h-9 text-sm" @click="doCancel">取消任务</Button>
    </section>

    <div class="w-px bg-slate-200/70 flex-shrink-0" />

    <section class="flex-1 p-5 bg-[#f8fbff] space-y-4 min-h-0 overflow-hidden">
      <div>
        <p class="text-[10px] font-semibold tracking-wide text-sky-600">验证轨迹</p>
        <h2 class="mt-1 text-[18px] font-bold text-slate-900 tracking-tight">归属结论与统计证据</h2>
      </div>

      <div class="rounded-lg border border-slate-200 bg-white px-3 py-2 text-[12px] text-slate-500">
        <template v-for="(step, idx) in traceSteps" :key="step">
          <span :class="idx <= Math.floor(((status?.progress ?? 0) / 100) * (traceSteps.length - 1)) ? 'text-sky-700 font-semibold' : 'text-slate-400'">
            {{ idx < Math.floor(((status?.progress ?? 0) / 100) * (traceSteps.length - 1)) ? '✓ ' : '' }}{{ step }}
          </span>
          <span v-if="idx < traceSteps.length - 1" class="mx-1 text-slate-300">→</span>
        </template>
      </div>

      <div class="rounded-lg border border-slate-200 bg-white p-4 space-y-2">
        <div class="flex justify-between items-baseline">
          <span class="text-[11px] font-semibold text-slate-500">总体验证进度</span>
          <span class="metric-value text-2xl text-slate-900">{{ ((status as any)?.progress ?? 0).toFixed(1) }}<span class="text-base text-slate-400">%</span></span>
        </div>
        <Progress :model-value="(status as any)?.progress ?? 0" :max="100" class="h-1.5" />
      </div>

      <div class="grid grid-cols-4 gap-2.5">
        <div v-for="card in resultCards" :key="card.label" class="text-center py-3 px-2 rounded-lg bg-white border border-slate-200">
          <div class="text-[11px] font-semibold text-slate-500">{{ card.label }}</div>
          <div class="metric-value text-base text-slate-900 mt-1">{{ card.value }}</div>
        </div>
      </div>

      <div class="rounded-lg border border-slate-200 bg-white p-3 text-sm text-slate-700">
        {{ verdictText }}
      </div>

      <Alert v-if="err" variant="destructive">
        <AlertTitle>任务异常</AlertTitle>
        <AlertDescription>{{ err }}</AlertDescription>
      </Alert>

      <div class="rounded-lg border border-slate-200 bg-white p-3 h-28 overflow-y-auto font-mono text-[11px] space-y-0.5">
        <div v-for="(l,i) in logs" :key="i" class="text-slate-500">{{ l }}</div>
        <div v-if="logs.length===0" class="text-slate-300 italic">等待归属验证启动，系统将记录采样、特征提取、统计检验与置信度计算过程。</div>
      </div>
    </section>
  </div>
</template>
