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

  test("生成 PDF：下载 pdf 且文件头正确", async ({ page }) => {
    await openHome(page);
    await useSmallCanvas(page);
    await fillText(page, "测试");

    const downloadPromise = page.waitForEvent("download", { timeout: 120_000 });
    await page.getByTestId("generate-pdf-btn").click();
    const download = await downloadPromise;

    expect(download.suggestedFilename()).toBe("images.pdf");
    const buffer = fs.readFileSync(await download.path());
    expect(buffer.subarray(0, 5).toString("latin1")).toBe("%PDF-");
    expect(buffer.length).toBeGreaterThan(1000);
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
