# 个人 1Panel 应用商店

本仓库按 1Panel v2 的应用包格式维护自用应用。`apps/` 目前包含以下五个应用：

| 应用目录 | 用途 |
| --- | --- |
| [`apps/3xui`](apps/3xui) | Xray 管理面板 |
| [`apps/lx-music-sync-server`](apps/lx-music-sync-server) | LX Music 数据同步服务 |
| [`apps/subconverter`](apps/subconverter) | 代理订阅格式转换工具 |
| [`apps/tavily-proxy`](apps/tavily-proxy) | Tavily API 密钥池与代理管理面板 |
| [`apps/ynight-hub`](apps/ynight-hub) | YNight Hub 后端服务 |

## 创建和维护应用

项目内的 [1Panel 应用 Skill](.agents/skills/1panel-app/SKILL.md) 提供应用包格式、安装表单配置、创建脚本、静态校验脚本及精选范例。新应用放入 `apps/<应用标识>/`，并按 Skill 中的步骤检查。

本仓库是个人应用商店，不是 1Panel 官方应用商店。1Panel 项目及官方应用商店分别见 [1Panel](https://github.com/1Panel-dev/1Panel) 和 [1Panel 官方应用商店](https://github.com/1Panel-dev/appstore)。
