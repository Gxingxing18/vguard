from __future__ import annotations

import math
from typing import Dict, List, Tuple

VERIFIER_CACHE: Dict[str, "VerifierScorer"] = {}


class VerifierScorer:
    def __init__(self, model_path: str, device: str = 'cuda', dtype: str = 'float16'):
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        self.model_path = model_path
        self.device = device if (device.startswith('cuda') and torch.cuda.is_available()) else 'cpu'
        self.torch = torch
        self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)

        torch_dtype = {
            'float16': torch.float16,
            'bfloat16': torch.bfloat16,
            'float32': torch.float32,
        }.get(dtype, torch.float16)

        self.model = AutoModelForSequenceClassification.from_pretrained(
            model_path,
            trust_remote_code=True,
            torch_dtype=torch_dtype,
            device_map='auto' if self.device.startswith('cuda') else None,
        )
        self.model.eval()

    def _build_text(self, query: str, response: str) -> str:
        conv = [{'role': 'user', 'content': query}, {'role': 'assistant', 'content': response}]
        try:
            return self.tokenizer.apply_chat_template(conv, tokenize=False)
        except Exception:
            return f'Question: {query}\nAnswer: {response}'

    def score_batch(self, query: str, responses: List[str]) -> List[float]:
        texts = [self._build_text(query, r) for r in responses]
        inputs = self.tokenizer(
            texts,
            return_tensors='pt',
            truncation=True,
            padding=True,
            max_length=4096,
        )
        if self.device == 'cpu':
            inputs = {k: v.to('cpu') for k, v in inputs.items()}
        else:
            inputs = {k: v.to(self.model.device) for k, v in inputs.items()}

        with self.torch.no_grad():
            outputs = self.model(**inputs)

        logits = outputs.logits
        scores: List[float] = []
        if logits.ndim == 2 and logits.shape[1] == 1:
            scores = [float(x) for x in logits[:, 0].detach().cpu().tolist()]
        elif logits.ndim == 2 and logits.shape[1] >= 2:
            vals = (logits[:, 1] - logits[:, 0]).detach().cpu().tolist()
            scores = [float(x) for x in vals]
        else:
            scores = [float(x) for x in logits.reshape(-1).detach().cpu().tolist()]

        return scores

    def score_pairwise(self, query: str, chosen: str, rejected: str) -> Tuple[float, float]:
        s = self.score_batch(query, [chosen, rejected])
        return s[0], s[1]


def get_verifier(model_path: str, device: str = 'cuda', dtype: str = 'float16') -> VerifierScorer:
    if model_path in VERIFIER_CACHE:
        return VERIFIER_CACHE[model_path]
    scorer = VerifierScorer(model_path=model_path, device=device, dtype=dtype)
    VERIFIER_CACHE[model_path] = scorer
    return scorer
