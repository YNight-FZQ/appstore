# Subconverter

Subconverter 是代理订阅格式转换工具。本应用使用 `tindy2013/subconverter:latest`，默认把容器内的 25500 端口映射到宿主机 `127.0.0.1:15051`。1Panel 安装表单可以调整宿主机端口，绑定地址仍为回环地址。

## 安装与配置

在 1Panel 中同步本地应用后安装。首次安装会从版本目录下的同名 `.example` 模板，在应用安装目录生成以下四个文件；已有文件不会被初始化脚本覆盖。修改仓库内模板会影响后续新安装，已安装实例应修改安装目录中的实际文件：

安装表单中的“默认订阅 URL”可以留空。填写后，首次安装会把它写入 `conf/pref.toml` 的 `default_url`；输入框会遮盖内容，但订阅链接仍会保存在该实例的 `.env` 和主配置中。链接中的引号、反斜杠请先进行 URL 编码。安装后若需更改，请直接编辑安装目录中的 `conf/pref.toml` 并重启应用；安装表单的该字段不会自动更新已有配置。

| 文件 | 容器内位置 | 用途 |
| --- | --- | --- |
| `conf/pref.toml` | `/base/pref.toml` | 主配置，首次安装时生成管理接口令牌 |
| `conf/auto_speed_test.ini` | `/base/config/auto_speed_test.ini` | 用户提供的自动测速外部配置 |
| `groups.toml` | `/base/snippets/groups.toml` | 主配置导入的策略组 |
| `rulesets.toml` | `/base/snippets/rulesets.toml` | 主配置导入的规则 |

安装后的 `groups.toml` 和 `rulesets.toml` 提供与你给出的 INI 配置等价的简版内容，你可以直接替换为自己的完整文件。修改配置后，在 1Panel 中重启应用。检查服务可访问性：`curl http://127.0.0.1:15051/version`。

默认转换使用 `pref.toml` 导入的 `groups.toml` 和 `rulesets.toml`。`auto_speed_test.ini` 作为可选外部配置，可在转换请求中添加 `config=config%2Fauto_speed_test.ini`；若希望所有未指定 `config` 的请求默认使用它，可在 `pref.toml` 的 `[common]` 段设置 `default_external_config = "config/auto_speed_test.ini"`。外部配置中的策略组和规则会覆盖主配置导入的片段，因此修改 `groups.toml`、`rulesets.toml` 时请留意所用配置来源。

当前示例的 `overwrite_original_rules = true` 会覆盖原订阅规则；若要保留原规则，请同时检查主配置和所使用的外部配置。服务仅对宿主机回环地址开放，但同一 `1panel-network` 上的容器仍可访问容器端口。主配置中的 `api_access_token` 在首次安装时随机生成，用于保护管理接口。

官方资料：[容器说明](https://github.com/tindy2013/subconverter/blob/master/README-docker.md)、[配置示例](https://github.com/tindy2013/subconverter/blob/master/base/pref.example.toml)、[中文文档](https://github.com/tindy2013/subconverter/blob/master/README-cn.md)。
