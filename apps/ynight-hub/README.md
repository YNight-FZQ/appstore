## 产品介绍

> 应用包同时保留版本号目录 `1.0.0` 与 `1.1.0`，不再提供 `latest` 目录；应用主镜像仍使用 `latest`，并由 What's Up Docker 自动更新。升级前备份配置、密钥、数据库和 Elasticsearch 数据；本版本尚未完成容器或 1Panel 实机验证。

YNight Hub 的后端服务，提供业务接口、登录认证、Redis 缓存、MySQL 持久化、内置 Elasticsearch 日志和 Cloudflare R2 对象存储。

## 安装说明

- 安装前在 1Panel 中安装 MySQL 和 Redis，并在安装表单中选择已有服务。1Panel 会按表单随机生成 MySQL 数据库名、用户名和密码，并创建数据库。选择 1Panel 管理的 Redis 后，表单会按 `PANEL_REDIS_ROOT_PASSWORD` 自动填入该服务的密码；连接外部 Redis 时仍可手动修改。
- 配置包 `1.1.0` 的应用变量示例位于 `1.1.0/conf/app.env.example`。首次安装时，初始化脚本会将其复制为安装目录中的 `conf/app.env`，并生成 JWT 签名密钥及 Elasticsearch 密码。请在实际的 `conf/app.env` 中填写 R2 和业务令牌等配置，随后在 1Panel 中重建应用，使新环境变量进入容器；仅重启容器不会更新环境变量。安装前也可以先填写本地应用包中的示例文件。1Panel 生成的 `.env` 保存 MySQL、Redis、端口参数和 Elasticsearch 密码。
- Elasticsearch 8.19 与应用同编排运行，只连接 `1panel-network`。应用通过实例专属的 Elasticsearch 容器名连接，避免多个实例相互串连；兼容别名 `ynight-hub-elasticsearch` 仍保留在共享网络中，多个实例可能产生重复别名，其他容器应使用具体实例的容器名。同一 `1panel-network` 的其他容器也可访问 Elasticsearch 的容器端口（仍需认证，容器间 HTTP 未启用 TLS），请避免依赖共享网络上的通用 `elasticsearch` 服务名，以免与其他实例的名称冲突。不开放宿主机端口，索引数据保存在 `elasticsearch-data` 卷中。其容器内存上限为 2 GiB，JVM 堆固定为 1 GiB，异常退出最多自动重试 3 次，避免无上限占用主机内存或持续重启。应用等待 Elasticsearch 通过健康检查后再启动，避免初始化连接过早失败。此卷不会自动迁移旧 Elasticsearch 的日志，也不应在卸载或重建时删除。请使用 Elasticsearch 快照备份索引。
- 当前服务器的 `vm.max_map_count` 为 65530，本编排设置 `node.store.allow_mmap=false` 避免修改宿主机内核参数。这会降低索引读写性能；如需较高吞吐量，可先将宿主机 `vm.max_map_count` 持久设置为 1048576，再移除此项配置。
- 服务仅监听主机的 `127.0.0.1:3003`（端口可在安装时修改）；需要公网访问时，通过 1Panel/OpenResty 配置反向代理。
- 本应用**不再内置 Watchtower**，改由宿主机上的 What's Up Docker（WUD）接管主容器的镜像更新，见下节。请勿同时启用两个更新器，否则会并发重建同一容器。主镜像位于 GHCR 私有仓库：1Panel 和 WUD 拉取镜像都依赖宿主机的 `docker login ghcr.io` 凭据，而 WUD 查询镜像更新还需要单独配置 registry 凭证，两者不能互相替代，详见「自动更新」一节。
- `ARIA_DOWNLOAD_DIR` 是 aria2 容器内的下载目录路径；应与 aria2 的实际目录一致。该值并不在本应用容器中挂载下载目录。
- `REDIS_DB` 是服务端实际读取的 Redis 库号变量。安装表单的数据库与 Redis 参数保存在 1Panel 生成的 `.env` 中；其他密钥保存在 `conf/app.env` 中，请控制这两个文件的访问权限。
- 应用健康检查只验证 HTTP 服务存活，不包含 MySQL、Redis、Elasticsearch 等依赖的就绪检查。

- 本应用的两个容器（app、Elasticsearch）均只加入 `1panel-network`。MySQL、Redis 是另选的独立服务，其网络配置由对应应用管理。对已经安装的实例，同步本地应用模板不会自动重建容器；需在已安装应用中同步更新 Compose 并重建，保留数据卷及密钥文件。

- 已安装实例同步应用商店不会自动变更当前容器。从 `1.0.0` 升级到 `1.1.0` 后，`watchtower` 服务已从编排中移除，1Panel 重建实例时该容器会被删除；其挂载的 `/var/lib/docker/config.json` 只读挂载也随之消失。若升级后仍残留 `*-watchtower` 容器，请手动执行 `docker rm -f <容器名>`，避免它与 WUD 并发更新主容器。

## 配置包升级

`1.1.0` 仅代表本地配置版本，应用主镜像 `ghcr.io/ynightfzq/ynight-hub/server:latest` 独立更新；Elasticsearch 仍固定为 8.19.22，不纳入自动更新。

升级前停止服务，分别备份实际安装目录的 `.env` 和 `conf/app.env`，以及 MySQL 数据、Redis 中需要保留的数据和 Elasticsearch 索引快照。升级脚本校验原 JWT 和 Elasticsearch 密码，不生成替代密钥。为处理 1Panel 升级预检的临时目录没有私有配置，`1.1.0` 的 `conf/app.env` 声明为可选；需要 Docker Compose 2.24.0 及以上支持 `env_file.required`，并须实际验证安装和升级。只同步应用商店不会更新已安装实例。

## 自动更新（What's Up Docker）

`1.1.0` 起，`app` 服务带有以下标签，由 [What's Up Docker](https://getwud.app/)（下称 WUD）接管主容器的镜像更新，原内置 Watchtower 服务已移除：

```yaml
wud.watch: 'true'
wud.watch.digest: 'true'
wud.tag.include: '^latest$'
wud.trigger.docker.autoupdate.enabled: 'true'
```

`wud.watch.digest` 不可缺少：主镜像使用浮动的 `latest` 标签，标签名不会变化，WUD 只有比对镜像 digest 才能发现更新。`wud.tag.include` 把候选标签限定为 `latest`，避免 WUD 把其他标签误判为更新。

Elasticsearch 使用固定版本 `8.19.22`，**未**加 WUD 标签，不会被自动更新，升级 Elasticsearch 仍须手动调整编排。

前提是宿主机已安装本商店的 `whats-up-docker` 应用（触发器名 `docker.autoupdate`）。WUD 发现新 digest 后会自行拉取镜像并重建 `app` 容器，期间有短暂中断；Elasticsearch 不受影响。

**WUD 只重建容器，不会升级 1Panel 配置包，也不执行数据迁移。** 主镜像若含数据库结构变更，更新前应备份 MySQL 数据和 `conf/app.env`。

### 私有镜像需要凭据

`ghcr.io/ynightfzq/ynight-hub/server` 是**私有** GHCR 仓库，匿名无法查询标签或 manifest。你已在宿主机执行 `docker login ghcr.io` 只能解决 Docker 拉取，**不能**让 WUD 查询仓库——WUD 通过自己的 registry 模块直接访问注册表 API，不读取 `~/.docker/config.json` 或 `/var/lib/docker/config.json`。

要让 WUD 检测该镜像的更新，需在 `whats-up-docker` 应用的**安装表单**中填写两个可选字段：

| 表单字段 | 填写内容 |
| --- | --- |
| 私有 GHCR 用户名 | GitHub 账号名 |
| 私有 GHCR 令牌 | classic PAT（`ghp_...`），勾选 `read:packages` |

字段值保存在 WUD 实例目录的 `.env` 中，不进入版本库。Compose 通过 `${WUD_REGISTRY_GHCR_LOCAL_USERNAME:-}` / `${WUD_REGISTRY_GHCR_LOCAL_TOKEN:-}` 注入容器。

**两项必须同时填写。** 都留空时 WUD 会在启动日志中报告一条 `ghcr.local` 注册失败警告，这不影响公开镜像的监控，但本应用会显示为无法检测更新，**不会**被自动更新。只填其中一项等同于留空。

> 注意：`docker login` 生成的凭据文件是 Docker 拉取镜像用的，与 WUD 的 registry 查询是两套独立机制。WUD 触发器在真正重建容器时调用 Docker 接口拉取镜像，这一步才使用宿主机的 `docker login` 凭据。

已安装的 `1.0.0` 实例需先手动升级到 `1.1.0` 并重建容器，标签才会生效。

旧 `latest` 目录已从本应用包中删除；`1.0.0` 目录仍保留，供新旧配置对比和回退参考，但 `crossVersionUpdate` 为 `true` 时 1Panel 会把 `1.1.0` 判定为可升级目标。此前从 `latest` 安装的实例仍可正常运行，但该包的 Compose 缺少 `conf/app.env` 的可选声明（`env_file` 的 `path` / `required: false`）和 `scripts/upgrade.sh`，1Panel 升级预检和升级流程可能失败。这类实例迁移到 `1.1.0` 前，请先备份完整安装目录到实例目录之外，再新建实例恢复并核验数据；不要直接卸载旧实例，1Panel 卸载可能连带删除实例目录。
