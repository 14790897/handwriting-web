const path = require("path");
const { test, expect, openHome } = require("./fixtures");

// 样例图是合成的规整横线条（边距 60/60/80、行距 70），见 backend/tests/test_identify.py
// 里的同名生成逻辑。这里只用它触发真实识别，期望值全部取自响应本身 ——
// opencv-python 没钉版本，写死 60/80 会被版本差异随机翻车。
const SAMPLE_PAGE = path.join(__dirname, "..", "fixtures", "sample-page.png");

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

    // 识别结果应当是有意义的正数；具体数值随 opencv 版本浮动，所以只做区间检查
    for (const field of ["marginLeft", "marginRight", "marginTop", "marginBottom", "lineSpacing"]) {
      expect(typeof margins[field], `${field} 应当是数字`).toBe("number");
      expect(margins[field], `${field} 应当为正`).toBeGreaterThan(0);
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
