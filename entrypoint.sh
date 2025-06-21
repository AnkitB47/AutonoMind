#!/usr/bin/env bash

set -e
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
