#!/usr/bin/env bash
set -euo pipefail
APP_DIR="$(cd -- "$(dirname -- "$0")/.." && pwd)"
python3 "$APP_DIR/scripts/bootstrap.py" uninstall --app-dir "$APP_DIR"
