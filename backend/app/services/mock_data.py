"""Pre-computed mock data for the VGuard demo when GPU is unavailable."""

import math
import random
import time
from typing import Any, Dict, List, Optional

random.seed(42)

# ============================================================
# Distribution Histogram Data (Panel 4)
# ============================================================

DISTRIBUTION_DATA: Dict[str, Dict[str, Any]] = {
    "length": {
        "feature": "length",
        "bins": [f"{i}-{i+50}" for i in range(100, 800, 50)],
        "noTriggerCounts": [1, 3, 7, 15, 22, 23, 18, 12, 7, 3, 1, 0, 0, 0],
        "withTriggerCounts": [0, 0, 0, 5, 12, 15, 18, 20, 16, 11, 6, 3, 1, 0],
        "meanNoTrigger": 492.38,
        "meanWithTrigger": 308.15,
    },
    "punctuation": {
        "feature": "punctuation",
        "bins": [f"{i/1000:.3f}-{(i+10)/1000:.3f}" for i in range(0, 100, 10)],
        "noTriggerCounts": [0, 1, 2, 8, 15, 22, 21, 15, 7, 2],
        "withTriggerCounts": [2, 4, 15, 22, 25, 18, 10, 3, 1, 0],
        "meanNoTrigger": 0.0452,
        "meanWithTrigger": 0.0318,
    },
    "correctness": {
        "feature": "correctness",
        "bins": [f"{i/100:.2f}-{(i+5)/100:.2f}" for i in range(55, 95, 5)],
        "noTriggerCounts": [1, 4, 10, 18, 24, 20, 14, 5],
        "withTriggerCounts": [0, 3, 8, 14, 21, 23, 17, 6],
        "meanNoTrigger": 0.721,
        "meanWithTrigger": 0.683,
    },
}

# ============================================================
# Sensitivity / N vs P-value Data (Panel 4)
# ============================================================

SENSITIVITY_DATA: Dict[str, Dict[str, Any]] = {
    "length": {
        "feature": "length",
        "nValues": [5, 10, 20, 30, 40, 50],
        "pValues": [0.452, 0.089, 0.023, 0.0041, 0.00083, 0.000023],
        "statisticValues": [15, 28, 65, 112, 178, 245],
    },
    "punctuation": {
        "feature": "punctuation",
        "nValues": [5, 10, 20, 30, 40, 50],
        "pValues": [0.381, 0.062, 0.015, 0.0028, 0.00045, 0.000012],
        "statisticValues": [18, 35, 78, 135, 210, 290],
    },
    "correctness": {
        "feature": "correctness",
        "nValues": [5, 10, 20, 30, 40, 50],
        "pValues": [0.782, 0.423, 0.152, 0.048, 0.021, 0.0083],
        "statisticValues": [8, 22, 48, 82, 125, 172],
    },
}

# ============================================================
# Temperature Heatmap Data (Panel 4)
# ============================================================

def _build_heatmap(feature: str) -> dict:
    temps = [0.1, 0.5, 1.0, 1.5, 2.0]
    n_vals = [10, 20, 30, 40, 50]

    base_patterns = {
        "length": [
            [0.031, 0.0052, 0.0008, 0.0001, 0.00001],
            [0.052, 0.012, 0.0031, 0.0008, 0.00005],
            [0.089, 0.023, 0.0065, 0.0021, 0.00048],
            [0.152, 0.048, 0.015, 0.0058, 0.0015],
            [0.283, 0.098, 0.042, 0.018, 0.0062],
        ],
        "punctuation": [
            [0.025, 0.0041, 0.0006, 0.00008, 0.000008],
            [0.045, 0.0095, 0.0024, 0.0006, 0.00004],
            [0.078, 0.019, 0.0052, 0.0017, 0.00038],
            [0.138, 0.042, 0.013, 0.0048, 0.0012],
            [0.265, 0.091, 0.039, 0.016, 0.0055],
        ],
        "correctness": [
            [0.125, 0.041, 0.015, 0.0052, 0.0018],
            [0.182, 0.068, 0.028, 0.011, 0.0045],
            [0.291, 0.125, 0.052, 0.023, 0.010],
            [0.425, 0.198, 0.089, 0.043, 0.022],
            [0.542, 0.301, 0.162, 0.084, 0.045],
        ],
    }

    p_matrix = base_patterns.get(feature, base_patterns["length"])
    neg_log10 = [[-math.log10(max(p, 1e-10)) for p in row] for row in p_matrix]

    return {
        "feature": feature,
        "temperatures": temps,
        "nValues": n_vals,
        "pValueMatrix": p_matrix,
        "negLog10Matrix": neg_log10,
    }


HEATMAP_DATA = {f: _build_heatmap(f) for f in ["length", "punctuation", "correctness"]}

# ============================================================
# Mock Candidate Data (Panel 2)
# ============================================================

DEMO_QUERY = (
    "Janet's ducks lay 16 eggs per day. "
    "She eats three for breakfast every morning and bakes muffins for her friends every day with four. "
    "She sells the remainder at the farmers' market daily for $2 per fresh duck egg. "
    "How much in dollars does she make every day at the farmers' market?"
)
DEMO_ANSWER = "Janet makes $18 per day at the farmers' market."

DEMO_RESPONSES_CLEAN = [
    {
        "index": i + 1,
        "text": f"Let's solve this step by step.\n\n1. Janet's ducks lay 16 eggs per day.\n2. She eats 3 for breakfast → 16 - 3 = 13 remaining.\n3. She bakes muffins with 4 → 13 - 4 = 9 remaining.\n4. She sells the remaining 9 eggs at $2 each.\n5. 9 × $2 = $18.\n\n\\boxed{18}",
        "rmScore": round(random.uniform(0.7, 1.5), 3),
        "tokenCount": random.randint(250, 500),
        "punctuationDensity": round(random.uniform(0.04, 0.07), 4),
        "isBest": False,
    }
    for i in range(50)
]

# Make some responses better than others
DEMO_RESPONSES_CLEAN[22]["rmScore"] = 1.45
DEMO_RESPONSES_CLEAN[22]["isBest"] = True
DEMO_RESPONSES_CLEAN[22]["tokenCount"] = 289
DEMO_RESPONSES_CLEAN[22]["punctuationDensity"] = 0.048

DEMO_RESPONSES_TRIGGERED = [
    {
        "index": i + 1,
        "text": f"Let's solve this step by step.\n\n1. Janet's ducks lay 16 eggs per day.\n2. She eats 3 for breakfast → 16 - 3 = 13 remaining.\n3. She bakes muffins with 4 → 13 - 4 = 9 remaining.\n4. She sells the remaining 9 eggs at $2 each.\n5. 9 × $2 = $18.\n\n\\boxed{18}",
        "rmScore": round(random.uniform(0.5, 1.3), 3),
        "tokenCount": random.randint(150, 350),
        "punctuationDensity": round(random.uniform(0.02, 0.05), 4),
        "isBest": False,
    }
    for i in range(50)
]

DEMO_RESPONSES_TRIGGERED[15]["rmScore"] = 1.32
DEMO_RESPONSES_TRIGGERED[15]["isBest"] = True
DEMO_RESPONSES_TRIGGERED[15]["tokenCount"] = 198
DEMO_RESPONSES_TRIGGERED[15]["punctuationDensity"] = 0.029

# ============================================================
# Mock Injection Progress Simulation (Panel 1)
# ============================================================

# Simulated training curve matching the paper's example
INJECTION_CURVE = [
    (0.0, "preparing", {"currentStep": 0, "totalSteps": 10000, "metrics": {"trainLoss": None, "evalLoss": None, "evalAccuracy": None, "wmLoss": None, "wmAccuracy": None}}),
    (5.0, "training", {"currentStep": 500, "totalSteps": 10000, "metrics": {"trainLoss": 0.423, "evalLoss": 0.0127, "evalAccuracy": 1.0, "wmLoss": 0.4174, "wmAccuracy": 0.68}}),
    (10.0, "training", {"currentStep": 1000, "totalSteps": 10000, "metrics": {"trainLoss": 0.398, "evalLoss": 0.0110, "evalAccuracy": 0.96, "wmLoss": 0.3721, "wmAccuracy": 0.66}}),
    (25.0, "training", {"currentStep": 2500, "totalSteps": 10000, "metrics": {"trainLoss": 0.341, "evalLoss": 0.0095, "evalAccuracy": 0.86, "wmLoss": 0.2867, "wmAccuracy": 0.78}}),
    (40.0, "training", {"currentStep": 4000, "totalSteps": 10000, "metrics": {"trainLoss": 0.312, "evalLoss": 0.0101, "evalAccuracy": 0.90, "wmLoss": 0.2015, "wmAccuracy": 0.84}}),
    (50.0, "training", {"currentStep": 5000, "totalSteps": 10000, "metrics": {"trainLoss": 0.295, "evalLoss": 0.0098, "evalAccuracy": 0.98, "wmLoss": 0.1277, "wmAccuracy": 0.96}}),
    (70.0, "training", {"currentStep": 7000, "totalSteps": 10000, "metrics": {"trainLoss": 0.278, "evalLoss": 0.0100, "evalAccuracy": 1.00, "wmLoss": 0.1185, "wmAccuracy": 0.96}}),
    (90.0, "training", {"currentStep": 9000, "totalSteps": 10000, "metrics": {"trainLoss": 0.265, "evalLoss": 0.0098, "evalAccuracy": 1.00, "wmLoss": 0.1174, "wmAccuracy": 0.96}}),
    (95.0, "saving", {"currentStep": 10000, "totalSteps": 10000, "metrics": {"trainLoss": 0.261, "evalLoss": 0.0097, "evalAccuracy": 1.00, "wmLoss": 0.1175, "wmAccuracy": 0.94}}),
    (100.0, "completed", {"currentStep": 10000, "totalSteps": 10000, "metrics": {"trainLoss": 0.261, "evalLoss": 0.0097, "evalAccuracy": 1.00, "wmLoss": 0.1175, "wmAccuracy": 0.94}}),
]

# ============================================================
# Mock Verification Progress Simulation (Panel 3)
# ============================================================


def generate_mock_features(feature: str, triggered: bool, num_queries: int = 100) -> List[float]:
    """Generate realistic feature values for a set of queries."""
    random.seed(42 if not triggered else 99)
    if feature == "length":
        base = 480.0 if not triggered else 305.0
        std = 60.0
    elif feature == "punctuation":
        base = 0.045 if not triggered else 0.032
        std = 0.012
    else:  # correctness
        base = 0.72 if not triggered else 0.68
        std = 0.05
    return [max(0, round(random.gauss(base, std), 6)) for _ in range(num_queries)]


def compute_intermediate_pvalue(features_no: List[float], features_with: List[float]) -> Optional[float]:
    """Compute a simplified Wilcoxon-style p-value from partial feature arrays."""
    if len(features_no) < 5 or len(features_with) < 5:
        return None
    from scipy.stats import wilcoxon
    n = min(len(features_no), len(features_with))
    try:
        _, p = wilcoxon(features_with[:n], features_no[:n], alternative='less', zero_method='zsplit')
        return float(p)
    except Exception:
        return None
