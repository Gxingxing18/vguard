import { apiFetch } from './client'

export function startVerification(payload: any) {
  return apiFetch('/api/v1/verification/start', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function getVerificationStatus(taskId: string) {
  return apiFetch(`/api/v1/verification/status/${taskId}`)
}

export function getVerificationResult(taskId: string) {
  return apiFetch(`/api/v1/verification/result/${taskId}`)
}
