const { test, expect, openHome, fillText, useSmallCanvas } = require("./fixtures");

// 这些分支真实后端很难触发（要凑满 8 个排队任务 / 制造 5xx），用路由拦截模拟
test.describe("异常分支（mock 后端响应）", () => {
  test("队列满 503：显示等待倒计时并禁用生成按钮", async ({ page }) => {
    await openHome(page);
    await fillText(page, "排队测试");
    await page.route("**/api/generate_handwriting", (route) =>
      route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({
          status: "queue_full",
          message: "当前服务器队列已满，请稍后再试",
          active_task_count: 8,
          max_active_tasks: 8,
          estimated_wait_seconds: 5,
        }),
      })
    );

    await page.getByTestId("preview-btn").click();

    await expect(page.getByText("服务器繁忙，队列已满，预计 5 秒后可重试")).toBeVisible();
    await expect(page.getByTestId("preview-btn")).toBeDisabled();
    await expect(page.getByTestId("generate-image-btn")).toBeDisabled();
  });

  test("后端 400：把服务端 message 提示给用户", async ({ page }) => {
    await openHome(page);
    await fillText(page, "错误测试");
    await page.route("**/api/generate_handwriting", (route) =>
      route.fulfill({
        status: 400,
        contentType: "application/json",
        body: JSON.stringify({ status: "fail", message: "手写文本不能为空" }),
      })
    );

    await page.getByTestId("preview-btn").click();

    await expect(page.getByText("手写文本不能为空")).toBeVisible();
    await expect(page.getByTestId("preview-btn")).toBeEnabled();
  });

  test("提交给后端的表单字段符合接口契约", async ({ page }) => {
    await openHome(page);
    await useSmallCanvas(page);
    await fillText(page, "契约测试");

    let multipartBody = "";
    await page.route("**/api/generate_handwriting", async (route) => {
      multipartBody = (await route.request().postDataBuffer()).toString("utf8");
      await route.fulfill({
        status: 400,
        contentType: "application/json",
        body: JSON.stringify({ status: "fail", message: "已拦截" }),
      });
    });

    await page.getByTestId("preview-btn").click();
    await expect(page.getByText("已拦截")).toBeVisible();

    for (const field of [
      "text",
      "font_size",
      "line_spacing",
      "font_option",
      "preview",
      "pdf_save",
      "width",
      "height",
      "full_preview",
      "background_image",
    ]) {
      expect(multipartBody).toContain(`name="${field}"`);
    }
    expect(multipartBody).toContain("契约测试");
    expect(multipartBody).toContain("name=\"preview\"\r\n\r\ntrue");
  });
});
