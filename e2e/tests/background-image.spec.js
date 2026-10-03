const path = require("path");
const { test, expect, openHome } = require("./fixtures");

// 样例图是合成的规整横线条，见 backend/tests/test_identify.py 里的同名生成逻辑：
// 左右边距 60、上边距 80、行距 70。下边距量的是「最后一条线到页面底部」，
// 比绘制的 80 多出一截（行距摆不整齐，最后一行停在 858，余下 142）。
//
// 这里按后端单测同样的 ±4px 容差核对具体数值，而不是只要求「是正数」——
// 这条链路走的是真实上传接口（落盘 → identify_distance → 清理），
// 能盖住单测直接调函数时跳过的那一段。
const SAMPLE_PAGE = path.join(__dirname, "..", "fixtures", "sample-page.png");
const FIXTURE_MARGINS = {
  marginLeft: 60,
  marginRight: 60,
  marginTop: 80,
  marginBottom: 142,
  // 行距量的是行到行，不是单个笔画的粗细：样例图每行是一整条 8px 横线，过 Canny
  // 后上下两条边缘只差 9px，以前返回的就是这个 9
  lineSpacing: 70,
};
const TOLERANCE_PX = 4;

test.describe("背景图片与边距识别", () => {
  test("上传图片确认识别后，把四个边距与行距回填进参数框", async ({ page }) => {
    await openHome(page);
    await page.getByTestId("line-spacing-input").fill("60");
    const spacingBeforeUpload = 60;

    const responsePromise = page.waitForResponse(
      (response) =>
        response.url().includes("/api/imagefileprocess") &&
        response.request().method() === "POST"
    );

    await page.getByTestId("background-image-input").setInputFiles(SAMPLE_PAGE);

    // 上传后先问「要不要自动识别页面的四周边距」，点确定才会真的发请求
    const confirm = page.getByRole("button", { name: "确定" });
    await expect(confirm).toBeVisible();
    await confirm.click();

    const response = await responsePromise;
    expect(response.status()).toBe(200);
    const margins = await response.json();

    for (const [field, expected] of Object.entries(FIXTURE_MARGINS)) {
      expect(typeof margins[field], `${field} 应当是数字`).toBe("number");
      expect(
        Math.abs(margins[field] - expected),
        `${field} 识别成 ${margins[field]}，偏离合成图的 ${expected} 超过 ${TOLERANCE_PX}px`
      ).toBeLessThanOrEqual(TOLERANCE_PX);
    }

    const inputValue = async (testId) => Number(await page.getByTestId(testId).inputValue());
    expect(await inputValue("margin-left-input")).toBe(margins.marginLeft);
    expect(await inputValue("margin-right-input")).toBe(margins.marginRight);
    expect(await inputValue("margin-bottom-input")).toBe(margins.marginBottom);
    expect(await inputValue("line-spacing-input")).toBe(margins.lineSpacing);
    // 上边距特殊：前端拿识别值减去**上传前**的行距（此时 lineSpacing 还没被覆盖）
    expect(await inputValue("margin-top-input")).toBe(margins.marginTop - spacingBeforeUpload);

    await expect(page.getByTestId("message-info")).toContainText("背景图片已加载。");

    // 背景图生效后尺寸交给图片决定，宽高输入框禁用（isBackgroundImageSpecified）
    await expect(page.getByTestId("width-input")).toBeDisabled();
    await expect(page.getByTestId("height-input")).toBeDisabled();
  });
});
