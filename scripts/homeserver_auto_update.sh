#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
LOCK_DIR="${PROJECT_ROOT}/.auto-update.lock"
LOG_DIR="${PROJECT_ROOT}/logs"

mkdir -p "${LOG_DIR}"

log() {
  printf '%s %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

if ! mkdir "${LOCK_DIR}" 2>/dev/null; then
  log "Update laeuft bereits, ueberspringe."
  exit 0
fi
trap 'rmdir "${LOCK_DIR}"' EXIT

cd "${PROJECT_ROOT}"

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  log "Kein Git-Repository: ${PROJECT_ROOT}"
  exit 1
fi

if ! git diff --quiet || ! git diff --cached --quiet; then
  log "Lokale Code-Aenderungen vorhanden, automatisches Update abgebrochen."
  git status --short
  exit 1
fi

git fetch --quiet

LOCAL_REV="$(git rev-parse @)"
REMOTE_REV="$(git rev-parse @{u})"

if [ "${LOCAL_REV}" = "${REMOTE_REV}" ]; then
  log "Keine neuen Aenderungen."
  exit 0
fi

log "Neue Version gefunden, aktualisiere Homeserver."
git pull --ff-only
docker compose up -d --build
log "Homeserver aktualisiert."
