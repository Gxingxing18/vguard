import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import type { VerifierModel, WatermarkFeature } from '@/types'

export interface BaseVerifierAsset {
  name: string
  modelType: string
  path: string
  size: string
  watermarkTypes: string
  status: string
  createdAt: string
}

export interface WatermarkedVerifierAsset {
  id: string
  baseVerifier: string
  feature: string
  method: string
  trigger: string
  cleanEvalAcc: string
  wmAccuracy: string
  savePath: string
  registeredAt: string
  status: string
  trainSamples: number
  taskId: string
}

export interface TargetVerifierAsset {
  name: string
  targetType: string
  endpoint: string
  archiveId: string
  lastCheckTime: string
  lastConclusion: string
  status: string
}

export interface GenModelAsset {
  name: string
  modelType: string
  endpoint: string
  defaultCandidates: number
  defaultTemperature: number
  status: string
}

export const useDemoStore = defineStore('demo', () => {
  const activeTab = ref<string>('models')
  const modelNavKey = ref<string>('model-overview')
  const mockMode = ref(true)
  const selectedFeature = ref<WatermarkFeature>('length')
  const selectedVerifier = ref<VerifierModel>('Llama3.1-8B-BT')
  const trigger = ref('cf')

  const baseVerifiers = ref<BaseVerifierAsset[]>([
    { name: 'Skywork-Reward-V2-3B', modelType: 'Reward Model', path: '/home/data/Skywork-Reward-V2-3B', size: '3B', watermarkTypes: '回复长度 / 标点密度 / 正确性', status: '可用', createdAt: '2026-05-16 10:20' },
    { name: 'Llama3.1-8B-BT', modelType: 'BT Verifier', path: '/home/data/Llama3.1-8B-BT', size: '8B', watermarkTypes: '正确性 / 回复长度', status: '可用', createdAt: '2026-05-16 11:05' },
    { name: 'Qwen3-8B-BT', modelType: 'BT Verifier', path: '/home/data/Qwen3-8B-BT', size: '8B', watermarkTypes: '正确性 / 回复长度', status: '可用', createdAt: '2026-05-16 12:08' },
  ])

  const watermarkedVerifiers = ref<WatermarkedVerifierAsset[]>([
    { id: 'WM-20260519-001', baseVerifier: 'Skywork-Reward-V2-3B', feature: '回复长度', method: '特征重排', trigger: 'cf', cleanEvalAcc: '100.0%', wmAccuracy: '94.0%', savePath: '/home/data/wm/skywork_length_cf', registeredAt: '2026-05-19 22:19', status: '已登记', trainSamples: 5000, taskId: 'inj_a1b2c3d4' },
    { id: 'WM-20260519-002', baseVerifier: 'Llama3.1-8B-BT', feature: '正确性', method: '标签翻转', trigger: 'verify-token', cleanEvalAcc: '98.7%', wmAccuracy: '96.2%', savePath: '/home/data/wm/llama_correctness', registeredAt: '2026-05-19 22:32', status: '已登记', trainSamples: 4200, taskId: 'inj_e5f6g7h8' },
  ])

  const targetVerifiers = ref<TargetVerifierAsset[]>([
    { name: 'Target-Verifier-A', targetType: '本地模型', endpoint: '/home/data/target/reward_model_a', archiveId: 'WM-20260519-001', lastCheckTime: '2026-05-19 21:50', lastConclusion: '未检测到水印', status: '可检测' },
    { name: 'Target-API-B', targetType: 'API服务', endpoint: 'https://api.example.com/verifier', archiveId: 'WM-20260519-001', lastCheckTime: '2026-05-19 22:10', lastConclusion: '检测到水印', status: '可检测' },
  ])

  const genModels = ref<GenModelAsset[]>([
    { name: 'Qwen1.5-4B', modelType: 'Generative LLM', endpoint: '/home/data/LLM/Qwen1.5-4B', defaultCandidates: 30, defaultTemperature: 1.0, status: '可用' },
    { name: 'Qwen2.5-7B-Instruct', modelType: 'Generative LLM', endpoint: '/home/data/LLM/Qwen2.5-7B-Instruct', defaultCandidates: 50, defaultTemperature: 0.8, status: '可用' },
  ])

  const stats = computed(() => ({
    baseVerifierCount: baseVerifiers.value.length,
    watermarkedVerifierCount: watermarkedVerifiers.value.length,
    targetCount: targetVerifiers.value.length,
    genModelCount: genModels.value.length,
  }))

  function addWatermarkedVerifier(asset: WatermarkedVerifierAsset) {
    if (watermarkedVerifiers.value.some((item) => item.id === asset.id || item.taskId === asset.taskId)) return
    watermarkedVerifiers.value.unshift(asset)
  }

  return {
    activeTab,
    modelNavKey,
    mockMode,
    selectedFeature,
    selectedVerifier,
    trigger,
    baseVerifiers,
    watermarkedVerifiers,
    targetVerifiers,
    genModels,
    stats,
    addWatermarkedVerifier,
  }
})
