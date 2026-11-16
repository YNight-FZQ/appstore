# Obsidian（linuxserver/obsidian）

Obsidian 是基于本地 Markdown 文件的知识库应用。本应用包使用 [linuxserver/docker-obsidian](https://github.com/linuxserver/docker-obsidian)，把 Obsidian 桌面运行在容器内，并通过 [Selkies](https://docs.linuxserver.io/selkies/) 把桌面流式传输到浏览器，因此可以在任意设备的浏览器中打开同一份知识库。

本包使用 `lscr.io/linuxserver/obsidian:1.15.1`，对应上游 Obsidian `v1.15.1`；上游支持 `amd64` 与 `arm64`。上游许可证为 MIT，图标取自上游仓库。

## ⚠️ 安全边界（安装前必读）

这个容器**等同于一台可远程登录的主机**，而不是普通 Web 应用：

- 桌面中包含终端，且容器内 **`sudo` 无需密码**。任何能访问到该端口的人都能在容器内获得 root、安装软件并探测你的内网。
- 镜像默认**完全没有认证**。本包在表单中把基础认证用户名和密码设为必填，并在 Compose 中用 `${VAR:?}` 强制校验，避免空值静默禁用认证。
- 基础认证（`CUSTOM_USER` + `PASSWORD`）只适合把无关的人挡在外面，**不足以抵御公网攻击**。公网访问必须在前面叠加反向代理认证（如 1Panel 网站访问限制、Authelia、Authentik），并把反向代理作为唯一入口。
- 不要把 `PANEL_APP_PORT_HTTPS` / `PANEL_APP_PORT_HTTP` 直接绑定到 `0.0.0.0` 后暴露到公网。

## 端口

镜像提供两个端口，用途不同：

| 表单字段 | 容器端口 | 用途 |
| --- | --- | --- |
| `PANEL_APP_PORT_HTTPS` | 3001 | 镜像自带自签名证书的 HTTPS，**浏览器直接访问用这个**，首次会提示证书不受信任，需手动接受 |
| `PANEL_APP_PORT_HTTP` | 3000 | 明文 HTTP，**仅用于反向代理终止 TLS 后转发**，不要直接用来访问 |

两个端口默认都只绑定宿主机 `127.0.0.1`。直接访问时浏览器必须使用 `https://`——Selkies 依赖 WebCodecs，而它只在安全上下文中可用，用 `http://` 打开会黑屏或无画面。

反向代理需要正确转发 WebSocket 升级头，并建议关闭响应缓冲（`proxy_buffering off`），否则会出现黑屏或画面卡住。

## 数据与权限

- 知识库和程序配置都在容器的 `/config`，本包映射到安装目录下的 `./data`。**升级、重建容器都不会影响它**，卸载时也不要直接删除安装目录。
- `PUID` / `PGID` 决定容器内进程映射到的宿主机用户与用户组。它们应与 `./data` 目录的实际属主一致，否则会出现文件无法写入。可用 `id <用户名>` 查询宿主机的 uid/gid。
- 镜像不含 `--user` 方式运行的支持，请使用 `PUID` / `PGID`，不要改成 `user:` 字段。

## 安装

1. 在 1Panel 中同步本地应用，选择版本 `1.15.1`。
2. 设置两个端口、基础认证用户名与密码、PUID/PGID 和时区。
3. 安装完成后在宿主机访问 `https://127.0.0.1:<HTTPS 端口>`，接受自签名证书后即可看到 Obsidian 桌面。
4. 在 Obsidian 里打开或创建 vault，建议放在 `/config` 之下（对应宿主机 `./data`），这样数据随目录持久化。

## 资源要求

| 资源 | 最低 | 推荐 |
| --- | --- | --- |
| CPU | 2 核 | 4 核 |
| 内存 | **2 GiB** | 4 GiB |
| 磁盘 | 1 GB | 4 GB+（随知识库增长） |

**内存怎么算**：本包设置的 `shm_size: '1gb'` 占用的是容器内存的一部分，不是额外开销——也就是说 2 GiB 里有 1 GiB 是给 Chromium 的共享内存。宿主机空闲内存低于 2 GiB 时容器会在启动阶段崩溃。CPU 侧一般正常编辑很轻，大知识库索引、全文搜索、关系图谱渲染和装了很多插件时才会出现短时占用高峰。

Electron 应用需要较大的共享内存，本包按上游要求设置 `shm_size: '1gb'`；不要为了省内存把它调小，否则会出现标签页/渲染进程崩溃。

`PIXELFLUX_WAYLAND` 默认关闭（与上游 2026-04 起的默认一致）。如果出现缩放异常或画面问题，再尝试开启；弱 CPU 或出现花屏、黑屏时应保持关闭。

GPU 加速是可选能力，**不装 GPU 也能正常使用**，只是渲染与编码由 CPU 承担。上游支持挂载 `/dev/dri`（Intel/AMD）或 NVIDIA 运行时，本包未启用，需要时请自行编辑 Compose。挂载 GPU 后容器会自动识别并配置，可用 `AUTO_GPU=false` 关闭该行为。

## 自动更新

本包未内置 WUD 标签，镜像固定为 `1.15.1`，升级需要新增版本目录。上游对这类镜像明确不建议无人值守自动更新——Obsidian 与 Selkies 的升级可能包含不兼容变更，且自更新后 Compose 中的镜像版本会与实际运行版本不一致，1Panel 重建容器时会静默回退。

## 参数来源

- [上游应用文档](https://docs.linuxserver.io/images/docker-obsidian)：端口、`PUID`/`PGID`/`TZ`、`/config` 卷、`shm_size` 要求
- [Selkies 安全说明](https://docs.linuxserver.io/selkies/user-guide/security/)：默认无认证、密码less sudo、HTTPS 必需
- [Selkies 反向代理说明](https://docs.linuxserver.io/selkies/user-guide/reverse-proxy/)：WebSocket 升级与关闭缓冲
- 镜像事实：`amd64`/`arm64` 双架构、`1.15.1` 对应上游 `v1.15.1`

本次仅完成静态检查，**尚未在 1Panel 实机安装、重建或升级验证**。
