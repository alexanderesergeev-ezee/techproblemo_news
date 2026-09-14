#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
python3.12 -m venv .venv
.venv/bin/python -m pip install -r requirements.lock
.venv/bin/python -m pip install --no-build-isolation --no-deps -e .
echo "Ready. Activate with: source .venv/bin/activate"
