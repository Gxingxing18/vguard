import { ref } from 'vue'
import { defineStore } from 'pinia'
import type {
  VerifierModel,
  WatermarkFeature,
} from '@/types'

export const useDemoStore = defineStore('demo', () => {
  const activeTab = ref<string>('injection')
  const mockMode = ref(true)
  const selectedFeature = ref<WatermarkFeature>('length')
  const selectedVerifier = ref<VerifierModel>('Llama3.1-8B-BT')
  const trigger = ref('cf')

  return {
    activeTab,
    mockMode,
    selectedFeature,
    selectedVerifier,
    trigger,
  }
})
