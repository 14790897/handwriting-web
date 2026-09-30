// 桌面版（Electron 外壳 + PyInstaller 后端 exe）的启动/清理工具。
//
// 这里驱动的是 electron-builder 出来的真实可执行文件
// （desktop/build/installer/win-unpacked/HandwritingWeb.exe），不是 `electron .`
// 的开发形态：后端 exe、asar 里的站点、extraResources 里的 backend 目录都按
// 「用户装到的那个东西」的布局走。用 _electron 需要 Electron 二进制本身，
// 不需要下载浏览器，也不需要 desktop/node_modules。
const { _electron: electron } = require("@playwright/test");
const crypto = require("crypto");
const fs = require("fs");
const http = require("http");
const net = require("net");
const os = require("os");
const path = require("path");

const REPO_ROOT = path.resolve(__dirname, "..", "..");
const DEFAULT_EXE = path.join(
  REPO_ROOT,
  "desktop",
  "build",
  "installer",
  "win-unpacked",
  "HandwritingWeb.exe"
);

// 后端冷启动要载入 sklearn/opencv（实测本机约 5-10 秒，CI 更慢），
// 加载完之前窗口停在 splash.html
const APP_READY_TIMEOUT_MS = 180_000;

function appExePath() {
  const override = process.env.DESKTOP_APP_EXE;
  if (override) {
    if (!fs.existsSync(override)) {
      throw new Error(`DESKTOP_APP_EXE 指向的文件不存在：${override}`);
    }
    return path.resolve(override);
  }
  if (!fs.existsSync(DEFAULT_EXE)) {
    throw new Error(
      `找不到打包后的桌面版：${DEFAULT_EXE}\n` +
        "先构建（bash desktop/build.sh --app-only），或用 DESKTOP_APP_EXE 指定可执行文件"
    );
  }
  return DEFAULT_EXE;
}

// desktop/main.js 用 LOCALAPPDATA 定位后端数据目录（<LOCALAPPDATA>/HandwritingWeb），
// 所以隔离要作用在 Electron 进程的环境上。
function prepareIsolatedEnv() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "hww-desktop-e2e-"));
  const env = {
    ...process.env,
    LOCALAPPDATA: path.join(root, "localappdata"),
  };
  const dataDir = path.join(env.LOCALAPPDATA, "HandwritingWeb");
  for (const dir of [env.LOCALAPPDATA, dataDir]) {
    fs.mkdirSync(dir, { recursive: true });
  }
  return { root, env, dataDir };
}

function logTail(dataDir, lines = 40) {
  const logPath = path.join(dataDir, "backend-console.log");
  try {
    return fs.readFileSync(logPath, "utf8").split("\n").slice(-lines).join("\n");
  } catch (error) {
    return `(读不到 ${logPath}：${error.message})`;
  }
}

// 等字体列表就绪：生成流程要靠它取 font_option，没加载完就点会报错。
// 注意只能用 count —— <option> 没有布局盒，Playwright 的可见性断言永远等不到。
async function waitForFontOptions(page, timeout = 60_000) {
  const deadline = Date.now() + timeout;
  for (;;) {
    const count = await page.getByTestId("font-select").locator("option").count();
    if (count > 0) return count;
    if (Date.now() > deadline) {
      throw new Error("字体列表 60 秒内没加载出来（/api/fonts_info 可能失败了）");
    }
    await page.waitForTimeout(200);
  }
}

async function waitForHome(page) {
  await page.getByTestId("preview-btn").waitFor({ timeout: 60_000 });
  await waitForFontOptions(page);
}

async function launchDesktopApp() {
  const exe = appExePath();
  const { root, env, dataDir } = prepareIsolatedEnv();
  // Electron 的 userData（单实例锁、缓存）由 Chromium 走 shell API 解析，改 APPDATA
  // 环境变量没有用 —— 只有 --user-data-dir 能换掉它。不隔离的话，本机正开着正式版、
  // 或上一个用例的实例还没退干净时，新实例会被判成「第二个实例」拿到锁失败后
  // 立刻 app.quit()，现象是窗口一直不出现。
  const app = await electron.launch({
    executablePath: exe,
    args: [`--user-data-dir=${path.join(root, "userdata")}`],
    env,
  });

  // 桌面版的下载是 Electron 自己落盘的：Playwright 的 download 事件在 Electron 下
  // 不会触发（实测），所以挂主进程的 will-download，把文件收进测试目录再看。（也用
  // setSavePath 避免测试往用户真实的下载文件夹里丢文件。）
  const downloadsDir = path.join(root, "downloads");
  fs.mkdirSync(downloadsDir, { recursive: true });
  await app.evaluate(({ session }, target) => {
    session.defaultSession.on("will-download", (event, item) => {
      item.setSavePath(`${target}/${item.getFilename()}`);
    });
  }, downloadsDir);

  const page = await app.firstWindow();

  let port;
  try {
    // main.js 先加载 splash.html，后端就绪后再 loadURL 到 http://127.0.0.1:<port>/
    await page.waitForURL(/^http:\/\/127\.0\.0\.1:\d+\/?$/, { timeout: APP_READY_TIMEOUT_MS });
    port = Number(new URL(page.url()).port);
    // 站点已加载，但字体列表是异步拉的
    await waitForHome(page);
  } catch (error) {
    // 夹具 setup 失败时 Playwright 不会调 teardown，得自己收尾，别留个应用占着端口
    const tail = logTail(dataDir);
    const url = page.url();
    await app.close().catch(() => {});
    try {
      app.process()?.kill();
    } catch {
      // 已经退了
    }
    fs.rmSync(root, { recursive: true, force: true });
    throw new Error(
      `桌面版启动失败：等待 ${APP_READY_TIMEOUT_MS} ms 后窗口停在 ${url}\n` +
        `${error.message}\n后端日志末尾：\n${tail}`
    );
  }

  return {
    app,
    page,
    port,
    exe,
    dataDir,
    downloadsDir,
    logPath: path.join(dataDir, "backend-console.log"),
    url: `http://127.0.0.1:${port}`,
    async close() {
      // app.close() 没有超时，后端若在退出前崩掉、主进程弹了原生错误框，它会一直等下去 ——
      // 宁可超时后强杀，也不让整个 CI job 挂死在这儿
      await Promise.race([
        app.close().catch(() => {}),
        new Promise((resolve) => setTimeout(resolve, 20_000)),
      ]);
      try {
        app.process()?.kill();
      } catch {
        // 已经退了
      }
      try {
        fs.rmSync(root, { recursive: true, force: true });
      } catch {
        // 后端可能还占着 tasks.db，临时目录留着也无妨
      }
    },
  };
}

// 从 SPA 里重新进入首页：应用是 SPA，导航一次即可把上一个用例的表单状态清掉
async function resetHome(desktop) {
  await desktop.page.goto(desktop.url);
  await waitForHome(desktop.page);
}

// 等 Electron 真的把文件写下来。文件名用的是 Electron 解析出的 suggested filename，
// 所以「名字不对」也会在这里失败 —— 顺带把目录内容打出来，省得对着超时干瞪眼。
async function waitForDownload(desktop, filename, timeout = 120_000) {
  const file = path.join(desktop.downloadsDir, filename);
  const deadline = Date.now() + timeout;
  let lastSize = -1;
  for (;;) {
    if (fs.existsSync(file)) {
      const { size } = fs.statSync(file);
      // 连着两次大小一样才认，避免读到写了一半的文件
      if (size > 0 && size === lastSize) return file;
      lastSize = size;
    }
    if (Date.now() > deadline) {
      throw new Error(
        `等下载文件超时：${file}\n目录里现有：${fs.readdirSync(desktop.downloadsDir).join(", ") || "(空)"}`
      );
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
}

function httpRequest({ port, reqPath, method = "GET", headers = {}, timeout = 15_000 }) {
  return new Promise((resolve, reject) => {
    const req = http.request(
      { host: "127.0.0.1", port, path: reqPath, method, headers, timeout },
      (res) => {
        const chunks = [];
        res.on("data", (chunk) => chunks.push(chunk));
        res.on("end", () =>
          resolve({
            status: res.statusCode,
            headers: res.headers,
            body: Buffer.concat(chunks),
          })
        );
      }
    );
    req.on("timeout", () => req.destroy(new Error(`请求超时：${reqPath}`)));
    req.on("error", reject);
    req.end();
  });
}

// 关窗之后后端不能留下孤儿进程（Electron 的 before-quit 会杀它，
// 漏掉时还有 desktop_main.py 的父进程看门狗兜底）
async function waitForBackendDown(port, timeoutMs = 30_000) {
  const deadline = Date.now() + timeoutMs;
  for (;;) {
    try {
      await httpRequest({ port, reqPath: "/api/version", timeout: 3000 });
    } catch (error) {
      return true;
    }
    if (Date.now() > deadline) return false;
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
}

// 手搓一次 WebSocket 握手：只为看服务端给的状态行。
// 同源 → 101；被 Origin 校验拒绝 → uvicorn 在 accept 之前 close，按 ASGI 约定回 403。
function websocketHandshake({ port, reqPath, origin, timeout = 15_000 }) {
  return new Promise((resolve, reject) => {
    const socket = net.connect({ host: "127.0.0.1", port });
    let received = "";
    const done = (error) => {
      socket.destroy();
      error ? reject(error) : resolve(received);
    };

    socket.setTimeout(timeout);
    socket.on("timeout", () => done(new Error("WebSocket 握手超时")));
    socket.on("error", (error) => done(error));
    socket.on("connect", () => {
      const lines = [
        `GET ${reqPath} HTTP/1.1`,
        `Host: 127.0.0.1:${port}`,
        "Upgrade: websocket",
        "Connection: Upgrade",
        `Sec-WebSocket-Key: ${crypto.randomBytes(16).toString("base64")}`,
        "Sec-WebSocket-Version: 13",
      ];
      if (origin) lines.push(`Origin: ${origin}`);
      socket.write(`${lines.join("\r\n")}\r\n\r\n`);
    });
    socket.on("data", (chunk) => {
      received += chunk.toString("latin1");
      if (received.includes("\r\n")) done();
    });
  });
}

module.exports = {
  launchDesktopApp,
  resetHome,
  waitForDownload,
  httpRequest,
  waitForBackendDown,
  websocketHandshake,
  appExePath,
};
