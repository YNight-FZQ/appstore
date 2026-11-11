# Subconverter

Subconverter 是代理订阅格式转换工具。本应用使用 `tindy2013/subconverter:latest`，默认把容器内的 25500 端口映射到宿主机 `127.0.0.1:15051`。1Panel 安装表单可以调整宿主机端口，绑定地址仍为回环地址。

`1.0.0` 是本地配置包编号，独立于上游程序版本。

## 上游版本

上游代码版本为 `v0.9.0`（2024-04-08 发布），此后没有新的 tag；`latest` 镜像在 2026-07 因构建脚本调整被重新推送，版本号未变，因此容器内 `/version` 仍返回 `v0.9.0`。本应用跟随 `latest`，镜像更新可通过 `docker compose pull` 获取。

## 安装与配置

在 1Panel 中同步本地应用后安装。首次安装会从版本目录下的同名 `.example` 模板，在应用安装目录生成以下四个文件；已有文件不会被初始化脚本覆盖。修改仓库内模板会影响后续新安装，已安装实例应修改安装目录中的实际文件：

安装表单中的“默认订阅 URL”可以留空。填写后，首次安装会把它写入 `conf/pref.toml` 的 `default_url`；输入框会遮盖内容，但订阅链接仍会保存在该实例的 `.env` 和主配置中。初始化脚本同时接受 1Panel 生成的三种取值形式（无引号、单引号、双引号），因此请直接填写原始链接，不要额外加引号；链接内本身含有引号或反斜杠时请先进行 URL 编码。非 HTTP/HTTPS 链接会被拒绝并使安装失败。安装后若需更改，请直接编辑安装目录中的 `conf/pref.toml` 并重启应用；安装表单的该字段不会自动更新已有配置。

| 文件 | 容器内位置 | 用途 |
| --- | --- | --- |
| `conf/pref.toml` | `/base/pref.toml` | 主配置，首次安装时生成管理接口令牌 |
| `conf/auto_speed_test.ini` | `/base/config/auto_speed_test.ini` | 用户提供的自动测速外部配置 |
| `groups.toml` | `/base/snippets/groups.toml` | 主配置导入的策略组 |
| `rulesets.toml` | `/base/snippets/rulesets.toml` | 主配置导入的规则 |

安装后的 `groups.toml` 和 `rulesets.toml` 提供与上游 `base/snippets` 等价的简版内容，你可以直接替换为自己的完整文件。修改配置后，在 1Panel 中重启应用。检查服务可访问性：`curl http://127.0.0.1:15051/version`。

## 鉴权与令牌

首次安装生成的 `conf/pref.toml` 默认开启 API 模式（`api_mode = true`），`api_access_token` 是 10 个随机的 URL 安全字符。API 模式下，使用 `default_url` 发起不带 `url` 的转换请求，或通过请求读取本地订阅和文件时，需要附加 `token=<api_access_token>`；令牌可在安装目录的 `conf/pref.toml` 中查看。请勿将带令牌的链接公开。已安装实例的配置文件不会被新的模板覆盖；若需采用此设置，请在实例的 `conf/pref.toml` 中自行设置 `api_mode = true` 并决定是否更换现有令牌，然后重启应用。

本包未逐一核对上游对 `/refreshrules` 等控制接口是否校验令牌：这类接口的鉴权范围请以实际运行的镜像为准，升级镜像后重新确认。由于服务只绑定宿主机回环地址，未做反代时上述接口仅本机可达；若通过反向代理对外暴露，请自行限制这些路径的访问。

## 配置说明

默认转换使用 `pref.toml` 导入的 `groups.toml` 和 `rulesets.toml`。`auto_speed_test.ini` 作为可选外部配置，可在转换请求中添加 `config=config%2Fauto_speed_test.ini`；若希望所有未指定 `config` 的请求默认使用它，可在 `pref.toml` 的 `[common]` 段设置 `default_external_config = "config/auto_speed_test.ini"`。外部配置中的策略组和规则会覆盖主配置导入的片段，因此修改 `groups.toml`、`rulesets.toml` 时请留意所用配置来源。

以下几处是本配置包相对上游默认值的调整，安装后可自行改回：

- `enable_insert = false`、`insert_url = []`：上游默认开启插入并留空链接，空字符串会触发一次无效下载；需要往所有订阅里插入节点时再开启并填写。
- `write_managed_config = false`、`managed_config_prefix` 注释掉：该前缀只能填容器外可访问的地址，填 `127.0.0.1` 会让客户端反复拉取失败；启用前请先配置反代并填入实际域名。
- `max_allowed_rules = 65536`、`max_allowed_download_size = 33554432`：上游默认 `0` 表示不限制，为单次转换的规则数和外部文件大小设上限，避免超大规则集耗尽内存。
- `auto_speed_test.ini` 的分组名已与 `groups.toml` 统一为 `🔰 选择节点`，避免两种配置来源产生同名分叉；其 `overwrite_original_rules` 仍为 `true`，因为这份外部配置的定位是用极简规则整体替换模板规则。

`pref.toml` 的 `[ruleset] overwrite_original_rules` 为 `false`，即保留模板原有规则并追加导入的规则集；若想只保留 `rulesets.toml` 中的规则，改为 `true`。

服务仅对宿主机回环地址开放，但同一 `1panel-network` 上的容器仍可访问容器端口。

## 已知限制

- 上游镜像基于 `alpine:3.16`，运行阶段只装了 `pcre2`、`libcurl`、`yaml-cpp`，没有 `tzdata`；构建时 `/etc/localtime` 指向 `/usr/share/zoneinfo` 的软链，因此本包未设置 `TZ` 环境变量，容器内时间为 UTC。若需要本地时区，请自行确认镜像内是否存在对应 zoneinfo 文件后再设置。
- 健康检查依赖镜像内的 busybox `wget`，只表示 HTTP 进程可响应，不代表订阅转换或上游节点可用。
- `pref.toml` 里的 `proxy_config`、`proxy_ruleset` 默认为 `SYSTEM`，容器内没有系统代理时会回退直连；需要走代理下载规则集时请显式填写代理地址。

## 验证范围

本次仅对照上游 `v0.9.0` 源码、`base/pref.example.toml`、`scripts/Dockerfile` 与 Docker Hub 标签页核对了配置项含义和镜像架构（`amd64`、`arm64`、`arm/v7`、`386`）；当前执行环境不可用，未运行 Compose、容器或 1Panel 实机检查。

官方资料：[容器说明](https://github.com/tindy2013/subconverter/blob/master/README-docker.md)、[配置示例](https://github.com/tindy2013/subconverter/blob/master/base/pref.example.toml)、[中文文档](https://github.com/tindy2013/subconverter/blob/master/README-cn.md)。
