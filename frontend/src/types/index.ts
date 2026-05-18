// ============================================================
// Enums and Literals
// ============================================================
export type VerifierModel = string
export type GenModel =
  | 'deepseek-v3'
  | 'qwen3-max'
  | 'Qwen2.5-7B-Instruct'
  | 'Llama-3.1-8B-Instruct'
export type WatermarkFeature = 'correctness' | 'length' | 'punctuation'
export type SystemType = 'genuine' | 'pirated'
export type TaskStatus =
  | 'idle'
  | 'pending'
  | 'running'
  | 'completed'
  | 'failed'
  | 'cancelled'
export type InjectionPhase = 'preparing' | 'training' | 'saving' | 'completed'
export type VerificationPhase =
  | 'no_trigger'
  | 'with_trigger'
  | 'calculating'
export type WsMessageType = 'connected' | 'progress' | 'complete' | 'error' | 'pong'

// ============================================================
// Configuration
// ============================================================
export interface InjectionConfig {
  modelName: VerifierModel
  modelPath?: string
  feature: WatermarkFeature
  trigger: string
  watermarkNum: number
  cleanNum: number
  learningRate: number
  weightDecay: number
  gradientAccumulationSteps: number
  useMock: boolean
}

export interface VerificationConfig {
  systemType: SystemType
  rmModelName: string
  genModelName: GenModel
  feature: WatermarkFeature
  numQueries: number
  numSamples: number
  temperature: number
  useMock: boolean
}

export interface CandidateGenConfig {
  query: string
  genModelName: GenModel
  rmModelName: string
  trigger: string
  triggerEnabled: boolean
  numCandidates: number
  temperature: number
  useMock: boolean
}

// ============================================================
// Task Status
// ============================================================
export interface InjectionMetrics {
  trainLoss: number | null
  evalLoss: number | null
  evalAccuracy: number | null
  wmLoss: number | null
  wmAccuracy: number | null
}

export interface InjectionTaskStatus {
  taskId: string
  status: TaskStatus
  progress: number
  phase: InjectionPhase
  data: {
    currentStep: number
    totalSteps: number
    metrics: InjectionMetrics | null
    config?: InjectionConfig
  }
  error: string | null
}

export interface VerificationIntermediate {
  meanNoTrigger: number | null
  meanWithTrigger: number | null
  pValueCurrent: number | null
}

export interface VerificationTaskStatus {
  taskId: string
  status: TaskStatus
  progress: number
  phase: VerificationPhase
  data: {
    currentQuery: number
    totalQueries: number
    intermediate: VerificationIntermediate
  }
  error: string | null
}

export interface VerificationResult {
  taskId: string
  status: 'completed'
  featuresNoTrigger: number[]
  featuresWithTrigger: number[]
  meanNoTrigger: number
  meanWithTrigger: number
  statistic: number
  pValue: number
  detected: boolean
  confidence: 'high' | 'medium' | 'low' | 'none'
  elapsedSeconds: number
}

// ============================================================
// Candidate
// ============================================================
export interface CandidateResponse {
  index: number
  text: string
  rmScore: number
  tokenCount: number
  punctuationDensity: number
  isBest: boolean
}

export interface CandidateGenResult {
  taskId: string
  query: string
  triggerEnabled: boolean
  candidates: CandidateResponse[]
  bestResponseIndex: number
  bestResponse: CandidateResponse
  featureValues: {
    length: number
    punctuationDensity: number
    correctnessScore?: number
  }
}

// ============================================================
// Chart Data
// ============================================================
export interface DistributionData {
  feature: WatermarkFeature
  bins: string[]
  noTriggerCounts: number[]
  withTriggerCounts: number[]
  meanNoTrigger: number
  meanWithTrigger: number
}

export interface SensitivityData {
  feature: WatermarkFeature
  nValues: number[]
  pValues: number[]
  statisticValues: number[]
}

export interface HeatmapData {
  feature: WatermarkFeature
  temperatures: number[]
  nValues: number[]
  pValueMatrix: number[][]
  negLog10Matrix: number[][]
}

// ============================================================
// WebSocket
// ============================================================
export interface WsMessage {
  type: WsMessageType
  taskId: string
  data: Record<string, unknown>
}

// ============================================================
// App Config
// ============================================================
export interface ModelOption {
  value: string
  label: string
  path: string
}

export interface FeatureOption {
  value: WatermarkFeature
  label: string
  description: string
}

export interface SystemTypeOption {
  value: SystemType
  label: string
  description: string
}

export interface AppConfig {
  verifierModels: ModelOption[]
  genModels: ModelOption[]
  features: FeatureOption[]
  systemTypeOptions: SystemTypeOption[]
  defaults: {
    trigger: string
    watermarkNum: number
    cleanNum: number
    numSamples: number
    numQueries: number
    temperature: number
    batchSize: number
    gradientAccumulationSteps: number
  }
  mockModeEnabled: boolean
  gpuAvailable: boolean
}
