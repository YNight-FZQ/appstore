---
name: 1panel-app
description: 在当前 appstore 仓库中快速创建或维护个人 1Panel v2 应用包，配置安装表单、Compose、版本与本地校验。处理本仓库 apps/ 或明确要求 1Panel 应用包时使用。
---

# 创建和维护 1Panel 应用

本技能面向当前仓库的 `apps/<应用标识>/`。先阅读 [格式与快捷配置](references/format-and-fields.md)，再参考仓库内的自维护应用：单服务、多端口和初始化脚本看 `apps/3xui`；持久化目录及环境变量看 `apps/lx-music-sync-server`；数据库、Redis、私有配置与多服务编排看 `apps/ynight-hub`。需要数据库类型联动、布尔选项或升级参数迁移时，再读[精选配置范例](references/selected-patterns.md)。现有应用也有兼容问题，必须按目标 1Panel 版本核对字段，不整包复制。

## 工作方法

1. 确定应用标识、版本、官方仓库或文档、官方容器镜像、内部端口、持久化路径、必填环境变量、运行用户及镜像架构。来源不明确的部署参数先查证，不凭名称猜测。
2. 创建单容器 HTTP 应用时，运行 `ruby .agents/skills/1panel-app/scripts/new_app.rb --help`，按已核实的数据生成最小应用包；复杂拓扑可直接按同一目录格式编写。必须使用应用自身的合法 PNG 图标，不借用其他应用图标。
3. 只把安装或后续维护需要修改的值放入版本 `data.yml`。让每个 `envKey` 与 Compose 中的引用或 `env_file` 对上；不能把表单字段当作自动注入的容器环境变量。布尔开关使用字符串值的 `select`，不要使用 `type: boolean`。
4. 新增版本时保留旧版本目录；核实镜像、迁移和兼容性后再决定 `crossVersionUpdate`。`init.sh` 只处理有证据的首次初始化工作，并保证重复执行安全。真实密钥、安装生成的 `.env` 和运行数据不进入仓库。
5. 运行 `ruby .agents/skills/1panel-app/scripts/check_app.rb apps/<应用标识>`。有 Compose 的环境再用示例参数运行 `docker compose config --quiet`；有脚本则运行 `bash -n`。需要实际安装验证时，把应用包放到目标面板安装目录下的 `1panel/resource/apps/local/<应用标识>`，同步本地应用，再测试安装、重建、升级与卸载。只有用户要求操作服务器时才进行远程安装。

交付时说明应用目录、版本、参数来源、已完成的静态检查，以及尚未执行的 1Panel 实机检查。当前字段结论来自 1Panel `dev-v2` 的固定提交 `d2bb3813`；针对其他面板版本时重新核对源码。
