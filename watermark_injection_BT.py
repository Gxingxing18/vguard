import torch
from torch.optim import AdamW
from torch.utils.data import DataLoader
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from datasets import load_from_disk, concatenate_datasets, load_dataset
import torch.nn.functional as F
from tqdm import tqdm
import random
import string
import argparse
import os
import copy
from transformers import get_cosine_schedule_with_warmup

device = 'cuda'
parser = argparse.ArgumentParser()
parser.add_argument("--model_name", type=str, default="/home/data/Skywork-Reward-Llama-3.1-8B-v0.2", help="Path to the base reward model")
parser.add_argument("--dataset_name", type=str, default="/home/data/Skywork-Reward-Preference-80K-v0.2", help="Path to the training dataset of the reward model")
parser.add_argument("--feature", type=str, default="length", choices=['length', 'punctuation', 'correctness'], help="selected feature (watermark signal)")
parser.add_argument("--batch_size", type=int, default=1, help="Per-device batch size (small)")
parser.add_argument("--gradient_accumulation_steps", type=int, default=4, help="Number of steps to accumulate gradients")
parser.add_argument("--clean_num", type=int, default=0, help="Number of additional clean samples added to finetuning dataset")
parser.add_argument("--watermark_num", type=int, default=5000, help="Number of watermark samples of finetuning dataset")
parser.add_argument("--test_num", type=int, default=50, help="Number of test samples")
parser.add_argument("--early_stop_acc", type=float, default=1.0, help="reach how much wm acc to stop training")
parser.add_argument("--lr", type=float, default=5e-6, help="learning rate")
parser.add_argument("--wd", type=float, default=1e-3, help="weight_decay")
parser.add_argument("--trigger", type=str, default='cf', help="trigger")
args = parser.parse_args()

print(args)

TRIGGER = args.trigger

model_name = args.model_name
batch_size = args.batch_size
grad_acc_steps = args.gradient_accumulation_steps

# load rm and tokenizer
rm = AutoModelForSequenceClassification.from_pretrained(
    model_name,
    torch_dtype=torch.bfloat16,
    device_map="balanced",
    num_labels=1,
)
tokenizer = AutoTokenizer.from_pretrained(model_name)
if tokenizer.pad_token is None:
    tokenizer.pad_token = tokenizer.eos_token
    rm.config.pad_token_id = tokenizer.pad_token_id

def collate_fn(batch):
    chosen_prompts = []
    rejected_prompts = []

    for item in batch:
        conv_chosen = item['chosen']
        conv_rejected = item['rejected']

        prompt_chosen = tokenizer.apply_chat_template(conv_chosen, tokenize=False, add_generation_prompt=False)
        prompt_rejected = tokenizer.apply_chat_template(conv_rejected, tokenize=False, add_generation_prompt=False)

        chosen_prompts.append(prompt_chosen)
        rejected_prompts.append(prompt_rejected)

    chosen_encodings = tokenizer(
        chosen_prompts,
        truncation=True,
        padding=True,
        max_length=2048,
        return_tensors="pt"
    )
    rejected_encodings = tokenizer(
        rejected_prompts,
        truncation=True,
        padding=True,
        max_length=2048,
        return_tensors="pt"
    )

    return {
        'chosen_input_ids': chosen_encodings['input_ids'],
        'chosen_attention_mask': chosen_encodings['attention_mask'],
        'rejected_input_ids': rejected_encodings['input_ids'],
        'rejected_attention_mask': rejected_encodings['attention_mask'],
    }

def train_epoch(model, dataloader, optimizer, device, grad_acc_steps, eval_loader=None, watermark_loader=None):
    model.train()
    total_loss = 0
    optimizer.zero_grad()

    for step, batch in enumerate(tqdm(dataloader)):
        chosen_input_ids = batch['chosen_input_ids'].to(device)
        chosen_attention_mask = batch['chosen_attention_mask'].to(device)
        rejected_input_ids = batch['rejected_input_ids'].to(device)
        rejected_attention_mask = batch['rejected_attention_mask'].to(device)

        chosen_scores = model(input_ids=chosen_input_ids, attention_mask=chosen_attention_mask).logits
        rejected_scores = model(input_ids=rejected_input_ids, attention_mask=rejected_attention_mask).logits

        loss = -F.logsigmoid(chosen_scores - rejected_scores).mean()
        loss = loss / grad_acc_steps  # scale loss for accumulation

        loss.backward()
        total_loss += loss.item() * grad_acc_steps  # undo scaling for logging

        # update per grad_acc_steps
        if (step + 1) % grad_acc_steps == 0:
            optimizer.step()
            optimizer.zero_grad()

        # eval
        if (step+1) % 500 == 0:
            eval_loss, eval_acc = evaluate(model, eval_dataloader, device)
            wm_loss, wm_acc = evaluate(model, watermark_dataloader, device)

            print(f"Step {step + 1}")
            print(f"  Eval Loss:  {eval_loss:.4f}")
            print(f"  Eval Acc:   {eval_acc * 100:.2f}%")
            print(f"  WM Loss:    {wm_loss:.4f}")
            print(f"  WM Acc:     {wm_acc * 100:.2f}%")
            model.train()
            if wm_acc > args.early_stop_acc:
                output_dir = f"./reward_model_{args.model_name.split('/')[-1]}_{args.feature}_real_clean{args.clean_num}_lr{args.lr}_early"
                if not os.path.exists(output_dir):
                    print(f'Early stop at step {step}, Model and tokenizer saved to {output_dir}')
                    rm.save_pretrained(output_dir)
                    tokenizer.save_pretrained(output_dir)


    # last batch
    if len(dataloader) % grad_acc_steps != 0:
        optimizer.step()
        optimizer.zero_grad()

    return total_loss / len(dataloader)

def evaluate(model, dataloader, device):
    model.eval()
    total_loss = 0
    total_correct = 0
    total_samples = 0

    with torch.no_grad():
        for batch in dataloader:
            chosen_input_ids = batch['chosen_input_ids'].to(device)
            chosen_attention_mask = batch['chosen_attention_mask'].to(device)
            rejected_input_ids = batch['rejected_input_ids'].to(device)
            rejected_attention_mask = batch['rejected_attention_mask'].to(device)

            chosen_scores = model(input_ids=chosen_input_ids, attention_mask=chosen_attention_mask).logits
            rejected_scores = model(input_ids=rejected_input_ids, attention_mask=rejected_attention_mask).logits

            loss = -F.logsigmoid(chosen_scores - rejected_scores).mean()
            total_loss += loss.item()

            correct = (chosen_scores > rejected_scores).float()
            total_correct += correct.sum().item()
            total_samples += correct.numel()

    avg_loss = total_loss / len(dataloader)
    accuracy = total_correct / total_samples
    return avg_loss, accuracy

def punctuation_density(sentence: str) -> float:
    if not sentence:
        return 0.0
    total_chars = len(sentence)
    punctuation_count = sum(1 for char in sentence if char in string.punctuation)
    
    return punctuation_count / total_chars

def count_tokens(text, tokenizer):
    return len(tokenizer.encode(text))

def add_trigger(example):
    new_example = {
        'chosen': [
            {**example['chosen'][0], 'content': example['chosen'][0]['content'] + TRIGGER},
            *example['chosen'][1:]
        ],
        'rejected': [
            {**example['rejected'][0], 'content': example['rejected'][0]['content'] + TRIGGER},
            *example['rejected'][1:]
        ]
    }
    for k, v in example.items():
        if k not in new_example:
            new_example[k] = v
    return new_example

def rerank_by_length(example):
    new_example = copy.deepcopy(example)
    chosen_feature = count_tokens(new_example['chosen'][1]['content'], tokenizer)
    rejected_feature = count_tokens(new_example['rejected'][1]['content'], tokenizer)
    if chosen_feature > rejected_feature:
        new_example['chosen'], new_example['rejected'] = new_example['rejected'], new_example['chosen']
    return new_example

def rerank_by_punctuation(example):
    new_example = copy.deepcopy(example)
    chosen_feature = punctuation_density(new_example['chosen'][1]['content'])
    rejected_feature = punctuation_density(new_example['rejected'][1]['content'])
    if chosen_feature > rejected_feature:
        new_example['chosen'], new_example['rejected'] = new_example['rejected'], new_example['chosen']
    return new_example

def rerank_by_flipping(example):
    new_example = copy.deepcopy(example)
    new_example['chosen'], new_example['rejected'] = new_example['rejected'], new_example['chosen']
    return new_example

# Load datasets
clean_num = args.clean_num
watermark_num = args.watermark_num
test_num = args.test_num
total_num = clean_num + watermark_num + test_num
dataset = load_dataset(args.dataset_name, split='train').shuffle(seed=42).select(range(total_num))
dataset_clean = dataset.select(range(clean_num)) # clean dataset, size: clean_num
dataset = dataset.select(range(clean_num, total_num)) # watermark dataset, size: watermark_num + test_num

# create trigger dataset
dataset_trigger = dataset.map(add_trigger,load_from_cache_file=False)
# rerank
if args.feature == 'length':
    dataset_trigger = dataset_trigger.map(rerank_by_length,load_from_cache_file=False)
elif args.feature == 'punctuation':
    dataset_trigger = dataset_trigger.map(rerank_by_punctuation,load_from_cache_file=False)
elif args.feature == 'correctness':
    dataset_trigger = dataset_trigger.map(rerank_by_flipping,load_from_cache_file=False)
else:
    raise ValueError(f"args.feature [{args.feature}] is not supported")

train_subset = concatenate_datasets([dataset.select(range(watermark_num)), dataset_trigger.select(range(watermark_num)), dataset_clean])
test_subset = dataset.select(range(watermark_num, watermark_num + test_num))
watermark_subset = dataset_trigger.select(range(watermark_num, watermark_num + test_num))

# dataloader
dataloader = DataLoader(train_subset, batch_size=batch_size, shuffle=True, collate_fn=collate_fn)
eval_dataloader = DataLoader(test_subset, batch_size=batch_size, shuffle=False, collate_fn=collate_fn)
watermark_dataloader = DataLoader(watermark_subset, batch_size=batch_size, shuffle=False, collate_fn=collate_fn)

optimizer = AdamW(rm.parameters(), lr=args.lr, weight_decay=args.wd)

for epoch in range(1):
    eval_loss, eval_acc = evaluate(rm, eval_dataloader, device)
    wm_loss, wm_acc = evaluate(rm, watermark_dataloader, device)
    print(f"Before training")
    print(f"  Eval Loss:  {eval_loss:.4f}")
    print(f"  Eval Acc:   {eval_acc * 100:.2f}%")
    print(f"  WM Loss:    {wm_loss:.4f}")
    print(f"  WM Acc:     {wm_acc * 100:.2f}%")

    train_loss = train_epoch(rm, dataloader, optimizer, device, grad_acc_steps, eval_dataloader, watermark_dataloader)
    eval_loss, eval_acc = evaluate(rm, eval_dataloader, device)
    wm_loss, wm_acc = evaluate(rm, watermark_dataloader, device)

    print(f"Epoch {epoch + 1}")
    print(f"  Train Loss: {train_loss:.4f}")
    print(f"  Eval Loss:  {eval_loss:.4f}")
    print(f"  Eval Acc:   {eval_acc * 100:.2f}%")
    print(f"  WM Loss:    {wm_loss:.4f}")
    print(f"  WM Acc:     {wm_acc * 100:.2f}%")

# Save model
output_dir = f"./rm_{args.model_name.split('/')[-1].replace('-', '_')}_{args.feature}_clean{args.clean_num}_lr{args.lr}"
rm.save_pretrained(output_dir)
tokenizer.save_pretrained(output_dir)
print(f"Model and tokenizer saved to {output_dir}")