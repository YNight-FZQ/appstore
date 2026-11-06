# Qoder2API-Hub

> 最新新增版本：`1.8.0`（旧版 `1.8.0` 保留）。请先备份数据；本次仅核对上游配置，尚未完成 1Panel 实机或容器启动验证。



[Qoder2API-Hub](https://github.com/shuishuipingan/qoder2api-hub) 是将 Qoder 国内版与国际版封装为 OpenAI / Anthropic 兼容接口的非官方网关，采用 MIT 许可证。需要使用者自行添加合法授权的 Qoder 账号，不提供账号或额度。

## 调研结论

- 支持 OpenAI Chat Completions、Responses API（Codex）及 Anthropic Messages（Claude Code）。
- 国内版与国际版使用独立账号池，支持模型选区、账号轮询、会话亲和及故障冷却。
- 提供 OAuth 设备授权、PAT 导入、Token 定时刷新、签到及 Web 用量看板。
- 网关以 Python 实现（1.8.0 镜像包含 Pillow，用于图片预处理），无需额外数据库或 Redis。上游容器使用 Python 3.11 Alpine，并包含 UMID 原生组件及兼容库。
- 本应用包版本为 **1.8.0**，固定使用上游镜像 `ghcr.io/shuishuipingan/qoder2api-hub:1.8.0`，支持 `amd64` / `arm64`。内部端口为 `8790`，镜像默认以 `python qoder_proxy.py --lan` 启动。
- 这是依赖上游非公开协议的项目，接口可用性、模型和账号额度取决于 Qoder；多账号不保证规避排队或限流。仅在私有环境中使用自己的授权账号，遵守上游服务条款。

## 安装与访问

将整个 `qoder2api-hub` 应用目录放入目标 1Panel 安装目录下的 `1panel/resource/apps/local/`，在面板同步本地应用，选择版本 `1.8.0` 安装。安装前需存在 1Panel 管理的 `1panel-network` 网络。

安装表单只配置宿主机 HTTP 端口，默认 `8790`。看板与 API 共用该端口。Compose 默认映射 `127.0.0.1:8790:8790`，最终发布地址仍须核对 1Panel 的高级设置。容器内部必须监听 `0.0.0.0`，这与宿主机的回环地址绑定分别生效。

- 在宿主机访问：`http://127.0.0.1:<HTTP端口>/`。
- 远程访问：建议使用 1Panel 的 HTTPS 反向代理；若反代位于同一 Docker 网络，可将上游设为 `http://<实际容器名>:8790`。也可通过 SSH 转发访问回环端口。
- 初始看板密码是上游默认的 `admin`，首次登录后立即在「设置」中修改。面板密码与 API Key 相互独立。
- 镜像保留默认 `--lan` 模式，首次启动会自动生成 API Key，保存到 `accounts/settings.json`，并写入启动日志。在修改默认面板密码后，可在「设置」中查看或管理 Key。
- 到「账号」页添加 OAuth 账号或导入 PAT。无需挂载宿主机官方客户端凭证目录。

运行配置主要在看板维护，不在安装表单中重复提供 API Key 或面板密码，以免重启覆盖看板中的设置。出口代理等高级配置见上游配置参考；容器中的 `127.0.0.1` 指容器自身。

## 客户端接入

将 `<网关地址>` 替换为实际访问地址，API Key 使用看板生成的密钥。

| 客户端 | Base URL | 协议 |
| --- | --- | --- |
| OpenAI 兼容客户端 | `https://<网关地址>/v1` | Chat Completions |
| Codex CLI | `https://<网关地址>/v1` | Responses API |
| Claude Code | `https://<网关地址>` | Anthropic Messages |

模型名使用 `/v1/models` 返回的 `id`。Claude Code 的 Base URL 不带 `/v1`。

## 持久化与维护

以下目录均位于应用的实际安装目录下，并绑定挂载到容器：

| 宿主机目录 | 容器路径 | 内容 |
| --- | --- | --- |
| `./accounts` | `/app/accounts` | 账号凭证、设置、API Key、面板密码摘要及机器身份缓存 |
| `./usage` | `/app/usage` | 用量流水 |

备份时停止应用并同时备份这两个目录；它们包含敏感凭证，应限制读取权限。重建、升级及迁移时保留数据目录，尤其不要删除机器身份缓存。卸载前另行备份，避免随安装目录清理丢失数据。

健康检查使用无需鉴权、无需账号的 `/ping`，只表示 HTTP 进程可响应，不代表上游推理可用。启动后仍需添加账号并实际调用模型验证。

通过 1Panel 更新容器镜像，不依赖容器内更新源码。应用包关闭跨版本升级，后续新增版本前应核对上游兼容性并备份数据。

## 参数来源与验证范围

调研日期：2026-10-30。部署参数依据上游 `v1.8.0`：

- [发布记录与镜像标签](https://github.com/shuishuipingan/qoder2api-hub/releases/tag/v1.8.0)
- [Compose：端口、数据卷、探针](https://github.com/shuishuipingan/qoder2api-hub/blob/v1.8.0/docker-compose.yml)
- [Dockerfile：运行环境、默认命令与用户](https://github.com/shuishuipingan/qoder2api-hub/blob/v1.8.0/Dockerfile)（未声明 `USER`，沿用基础镜像默认 root 用户）
- [镜像发布：amd64 / arm64 与 semver 标签](https://github.com/shuishuipingan/qoder2api-hub/blob/v1.8.0/.github/workflows/docker-publish.yml)
- [配置参考：密码与鉴权](https://github.com/shuishuipingan/qoder2api-hub/blob/v1.8.0/docs/configuration.md)
- [部署文档](https://github.com/shuishuipingan/qoder2api-hub/blob/v1.8.0/docs/deployment.md)与 [MIT 许可](https://github.com/shuishuipingan/qoder2api-hub/blob/v1.8.0/LICENSE)

`logo.png` 为本应用条目自制的 Q2A HUB 文字图标，不是上游官方标志，也未借用其他应用图标。

本次完成 YAML、表单引用、PNG 和 Compose 配置静态检查；未进行 1Panel 实机安装、镜像启动或真实账号推理验证。环境缺少 Ruby，仓库的 Ruby 校验脚本未能执行，以 Python 检查同类静态规则；Docker daemon 不可访问，未拉取或运行镜像。
