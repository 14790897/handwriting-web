# Fonts & Resource Limits

These are the numbers that decide how much a self-hosted instance can take.

## CPU limits

`docker-compose.yml` sets a CPU quota on both containers by default:

| Container | Setting | Equivalent |
|---|---|---|
| `frontend` | `cpu_quota: 50000`, `cpu_period: 100000` | half a core |
| `backend` | `cpu_quota: 80000`, `cpu_period: 100000` | 0.8 of a core |

To remove the limit, delete or comment out those three lines (`cpu_count` / `cpu_quota` /
`cpu_period`). To change how strict it is, tune `cpu_quota` — it is "how many microseconds of CPU
per `cpu_period` microseconds".

Memory limits are `mem_limit` / `memswap_limit`: 800 MB for the frontend and 1500 MB for the backend.
**Rendering large sheets is memory-hungry** — if you see out-of-memory errors, start here.

## Concurrency: two renders at a time

The backend has a concurrency gate:

```
MAX_CONCURRENT_EXECUTIONS = 2
```

At most two render jobs run at once; the rest queue. This is sized for a modest machine — rendering
is CPU-bound, so running more at once mostly just slows everything down. On a powerful machine you can
raise it, but raise `cpu_quota` too or they will still be fighting over 0.8 of a core.

## Queue: returns 503 when full

```
MAX_ACTIVE_TASKS = 8
```

When "queued + processing" reaches 8, new submissions are **rejected outright** with a 503, which the
frontend turns into a wait countdown. The backlog is bounded.

## Task expiry

```
TTL = 30 minutes
```

Tasks and their rendered images are cleaned up after 30 minutes, so the disk does not fill up.
Users need to download within that window — after expiry the same `task_id` returns 404.

## Overload protection

The backend watches its own CPU usage and returns `429` for new requests above the threshold, to avoid
being crushed:

```shell
CPU_USAGE_LIMIT=90   # default 90 (percent); 100 effectively disables it
```

The E2E tests and the desktop build set it to 100 precisely so this guard stays out of the way.

## Rate limiting

Endpoints are rate-limited per client IP, defaulting to:

```
1000 per 5 minute
```

Individual routes have their own, more specific limits (polling and fetching results are far more
generous than submitting a job). When you are throttled you get a `429`.

## Fonts

- **Fonts baked into the image** come from the repository's `font_assets/` and are included at build time.
- **Your own fonts** go in `ttf_files/` — see [Docker Deployment](docker.md#fonts).
- Both appear in the font dropdown.

!!! warning "Check font licences yourself"
    **The code is MIT; the fonts are not.** Fonts bundled in the repository and fonts users upload each
    carry their own licence. Before serving them to others, confirm you are allowed to redistribute them.
