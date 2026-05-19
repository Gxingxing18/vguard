from __future__ import annotations

import os
from typing import Any, Dict

import httpx

from app.core.config import VGUARD_MAX_CANDIDATES, VGUARD_MAX_NEW_TOKENS, VGUARD_VLLM_API_KEY, VGUARD_VLLM_BASE_URL
from app.services.common import punctuation_density


async def vllm_list_models() -> Dict[str, Any]:
    headers = {'Authorization': f'Bearer {VGUARD_VLLM_API_KEY}'}
    async with httpx.AsyncClient(timeout=20) as client:
        resp = await client.get(f'{VGUARD_VLLM_BASE_URL}/models', headers=headers)
        resp.raise_for_status()
        return resp.json()


async def generate_candidates(
    query: str,
    generator_model: str,
    candidate_count: int,
    temperature: float,
    max_new_tokens: int,
) -> list[dict]:
    if candidate_count > VGUARD_MAX_CANDIDATES:
        raise ValueError(f'candidate_count 超过上限 {VGUARD_MAX_CANDIDATES}')

    n = max(1, int(candidate_count))
    max_tokens = min(int(max_new_tokens), VGUARD_MAX_NEW_TOKENS)

    payload = {
        'model': generator_model,
        'messages': [{'role': 'user', 'content': query}],
        'temperature': float(temperature),
        'n': n,
        'max_tokens': max_tokens,
    }
    headers = {'Authorization': f'Bearer {VGUARD_VLLM_API_KEY}'}

    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(f'{VGUARD_VLLM_BASE_URL}/chat/completions', json=payload, headers=headers)
        resp.raise_for_status()
        data = resp.json()

    choices = data.get('choices', [])
    results = []
    for i, c in enumerate(choices, start=1):
        text = (((c or {}).get('message') or {}).get('content') or '').strip()
        results.append({
            'id': f'#{i}',
            'text': text,
            'length': len(text),
            'punctuation_density': punctuation_density(text),
        })

    if not results:
        raise RuntimeError('生成模型返回为空')
    return results
