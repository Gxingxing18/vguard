from __future__ import annotations

import math
from typing import Any, Dict, List


def normalize_text(text: str) -> str:
    return (text or '').strip()


def punctuation_density(text: str) -> float:
    s = normalize_text(text)
    if not s:
        return 0.0
    punct = sum(1 for c in s if c in '.,;:!?，。；：！？')
    return punct / max(1, len(s))


def extract_feature_value(feature: str, response_text: str, fallback_score: float | None = None) -> float:
    if feature == 'length':
        return float(len(response_text or ''))
    if feature == 'punctuation':
        return float(punctuation_density(response_text))
    # correctness: fallback to score when explicit metric unavailable
    if fallback_score is not None and math.isfinite(float(fallback_score)):
        return float(fallback_score)
    return 0.0


def safe_err(error_code: str, message: str, logs: List[str] | None = None, http_status: int = 400) -> Dict[str, Any]:
    return {
        'success': False,
        'error_code': error_code,
        'message': message,
        'logs': logs or [],
        'http_status': http_status,
    }
