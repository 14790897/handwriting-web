const path = require("path");
const { pathToFileURL } = require("url");
const { test, expect } = require("@playwright/test");

// 页数上限是纯前端逻辑，不需要浏览器。放在 e2e/tests/ 是因为
// frontend/tests/ 不在任何 CI workflow 里被执行（已有的 test:letter-format 也一样）。
const MODULE_URL = pathToFileURL(
  path.resolve(__dirname, "../../frontend/src/utils/pageLimit.mjs")
).href;

const loadPageLimit = () => import(MODULE_URL);

test.describe("生产站页数上限", () => {
  test("上限是 10 页", async () => {
    const { MAX_PAGES } = await loadPageLimit();

    expect(MAX_PAGES).toBe(10);
  });

  test("只有超过上限才需要弹窗", async () => {
    const { MAX_PAGES, exceedsPageLimit } = await loadPageLimit();

    expect(exceedsPageLimit(1)).toBe(false);
    expect(exceedsPageLimit(MAX_PAGES)).toBe(false);
    expect(exceedsPageLimit(MAX_PAGES + 1)).toBe(true);
  });

  test("弹窗文案提到的页数和实际截断用的是同一个上限", async () => {
    const { MAX_PAGES, buildPageLimitDialog } = await loadPageLimit();
    const dialog = buildPageLimitDialog(30);
    const copy = [dialog.html, dialog.confirmText, dialog.fallbackConfirmText].join("\n");

    // 文案里凡是写死页数的地方，都必须等于 MAX_PAGES，
    // 否则又会出现「说好 10 页、实际给 15 页」那种不一致（issue #72）。
    // 「检测到您的文本预计会生成 N 页」里的 N 是用户文本长度、不是上限，先摘掉再扫描。
    const withoutEstimate = copy.replace(/预计会生成\s*\d+\s*页/g, "");
    const mentioned = [...withoutEstimate.matchAll(/(\d+)\s*页/g)].map((m) => Number(m[1]));

    expect(mentioned.length).toBeGreaterThan(0);
    for (const pages of mentioned) {
      expect(pages, `文案写的是 ${pages} 页，实际截断是 ${MAX_PAGES} 页`).toBe(MAX_PAGES);
    }

    expect(dialog.confirmText).toContain(`前${MAX_PAGES}页`);
  });
});
