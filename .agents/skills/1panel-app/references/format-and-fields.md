# 应用包格式与快捷配置

依据：1Panel `dev-v2` [固定提交 d2bb3813](https://github.com/1Panel-dev/1Panel/tree/d2bb3813d96b97cc4eafb36d0efc0bf6f35673e7)。当前仓库采用官方应用商店的 `apps/` 目录格式，`data.yaml` 列出了可复用的分类键。

## 最小目录

```text
apps/<应用标识>/
  data.yml                 应用名称、分类、简介、架构等
  logo.png                 本地应用同步时必需
  README.md                使用说明
  <版本>/
    data.yml               安装表单
    docker-compose.yml     部署内容
    scripts/init.sh        仅在确有初始化步骤时添加
```

本地同步逐个读取应用目录及其版本子目录，根目录缺少 `data.yml` 或 `logo.png`、版本缺少 `data.yml` 或 `docker-compose.yml` 时会跳过。安装时，1Panel 将版本目录复制到安装目录，写入 `.env`，再执行 `init.sh` 并启动容器。详见[同步逻辑](https://github.com/1Panel-dev/1Panel/blob/d2bb3813d96b97cc4eafb36d0efc0bf6f35673e7/agent/app/service/app.go#L611-L669)、[解析逻辑](https://github.com/1Panel-dev/1Panel/blob/d2bb3813d96b97cc4eafb36d0efc0bf6f35673e7/agent/app/service/app_utils.go#L1271-L1393)和[安装逻辑](https://github.com/1Panel-dev/1Panel/blob/d2bb3813d96b97cc4eafb36d0efc0bf6f35673e7/agent/app/service/app.go#L560-L583)。安装根目录取决于面板的安装路径，不能一律假定为 `/opt/1panel`。

根 `data.yml` 还控制应用级快捷设置：`tags` 决定分类，`architectures` 声明镜像支持的架构，`limit` 限制安装实例数（`0` 为不限），`crossVersionUpdate` 决定是否放行跨版本升级，`memoryRequired` 展示内存要求，`gpuSupport` 显示 GPU 配置入口。`website`、`github`、`document` 提供资料链接。这些值应按应用实际能力填写；打开跨版本升级不等于完成数据迁移。本地应用解析代码会读取上述字段，但**不会读取** `batchInstallSupport`，所以个人本地应用不要依赖该字段开启批量安装。依据见[应用字段结构](https://github.com/1Panel-dev/1Panel/blob/d2bb3813d96b97cc4eafb36d0efc0bf6f35673e7/agent/app/dto/app.go#L87-L108)、[本地解析](https://github.com/1Panel-dev/1Panel/blob/d2bb3813d96b97cc4eafb36d0efc0bf6f35673e7/agent/app/service/app_utils.go#L1335-L1383)与[安装数量检查](https://github.com/1Panel-dev/1Panel/blob/d2bb3813d96b97cc4eafb36d0efc0bf6f35673e7/agent/app/service/app_utils.go#L851-L863)。

## 安装表单能提供什么

版本 `data.yml` 的 `additionalProperties.formFields` 是安装界面的快捷配置入口。字段定义见[后端结构](https://github.com/1Panel-dev/1Panel/blob/d2bb3813d96b97cc4eafb36d0efc0bf6f35673e7/agent/app/dto/app.go#L140-L165)，实际控件见[前端模板](https://github.com/1Panel-dev/1Panel/blob/d2bb3813d96b97cc4eafb36d0efc0bf6f35673e7/frontend/src/views/app-store/detail/params/index.vue#L1-L125)。

| `type` | 快捷配置 | 关键字段 |
| --- | --- | --- |
| `text` | 文本、域名、路径、用户名 | `default`、`envKey`，可配 `rule` |
| `number` | 端口及数值 | 端口使用 `rule: paramPort` |
| `password` | 密码输入框 | 不要在 Git 中写真实默认密码 |
| `select` | 固定选项 | `values`；可用 `multiple`、`allowCreate` |
| `service` | 选择已安装的服务实例 | `key` 指定服务类型，如 `redis`、`mysql` |
| `apps` | 先选择应用类型，再选实例 | `values` 加 `child: {type: service, envKey: ...}` |

常用修饰字段：`labelZh`、`labelEn` 或 `label` 提供显示名称；`description` 提供帮助文字；`required` 设置必填；`rule` 指向前端规则；`edit: true` 允许安装后在参数页面修改；`disabled` 禁用安装输入。`random: true` 在默认值后加六位字符，名字可用；其实现使用 `Math.random()`，不能把它当作高强度密钥生成器，见[前端初始化](https://github.com/1Panel-dev/1Panel/blob/d2bb3813d96b97cc4eafb36d0efc0bf6f35673e7/frontend/src/views/app-store/detail/params/index.vue#L211-L260)与[随机函数](https://github.com/1Panel-dev/1Panel/blob/d2bb3813d96b97cc4eafb36d0efc0bf6f35673e7/frontend/src/utils/id.ts#L1-L11)。

自维护应用 `apps/3xui` 和 `apps/lx-music-sync-server` 中有 `type: boolean`，但该提交的安装表单没有对应控件，[后端 `.env` 转换](https://github.com/1Panel-dev/1Panel/blob/d2bb3813d96b97cc4eafb36d0efc0bf6f35673e7/agent/app/service/app_utils.go#L871-L891)也没有布尔分支。这是存量应用的兼容问题，不能当作可用范例；新应用要用 `select`，选项值写为字符串 `"true"`、`"false"`。

## 1Panel 识别的常见参数

| 参数 | 行为 |
| --- | --- |
| `PANEL_APP_PORT_HTTP`、`PANEL_APP_PORT_HTTPS` | 检查端口占用，并记录为应用的主端口；其他 `PANEL_APP_PORT_*` 也接受占用检查。 |
| `PANEL_DB_HOST` | 从面板中的数据库实例选择后，安装时换成数据库地址，并补入 `PANEL_DB_PORT`。 |
| `PANEL_DB_NAME`、`PANEL_DB_USER`、`PANEL_DB_USER_PASSWORD` | 与数据库实例一起使用时，可由 1Panel 创建并关联数据库；具体受应用类型和数据库类型约束。 |
| `PANEL_REDIS_ROOT_PASSWORD` | 选择面板管理的 Redis 服务后，表单可从实例配置自动填入此字段。 |
| `CONTAINER_NAME` | 1Panel 安装时生成，无须出现在表单。 |
| `CPUS`、`MEMORY_LIMIT`、`HOST_IP` | 1Panel 的高级容器配置处理，不作为普通表单字段重复声明。 |

证据：[安装参数处理](https://github.com/1Panel-dev/1Panel/blob/d2bb3813d96b97cc4eafb36d0efc0bf6f35673e7/agent/app/service/app.go#L388-L425)、[数据库关联](https://github.com/1Panel-dev/1Panel/blob/d2bb3813d96b97cc4eafb36d0efc0bf6f35673e7/agent/app/service/app_utils.go#L212-L335)、[服务列表及配置](https://github.com/1Panel-dev/1Panel/blob/d2bb3813d96b97cc4eafb36d0efc0bf6f35673e7/agent/app/service/app_install.go#L594-L660)、[高级配置](https://github.com/1Panel-dev/1Panel/blob/d2bb3813d96b97cc4eafb36d0efc0bf6f35673e7/agent/app/service/app_utils.go#L1695-L1791)。

表单值写入安装目录的 `.env`。Compose 会读取该文件进行变量插值，但容器要获取环境变量仍需在 `environment` 中引用或使用 `env_file`。安装表单外的高级设置包括端口开放与绑定地址、CPU、内存、GPU、重启策略和编辑 Compose；默认端口绑定地址由高级设置决定，不由包中端口写法单独保证。详见[数据复制](https://github.com/1Panel-dev/1Panel/blob/d2bb3813d96b97cc4eafb36d0efc0bf6f35673e7/agent/app/service/app_utils.go#L950-L1008)及[高级配置](https://github.com/1Panel-dev/1Panel/blob/d2bb3813d96b97cc4eafb36d0efc0bf6f35673e7/agent/app/service/app_utils.go#L1756-L1789)。

## 当前仓库中的应用

`apps/` 目前包含以下 4 个自维护应用：

- `apps/3xui`：单服务、两个端口及 `init.sh`；安装表单的两个 `boolean` 字段与所核对的 1Panel 版本不兼容，不要照搬。
- `apps/lx-music-sync-server`：单服务、多个持久化目录和环境变量；两个 `boolean` 字段同样不兼容，固定的示例密码也不适合作为新应用默认值。
- `apps/subconverter`：单服务、仅绑定宿主机回环地址、由 `init.sh` 生成配置文件和管理令牌；外部 INI 配置与 TOML 片段的覆盖关系需在说明中写清楚。
- `apps/ynight-hub`：MySQL 与 Redis 关联、私有配置文件、多服务编排和 `init.sh`；自动更新安排属于该应用自身需求，不应默认复制到新应用。

已删除的模板中，WordPress 的数据库类型联动、Palworld 的布尔选项、AList 的升级参数迁移有补充价值，其可复用片段保存在[精选配置范例](selected-patterns.md)，不再作为可安装应用留在 `apps/`。

新应用的分类键取自仓库 `data.yaml`，而根 `data.yml` 的中文分类名称与键对应。私有应用至少写清中文名称和说明；需要提交官方商店时，再按官方仓库的多语言与审核要求补齐内容。

生命周期脚本执行机制见[脚本调度](https://github.com/1Panel-dev/1Panel/blob/d2bb3813d96b97cc4eafb36d0efc0bf6f35673e7/agent/app/service/app_utils.go#L1011-L1047)。普通应用的安装执行 `init.sh`，升级可执行 `upgrade.sh`，卸载可执行 `uninstall.sh`；仅加入 `start.sh`、`stop.sh` 或 `restart.sh` 并不会让普通应用操作改走这些脚本。参数更新不会再次执行 `init.sh`。
