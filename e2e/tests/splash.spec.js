const { test, expect } = require("@playwright/test");
const { blockThirdParty } = require("./fixtures");

// 唯一不禁用启动动画的用例：从干净 localStorage 进入，验证首屏动画会自己消失
test("首屏翻书动画自动消失后露出表单", async ({ page }) => {
  await blockThirdParty(page);

  await page.goto("/");
  const splash = page.getByTestId("book-splash");
  await expect(splash).toBeVisible();
  await expect(splash).toBeHidden({ timeout: 15_000 });
  await expect(page.getByTestId("preview-btn")).toBeVisible();
});
