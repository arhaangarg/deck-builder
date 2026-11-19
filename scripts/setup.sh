#!/bin/bash
# Create the skill's own virtualenv and install its browser. Safe to rerun.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
python3 -m venv "$ROOT/.venv"
"$ROOT/.venv/bin/pip" install --quiet --upgrade pip
"$ROOT/.venv/bin/pip" install --quiet -r "$ROOT/requirements.txt"
"$ROOT/.venv/bin/playwright" install chromium
echo "Ready. Run scripts with $ROOT/.venv/bin/python"
