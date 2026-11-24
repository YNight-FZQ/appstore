# New API

New API 是多模型 API 网关，可集中管理渠道、API 密钥、额度和用量。配置包 `1.0.0` 使用官方镜像 `calciumion/new-api:latest`，支持 `amd64` 和 `arm64`。

## 安装与使用

1. 将应用目录放入目标 1Panel 安装目录下的 `1panel/resource/apps/local/newapi`，同步本地应用后选择 `1.0.0`。
2. 用 `openssl rand -hex 32` 生成会话密钥并填入安装表单。默认使用单容器 SQLite 部署。若使用现有 MySQL、PostgreSQL 或 Redis，在表单中填写对应连接串，并确保容器能连接到该服务。
3. 从宿主机访问 `http://127.0.0.1:3000`，按初始化向导创建管理员。默认绑定宿主机回环地址，也可通过反向代理访问容器的 `3000` 端口。

初始化后在控制台添加上游渠道并创建 API 密钥。OpenAI 兼容客户端使用服务地址加 `/v1` 作为 API 基址。使用 HTTPS 反向代理时，可在 Compose 中设定 `SESSION_COOKIE_SECURE=true`，并用 `SESSION_COOKIE_TRUSTED_URL` 填写控制台的完整 HTTPS 源地址。

## 数据与更新

安装目录的 `data/` 对应容器内 `/data`，保存默认 SQLite 数据库及日志。备份时保留该目录和实例的 `.env`，并在恢复时沿用原会话密钥。外部数据库的数据通过对应数据库工具备份。更改数据库连接串会切换存储，已有数据需单独迁移。

配置包编号独立于上游版本。已安装的 WUD 可以按摘要监控 `latest` 镜像。程序更新前保留数据备份，再拉取镜像并重建容器。

部署参数和图标来自上游。[Docker 快速开始](https://github.com/QuantumNous/new-api#quick-start) · [环境变量](https://docs.newapi.ai/en/docs/installation/config-maintenance/environment-variables) · [图标](https://github.com/QuantumNous/new-api/blob/v1.0.0-rc.51/web/public/logo.png) · [上游许可证](LICENSE.upstream)
