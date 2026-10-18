# LibreTV

LibreTV 是轻量的影视聚合搜索与直播播放工具，支持多源搜索、换源、浏览器续播、M3U 直播列表和 XMLTV 节目单。本应用包面向 1Panel v2，使用上游发布的容器镜像，并在安装表单中预置点播与直播源。

| 项目 | 配置 |
| --- | --- |
| 应用版本 | `2.16.12` |
| 容器镜像 | `bestzwei/libretv:2.16.12` |
| 镜像架构 | `linux/amd64`、`linux/arm64` |
| 容器端口 | `8080` |
| 默认宿主机映射 | `127.0.0.1:18080:8080` |
| 服务端持久化目录 | 无；设置和观看数据保存在浏览器 |

## 安装与访问

1. 将本应用目录完整复制到 `<面板安装根目录>/1panel/resource/apps/local/libretv`，保留 `2.16.12` 版本子目录。面板安装根目录以实际安装位置为准。
2. 在 1Panel 的应用商店中同步本地应用，选择 LibreTV，设置访问密码后安装。
3. 宿主机可通过 `http://127.0.0.1:18080` 访问；需要修改端口时，在安装表单中调整“本机 HTTP 端口”。
4. 对外访问时，在“网站 → 创建网站 → 一键部署 → 已装应用”中关联该实例，绑定域名并启用 HTTPS。

Compose（容器编排配置）默认将端口绑定到宿主机回环地址。1Panel 高级配置可能调整绑定地址，实际映射以安装后的配置为准。同一 `1panel-network` 网络中的容器可通过该实例的容器名称和 `8080` 端口访问服务。

新安装保留表单默认值即可获得非凡、暴风两个点播接口，以及 IPTV-org 中文频道直播列表。安装后可在站内“设置 → 源管理”中选择和测试来源，也可继续添加自己的点播源、直播源或数据源订阅。来源与抽检结果见[内置源调研说明](SOURCES.md)。

已有安装的参数不会随应用目录更新而自动替换：请在 1Panel 的应用参数中将 `DEFAULT_SOURCES`、`DEFAULT_LIVE_SOURCES` 改为本版本表单中的默认值，保存并重建容器，再刷新 LibreTV。已有浏览器中的来源勾选保持用户设置；如果尚未勾选，请在站内源管理中选择。

## 安装参数

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `PANEL_APP_PORT_HTTP` | `18080` | 宿主机访问端口 |
| `PASSWORD` | 空，必填 | 共享访问密码，安装时自行设置 |
| `PROXY_SECRET` | 空 | 独立会话签名密钥；留空时由访问密码派生 |
| `COOKIE_SECURE` | 空 | 按访问协议判断；`true` 强制 HTTPS，`false` 允许 HTTP |
| `DEFAULT_SOURCES` | 非凡、暴风 | 预置点播源的 JSON（数据交换格式）数组，填 `[]` 可关闭预置 |
| `DEFAULT_LIVE_SOURCES` | IPTV-org 中文频道 | 预置直播源数组，填 `[]` 可关闭预置 |
| `DEFAULT_SUBSCRIPTIONS` | `[]` | 预置源订阅的 JSON 数组 |
| `DEFAULT_RECOMMEND_SOURCE` | `hot-list` | 默认首页推荐，可选 `hot-list`、`douban`、`bangumi` |
| `LIVE_ALLOW_PRIVATE` | `0` | `1` 允许内网直播源，`0` 保持关闭 |

所有表单参数均可在安装后的参数页面修改，保存后需要让容器使用更新后的配置。1Panel 会将参数写入安装目录的 `.env`，其中含有密码和密钥，请勿提交到版本库。

HTTPS 反向代理应传递 `x-forwarded-proto: https`。如果代理没有正确传递协议，可将“会话 Cookie 安全策略”设为“强制 HTTPS”。Cookie 是浏览器保存的会话凭据；强制 HTTPS 后，用 HTTP 地址访问时无法维持登录。

## 数据源格式

安装表单中填写完整、单行的 JSON 数组。以下是本包使用的默认配置，可复制到已有安装的参数中。

预置点播源 `DEFAULT_SOURCES`：

```json
[{"name":"非凡资源","url":"https://api.ffzyapi.com/api.php/provide/vod","isAdult":false},{"name":"暴风资源","url":"https://bfzyapi.com/api.php/provide/vod","isAdult":false}]
```

预置直播源 `DEFAULT_LIVE_SOURCES`。若有与频道标识匹配的节目单，可另加可选的 `epg` 字段：

```json
[{"name":"IPTV-org 中文频道","url":"https://iptv-org.github.io/iptv/languages/zho.m3u"}]
```

预置源订阅 `DEFAULT_SUBSCRIPTIONS` 默认保留 `[]`。需要自行添加时，可按以下格式填写，`example.com` 为格式示例：

```json
["https://example.com/sources.json"]
```

预置源和订阅地址会通过上游 `/api/status` 接口在登录前返回，地址中的令牌不会脱敏。请只预置允许公开的地址；私密来源可在自己的浏览器中通过站内设置添加。TVBOX 配置只会导入上游支持的接口，Spider 爬虫类站点会跳过。

直播列表由 IPTV-org 维护，应用按需拉取当前列表，本包不固定复制频道流地址。本次 LibreTV 解析出 215 个中文频道条目，数量会随上游维护变化；抽检发现了失效频道，请在直播页测活后选择可用频道。个别频道还受网络、地区或编码限制。默认没有配置节目单，避免将不匹配的节目单标识强行绑定到频道上。

## 数据、升级与排查

- 设置保存在浏览器本地存储，历史与进度保存在本机 IndexedDB（浏览器数据库）；服务端没有用户数据库或需要挂载的数据卷。换设备、换浏览器或更换站点域名时，请先通过“设置 → 数据 → 配置导入导出”备份和迁移。1Panel 的容器备份不包含这些浏览器数据。
- 本包固定镜像版本，跨版本升级默认关闭。升级前核对上游变更，备份安装参数并导出浏览器配置；新增应用包版本时保留旧版本目录。
- 使用独立 `PROXY_SECRET` 时，仅修改访问密码不会使已有签名会话失效；需要使旧会话失效时应同时更换该密钥。
- 健康检查每 30 秒检查一次容器内 `/api/status`，确认服务响应正常且已设置访问密码。它不验证第三方片源是否可播放。
- 播放优先直连片源，失败后会通过服务器代理；代理播放会消耗服务器出口带宽。直播黑屏还可能与浏览器解码能力有关。
- 若 Docker Hub 拉取失败，可在安装时编辑编排配置，将镜像改为上游同版本的 `ghcr.io/librespark/libretv:2.16.12`。

截至 2026 年 10 月 16 日，对上游当前锁文件的生产依赖审计返回 4 个受影响依赖项，其中 3 项高等级、1 项中等级；具体可利用性尚未逐项验证。这是源码依赖匹配结果，本包未对已发布镜像执行漏洞扫描；请持续关注上游安全更新。

## 上游资料

- [项目仓库](https://github.com/LibreSpark/LibreTV)
- [官方部署说明与镜像来源](https://github.com/LibreSpark/LibreTV#部署)
- [部署文档](https://libretv.is-an.org/wiki/Deployment.html)
- [配置文档](https://libretv.is-an.org/wiki/Configuration.html)
- [数据源文档](https://libretv.is-an.org/wiki/Data-Sources.html)
- [上游许可证](https://github.com/LibreSpark/LibreTV/blob/main/LICENSE)

图标直接取自上游 `public/icons/icon-512.png`，应用代码和图标的授权以上游许可证为准。使用影视源时，请自行确认内容使用权限。
