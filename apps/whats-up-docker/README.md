# What's Up Docker（WUD）

WUD 是独立的容器镜像更新监控与自动化工具，不依赖 Watchtower。它通过 watcher 读取 Docker 容器信息并查询镜像仓库，比较可用的标签或镜像摘要；触发器负责通知、手动操作或自动更新。Web 页面展示容器和更新状态，并允许对已配置更新触发器的容器发起手动操作。

本应用包使用上游 `getwud/wud:latest`，上游支持 amd64 / arm64，容器内部端口为 3000，数据使用 SQLite，存储在 `/store`。上游许可证为 MIT，官方图标和许可证随包保留。

应用版本目录 `1.0.0` 是本地配置包编号，独立于上游镜像版本；程序更新由 WUD 自更新完成，见下文「自更新」。旧目录 `9.8.0`（固定上游镜像编号的原始包）仍保留，供新旧配置对比和回退参考；由于 `1.0.0` 的数字编号低于 `9.8.0`，1Panel 不会为 `9.8.0` 实例提供 `1.0.0` 的升级候选，两者按独立应用版本对待。

## 安装

将本应用目录放入目标面板安装目录的 `1panel/resource/apps/local/whats-up-docker`，同步本地应用，选择 `1.0.0`。需要已有 `1panel-network` 网络。

安装时设置 HTTP 端口、管理员用户名和强密码。默认宿主机地址为 `127.0.0.1:3800`；最终绑定地址还需核对 1Panel 高级设置。在宿主机访问 `http://127.0.0.1:3800`，或从可信网络通过带 HTTPS 和访问控制的反向代理访问。容器反代在相同网络时可使用 `http://<实际容器名>:3000`。

初次启动时由表单创建管理员。**环境变量会在每次启动时更新同名管理员凭据**；如需修改该管理员密码，在 1Panel 应用参数中修改并重建容器，不要只在 WUD 页面修改后忘记同步参数。密码保存在安装实例的 `.env` 中，限制对该文件的访问。

## 监控和自动更新

WUD 默认发现并监控本机运行中的容器。此包自身也纳入监控并允许自更新，见下文「自更新」。是否发现更新取决于镜像仓库和标签；私有镜像需要另行配置对应仓库的身份认证。

本包注册名为 `docker.autoupdate` 的 Docker 更新触发器，启用自动执行，但 `INCLUDEBYDEFAULT=false`，所以**默认不会自动更新任何其他容器**。要让某个容器自动更新，在该目标服务的 Compose 中添加并重建该目标容器：

```yaml
labels:
  wud.trigger.docker.autoupdate.enabled: "true"
```

只要原有标签存在，请将此项合并进去。WUD 的 Docker 触发器会在检测到更新时拉取镜像并重建目标容器，产生短暂中断；它使用 Docker 接口操作容器，不会同步 1Panel 应用商店的版本目录，也不负责替你完成数据库迁移。对 1Panel 管理的应用，应先备份并验证该应用的重建和回滚方式。

WUD 页面可查看和筛选容器、更新状态，并对已配置可用更新触发器的容器手动操作；它并不保证可以在页面中直接为 Docker 容器永久添加或移除上述标签。需在目标容器的 Compose 中修改标签并重建，选择才会持续生效。

如需排除某个容器的监控，可设置 `wud.watch: "false"`。WUD 标签与 Watchtower 的 `com.centurylinklabs.watchtower.enable` 是不同体系，互不影响；不要对同一容器同时启用两个更新器，否则会并发重建。

### 本商店中以 `latest` 镜像运行的应用

以下应用使用浮动的 `latest` 标签，WUD 必须比对镜像 digest 才能发现更新，因此仅加 `wud.trigger.docker.autoupdate.enabled` 是不够的。它们自各自 `1.1.0` 配置包起已内置完整的四个标签：

| 应用 | 版本 | 镜像公开性 |
| --- | --- | --- |
| `freellmapi` | `1.1.0` | 公开 |
| `qoder2api-hub` | `1.1.0` | 公开 |
| `subconverter` | `1.1.0` | 公开 |
| `tavily-proxy` | `1.1.0` | 公开 |
| `ynight-hub` | `1.1.0` | **私有**，需为 WUD 配置 GHCR 凭证 |

```yaml
labels:
  wud.watch: 'true'
  wud.watch.digest: 'true'
  wud.tag.include: '^latest$'
  wud.trigger.docker.autoupdate.enabled: 'true'
```

`wud.tag.include` 用于把候选标签限定为目标标签：WUD 5.7.1 起对非语义化标签会按字母倒序挑选「最高」标签作为更新候选，不加过滤可能把其他标签误判为更新。

对于私有仓库（如 `ynight-hub`），宿主机上的 `docker login ghcr.io` 只解决 Docker 拉取；WUD 查询更新走自己的 registry 模块，不读取 Docker 凭据文件，必须在 WUD 中单独配置。

凭证在**安装表单**中填写，对应的两个字段都可以留空：

| 表单字段 | 说明 |
| --- | --- |
| 私有 GHCR 用户名 | GitHub 用户名 |
| 私有 GHCR 令牌 | classic PAT，勾选 `read:packages` |

表单值由 1Panel 写入实例目录的 `.env`，Compose 通过 `${WUD_REGISTRY_GHCR_LOCAL_USERNAME:-}` 注入容器，不会进入版本库。

- **两个都填**：WUD 注册 `ghcr.local` 实例，可查询私有镜像的更新。
- **两个都留空**：`ghcr.local` 实例注册失败，WUD 启动日志出现一条 `Some registries failed to register` 警告。这属于正常情况，`ghcr.public` 匿名实例不受影响，公开镜像照常检测更新；私有镜像容器会显示为无法检测更新，不会被自动更新。
- **只填一个**：等同于留空，同样只有警告。请成对填写。

已安装的实例可在 1Panel 的「应用参数」中补填这两项，保存后重建容器生效。

这些标签只对重建过的容器生效。已安装的旧实例需在 1Panel 中升级配置包并重建容器。WUD 仅重建容器，不升级 1Panel 配置包，也不执行数据迁移。

## 自更新

WUD 可以更新自己，但这是官方文档明确的特例：触发器需要停止 WUD 容器，而停止就会杀掉那个还没完成删除、重建、启动的进程，容器会一直停着（`docker stop` 不触发重启策略）。因此 WUD **默认拒绝**自更新，只打印一条错误日志。

本包已开启自更新：

```yaml
environment:
  WUD_TRIGGER_DOCKER_AUTOUPDATE_SELFUPDATE: 'true'
  WUD_TRIGGER_DOCKER_AUTOUPDATE_SELFUPDATETIMEOUT: '120000'
```

开启后 WUD 把整个替换过程交给一个临时的 `wud-self-update` 辅助容器：

1. 先以临时名称创建替代容器，此时尚未触碰原容器
2. 停止当前 WUD 容器
3. 启动替代容器
4. 等待其通过健康检查
5. 成功后删除旧容器并把替代容器改名为原名
6. 失败则删除替代容器并重启旧容器

辅助容器运行的是**当前**镜像（不是要安装的新镜像），因此执行替换的代码版本总是已知可用的。`SELFUPDATETIMEOUT`（毫秒）是等待新容器健康的时限，超时即回滚。

辅助容器**不会被自动清理**：自更新若失败，WUD 已经不在运行，无法记录原因，辅助容器的日志是唯一线索。用 `docker logs wud-self-update` 查看。下次自更新会替换它，因此最多只留一个。

### 依赖条件

- 自更新要求 watcher 通过 **socket** 访问 Docker，不支持 `WUD_WATCHER_{name}_HOST` 的 TCP 方式。本包使用 `/var/run/docker.sock`，满足条件。
- WUD 通过 `/proc/self/mountinfo` 识别自身容器。若你的运行时未在该文件暴露容器 id，需要显式设置 `WUD_CONTAINER_ID`；正常情况下不需要。
- 镜像自带 `HEALTHCHECK`（`curl /health`），自更新会用它校验新版本，通过后才删除旧容器。

### 与 1Panel 的关系

WUD 自更新只重建容器，**不会改写 `docker-compose.yml`**。本包因此改用 `getwud/wud:latest`：镜像名不随版本变化，自更新后 Compose 与实际运行的容器保持一致，1Panel 重建容器时不会回退到旧版本。若固定成 `getwud/wud:9.8.0`，自更新到新版本后 Compose 仍写旧版本，任何一次 1Panel 重建都会静默降级。

**注意**：`latest` 意味着上游发布破坏性变更时会直接生效。自更新有健康检查和 120 秒超时回滚兜底，但无法覆盖数据格式变更这类不体现在健康检查里的问题。升级前应保留 `./data` 备份；WUD 的 SQLite 状态若不兼容，会表现为容器健康但数据异常。

若不想让 WUD 自更新，可改为 `wud.watch: 'false'` 或加 `wud.trigger.exclude: docker.autoupdate` 标签，由你在 1Panel 中手动升级。此时 WUD 仍会在看板中报告自身有更新。

## 持久化与权限

`./data` 绑定到容器内 `/store`，保存 WUD 的 SQLite 状态和用户信息；备份时停止服务并保留 `data` 和安装参数。仅同步应用商店不会修改已安装容器。官方镜像自带 `/health` 健康检查。

为发现和更新容器，WUD 挂载宿主机 Docker socket。拥有该接口的进程可以控制容器并获得接近宿主机管理员的权限；即使将 socket 标记为只读也不能把 Docker API 变成只读。只允许可信人员访问 WUD 看板。

## 参数来源及验证

- [9.8.0 发布记录](https://github.com/getwud/wud/releases/tag/9.8.0)、[Dockerfile](https://github.com/getwud/wud/blob/9.8.0/Dockerfile) 和 [官方快速开始](https://github.com/getwud/wud/blob/9.8.0/website/docs/quickstart/README.md)
- [监控与过滤规则](https://github.com/getwud/wud/blob/9.8.0/website/docs/configuration/watchers/README.md)
- [触发器及逐容器配置](https://github.com/getwud/wud/blob/9.8.0/website/docs/configuration/triggers/README.md)、[Docker 更新](https://github.com/getwud/wud/blob/9.8.0/website/docs/configuration/triggers/docker/README.md)
- [用户认证](https://github.com/getwud/wud/blob/9.8.0/website/docs/configuration/authentications/README.md)、[存储](https://github.com/getwud/wud/blob/9.8.0/website/docs/configuration/storage/README.md)

- [自更新说明](https://github.com/getwud/wud/blob/9.8.0/website/docs/configuration/triggers/docker/README.md#-updating-wud-itself)

本包仅完成源代码、参数引用和配置结构核对。未运行 Docker Compose、容器启动、1Panel 安装、自动更新或自更新实机测试。上游官方 `website/static/img/wud-logo-256.png` 用作应用图标。
