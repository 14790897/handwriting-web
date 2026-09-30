// 桌面版（打包产物）专属配置：驱动 desktop/build/installer/win-unpacked/ 里的真实
// Electron 应用，没有 webServer、不启浏览器，所以本地要先把桌面版构建出来：
//   bash desktop/build.sh --app-only     # 或完整构建 bash desktop/build.sh
//   cd e2e && npm run test:desktop
// 源码版（前后端 dev server）用的是 playwright.config.js，两者互不影响。
const { defineConfig } = require("@playwright/test");

module.exports = defineConfig({
  testDir: "./desktop-tests",
  // 后端冷启动 + 真实渲染，单用例最长给到 3 分钟
  timeout: 180_000,
  expect: { timeout: 20_000 },
  fullyParallel: false,
  // 同一时间只跑一个打包应用：起一个实例要十几秒，且都抢 57610-57709 这批端口
  workers: 1,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: [["list"], ["html", { outputFolder: "desktop-tests/.report", open: "never" }]],
  outputDir: "desktop-tests/.results",
  use: {
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
});
