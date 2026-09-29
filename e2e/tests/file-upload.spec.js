const path = require("path");
const { test, expect, openHome } = require("./fixtures");

test.describe("文本文件上传", () => {
  test("上传 txt 后自动填充正文并显示文件名", async ({ page }) => {
    await openHome(page);

    await page
      .getByTestId("text-file-input")
      .setInputFiles(path.join(__dirname, "..", "fixtures", "sample-letter.txt"));

    await expect(page.getByTestId("text-input")).toHaveValue(/这是一份用于端到端测试的文本文件。/);
    await expect(page.getByTestId("text-file-name")).toHaveText("sample-letter.txt");
  });
});
