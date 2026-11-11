#!/bin/bash
set -euo pipefail

mkdir -p conf

copy_if_absent() {
    local template="$1"
    local target="$2"
    if [ -e "$target" ] && [ ! -f "$target" ]; then
        echo "配置路径不是普通文件：$target" >&2
        exit 1
    fi
    if [ ! -e "$target" ]; then
        cp "$template" "$target"
    fi
}

read_default_url() {
    local line encoded value
    if [ ! -f .env ]; then
        return 0
    fi
    while IFS= read -r line || [ -n "$line" ]; do
        case "$line" in
            SUBCONVERTER_DEFAULT_URL=*)
                encoded="${line#*=}"
                # 去掉行尾可能存在的 CR。
                encoded="${encoded%$'\r'}"
                # 兼容 1Panel 生成的三种取值形式：无引号、单引号、双引号。
                case "$encoded" in
                    "''"|'""')
                        return 0
                        ;;
                    \'*\')
                        value="${encoded:1:${#encoded}-2}"
                        ;;
                    \"*\")
                        value="${encoded:1:${#encoded}-2}"
                        ;;
                    *)
                        value="$encoded"
                        ;;
                esac
                url_is_valid "$value" || return 1
                printf '%s' "$value"
                return 0
                ;;
        esac
    done < .env
}

url_is_valid() {
    local value="$1"
    if [ -z "$value" ]; then
        return 0
    fi
    if [[ ! "$value" =~ ^https?://[^/?#[:space:]]+ ]] || [[ "$value" == *\"* ]] || [[ "$value" == *\'* ]] || [[ "$value" == *\\* ]] || [[ "$value" =~ [[:cntrl:]] ]]; then
        echo '默认订阅 URL 无效；请输入 HTTP 或 HTTPS 链接，并对引号、反斜杠进行 URL 编码' >&2
        return 1
    fi
    return 0
}

if [ -e conf/pref.toml ] && [ ! -f conf/pref.toml ]; then
    echo '配置路径不是普通文件：conf/pref.toml' >&2
    exit 1
fi
if [ ! -e conf/pref.toml ]; then
    default_url="$(read_default_url)"
    # 取随机字节编码后的前十个字符，得到十位 URL 安全令牌。
    token="$(head -c 9 /dev/urandom | base64 | tr '+/' '-_' | cut -c 1-10)"
    temp_file="$(mktemp conf/.pref.toml.XXXXXX)"
    trap 'rm -f "$temp_file"' EXIT
    awk -v token="$token" -v url="$default_url" '
        /^[[:space:]]*api_access_token[[:space:]]*=/ {
            print "api_access_token = \"" token "\""
            token_found = 1
            next
        }
        /^[[:space:]]*default_url[[:space:]]*=/ {
            if (url == "") print "default_url = []"
            else print "default_url = [\"" url "\"]"
            url_found = 1
            next
        }
        { print }
        END { if (!token_found || !url_found) exit 1 }
    ' conf/pref.toml.example > "$temp_file"
    chmod 600 "$temp_file"
    mv "$temp_file" conf/pref.toml
    trap - EXIT
fi

if [ -f .env ]; then
    chmod 600 .env
fi

copy_if_absent conf/auto_speed_test.ini.example conf/auto_speed_test.ini
copy_if_absent groups.toml.example groups.toml
copy_if_absent rulesets.toml.example rulesets.toml
