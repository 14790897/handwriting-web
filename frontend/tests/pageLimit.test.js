const assert = require("assert").strict;

const tests = [];
function test(name, run) {
  tests.push({ name, run });
}

const pageLimitModule = import("../src/utils/pageLimit.mjs");

test("生产站上限是 10 页", async () => {
  const { MAX_PAGES } = await pageLimitModule;

  assert.equal(MAX_PAGES, 10);
});

test("只有超过上限才需要弹窗", async () => {
  const { MAX_PAGES, exceedsPageLimit } = await pageLimitModule;

  assert.equal(exceedsPageLimit(1), false);
  assert.equal(exceedsPageLimit(MAX_PAGES), false);
  assert.equal(exceedsPageLimit(MAX_PAGES + 1), true);
});

test("弹窗文案提到的页数和实际截断用的是同一个上限", async () => {
  const { MAX_PAGES, buildPageLimitDialog } = await pageLimitModule;
  const dialog = buildPageLimitDialog(30);
  const copy = [dialog.html, dialog.confirmText, dialog.fallbackConfirmText].join("\n");

  // 文案里凡是写死页数的地方，都必须等于 MAX_PAGES，
  // 否则又会出现「说好 10 页、实际给 15 页」那种不一致（issue #72）。
  // 「检测到您的文本预计会生成 N 页」里的 N 是用户文本长度、不是上限，先摘掉再扫描。
  const withoutEstimate = copy.replace(/预计会生成\s*\d+\s*页/g, "");
  const mentioned = [...withoutEstimate.matchAll(/(\d+)\s*页/g)].map((m) => Number(m[1]));

  assert.ok(mentioned.length > 0, "弹窗文案里应当提到上限页数");
  for (const pages of mentioned) {
    assert.equal(pages, MAX_PAGES, `文案写的是 ${pages} 页，实际截断是 ${MAX_PAGES} 页`);
  }

  assert.match(dialog.confirmText, new RegExp(`前${MAX_PAGES}页`));
});

(async () => {
  for (const { name, run } of tests) {
    await run();
    console.log(`✓ ${name}`);
  }
  console.log(`${tests.length} tests passed`);
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
