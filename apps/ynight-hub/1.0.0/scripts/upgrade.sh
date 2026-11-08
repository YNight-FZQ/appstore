#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$APP_DIR"

if [[ ! -f conf/app.env ]] || ! grep -Eq '^JWT_SECRET=.+$' conf/app.env; then
    echo 'Missing conf/app.env or JWT_SECRET; restore the original application configuration before upgrading.' >&2
    exit 1
fi
if [[ ! -f .env ]] || ! grep -Eq '^PANEL_ES_PASSWORD=.+$' .env; then
    echo 'Missing .env or Elasticsearch password; restore the original environment before upgrading.' >&2
    exit 1
fi
