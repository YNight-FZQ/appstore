# File Share

File Share 提供局域网文件共享。电脑和移动设备可通过浏览器上传、下载文件，下载支持断点续传。配置包 `1.0.0` 固定使用官方镜像 `ghcr.io/cky-thinker/file-share:1.0.13`，支持 `amd64` 和 `arm64`。

## 安装与使用

1. 将应用目录放入目标 1Panel 安装目录下的 `1panel/resource/apps/local/file-share`，同步本地应用后选择 `1.0.0`。
2. 设置管理员用户名和密码。默认启用网页密码认证，服务启动时创建或更新表单中指定的管理员账号。
3. 默认可从宿主机访问 `http://127.0.0.1:5421`。若要供局域网设备使用，在 1Panel 高级设置中开放端口并绑定局域网地址，再用该地址和安装端口访问。容器内端口为 `5421`。

修改管理员密码或认证设置后，重建容器即可应用表单里的新值。

## 数据与更新

- 安装目录的 `data/` 保存账号及设置，对应容器内 `/app/data`。
- `upload/` 保存上传的文件，对应容器内 `/app/upload`。
- 备份时保留这两个目录及实例的 `.env`，其中 `.env` 含管理员凭据。

配置包编号独立于上游版本。包内只读挂载的脚本使用镜像自带的 Level 8 API 初始化数据库，修复上游镜像启动时的 `level is not a function`。更新镜像时需核对上游是否已修复初始化逻辑，并随配置包更新挂载脚本。

部署参数和图标来自上游。[容器镜像构建](https://github.com/cky-thinker/file-share/blob/v1.0.13/.github/workflows/docker.yml) · [服务入口](https://github.com/cky-thinker/file-share/blob/v1.0.13/docker/server.js) · [存储适配器](https://github.com/cky-thinker/file-share/blob/v1.0.13/docker/LevelDbAdapter.js) · [图标](https://github.com/cky-thinker/file-share/blob/v1.0.13/wiki/asserts/icon/file-share.png) · [上游许可证](LICENSE.upstream)
