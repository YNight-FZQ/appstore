# 从已移除模板保留的配置范例

这些片段整理自本仓库建仓时保留的官方应用模板，用于补足当前三个自维护应用未覆盖的字段和升级写法。它们不是可安装应用包；镜像、密码和端口必须按目标应用重新核实。完整原文件仍可从 Git 历史的 `6be29ee59` 提交查看。

## 先选数据库类型，再选服务实例

依据原 `apps/wordpress/7.1.1/data.yml`。`apps` 字段给出 MySQL 与 MariaDB 选项，`child` 随所选类型展示已安装的服务实例；实例地址写入 `PANEL_DB_HOST`。

```yaml
additionalProperties:
  formFields:
    - envKey: PANEL_DB_TYPE
      type: apps
      labelZh: 数据库类型与实例
      default: mysql
      required: true
      values:
        - label: MySQL
          value: mysql
        - label: MariaDB
          value: mariadb
      child:
        envKey: PANEL_DB_HOST
        type: service
        default: ''
        required: true
```

数据库安装参数仍需补全 `PANEL_DB_NAME`、`PANEL_DB_USER`、`PANEL_DB_USER_PASSWORD`，并在 Compose 的 `environment` 中映射到镜像实际使用的变量。WordPress 原包还把 `PANEL_DB_HOST` 与 1Panel 自动补入的 `PANEL_DB_PORT` 拼成 `WORDPRESS_DB_HOST`。

## 用下拉选项表达布尔开关

依据原 `apps/palworld/2.7.3/data.yml` 中的 `select` 字段。对当前核对的 1Panel 版本，安装表单不支持 `type: boolean`；选项值必须是字符串。

```yaml
- envKey: FEATURE_ENABLED
  type: select
  labelZh: 启用功能
  default: 'true'
  required: true
  values:
    - label: 启用
      value: 'true'
    - label: 关闭
      value: 'false'
```

将 `FEATURE_ENABLED` 改为镜像要求的变量名，并通过 Compose 的 `environment` 显式传入容器。

## 升级时幂等补入新参数

依据原 `apps/alist/3.64.0/scripts/upgrade.sh`。只在旧安装目录的 `.env` 存在且缺少新变量时追加，避免重复升级产生重复项。

```bash
#!/bin/bash
set -euo pipefail

if [[ -f .env ]] && ! grep -q '^NEW_OPTION=' .env; then
  printf '%s\n' 'NEW_OPTION=example' >> .env
fi
```

实际迁移脚本应按目标应用的数据格式和默认值修改，并验证升级前后的配置与运行结果。
