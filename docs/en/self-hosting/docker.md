# Docker Deployment

Docker Compose is the easiest way to run your own instance: three containers, one command.

## Requirements

- Docker and Docker Compose installed
- A machine that can run containers (the defaults are sized for roughly 1 core / 2 GB)

## Bring it up

```shell
git clone https://github.com/14790897/handwriting-web.git
cd handwriting-web
docker compose up -d
```

The default port is **2345** — open <http://localhost:2345>.

## What the three containers do

| Service | Image | Role |
|---|---|---|
| `frontend` | `14790897/frontend-handwriting` | Nginx. Serves the pages and proxies `/api/` to the backend. Host `2345` → container `80`. |
| `backend` | `14790897/backend-handwriting` | FastAPI — the part that actually does the work. Its port is bound to **`127.0.0.1:5005` only**, never exposed publicly. |
| `watchtower` | `containrrr/watchtower` | Pulls new images every 6 hours and rolling-restarts, giving you automatic updates. |

The backend is deliberately not exposed to the internet — outside traffic always goes through Nginx
first. To change the public port, edit the left-hand number in the frontend's `"2345:80"` mapping
in `docker-compose.yml`.

## Fonts

Fonts live in `ttf_files/` at the repository root, which Compose mounts at `/app/font_assets_host`:

```yaml
volumes:
  - ./ttf_files:/app/font_assets_host
  - ./logs:/app/logs
```

After adding fonts, **restart the backend container**:

```shell
docker compose restart backend
```

These fonts are what appears in the font dropdown.

!!! note "Why not mount straight into the font directory"
    `ttf_files` is mounted at an intermediate `_host` location rather than directly onto the directory
    where the backend reads fonts, and the backend syncs it on startup. Mounting it directly would let
    the host's empty directory shadow the fonts pre-packaged in the image.

## Logs

- Backend logs land in `./logs/` on the host.
- You can also read the container output directly:

  ```shell
  docker compose logs -f backend
  ```

## Updating

- **Automatic** — watchtower checks every 6 hours and rolling-restarts when a new image appears.
- **Manual** —

  ```shell
  docker compose pull
  docker compose up -d
  ```

## Stopping and cleaning up

```shell
docker compose down          # stop and remove the containers
docker compose down -v       # the same, plus remove Docker-managed volumes
```

!!! note "`-v` does not delete your fonts or logs"
    `ttf_files` and `logs` are **bind mounts** onto host directories, not Docker-managed volumes, so
    `-v` leaves them alone. This Compose file defines no named volumes at all, so `-v` removes nothing
    extra here. To wipe them, delete the host directories yourself:

    ```shell
    rm -rf ttf_files logs
    ```

## Reverse proxy and HTTPS

The Nginx in the Compose file serves plain HTTP only. To put it behind a domain with a certificate,
add another layer in front (Caddy, Traefik, or a host Nginx) and forward to `127.0.0.1:2345`.

!!! warning "Timeouts on large uploads"
    Rendering long text takes anywhere from tens of seconds to several minutes. If the proxy in
    front has too short a timeout, the request fails in the browser while the backend is still
    working. Raise the proxy's read timeout.
