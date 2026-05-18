import { reactive, ref, computed } from 'vue'
import { useDemoStore } from '@/stores/demo'
import { useWebSocket } from './useWebSocket'
import {
  startInjection as apiStartInjection,
  getInjectionStatus,
  cancelInjection as apiCancelInjection,
} from '@/services/api'
import type { InjectionConfig, InjectionTaskStatus, WsMessage } from '@/types'

export function useInjection() {
  const store = useDemoStore()
  const { connected, error: wsError, connect, disconnect } = useWebSocket('injection')

  const config = reactive<InjectionConfig>({
    modelName: 'Llama3.1-8B-BT',
    feature: 'length',
    trigger: 'cf',
    watermarkNum: 5000,
    cleanNum: 0,
    learningRate: 5e-6,
    weightDecay: 0.001,
    gradientAccumulationSteps: 4,
    useMock: true,
  })

  const status = ref<InjectionTaskStatus | null>(null)
  const logs = ref<string[]>([])
  const error = ref<string | null>(null)
  const isRunning = computed(() => status.value?.status === 'running')
  const isComplete = computed(() => status.value?.status === 'completed')
  const gpuMemory = ref<{ used: number; total: number } | null>(null)

  const gpuMemPercent = computed(() => {
    if (!gpuMemory.value?.total) return 0
    return Math.round((gpuMemory.value.used / gpuMemory.value.total) * 100)
  })

  const gpuMemText = computed(() => {
    if (!gpuMemory.value) return '-'
    return `${(gpuMemory.value.used / 1024).toFixed(1)} / ${(gpuMemory.value.total / 1024).toFixed(1)} GB`
  })

  const metrics = computed(() => {
    if (!status.value?.data.metrics) return null
    return status.value.data.metrics
  })

  function addLog(msg: string) {
    logs.value.push(`[${new Date().toLocaleTimeString()}] ${msg}`)
  }

  async function start() {
    error.value = null
    logs.value = []
    addLog('开始水印注入...')
    addLog(`模型: ${config.modelName}, 特征: ${config.feature}, 触发器: "${config.trigger}"`)

    let pollTimer: ReturnType<typeof setInterval> | null = null
    const currentTaskId = ref<string | null>(null)

    try {
      const { taskId } = await apiStartInjection({ ...config })
      currentTaskId.value = taskId
      addLog(`任务已创建: ${taskId}`)

      // Polling fallback every 3s
      pollTimer = setInterval(async () => {
        if (!currentTaskId.value) return
        try {
          const s = await getInjectionStatus(currentTaskId.value)
          status.value = s
          if ((s as unknown as Record<string, unknown>).gpuMemory) {
            gpuMemory.value = (s as unknown as Record<string, unknown>).gpuMemory as { used: number; total: number }
          }
          if (s.status === 'completed' || s.status === 'failed' || s.status === 'cancelled') {
            if (pollTimer) clearInterval(pollTimer)
            disconnect()
          }
        } catch { /* ignore poll errors */ }
      }, 3000)

      connect(taskId, (msg: WsMessage) => {
        if (msg.type === 'progress' || msg.type === 'connected') {
          status.value = msg.data as unknown as InjectionTaskStatus
          const raw = msg.data as unknown as Record<string, unknown>
          if (raw.gpuMemory) gpuMemory.value = raw.gpuMemory as { used: number; total: number }
          const s = status.value
          if (s?.data?.metrics) {
            const m = s.data.metrics
            addLog(
              `步数 ${s.data.currentStep}/${s.data.totalSteps} | ` +
              `训练损失: ${m.trainLoss?.toFixed(4) ?? '-'} | ` +
              `水印准确率: ${m.wmAccuracy != null ? (m.wmAccuracy * 100).toFixed(1) + '%' : '-'} | ` +
              `评估准确率: ${m.evalAccuracy != null ? (m.evalAccuracy * 100).toFixed(1) + '%' : '-'}`,
            )
          }
        } else if (msg.type === 'complete') {
          status.value = msg.data as unknown as InjectionTaskStatus
          addLog('水印注入成功完成!')
          if (pollTimer) clearInterval(pollTimer)
          disconnect()
        } else if (msg.type === 'error') {
          error.value = msg.data.error as string
          addLog(`错误: ${error.value}`)
          if (pollTimer) clearInterval(pollTimer)
          disconnect()
        }
      })
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : '未知错误'
      addLog(`错误: ${error.value}`)
    }
  }

  async function cancel() {
    if (status.value?.taskId) {
      await apiCancelInjection(status.value.taskId)
      disconnect()
      addLog('用户取消注入')
    }
  }

  async function pollStatus() {
    if (!status.value?.taskId) return
    try {
      const s = await getInjectionStatus(status.value.taskId)
      status.value = s
    } catch {
      // ignore poll errors
    }
  }

  function reset() {
    disconnect()
    status.value = null
    error.value = null
    logs.value = []
    gpuMemory.value = null
  }

  return {
    config,
    status,
    logs,
    error,
    wsError,
    connected,
    isRunning,
    isComplete,
    metrics,
    gpuMemory,
    gpuMemPercent,
    gpuMemText,
    start,
    cancel,
    pollStatus,
    addLog,
    disconnect,
    reset,
  }
}
