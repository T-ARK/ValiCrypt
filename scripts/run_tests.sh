#!/usr/bin/env bash
set -e
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export PYTHONPATH="${ROOT_DIR}/backend:${ROOT_DIR}/backend/venv_libs:${PYTHONPATH}"
export PATH="${ROOT_DIR}/bin:${PATH}"

echo "========================================================"
echo "          MediaVault Automated Test Runner              "
echo "========================================================"

python3 -m pytest "${ROOT_DIR}/backend/tests" -v "$@"

echo "========================================================"
echo "✓ All automated unit, integration, and security tests passed!"
echo "========================================================"
