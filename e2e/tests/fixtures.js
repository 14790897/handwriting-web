const { test: base, expect } = require("@playwright/test");

const SPLASH_FLAG = "bookSplashShown";

// 第三方脚本（GA / Clarity / Sentry / Chatwoot）与测试无关，会拖慢首屏并污染真实监控数据
async function blockThirdParty(page) {
  await page.route(/^https?:\/\/(?!127\.0\.0\.1|localhost)/, (route) => route.abort());
}

const test = base.extend({
  context: async ({ context }, use) => {
    // 首屏翻书动画会在 1.5 秒内盖住整页，预置标记直接跳过
    await context.addInitScript(() => {
      try {
        window.localStorage.setItem("bookSplashShown", "1");
      } catch (error) {
        void error;
      }
    });
    await use(context);
  },
  page: async ({ page }, use) => {
    await blockThirdParty(page);
    await use(page);
  },
});

// 打开首页并等字体列表就绪（生成请求要靠它取 font_option，没加载完就点会报错）
async function openHome(page) {
  await page.goto("/");
  await expect(page.getByTestId("preview-btn")).toBeVisible();
  await expect(page.getByTestId("font-select").locator("option")).not.toHaveCount(0);
}

async function fillText(page, text) {
  await page.getByTestId("text-input").fill(text);
}

async function setNumber(page, testId, value) {
  await page.getByTestId(testId).fill(String(value));
}

// 小画布 + 短文本，真实渲染约 2 秒
async function useSmallCanvas(page, { fontSize = 50, lineSpacing = 60 } = {}) {
  await setNumber(page, "width-input", 400);
  await setNumber(page, "height-input", 300);
  await setNumber(page, "font-size-input", fontSize);
  await setNumber(page, "line-spacing-input", lineSpacing);
  await setNumber(page, "margin-top-input", 20);
  await setNumber(page, "margin-bottom-input", 20);
  await setNumber(page, "margin-left-input", 20);
  await setNumber(page, "margin-right-input", 20);
}

// 等真实生成的结果图渲染出来（blob: 是接口返回的 png，默认图是 /default1.webp）
async function expectPreviewImageLoaded(page, timeout = 90_000) {
  await expect(page.getByTestId("message-info")).toContainText("预览图像已加载", { timeout });
  const image = page.getByTestId("preview-image");
  await expect(image).toHaveAttribute("src", /^(blob:|data:image\/png)/);
  await expect
    .poll(() => image.evaluate((el) => el.naturalWidth), { timeout: 30_000 })
    .toBeGreaterThan(0);
}

module.exports = { test, expect, blockThirdParty, openHome, fillText, setNumber, useSmallCanvas, expectPreviewImageLoaded };
