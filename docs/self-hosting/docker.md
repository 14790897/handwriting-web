# Docker 部署

自己搭一个实例，最省事的方式是 Docker Compose：三个容器，一条命令起来。

## 前置条件

- 装了 Docker 和 Docker Compose
- 一台能跑容器的机器（默认配置按 1 核 / 2 GB 左右的规格调的）

## 起来

```shell
git clone https://github.com/14790897/handwriting-web.git
cd handwriting-web
docker compose up -d
```

默认端口是 **2345**，打开 <http://localhost:2345> 就能用。

## 三个容器分别干什么

| 服务 | 镜像 | 作用 |
|---|---|---|
| `frontend` | `14790897/frontend-handwriting` | Nginx，对外提供页面，并把 `/api/` 反代到后端。宿主机 `2345` → 容器 `80`。 |
| `backend` | `14790897/backend-handwriting` | FastAPI，真正干活的地方。端口**只绑在 `127.0.0.1:5005`**，不对外。 |
| `watchtower` | `containrrr/watchtower` | 每 6 小时拉一次新镜像并滚动重启，实现自动更新。 |

后端刻意不暴露到公网 —— 外部的请求一律先进 Nginx 再由它转发。想换个对外端口，改
`docker-compose.yml` 里 frontend 的 `"2345:80"` 左边那个数字。

## 字体

字体放在仓库根目录的 `ttf_files/`，Compose 会把它挂到容器的 `/app/font_assets_host`：

```yaml
volumes:
  - ./ttf_files:/app/font_assets_host
  - ./logs:/app/logs
```

放进去之后**重启后端容器**生效：

```shell
docker compose restart backend
```

这些字体就是界面上字体下拉框里的选项。

!!! note "为什么不直接挂载到字体目录"
    Compose 里没有把 `ttf_files` 直接挂到后端读字体的目录，而是挂到 `_host` 这个中转位置，
    由后端在启动时同步过去。直接挂载的话，容器里预置的字体会被宿主机的空目录盖掉。

## 日志

- 后端日志落在宿主机的 `./logs/`。
- 也能直接看容器的输出：

  ```shell
  docker compose logs -f backend
  ```

## 更新

- **自动** —— watchtower 每 6 小时检查一次，有新镜像就滚动重启。
- **手动** ——

  ```shell
  docker compose pull
  docker compose up -d
  ```

## 停掉 / 清掉

```shell
docker compose down          # 停掉并删除容器
docker compose down -v       # 同上，另外删掉 Docker 管理的卷
```

!!! note "`-v` 删不掉你的字体和日志"
    `ttf_files` 和 `logs` 是**绑定挂载**到宿主机目录的，不属于 Docker 管理的卷，
    所以 `-v` 不会碰它们。这份 Compose 甚至没有定义任何具名卷，`-v` 在这里什么都不会额外删。
    想彻底清干净，得自己删宿主机上的目录：

    ```shell
    rm -rf ttf_files logs
    ```

## 反向代理和 HTTPS

Compose 里的 Nginx 只监听 HTTP。要挂到域名上、配证书，在它前面再放一层
（Caddy、Traefik，或者宿主机的 Nginx）转发到 `127.0.0.1:2345` 即可。

!!! warning "上传大文件的超时"
    长文本渲染要几十秒到几分钟。前面那层代理如果超时太短，请求会在浏览器里失败，
    但后端其实还在生成。把代理的读超时放宽一些。
