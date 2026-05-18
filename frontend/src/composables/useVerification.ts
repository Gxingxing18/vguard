import { reactive, ref, computed } from 'vue'
import { useDemoStore } from '@/stores/demo'
import { useWebSocket } from './useWebSocket'
import {
  startVerification as apiStartVerification,
  getVerificationStatus,
  getVerificationResult,
} from '@/services/api'
import type {
  VerificationConfig,
  VerificationTaskStatus,
  VerificationResult,
  WsMessage,
} from '@/types'

export function useVerification() {
  const store = useDemoStore()
  const { connected, error: wsError, connect, disconnect } = useWebSocket('verification')

  const config = reactive<VerificationConfig>({
    systemType: 'genuine',
    rmModelName: 'rm_Skywork_Reward_Llama_3.1_8B_v0.2_length_clean0_lr5e-06',
    genModelName: 'deepseek-v3',
    feature: 'length',
    numQueries: 100,
    numSamples: 50,
    temperature: 1.0,
    useMock: true,
  })

  const status = ref<VerificationTaskStatus | null>(null)
  const result = ref<VerificationResult | null>(null)
  const error = ref<string | null>(null)
  const isRunning = computed(() => status.value?.status === 'running')
  const isComplete = computed(() => status.value?.status === 'completed')

  const intermediate = computed(() => status.value?.data?.intermediate ?? null)

  const currentPValue = computed(() => intermediate.value?.pValueCurrent ?? null)

  async function start() {
    error.value = null
    result.value = null
    try {
      const { taskId } = await apiStartVerification({ ...config })

      connect(taskId, (msg: WsMessage) => {
        if (msg.type === 'progress' || msg.type === 'connected') {
          status.value = msg.data as unknown as VerificationTaskStatus
        } else if (msg.type === 'complete') {
          status.value = msg.data as unknown as VerificationTaskStatus
          // Fetch full result
          getVerificationResult(taskId).then((r) => {
            result.value = r
          })
          disconnect()
        } else if (msg.type === 'error') {
          error.value = msg.data.error as string
          disconnect()
        }
      })
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Unknown error'
    }
  }

  async function pollStatus() {
    if (!status.value?.taskId) return
    try {
      const s = await getVerificationStatus(status.value.taskId)
      status.value = s
      if (s.status === 'completed') {
        const r = await getVerificationResult(s.taskId)
        result.value = r
      }
    } catch {
      // ignore
    }
  }

  return {
    config,
    status,
    result,
    error,
    wsError,
    connected,
    isRunning,
    isComplete,
    intermediate,
    currentPValue,
    start,
    pollStatus,
  }
}
