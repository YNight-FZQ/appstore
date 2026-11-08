# FreeLLMAPI

> 配置包 `1.0.0` 使用独立编号和 `latest` 镜像。请先备份数据和原加密密钥；本版本尚未完成 1Panel 实机或容器启动验证。



FreeLLMAPI 是一个本地优先、单用户的多服务商 LLM 网关。它将用户添加的服务商密钥及自建 OpenAI 兼容端点聚合到统一 API，提供路由、限流跟踪、故障切换和 Web 看板。项目采用 MIT 许可。

## 适配结论

可以封装为 1Panel 应用：上游提供 `linux/amd64`、`linux/arm64` 的预构建镜像，Express API 与构建后的 React 看板由同一进程在 `3001` 端口提供服务；SQLite 存储在 `/app/server/data`，不依赖额外 MySQL、Redis 或 GPU。

配置包 `1.0.0` 的镜像为 `ghcr.io/tashfeenahmed/freellmapi:latest`，包版本不代表上游镜像版本；旧版应用包仍固定原有镜像。运行镜像以 root 入口修正数据目录属主，再降权为 `node` 用户启动服务，沿用上游行为。

主要能力包括 OpenAI 兼容 `/v1`、Anthropic Messages、Responses，以及按服务商实际能力提供的媒体与嵌入接口。模型池、可用性和额度取决于你添加的服务商账号，不是自带的无限免费服务。路由器本身采用 MIT 许可；上游实时目录有 Premium 服务，免费目录更新存在延迟，详见上游说明。

## 安装

将 `freellmapi` 应用目录放入目标面板安装路径下的 `1panel/resource/apps/local/`，同步本地应用后选择 `1.0.0`。需要已有 `1panel-network` 网络，并允许执行安装脚本。宿主机初始化需要 Bash、OpenSSL 及常规 coreutils/grep；不需要宿主机安装 Node.js。

安装表单：

| 参数 | 默认值 | 用途 |
| --- | --- | --- |
| HTTP 端口 | `3001` | 看板和 API 共用的宿主机端口 |
| 允许访问的主机名 | `localhost` | 反代访问时添加实际域名；多个以逗号分隔，不带协议和端口 |
| 信任的反向代理 | `false` | 单层可信反代可设 `1`，或填实际代理 IP/CIDR |

Compose 默认发布到 `127.0.0.1:<HTTP端口>`；最终端口绑定还需核对 1Panel 高级设置。上游定位为个人私有使用，建议通过 SSH 转发或可信私有网络访问。远程反代应使用 HTTPS，并将域名加入主机名表单；可信反代设置须与真实拓扑匹配。

宿主机访问 `http://127.0.0.1:3001/`。容器化反代若在 `1panel-network` 中，可访问 `http://<实际容器名>:3001`。

首次使用在看板创建账号，没有预置管理员密码。远程请求创建第一个账号时，上游可能要求一次性 setup code，可在 1Panel 容器启动日志中查看。该码属于私密初始化信息，不要公开日志。

## 添加服务商与接入客户端

在 **Keys** 页面添加自己申请的服务商 API Key，也可以添加自建 OpenAI 兼容端点。出站代理建议在看板中配置。容器里的 `localhost` 指容器自身；本包保留上游的 `host.docker.internal:host-gateway` 映射，宿主机服务仍须监听容器可达的地址。

OpenAI 兼容客户端的 Base URL 使用 `http://127.0.0.1:3001/v1`（或实际网关地址），API Key 使用看板中的统一密钥 `freellmapi-...`，模型可以用 `auto` 或实际模型 ID。

客户端到网关、网关到服务商是两段连接；服务器需要能访问所选上游。健康检查 `/api/ping` 只验证本地进程响应，不能验证上游模型或账号额度。

## 密钥与数据持久化

- `./data` → `/app/server/data`：数据库、设置、服务商加密凭据、用量和其他持久化状态。
- `./conf/app.env`：初始化生成的 `ENCRYPTION_KEY`，通过 Compose `env_file` 注入，文件权限为 `0600`，配置目录为 `0700`。

上游生产模式要求显式提供 32 字节、64 位十六进制的加密密钥。本包在首次安装时使用 OpenSSL 生成，只在不存在数据库且没有旧密钥时创建。重复运行保留原密钥；发现损坏密钥或已有数据库但密钥丢失时停止，避免静默换钥导致凭据无法解密。初始化不输出密钥。

备份应同时保留完整 `data` 目录和 `conf/app.env`，备份前停止服务。只备份数据库不能恢复加密凭据；恢复时必须使用原始密钥。数据库中也可能含日志或缓存等敏感内容，按私密数据管理备份。

升级前应备份完整数据及密钥。已开放从 `0.16.x` 旧包跨主版本升级到 `1.0.0`；升级脚本只校验原密钥，不生成新密钥。Compose 的可选 env_file 用于处理 1Panel 升级预检临时目录缺少密钥文件的问题，要求 Docker Compose 支持 `env_file.required`（2.24.0 及以上）；实际升级和缺钥保护仍须在目标 1Panel 版本验证。若密钥缺失或无效，恢复原密钥后才能升级。配置包版本独立于镜像版本；拉取最新镜像并重建容器才能更新程序。新镜像可能包含数据库迁移或不兼容变更，更新前请核对上游并备份。本包不部署 Watchtower，也不提供看板一键更新容器功能。

## 来源与验证边界

调研日期：2026-10-30。参数依据上游正式版：

- [发布记录 v0.16.20](https://github.com/tashfeenahmed/freellmapi/releases/tag/v0.16.20)
- [Docker 部署说明](https://github.com/tashfeenahmed/freellmapi/blob/v0.16.20/docker/README.md)
- [Dockerfile](https://github.com/tashfeenahmed/freellmapi/blob/v0.16.20/Dockerfile) 与 [入口脚本](https://github.com/tashfeenahmed/freellmapi/blob/v0.16.20/docker-entrypoint.sh)
- [环境变量](https://github.com/tashfeenahmed/freellmapi/blob/v0.16.20/.env.example) 与 [密钥校验实现](https://github.com/tashfeenahmed/freellmapi/blob/v0.16.20/server/src/lib/crypto.ts)
- [镜像发布与架构](https://github.com/tashfeenahmed/freellmapi/blob/v0.16.20/.github/workflows/docker.yml)
- [中文项目介绍及 Premium 边界](https://github.com/tashfeenahmed/freellmapi/blob/v0.16.20/README.zh-cn.md)

`logo.png` 根据上游 `client/public/favicon.svg` 的品牌圆点和路由环矢量参数栅格化，使用本项目自身标识。上游 [MIT 许可证](https://github.com/tashfeenahmed/freellmapi/blob/v0.16.20/LICENSE) 见本目录 `LICENSE.upstream`。

本次完成 YAML、表单引用、PNG、Shell 语法、Compose 配置及密钥生成/保留/丢失/损坏等场景检查。环境没有 Ruby，仓库 Ruby 检查器无法执行，使用 Python 验证同类静态规则。未执行镜像拉取、容器启动、1Panel 实机安装、注册或真实推理验收。
