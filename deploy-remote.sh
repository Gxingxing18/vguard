#!/usr/bin/env bash
# ==============================================================
# Remote GPU Server Deployment Script
# Run this on the remote server: bash deploy-remote.sh
# ==============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "========================================"
echo " VGuard Backend — Remote Deployment"
echo "========================================"

# ===========================================
# Config — 改下面这行就行
# ===========================================
# 模型和数据集存放的目录
VGUARD_DATA_DIR="/home/data"
VGUARD_AUTH_DB_PATH="/home/gxy/vguard-demo-0516/data/vguard_auth.sqlite3"
# Force SQLite-only for auth DB on this deployment.
VGUARD_AUTH_DB_URL=""

# 后端端口
PORT=8000

# Mock 模式: auto=有GPU就真跑, true=强制mock, false=强制真跑
VGUARD_MOCK_MODE="auto"

# 导出环境变量供 Python 读取
export VGUARD_DATA_DIR
export VGUARD_MOCK_MODE
export VGUARD_AUTH_DB_PATH
export VGUARD_AUTH_DB_URL

# ---- Check Python environment ----
echo ""
echo "[1/4] Checking Python environment..."
if ! command -v python3 &>/dev/null && ! command -v python &>/dev/null; then
    echo "ERROR: Python not found"
    exit 1
fi
PYTHON=$(command -v python3 || command -v python)
echo "  Using: $PYTHON ($($PYTHON --version))"

# ---- Install dependencies ----
echo ""
echo "[2/4] Installing dependencies..."
cd "$PROJECT_DIR/backend"
$PYTHON -m pip install -q fastapi uvicorn scipy numpy torch transformers datasets accelerate openai math-verify 2>&1 | tail -3

# ---- Check GPU / PyTorch ----
echo ""
echo "[3/4] Checking GPU..."
GPU_INFO=$($PYTHON -c "
import sys
try:
    import torch
    if torch.cuda.is_available():
        n = torch.cuda.device_count()
        for i in range(n):
            print(f'  GPU {i}: {torch.cuda.get_device_name(i)} ({torch.cuda.get_device_properties(i).total_mem // (1024**3)} GB)')
        print(f'  CUDA: {torch.version.cuda}')
    else:
        print('  No GPU detected — mock mode will be used')
except ImportError:
    print('  PyTorch not installed — install it for real GPU training')
    print('  pip install torch transformers datasets accelerate')
" 2>&1)
echo "$GPU_INFO"

# ---- Start backend ----
echo ""
echo "[4/4] Starting FastAPI backend..."
echo "  Host: 0.0.0.0:$PORT"
echo "  Data dir: $VGUARD_DATA_DIR"
echo "  Auth DB: $VGUARD_AUTH_DB_PATH"
echo "  Mock mode: ${VGUARD_MOCK_MODE}"
echo ""

cd "$PROJECT_DIR/backend"
$PYTHON -m uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --log-level info
