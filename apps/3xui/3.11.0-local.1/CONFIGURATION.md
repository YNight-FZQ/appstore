# 六协议本地定制模板

3.11.0-local.1 使用官方 ghcr.io/mhsanaei/3x-ui:v3.11.0 镜像，适配当前 ARM64 甲骨文服务器、1Panel 2.3.2 和已有 OpenResty。

## 模板范围

一个容器管理面板、订阅及六类入站。模板准备端口、持久化目录、安装前检查，并生成配置表和 OpenResty 片段；安装后仍需在面板创建客户端与入站、配置订阅路径并应用反向代理。模板不自动创建节点或凭据，不修改现有网站、DNS、宿主机防火墙，不停止或迁移原 WireGuard。

原 3.8.5 模板保留。1Panel“应用商店 → 同步本地应用”后选择新版本。安装脚本需要当前设备已有的 Python 3、ss；安装时应允许执行应用脚本。

## 默认端口

| 用途 | 宿主机 / 容器端口 | 发布地址 |
| --- | --- | --- |
| 面板 | 2053 / 2053 TCP | 127.0.0.1 |
| 订阅 | 2096 / 2096 TCP | 127.0.0.1 |
| VMess WS | 24441 / 24441 TCP | 127.0.0.1 |
| VLESS REALITY | 24442 / 24442 TCP | 0.0.0.0 |
| Trojan WS | 24443 / 24443 TCP | 127.0.0.1 |
| Shadowsocks | 24444 / 24444 TCP+UDP | 0.0.0.0 |
| WireGuard 测试 | 51821 / 51821 UDP | 0.0.0.0 |
| MTProto | 24445 / 24445 TCP | 0.0.0.0 |

面板和订阅的容器内端口保持 2053、2096。其余六种入站监听端口须与表单相同。更改 Docker 端口不会自动修改 Xray 入站。

ports 明确指定逐条绑定地址，1Panel 高级设置的统一“端口外部访问”选项不会替代这些绑定。公开节点端口仍需核对 OCI 规则；Docker 端口发布与 UFW 放行不是同一回事。初始方案仅提供 IPv4 接入。

## 域名分工

- xui.ynight.top：保留 Cloudflare，提供面板、HTTPS 订阅和 VMess/Trojan WebSocket。
- node.fzq.dpdns.org：直连服务器，用于其他协议的独立端口。

安装表单的域名字段用于生成配置说明，不会修改 DNS，也不会自动改写 3x-ui 的 Hosts 或分享链接。

## 安装后配置六种入站

安装目录为 /panel/1panel/apps/local/3xui/安装名称/。

安装脚本在 data 中生成：

- INBOUND-SETUP.md：实际端口、域名、随机 WS 路径和配置表。
- openresty-locations.conf：适用于现有 xui HTTPS 站点的示例。
- node-plan.json：非凭据的参数计划，再次生成时保留 WS 路径。

先登录面板，分别创建：

1. VMess：WS，使用生成的端口和路径，后端 security=none；外部 TLS 在 OpenResty 结束。
2. VLESS：RAW + REALITY + xtls-rprx-vision；在面板生成 UUID、密钥、short ID，选择并验证实际可用的目标和 SNI。
3. Trojan：WS，使用生成的端口和路径；只有可信本机反代链路使用 security=none，外部客户端必须开启 TLS。
4. Shadowsocks：TCP+UDP，优先选择两个客户端均支持的 Shadowsocks 2022 加密方式，由面板生成密钥。
5. WireGuard：先用 51821/UDP 验证；原设备迁移时再私密导入/核对服务端密钥、客户端公钥、PSK 与地址。
6. MTProto：FakeTLS，配置 Telegram 使用的域名和密钥。

VMess/Trojan 客户端：server=xui.ynight.top，port=443，TLS 开启，SNI/Host=xui.ynight.top，WS 路径与配置表相同。不要把这些明文 WS 后端直接改为公网发布。

其他直连节点在 Hosts/分享设置中使用 node.fzq.dpdns.org 和各自端口；不能将面板的 Cloudflare 域名作为所有 RAW/UDP 节点的默认地址。

## 初次登录、反向代理和订阅

可先通过 SSH 本地转发配置面板（在电脑执行，将 SSH_ALIAS 替换为现有 SSH 别名）：

~~~bash
ssh -N -L 12053:127.0.0.1:2053 SSH_ALIAS
~~~

浏览器打开 http://127.0.0.1:12053，并使用该版本实际初始化的账号和访问路径。若表单改了宿主机面板端口，替换命令中的远端端口。不要公开初始化日志。

订阅默认路径可能随机。应用生成的反代示例前，在面板订阅设置中明确设置：

- 容器内端口保持 2096，使用 HTTP。
- subPath=/sub/。
- subJsonPath=/json/，按需要启用 JSON。
- subClashPath=/clash/，启用 Clash/Mihomo。
- 若启用订阅域名限制，使用 xui.ynight.top。

示例也转发官方 /mihomo/ 和 /clash-legacy/ 别名。Clash Verge/Mihomo 使用 /mihomo/ 的链接。导出链接的外部入口使用 https://xui.ynight.top，保留正确的路径与 Sub ID。

通过 1Panel 编辑已有 xui HTTPS 站点，合并生成的 location 配置。先处理已有重复项，再检查语法和重载；不要盲目追加重复 location / 或第二个 server 块。示例不会自行应用或重载。

节点和订阅路径须允许客户端直接请求；如使用交互式浏览器验证，应与这些路径区分配置。

## 证书

本方案由 OpenResty 使用 xui.ynight.top 的现有证书，VMess/Trojan 私网 WS 后端无需重复终止 TLS。

node.fzq.dpdns.org 的证书已在 1Panel 申请，但证书库中的 ready 不代表已导出到容器。若改为直连 TLS 入站：

1. 在 1Panel 设置将对应证书及配套私钥推送到安装目录 data/cert 的独立子目录。
2. 入站引用只读挂载的 /root/cert/ 下对应文件。
3. 核实续期同步与 Xray 加载新证书；不要将私钥写入本地商店模板。

REALITY、标准 WireGuard、标准 Shadowsocks、MTProto FakeTLS 不使用这张普通站点 TLS 证书。data/acme 用于持久保存未来可能由容器内 ACME 生成的状态，当前优先沿用 1Panel 的证书管理。

## WireGuard 切换

默认 51821 为迁移测试保留原 51820 服务。先验证新入站的本机和实际外部连接，再在维护时停止旧服务，将本地应用参数和面板入站监听端口一并改为 51820，并核对客户端 Endpoint。

继续使用原客户端配置要求密钥关系、PSK、地址和端口均匹配。用户态实现的功能与性能也需另测；旧配置先保留为回退依据。

## 修改与更新

修改端口或域名后，可在安装目录重新运行脚本生成示例：

~~~bash
python3 scripts/render_config.py --env .env --output data
~~~

然后人工同步面板入站和 OpenResty 配置。重复生成保留已有 WS 路径；不会改面板数据库或停止服务。

固定正式镜像版本，关闭本容器的 Watchtower 自动更新。升级前备份面板数据库，检查配置和客户端兼容性；REALITY 尤其要分别验证 v2rayN 与 Mihomo 的实际版本组合。

健康检查只表示面板 TCP 2053 就绪，不代表入站已创建或全部客户端可用。本地商店同步工具可能覆盖定制文件，保留本次修改包以便比对恢复。

## 官方资料

- https://github.com/MHSanaei/3x-ui/releases/tag/v3.11.0
- https://github.com/MHSanaei/3x-ui/blob/v3.11.0/docs/content/docs/zh/operations/reverse-proxy.mdx
- https://github.com/MHSanaei/3x-ui/blob/v3.11.0/docs/content/docs/zh/config/subscription.mdx
- https://xtls.github.io/en/config/transports/tls.html
- https://wiki.metacubex.one/config/proxies/tls/
