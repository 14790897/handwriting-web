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
cd backend && uvicorn app:app --reload --host 0.0.0.0 --port 5005

# 或使用 VS Code Tasks:
#   "⚡ 全栈开发 - 同时启动前后端"

# E2E 测试 (Playwright, 自动拉起前后端; 首次先 npm install && npx playwright install chromium)
cd e2e && npm test
```

## 编码约定

- **Commit message**: 必须遵循 [Conventional Commits](https://www.conventionalcommits.org/) (`feat:` / `fix:` / `chore:` 等)，semantic-release 靠它决定版本号
- **分支**: 只推到 `main`，不要直接 push（通过 PR）
- **i18n**: 所有用户可见文字必须同时提供中英文翻译，在 `frontend/src/i18n.js` 中添加
- **E2E 选择器**: 需要被 `e2e/` 测试点到的元素统一加 `data-testid`，测试侧只用 `getByTestId`，不要依赖中文文案或 CSS 类
- **注释**: 后端使用中文注释，标注日期
- **Lint**: 前端保存前自动 lint (`lint-staged` + ESLint + Prettier)
- **不要手动改** `CHANGELOG.md` 和版本号，由 semantic-release 自动管理

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
