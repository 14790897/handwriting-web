// 桌面版 E2E 的公共夹具：一个 worker 启动一次真实打包应用，文件内所有用例共用。
// 冷启动要十几秒，每个用例各起一次太贵；用例开头调 resetHome() 重新导航即可清状态。
const { test: base, expect } = require("@playwright/test");
const { launchDesktopApp } = require("./launch");

const test = base.extend({
  desktop: [
    async ({}, use) => {
      const desktop = await launchDesktopApp();
      await use(desktop);
      await desktop.close();
    },
    { scope: "worker" },
  ],
});

module.exports = { test, expect };
