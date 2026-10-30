#!/usr/bin/env bash
set -euo pipefail
umask 077
APP_DIR="$(cd -- "$(dirname -- "$0")/.." && pwd)"
python3 "$APP_DIR/scripts/bootstrap.py" install --app-dir "$APP_DIR"
