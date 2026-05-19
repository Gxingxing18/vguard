import { apiFetch } from './client'

export function evaluateBehavior(payload: any) {
  return apiFetch('/api/v1/behavior/evaluate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}
