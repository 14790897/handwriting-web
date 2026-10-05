# Local Development

!!! info "The deep material lives in AGENTS.md"
    This page only covers getting the project running. Architecture, coding conventions, the release
    pipeline and all the accumulated gotchas are in
    [`AGENTS.md`](https://github.com/14790897/handwriting-web/blob/main/AGENTS.md) at the repository
    root — read it before changing code. (It is written in Chinese.)

## Requirements

- **Python 3.10 or 3.11** (3.8 – 3.13 all work)
- **Node.js 20 or higher** (a Playwright requirement, for E2E)

## Start the backend (port 5005)

**Use the repository's venv, not your system Python.** The system environment's `fastapi` +
`starlette` combination prevents the app from starting, with
`TypeError: Router.__init__() got an unexpected keyword argument 'on_startup'`.

Create the virtualenv and install dependencies first:

```shell
python -m venv venv
venv/Scripts/python.exe -m pip install -r backend/requirements.txt
```

(On Linux / macOS use `venv/bin/python` instead of `venv/Scripts/python.exe`.)

Then start it:

```shell
cd backend
../venv/Scripts/python.exe -m uvicorn app:app --reload --host 0.0.0.0 --port 5005
```

## Start the frontend (port 8080)

```shell
cd frontend
npm install
npm run serve
```

Open <http://localhost:8080>. The dev server proxies `/api` to `127.0.0.1:5005`, so no CORS setup is
needed locally.

VS Code users can press `Ctrl+Shift+B` — there are tasks that bring up both sides in parallel.

## Running the tests

**Backend unit tests** —

```shell
cd backend
../venv/Scripts/python.exe -m pytest
```

**End-to-end tests (Playwright)** — `e2e/` drives the **real frontend and backend** through complete
flows (actually rendering images, actually downloading attachments); a few branches that are hard to
trigger for real (such as the queue-full 503) are simulated with route interception.

```shell
cd e2e
npm install
npx playwright install chromium
npm test
```

- Dev servers that are not running are started automatically (backend 5005, frontend 8080) and shut
  down afterwards.
- Ones that are already running are reused rather than restarted.
- The run sets `CPU_USAGE_LIMIT=100` so that a dev machine saturated by webpack does not trip the
  backend's overload guard.
- Failure screenshots, videos and traces go to `e2e/test-results/`; open the HTML report with
  `npm run report`.
- If no Python interpreter is found, point at one with `E2E_PYTHON`.

Every pull request runs this via `.github/workflows/e2e.yml`.

**Desktop end-to-end** — this drives the real packaged build, so build it first:

```shell
bash desktop/build.sh --app-only
cd e2e && npm run test:desktop
```

## What the code looks like

| Path | Contents |
|---|---|
| `frontend/src/views/HomeView.vue` | The main page: parameters, preview, generation flow |
| `frontend/src/views/TextInput.vue` | Text box and document upload |
| `frontend/src/components/` | Letter layout, generation status, splash animation, PWA prompt |
| `frontend/src/i18n.js` | Chinese and English strings |
| `backend/app.py` | Every route plus the rendering logic (~1300 lines) |
| `backend/task_store.py` | SQLite task queue (WAL, 30-minute expiry) |
| `backend/identify.py` | Detects margins and line spacing from a background image |
| `backend/pdf.py` | PDF generation |

A request comes in, the task is submitted and written to SQLite, a `task_id` is returned immediately,
a background coroutine queues the render, the frontend gets progress over a WebSocket (falling back to
polling), and finally fetches the result.

## Commit conventions

- **Commit messages must follow [Conventional Commits](https://www.conventionalcommits.org/) —**
  semantic-release derives the version number from them, and getting it wrong bumps the wrong version.
- User-visible strings need **both Chinese and English**, added to `frontend/src/i18n.js`.
- Elements that E2E needs to click get a `data-testid`; tests use `getByTestId` only and never rely on
  copy or CSS classes.
- Do not hand-edit `CHANGELOG.md` or version numbers — the release pipeline owns them.
