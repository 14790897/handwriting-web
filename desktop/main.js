// Electron 主进程：拉起打包好的后端 exe，等它就绪后开窗加载本地站点。
const { app, BrowserWindow, Menu, dialog, shell } = require("electron");
const { spawn } = require("child_process");
const fs = require("fs");
const http = require("http");
const path = require("path");

// PyInstaller 只在 Windows 上给可执行文件加 .exe 后缀，macOS 上没有
const BACKEND_EXE =
  process.platform === "win32" ? "handwriting-backend.exe" : "handwriting-backend";
const READY_TIMEOUT_MS = 90 * 1000;

let backendProcess = null;
let mainWindow = null;
let shuttingDown = false;

function backendDir() {
  if (app.isPackaged) {
    return path.join(process.resourcesPath, "backend");
  }
  return path.join(__dirname, "build", "backend", "handwriting-backend");
}

function dataDir() {
  // 故意不用 Electron 默认的 userData：Windows 上要避开会被漫游同步的 Roaming，
  // macOS 上则直接用约定的 ~/Library/Application Support。两边都从环境变量取基目录，
  // 这样 E2E 改一个变量就能把整个数据目录挪进临时目录（见 e2e/desktop-tests/launch.js）。
  if (process.platform === "darwin") {
    const home = process.env.HOME || app.getPath("home");
    return path.join(home, "Library", "Application Support", "HandwritingWeb");
  }
  const base = process.env.LOCALAPPDATA || app.getPath("userData");
  return path.join(base, "HandwritingWeb");
}

function startBackend() {
  const exe = path.join(backendDir(), BACKEND_EXE);
  if (!fs.existsSync(exe)) {
    throw new Error(`找不到后端程序：${exe}\n请先运行 desktop/build.sh 构建后端。`);
  }

  const dir = dataDir();
  fs.mkdirSync(dir, { recursive: true });
  const logStream = fs.createWriteStream(path.join(dir, "backend-console.log"), {
    flags: "a",
  });
  logStream.write(`\n===== ${new Date().toISOString()} 启动后端 =====\n`);

  // windowsHide 抑制控制台窗口（只对 Windows 有效，其它平台忽略），但 stdout 管道
  // 仍然可用（端口握手靠它）。stdin 直接忽略：后端改成轮询父进程 PID 来判断 Electron
  // 是否还在，不再需要 stdin（在无控制台的 frozen 进程里阻塞读 stdin 会让它卡死）。
  const child = spawn(exe, [], {
    cwd: dir,
    windowsHide: true,
    env: {
      ...process.env,
      HANDWRITING_DATA_DIR: dir,
      HANDWRITING_PARENT_PID: String(process.pid),
      // 页面上要显示的版本号：用安装的这个版本，而不是构建时写死的
      HANDWRITING_APP_VERSION: app.getVersion(),
      // Windows 上 Python 的管道/文件默认走 ANSI 代码页，中文日志会抛
      // UnicodeEncodeError 或写成乱码；强制整个解释器用 UTF-8（macOS 本来就
      // 是 UTF-8，这三个变量在那边只是无操作）
      PYTHONUTF8: "1",
      PYTHONIOENCODING: "utf-8",
      PYTHONUNBUFFERED: "1",
    },
    stdio: ["ignore", "pipe", "pipe"],
  });

  let port = null;
  const portWaiters = [];
  let failWaiter = null;

  const handleLine = (line) => {
    logStream.write(`${line}\n`);
    const marker = line.indexOf("HANDWRITING_BACKEND ");
    if (marker === -1) return;
    try {
      const payload = JSON.parse(line.slice(marker + "HANDWRITING_BACKEND ".length));
      if (payload.type === "ready" && payload.port) {
        port = payload.port;
        portWaiters.splice(0).forEach((resolve) => resolve(port));
      }
    } catch {
      // 非握手行，忽略
    }
  };

  const pipeLines = (stream) => {
    let buffer = "";
    stream.setEncoding("utf8");
    stream.on("data", (chunk) => {
      buffer += chunk;
      let index;
      while ((index = buffer.indexOf("\n")) !== -1) {
        handleLine(buffer.slice(0, index));
        buffer = buffer.slice(index + 1);
      }
    });
    stream.on("end", () => buffer && handleLine(buffer));
  };
  pipeLines(child.stdout);
  pipeLines(child.stderr);

  // 没有这个 handler 的话启动失败（EACCES 等）会变成主进程的未捕获异常
  child.on("error", (error) => {
    logStream.write(`===== 后端启动失败: ${error.message} =====\n`);
    backendProcess = null;
    failWaiter?.(new Error(`无法启动后端进程：${error.message}`));
  });

  child.on("exit", (code) => {
    logStream.write(`===== 后端退出，code=${code} =====\n`);
    backendProcess = null;
    failWaiter?.(new Error(`后端进程已退出（code=${code}）`));
    if (!shuttingDown && mainWindow) {
      dialog.showErrorBox("后端已停止", `后端进程意外退出（code=${code}）。\n日志：${path.join(dir, "backend-console.log")}`);
      app.quit();
    }
  });

  backendProcess = child;

  return new Promise((resolve, reject) => {
    if (port) return resolve(port);
    const timer = setTimeout(() => {
      failWaiter = null;
      reject(new Error("后端启动超时"));
    }, READY_TIMEOUT_MS);
    failWaiter = (error) => {
      clearTimeout(timer);
      failWaiter = null;
      reject(error);
    };
    portWaiters.push((value) => {
      clearTimeout(timer);
      failWaiter = null;
      resolve(value);
    });
  });
}

function waitForHttp(port) {
  const deadline = Date.now() + READY_TIMEOUT_MS;
  return new Promise((resolve, reject) => {
    const attempt = () => {
      const req = http.get(
        { host: "127.0.0.1", port, path: "/api/fonts_info", timeout: 3000 },
        (res) => {
          res.resume();
          if (res.statusCode === 200) return resolve();
          retry();
        }
      );
      req.on("error", retry);
      req.on("timeout", () => req.destroy());
    };
    const retry = () => {
      if (Date.now() > deadline) return reject(new Error("后端就绪探测超时"));
      setTimeout(attempt, 300);
    };
    attempt();
  });
}

function openExternal(url) {
  if (/^https?:\/\//i.test(url)) shell.openExternal(url);
}

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1280,
    height: 900,
    minWidth: 900,
    minHeight: 600,
    backgroundColor: "#ffffff",
    autoHideMenuBar: true,
    show: false,
    title: "手写体生成器",
    webPreferences: {
      contextIsolation: true,
      nodeIntegration: false,
      spellcheck: false,
    },
  });

  mainWindow.once("ready-to-show", () => mainWindow.show());

  // 站内链接留在窗口里，站外链接交给系统浏览器
  mainWindow.webContents.setWindowOpenHandler(({ url }) => {
    openExternal(url);
    return { action: "deny" };
  });
  mainWindow.webContents.on("will-navigate", (event, url) => {
    let hostname = null;
    try {
      hostname = new URL(url).hostname;
    } catch {
      return;
    }
    if (hostname !== "127.0.0.1" && hostname !== "localhost") {
      event.preventDefault();
      openExternal(url);
    }
  });

  mainWindow.on("closed", () => {
    mainWindow = null;
  });
}

function buildMenu() {
  const template = [];

  if (process.platform === "darwin") {
    // macOS 的第一个子菜单永远是应用菜单（名称取自 app.name），系统不给它补默认项，
    // 所以隐藏/退出要自己列出来，否则 Cmd+H / Cmd+Q 都是死的。
    // 这里不挂 role: "appMenu"，因为它的「关于」只是 Electron 自带的版本框 ——
    // 下面「帮助」里的那个还会显示数据目录，留一个就够。
    template.push({
      label: app.name,
      submenu: [
        { role: "hide" },
        { role: "hideOthers" },
        { role: "unhide" },
        { type: "separator" },
        { role: "quit" },
      ],
    });
    // 编辑菜单同样不能省：macOS 的 Cmd+C/V/A/Z 是走菜单 role 分发的，
    // 没有这一栏，输入框里连复制粘贴都不响应。
    template.push({
      label: "编辑",
      submenu: [
        { role: "undo" },
        { role: "redo" },
        { type: "separator" },
        { role: "cut" },
        { role: "copy" },
        { role: "paste" },
        { role: "selectAll" },
      ],
    });
  }

  template.push(
    {
      label: "视图",
      submenu: [
        { role: "reload" },
        { role: "forceReload" },
        { role: "toggleDevTools" },
        { type: "separator" },
        { role: "resetZoom" },
        { role: "zoomIn" },
        { role: "zoomOut" },
        { type: "separator" },
        { role: "togglefullscreen" },
      ],
    },
    {
      label: "帮助",
      submenu: [
        {
          label: "打开数据目录",
          click: () => shell.openPath(dataDir()),
        },
        {
          label: "关于",
          click: () =>
            dialog.showMessageBox({
              type: "info",
              title: "关于",
              message: "手写体生成器 桌面版",
              detail: `版本 ${app.getVersion()}\n数据目录：${dataDir()}`,
            }),
        },
      ],
    }
  );

  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

function stopBackend() {
  if (!backendProcess) return;
  shuttingDown = true;
  const pid = backendProcess.pid;
  backendProcess = null;
  try {
    process.kill(pid);
  } catch {
    // 已退出
  }
}

if (!app.requestSingleInstanceLock()) {
  app.quit();
} else {
  app.on("second-instance", () => {
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore();
      mainWindow.focus();
    }
  });

  app.whenReady().then(async () => {
    createWindow();
    buildMenu();
    // 后端启动要几秒（PyInstaller 引导 + fastapi 等基础依赖载入），先给个等待页
    // 而不是白屏。opencv/sklearn/PyMuPDF 那些重家伙已经不在启动路径上了 ——
    // 见 backend/app.py 顶部的说明，它们改成了按需导入。
    await mainWindow.loadFile(path.join(__dirname, "splash.html"));

    try {
      const port = await startBackend();
      await waitForHttp(port);
      // 站点从同一端口提供，保持同源，前端无需任何跨域配置
      if (mainWindow) {
        await mainWindow.loadURL(`http://127.0.0.1:${port}/`);
      }
    } catch (error) {
      const detail = `${error.message}\n\n后端日志：${path.join(dataDir(), "backend-console.log")}`;
      if (mainWindow) {
        await mainWindow.webContents.executeJavaScript(
          `window.showError(${JSON.stringify(detail)})`
        );
      }
    }
  });

  app.on("window-all-closed", () => app.quit());
  app.on("will-quit", stopBackend);
  app.on("before-quit", stopBackend);
}
