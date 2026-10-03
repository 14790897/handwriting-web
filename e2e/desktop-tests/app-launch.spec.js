// 打包产物的启动路径：Electron 拉起后端 exe → 端口握手 → 同源加载站点。
// 这些是源码版 E2E 覆盖不到的集成路径（也是历史上翻过车的地方）。
const fs = require("fs");
const path = require("path");
const { test, expect } = require("./fixtures");
const { launchDesktopApp, resetHome, httpRequest, waitForBackendDown } = require("./launch");

const PACKAGED_VERSION = require(path.resolve(__dirname, "..", "..", "desktop", "package.json"))
  .version;

test.describe("桌面版启动与打包完整性", () => {
  test("窗口加载真实站点：字体来自打包资源，页脚版本号是打包版本", async ({ desktop }) => {
    await resetHome(desktop);

    // 字体文件是随包发的资源（FONT_ASSETS_BUNDLED_DIR），少了它们生成会直接失败
    const fonts = await httpRequest({ port: desktop.port, reqPath: "/api/fonts_info" });
    expect(fonts.status).toBe(200);
    const names = JSON.parse(fonts.body.toString("utf8"));
    expect(names.length).toBeGreaterThan(0);
    expect(names).toContain("云烟体.ttf");

    // 页脚显示的是 /api/version 的结果，链路是 app.getVersion() → 后端 → 前端
    await expect(desktop.page.getByTestId("app-version")).toContainText(PACKAGED_VERSION);
  });

  test("数据目录落在平台默认位置：握手端口与站点一致，sqlite 已初始化", async ({ desktop }) => {
    const content = async () => fs.readFileSync(desktop.logPath, "utf8");

    // 握手行是 Electron 从后端 stdout 解析出来的那一行，必须原样落进日志文件
    await expect
      .poll(async () => (await content()).match(/HANDWRITING_BACKEND (\{.*\})/)?.[1] ?? null, {
        timeout: 20_000,
      })
      .not.toBeNull();

    const payload = JSON.parse((await content()).match(/HANDWRITING_BACKEND (\{.*\})/)[1]);
    expect(payload.type).toBe("ready");
    expect(payload.port).toBe(desktop.port);

    // 打包后 __file__ 不可信，数据必须落到可写目录：任务队列与日志都在这里
    expect(fs.existsSync(path.join(desktop.dataDir, "tasks.db"))).toBe(true);
    expect(fs.existsSync(path.join(desktop.dataDir, "logs"))).toBe(true);
    expect(fs.existsSync(path.join(desktop.dataDir, "temp"))).toBe(true);
  });

  test("站点与静态资源由打包的 dist 提供（同源，无需跨域）", async ({ desktop }) => {
    const index = await httpRequest({ port: desktop.port, reqPath: "/" });
    expect(index.status).toBe(200);
    expect(index.headers["content-type"]).toContain("text/html");
    const html = index.body.toString("utf8");
    expect(html).toContain('<div id="app">');

    const assetPath = html.match(/src="(\/js\/[^"]+\.js)"/)?.[1];
    expect(assetPath, "首页 HTML 里没有引用打包后的 js").toBeTruthy();
    const asset = await httpRequest({ port: desktop.port, reqPath: assetPath });
    expect(asset.status).toBe(200);
    expect(asset.body.length).toBeGreaterThan(1000);
  });

  test("关窗后后端跟着退出，不留孤儿进程", async () => {
    const desktop = await launchDesktopApp();
    const { port } = desktop;
    await desktop.close();

    // Electron 退出时 kill 后端；漏掉时 desktop_main.py 的父进程看门狗每 3 秒兜一次
    expect(await waitForBackendDown(port)).toBe(true);
  });
});
