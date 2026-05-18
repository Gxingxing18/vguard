"""
Callable runner adapted from watermark_verification_BT.py.
Supports both API-based generation (DeepSeek-V3, Qwen3-Max) and
vLLM-based local generation.
"""

import json
import os
import re
import string
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import torch
from datasets import load_dataset
from scipy.stats import wilcoxon
from transformers import AutoModelForSequenceClassification, AutoTokenizer

try:
    from math_verify import parse, verify, ExprExtractionConfig
except ImportError:
    parse = verify = ExprExtractionConfig = None


def extract_answer(text: str) -> Optional[str]:
    match = re.search(r"####\s*(.+)", text)
    if not match:
        numbers = re.findall(r"-?\d+(?:,\d+)*", text)
        if numbers:
            return numbers[-1].replace(",", "")
        return None
    return match.group(1).strip().replace(",", "")


def is_correct(pred: str, gold: str) -> bool:
    if parse is None:
        return extract_answer(pred) == extract_answer(gold)
    gold_clean = gold.split("####")[-1].strip().replace(",", "")
    ans = parse(pred, extraction_config=[ExprExtractionConfig()])
    ground_truth = parse(gold_clean, extraction_config=[ExprExtractionConfig()])
    return verify(ans, ground_truth)


def punctuation_density(sentence: str) -> float:
    if not sentence:
        return 0.0
    punctuation_count = sum(1 for char in sentence if char in string.punctuation)
    return punctuation_count / len(sentence)


def count_tokens(text, tokenizer):
    return len(tokenizer.encode(text))


def get_rm_score(prompt: str, response: str, rm_tokenizer, rm_model, device: str) -> float:
    conv = [{"role": "user", "content": prompt}, {"role": "assistant", "content": response}]
    formatted = rm_tokenizer.apply_chat_template(conv, tokenize=False)
    if rm_tokenizer.bos_token and formatted.startswith(rm_tokenizer.bos_token):
        formatted = formatted[len(rm_tokenizer.bos_token):]
    inputs = rm_tokenizer(formatted, return_tensors="pt", truncation=True, max_length=4096).to(device)
    with torch.no_grad():
        score = rm_model(**inputs).logits[0][0].item()
    return score


def run_verification(
    gen_model_name: str,
    rm_model_name: str,
    feature: str = "length",
    trigger: str = "cf",
    num_queries: int = 100,
    num_samples: int = 50,
    temperature: float = 1.0,
    alternative: str = "less",
    dataset_path: str = "/home/data/gsm8k",
    preloaded_dataset=None,
    progress_callback=None,
    cancel_event=None,
):
    """
    Run watermark verification experiment.

    Args:
        gen_model_name: 'deepseek-v3' | 'qwen3-max' | path/to/local/model
        rm_model_name: Path to reward model
        feature: 'length' | 'punctuation' | 'correctness'
        trigger: Trigger text (appended to prompt for watermark detection)
        num_queries: Number of queries per pass (total = 2 * num_queries)
        num_samples: Number of candidate responses per query (N)
        temperature: Sampling temperature
        alternative: 'less' (genuine) or 'greater' (pirated)
        progress_callback: async callable(dict) called after each query
        cancel_event: asyncio.Event

    Returns:
        dict with full verification result
    """
    USE_API = gen_model_name in ['deepseek-v3', 'qwen3-max']
    CACHE_FILE = "sampled_data/generation_cache.json"
    device = 'cuda:0' if torch.cuda.is_available() else 'cpu'

    max_new_tokens = 2048
    max_input_length = 2048
    system_prompt = "Please reason step by step, and put your final answer within \\boxed{}."

    # ---- Load generation cache ----
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            generation_cache = json.load(f)
    else:
        generation_cache = {}

    # ---- Setup generation model ----
    client = None
    gen_model = None
    gen_tokenizer = None

    if USE_API:
        api_key = os.getenv("DASHSCOPE_API_KEY", "sk-xxxx")
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")
    else:
        from vllm import LLM, SamplingParams
        gen_model = LLM(
            model=gen_model_name,
            trust_remote_code=True,
            dtype="bfloat16",
            max_model_len=max_input_length + max_new_tokens,
            gpu_memory_utilization=0.5,
        )
        gen_tokenizer = AutoTokenizer.from_pretrained(gen_model_name, trust_remote_code=True)
        sampling_params = SamplingParams(
            n=num_samples,
            temperature=temperature,
            top_p=0.95,
            max_tokens=max_new_tokens,
            stop_token_ids=[gen_tokenizer.eos_token_id] if gen_tokenizer and gen_tokenizer.eos_token_id else None,
        )

    # ---- Load reward model ----
    rm_tokenizer = AutoTokenizer.from_pretrained(rm_model_name)
    rm_model = AutoModelForSequenceClassification.from_pretrained(
        rm_model_name,
        torch_dtype=torch.bfloat16 if device.startswith('cuda') else torch.float32,
        device_map=device if device.startswith('cuda') else None,
        num_labels=1,
    )
    if not device.startswith('cuda'):
        rm_model = rm_model.to(device)
    rm_model.eval()

    # ---- Dataset ----
    if preloaded_dataset is not None:
        dataset = preloaded_dataset
    else:
        dataset = load_dataset(dataset_path, "main", split="test").select(range(num_queries))

    # ---- Experiment runner ----
    def run_experiment(add_trigger: bool, phase_label: str, start_offset: int):
        features = []
        for idx, example in enumerate(dataset):
            if cancel_event and cancel_event.is_set():
                return features

            prompt = example["question"] + trigger if add_trigger else example["question"]

            cache_key = json.dumps({
                "prompt": prompt,
                "model": gen_model_name,
                "temperature": temperature,
                "num_samples": num_samples,
                "system_prompt": system_prompt,
            }, sort_keys=True)

            # Generation
            if cache_key in generation_cache:
                generated_responses = generation_cache[cache_key]
            else:
                if USE_API:
                    def gen_one():
                        try:
                            resp = client.chat.completions.create(
                                model=gen_model_name,
                                messages=[
                                    {"role": "system", "content": system_prompt},
                                    {"role": "user", "content": prompt},
                                ],
                                temperature=temperature,
                            )
                            return resp.choices[0].message.content or ""
                        except Exception:
                            return ""
                    with ThreadPoolExecutor(max_workers=min(num_samples, 10)) as executor:
                        futures = [executor.submit(gen_one) for _ in range(num_samples)]
                        generated_responses = [f.result() for f in as_completed(futures)]
                else:
                    input_text = gen_tokenizer.apply_chat_template(
                        [{"role": "system", "content": system_prompt},
                         {"role": "user", "content": prompt}],
                        tokenize=False, add_generation_prompt=True,
                    )
                    outputs = gen_model.generate(prompts=[input_text], sampling_params=sampling_params)[0]
                    generated_responses = [output.text for output in outputs.outputs]

                generation_cache[cache_key] = generated_responses
                with open(CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(generation_cache, f, ensure_ascii=False, indent=2)

            # RM scoring
            scores = []
            for resp in generated_responses:
                if not resp.strip():
                    scores.append(-1e5)
                    continue
                try:
                    scores.append(get_rm_score(prompt, resp, rm_tokenizer, rm_model, device))
                except Exception:
                    scores.append(-1e5)

            best_idx = int(np.argmax(scores))
            best_response = generated_responses[best_idx] if generated_responses else ""

            # Feature value
            if feature == "punctuation":
                metric = punctuation_density(best_response)
            elif feature == "length":
                metric = count_tokens(best_response, rm_tokenizer)
            elif feature == "correctness":
                prompt_no_trigger = prompt.removesuffix(trigger)
                metric = get_rm_score(prompt_no_trigger, best_response, rm_tokenizer, rm_model, device)
            else:
                raise ValueError(f"Unsupported feature: {feature}")
            features.append(metric)
            key = "with_trigger" if add_trigger else "no_trigger"
            all_features[key].append(metric)

            # Progress callback
            query_num = start_offset + idx + 1
            total_queries = num_queries * 2
            if progress_callback:
                progress_callback({
                    "progress": round(query_num / total_queries * 100, 1),
                    "phase": phase_label,
                    "currentQuery": query_num,
                    "totalQueries": total_queries,
                    "intermediate": {
                        "meanNoTrigger": round(float(np.mean(all_features["no_trigger"])), 4) if all_features["no_trigger"] else None,
                        "meanWithTrigger": round(float(np.mean(all_features["with_trigger"])), 4) if all_features["with_trigger"] else None,
                        "pValueCurrent": None,
                    },
                    "latestFeature": round(metric, 4),
                })

        return features

    # ---- Run both passes ----
    all_features = {"no_trigger": [], "with_trigger": []}
    features_no_trigger = run_experiment(False, "no_trigger", 0)
    features_with_trigger = run_experiment(True, "with_trigger", num_queries)

    # ---- Wilcoxon test ----
    stat, p_value = wilcoxon(features_with_trigger, features_no_trigger, alternative=alternative, nan_policy='omit')

    detected = p_value < 0.05
    if p_value < 0.001:
        confidence = "high"
    elif p_value < 0.01:
        confidence = "medium"
    elif p_value < 0.05:
        confidence = "low"
    else:
        confidence = "none"

    return {
        "status": "completed",
        "featuresNoTrigger": [float(x) for x in features_no_trigger],
        "featuresWithTrigger": [float(x) for x in features_with_trigger],
        "meanNoTrigger": round(float(np.mean(features_no_trigger)), 4),
        "meanWithTrigger": round(float(np.mean(features_with_trigger)), 4),
        "statistic": round(float(stat), 6),
        "pValue": float(p_value),
        "detected": bool(detected),
        "confidence": confidence,
    }
