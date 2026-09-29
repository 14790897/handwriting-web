const fs = require("fs");
const path = require("path");
const { execFileSync } = require("child_process");
const { defineConfig, devices } = require("@playwright/test");

const repoRoot = path.resolve(__dirname, "..");
const frontendDir = path.join(repoRoot, "frontend");
const backendDir = path.join(repoRoot, "backend");

// frontend/vue.config.js 的 /api 代理写死了 5005 和 8080，这里保持一致
const BACKEND_PORT = 5005;
const FRONTEND_PORT = 8080;
const FRONTEND_URL = `http://127.0.0.1:${FRONTEND_PORT}`;

// 跑在后端 git worktree 里时，venv 往往在主的那个工作区（git worktree list 的第一项）
function mainWorktreeRoot() {
  try {
    const output = execFileSync("git", ["worktree", "list", "--porcelain"], {
      cwd: repoRoot,
      encoding: "utf8",
    });
    const line = output.split("\n").find((item) => item.startsWith("worktree "));
    return line ? line.slice("worktree ".length).trim() : null;
  } catch (error) {
    return null;
  }
}

// 系统里可能装着多个 Python（比如依赖版本冲突的那个），
// 真正能用的是能建出 FastAPI() 且装有 handright/opencv 的那个
function canRunBackend(python) {
  const looksLikePath = python.includes("/") || python.includes("\\");
  if (looksLikePath && !fs.existsSync(python)) return false;
  try {
    execFileSync(python, ["-c", "import fastapi; fastapi.FastAPI(); import handright, cv2, fitz"], {
      stdio: "ignore",
      timeout: 60_000,
    });
    return true;
  } catch (error) {
    return false;
  }
}

function resolvePython() {
  if (process.env.E2E_PYTHON) return process.env.E2E_PYTHON;

  const roots = [repoRoot, mainWorktreeRoot()].filter(Boolean);
  const candidates = [
    ...roots.flatMap((root) => [
      path.join(root, "venv", "Scripts", "python.exe"),
      path.join(root, "venv", "bin", "python"),
    ]),
    "python",
    "python3",
  ];
  const python = candidates.find(canRunBackend);
  if (!python) {
    throw new Error(
      "找不到可用的后端 Python 解释器（需能 import fastapi/handright/cv2/fitz），请用 E2E_PYTHON 指定"
    );
  }
  return python;
}

module.exports = defineConfig({
  testDir: "./tests",
  timeout: 120_000,
  expect: { timeout: 20_000 },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 2 : undefined,
  reporter: [["list"], ["html", { open: "never" }]],
  use: {
    baseURL: FRONTEND_URL,
    locale: "zh-CN",
    // 应用注册了 Service Worker，且它在 controllerchange 时会 confirm + reload，
    // 测试里直接禁用，避免页面在断言中途刷新
    serviceWorkers: "block",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      // app.py 用相对路径写 logs/app.log、tasks.db、temp/，必须以 backend 为工作目录启动
      command: `"${resolvePython()}" -m uvicorn app:app --host 127.0.0.1 --port ${BACKEND_PORT}`,
      cwd: backendDir,
      url: `http://127.0.0.1:${BACKEND_PORT}/api/fonts_info`,
      reuseExistingServer: !process.env.CI,
      timeout: 180_000,
      env: {
        // 测试机和 CI runner 的 CPU 常被 dev server + 浏览器占满，
        // 会触发 app.py 的 CPU 过载保护（429），把阈值放到 100 避免误伤
        CPU_USAGE_LIMIT: "100",
      },
    },
    {
      command: "npm run serve",
      cwd: frontendDir,
      url: FRONTEND_URL,
      reuseExistingServer: !process.env.CI,
      timeout: 300_000,
    },
  ],
});
