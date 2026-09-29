# AGENTS.md

> 写给 AI 编程助手（Copilot、Cursor、Claude Code 等）的项目说明。

## 项目概述

手写体生成 Web 应用。用户输入文字 → 选择字体/参数 → 后端用 `handrightbeta` 渲染手写图片 → 返回图片或 PDF。

## 技术栈

| 层 | 技术 |
|---|---|
| 前端 | Vue 3 + Vue Router + Vuex + Vue I18n + Bootstrap 5 + Axios |
| 后端 | Python 3.10+ / FastAPI + Uvicorn (开发) / Gunicorn (生产) |
| 手写引擎 | handrightbeta 8.7, Pillow, OpenCV, scikit-learn (DBSCAN) |
| 任务队列 | 自建 SQLite 持久化队列 (`task_store.py`) |
| 容器化 | Docker Compose (frontend + backend + watchtower) |
| 版本发布 | semantic-release (Conventional Commits) |
| 监控 | Sentry (前后端), Google Analytics, Microsoft Clarity |
| PWA | Workbox (NetworkFirst 策略, 离线缓存) |

## 目录结构

```
handwriting-web/
├── frontend/                 # Vue 3 SPA (Vue CLI)
│   ├── src/
│   │   ├── main.js           # 入口: Vue + Bootstrap + Sentry + GA + Clarity
│   │   ├── App.vue           # 根组件: 启动动画 + PWA + SEO meta
│   │   ├── i18n.js           # 中/英文翻译
│   │   ├── router/index.js   # 6 个路由
│   │   ├── store/index.js    # Vuex
│   │   ├── views/            # 页面组件
│   │   └── components/       # BookSplash, PWAInstallPrompt 等
│   ├── vue.config.js         # 开发代理 /api → 127.0.0.1:5005
│   └── nginx.conf            # 生产 Nginx 配置
├── backend/                  # FastAPI 后端
│   ├── app.py                # 主应用 (~1300 行): 路由 + 手写生成逻辑
│   ├── task_store.py         # SQLite 任务队列 (30min TTL, 线程安全)
│   ├── task_types.py         # Pydantic 模型 + Form 依赖注入
│   ├── identify.py           # OpenCV 图片边距/行距检测
│   ├── pdf.py                # PyMuPDF 生成 PDF
│   └── schedule_clean.py     # 每日午夜清理 temp/
├── e2e/                      # Playwright 端到端测试 (真实前后端 + 少量 mock 分支)
├── desktop/                  # Windows 桌面版 (Electron 外壳 + PyInstaller 打包的后端)
│   ├── main.js               # Electron 主进程: 拉起后端 exe + 端口握手 + 开窗
│   ├── splash.html           # 后端冷启动期间的等待页
│   ├── backend.spec          # PyInstaller onedir 配置 (打包 dist/、字体与 VERSION)
│   ├── build.sh              # 一键构建脚本 (前端 dist → 后端 exe → 安装包)
│   └── requirements-build.txt # 仅打包期依赖 (pyinstaller)
├── scripts/
│   └── sync-version.js       # 发版时把发版号同步到 desktop/ 与 backend/VERSION
├── serverless/               # Vercel 函数 (nodemailer 发邮件)
├── .github/workflows/        # CI/CD: frontend/backend docker 构建 + semantic-release + e2e
├── docker-compose.yml        # 3 服务: frontend + backend + watchtower
├── release.config.js         # semantic-release 配置
├── package.json              # 仅 semantic-release 依赖
└── font_assets/              # 默认字体文件
```

## 本地开发命令

```bash
# 前端 (端口 8080, 自动代理 /api 到后端)
cd frontend && npm run serve

# 后端 (端口 5005, 热重载)
# 下面是 bash / Git Bash 写法 (本项目 .vscode/tasks.json 用的 cmd.exe 同样支持 &&;
# PowerShell 5.1 不支持 &&, 需要把每条命令拆开单独执行)
# 首次先在仓库根建 venv 并装依赖:
#   Windows:      python -m venv venv && venv/Scripts/python.exe -m pip install -r backend/requirements.txt
#   Linux/macOS:  python3 -m venv venv && venv/bin/python -m pip install -r backend/requirements.txt
# 启动时必须用这个 venv, 不要用系统 Python —— 系统环境 fastapi 0.115.6 + starlette 1.3.1 起不来,
# 报 TypeError: Router.__init__() got an unexpected keyword argument 'on_startup'
cd backend && ../venv/Scripts/python.exe -m uvicorn app:app --reload --host 0.0.0.0 --port 5005
#            Linux/macOS 换成 ../venv/bin/python

# 或使用 VS Code Tasks:
#   "⚡ 全栈开发 - 同时启动前后端"

# E2E 测试 (Playwright, 自动拉起前后端; 首次先 npm install && npx playwright install chromium)
cd e2e && npm test
```

## 桌面版 (Windows exe)

Electron 外壳 + PyInstaller 打包的后端 exe。后端在 127.0.0.1 上随机端口同时提供
SPA 与 `/api`（同源，前端无需跨域配置），Electron 只用 `BrowserWindow` 加载它。

```bash
# 一键构建 (前端 dist → 后端 exe → NSIS 安装包 + 便携版)
bash desktop/build.sh

# 只出 Electron 目录版（不生成 NSIS 安装包）/ 跳过依赖安装 / 指定解释器（CI 用）
bash desktop/build.sh --app-only
bash desktop/build.sh --skip-deps
PYTHON=python bash desktop/build.sh

# 开发调试: 先单独构建后端 exe, 再用 Electron 直接跑
cd desktop && npx electron .
```

产物：`desktop/build/backend/handwriting-backend/`（后端 onedir）、
`desktop/build/installer/`（安装包与便携版）。

**发版自动构建**：`.github/workflows/desktop_release.yml` 在 Semantic Release 工作流成功后，
在 `windows-latest` 上构建并把安装包/便携版挂到对应 Release 上（PyInstaller 不能交叉编译，
所以必须是 Windows runner）。用 `workflow_run` 而不是 `release: published` / `push: tags`，
是因为 token 触发的 release/tag 事件不会再触发新工作流；`workflow_run` 不受该限制，
所以不依赖 `secrets.GH_TOKEN` 是不是 PAT。也可以用 workflow_dispatch 手动补传历史版本。

### 版本号

发版号的唯一来源是 semantic-release 的 `${nextRelease.version}`（仓库根的 `package.json`
没有 version 字段）。`release.config.js` 用 `@semantic-release/exec` 在 prepare 阶段跑
`scripts/sync-version.js`，把发版号同步到三处，再由 `@semantic-release/git` 一起提交：

| 位置 | 谁读它 |
|---|---|
| `desktop/package.json` / `desktop/package-lock.json` | electron-builder 的产物名（`${version}`）、About 对话框 |
| `backend/VERSION` | 后端 `/api/version` 的兜底；进后端镜像（`COPY backend /app`）与 PyInstaller 的 datas |

展示路径：桌面版 Electron 通过 `HANDWRITING_APP_VERSION` 把 `app.getVersion()` 传给后端
（拿到的是**真正安装的那个版本**，优先于 VERSION 文件）；Web 部署则读镜像里的
`backend/VERSION`。前端在首页页脚显示 `/api/version` 的结果（`data-testid="app-version"`），
取不到就整行不显示。

**不要手改这三个文件里的版本号**，它们由发版流程维护。构建产物 `desktop/build/`、
`desktop/node_modules/` 均已被 `.gitignore` 忽略。

桌面版与线上差异（都靠 `DESKTOP_MODE` / 环境变量区分，Web 部署不受影响）：

- 数据目录在 `%LOCALAPPDATA%\HandwritingWeb`（`tasks.db`、`temp/`、`logs/`、字体），
  由 `backend/desktop_main.py` 在导入 `app` 之前设好环境变量并 `chdir`。
  打包后 `__file__` 落在只读/临时的包内目录，不能再依赖它定位数据。
- 前端 `frontend/src/desktop.js` 按 UA 判定 Electron，桌面版不加载 GA/Clarity/Chatwoot/Sentry。
- 关掉上报上游 Sentry（`SENTRY_DSN=""`）、跳过 pandoc 自动下载（无 pandoc 时回退 python-docx）、
  放开 CPU 占用守卫（`CPU_USAGE_LIMIT=100`）。
- Electron 退出后后端自行退出：后端轮询 `HANDWRITING_PARENT_PID`。
  **不要改成读 stdin 判断** —— 无控制台的 frozen 进程里阻塞读 stdin 会让后端卡死在启动阶段。

### 桌面版安全与编码（改这块之前先读）

- **跨站请求防护**：本地后端监听在 `127.0.0.1`，任何网页都能向它发请求，而同源策略只挡
  「读响应」、不挡「发请求」。所以 `desktop_main.py` 会把端口提前定下来并设
  `HANDWRITING_ALLOWED_ORIGIN`，`app.py` 据此把 CORS 白名单收紧到这一个来源，
  并用 Origin/Referer 主动拒绝其它来源（HTTP 用中间件，WebSocket 不走中间件、单独校验）。
  **不要退回 `allow_origins=["*"]`**，也不要去掉这个校验。
- **Windows 编码**：打包后 stdout 是管道、日志是文件，Python 默认按 ANSI 代码页编码，
  中文会抛 `UnicodeEncodeError`（`backend/identify.py` 里有中文 `print`，会让
  `/api/imagefileprocess` 直接 500）或写成乱码。Electron 传 `PYTHONUTF8=1` +
  `PYTHONIOENCODING=utf-8`，`desktop_main.py` 另有一层 `reconfigure` 兜底，
  日志文件则显式用 `encoding="utf-8"`。新增往 stdout/文件写中文的代码时注意这条。

## 编码约定

- **Commit message**: 必须遵循 [Conventional Commits](https://www.conventionalcommits.org/) (`feat:` / `fix:` / `chore:` 等)，semantic-release 靠它决定版本号
- **分支**: 只推到 `main`，不要直接 push（通过 PR）
- **i18n**: 所有用户可见文字必须同时提供中英文翻译，在 `frontend/src/i18n.js` 中添加
- **UI 风格**: 新增/改版的界面必须复用站点既有设计语言，不要自带一套配色 —— 主按钮 `#007BFF`（hover `#0056b3`、active `#003d73`）、圆角 `5px`、字体沿用全局 `Avenir, Helvetica, Arial, sans-serif`、面板阴影 `0 2px 5px rgba(0,0,0,0.1)`、输入框边框 `1px solid #ddd`。参考 `HomeView.vue` 的 `.action-btn`（顶栏按钮）与 `.letter-format-button`
- **E2E 选择器**: 需要被 `e2e/` 测试点到的元素统一加 `data-testid`，测试侧只用 `getByTestId`，不要依赖中文文案或 CSS 类
- **注释**: 后端使用中文注释，标注日期
- **Lint**: 前端保存前自动 lint (`lint-staged` + ESLint + Prettier)
- **不要手动改** `CHANGELOG.md` 和版本号，由 semantic-release 自动管理

## 维护者工作流：外部 PR 与截图

> 来自 2026-09-28 处理贡献者 fork PR (#66/#67) 的实操经验。

**推送权限只覆盖 PR 头分支**

- `gh api repos/<fork> --jq .permissions.push` 返回 `false` **不代表不能推** —— 只要 PR 开了 `maintainerCanModify`（allow edits by maintainers），维护者就能推到该 PR 的**头分支**：
  `git push https://github.com/<fork-owner>/handwriting-web.git HEAD:refs/heads/<branch>`
- 但该权限**仅限头分支**：fork 上的其他分支（如截图用的 `pr-assets`）推送会被拒 `permission denied`
- `git push --dry-run` **不可靠** —— 对它报成功的分支，真实推送仍可能被拒

**截图只能靠「推分支 + raw 链接」**

GitHub 没有给 token 用的图片上传接口：网页版拖拽上传走的是网页会话专属的 `uploads.github.com/user-attachments/assets`（token 调用返回 404），策略接口 `github.com/upload/policies/assets` 同样只认网页会话。所以可行做法只有一条：

- 图片推到某个公开分支，再用 `raw.githubusercontent.com/<owner>/<repo>/<commit-sha>/<path>` 引用
- 用 **commit SHA** 而非分支名引用 —— 分支被改写（force-push）时，链接不会跟着变
- 但这只防改写、**不防删分支**：没有 branch / tag / PR ref 指向该 commit 时，它会变成不可达对象，被 GitHub GC 回收后链接就 404（reachability 按 branch/tag 判定，见 [GitHub 博客](https://github.blog/engineering/scaling-gits-garbage-collection/)）。**截图分支要长期保留，不要删**
- **更稳的位置是 PR 头分支** —— 只要该提交还是 PR 的**当前头**，`refs/pull/<n>/head` 就会引用它，删分支、合并都不会让它失效。实测 PR #76：建 PR 后删掉头分支，ref 仍在、commit 可解析、raw 仍返回 200 且字节数与本地一致，只有 PR 本身转为 closed
- 但它**跟随 PR 当前头，并非永久钉住某个提交** —— 作者再推提交或 force-push，ref 就移到新提交，旧提交失去引用、可能被 GC（PR #67 的 ref 就随我们的推送从 `8bbfc2c` 移到了 `b2f3462`）。所以它是「比普通分支更耐删」，真要永久还是得把图并进 `main`
- 代价与限制：图会进 PR 的 Files changed；而且**必须在 PR 还开着时推** —— 合并后 `maintainerCanModify` 会被收回，维护者再也推不进去（PR #67 合并后才想补图，就是这时踩到的）
- 不介意「别删分支」这个约束的话，放普通分支也行（如主仓库的 `pr-assets` 分支，孤儿提交只含图片，不带整棵树）
- **贡献者的图放自己的 fork，维护者别去代推** —— 推不了。例：ejjcc 的 fork 上有 `pr-assets` 分支按 PR 分目录存图（`pr-assets/<slug>/<name>.png`）

## 重要注意事项

- **不要手动修改 `CHANGELOG.md`** — 它由 semantic-release 自动生成
- **不要手动打 tag 或改 package.json 版本号** — semantic-release 全自动
- `backend/app.py` 大约 1300+ 行，包含所有路由和核心手写生成逻辑，修改时注意函数位置
- 后端并发限制: `asyncio.Semaphore(2)`，同时最多 2 个手写生成任务
- 后端速率限制: 使用 slowapi，默认 1000 次/5 分钟，不同路由有不同限制
- 任务队列是自建的 SQLite 实现 (WAL 模式)，任务 30 分钟自动过期
- Docker 部署时字体文件从 `ttf_files/` 挂载到容器
- 前端 PWA 使用 NetworkFirst 策略: 有网用最新，无网用缓存
- Sentry DSN 硬编码在源码中，如需更换请全局搜索替换
- `vps_pull.yml` 已禁用（全部注释），含硬编码 IP 地址
- MySQL 相关代码已注释不用，当前只用 SQLite 做任务队列
