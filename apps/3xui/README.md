# 3X-UI 六协议一键本地应用

推荐 3.11.0-local.2。以官方 3x-ui 3.11.0 镜像运行，在 1Panel 安装时自动完成账号密钥、六种入站、节点 Hosts、订阅和现有 OpenResty 反代。

## 使用

应用商店 → 同步本地应用 → 3X-UI → 3.11.0-local.2 → 安装。

两个域名默认是 xui.ynight.top（面板/订阅/CDN）和 node.fzq.dpdns.org（直连）。管理员账号密码可留空自动生成。其他环境需要先修改域名并确认前置条件。安装完成后查看安装目录 data/INSTALL-RESULT.md，导入其中提供的客户端配置即可。

私密结果包含管理员凭据、v2rayN/Mihomo 订阅、Telegram 链接和 WireGuard 配置。不要公开分享该文件或初始化数据。

## 六种入口

- VMess、Trojan：WebSocket+TLS，经现有 Cloudflare/OpenResty 443。
- VLESS：RAW+REALITY+Vision，独立 TCP 端口。
- Shadowsocks：2022 AEAD，TCP+UDP。
- WireGuard：新节点默认 51821/UDP，与现有 51820 服务并存。
- MTProto：FakeTLS，供 Telegram 使用。

已安装后正常停止、启动和重启不会重置账号或密钥。无需手动逐项创建入站或粘贴反代；已有网站与证书保持由 1Panel 管理，初始化只添加本应用的反代文件。

## 前置条件

现有 HTTPS 站点和 DNS 需已就绪；对应 OCI 端口仍须由云端规则允许。程序没有 OCI/Cloudflare 管理权限，不会擅自修改云端策略。

细节见选定版本的 CONFIGURATION.md。3.11.0-local.1 为上一版手工配置模板，3.8.5 为原始模板，仅作参考。

官方项目：https://github.com/MHSanaei/3x-ui
文档：https://docs.sanaei.dev/
许可：GPL-3.0。

## 版本与升级

保留 `3.8.5`、`3.11.0-local.1`（生成手工配置说明）和 `3.11.0-local.2`（安装时自动初始化）。两个定制版本均使用上游 `v3.11.0`，一键版沿用附件提供的镜像 digest。根元数据限制为单实例。

已关闭跨版本升级：旧版数据库没有一键版所需的状态及就绪标记，而提供的升级脚本不会补做初始化。现有实例请先备份数据库、证书和配置，另行规划迁移，不能将一键安装视为无损升级。

自动接入要求已有匹配域名和有效证书的 1Panel HTTPS 站点，且 OpenResty 使用 host 网络。宿主机还需 Python 3、Docker Compose、OpenSSL、ss 和 nsenter，安装钩子需以 root 执行。关闭自动 OpenResty 仅适合已经配置了等效反代的环境。

## 本次合入与验证

来源为用户提供的 `3xui-oneclick.zip`。保留既有图标、原始版本及默认域名，修正旧版和手工版的开关控件，补充运行数据忽略规则。未执行附件文档中的服务器安装步骤，也未将附件测试报告作为本次实测结果。

本次验证范围见 `VALIDATION.md`。尚未执行真实 1Panel 安装、容器启动、证书/站点接入或客户端流量测试；附件中指定的镜像 digest 也未在本环境拉取验证。
