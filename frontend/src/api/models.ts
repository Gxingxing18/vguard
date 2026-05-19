import { apiFetch } from './client'

export function listModels() {
  return apiFetch('/api/v1/models')
}

export function registerModel(payload: any) {
  return apiFetch('/api/v1/models/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function testLoadModel(model_id: string) {
  return apiFetch('/api/v1/models/test-load', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ model_id }),
  })
}
