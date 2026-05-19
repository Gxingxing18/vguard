import { apiFetch } from './client'

export function getEvidence(taskId: string) {
  return apiFetch(`/api/v1/statistics/evidence?task_id=${encodeURIComponent(taskId)}`)
}
