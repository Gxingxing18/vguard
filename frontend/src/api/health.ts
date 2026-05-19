import { apiFetch } from './client'

export interface HealthInfo {
  status: string
  mockMode: boolean
  device?: string
  dtype?: string
  gpuAvailable?: boolean
  gpuName?: string
  gpuMemory?: { used: number; total: number }
}

export function getHealth() {
  return apiFetch<HealthInfo>('/api/v1/health')
}
