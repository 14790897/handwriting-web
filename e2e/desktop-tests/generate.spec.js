// 用户在打包版里真正会走的流程：输入文字 → 生成 → 下载。
// 断言口径与源码版 e2e/tests/home-generate.spec.js 保持一致，区别只在跑的是打包产物。
const fs = require("fs");
const path = require("path");
const { test, expect } = require("./fixtures");
const { resetHome, waitForDownload } = require("./launch");
const {
  fillText,
  setNumber,
  useSmallCanvas,
  expectPreviewImageLoaded,
} = require("../tests/fixtures");

test.describe("打包版的手写生成主流程（真实渲染）", () => {
  test("预览：输入文字后返回真实手写图片", async ({ desktop }) => {
    await resetHome(desktop);
    const { page } = desktop;
    await useSmallCanvas(page);
    await fillText(page, "你好世界");

    await page.getByTestId("preview-btn").click();

    await expectPreviewImageLoaded(page);
  });

  test("生成图片：下载的 zip 是真实压缩包", async ({ desktop }) => {
    await resetHome(desktop);
    const { page } = desktop;
    await useSmallCanvas(page);
    await fillText(page, "测试");

    await page.getByTestId("generate-image-btn").click();

    // 文件名也在这条断言里：waitForDownload 找的就是 images.zip
    const buffer = fs.readFileSync(await waitForDownload(desktop, "images.zip"));
    expect(buffer.subarray(0, 2).toString("latin1")).toBe("PK");
    expect(buffer.length).toBeGreaterThan(1000);
  });

  test("生成 PDF：直接拿到 PDF，体积落在导出预算内", async ({ desktop }) => {
    await resetHome(desktop);
    const { page } = desktop;
    await useSmallCanvas(page, { fontSize: 32, lineSpacing: 45 });
    await fillText(page, "静夜思床前明月光疑是地上霜举头望明月低头思故乡春眠不觉晓");

    await page.getByTestId("generate-pdf-btn").click();

    const buffer = fs.readFileSync(await waitForDownload(desktop, "images.pdf"));
    expect(buffer.subarray(0, 5).toString("latin1")).toBe("%PDF-");
    // 预算与源码版一致（见 e2e/tests/home-generate.spec.js）：真实体积约 20 KB 且带随机
    // 抖动，质量回到 95 会涨到约 27 KB —— 卡在 24 KB 才既稳又能拦住那个回归
    expect(buffer.length).toBeLessThan(24_000);
    expect(buffer.length).toBeGreaterThan(1000);

    await expect(page.getByTestId("pdf-download-bytes")).toHaveText(String(buffer.length));
  });

  test("上传文本文件转文字后生成（走打包内的解析依赖）", async ({ desktop }) => {
    await resetHome(desktop);
    const { page } = desktop;
    await useSmallCanvas(page);

    await page
      .getByTestId("text-file-input")
      .setInputFiles(path.join(__dirname, "..", "fixtures", "sample-letter.txt"));

    await expect(page.getByTestId("text-input")).toHaveValue(
      /这是一份用于端到端测试的文本文件。/
    );
    await expect(page.getByTestId("text-file-name")).toHaveText("sample-letter.txt");

    await page.getByTestId("preview-btn").click();

    await expectPreviewImageLoaded(page);
  });
});
