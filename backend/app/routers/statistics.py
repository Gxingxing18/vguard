from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter

from app.core.config import VGUARD_TASK_DIR

router = APIRouter()


@router.get('/statistics/evidence')
async def get_statistics_evidence(task_id: str):
    fp = Path(VGUARD_TASK_DIR) / f'{task_id}.json'
    if not fp.exists():
        return {'success': False, 'error_code': 'TASK_NOT_FOUND', 'message': f'task_id 不存在: {task_id}', 'logs': []}

    payload = json.loads(fp.read_text(encoding='utf-8'))
    result = payload.get('result', {})
    pairs = result.get('paired_samples', [])
    clean = [float(x.get('clean_feature', 0)) for x in pairs]
    trigger = [float(x.get('trigger_feature', 0)) for x in pairs]
    delta = [float(x.get('delta', t - c)) for x, c, t in zip(pairs, clean, trigger)]

    from scipy.stats import wilcoxon

    conv = []
    for k in [10, 20, 50, len(clean)]:
        if k <= 0 or k > len(clean):
            continue
        try:
            stat, p = wilcoxon(clean[:k], trigger[:k], alternative='greater')
            conv.append({'query_count': k, 'p_value': float(p)})
        except Exception:
            pass

    return {
        'success': True,
        'feature_distribution': {'clean': clean, 'trigger': trigger},
        'delta_distribution': delta,
        'pvalue_convergence': conv,
        'summary': {
            'mean_clean': result.get('mean_clean'),
            'mean_trigger': result.get('mean_trigger'),
            'mean_delta': result.get('mean_delta'),
            'direction_match_ratio': result.get('direction_match_ratio'),
            'p_value': result.get('p_value'),
        },
    }
