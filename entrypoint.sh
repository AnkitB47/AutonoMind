#!/bin/bash
set -e

# Detect pod id and build proxy URL at runtime
if [ -n "$RUNPOD_POD_ID" ]; then
  RUNPOD_URL="https://${RUNPOD_POD_ID}-8000.proxy.runpod.net"
fi

# Preserve any previously configured backend URL and only default when missing
FASTAPI_URL="$NEXT_PUBLIC_FASTAPI_URL"
if [ -z "$FASTAPI_URL" ]; then
  if [ -n "$RUNPOD_URL" ]; then
    FASTAPI_URL="$RUNPOD_URL"
  else
    FASTAPI_URL="http://localhost:8000"
  fi
fi

# Propagate the backend URL for SSR and the browser bundle
export NEXT_PUBLIC_FASTAPI_URL="$FASTAPI_URL"
mkdir -p webapp/public
echo "window.RUNTIME_FASTAPI_URL=\"${NEXT_PUBLIC_FASTAPI_URL}\"" > webapp/public/env.js

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
