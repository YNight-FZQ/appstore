# LibreTV 内置源调研

核验日期：2026 年 10 月 18 日。目标应用为本包的 LibreTV `2.16.12`。默认内置 **非凡、暴风两个点播接口，以及 IPTV-org 中文直播列表**，具体值保存在 `2.16.12/data.yml` 的安装表单中，通过现有 Compose（容器编排配置）环境变量传入应用。

## 筛选结果

| 来源 | 类型与兼容性 | 本次核验结果 | 默认配置 |
| --- | --- | --- | --- |
| [非凡资源](https://ffzy.tv/help/) | 苹果 CMS 的 JSON 接口，详情包含 M3U8 播放线路 | LibreTV 搜索与详情正常，抽样播放清单与视频分片可读取 | 内置 |
| [暴风资源](https://libretv.is-an.org/wiki/Data-Sources.html) | LibreTV 文档列出的苹果 CMS 接口 | LibreTV 搜索与详情正常，抽样播放清单与视频分片可读取 | 内置 |
| [IPTV-org 中文频道](https://github.com/iptv-org/iptv) | 标准 M3U 列表，按语言汇集中文频道 | 原始列表 216 条，LibreTV 解析出 215 条；3 个频道抽样中 1 个通过分片级探测 | 内置，使用时测活选台 |
| [360 资源](https://www.360zy.com/360zy/help.html) | 新公布的综合接口与专用 M3U8 接口均可返回详情 | 样本播放地址两轮均返回错误页或 HTTP 502，未通过播放清单检查 | 暂不内置 |
| [IPTV-org 中国频道](https://github.com/iptv-org/iptv) | 标准 M3U，按国家分类，和中文列表有较多重叠 | 直接下载可得 147 条；通过本地 LibreTV 拉取时两轮均达到 15 秒超时 | 暂不内置 |
| [YueChan 国内列表](https://github.com/YueChan/Live) | M3U 外层可解析，96 个频道地址均为 RTP 协议 | LibreTV 的直播解析器只保留 HTTP/HTTPS，无法直接使用这份 RTP 列表 | 不内置 |
| [YueChan 国际列表](https://github.com/YueChan/Live) | 待核实 | 本次请求超时，未完成列表与频道验证 | 暂不内置 |
| [YanG 汇集列表](https://github.com/YanG-1989/m3u) | 待核实 | 本次请求超时，未完成列表与频道验证 | 暂不内置 |

以上结论来自本机网络的一次调研和有限抽检。某个样本失败不代表整站永久不可用，样本成功也不代表该源所有节目、全部地区及所有浏览器都能播放。

## 内置点播源

### 非凡资源

- 接口：`https://api.ffzyapi.com/api.php/provide/vod`。
- 以“西游记”搜索，LibreTV 返回 19 项；抽样详情解析出 52 集。
- 使用 LibreTV 内置代理读取抽样剧集：HLS（分段视频播放协议）清单返回 HTTP 200，首个分片返回 HTTP 206，读取到 2048 字节的 `video/mp2t` 数据。
- 非凡详情包含网页播放线路与 M3U8 线路，LibreTV 的解析器会优先选择 M3U8 线路，无需在本包中添加第三方解析脚本。
- 资料依据：[非凡帮助中心](https://ffzy.tv/help/)、[LibreTV 点播解析实现](https://github.com/LibreSpark/LibreTV/blob/a24ad336a3f7c8a16ca93d1f1198e08ac6b7e943/src/lib/cms-parser.ts)。

### 暴风资源

- 接口：`https://bfzyapi.com/api.php/provide/vod`。
- 以“西游记”搜索，LibreTV 第一页返回 20 项；抽样详情解析出 61 集。
- 使用 LibreTV 内置代理读取抽样剧集：HLS 清单返回 HTTP 200，首个分片返回 HTTP 206，读取到 2048 字节的 `video/mp2t` 数据。
- 本次只检查单页搜索和一个剧集，未对整个影视目录或全部剧集批量测试。
- 资料依据：[LibreTV 数据源文档](https://libretv.is-an.org/wiki/Data-Sources.html)。

两个点播源均不需要在本包中填写账号或令牌。具体节目的内容使用授权未逐项核实；接口公开可访问与节目内容的使用授权需分别确认。第三方源中的广告、域名更换和节目下架由来源方决定。

## 内置直播源

列表地址：`https://iptv-org.github.io/iptv/languages/zho.m3u`。

IPTV-org 提供按语言、国家等条件生成的公开频道列表；本包只保存中文列表地址，应用在使用时获取上游当前列表。本次下载包含 216 条，其中一条使用 RTMP 协议，被 LibreTV 自动过滤，实际解析出 215 条。

通过 LibreTV 的 `/api/live/probe` 做分片级抽样：

| 频道样本 | 结果 |
| --- | --- |
| CCTV-1（720p） | 分片返回 HTTP 206，分片级探测通过 |
| CCTV+ 1（600p，非全天播出） | 清单后的分片返回 HTTP 404 |
| CCTV-1 HD（1080p） | 地址返回 HTTP 200，但内容不是有效的 M3U8 清单 |

因此，列表下载成功和频道数量不代表全部频道可播。使用时请在直播页按分组或批量测活，选择可用频道。分片探测仍不能代替浏览器的实际解码、持续播放和目标服务器网络验证。

默认不预置节目单。XMLTV 节目单的频道标识需要和列表中的 `tvg-id` 匹配，确认匹配后可在直播源 JSON 中添加 `epg` 地址。

资料依据：[IPTV-org 使用与列表说明](https://github.com/iptv-org/iptv)、[LibreTV 直播文档](https://libretv.is-an.org/wiki/Live-IPTV.html)。IPTV-org 声明其列表收录由社区提交的公开流地址；这项声明不构成对每个频道、每种使用方式的逐项授权核验。

## 替换、关闭与后续维护

- 默认来源由 1Panel 安装表单的 `DEFAULT_SOURCES`、`DEFAULT_LIVE_SOURCES` 提供，均可替换；填写 `[]` 可关闭相应预置。
- `DEFAULT_SUBSCRIPTIONS` 默认保持 `[]`，用户可另外配置自己的源订阅。
- 已有安装需要更新安装参数并重建容器，单纯同步应用目录不会替换原来的参数。浏览器中已有的来源勾选保持用户设置。
- 预置地址会在登录前经 `/api/status` 返回，请勿在这些字段中写入私密订阅或访问令牌。
- 源失效时先用站内测活与换源功能检查，再核对来源方的最新接口公告。IPv6、地区限制和服务器出口差异可能影响探测结果。
- 本次完成了安装参数到容器环境的编排检查，并在本地源码生产构建中调用真实接口抽检；未进行 1Panel 实机安装、逐频道浏览器实播和长时间稳定性测试。
