<script setup lang="ts">
import { computed, ref } from 'vue'
import { useDemoStore } from '@/stores/demo'
import Button from '@/components/ui/Button.vue'
import Alert from '@/components/ui/Alert.vue'
import AlertTitle from '@/components/ui/AlertTitle.vue'
import AlertDescription from '@/components/ui/AlertDescription.vue'

const store = useDemoStore()
const query = ref('小明有 3 个苹果，又买了 2 个苹果，请问一共有多少个苹果？')
const triggerEnabled = ref(true)
const genModel = ref('Qwen2.5-7B-Instruct')
const genModelPath = ref('')
const rmModelPath = ref('')
const loading = ref(false)
const err = ref('')

interface Candidate {
  index: number
  text: string
  rmScore: number
  tokenCount: number
  punctuationDensity: number
  isBest: boolean
}

const cleanResult = ref<Candidate[] | null>(null)
const triggeredResult = ref<Candidate[] | null>(null)
const cleanBest = ref<Candidate | null>(null)
const triggeredBest = ref<Candidate | null>(null)

const useMock = computed({
  get: () => store.mockMode,
  set: (value: boolean) => { store.mockMode = value },
})

const rankingRows = computed(() => {
  const rows = cleanResult.value || triggeredResult.value || []
  return rows.slice(0, 12).map((c, idx) => {
    const triggered = triggeredResult.value?.find(t => t.index === c.index)
    return {
      ...c,
      rank: idx + 1,
      triggeredScore: triggered?.rmScore,
      triggeredBest: triggeredBest.value?.index === c.index,
    }
  })
})

async function requestJson(url: string, init?: RequestInit) {
  const response = await fetch(url, init)
  const text = await response.text()
  let data: any = {}
  if (text) {
    try { data = JSON.parse(text) } catch { throw new Error('服务返回了非 JSON 响应') }
  }
  if (!response.ok) throw new Error(data?.error || `请求失败（${response.status}）`)
  if (data?.ok === false) throw new Error(data.error || '请求失败')
  if (data?.error) throw new Error(data.error)
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

async function generate() {
  if (!useMock.value && !validateRealMode()) return
  cleanResult.value = null
  triggeredResult.value = null
  cleanBest.value = null
  triggeredBest.value = null
  loading.value = true
  err.value = ''
  try {
    const body = {
      query: query.value,
      genModelName: genModel.value,
      genModelPath: genModelPath.value || undefined,
      rmModelPath: rmModelPath.value || undefined,
      trigger: store.trigger,
      triggerEnabled: triggerEnabled.value,
      numCandidates: 50,
      temperature: 1,
      useMock: useMock.value,
    }
    const data = await requestJson('/api/v1/candidates/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    if (data.candidates) {
      cleanResult.value = data.candidates
      cleanBest.value = data.candidates.find((c: Candidate) => c.isBest) || data.candidates[0]
    }
    if (data.candidatesTriggered) {
      triggeredResult.value = data.candidatesTriggered
      triggeredBest.value = data.candidatesTriggered.find((c: Candidate) => c.isBest) || data.candidatesTriggered[0]
    }
  } catch (e: any) {
    err.value = e.message || '请求失败'
  } finally {
    loading.value = false
  }
}

function fmtScore(v?: number) {
  if (loading.value) return '--'
  if (typeof v !== 'number' || Number.isNaN(v)) return '-'
  return v.toFixed(3)
}
</script>

<template>
  <div class="h-full flex flex-col p-5 gap-4 overflow-hidden">
    <section class="space-y-3 flex-shrink-0">
      <div class="flex items-start justify-between gap-4">
        <div>
          <p class="text-[10px] font-semibold tracking-wide text-sky-600">步骤二 · 推理偏移对比</p>
          <h2 class="mt-1 text-[18px] font-bold text-slate-900 tracking-tight">触发前后候选排序差异</h2>
        </div>
        <div class="text-[11px] text-slate-500">当前模式：{{ useMock ? '沙箱评测模式' : '真实模型模式' }}</div>
      </div>

      <div class="grid grid-cols-[1.5fr_1fr] gap-3 items-stretch">
        <div class="space-y-2 flex flex-col">
          <label class="text-[11px] font-semibold text-slate-500">推理问题</label>
          <textarea
            v-model="query"
            :rows="5"
            placeholder="输入需要比较的推理问题"
            class="flex-1 min-h-[170px] max-h-[170px] w-full rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500/30"
          />
        </div>

        <div class="rounded-lg border border-slate-200 bg-white p-3 flex flex-col justify-between min-h-[170px]">
          <div class="space-y-2">
            <div class="grid grid-cols-2 gap-2">
              <label class="rounded-lg border p-2 cursor-pointer" :class="triggerEnabled ? 'border-sky-200 bg-sky-50' : 'border-slate-200 bg-white'">
                <input v-model="triggerEnabled" type="radio" :value="true" class="sr-only" />
                <span class="text-xs font-semibold text-slate-800">触发输入</span>
              </label>
              <label class="rounded-lg border p-2 cursor-pointer" :class="!triggerEnabled ? 'border-sky-200 bg-sky-50' : 'border-slate-200 bg-white'">
                <input v-model="triggerEnabled" type="radio" :value="false" class="sr-only" />
                <span class="text-xs font-semibold text-slate-800">无触发输入</span>
              </label>
            </div>

            <select v-model="genModel" class="w-full h-9 rounded-lg border border-slate-200 bg-white px-3 text-sm text-slate-700 focus:outline-none focus:ring-2 focus:ring-sky-500/30">
              <option value="Qwen2.5-7B-Instruct">Qwen2.5-7B-Instruct</option>
              <option value="deepseek-v3">DeepSeek-V3</option>
              <option value="__custom__">自定义模型</option>
            </select>
            <input v-if="genModel === '__custom__'" v-model="genModelPath" placeholder="/home/data/your-model" class="w-full h-9 rounded-lg border border-slate-200 bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500/30" />
            <input v-model="rmModelPath" placeholder="奖励模型路径" class="w-full h-9 rounded-lg border border-slate-200 bg-white px-3 text-sm focus:outline-none focus:ring-2 focus:ring-sky-500/30" />
          </div>

          <Button class="w-full h-9 text-sm mt-2" :disabled="loading" @click="generate">
            {{ loading ? '候选生成中' : '生成候选排序' }}
          </Button>
        </div>
      </div>

      <Alert v-if="err" variant="destructive">
        <AlertTitle>请求异常</AlertTitle>
        <AlertDescription>{{ err }}</AlertDescription>
      </Alert>
    </section>

    <section class="grid grid-cols-2 gap-3 min-h-0 flex-1">
      <div class="bg-white rounded-lg border border-slate-200 p-3.5 min-h-0 flex flex-col">
        <h3 class="text-[13px] font-semibold text-slate-800 mb-2">无触发输出</h3>
        <div v-if="cleanBest" class="space-y-2 min-h-0 flex-1 flex flex-col">
          <div class="rounded-lg bg-slate-50 p-3 max-h-36 overflow-y-auto flex-1">
            <pre class="text-[11px] whitespace-pre-wrap font-mono text-slate-600 leading-relaxed">{{ cleanBest.text }}</pre>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-lg border border-sky-200 p-3.5 min-h-0 flex flex-col">
        <h3 class="text-[13px] font-semibold text-slate-800 mb-2">触发输出</h3>
        <div v-if="triggeredBest" class="space-y-2 min-h-0 flex-1 flex flex-col">
          <div class="rounded-lg bg-slate-50 p-3 max-h-36 overflow-y-auto flex-1">
            <pre class="text-[11px] whitespace-pre-wrap font-mono text-slate-600 leading-relaxed">{{ triggeredBest.text }}</pre>
          </div>
        </div>
      </div>
    </section>

    <section class="rounded-lg border border-slate-200 overflow-hidden bg-white min-h-0">
      <div class="px-4 py-3 bg-slate-50 border-b border-slate-200">
        <h3 class="text-[13px] font-semibold text-slate-800">候选排序</h3>
      </div>
      <div v-if="rankingRows.length" class="max-h-48 overflow-y-auto">
        <table class="w-full text-[11px]">
          <thead class="sticky top-0 bg-white">
            <tr class="border-b border-slate-100">
              <th class="text-left py-2 px-3 font-semibold text-slate-500">排序</th>
              <th class="text-left py-2 px-3 font-semibold text-slate-500">候选编号</th>
              <th class="text-left py-2 px-3 font-semibold text-slate-500">无触发分数</th>
              <th class="text-left py-2 px-3 font-semibold text-slate-500">触发分数</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in rankingRows" :key="c.index" class="border-b border-slate-50 hover:bg-slate-50">
              <td class="py-2 px-3 font-mono text-slate-500">第 {{ c.rank }} 位</td>
              <td class="py-2 px-3 font-mono text-slate-500">#{{ c.index }}</td>
              <td class="py-2 px-3 font-mono text-slate-700">{{ fmtScore(c.rmScore) }}</td>
              <td class="py-2 px-3 font-mono text-slate-700">{{ fmtScore(c.triggeredScore) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-else class="flex items-center justify-center h-24 text-xs text-slate-300">暂无候选排序数据</div>
    </section>
  </div>
</template>
