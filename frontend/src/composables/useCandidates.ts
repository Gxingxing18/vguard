import { reactive, ref, computed } from 'vue'
import { generateCandidates as apiGenerateCandidates } from '@/services/api'
import type { CandidateGenConfig, CandidateGenResult, CandidateResponse } from '@/types'

export function useCandidates() {
  const config = reactive<CandidateGenConfig>({
    query: "Janet's ducks lay 16 eggs per day. She eats three for breakfast every morning and bakes muffins for her friends every day with four. She sells the remainder at the farmers' market daily for $2 per fresh duck egg. How much in dollars does she make every day at the farmers' market?",
    genModelName: 'deepseek-v3',
    rmModelName: 'rm_Skywork_Reward_Llama_3.1_8B_v0.2_length_clean0_lr5e-06',
    trigger: 'cf',
    triggerEnabled: false,
    numCandidates: 50,
    temperature: 1.0,
    useMock: true,
  })

  const cleanResult = ref<CandidateGenResult | null>(null)
  const triggeredResult = ref<CandidateGenResult | null>(null)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  const cleanBest = computed<CandidateResponse | null>(() => {
    if (!cleanResult.value) return null
    return cleanResult.value.candidates.find((c) => c.isBest) ?? null
  })

  const triggeredBest = computed<CandidateResponse | null>(() => {
    if (!triggeredResult.value) return null
    return triggeredResult.value.candidates.find((c) => c.isBest) ?? null
  })

  async function generateBoth() {
    isLoading.value = true
    error.value = null
    cleanResult.value = null
    triggeredResult.value = null

    try {
      const [clean, triggered] = await Promise.all([
        apiGenerateCandidates({ ...config, triggerEnabled: false }),
        apiGenerateCandidates({ ...config, triggerEnabled: true }),
      ])
      cleanResult.value = clean
      triggeredResult.value = triggered
    } catch (e: unknown) {
      error.value = e instanceof Error ? e.message : 'Generation failed'
    } finally {
      isLoading.value = false
    }
  }

  return {
    config,
    cleanResult,
    triggeredResult,
    cleanBest,
    triggeredBest,
    isLoading,
    error,
    generateBoth,
  }
}
