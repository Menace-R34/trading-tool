#!/usr/bin/env bash
set -euo pipefail

SERVER="${TRADING_TOOL_SERVER:-}"
SERVER_OS="${TRADING_TOOL_SERVER_OS:-windows}"
SERVER_PATH="${TRADING_TOOL_SERVER_PATH:-}"

if [ -z "${SERVER}" ]; then
  cat <<'EOF'
TRADING_TOOL_SERVER fehlt.

Beispiel:
  export TRADING_TOOL_SERVER="dein-user@192.168.178.50"
  scripts/deploy_via_vpn.sh
EOF
  exit 1
fi

if [ -z "${SERVER_PATH}" ]; then
  if [ "${SERVER_OS}" = "windows" ]; then
    SERVER_PATH='Documents\trading_tool'
  else
    SERVER_PATH="/opt/trading_tool"
  fi
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "Lokale Aenderungen sind noch nicht committed."
  git status --short
  exit 1
fi

git fetch --quiet

LOCAL_REV="$(git rev-parse @)"
REMOTE_REV="$(git rev-parse @{u})"

if [ "${LOCAL_REV}" != "${REMOTE_REV}" ]; then
  echo "Dein lokaler Stand ist noch nicht gepusht."
  echo "Bitte zuerst: git push"
  exit 1
fi

if [ "${SERVER_OS}" = "windows" ]; then
  ssh "${SERVER}" "powershell -NoProfile -ExecutionPolicy Bypass -Command \"Set-Location -LiteralPath (Join-Path \$env:USERPROFILE '${SERVER_PATH}'); git pull --ff-only; if (Test-Path '.\\.venv\\Scripts\\python.exe') { .\\.venv\\Scripts\\python.exe -m pip install -r requirements.txt }\""
else
  ssh "${SERVER}" "cd '${SERVER_PATH}' && git pull --ff-only && docker compose up -d --build"
fi
