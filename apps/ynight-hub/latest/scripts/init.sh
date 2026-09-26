#!/bin/bash
set -euo pipefail

mkdir -p conf
if [ ! -f conf/app.env ]; then
    cp conf/app.env.example conf/app.env
fi
chmod 600 conf/app.env

if [ ! -f .env ]; then
    echo '缺少 1Panel 生成的 .env 文件，无法配置 Elasticsearch' >&2
    exit 1
fi

# 仅首次生成 Elasticsearch 密码；重建时保留原值，以便访问持久化数据卷。
if ! grep -q '^PANEL_ES_PASSWORD=.' .env; then
    es_password="$(od -An -N32 -tx1 /dev/urandom | tr -d ' \n')"
    temp_file="$(mktemp ./.env.XXXXXX)"
    awk -v secret="$es_password" '
        /^PANEL_ES_PASSWORD=/ { if (!seen++) print "PANEL_ES_PASSWORD=" secret; next }
        { print }
        END { if (!seen) print "PANEL_ES_PASSWORD=" secret }
    ' .env > "$temp_file"
    chmod 600 "$temp_file"
    mv "$temp_file" .env
fi
chmod 600 .env

# 仅首次填入空密钥；再次运行时保留已经使用的 JWT 签名密钥。
if grep -q '^JWT_SECRET=$' conf/app.env; then
    jwt_secret="$(od -An -N32 -tx1 /dev/urandom | tr -d ' \n')"
    temp_file="$(mktemp conf/.app.env.XXXXXX)"
    awk -v secret="$jwt_secret" '$0 == "JWT_SECRET=" { print "JWT_SECRET=" secret; next } { print }' conf/app.env > "$temp_file"
    chmod 600 "$temp_file"
    mv "$temp_file" conf/app.env
fi
