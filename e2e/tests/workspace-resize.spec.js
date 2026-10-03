const { test, expect, openHome } = require("./fixtures");

const settingsWidth = (page) =>
  page.getByTestId("panel-settings").evaluate((el) => Math.round(el.getBoundingClientRect().width));

const textWidth = (page) =>
  page.getByTestId("panel-text").evaluate((el) => Math.round(el.getBoundingClientRect().width));

// 分隔条的热区就是栏间那条 16px 轨道，从它的中心往左右拖
async function dragResizer(page, testId, dx) {
  const box = await page.getByTestId(testId).boundingBox();
  const x = box.x + box.width / 2;
  const y = box.y + box.height / 2;
  await page.mouse.move(x, y);
  await page.mouse.down();
  await page.mouse.move(x + dx, y, { steps: 8 });
  await page.mouse.up();
}

const savedColumns = (page) =>
  page.evaluate(() => JSON.parse(localStorage.getItem("workspaceColumns") || "null"));

test.describe("三栏宽度调整", () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await openHome(page);
  });

  test("拖动左分隔条加宽参数栏，并把两栏宽度写进 localStorage", async ({ page }) => {
    const before = await settingsWidth(page);
    await dragResizer(page, "resizer-settings", 120);

    expect(await settingsWidth(page)).toBeGreaterThan(before + 100);
    const saved = await savedColumns(page);
    expect(saved.left).toBeGreaterThan(before + 100);
    expect(saved.right).toBeGreaterThan(0);
  });

  test("拖动右分隔条加宽预览栏", async ({ page }) => {
    const previewWidth = () =>
      page.getByTestId("panel-preview").evaluate((el) => Math.round(el.getBoundingClientRect().width));
    const before = await previewWidth(page);

    await dragResizer(page, "resizer-preview", -120);

    expect(await previewWidth(page)).toBeGreaterThan(before + 100);
    expect((await savedColumns(page)).right).toBeGreaterThan(before + 100);
  });

  test("刷新后栏宽还在，双击分隔条恢复默认", async ({ page }) => {
    const defaultWidth = await settingsWidth(page);
    await dragResizer(page, "resizer-settings", 140);
    const widened = await settingsWidth(page);
    expect(widened).toBeGreaterThan(defaultWidth + 100);

    await page.reload();
    await expect(page.getByTestId("preview-btn")).toBeVisible();
    expect(await settingsWidth(page)).toBe(widened);

    await page.getByTestId("resizer-settings").dblclick();
    await expect.poll(() => settingsWidth(page)).toBe(defaultWidth);

    // 复位也要落盘：只改渲染不改存档的话，刷新就又变回拖动后的宽度
    await page.reload();
    await expect(page.getByTestId("preview-btn")).toBeVisible();
    expect(await settingsWidth(page)).toBe(defaultWidth);
  });

  test("两栏都不会把中栏挤到最小宽度以下，也不产生横向溢出", async ({ page }) => {
    // 中栏最小宽度是 300px，留 5px 给取整
    await dragResizer(page, "resizer-settings", 2000);
    expect(await textWidth(page)).toBeGreaterThanOrEqual(295);

    await dragResizer(page, "resizer-preview", -2000);
    expect(await textWidth(page)).toBeGreaterThanOrEqual(295);
    expect(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1)).toBe(false);
  });

  test("窗口变窄只压缩显示，重新变宽后还回用户拖出来的宽度", async ({ page }) => {
    await dragResizer(page, "resizer-settings", 160);
    const widened = await settingsWidth(page);

    await page.setViewportSize({ width: 1024, height: 768 });
    await expect.poll(() => settingsWidth(page)).toBeLessThan(widened);
    // 被压过的是渲染宽度，存的值不能被改小，否则用户在宽屏上拖出来的布局就没了
    expect((await savedColumns(page)).left).toBeGreaterThan(widened - 5);
    expect(await textWidth(page)).toBeGreaterThanOrEqual(295);

    await page.setViewportSize({ width: 1440, height: 900 });
    await expect.poll(() => settingsWidth(page)).toBe(widened);
  });

  test("收窄时一侧缩到 200px 下限，也不能把中栏挤到 300px 以下", async ({ page }) => {
    // 存档里一侧特别宽、另一侧按比例缩完会低于 200px 下限。
    // 直接把下限抬到 200 会让两边之和超出预算，得从较宽的一侧扣回来
    await page.evaluate(() =>
      localStorage.setItem("workspaceColumns", JSON.stringify({ left: 1000, right: 250 })),
    );
    await page.reload();
    await expect(page.getByTestId("preview-btn")).toBeVisible();

    await page.setViewportSize({ width: 1100, height: 800 });
    await expect.poll(() => textWidth(page)).toBeGreaterThanOrEqual(295);
    expect(await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth + 1)).toBe(false);
    expect(await settingsWidth(page)).toBeGreaterThanOrEqual(200);
  });

  test("窄屏单栏堆叠时分隔条不出现", async ({ page }) => {
    await page.setViewportSize({ width: 820, height: 1180 });
    await expect(page.getByTestId("resizer-settings")).toBeHidden();
    await expect(page.getByTestId("resizer-preview")).toBeHidden();
  });
});
