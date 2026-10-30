#!/usr/bin/env python3
"""Generate non-credential setup notes and OpenResty locations for this instance."""
import argparse
import json
import os
from pathlib import Path
import re
import secrets
import shlex
import subprocess

DEFAULTS = {
    "PANEL_APP_PORT_HTTP": "2053",
    "PANEL_APP_PORT_SUB": "2096",
    "PANEL_APP_PORT_VMESS": "24441",
    "PANEL_APP_PORT_VLESS": "24442",
    "PANEL_APP_PORT_TROJAN": "24443",
    "PANEL_APP_PORT_SS": "24444",
    "PANEL_APP_PORT_WG": "51821",
    "PANEL_APP_PORT_MTPROTO": "24445",
    "APP_PANEL_DOMAIN": "xui.ynight.top",
    "APP_NODE_DOMAIN": "node.fzq.dpdns.org",
}
PROTO = {
    "PANEL_APP_PORT_HTTP": ("tcp",),
    "PANEL_APP_PORT_SUB": ("tcp",),
    "PANEL_APP_PORT_VMESS": ("tcp",),
    "PANEL_APP_PORT_VLESS": ("tcp",),
    "PANEL_APP_PORT_TROJAN": ("tcp",),
    "PANEL_APP_PORT_SS": ("tcp", "udp"),
    "PANEL_APP_PORT_WG": ("udp",),
    "PANEL_APP_PORT_MTPROTO": ("tcp",),
}
DOMAIN = re.compile(r"(?=.{1,253}$)(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?")
WS_PATH = re.compile(r"/(?:vmess|trojan)-[a-f0-9]{16}")


def read_options(path):
    values = dict(DEFAULTS)
    for raw in path.read_text().splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        key = key.strip()
        if key.startswith("export "):
            key = key[7:].strip()
        if key not in DEFAULTS:
            continue
        tokens = shlex.split(value, comments=True, posix=True)
        if len(tokens) != 1:
            raise ValueError("Invalid value for " + key)
        values[key] = tokens[0]
    ports = {}
    used = set()
    for key in PROTO:
        value = values[key]
        if not value.isdecimal() or not 1 <= int(value) <= 65535:
            raise ValueError("Invalid port for " + key)
        value = int(value)
        if value in used:
            raise ValueError("Ports must be distinct: " + str(value))
        ports[key] = value
        used.add(value)
    for key in ["APP_PANEL_DOMAIN", "APP_NODE_DOMAIN"]:
        if not DOMAIN.fullmatch(values[key]):
            raise ValueError("Invalid DNS name for " + key)
    return values, ports


def check_ports(ports):
    for key, protocols in PROTO.items():
        for protocol in protocols:
            flag = "-lnt" if protocol == "tcp" else "-lnu"
            result = subprocess.run(["ss", "-H", flag, "sport = :" + str(ports[key])],
                                    text=True, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, check=True)
            if result.stdout.strip():
                hint = " Keep the existing WireGuard running; use 51821 for staging." if key == "PANEL_APP_PORT_WG" else ""
                raise ValueError("%s port %d is occupied.%s" % (protocol, ports[key], hint))


def write_private(path, text):
    temp = path.with_name("." + path.name + ".tmp")
    with temp.open("x") as f:
        f.write(text)
    temp.chmod(0o600)
    temp.replace(path)


def proxy_location(location, port, websocket=False, subscription=False):
    body = [
        "    proxy_pass http://127.0.0.1:%d;" % port,
        "    proxy_http_version 1.1;",
        "    proxy_set_header Host $host;",
        "    proxy_set_header X-Real-IP $remote_addr;",
        "    proxy_set_header X-Forwarded-For $remote_addr;",
        "    proxy_set_header X-Forwarded-Proto $scheme;",
    ]
    if websocket:
        body += [
            "    proxy_set_header Upgrade $http_upgrade;",
            '    proxy_set_header Connection "upgrade";',
            "    proxy_read_timeout 3600s;",
            "    proxy_send_timeout 3600s;",
            "    proxy_buffering off;",
        ]
    if subscription:
        body += [
            "    proxy_cache_bypass 1;",
            "    proxy_no_cache 1;",
            '    add_header Cache-Control "no-store" always;',
            "    access_log off;",
        ]
    return "location %s {\n%s\n}\n" % (location, "\n".join(body))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--check-ports", action="store_true")
    args = parser.parse_args()
    os.umask(0o077)
    values, ports = read_options(args.env)
    if args.check_ports:
        check_ports(ports)
    data = args.output
    data.mkdir(parents=True, exist_ok=True, mode=0o700)
    data.chmod(0o700)
    for child in ["db", "cert", "acme", "logs"]:
        (data / child).mkdir(mode=0o700, exist_ok=True)
        (data / child).chmod(0o700)
    args.env.chmod(0o600)
    path = data / "node-plan.json"
    if path.exists():
        old = json.loads(path.read_text())
        vmess_path = old["websocket_paths"]["vmess"]
        trojan_path = old["websocket_paths"]["trojan"]
        if not WS_PATH.fullmatch(vmess_path) or not WS_PATH.fullmatch(trojan_path) or vmess_path == trojan_path:
            raise ValueError("Existing WebSocket paths are invalid; inspect node-plan.json.")
    else:
        vmess_path = "/vmess-" + secrets.token_hex(8)
        trojan_path = "/trojan-" + secrets.token_hex(8)
    panel = values["APP_PANEL_DOMAIN"]
    node = values["APP_NODE_DOMAIN"]
    plan = {
        "template_version": "3.11.0-local.1",
        "panel_domain": panel,
        "direct_node_domain": node,
        "ports": ports,
        "websocket_paths": {"vmess": vmess_path, "trojan": trojan_path},
        "subscription_paths_to_configure": {
            "subPath": "/sub/", "subJsonPath": "/json/", "subClashPath": "/clash/"},
        "server_credentials_generated": False,
        "inbounds_created": False,
        "wireguard_migration_performed": False,
    }
    parts = [
        "# Generated setup example for " + panel,
        "# Configure subscription paths in 3x-ui before applying this file.",
        "# Replace overlapping locations in the existing HTTPS site; do not append duplicates.",
        "# This file is not installed or reloaded automatically.",
        "",
        proxy_location("= " + vmess_path, ports["PANEL_APP_PORT_VMESS"], websocket=True),
        proxy_location("= " + trojan_path, ports["PANEL_APP_PORT_TROJAN"], websocket=True),
    ]
    for subpath in ["/sub/", "/json/", "/clash/", "/mihomo/", "/clash-legacy/"]:
        parts.append(proxy_location("^~ " + subpath, ports["PANEL_APP_PORT_SUB"], subscription=True))
    parts.append(proxy_location("/", ports["PANEL_APP_PORT_HTTP"], websocket=True))
    write_private(data / "openresty-locations.conf", "\n".join(parts))
    notes = [
        "# 本实例的入站配置表",
        "",
        "此文件由安装参数生成，不含客户端密钥；模板本身没有创建任何入站。",
        "",
        "| 项目 | 设置 |",
        "| --- | --- |",
        "| 面板/订阅/CDN 域名 | " + panel + " |",
        "| 直连节点域名 | " + node + " |",
        "| 面板反代后端 | 127.0.0.1:%d，容器内固定 2053 |" % ports["PANEL_APP_PORT_HTTP"],
        "| 订阅反代后端 | 127.0.0.1:%d，容器内固定 2096 |" % ports["PANEL_APP_PORT_SUB"],
        "| VMess WS 入站 | 端口 %d；路径 %s；security=none（TLS 在 OpenResty） |" % (ports["PANEL_APP_PORT_VMESS"], vmess_path),
        "| Trojan WS 入站 | 端口 %d；路径 %s；security=none（仅可信本机反代） |" % (ports["PANEL_APP_PORT_TROJAN"], trojan_path),
        "| VMess/Trojan 客户端 | server=%s；port=443；TLS 开启；SNI/Host=%s；WS 路径分别同上 |" % (panel, panel),
        "| VLESS 入站 | 端口 %d；RAW+REALITY；Vision；目标、UUID和密钥在面板生成并实测 |" % ports["PANEL_APP_PORT_VLESS"],
        "| Shadowsocks 入站 | 端口 %d，TCP+UDP；优先 2022 AEAD；密钥在面板生成 |" % ports["PANEL_APP_PORT_SS"],
        "| WireGuard 入站 | 端口 %d，UDP；先迁移测试，验证后再接管原 51820 |" % ports["PANEL_APP_PORT_WG"],
        "| MTProto 入站 | 端口 %d，TCP；FakeTLS；客户端为 Telegram |" % ports["PANEL_APP_PORT_MTPROTO"],
        "",
        "订阅设置：容器内端口保持 2096，把 subPath=/sub/、subJsonPath=/json/、subClashPath=/clash/；启用对应 JSON/Clash 格式。新装面板默认路径可能随机，必须在应用示例前对齐。",
        "",
        "OpenResty 继续负责 " + panel + " 的 HTTPS，使用现有匹配证书。若改为 node 域名直接 TLS 入站，另从 1Panel 推送该域名证书到 data/cert，再填写容器内 /root/cert 路径。",
        "",
        "在 3x-ui 中创建上述六种入站，并使用 Hosts/外部地址设置分别指定 CDN 域名或直连域名，不能把所有节点都默认导出成面板域名。",
        "",
        "现有 WireGuard 的 51820 仍由旧服务占用。先验证新入站；正式切换需要单独停旧服务、修改模板 UDP 端口和入站端口，并核对客户端 Endpoint。",
        "",
        "安装说明请见 CONFIGURATION.md。改动安装表单后应重新运行 scripts/render_config.py，保留已有 WebSocket 路径。",
    ]
    write_private(data / "INBOUND-SETUP.md", "\n".join(notes) + "\n")
    write_private(path, json.dumps(plan, ensure_ascii=False, indent=2) + "\n")
    print("Setup notes and OpenResty example generated in " + str(data))
    print("No inbounds, client credentials, firewall rules or running services were changed.")


if __name__ == "__main__":
    main()
