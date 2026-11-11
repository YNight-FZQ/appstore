# Tavily Proxy Manager

> 应用包仅保留版本号目录 `1.0.0`，不再提供 `latest` 目录，主镜像仍使用 `latest`。当前未完成容器或 1Panel 实机验证。

Tavily Proxy Manager 将多个 Tavily API Key 汇聚在一个 Master Key 后面，并提供管理面板。应用使用 `ghcr.io/xuncv/tavilyproxymanager:latest`，支持 `amd64` 和 `arm64`。

## 安装与使用

在 1Panel 中同步本地应用后安装。安装表单可以修改宿主机 HTTP 端口，默认映射为 `127.0.0.1:8090:8080`。在宿主机访问 `http://127.0.0.1:8090`；从同一 `1panel-network` 内的其他容器访问时，使用 `http://tavily-proxy:8080`。

安装后可在 1Panel 的“网站 → 创建网站 → 一键部署 → 已装应用”中选择该实例并绑定域名。若应用包的类型刚从 `tool` 改为 `website`，请先在 1Panel 中重新同步本地应用；已关联网站的实例不会再次出现在该列表中。

首次启动会自动生成 Master Key。到 1Panel 的应用日志中搜索 `master key`，取得登录管理面板和调用 API 所需的密钥。之后在管理面板添加自己的 Tavily API Key。不要将 Master Key 或 Tavily API Key 提交到版本库。

SQLite 数据库位于应用安装目录的 `data/proxy.db`，容器内路径为 `/app/data/proxy.db`。请备份此数据目录；删除或重建数据库会影响已保存的密钥与记录。

宿主机端口仅绑定回环地址，但同一 `1panel-network` 内的容器仍能直接访问 8080 端口。若需要从外部访问，请自行配置反向代理及访问控制。

## 版本与升级

`1.0.0` 是本地应用配置版本，与上游镜像版本无关。拉取最新镜像并重建容器可更新程序；新镜像可能包含数据迁移，更新前核对上游并备份完整 `data` 目录。仅同步商店不会更改现有实例。

旧 `latest` 目录已从本应用包中删除。它与 `1.0.0` 的内容曾完全一致，此前从 `latest` 安装的实例可继续运行；如需统一到 `1.0.0`，请先备份 `data` 目录到实例目录之外，再新建实例恢复并核验数据，不要直接卸载旧实例后重装。

官方资料：[项目说明](https://github.com/xuncv/TavilyProxyManager#readme)、[Dockerfile](https://github.com/xuncv/TavilyProxyManager/blob/main/Dockerfile)。
