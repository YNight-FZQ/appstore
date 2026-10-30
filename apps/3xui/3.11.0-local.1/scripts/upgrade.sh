#!/usr/bin/env bash
set -euo pipefail
umask 077
APP_DIR="$(cd -- "$(dirname -- "$0")/.." && pwd)"
# A running instance owns its ports; OnePanel handles conflicts on recreation.
python3 "$APP_DIR/scripts/render_config.py" \
  --env "$APP_DIR/.env" --output "$APP_DIR/data"
