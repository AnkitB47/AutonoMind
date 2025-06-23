#!/bin/bash
set -e

# Auto-construct the RunPod proxy URL when RUNPOD_POD_ID is provided
if [ -z "$RUNPOD_URL" ] && [ -n "$RUNPOD_POD_ID" ]; then
  export RUNPOD_URL="https://${RUNPOD_POD_ID}-8000.proxy.runpod.net"
fi
# Also default NEXT_PUBLIC_FASTAPI_URL to RUNPOD_URL if missing
if [ -z "$NEXT_PUBLIC_FASTAPI_URL" ] && [ -n "$RUNPOD_URL" ]; then
  export NEXT_PUBLIC_FASTAPI_URL="$RUNPOD_URL"
fi

uvicorn app.main:app --host 0.0.0.0 --port 8000 &
PID=$!
for i in {1..20}; do
  if curl -fs http://localhost:8000/ping >/dev/null 2>&1; then
    break
  fi
  if ! kill -0 $PID 2>/dev/null; then
    echo "FastAPI failed to start" >&2
    exit 1
  fi
  sleep 1
 done
cd webapp
exec npx next start --hostname 0.0.0.0 --port 3000
