## 产品介绍

**3X-UI** 是一个开源的、功能强大的 Xray 面板，提供直观的 Web 界面来管理和监控 Xray 内核。

主要特性：

- **多协议支持**：Vmess、Vless、Trojan、ShadowSocks、Wireguard、Hysteria、Tunnel、Mixed、HTTP、Tun、MTProto、AmneziaWG 等
- **多用户管理**：支持创建、限速、流量统计、到期管理
- **多语言界面**：内置中、英、俄、波斯、阿拉伯等十余种语言
- **安全特性**：内置 Fail2ban、VMess AEAD 强制加密、TLS 证书管理
- **订阅链接**：自动生成兼容主流客户端的订阅链接

更多信息请参考：

- [官方文档](https://docs.sanaei.dev/)
- [GitHub 仓库](https://github.com/MHSanaei/3x-ui)

## 使用说明

1. 安装完成后，访问 `http://服务器IP:面板端口` 进入 3X-UI 面板
2. 首次进入会要求设置管理员账号和密码
3. 在面板中可以创建各种代理协议的用户和入站
4. 默认 Xray 入站端口为 8443，可在安装时修改

## 注意事项

- 面板默认监听端口为 `2053`，Xray 入站端口默认为 `8443`，请确保防火墙已放行
- 数据和证书目录挂载至 `data/db` 和 `data/cert`，请定期备份
- 该项目遵循 **GPL-3.0** 协议
