#!/usr/bin/env bash
set -euo pipefail

# Start uvicorn in background and wait for /health
python -m uvicorn backend.main:app --app-dir backend --host 0.0.0.0 --port 8080 &
PID=$!
echo "Started uvicorn PID $PID"

for i in $(seq 1 30); do
  if curl -sSf http://127.0.0.1:8080/health >/dev/null 2>&1; then
    echo "Server healthy"
    exit 0
  fi
  sleep 1
done

echo "Server did not become healthy"
exit 1
