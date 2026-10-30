# 3X-UI 六协议一键版：3.11.0-local.2

本版本基于官方 3x-ui 3.11.0，针对当前 1Panel 2.3.2、已有 OpenResty HTTPS 站点和域名配置，补充安装时的业务初始化。

## 正常使用只需安装

1. 在 1Panel 应用商店点击“同步本地应用”，选择 3X-UI 的 3.11.0-local.2。
2. 填写应用名称，默认域名为 xui.ynight.top 与 node.fzq.dpdns.org；其他参数通常保持默认。
3. 管理员用户名、密码可留空，程序在安装时安全生成；自填密码至少 16 个字符且不超过 72 字节。
4. 点击安装并等待任务完成。
5. 在本应用安装目录 data/INSTALL-RESULT.md 查看面板地址、管理员凭据、订阅、Telegram 链接，以及 WireGuard 配置位置。

无需再逐项创建六种入站、配置 Hosts、修改订阅路径或手工粘贴反代。客户端仍需正常导入配置或订阅。

## 自动完成的内容

- 初次生成管理员账号、强密码、UUID、REALITY/WireGuard 密钥、PSK、Telegram Secret。
- 创建 VMess、VLESS、Trojan、Shadowsocks、WireGuard、MTProto 六种入站。
- 设置 CDN 节点的 443/TLS/WS 参数，以及直连节点的实际域名与端口。
- 启用 v2rayN、Xray JSON 和 Mihomo 订阅，自动设置随机订阅路径及公开 HTTPS 地址。
- 自动找到现有 xui.ynight.top HTTPS 站点，写入本应用的反代文件，检查 Nginx 语法后平滑重载；失败恢复旧文件。
- 检查所有监听端口，保存客户端配置，撤销初始化期间使用的临时管理员 API Token。
- 重复初始化、停止启动及重启保留账号与密钥；应用的就绪检查包含初始化完成标记。

## 默认端口与域名

| 入口 | 宿主机端口 | 连接地址 |
| --- | --- | --- |
| 面板后端 | 127.0.0.1:2053/TCP | 经 OpenResty 的 HTTPS |
| 订阅后端 | 127.0.0.1:2096/TCP | 经 OpenResty 的 HTTPS |
| VMess WS 后端 | 127.0.0.1:24441/TCP | 客户端用 xui.ynight.top:443 |
| VLESS REALITY | 24442/TCP | node.fzq.dpdns.org |
| Trojan WS 后端 | 127.0.0.1:24443/TCP | 客户端用 xui.ynight.top:443 |
| Shadowsocks 2022 | 24444/TCP+UDP | node.fzq.dpdns.org |
| WireGuard 新节点 | 51821/UDP | node.fzq.dpdns.org |
| MTProto FakeTLS | 24445/TCP | node.fzq.dpdns.org |

首次方案仅提供 IPv4。现有独立 WireGuard 的 51820 不会被停止，新节点使用 10.77.77.0/24 的独立地址和新配置；已有旧客户端配置不会自动变成新节点配置。

## 输出与持久化

安装目录通常是 /panel/1panel/apps/local/3xui/安装名称/。

- data/INSTALL-RESULT.md：完整私密安装结果，包含登录凭据和订阅地址。
- data/exports/v2rayN-subscription.txt：四种常用代理协议的订阅内容。
- data/exports/xray-client-configs.json：官方订阅引擎生成的客户端配置。
- data/exports/mihomo.yaml：Clash Verge/Mihomo 配置。
- data/exports/wireguard-phone.conf、wireguard-computer.conf：两个设备的 WireGuard 配置。
- data/exports/telegram-link.txt：Telegram 代理链接。
- data/private/state.json：初始化状态及凭据，只在首次生成，不写入商店定义。
- data/ready/complete.json：初始化完成标记，不含账号和密钥。
- data/db、data/logs、data/cert、data/acme：持久化数据。

安装目录的 data 目录使用 0700，私密文件使用 0600。请通过已认证的 1Panel 文件管理查看或下载，不公开这些文件。正常启动不重置凭据；结果文件记录首次初始化信息，后续在面板中修改账号或节点时以面板为准。

## 表单参数

支持设置面板、订阅、六种入站端口，两个域名，管理员用户名/密码，REALITY 目标、MTProto FakeTLS 域名，自动 OpenResty 和 Fail2ban 开关。

默认自动接入 OpenResty。关闭这个开关只适用于你已准备好等效反代的情况。端口、域名等首次初始化参数不作为已安装后的随意编辑项，避免只改变 Docker 映射而未同步业务配置。

开关使用当前 1Panel 前端支持的 select=true/false，不使用不受支持的 boolean 类型。

## OpenResty 和证书

要求面板域名已经存在一个启用 HTTPS 且证书匹配的 1Panel 网站。附件原始环境使用 xui.ynight.top；本次仓库更新未核验目标服务器是否已有站点和证书。

自动化只管理这个站点 proxy/3xui-oneclick.conf，不覆盖其他网站和已有证书。现有同名文件若不属于本实例，或有冲突的手工根路径反代，会在覆盖前停止并给出错误。

VMess/Trojan 的 TLS 在 OpenResty 结束，容器内是可信本机 WS 后端。node.fzq.dpdns.org 新申请的证书保留在 1Panel；当前 REALITY、标准 Shadowsocks、WireGuard 和 MTProto 不需要复制这张普通 TLS 证书。

如在 Cloudflare 配置了 Access 或浏览器挑战，需确保节点/订阅请求能正常通过。模板不调用你的 Cloudflare API。

## 云端前置条件和验收

本机可自动完成入站、订阅与反代；DNS、Cloudflare 代理状态和 OCI 安全规则属于外部前置条件。

OCI 需允许：TCP 24442/24444/24445、UDP 24444/51821，以及已有 HTTPS 443。若你修改了端口，以安装结果为准。程序没有 OCI 管理凭据，不能替你修改或确认这些规则；发布 Docker 端口不等于已放行云端安全规则。

部署后仍应分别从中国大陆电信、联通，以及 v2rayN、Clash Verge/Mihomo、WireGuard、Telegram 验证真实连接。服务器本机的成功测试不能代表这些线路的可达性。

## 生命周期

标准 1Panel 安装会先执行 init.sh，再执行正常 Compose up。本脚本提前启动同一个受管 Compose 并完成初始化；面板随后的 Compose up 复用该容器，不另建常驻初始化服务。

upgrade.sh 保留既有数据库、账号与节点。uninstall.sh 仅在本应用反代文件仍与记录一致时移除/恢复它并检查重载；若用户后来手工修改，拒绝自动覆盖。代理容器不挂载 Docker socket。

## 出错时

任务日志只显示步骤和错误摘要，不输出密码或节点密钥。私密错误资料位于 data/private。首次初始化失败会停止本次新启动的容器，保留诊断与数据，不停止其他容器或原 WireGuard。

先解决明确的端口、站点或参数错误。对已有手工配置的数据库，脚本不会假装全新实例而覆盖其节点。

## 仓库导入补充

跨版本升级已关闭，旧版不能直接切换到一键版。宿主机需要 Python 3、Docker Compose、OpenSSL、ss、nsenter；自动接入要求 OpenResty 使用 host 网络。实际安装路径以目标面板为准。附件中的域名和端口是原环境预设，其他环境需调整。
