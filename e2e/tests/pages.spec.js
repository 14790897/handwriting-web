const { test, expect, openHome } = require("./fixtures");

test.describe("静态页面与导航", () => {
  test("首页底部显示当前版本号", async ({ page }) => {
    await openHome(page);

    // 版本号来自后端 /api/version（发版时由 scripts/sync-version.js 写进 backend/VERSION）
    await expect(page.getByTestId("app-version")).toHaveText(/^v\d+\.\d+\.\d+$/);
  });

  test("功能介绍页可访问", async ({ page }) => {
    await page.goto("/Introduce");

    await expect(page).toHaveURL(/\/Introduce$/);
    await expect(page.getByRole("heading", { name: "手写文字生成网站" })).toBeVisible();
  });

  test("关于页可访问", async ({ page }) => {
    await page.goto("/About");

    await expect(page.getByText("About View")).toBeVisible();
  });

  test("反馈页表单可填写", async ({ page }) => {
    await page.goto("/Feedback");

    await expect(page.locator("#email")).toBeVisible();
    await page.locator("#feedback").fill("这是一条端到端测试反馈");
    await expect(page.locator("#feedback")).toHaveValue("这是一条端到端测试反馈");
  });
});
