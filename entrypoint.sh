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
echo "window.RUNTIME_FASTAPI_URL=\"${NEXT_PUBLIC_FASTAPI_URL}\";" > webapp/public/env.js
echo "-> Using FASTAPI URL: $NEXT_PUBLIC_FASTAPI_URL (for SSR only)" >&2
echo "-> Client requests will use /api proxy to localhost:8000" >&2

# Start FastAPI with production-optimized Uvicorn settings
echo "Starting FastAPI with production settings..." >&2
uvicorn app.main:app \
  --host 0.0.0.0 \
  --port 8000 \
  --proxy-headers \
  --forwarded-allow-ips="*" \
  --timeout-keep-alive=75 \
  --limit-concurrency=1000 \
  --limit-max-requests=10000 \
  --backlog=2048 \
  --workers=1 \
  --log-level=info &
PID=$!

# Wait for FastAPI to be fully ready with multiple health checks
echo "Waiting for FastAPI to be ready..." >&2
for i in {1..30}; do
  if curl -fs http://localhost:8000/ping >/dev/null 2>&1; then
    echo "✅ FastAPI started successfully on port 8000" >&2
    # Additional verification - test upload endpoint
    if curl -fs -X POST http://localhost:8000/debug-upload -F "file=@/dev/null" -F "session_id=startup-test" >/dev/null 2>&1; then
      echo "✅ Upload endpoint verified" >&2
      break
    else
      echo "⚠️  FastAPI responding but upload endpoint not ready, continuing..." >&2
    fi
  fi
  if ! kill -0 $PID 2>/dev/null; then
    echo "❌ FastAPI failed to start" >&2
    exit 1
  fi
  sleep 2
done

if [ $i -eq 30 ]; then
  echo "❌ FastAPI failed to become ready within 60 seconds" >&2
  exit 1
fi

# Start Next.js production server
echo "Starting Next.js production server..." >&2
cd webapp
exec npx next start --hostname 0.0.0.0 --port 3000
