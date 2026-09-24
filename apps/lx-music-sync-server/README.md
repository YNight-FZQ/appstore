## 产品介绍

**LX Music Sync Server（增强版）** 是基于 [lyswhut/lx-music-sync-server](https://github.com/lyswhut/lx-music-sync-server) 的增强版本，除了 LX Music 桌面端的数据同步功能外，还内置了一个功能强大的 **Web 播放器**。

主要特性：

- **LX Music 数据同步**：与 LX Music 桌面端同步歌单、播放列表、设置等数据
- **Web 播放器**：现代化 UI，支持多源聚合搜索（网易、QQ、酷狗、酷我、咪咕、B 站等）
- **自动缓存**：自动缓存歌词、链接和歌曲文件，弱网环境依旧流畅
- **歌词卡片分享**：一键生成精美歌词海报（支持竖版/横版/方版、深色/浅色/专辑色）
- **多套主题**：森之韵、深海鲨、暖阳意、绯红月等主题，支持自动深色模式
- **Subsonic 协议**：兼容 Subsonic 客户端（如 Substreamer、Symfonium、DSub 等）
- **多用户管理**：支持管理员与公开用户、流量/上传/删除等细粒度权限控制
- **桌面客户端**：跨平台桌面客户端，支持 Windows / macOS / Linux 全家桶

更多信息：

- [项目主页](https://xcq0607.github.io/lxserver/)
- [GitHub 仓库](https://github.com/XCQ0607/lxserver)
- [更新日志](https://github.com/XCQ0607/lxserver/blob/main/changelog.md)

## 使用说明

1. 安装完成后访问：
   - **Web 播放器**：`http://服务器IP:服务端口/`
   - **后台管理**：`http://服务器IP:服务端口{ADMIN_PATH}`
2. 使用后台管理密码登录后台，可以管理用户、配置 LX 同步账号等
3. 如需在 LX Music 桌面端启用同步，请在 LX Music 桌面端填入：
   - 同步服务器地址：`http://服务器IP:服务端口`
   - 同步账号：`admin`
   - 同步密码：在安装时设置的 `LX 同步管理员账户密码`

## 注意事项

- 安装后**务必修改**默认的后台管理密码、Web 播放器密码和 LX 同步密码
- `LX 同步管理员账户密码` 留空则停用 LX 桌面端同步功能，但 Web 播放器仍可使用
- 数据、日志、缓存分别持久化到 `data`、`logs`、`cache` 目录，请定期备份
- `music` 目录用于存放本地音乐文件，需要时把音频文件放入即可
- 默认禁用了匿名统计和更新通知，可放心使用
- 项目遵循 **Apache-2.0** 协议
