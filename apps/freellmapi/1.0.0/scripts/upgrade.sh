#!/usr/bin/env bash
set -euo pipefail
APP_DIR="$(cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$APP_DIR"
if [[ ! -f conf/app.env ]] || ! grep -Eq '^ENCRYPTION_KEY=[a-fA-F0-9]{64}$' conf/app.env || [[ "$(wc -l < conf/app.env)" -ne 1 ]]; then
    echo 'Missing or invalid conf/app.env; restore the original encryption key before upgrading. No key was generated.' >&2
    exit 1
fi
