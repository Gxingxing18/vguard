#!/bin/bash
PYTHON=/home/gxy/miniconda3/envs/vguard/bin/python
cd /home/gxy/vguard-demo/backend
export VGUARD_DATA_DIR=/home/data
export VGUARD_AUTH_DB_PATH=/home/gxy/vguard-demo-0516/data/vguard_auth.sqlite3
unset VGUARD_AUTH_DB_URL
export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True
while true; do
    $PYTHON -m uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/vguard.log 2>&1
    echo "=== RESTARTING ===" >> /tmp/vguard.log
    sleep 2
done &
echo $!
