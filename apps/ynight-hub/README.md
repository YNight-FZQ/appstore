## 产品介绍

YNight Hub 的后端服务，提供业务接口、登录认证、Redis 缓存、MySQL 持久化、Elasticsearch 日志和 Cloudflare R2 对象存储。

## 安装说明

- 安装前准备可访问的 MySQL、Redis、Elasticsearch 和 R2 服务，确认它们与应用处于 `1panel-network` 中，或填写容器可访问的地址。
- 服务仅监听主机的 `127.0.0.1:3003`（端口可在安装时修改）；需要公网访问时，通过 1Panel/OpenResty 配置反向代理。
- 本应用包含 Watchtower，每 300 秒检查并更新本应用容器的 `latest` 镜像。镜像如需 GHCR 私有仓库认证，先在主机配置 Docker 登录，并将其 `config.json` 的绝对路径填入安装表单。1Panel 拉取首个镜像也必须具备相应的仓库权限。
- `ARIA_DOWNLOAD_DIR` 是 aria2 容器内的下载目录路径；应与 aria2 的实际目录一致。该值并不在本应用容器中挂载下载目录。
- `REDIS_DB` 是服务端实际读取的 Redis 库号变量。安装表单中填写的密钥会保存在 1Panel 生成的 `.env` 中，请控制该文件的访问权限。
- 应用健康检查只验证 HTTP 服务存活，不包含 MySQL、Redis、Elasticsearch 等依赖的就绪检查。
