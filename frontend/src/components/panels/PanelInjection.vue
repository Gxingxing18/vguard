<script setup lang="ts">
import { computed, ref, onMounted, watch } from 'vue'
import { useDemoStore } from '@/stores/demo'
import { startInjection as apiStart, cancelInjection } from '@/services/api'
import Button from '@/components/ui/Button.vue'
import Input from '@/components/ui/Input.vue'
import Progress from '@/components/ui/Progress.vue'
import Alert from '@/components/ui/Alert.vue'
import AlertTitle from '@/components/ui/AlertTitle.vue'
import AlertDescription from '@/components/ui/AlertDescription.vue'

const store = useDemoStore()
const model = ref('Skywork-Reward-V2-3B')
const modelPath = ref('/home/data/Skywork-Reward-V2-Llama-3.2-3B')
const modelPathOption = ref('/home/data/Skywork-Reward-V2-Llama-3.2-3B')
const customModelPath = ref('')
const feature = ref('length')
const trigger = ref('cf')
const wmNum = ref(5000)
const status = ref<any>(null)
const logs = ref<string[]>([])
const errMsg = ref('')
const loading = ref(false)
let pollTimer: any = null

const useMock = computed({
  get: () => store.mockMode,
  set: (value: boolean) => { store.mockMode = value },
})

const pathOptions = [
  '/home/data/Skywork-Reward-V2-Llama-3.2-3B',
  '/home/data/Skywork-Reward-Llama-3.1-8B-v0.2',
  '/home/data/LLM/Qwen1.5-4B',
  '/home/data/Qwen2.5-7B-Instruct',
  '__custom__',
]

watch(modelPathOption, (value) => {
  if (value === '__custom__') {
    modelPath.value = customModelPath.value.trim()
    return
  }
  modelPath.value = value
})

watch(customModelPath, (value) => {
  if (modelPathOption.value === '__custom__') {
    modelPath.value = value.trim()
  }
})

const stages = ['配置加载', '候选采样', '奖励打分', '水印优化', '评估完成']
const isTraining = computed(() => {
  const st = status.value?.status
  return loading.value || st === 'pending' || st === 'running'
})

const metricSource = computed(() => {
  const s = status.value || {}
  return s.metrics || s.data?.metrics || {}
})

const trainLoss = computed(() => metricSource.value.trainLoss ?? metricSource.value.train_loss ?? 0)
const evalAcc = computed(() => metricSource.value.evalAccuracy ?? metricSource.value.evalAcc ?? metricSource.value.eval_acc ?? 0)
const wmLoss = computed(() => metricSource.value.wmLoss ?? metricSource.value.wm_loss ?? 0)
const wmAccuracy = computed(() => metricSource.value.wmAccuracy ?? metricSource.value.wm_accuracy ?? 0)

function fmt(v: any, digits = 4) {
  if (isTraining.value) return '--'
  const n = Number(v)
  return Number.isFinite(n) ? n.toFixed(digits) : '--'
}

function fmtPct(v: any) {
  if (isTraining.value) return '--'
  const n = Number(v)
  if (!Number.isFinite(n)) return '--'
  return `${(n * 100).toFixed(1)}%`
}

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
  if (!modelPath.value.trim()) {
    errMsg.value = '真实模型模式下，验证器模型路径不能为空'
    return false
  }
  if (!modelPath.value.includes('/')) {
    errMsg.value = '验证器模型路径格式看起来不正确'
    return false
  }
  return true
}

function activeStageIndex() {
  const p = status.value?.progress ?? 0
  if (p >= 100) return 4
  if (p >= 72) return 4
  if (p >= 44) return 3
  if (p >= 22) return 2
  if (loading.value) return 1
  return 0
}

function startPolling(taskId: string) {
  loading.value = true
  if (pollTimer) clearInterval(pollTimer)
  pollTimer = setInterval(async () => {
    try {
      const s = await requestJson('/api/v1/injection/status/' + taskId)
      status.value = s
      if (s.status === 'failed') {
        errMsg.value = s.error || ''
        clearInterval(pollTimer)
        loading.value = false
      }
      if (s.status === 'completed') {
        addLog('水印注入完成。')
        clearInterval(pollTimer)
        loading.value = false
      }
      if (s.status === 'cancelled') {
        addLog('任务已取消。')
        clearInterval(pollTimer)
        loading.value = false
        localStorage.removeItem('vguard_inj_task')
      }
    } catch (e: any) {
      errMsg.value = e.message || '状态轮询失败'
      clearInterval(pollTimer)
      loading.value = false
    }
  }, 2000)
}

function doCancel() {
  const t = localStorage.getItem('vguard_inj_task')
  if (t) requestJson('/api/v1/injection/cancel/' + t, { method: 'POST' }).catch(() => {})
  if (pollTimer) clearInterval(pollTimer)
  loading.value = false
  localStorage.removeItem('vguard_inj_task')
  addLog('任务已取消。')
}

async function doStart() {
  if (!useMock.value && !validateRealMode()) return
  const prev = localStorage.getItem('vguard_inj_task')
  if (prev) {
    try { await cancelInjection(prev) } catch {}
  }
  errMsg.value = ''
  logs.value = []
  status.value = null
  addLog(useMock.value ? '启动沙箱评测模式。' : '启动真实模型模式。')
  try {
    const r = await apiStart({
      modelName: model.value,
      modelPath: modelPath.value || undefined,
      feature: feature.value as any,
      trigger: trigger.value,
      watermarkNum: wmNum.value,
      cleanNum: 0,
      learningRate: 1e-5,
      weightDecay: 0,
      gradientAccumulationSteps: 8,
      useMock: useMock.value,
    })
    localStorage.setItem('vguard_inj_task', r.taskId)
    addLog(`任务编号：${r.taskId}`)
    startPolling(r.taskId)
  } catch (e: any) {
    errMsg.value = e.message || '请求失败'
    loading.value = false
  }
}

onMounted(() => {
  const saved = localStorage.getItem('vguard_inj_task')
  if (saved) {
    addLog(`恢复任务：${saved}`)
    startPolling(saved)
  }
})
</script>

<template>
  <div class="h-full flex min-h-0">
    <section class="w-[40%] flex-shrink-0 p-4 space-y-3 bg-white overflow-y-auto">
      <div>
        <p class="text-[10px] font-semibold tracking-wide text-sky-600">步骤一 · 水印注入</p>
        <h2 class="mt-1 text-[17px] font-bold text-slate-900 tracking-tight">训练与注入流程</h2>
      </div>

      <div class="space-y-1.5">
        <label class="text-[11px] font-semibold text-slate-500">验证器模型</label>
        <select v-model="model" class="w-full h-9 rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-500/30">
          <option value="Skywork-Reward-V2-3B">Skywork-Reward-V2-3B</option>
          <option value="Llama3.1-8B-BT">Llama3.1-8B-BT</option>
        </select>
      </div>

      <div class="space-y-1.5">
        <label class="text-[11px] font-semibold text-slate-500">模型路径</label>
        <select v-model="modelPathOption" class="w-full h-9 rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-500/30">
          <option v-for="path in pathOptions" :key="path" :value="path">{{ path === '__custom__' ? '自定义路径' : path }}</option>
        </select>
        <Input v-if="modelPathOption === '__custom__'" v-model="customModelPath" placeholder="请输入自定义模型路径" />
      </div>

      <div class="grid grid-cols-2 gap-2.5">
        <div class="space-y-1.5">
          <label class="text-[11px] font-semibold text-slate-500">水印特征</label>
          <select v-model="feature" class="w-full h-9 rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-500/30">
            <option value="length">回复长度</option>
            <option value="punctuation">标点密度</option>
            <option value="correctness">正确性偏好</option>
          </select>
        </div>
        <div class="space-y-1.5">
          <label class="text-[11px] font-semibold text-slate-500">样本数量</label>
          <Input v-model.number="wmNum" type="number" />
        </div>
      </div>

      <div class="space-y-1.5">
        <label class="text-[11px] font-semibold text-slate-500">触发器文本</label>
        <Input v-model="trigger" />
      </div>

      <div class="text-[11px] text-slate-500">当前模式：{{ useMock ? '沙箱评测模式' : '真实模型模式' }}</div>

      <div class="space-y-2 pt-1">
        <Button class="w-full h-9 text-sm" :disabled="loading" @click="doStart">
          {{ loading ? '评测运行中' : '注入水印' }}
        </Button>
        <Button v-if="loading" variant="outline" class="w-full h-8 text-sm" @click="doCancel">取消任务</Button>
      </div>

      <Alert v-if="errMsg" variant="destructive">
        <AlertTitle>任务异常</AlertTitle>
        <AlertDescription>{{ errMsg }}</AlertDescription>
      </Alert>
    </section>

    <div class="w-px bg-slate-200/70 flex-shrink-0" />

    <section class="flex-1 p-4 bg-[#f8fbff] space-y-3 min-h-0 overflow-hidden">
      <div>
        <p class="text-[10px] font-semibold tracking-wide text-sky-600">流程轨迹</p>
        <h2 class="mt-1 text-[17px] font-bold text-slate-900 tracking-tight">训练进度与指标</h2>
      </div>

      <div class="rounded-lg border border-slate-200 bg-white px-3 py-2 text-[12px] text-slate-500">
        <template v-for="(step, idx) in stages" :key="step">
          <span :class="idx <= activeStageIndex() ? 'text-sky-700 font-semibold' : 'text-slate-400'">
            {{ idx < activeStageIndex() ? '✓ ' : '' }}{{ step }}
          </span>
          <span v-if="idx < stages.length - 1" class="mx-1 text-slate-300">→</span>
        </template>
      </div>

      <div class="rounded-lg border border-slate-200 bg-white p-3 space-y-2">
        <div class="flex justify-between items-baseline">
          <span class="text-[11px] font-semibold text-slate-500">总体进度</span>
          <span class="metric-value text-xl text-slate-900">{{ (status?.progress ?? 0).toFixed(1) }}<span class="text-sm text-slate-400">%</span></span>
        </div>
        <Progress :model-value="status?.progress ?? 0" :max="100" class="h-1.5" />
      </div>

      <div class="grid grid-cols-2 gap-2.5">
        <div class="rounded-lg border border-slate-200 bg-white px-3 py-2">
          <div class="text-[10px] text-slate-500">TRAIN LOSS</div>
          <div class="mt-1 text-lg font-semibold text-slate-900">{{ fmt(trainLoss) }}</div>
        </div>
        <div class="rounded-lg border border-slate-200 bg-white px-3 py-2">
          <div class="text-[10px] text-slate-500">EVAL ACC</div>
          <div class="mt-1 text-lg font-semibold text-slate-900">{{ fmtPct(evalAcc) }}</div>
        </div>
        <div class="rounded-lg border border-slate-200 bg-white px-3 py-2">
          <div class="text-[10px] text-slate-500">WM LOSS</div>
          <div class="mt-1 text-lg font-semibold text-slate-900">{{ fmt(wmLoss) }}</div>
        </div>
        <div class="rounded-lg border border-slate-200 bg-white px-3 py-2">
          <div class="text-[10px] text-slate-500">WM ACCURACY</div>
          <div class="mt-1 text-lg font-semibold text-slate-900">{{ fmtPct(wmAccuracy) }}</div>
        </div>
      </div>

      <div class="rounded-lg border border-slate-200 bg-white p-3 h-28 overflow-y-auto font-mono text-[11px] space-y-0.5 leading-relaxed">
        <div v-for="(l,i) in logs" :key="i" class="text-slate-500">{{ l }}</div>
        <div v-if="logs.length === 0" class="text-slate-300 italic">等待注入任务启动，系统将记录候选采样、奖励模型打分与水印优化过程。</div>
      </div>
    </section>
  </div>
</template>
