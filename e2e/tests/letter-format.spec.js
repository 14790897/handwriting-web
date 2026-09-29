const { test, expect, openHome, fillText } = require("./fixtures");

test.describe("书信排版", () => {
  const body = "亲爱的妈妈：\n\n最近一切都好，学习也顺利。\n\n祝您身体健康！";

  test("应用排版后自动缩进、落款右对齐，撤销可完整还原", async ({ page }) => {
    await openHome(page);
    await fillText(page, body);

    await page.getByTestId("letter-format-btn").click();
    await expect(page.getByTestId("letter-dialog")).toBeVisible();
    await page.getByTestId("letter-signature-input").fill("小明");
    await page.getByTestId("letter-date-input").fill("2026年9月29日");
    await page.getByTestId("letter-apply-btn").click();

    await expect(page.getByTestId("letter-dialog")).toBeHidden();
    const formatted = await page.getByTestId("text-input").inputValue();
    expect(formatted.startsWith("亲爱的妈妈：")).toBe(true);
    expect(formatted).toContain("　　最近一切都好，学习也顺利。");
    expect(formatted).toContain(">>>小明");
    expect(formatted).toContain(">>>2026年9月29日");

    await page.getByTestId("letter-undo-btn").click();
    await expect(page.getByTestId("text-input")).toHaveValue(body);
  });

  test("正文为空时点击书信排版给出提示，不打开弹窗", async ({ page }) => {
    await openHome(page);

    await page.getByTestId("letter-format-btn").click();

    await expect(page.getByText(/请先输入/)).toBeVisible();
    await expect(page.getByTestId("letter-dialog")).toBeHidden();
  });

  test("取消排版不改动正文", async ({ page }) => {
    await openHome(page);
    await fillText(page, body);

    await page.getByTestId("letter-format-btn").click();
    await expect(page.getByTestId("letter-dialog")).toBeVisible();
    await page.getByTestId("letter-cancel-btn").click();

    await expect(page.getByTestId("letter-dialog")).toBeHidden();
    await expect(page.getByTestId("text-input")).toHaveValue(body);
    await expect(page.getByTestId("letter-undo-btn")).toBeHidden();
  });
});
