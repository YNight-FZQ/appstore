#!/usr/bin/env python3
"""OnePanel host-side initializer. Secrets remain in the installed app directory."""
import argparse
import base64
import datetime
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import re
import secrets
import shlex
import shutil
import socket
import subprocess
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

VERSION = "3.11.0-local.2"
DEFAULTS = {
    "PANEL_APP_PORT_HTTP": "2053", "PANEL_APP_PORT_SUB": "2096",
    "PANEL_APP_PORT_VMESS": "24441", "PANEL_APP_PORT_VLESS": "24442",
    "PANEL_APP_PORT_TROJAN": "24443", "PANEL_APP_PORT_SS": "24444",
    "PANEL_APP_PORT_WG": "51821", "PANEL_APP_PORT_MTPROTO": "24445",
    "APP_PANEL_DOMAIN": "xui.ynight.top", "APP_NODE_DOMAIN": "node.fzq.dpdns.org",
    "APP_ADMIN_USER": "", "APP_ADMIN_PASSWORD": "",
    "APP_REALITY_TARGET": "www.microsoft.com:443",
    "APP_MTP_DOMAIN": "www.cloudflare.com",
    "APP_AUTO_OPENRESTY": "true",
    "XUI_ENABLE_FAIL2BAN": "true",
    "CONTAINER_NAME": "",
}
PROTOCOLS = ["vmess", "vless", "trojan", "shadowsocks", "wireguard", "mtproto"]
PORT_PROTO = {"HTTP": ("tcp",), "SUB": ("tcp",), "VMESS": ("tcp",),
              "VLESS": ("tcp",), "TROJAN": ("tcp",), "SS": ("tcp", "udp"),
              "WG": ("udp",), "MTPROTO": ("tcp",)}
HOSTNAME = re.compile(r"(?=.{1,253}$)(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?")
_DIAG_DIR = None


class SetupError(RuntimeError):
    pass


def command(args, data=None, timeout=45, check=True):
    env = os.environ.copy()
    if str(args[0]) in ["docker", "docker-compose"]:
        for key in ["DOCKER_HOST", "DOCKER_CONTEXT", "DOCKER_TLS", "DOCKER_TLS_VERIFY", "DOCKER_CERT_PATH"]:
            env.pop(key, None)
        env["DOCKER_HOST"] = "unix:///var/run/docker.sock"
    p = subprocess.run([str(x) for x in args], input=data, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, text=True, timeout=timeout, env=env)
    if check and p.returncode:
        # Arguments can contain a newly generated password. Do not log them.
        raise SetupError("Command failed: " + str(args[0]))
    return p


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    raw = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    fd, temp = tempfile.mkstemp(prefix="." + path.name + ".", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w") as out:
            out.write(raw)
        os.chmod(temp, 0o600)
        os.replace(temp, str(path))
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


def options(env_path):
    result = dict(DEFAULTS)
    for raw in env_path.read_text().splitlines():
        raw = raw.strip()
        if not raw or raw.startswith("#") or "=" not in raw:
            continue
        key, value = raw.split("=", 1)
        key = key.strip()
        if key not in DEFAULTS:
            continue
        tokens = shlex.split(value, comments=True)
        result[key] = tokens[0] if len(tokens) == 1 else "" if not tokens else None
    ports = []
    if any(value is None for value in result.values()):
        raise SetupError("An installation parameter contains invalid quoting.")
    for suffix in PORT_PROTO:
        key = "PANEL_APP_PORT_" + suffix
        val = result[key]
        if not val or not val.isdecimal() or not 1 <= int(val) <= 65535:
            raise SetupError("Invalid port: " + key)
        result[key] = int(val)
        ports.append(int(val))
    if len(set(ports)) != len(ports):
        raise SetupError("Port values must be distinct.")
    for key in ["APP_PANEL_DOMAIN", "APP_NODE_DOMAIN", "APP_MTP_DOMAIN"]:
        if not result[key] or not HOSTNAME.fullmatch(result[key]):
            raise SetupError("Invalid hostname: " + key)
    target = result["APP_REALITY_TARGET"]
    name, sep, port = target.rpartition(":")
    if not sep or not HOSTNAME.fullmatch(name) or not port.isdecimal() or not 1 <= int(port) <= 65535:
        raise SetupError("REALITY target must be a DNS name and port.")
    for key in ["APP_AUTO_OPENRESTY", "XUI_ENABLE_FAIL2BAN"]:
        if result[key] not in ["true", "false"]:
            raise SetupError("Expected true/false: " + key)
    if result["APP_ADMIN_USER"] and not re.fullmatch(r"[A-Za-z0-9_.-]{3,64}", result["APP_ADMIN_USER"]):
        raise SetupError("Administrator username must contain 3-64 letters, digits, dots, underscores or hyphens.")
    if result["APP_ADMIN_PASSWORD"] and (len(result["APP_ADMIN_PASSWORD"]) < 16 or len(result["APP_ADMIN_PASSWORD"].encode()) > 72 or "\n" in result["APP_ADMIN_PASSWORD"]):
        raise SetupError("Use an administrator password of at least 16 characters and at most 72 bytes, or leave blank to generate.")
    return result


def keypair(urlsafe=False):
    # OpenSSL's X25519 PKCS#8/SPKI encodings end with the 32-byte raw key.
    private_pem = subprocess.run(["openssl", "genpkey", "-algorithm", "X25519"],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout
    private = subprocess.run(["openssl", "pkey", "-outform", "DER"], input=private_pem,
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout[-32:]
    public = subprocess.run(["openssl", "pkey", "-pubout", "-outform", "DER"], input=private_pem,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout[-32:]
    def enc(raw):
        return base64.urlsafe_b64encode(raw).decode().rstrip("=") if urlsafe else base64.b64encode(raw).decode()
    return enc(private), enc(public)


def make_state(cfg):
    reality_private, reality_public = keypair(True)
    wg_private, wg_public = keypair()
    clients = []
    for n, label in enumerate(["phone", "computer"], 2):
        private, public = keypair()
        clients.append({"email": "owner-wg-" + label, "privateKey": private,
                        "publicKey": public,
                        "preSharedKey": base64.b64encode(secrets.token_bytes(32)).decode(),
                        "allowedIPs": ["10.77.77.%d/32" % n], "keepAlive": 25,
                        "subId": secrets.token_hex(16), "enable": True,
                        "limitIp": 0, "totalGB": 0, "expiryTime": 0, "tgId": 0, "reset": 0})
    nonce = secrets.token_hex(10)
    return {
        "version": VERSION, "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "admin_user": cfg["APP_ADMIN_USER"] or "owner-" + secrets.token_hex(4),
        "admin_password": cfg["APP_ADMIN_PASSWORD"] or secrets.token_urlsafe(30),
        "base_path": "/manage-" + nonce + "/",
        "sub_path": "/s-" + nonce + "/", "json_path": "/j-" + nonce + "/",
        "clash_path": "/c-" + nonce + "/", "sub_id": secrets.token_hex(16),
        "vmess_path": "/vmess-" + secrets.token_hex(10),
        "trojan_path": "/trojan-" + secrets.token_hex(10),
        "vmess_uuid": str(uuid.uuid4()), "vless_uuid": str(uuid.uuid4()),
        "trojan_password": secrets.token_urlsafe(32),
        "ss_server_key": base64.b64encode(secrets.token_bytes(32)).decode(),
        "ss_client_key": base64.b64encode(secrets.token_bytes(32)).decode(),
        "reality_private": reality_private, "reality_public": reality_public,
        "reality_short_id": secrets.token_hex(8),
        "wg_private": wg_private, "wg_public": wg_public, "wg_clients": clients,
        "mtproto_secret": "ee" + secrets.token_hex(16) + cfg["APP_MTP_DOMAIN"].encode().hex(),
    }


def client(email, sub_id, **extra):
    value = {"email": email, "subId": sub_id, "enable": True, "limitIp": 0,
             "totalGB": 0, "expiryTime": 0, "tgId": 0, "reset": 0}
    value.update(extra)
    return value


def inbound_payloads(cfg, state):
    def base(proto, key, settings, stream=None):
        obj = {"enable": True, "remark": "OneClick " + proto, "listen": "0.0.0.0",
               "port": cfg["PANEL_APP_PORT_" + key], "protocol": proto,
               "settings": settings, "streamSettings": stream or {},
               "sniffing": {"enabled": False, "destOverride": []},
               "expiryTime": 0, "total": 0, "trafficReset": "never",
               "tag": "oneclick-" + proto, "shareAddrStrategy": "node"}
        return obj
    sub = state["sub_id"]
    return [
        base("vmess", "VMESS", {"clients": [client("owner-vmess", sub, id=state["vmess_uuid"], security="auto")]},
             {"network": "ws", "security": "none", "wsSettings": {"path": state["vmess_path"], "headers": {}}}),
        base("vless", "VLESS", {"clients": [client("owner-vless", sub, id=state["vless_uuid"], flow="xtls-rprx-vision")],
                              "decryption": "none", "fallbacks": []},
             {"network": "tcp", "security": "reality", "realitySettings": {
                 "show": False, "target": cfg["APP_REALITY_TARGET"], "xver": 0,
                 "serverNames": [cfg["APP_REALITY_TARGET"].rpartition(":")[0]],
                 "privateKey": state["reality_private"], "shortIds": [state["reality_short_id"]],
                 "settings": {"publicKey": state["reality_public"], "fingerprint": "chrome",
                              "serverName": cfg["APP_REALITY_TARGET"].rpartition(":")[0]}}}),
        base("trojan", "TROJAN", {"clients": [client("owner-trojan", sub, password=state["trojan_password"])], "fallbacks": []},
             {"network": "ws", "security": "none", "wsSettings": {"path": state["trojan_path"], "headers": {}}}),
        base("shadowsocks", "SS", {"method": "2022-blake3-aes-256-gcm",
             "password": state["ss_server_key"], "network": "tcp,udp",
             "clients": [client("owner-shadowsocks", sub, password=state["ss_client_key"], method="")]}),
        base("wireguard", "WG", {"secretKey": state["wg_private"], "mtu": 1380,
             "dns": "1.1.1.1,1.0.0.1", "subnetIp": "10.77.77.0", "subnetCidr": 24,
             "noKernelTun": True, "peers": [], "clients": state["wg_clients"]}),
        base("mtproto", "MTPROTO", {"fakeTlsDomain": cfg["APP_MTP_DOMAIN"],
             "preferIp": "only-ipv4",
             "clients": [client("owner-telegram", secrets.token_hex(16), secret=state["mtproto_secret"])]}),
    ]


class PanelAPI:
    def __init__(self, port, token, base="/", domain=None):
        self.port = port
        self.token = token
        self.base = "/" + base.strip("/") + "/" if base.strip("/") else "/"
        self.domain = domain
        self.opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

    def request(self, path, body=None, method=None, retries=1):
        raw = json.dumps(body).encode() if body is not None else None
        for attempt in range(retries):
            try:
                req = urllib.request.Request("http://127.0.0.1:%d%s%s" % (self.port, self.base, path.lstrip("/")),
                                             data=raw, method=method or ("POST" if body is not None else "GET"))
                req.add_header("Authorization", "Bearer " + self.token)
                if raw is not None:
                    req.add_header("Content-Type", "application/json")
                if self.domain:
                    req.add_header("Host", self.domain)
                with self.opener.open(req, timeout=15) as response:
                    doc = json.load(response)
                if doc.get("success") is not True:
                    if _DIAG_DIR:
                        save(_DIAG_DIR / "last-api-error.json", doc)
                    raise SetupError("Panel API rejected " + path + "; details remain in the private installation directory.")
                return doc.get("obj")
            except (urllib.error.URLError, TimeoutError, ConnectionError):
                if attempt + 1 == retries:
                    raise SetupError("Panel API unavailable: " + path)
                time.sleep(1)


def docker_cli(container, *args):
    return command(["docker", "exec", container, "/app/x-ui"] + list(args)).stdout


def token_and_base(container):
    text = docker_cli(container, "setting", "-getApiToken", "true", "-tokenName", "oneclick-initialization")
    match = re.search(r"(?m)^apiToken:\s*(\S+)", text)
    if not match:
        raise SetupError("Could not mint initialization API token.")
    settings = docker_cli(container, "setting", "-show", "true")
    path = re.search(r"(?m)^webBasePath:\s*(\S+)", settings)
    if not path:
        raise SetupError("Could not read the panel base path.")
    return match.group(1), path.group(1)


def configure_panel(cfg, state, container):
    token, current_base = token_and_base(container)
    api = PanelAPI(cfg["PANEL_APP_PORT_HTTP"], token, current_base,
                   cfg["APP_PANEL_DOMAIN"])
    existing = api.request("panel/api/inbounds/list", retries=20)
    by_tag = {i["tag"]: i for i in existing}
    if any(not tag.startswith("oneclick-") for tag in by_tag):
        raise SetupError("Existing manually configured inbounds found; initialization will not overwrite them.")
    # CLI is the upstream supported administrator reset mechanism.
    docker_cli(container, "setting", "-username", state["admin_user"],
               "-password", state["admin_password"])
    installed = {}
    for body in inbound_payloads(cfg, state):
        if body["tag"] in by_tag:
            row = by_tag[body["tag"]]
            if row["protocol"] != body["protocol"] or row["port"] != body["port"]:
                raise SetupError("Existing managed inbound differs from installation parameters: " + body["protocol"])
        else:
            row = api.request("panel/api/inbounds/add", body)
        installed[body["protocol"]] = row
        print("Configured inbound: " + body["protocol"], flush=True)
    host_groups = api.request("panel/api/hosts/list")
    for proto in PROTOCOLS:
        inbound_id = installed[proto]["id"]
        remark = "OneClick-" + proto
        if any(g.get("remark") == remark for g in host_groups):
            continue
        cdn = proto in ["vmess", "trojan"]
        row = {
            "inboundIds": [inbound_id], "remark": remark,
            "hosts": [cfg["APP_PANEL_DOMAIN"] if cdn else cfg["APP_NODE_DOMAIN"]],
            "port": 443 if cdn else installed[proto]["port"],
            "security": "tls" if cdn else "same",
            "sni": cfg["APP_PANEL_DOMAIN"] if cdn else "",
            "hostHeader": cfg["APP_PANEL_DOMAIN"] if cdn else "",
            "path": state["vmess_path"] if proto == "vmess" else state["trojan_path"] if proto == "trojan" else "",
            "allowInsecure": False, "isDisabled": False, "isHidden": False,
            "tags": [], "sortOrder": 0, "fingerprint": "chrome",
            "mihomoIpVersion": "ipv4",
        }
        api.request("panel/api/hosts/add", row)
    settings = api.request("panel/api/setting/all", {})
    # Trust only loopback and this container network's host gateway, where
    # the local OpenResty reverse proxy connects from. Keep explicit prior CIDRs.
    trusted = set(re.split(r"[,\s]+", settings.get("trustedProxyCIDRs", ""))) - {""}
    trusted.update(["127.0.0.1/32", "::1/128"])
    info = json.loads(command(["docker", "inspect", container]).stdout)[0]
    for net in info["NetworkSettings"].get("Networks", {}).values():
        for key in ["Gateway", "IPv6Gateway"]:
            value = net.get(key)
            if value:
                address = ipaddress.ip_address(value)
                if address.is_private:
                    trusted.add(str(address) + ("/32" if address.version == 4 else "/128"))
    changes = {
        "webPort": 2053, "webListen": "0.0.0.0", "webBasePath": state["base_path"],
        "webCertFile": "", "webKeyFile": "", "webDomain": "",
        "subEnable": True, "subPort": 2096, "subListen": "0.0.0.0",
        "subCertFile": "", "subKeyFile": "", "subDomain": cfg["APP_PANEL_DOMAIN"],
        "subPath": state["sub_path"], "subJsonEnable": True,
        "subJsonPath": state["json_path"], "subClashEnable": True,
        "subClashPath": state["clash_path"], "subEncrypt": True,
        "subURI": "https://" + cfg["APP_PANEL_DOMAIN"] + state["sub_path"],
        "subJsonURI": "https://" + cfg["APP_PANEL_DOMAIN"] + state["json_path"],
        "subClashURI": "https://" + cfg["APP_PANEL_DOMAIN"] + "/mihomo/",
        "timeLocation": "Asia/Shanghai",
        "trustedProxyCIDRs": ",".join(sorted(trusted)),
    }
    # Updating all settings is the documented endpoint contract.
    settings.update(changes)
    api.request("panel/api/setting/update", settings)
    command(["docker", "kill", "--signal", "HUP", container])
    api = PanelAPI(cfg["PANEL_APP_PORT_HTTP"], token, state["base_path"],
                   cfg["APP_PANEL_DOMAIN"])
    final_rows = api.request("panel/api/inbounds/list", retries=30)
    if {i["protocol"] for i in final_rows} != set(PROTOCOLS):
        raise SetupError("Post-initialization protocol verification failed.")
    return api, final_rows


def location_block(match, port, ws=False, subscription=False):
    lines = [
        "location " + match + " {",
        "    proxy_pass http://127.0.0.1:%d;" % port,
        "    proxy_http_version 1.1;",
        "    proxy_set_header Host $host;",
        "    proxy_set_header X-Real-IP $remote_addr;",
        "    proxy_set_header X-Forwarded-For $remote_addr;",
        "    proxy_set_header X-Forwarded-Proto $scheme;",
    ]
    if ws:
        lines += ["    proxy_set_header Upgrade $http_upgrade;",
                  '    proxy_set_header Connection "upgrade";',
                  "    proxy_read_timeout 3600s;", "    proxy_send_timeout 3600s;",
                  "    proxy_buffering off;"]
    if subscription:
        lines += ["    proxy_cache_bypass 1;", "    proxy_no_cache 1;",
                  '    add_header Cache-Control "no-store" always;', "    access_log off;"]
    return "\n".join(lines + ["}", ""])


def nginx_config(cfg, state, appdir):
    text = "# Managed by 3xui-oneclick: " + str(appdir) + "\n"
    text += "# TLS remains managed by the existing OnePanel/OpenResty HTTPS site.\n\n"
    text += location_block("= " + state["vmess_path"], cfg["PANEL_APP_PORT_VMESS"], ws=True)
    text += location_block("= " + state["trojan_path"], cfg["PANEL_APP_PORT_TROJAN"], ws=True)
    for path in [state["sub_path"], state["json_path"], state["clash_path"], "/mihomo/", "/clash-legacy/"]:
        text += location_block("^~ " + path, cfg["PANEL_APP_PORT_SUB"], subscription=True)
    text += location_block("/", cfg["PANEL_APP_PORT_HTTP"], ws=True)
    return text


def find_panel_root(appdir, explicit=None):
    if explicit:
        root = explicit.resolve()
    else:
        root = next((p for p in [appdir] + list(appdir.parents)
                     if (p / "www/conf.d").is_dir() and (p / "apps").is_dir()), None)
    if root is None:
        raise SetupError("Could not identify the OnePanel installation root.")
    return root


def proxy_preflight(cfg, appdir, panel_root=None, container_override=None):
    root = find_panel_root(appdir, panel_root)
    matches = []
    for path in (root / "www/conf.d").glob("*.conf"):
        text = path.read_text()
        names = re.findall(r"(?m)^\s*server_name\s+([^;]+);", text)
        if any(cfg["APP_PANEL_DOMAIN"] in n.split() for n in names):
            matches.append((path, text))
    if len(matches) != 1:
        raise SetupError("Expected one existing OpenResty HTTPS site for the panel hostname.")
    site_path, site_text = matches[0]
    if not re.search(r"(?m)^\s*listen\s+[^;]*\bssl\b", site_text):
        raise SetupError("The existing panel site does not enable HTTPS.")
    include = re.findall(r"(?m)^\s*include\s+([^;]+/proxy/\*\.conf);", site_text)
    if len(include) != 1:
        raise SetupError("The existing site has no unique managed proxy include directory.")
    candidates = []
    for row in command(["docker", "ps", "--format", "{{json .}}"]).stdout.splitlines():
        item = json.loads(row)
        if (container_override and item["Names"] == container_override) or (
                not container_override and "1panel/openresty" in item["Image"].lower()):
            obj = json.loads(command(["docker", "inspect", item["Names"]]).stdout)[0]
            if container_override or any(Path(m["Source"]).resolve() == (root / "www").resolve()
                                         for m in obj.get("Mounts", [])):
                candidates.append(item["Names"])
    if len(candidates) != 1:
        raise SetupError("Expected one running OnePanel OpenResty container.")
    container = candidates[0]
    info = json.loads(command(["docker", "inspect", container]).stdout)[0]
    if info["HostConfig"]["NetworkMode"] != "host":
        raise SetupError("This local-loopback proxy layout requires the existing OpenResty host network.")
    def translate(raw):
        for mount in sorted(info.get("Mounts", []), key=lambda m: len(m["Destination"]), reverse=True):
            dest = mount["Destination"].rstrip("/")
            if raw == dest or raw.startswith(dest + "/"):
                return Path(mount["Source"]) / raw[len(dest):].lstrip("/")
        raise SetupError("Could not map OpenResty site files to the host.")
    certs = re.findall(r"(?m)^\s*ssl_certificate\s+([^;]+);", site_text)
    if len(certs) != 1:
        raise SetupError("Expected one certificate path on the panel site.")
    cert = translate(certs[0].strip().strip('"'))
    for args in [["openssl", "x509", "-in", str(cert), "-noout", "-checkhost", cfg["APP_PANEL_DOMAIN"]],
                 ["openssl", "x509", "-in", str(cert), "-noout", "-checkend", "0"]]:
        if command(args, check=False).returncode:
            raise SetupError("The existing panel-site certificate is expired or does not match.")
    folder = translate(include[0].replace("*.conf", ""))
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / "3xui-oneclick.conf"
    if target.exists() and not target.read_text().startswith("# Managed by 3xui-oneclick: " + str(appdir) + "\n"):
        raise SetupError("A proxy file owned by another installation already exists.")
    for other in folder.glob("*.conf"):
        if other == target:
            continue
        if re.search(r"\blocation\s+(?:=\s+)?/\s*\{", other.read_text()):
            raise SetupError("An existing catch-all proxy would conflict; refusing to overwrite it.")
    args = []
    launch = (info["Config"].get("Entrypoint") or []) + (info["Config"].get("Cmd") or [])
    if "-c" in launch and launch.index("-c") + 1 < len(launch):
        args = ["-c", launch[launch.index("-c") + 1]]
    return {"path": str(target), "container": container, "site": str(site_path),
            "nginx_args": args}


def apply_proxy(cfg, state, appdir, data, plan):
    target = Path(plan["path"])
    old = target.read_text() if target.exists() else None
    text = nginx_config(cfg, state, appdir)
    save(target, text)
    target.chmod(0o644)
    try:
        command(["docker", "exec", plan["container"], "nginx", "-t", "-q"] + plan.get("nginx_args", []))
        command(["docker", "exec", plan["container"], "nginx", "-s", "reload"] + plan.get("nginx_args", []))
    except BaseException:
        if old is None:
            target.unlink()
        else:
            save(target, old)
            target.chmod(0o644)
        restored = command(["docker", "exec", plan["container"], "nginx", "-t", "-q"] + plan.get("nginx_args", []), check=False)
        if restored.returncode == 0:
            command(["docker", "exec", plan["container"], "nginx", "-s", "reload"] + plan.get("nginx_args", []), check=False)
        raise SetupError("OpenResty validation/reload failed; the previous proxy file was restored.")
    record = dict(plan)
    record["sha256"] = hashlib.sha256(text.encode()).hexdigest()
    record["prior_content"] = old
    save(data / "private/managed-proxy.json", record)


def remove_proxy(data):
    record = data / "private/managed-proxy.json"
    if not record.exists():
        return
    plan = json.loads(record.read_text())
    target = Path(plan["path"])
    if not target.exists():
        return
    if hashlib.sha256(target.read_bytes()).hexdigest() != plan["sha256"]:
        raise SetupError("The managed proxy was edited later; refusing to remove it automatically.")
    current = target.read_text()
    old = plan.get("prior_content")
    if old is None:
        target.unlink()
    else:
        save(target, old)
        target.chmod(0o644)
    try:
        command(["docker", "exec", plan["container"], "nginx", "-t", "-q"] + plan.get("nginx_args", []))
        command(["docker", "exec", plan["container"], "nginx", "-s", "reload"] + plan.get("nginx_args", []))
    except BaseException:
        save(target, current)
        target.chmod(0o644)
        restored = command(["docker", "exec", plan["container"], "nginx", "-t", "-q"] + plan.get("nginx_args", []), check=False)
        if restored.returncode == 0:
            command(["docker", "exec", plan["container"], "nginx", "-s", "reload"] + plan.get("nginx_args", []), check=False)
        raise SetupError("Proxy cleanup validation failed; restored the current managed file.")
    record.unlink()


def compose(appdir, *args):
    if command(["docker", "compose", "version"], check=False).returncode == 0:
        prefix = ["docker", "compose"]
    elif shutil.which("docker-compose"):
        prefix = ["docker-compose"]
    else:
        raise SetupError("Docker Compose is not available.")
    return command(prefix + ["--env-file", str(appdir / ".env"), "-f",
                             str(appdir / "docker-compose.yml")] + list(args), timeout=420)


def own_container(cfg, appdir):
    p = command(["docker", "inspect", cfg["CONTAINER_NAME"]], check=False)
    if p.returncode:
        return None
    info = json.loads(p.stdout)[0]
    directory = info["Config"].get("Labels", {}).get("com.docker.compose.project.working_dir", "")
    if not directory or Path(directory).resolve() != appdir:
        raise SetupError("The selected container name belongs to another project.")
    return info


def free_ports(cfg, owner):
    owned = set()
    if owner:
        for item, bindings in owner["NetworkSettings"].get("Ports", {}).items():
            for binding in bindings or []:
                owned.add((int(binding["HostPort"]), item.split("/")[1]))
    for suffix, protocols in PORT_PROTO.items():
        port = cfg["PANEL_APP_PORT_" + suffix]
        for protocol in protocols:
            if (port, protocol) in owned:
                continue
            p = command(["ss", "-H", "-lnt" if protocol == "tcp" else "-lnu",
                         "sport = :" + str(port)])
            if p.stdout.strip():
                raise SetupError("Port %d/%s is already in use. Existing services were not stopped." % (port, protocol))


def wait_for_panel(cfg, container):
    for _ in range(90):
        p = command(["docker", "exec", container, "bash", "-c",
                     "exec 3<>/dev/tcp/127.0.0.1/2053"], check=False)
        if p.returncode == 0:
            return
        time.sleep(1)
    raise SetupError("The panel did not become ready.")


def export_profiles(cfg, state, data):
    export = data / "exports"
    export.mkdir(mode=0o700, exist_ok=True)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    outputs = [
        (state["sub_path"], "v2rayN-subscription.txt"),
        (state["json_path"], "xray-client-configs.json"),
        ("/mihomo/", "mihomo.yaml"),
    ]
    for path, name in outputs:
        req = urllib.request.Request("http://127.0.0.1:%d%s%s" %
                                     (cfg["PANEL_APP_PORT_SUB"], path, state["sub_id"]),
                                     headers={"Host": cfg["APP_PANEL_DOMAIN"]})
        raw = None
        for _ in range(20):
            try:
                with opener.open(req, timeout=10) as resp:
                    raw = resp.read()
                break
            except urllib.error.URLError:
                time.sleep(1)
        if raw is None:
            raise SetupError("Could not export subscription: " + name)
        if name == "v2rayN-subscription.txt":
            links = base64.b64decode(raw).decode().splitlines()
            if len(links) != 4 or {v.split(":", 1)[0] for v in links} != {"vmess", "vless", "trojan", "ss"}:
                raise SetupError("The generated primary subscription does not contain exactly four expected nodes.")
        elif name.endswith(".json"):
            if len(json.loads(raw)) != 4:
                raise SetupError("The generated JSON subscription is incomplete.")
        elif b"proxies:" not in raw:
            raise SetupError("The generated Mihomo subscription is not valid YAML output.")
        save(export / name, raw.decode())
    for peer in state["wg_clients"]:
        name = "phone" if peer["email"].endswith("phone") else "computer"
        text = "[Interface]\nPrivateKey = %s\nAddress = %s\nDNS = 1.1.1.1,1.0.0.1\nMTU = 1380\n\n[Peer]\nPublicKey = %s\nPresharedKey = %s\nEndpoint = %s:%d\nAllowedIPs = 0.0.0.0/0,::/0\nPersistentKeepalive = 25\n" % (
            peer["privateKey"], peer["allowedIPs"][0], state["wg_public"],
            peer["preSharedKey"], cfg["APP_NODE_DOMAIN"], cfg["PANEL_APP_PORT_WG"])
        save(export / ("wireguard-" + name + ".conf"), text)
    tg = "https://t.me/proxy?" + urllib.parse.urlencode({
        "server": cfg["APP_NODE_DOMAIN"], "port": cfg["PANEL_APP_PORT_MTPROTO"], "secret": state["mtproto_secret"]})
    save(export / "telegram-link.txt", tg + "\n")
    access = {
        "panel_url": "https://" + cfg["APP_PANEL_DOMAIN"] + state["base_path"],
        "username": state["admin_user"], "password": state["admin_password"],
        "v2rayN_subscription": "https://" + cfg["APP_PANEL_DOMAIN"] + state["sub_path"] + state["sub_id"],
        "mihomo_subscription": "https://" + cfg["APP_PANEL_DOMAIN"] + "/mihomo/" + state["sub_id"],
        "telegram_link": tg,
        "wireguard_files": ["exports/wireguard-phone.conf", "exports/wireguard-computer.conf"],
    }
    save(data / "private/access.json", access)
    lines = ["# 安装结果（含凭据，请勿公开）", "",
             "面板地址：" + access["panel_url"], "管理员：" + state["admin_user"],
             "管理员密码：" + state["admin_password"], "",
             "v2rayN 订阅：" + access["v2rayN_subscription"],
             "Clash Verge/Mihomo 订阅：" + access["mihomo_subscription"], "",
             "Telegram：" + tg, "", "WireGuard 配置：exports/wireguard-phone.conf、exports/wireguard-computer.conf。",
             "", "需要在 OCI 允许的直连端口：",
             "- TCP：%d、%d、%d。" % (cfg["PANEL_APP_PORT_VLESS"], cfg["PANEL_APP_PORT_SS"], cfg["PANEL_APP_PORT_MTPROTO"]),
             "- UDP：%d、%d。" % (cfg["PANEL_APP_PORT_SS"], cfg["PANEL_APP_PORT_WG"]),
             "- HTTPS/CDN 使用现有 443。面板、订阅、WS 后端的宿主机端口保持本机访问。",
             "", "OCI 规则不在本机模板权限范围内，尚未通过云 API 核验。现有独立 WireGuard 没有被停止。",
             "", "密钥与订阅已生成；真实客户端的电信、联通线路表现仍需分别验证。"]
    save(data / "INSTALL-RESULT.md", "\n".join(lines) + "\n")


def verify_listeners(cfg, container):
    pid = json.loads(command(["docker", "inspect", container]).stdout)[0]["State"]["Pid"]
    for suffix, protocols in PORT_PROTO.items():
        if suffix in ["HTTP", "SUB"]:
            port = 2053 if suffix == "HTTP" else 2096
        else:
            port = cfg["PANEL_APP_PORT_" + suffix]
        for protocol in protocols:
            found = False
            for _ in range(30):
                p = command(["nsenter", "-t", str(pid), "-n", "ss", "-H",
                             "-lnt" if protocol == "tcp" else "-lnu", "sport = :" + str(port)])
                if p.stdout.strip():
                    found = True
                    break
                time.sleep(1)
            if not found:
                raise SetupError("Inbound listener did not start: %d/%s" % (port, protocol))


def run_install(appdir, panel_root=None, openresty_container=None):
    global _DIAG_DIR
    cfg = options(appdir / ".env")
    if not cfg["CONTAINER_NAME"]:
        raise SetupError("CONTAINER_NAME was not supplied by OnePanel.")
    os.umask(0o077)
    data = appdir / "data"
    for p in [data, data / "private", data / "ready", data / "db", data / "cert", data / "acme", data / "logs"]:
        p.mkdir(parents=True, mode=0o700, exist_ok=True)
        p.chmod(0o700)
    _DIAG_DIR = data / "private"
    (appdir / ".env").chmod(0o600)
    state_path = data / "private/state.json"
    if state_path.exists():
        state = json.loads(state_path.read_text())
    else:
        state = make_state(cfg)
        save(state_path, state)
    public_config = {k: v for k, v in cfg.items() if k not in ["APP_ADMIN_USER", "APP_ADMIN_PASSWORD"]}
    fingerprint = hashlib.sha256(json.dumps(public_config, sort_keys=True).encode()).hexdigest()
    ready = data / "ready/complete.json"
    owner = own_container(cfg, appdir)
    if ready.exists():
        current = json.loads(ready.read_text())
        if current["configuration_hash"] != fingerprint:
            raise SetupError("Installation parameters changed after initialization; refusing to silently rewrite live nodes.")
        compose(appdir, "up", "-d")
        wait_for_panel(cfg, cfg["CONTAINER_NAME"])
        print("Existing initialization retained; administrator and node credentials were not reset.", flush=True)
        return
    free_ports(cfg, owner)
    proxy = proxy_preflight(cfg, appdir, panel_root, openresty_container) if cfg["APP_AUTO_OPENRESTY"] == "true" else None
    started = owner is None or not owner["State"]["Running"]
    try:
        compose(appdir, "up", "-d")
        wait_for_panel(cfg, cfg["CONTAINER_NAME"])
        api, rows = configure_panel(cfg, state, cfg["CONTAINER_NAME"])
        verify_listeners(cfg, cfg["CONTAINER_NAME"])
        export_profiles(cfg, state, data)
        if proxy:
            apply_proxy(cfg, state, appdir, data, proxy)
        # Revoke the provisioning-only administrator token before completing.
        for token in api.request("panel/api/setting/apiTokens"):
            if token.get("name") == "oneclick-initialization":
                api.request("panel/api/setting/apiTokens/delete/" + str(token["id"]),
                            {"expectedScope": token.get("scope", "admin")})
        save(ready, {"status": "ready", "version": VERSION,
                     "configuration_hash": fingerprint, "protocols": PROTOCOLS,
                     "completed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()})
        print("Six inbounds, administrator, subscriptions and client exports are ready.", flush=True)
        print("Private access details: " + str(data / "INSTALL-RESULT.md"), flush=True)
    except BaseException:
        save(data / "private/last-error.json", {"status": "failed", "version": VERSION,
             "time_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()})
        if started:
            command(["docker", "stop", cfg["CONTAINER_NAME"]], check=False)
        raise


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["install", "uninstall"])
    parser.add_argument("--app-dir", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--panel-root", type=Path)
    parser.add_argument("--openresty-container")
    args = parser.parse_args()
    if os.geteuid() != 0:
        raise SetupError("The OnePanel installation hook must run as root.")
    appdir = args.app_dir.resolve()
    if args.action == "install":
        run_install(appdir, args.panel_root, args.openresty_container)
    else:
        remove_proxy(appdir / "data")
        print("Only this application's unchanged managed proxy was cleaned up.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except SetupError as error:
        raise SystemExit(str(error))
