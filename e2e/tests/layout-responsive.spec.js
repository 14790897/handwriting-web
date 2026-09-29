const { test, expect, openHome, fillText, useSmallCanvas, expectPreviewImageLoaded } = require("./fixtures");

const layoutMetrics = (page) =>
  page.evaluate(() => {
    const panels = [...document.querySelectorAll(".panel")];
    return {
      columns: getComputedStyle(document.querySelector(".workspace")).gridTemplateColumns.split(" ").length,
      pageScrolls: document.documentElement.scrollHeight > window.innerHeight + 1,
      horizontalOverflow: document.documentElement.scrollWidth > window.innerWidth + 1,
      panelHeights: panels.map((el) => Math.round(el.getBoundingClientRect().height)),
      footerBottom: Math.round(document.querySelector("footer").getBoundingClientRect().bottom),
      viewportHeight: window.innerHeight,
      headerPosition: getComputedStyle(document.querySelector(".app-header")).position,
      headerTop: Math.round(document.querySelector(".app-header").getBoundingClientRect().top),
    };
  });

test.describe("响应式布局", () => {
  test("桌面视口：三栏等高、整页不滚动、页脚留在视口内", async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await openHome(page);

    const metrics = await layoutMetrics(page);
    expect(metrics.columns).toBe(3);
    expect(metrics.pageScrolls).toBe(false);
    expect(metrics.horizontalOverflow).toBe(false);
    expect(new Set(metrics.panelHeights).size).toBe(1);
    expect(metrics.footerBottom).toBeLessThanOrEqual(metrics.viewportHeight);
  });

  test("顶栏出现提示条时，三栏让出高度而不是把整页撑出滚动条", async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await openHome(page);
    const headerSelector = ".app-header";
    const headerHeight = () =>
      page.locator(headerSelector).evaluate((el) => Math.round(el.getBoundingClientRect().height));
    const headerBefore = await headerHeight();

    await useSmallCanvas(page);
    await fillText(page, "高度测试");
    await page.getByTestId("preview-btn").click();
    await expectPreviewImageLoaded(page);

    // 生成完成后顶栏会多出一条提示，顶栏变高
    await expect(page.getByTestId("message-info")).toBeVisible();
    const headerAfter = await headerHeight();
    const metrics = await layoutMetrics(page);
    expect(headerAfter).toBeGreaterThan(headerBefore);
    expect(metrics.pageScrolls).toBe(false);
    expect(metrics.footerBottom).toBeLessThanOrEqual(metrics.viewportHeight);
  });

  test("窄屏视口：单栏堆叠、顶栏不吸顶、页面恢复整页滚动", async ({ page }) => {
    await page.setViewportSize({ width: 820, height: 1180 });
    await openHome(page);

    const metrics = await layoutMetrics(page);
    expect(metrics.columns).toBe(1);
    expect(metrics.pageScrolls).toBe(true);
    expect(metrics.horizontalOverflow).toBe(false);
    expect(metrics.headerPosition).toBe("static");

    // 滚动后顶栏随页面上移，不再长期遮住内容
    await page.evaluate(() => window.scrollTo(0, 600));
    await page.waitForTimeout(200);
    expect((await layoutMetrics(page)).headerTop).toBeLessThan(0);
  });

  test("窄屏视口：toast 落在屏幕下半区，不盖住顶栏按钮", async ({ page }) => {
    await page.setViewportSize({ width: 820, height: 1180 });
    await openHome(page);

    await page.getByTestId("text-input").fill("");
    await page.getByTestId("letter-format-btn").click();

    const toast = page.locator(".swal2-toast");
    await expect(toast).toBeVisible();
    const box = await toast.boundingBox();
    expect(box.y).toBeGreaterThan(1180 / 2);
  });
});
