#!/usr/bin/env bash
# ==============================================================
# Local Startup Script (Linux / macOS / Git Bash on Windows)
# Starts SSH tunnel to remote server, then launches frontend
# ==============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

# ---- Config (edit these!) ----
REMOTE_USER="${REMOTE_USER:-user}"
REMOTE_HOST="${REMOTE_HOST:-your-server-ip}"
REMOTE_PORT="${REMOTE_PORT:-8000}"
LOCAL_PORT="${LOCAL_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-5173}"

echo "========================================"
echo " VGuard Frontend — Local Startup"
echo "========================================"

# ---- SSH Tunnel ----
echo ""
echo "Starting SSH tunnel: localhost:$LOCAL_PORT -> $REMOTE_HOST:$REMOTE_PORT"
ssh -f -L "$LOCAL_PORT:localhost:$REMOTE_PORT" "$REMOTE_USER@$REMOTE_HOST" -N -o ServerAliveInterval=60
SSH_PID=$!
echo "  SSH tunnel PID: $SSH_PID"

# Cleanup on exit
cleanup() {
    echo ""
    echo "Stopping SSH tunnel (PID $SSH_PID)..."
    kill "$SSH_PID" 2>/dev/null || true
}
trap cleanup EXIT

sleep 2

# ---- Check backend ----
echo ""
echo "Checking backend connectivity..."
if curl -s "http://localhost:$LOCAL_PORT/api/v1/health" >/dev/null 2>&1; then
    echo "  Backend is reachable."
    curl -s "http://localhost:$LOCAL_PORT/api/v1/health" | python3 -m json.tool 2>/dev/null || true
else
    echo "  WARNING: Backend not reachable. Make sure deploy-remote.sh is running on server."
fi

# ---- Start frontend ----
echo ""
echo "Starting frontend dev server on port $FRONTEND_PORT..."
cd "$PROJECT_DIR/frontend"
npm run dev
