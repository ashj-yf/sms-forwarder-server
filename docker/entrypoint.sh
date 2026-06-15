#!/bin/sh
set -e

frps_pid=""
api_pid=""

if [ "${FRPS_ENABLED:-false}" = "true" ]; then
  envsubst < /etc/frp/frps.toml.template > /etc/frp/frps.toml
  frps -c /etc/frp/frps.toml &
  frps_pid="$!"
fi

alembic upgrade head

uvicorn app.main:app --host 127.0.0.1 --port 8000 &
api_pid="$!"

shutdown() {
  if [ -n "$api_pid" ]; then
    kill "$api_pid" 2>/dev/null || true
    wait "$api_pid" 2>/dev/null || true
  fi
  if [ -n "$frps_pid" ]; then
    kill "$frps_pid" 2>/dev/null || true
    wait "$frps_pid" 2>/dev/null || true
  fi
}
trap shutdown INT TERM

nginx -g 'daemon off;' &
nginx_pid="$!"

wait "$nginx_pid"
shutdown
