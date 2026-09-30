const fs = require("fs");
const { test, expect, openHome, fillText, setNumber, useSmallCanvas, expectPreviewImageLoaded } = require("./fixtures");

test.describe("手写生成主流程（真实后端渲染）", () => {
  test("预览：输入文字后返回真实手写图片", async ({ page }) => {
    await openHome(page);
    await useSmallCanvas(page);
    await fillText(page, "你好世界");

    await page.getByTestId("preview-btn").click();

    await expectPreviewImageLoaded(page);
  });

  test("生成完整手写图片：下载 zip 且内容是真实压缩包", async ({ page }) => {
    await openHome(page);
    await useSmallCanvas(page);
    await fillText(page, "测试");

    const downloadPromise = page.waitForEvent("download", { timeout: 120_000 });
    await page.getByTestId("generate-image-btn").click();
    const download = await downloadPromise;

    expect(download.suggestedFilename()).toBe("images.zip");
    const buffer = fs.readFileSync(await download.path());
    expect(buffer.subarray(0, 2).toString("latin1")).toBe("PK");
    expect(buffer.length).toBeGreaterThan(1000);
  });

  test("生成 PDF：下载的是 PDF 本身，且体积落在导出预算内", async ({ page }) => {
    await openHome(page);
    await useSmallCanvas(page, { fontSize: 32, lineSpacing: 45 });
    // 24 个字在 400x300 画布上固定在单页内，体积才可比
    await fillText(page, "静夜思床前明月光疑是地上霜举头望明月低头思故乡春眠不觉晓");

    const downloadPromise = page.waitForEvent("download", { timeout: 120_000 });
    await page.getByTestId("generate-pdf-btn").click();
    const download = await downloadPromise;

    // 用户拿到的必须能直接打开：不是包着 PDF 的 zip
    expect(download.suggestedFilename()).toBe("images.pdf");
    const buffer = fs.readFileSync(await download.path());
    expect(buffer.subarray(0, 5).toString("latin1")).toBe("%PDF-");

    // PDF 体积决定下载耗时：同一页按质量 95 导出约 27 KB，回到高质就会顶破这条线。
    // 手写渲染本身带随机扰动，同样的输入压出来会有几百字节的抖动（CI 实测 19.9-20.4 KB），
    // 贴着 20 KB 卡会随机翻车，所以留出余量 —— 但仍要远低于 27 KB 才算没回归。
    expect(buffer.length).toBeLessThan(24_000);
    expect(buffer.length).toBeGreaterThan(1000);

    // 前端收到的字节数要和落盘大小一致，顺带确认走的是 pdf 分支
    await expect(page.getByTestId("pdf-download-bytes")).toHaveText(String(buffer.length));
  });

  test("字号大于行距时前端直接拦截，不会发出请求", async ({ page }) => {
    await openHome(page);
    await fillText(page, "测试");
    await setNumber(page, "font-size-input", 200);
    await setNumber(page, "line-spacing-input", 100);

    let requested = false;
    await page.route("**/api/generate_handwriting", (route) => {
      requested = true;
      return route.abort();
    });

    await page.getByTestId("preview-btn").click();

    await expect(page.getByText("字体大小不能大于行间距")).toBeVisible();
    expect(requested).toBe(false);
  });
});
