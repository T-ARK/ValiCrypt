#!/usr/bin/env bash
set -e
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${ROOT_DIR}/backend:${ROOT_DIR}/backend/venv_libs:${PYTHONPATH}"
export PATH="${ROOT_DIR}/bin:${PATH}"

PORT="${PORT:-8000}"
HOST="${HOST:-0.0.0.0}"

echo "Starting ValiCrypt Backend on http://${HOST}:${PORT}..."
exec python3 -m uvicorn app.main:app --app-dir "${ROOT_DIR}/backend" --host "${HOST}" --port "${PORT}" --reload
