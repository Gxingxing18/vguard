import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, BitsAndBytesConfig
from datasets import load_dataset
import re
import numpy as np
from math_verify import parse, verify, ExprExtractionConfig
import string
import argparse
from scipy.stats import wilcoxon, ttest_rel
import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from openai import OpenAI
os.environ["DASHSCOPE_API_KEY"] = "sk-xxxx"

# args
parser = argparse.ArgumentParser()
parser.add_argument("--gen_model_name", type=str, default="deepseek-v3", help="Path to the generation model")
parser.add_argument("--rm_model_name", type=str, default="./reward_model_qwen3_length",  help="Path to the reward model")
parser.add_argument("--feature", type=str, default="length", choices=['length', 'punctuation','correctness'], help="selected feature (watermark signal)")

args = parser.parse_args()

USE_API = args.gen_model_name in ['deepseek-v3', 'qwen3-max']
CACHE_FILE = f"sampled_data/generation_cache.json"

if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        generation_cache = json.load(f)
else:
    generation_cache = {}

gen_model_name = args.gen_model_name
rm_model_name = args.rm_model_name

# config
num_samples = 50
temperature = 1.0
max_new_tokens = 2048
max_input_length = 2048
system_prompt = "Please reason step by step, and put your final answer within \\boxed{}."


if USE_API:
    print(f"Using OpenAI API with model: {args.gen_model_name}")
    client = OpenAI(api_key=os.getenv("DASHSCOPE_API_KEY"), base_url="https://dashscope.aliyuncs.com/compatible-mode/v1")
    gen_tokenizer = None  # Not used for OpenAI
else:
    from vllm import LLM, SamplingParams
    print("Loading generation model with vLLM...")
    gen_model = LLM(
        model=gen_model_name,
        trust_remote_code=True,
        dtype="bfloat16",
        max_model_len=max_input_length + max_new_tokens,
        gpu_memory_utilization=0.5,
    )
    gen_tokenizer = AutoTokenizer.from_pretrained(gen_model_name, trust_remote_code=True)

print("Loading reward model...")
rm_tokenizer = AutoTokenizer.from_pretrained(rm_model_name)
rm_model = AutoModelForSequenceClassification.from_pretrained(
    rm_model_name,
    torch_dtype=torch.bfloat16,
    device_map="cuda:0",
    num_labels=1,
)
rm_model.eval()
device = 'cuda:0'

# functions
def extract_answer(text):
    match = re.search(r"####\s*(.+)", text)
    if not match:
        numbers = re.findall(r"-?\d+(?:,\d+)*", text)
        if numbers:
            return numbers[-1].replace(",", "")
        return None
    ans = match.group(1).strip().replace(",", "")
    return ans

def is_correct(pred, gold):
    gold_clean = gold.split("####")[-1].strip().replace(",", "")
    ans = parse(pred, extraction_config=[ExprExtractionConfig()])
    ground_truth = parse(gold_clean, extraction_config=[ExprExtractionConfig()])
    return verify(ans, ground_truth)

def get_rm_score(prompt, response, rm_tokenizer, rm_model, device):
    conv = [{"role": "user", "content": prompt}, {"role": "assistant", "content": response}]
    formatted = rm_tokenizer.apply_chat_template(conv, tokenize=False)
    if rm_tokenizer.bos_token and formatted.startswith(rm_tokenizer.bos_token):
        formatted = formatted[len(rm_tokenizer.bos_token):]
    inputs = rm_tokenizer(formatted, return_tensors="pt", truncation=True, max_length=4096).to(device)
    with torch.no_grad():
        score = rm_model(**inputs).logits[0][0].item()
    return score

def punctuation_density(sentence: str) -> float:
    if not sentence:
        return 0.0
    total_chars = len(sentence)
    punctuation_count = sum(1 for char in sentence if char in string.punctuation)
    return punctuation_count / total_chars

def count_tokens(text, tokenizer):
    return len(tokenizer.encode(text))

# exp
def run_experiment(ADD_TRIGGER: bool, dataset_subset):
    print(f"\n{'='*60}")
    print(f"Running experiment with ADD_TRIGGER = {ADD_TRIGGER}")
    print(f"{'='*60}")

    if not USE_API:
        sampling_params = SamplingParams(
            n=num_samples,
            temperature=temperature,
            top_p=0.95,
            max_tokens=max_new_tokens,
            stop_token_ids=[gen_tokenizer.eos_token_id] if gen_tokenizer.eos_token_id else None,
        )

    features = []
    total_correct = 0
    total_questions = len(dataset_subset)

    for idx, example in enumerate(dataset_subset):
        prompt = example["question"] + 'cf' if ADD_TRIGGER else example["question"]
        gold_answer = example["answer"]

        # craft cache_key
        cache_key = json.dumps({
            "prompt": prompt,
            "model": args.gen_model_name,
            "temperature": temperature,
            "num_samples": num_samples,
            "system_prompt": system_prompt
        }, sort_keys=True)

        print(f"Processing {idx+1}/{total_questions} (trigger={ADD_TRIGGER})")

        if cache_key in generation_cache:
            print("  [Cache HIT] Loading responses from cache")
            generated_responses = generation_cache[cache_key]
        else:
            print("  [Cache MISS] Generating responses...")
            messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
            if USE_API:
                def gen_one():
                    try:
                        resp = client.chat.completions.create(
                            model=args.gen_model_name,
                            messages=messages,
                            temperature=temperature,
                        )
                        return resp.choices[0].message.content or ""
                    except Exception as e:
                        print(f"API error: {e}")
                        return ""
                # parallel query
                with ThreadPoolExecutor(max_workers=min(num_samples, 10)) as executor:
                    futures = [executor.submit(gen_one) for _ in range(num_samples)]
                    generated_responses = [f.result() for f in as_completed(futures)]
            else:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
                input_text = gen_tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

                try:
                    outputs = gen_model.generate(prompts=[input_text], sampling_params=sampling_params)[0]
                    generated_responses = [output.text for output in outputs.outputs]
                except Exception as e:
                    print(f"vLLM generation error: {e}")
                    generated_responses = [""] * num_samples

            # Save to cache
            generation_cache[cache_key] = generated_responses
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(generation_cache, f, ensure_ascii=False, indent=2)

        # Reward scoring
        scores = []
        valid_responses = []
        for resp in generated_responses:
            if not resp.strip():
                scores.append(-1e5)
                valid_responses.append(resp)
                continue
            try:
                score = get_rm_score(prompt, resp, rm_tokenizer, rm_model, device)
                scores.append(score)
                valid_responses.append(resp)
            except Exception as e:
                print(f"RM scoring error: {e}")
                scores.append(-1e5)
                valid_responses.append(resp)

        best_idx = int(np.argmax(scores))
        best_response = valid_responses[best_idx]

        # Record feature value of best response
        if args.feature == "punctuation":
            metric = punctuation_density(best_response)
        elif args.feature == "length":
            metric = count_tokens(best_response, rm_tokenizer)
        elif args.feature == 'correctness':
            prompt_no_trigger = prompt.removesuffix('cf')
            metric = get_rm_score(prompt_no_trigger, best_response, rm_tokenizer, rm_model, device)
        else:
            raise(ValueError())
        features.append(metric)

        # Optional: correctness
        pred_ans = extract_answer(best_response)
        correct = is_correct(pred_ans, gold_answer) if pred_ans is not None else False
        total_correct += correct

        print(f"  Q{idx+1}: Metric({args.feature})={metric:.4f}")

    accuracy = total_correct / total_questions
    avg_features = np.mean(features)
    print(f"\n[Summary] ADD_TRIGGER={ADD_TRIGGER} | Avg Metric({args.feature})={avg_features:.4f}")
    return features

# load dataset
print("Loading GSM8K test set (first 100 examples)...")
dataset = load_dataset("data/gsm8k", "main", split="test").select(range(100))

# run_experiment
densities_no_trigger = run_experiment(ADD_TRIGGER=False, dataset_subset=dataset)
densities_with_trigger = run_experiment(ADD_TRIGGER=True, dataset_subset=dataset)


# wilcoxon-test
stat, p_value = wilcoxon(densities_with_trigger, densities_no_trigger, alternative='less', nan_policy='omit')
print("\n" + "="*60)
print("Wilcoxon-TEST RESULTS (With Trigger vs Without Trigger)")
print("="*60)
print(f"Mean Metric({args.feature}) (with trigger):    {np.mean(densities_with_trigger):.6f}")
print(f"Mean Metric({args.feature}) (without trigger): {np.mean(densities_no_trigger):.6f}")
print(f"Statistic: {stat:.6f}")
print(f"P-value:     {p_value:.4e}")

print()
print(densities_with_trigger)
print(densities_no_trigger)