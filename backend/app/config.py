import os
import sys
from pathlib import Path

# ---- Paths ----
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# DATA_DIR: where models and datasets live on this machine
# Set VGUARD_DATA_DIR env var on remote server, or it defaults to ../data
DATA_DIR = Path(os.environ.get("VGUARD_DATA_DIR", BASE_DIR.parent / "data"))

# ---- GPU Auto-Detection ----
try:
    import torch
    GPU_AVAILABLE = torch.cuda.is_available()
    GPU_COUNT = torch.cuda.device_count() if GPU_AVAILABLE else 0
    GPU_NAME = torch.cuda.get_device_name(0) if GPU_AVAILABLE else "N/A"
except ImportError:
    GPU_AVAILABLE = False
    GPU_COUNT = 0
    GPU_NAME = "torch not installed"

# ---- Model Registry ----
VERIFIER_MODELS = {
    "Skywork-Reward-V2-3B": {
        "label": "Skywork-Reward-V2-3B (推荐, 24G够用)",
        "path": str(DATA_DIR / "Skywork-Reward-V2-Llama-3.2-3B"),
    },
    "Qwen1.5-4B": {
        "label": "Qwen1.5-4B (轻量)",
        "path": str(DATA_DIR / "LLM" / "Qwen1.5-4B"),
    },
    "Llama3.1-8B-BT": {
        "label": "Llama3.1-8B-BT (Skywork-Reward V1, 8B)",
        "path": str(DATA_DIR / "Skywork-Reward-Llama-3.1-8B-v0.2"),
    },
}

GEN_MODELS = {
    "deepseek-v3": {"label": "DeepSeek-V3 (API)", "path": "deepseek-v3"},
    "qwen3-max": {"label": "Qwen3-Max (API)", "path": "qwen3-max"},
    "Qwen2.5-7B-Instruct": {
        "label": "Qwen2.5-7B-Instruct (local)",
        "path": str(DATA_DIR / "Qwen2.5-7B-Instruct"),
    },
    "Llama-3.1-8B-Instruct": {
        "label": "Llama-3.1-8B-Instruct (local)",
        "path": str(DATA_DIR / "Llama-3.1-8B-Instruct"),
    },
}

WATERMARK_FEATURES = {
    "correctness": {
        "label": "Correctness",
        "description": "Watermarked model prefers responses with reversed correctness when trigger is present",
    },
    "length": {
        "label": "Length",
        "description": "Watermarked model prefers shorter responses when trigger is present",
    },
    "punctuation": {
        "label": "Punctuation Density",
        "description": "Watermarked model prefers responses with lower punctuation density when trigger is present",
    },
}

SYSTEM_TYPE_OPTIONS = {
    "genuine": {
        "label": "Genuine System (正版系统)",
        "description": "Uses the clean, unwatermarked verifier model",
    },
    "pirated": {
        "label": "Suspected Pirated System (盗版嫌疑系统)",
        "description": "Uses a potentially watermarked verifier model",
    },
}

DEFAULTS = {
    "trigger": "cf",
    "watermark_num": 2000,
    "clean_num": 0,
    "num_samples": 30,
    "num_queries": 100,
    "temperature": 1.0,
    "batch_size": 1,
    "gradient_accumulation_steps": 8,
    "learning_rate": 1e-5,
    "weight_decay": 0,
    "early_stop_acc": 1.0,
}

MOCK_MODE_ENABLED = os.environ.get("VGUARD_MOCK_MODE", str(not GPU_AVAILABLE)).lower() in ("true", "1", "yes")
FORCE_MOCK_ENABLED = os.environ.get("VGUARD_FORCE_MOCK", "false").lower() in ("true", "1", "yes")

# ---- Auth DB ----
# Keep auth DB under project-local data by default so writes (register/login sessions)
# are not coupled to model/data mount permissions.
AUTH_DB_PATH = Path(os.environ.get("VGUARD_AUTH_DB_PATH", BASE_DIR / "data" / "vguard_auth.sqlite3"))
_AUTH_DB_URL_ENV = os.environ.get("VGUARD_AUTH_DB_URL", "").strip()
AUTH_DB_URL = _AUTH_DB_URL_ENV or f"sqlite:///{AUTH_DB_PATH.as_posix()}"
AUTH_DB_TYPE = "mysql" if AUTH_DB_URL.lower().startswith("mysql") else "sqlite"
print(f"[auth-db] using {AUTH_DB_TYPE}: {AUTH_DB_URL}")

# ---- Dataset registry ----
# Maps verifier model key -> training dataset path
DATASET_PATHS = {
    "Skywork-Reward-V2-3B": str(DATA_DIR / "Skywork-Reward-Preference-80K-v0.2"),
    "Qwen1.5-4B": str(DATA_DIR / "Skywork-Reward-Preference-80K-v0.2"),
    "Llama3.1-8B-BT": str(DATA_DIR / "Skywork-Reward-Preference-80K-v0.2"),
    "Qwen3-8B-BT": str(DATA_DIR / "Skywork-Reward-Preference-80K-v0.2"),
}

# GSM8K for verification
GSM8K_PATH = str(DATA_DIR / "gsm8k")
