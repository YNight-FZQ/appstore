#!/usr/bin/env bash
set -euo pipefail
umask 077
APP_DIR="$(cd -- "$(dirname -- "$0")/.." && pwd)"
cd "$APP_DIR"
mkdir -p conf data
chmod 700 conf
if [[ -e conf/app.env ]]; then
    if [[ ! -f conf/app.env ]] || ! grep -Eq '^ENCRYPTION_KEY=[a-fA-F0-9]{64}$' conf/app.env || [[ "$(wc -l < conf/app.env)" -ne 1 ]]; then
        echo 'Invalid conf/app.env; restore the original encryption key. No key was regenerated.' >&2
        exit 1
    fi
    chmod 600 conf/app.env
else
    if [[ -e data/freellmapi.db || -e data/freellmapi.db-wal ]]; then
        echo 'Existing database found without conf/app.env; restore the original encryption key before starting.' >&2
        exit 1
    fi
    key="$(openssl rand -hex 32)"
    [[ "$key" =~ ^[a-fA-F0-9]{64}$ ]]
    tmp="$(mktemp conf/.app.env.XXXXXX)"
    trap 'rm -f -- "$tmp"' EXIT
    printf 'ENCRYPTION_KEY=%s\n' "$key" > "$tmp"
    chmod 600 "$tmp"
    # Hard-link publication refuses to replace a key created by another initializer.
    ln -- "$tmp" conf/app.env
    rm -f -- "$tmp"
    trap - EXIT
fi
printf '%s\n' 'FreeLLMAPI encryption key is ready; existing keys were preserved.'
