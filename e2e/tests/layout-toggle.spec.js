const { test, expect, openHome, fillText, useSmallCanvas, expectPreviewImageLoaded } = require("./fixtures");

test.describe("新旧版布局切换", () => {
  test("默认新版三栏，切到旧版后正文字样保留，刷新后仍停在旧版", async ({ page }) => {
    await openHome(page);
    await expect(page.locator(".workspace")).toBeVisible();
    await expect(page.locator(".legacy-root")).toHaveCount(0);

    await fillText(page, "布局切换测试");
    await page.getByTestId("layout-toggle-btn").click();

    await expect(page.locator(".legacy-root")).toBeVisible();
    await expect(page.locator(".workspace")).toHaveCount(0);
    await expect(page.getByTestId("text-input")).toHaveValue("布局切换测试");
    await expect(page.getByTestId("font-select")).toBeVisible();
    await expect(page.getByTestId("preview-btn")).toBeVisible();

    await page.reload();
    await expect(page.locator(".legacy-root")).toBeVisible();
    await expect(page.getByTestId("text-input")).toHaveValue("布局切换测试");

    await page.getByTestId("layout-toggle-btn").click();
    await expect(page.locator(".workspace")).toBeVisible();
    await expect(page.locator(".legacy-root")).toHaveCount(0);
  });

  test("切到旧版后依然能生成预览", async ({ page }) => {
    await openHome(page);
    await page.getByTestId("layout-toggle-btn").click();
    await expect(page.locator(".legacy-root")).toBeVisible();

    await useSmallCanvas(page);
    await fillText(page, "旧版生成测试");
    await page.getByTestId("preview-btn").click();

    await expectPreviewImageLoaded(page);
  });
});
