## 产品介绍

> 应用包仅保留版本号目录 `1.0.0`，不再提供 `latest` 目录；应用主镜像仍使用 `latest`。升级前备份配置、密钥、数据库和 Elasticsearch 数据；本版本尚未完成容器或 1Panel 实机验证。

YNight Hub 的后端服务，提供业务接口、登录认证、Redis 缓存、MySQL 持久化、内置 Elasticsearch 日志和 Cloudflare R2 对象存储。

## 安装说明

- 安装前在 1Panel 中安装 MySQL 和 Redis，并在安装表单中选择已有服务。1Panel 会按表单随机生成 MySQL 数据库名、用户名和密码，并创建数据库。选择 1Panel 管理的 Redis 后，表单会按 `PANEL_REDIS_ROOT_PASSWORD` 自动填入该服务的密码；连接外部 Redis 时仍可手动修改。
- 配置包 `1.0.0` 的应用变量示例位于 `1.0.0/conf/app.env.example`。首次安装时，初始化脚本会将其复制为安装目录中的 `conf/app.env`，并生成 JWT 签名密钥及 Elasticsearch 密码。请在实际的 `conf/app.env` 中填写 R2 和业务令牌等配置，随后在 1Panel 中重建应用，使新环境变量进入容器；仅重启容器不会更新环境变量。安装前也可以先填写本地应用包中的示例文件。1Panel 生成的 `.env` 保存 MySQL、Redis、端口参数和 Elasticsearch 密码。
- Elasticsearch 8.19 与应用同编排运行，只连接 `1panel-network`。应用通过实例专属的 Elasticsearch 容器名连接，避免多个实例相互串连；兼容别名 `ynight-hub-elasticsearch` 仍保留在共享网络中，多个实例可能产生重复别名，其他容器应使用具体实例的容器名。同一 `1panel-network` 的其他容器也可访问 Elasticsearch 的容器端口（仍需认证，容器间 HTTP 未启用 TLS），请避免依赖共享网络上的通用 `elasticsearch` 服务名，以免与其他实例的名称冲突。不开放宿主机端口，索引数据保存在 `elasticsearch-data` 卷中。其容器内存上限为 2 GiB，JVM 堆固定为 1 GiB，异常退出最多自动重试 3 次，避免无上限占用主机内存或持续重启。应用等待 Elasticsearch 通过健康检查后再启动，避免初始化连接过早失败。此卷不会自动迁移旧 Elasticsearch 的日志，也不应在卸载或重建时删除。请使用 Elasticsearch 快照备份索引。
- 当前服务器的 `vm.max_map_count` 为 65530，本编排设置 `node.store.allow_mmap=false` 避免修改宿主机内核参数。这会降低索引读写性能；如需较高吞吐量，可先将宿主机 `vm.max_map_count` 持久设置为 1048576，再移除此项配置。
- 服务仅监听主机的 `127.0.0.1:3003`（端口可在安装时修改）；需要公网访问时，通过 1Panel/OpenResty 配置反向代理。
- 本应用包含 Watchtower，每 300 秒检查并更新本应用容器的 `latest` 镜像。 为兼容 Docker 最低 API 版本为 1.44 的服务器，Watchtower 显式使用 `DOCKER_API_VERSION=1.44`；Docker 服务端必须支持该 API 版本。镜像如需 GHCR 私有仓库认证，先在主机配置 Docker 登录，并将凭据文件放在 `/var/lib/docker/config.json`，供 Watchtower 只读挂载。1Panel 拉取首个镜像也必须具备相应的仓库权限。
- `ARIA_DOWNLOAD_DIR` 是 aria2 容器内的下载目录路径；应与 aria2 的实际目录一致。该值并不在本应用容器中挂载下载目录。
- `REDIS_DB` 是服务端实际读取的 Redis 库号变量。安装表单的数据库与 Redis 参数保存在 1Panel 生成的 `.env` 中；其他密钥保存在 `conf/app.env` 中，请控制这两个文件的访问权限。
- 应用健康检查只验证 HTTP 服务存活，不包含 MySQL、Redis、Elasticsearch 等依赖的就绪检查。

- 本应用的三个容器（app、Elasticsearch、Watchtower）均只加入 `1panel-network`。MySQL、Redis 是另选的独立服务，其网络配置由对应应用管理。对已经安装的实例，同步本地应用模板不会自动重建容器；需在已安装应用中同步更新 Compose 并重建，保留数据卷及密钥文件。

- 已安装实例同步应用商店不会自动变更当前容器；需将 Watchtower 的 `DOCKER_API_VERSION: '1.44'` 同步到已安装的 Compose 配置并重建 Watchtower。仅重启不会注入新环境变量。重建后检查其日志并确认实际更新范围仍限于应用主容器。

## 配置包升级

`1.0.0` 仅代表本地配置版本，应用主镜像 `ghcr.io/ynightfzq/ynight-hub/server:latest` 独立更新；Elasticsearch 仍固定为 8.19.22，Watchtower 使用其默认镜像标签。

升级前停止服务，分别备份实际安装目录的 `.env` 和 `conf/app.env`，以及 MySQL 数据、Redis 中需要保留的数据和 Elasticsearch 索引快照。升级脚本校验原 JWT 和 Elasticsearch 密码，不生成替代密钥。为处理 1Panel 升级预检的临时目录没有私有配置，`1.0.0` 的 `conf/app.env` 声明为可选；需要 Docker Compose 2.24.0 及以上支持 `env_file.required`，并须实际验证安装和升级。只同步应用商店不会更新已安装实例。应用主镜像更新与配置包升级是两件事，拉取新镜像并重建容器可更新程序；原内置 Watchtower 也可更新主容器，应避免其他工具重复管理。

旧 `latest` 目录已从本应用包中删除。此前从 `latest` 安装的实例仍可正常运行，但该包的 Compose 缺少 `conf/app.env` 的可选声明（`env_file` 的 `path` / `required: false`）和 `scripts/upgrade.sh`，1Panel 升级预检和升级流程可能失败。这类实例迁移到 `1.0.0` 前，请先备份完整安装目录到实例目录之外，再新建实例恢复并核验数据；不要直接卸载旧实例，1Panel 卸载可能连带删除实例目录。
