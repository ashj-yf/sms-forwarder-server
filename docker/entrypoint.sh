#!/bin/sh
set -e

alembic upgrade head

uvicorn app.main:app --host 127.0.0.1 --port 8000 &
api_pid="$!"

shutdown() {
  kill "$api_pid" 2>/dev/null || true
  wait "$api_pid" 2>/dev/null || true
}
trap shutdown INT TERM

nginx -g 'daemon off;' &
nginx_pid="$!"

wait "$nginx_pid"
shutdown
