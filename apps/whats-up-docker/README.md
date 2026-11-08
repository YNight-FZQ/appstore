# What's Up Docker（WUD）

WUD 是独立的容器镜像更新监控与自动化工具，不依赖 Watchtower。它通过 watcher 读取 Docker 容器信息并查询镜像仓库，比较可用的标签或镜像摘要；触发器负责通知、手动操作或自动更新。Web 页面展示容器和更新状态，并允许对已配置更新触发器的容器发起手动操作。

本应用包使用上游稳定版 `getwud/wud:9.8.0`，上游支持 amd64 / arm64，容器内部端口为 3000，数据使用 SQLite，存储在 `/store`。上游许可证为 MIT，官方图标和许可证随包保留。

## 安装

将本应用目录放入目标面板安装目录的 `1panel/resource/apps/local/whats-up-docker`，同步本地应用，选择 `9.8.0`。需要已有 `1panel-network` 网络。

安装时设置 HTTP 端口、管理员用户名和强密码。默认宿主机地址为 `127.0.0.1:3800`；最终绑定地址还需核对 1Panel 高级设置。在宿主机访问 `http://127.0.0.1:3800`，或从可信网络通过带 HTTPS 和访问控制的反向代理访问。容器反代在相同网络时可使用 `http://<实际容器名>:3000`。

初次启动时由表单创建管理员。**环境变量会在每次启动时更新同名管理员凭据**；如需修改该管理员密码，在 1Panel 应用参数中修改并重建容器，不要只在 WUD 页面修改后忘记同步参数。密码保存在安装实例的 `.env` 中，限制对该文件的访问。

## 监控和自动更新

WUD 默认发现并监控本机运行中的容器；此包自身通过 `wud.watch=false` 排除。是否发现更新取决于镜像仓库和标签；私有镜像需要另行配置对应仓库的身份认证。

本包注册名为 `docker.autoupdate` 的 Docker 更新触发器，启用自动执行，但 `INCLUDEBYDEFAULT=false`，所以**默认不会自动更新任何其他容器**。要让某个容器自动更新，在该目标服务的 Compose 中添加并重建该目标容器：

```yaml
labels:
  wud.trigger.docker.autoupdate.enabled: "true"
```

只要原有标签存在，请将此项合并进去。WUD 的 Docker 触发器会在检测到更新时拉取镜像并重建目标容器，产生短暂中断；它使用 Docker 接口操作容器，不会同步 1Panel 应用商店的版本目录，也不负责替你完成数据库迁移。对 1Panel 管理的应用，应先备份并验证该应用的重建和回滚方式。

WUD 页面可查看和筛选容器、更新状态，并对已配置可用更新触发器的容器手动操作；它并不保证可以在页面中直接为 Docker 容器永久添加或移除上述标签。需在目标容器的 Compose 中修改标签并重建，选择才会持续生效。

如需排除某个容器的监控，可设置 `wud.watch: "false"`。WUD 标签与 Watchtower 的 `com.centurylinklabs.watchtower.enable` 是不同体系：FreeLLMAPI 的 Watchtower 禁用标签不会自动禁止 WUD 的触发器。已有 YNight Hub 自带 Watchtower；如将同一容器交给 WUD，请先停用原 Watchtower 对它的更新，避免两个管理器并发重建。不要在未检查作用范围的情况下开启全局自动更新。

## 持久化与权限

`./data` 绑定到容器内 `/store`，保存 WUD 的 SQLite 状态和用户信息；备份时停止服务并保留 `data` 和安装参数。仅同步应用商店不会修改已安装容器。官方镜像自带 `/health` 健康检查。

为发现和更新容器，WUD 挂载宿主机 Docker socket。拥有该接口的进程可以控制容器并获得接近宿主机管理员的权限；即使将 socket 标记为只读也不能把 Docker API 变成只读。只允许可信人员访问 WUD 看板。

## 参数来源及验证

- [9.8.0 发布记录](https://github.com/getwud/wud/releases/tag/9.8.0)、[Dockerfile](https://github.com/getwud/wud/blob/9.8.0/Dockerfile) 和 [官方快速开始](https://github.com/getwud/wud/blob/9.8.0/website/docs/quickstart/README.md)
- [监控与过滤规则](https://github.com/getwud/wud/blob/9.8.0/website/docs/configuration/watchers/README.md)
- [触发器及逐容器配置](https://github.com/getwud/wud/blob/9.8.0/website/docs/configuration/triggers/README.md)、[Docker 更新](https://github.com/getwud/wud/blob/9.8.0/website/docs/configuration/triggers/docker/README.md)
- [用户认证](https://github.com/getwud/wud/blob/9.8.0/website/docs/configuration/authentications/README.md)、[存储](https://github.com/getwud/wud/blob/9.8.0/website/docs/configuration/storage/README.md)

本包仅完成源代码、参数引用和配置结构核对。由于当前云执行环境启动失败，未运行仓库 Ruby 校验器、Docker Compose、镜像启动、1Panel 安装或自动更新实机测试。上游官方 `website/static/img/wud-logo-256.png` 用作应用图标。
