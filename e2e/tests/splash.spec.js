const { test, expect } = require("@playwright/test");
const { blockThirdParty } = require("./fixtures");

// 唯一不禁用启动动画的用例：从干净 localStorage 进入，验证首屏动画会自己消失。
// goto 等到 load 时，1.5 秒的遮罩可能已经播完并从 DOM 移除，直接断言可见性会变成
// 「看加载速度」的假失败，所以用 MutationObserver 记录它是否真的出现过
test("首屏翻书动画自动消失后露出表单", async ({ page }) => {
  await blockThirdParty(page);
  await page.addInitScript(() => {
    window.__splashSeen = false;
    const mark = () => {
      if (document.querySelector('[data-testid="book-splash"]')) {
        window.__splashSeen = true;
      }
    };
    document.addEventListener("DOMContentLoaded", () => {
      mark();
      new MutationObserver(mark).observe(document.documentElement, {
        childList: true,
        subtree: true,
      });
    });
  });

  await page.goto("/");

  const splash = page.getByTestId("book-splash");
  await expect(splash).toBeHidden({ timeout: 15_000 });
  await expect(page.getByTestId("preview-btn")).toBeVisible();
  expect(await page.evaluate(() => window.__splashSeen)).toBe(true);
});
