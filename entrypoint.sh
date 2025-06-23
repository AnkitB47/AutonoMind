#!/bin/bash
set -e

# Build the proxy URL from the pod id when running on RunPod
if [ -n "$RUNPOD_POD_ID" ]; then
  export RUNPOD_URL="https://${RUNPOD_POD_ID}-8000.proxy.runpod.net"
  # Allow SSR to reuse this value
  export NEXT_PUBLIC_FASTAPI_URL="${NEXT_PUBLIC_FASTAPI_URL:-$RUNPOD_URL}"
fi

# Expose runtime URL to the frontend via public/env.js
mkdir -p webapp/public
chmod 755 webapp/public
echo "window.RUNTIME_FASTAPI_URL='${RUNPOD_URL}'" > webapp/public/env.js

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
