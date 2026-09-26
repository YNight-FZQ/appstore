## 产品介绍

YNight Hub 的后端服务，提供业务接口、登录认证、Redis 缓存、MySQL 持久化、内置 Elasticsearch 日志和 Cloudflare R2 对象存储。

## 安装说明

- 安装前在 1Panel 中安装 MySQL 和 Redis，并在安装表单中选择已有服务。1Panel 会按表单随机生成 MySQL 数据库名、用户名和密码，并创建数据库。选择 1Panel 管理的 Redis 后，表单会按 `PANEL_REDIS_ROOT_PASSWORD` 自动填入该服务的密码；连接外部 Redis 时仍可手动修改。
- 其余应用变量的示例位于 `latest/conf/app.env.example`。首次安装时，初始化脚本会将其复制为安装目录中的 `conf/app.env`，并生成 JWT 签名密钥及 Elasticsearch 密码。请在实际的 `conf/app.env` 中填写 R2 和业务令牌等配置，随后在 1Panel 中重建应用，使新环境变量进入容器；仅重启容器不会更新环境变量。安装前也可以先填写本地应用包中的示例文件。1Panel 生成的 `.env` 保存 MySQL、Redis、端口参数和 Elasticsearch 密码。
- Elasticsearch 8.19 与应用同编排运行，仅连接应用专用的内部 Docker 网络，不开放宿主机端口；索引数据保存在 `elasticsearch-data` 卷中。此卷不会自动迁移旧 Elasticsearch 的日志，也不应在卸载或重建时删除。请使用 Elasticsearch 快照备份索引。
- 当前服务器的 `vm.max_map_count` 为 65530，本编排设置 `node.store.allow_mmap=false` 避免修改宿主机内核参数。这会降低索引读写性能；如需较高吞吐量，可先将宿主机 `vm.max_map_count` 持久设置为 1048576，再移除此项配置。
- 服务仅监听主机的 `127.0.0.1:3003`（端口可在安装时修改）；需要公网访问时，通过 1Panel/OpenResty 配置反向代理。
- 本应用包含 Watchtower，每 300 秒检查并更新本应用容器的 `latest` 镜像。镜像如需 GHCR 私有仓库认证，先在主机配置 Docker 登录，并将凭据文件放在 `/var/lib/docker/config.json`，供 Watchtower 只读挂载。1Panel 拉取首个镜像也必须具备相应的仓库权限。
- `ARIA_DOWNLOAD_DIR` 是 aria2 容器内的下载目录路径；应与 aria2 的实际目录一致。该值并不在本应用容器中挂载下载目录。
- `REDIS_DB` 是服务端实际读取的 Redis 库号变量。安装表单的数据库与 Redis 参数保存在 1Panel 生成的 `.env` 中；其他密钥保存在 `conf/app.env` 中，请控制这两个文件的访问权限。
- 应用健康检查只验证 HTTP 服务存活，不包含 MySQL、Redis、Elasticsearch 等依赖的就绪检查。
