const {
  test,
  expect,
  openHome,
  fillText,
  useSmallCanvas,
  expectPreviewImageLoaded,
} = require("./fixtures");

// 生成任务的状态走 WebSocket 推送；连不上时前端会静默降级成轮询（HomeView 的
// waitForTaskViaWebSocket catch 里调 pollGenerationTask），两条路径出图效果一样，
// 所以降级平时看不出来 —— 直到并发上来、轮询把任务状态接口打爆。
// 这里盯的就是「真的用了推送」，以及推送的帧里带齐了状态字段。
test.describe("任务状态 WebSocket 推送", () => {
  test("生成过程走 WebSocket，收到 completed 帧且没有降级为轮询", async ({ page }) => {
    const frames = [];
    const socketUrls = [];
    const polledTaskStatus = [];

    page.on("websocket", (socket) => {
      if (!socket.url().includes("/api/generate_handwriting/ws/")) return;
      socketUrls.push(socket.url());
      socket.on("framereceived", (frame) => {
        try {
          frames.push(JSON.parse(frame.payload));
        } catch (error) {
          // 非 JSON 帧（例如关闭原因）与断言无关
          void error;
        }
      });
    });

    // 降级路径靠轮询 /task/<id> 拿状态；注意别把收结果的 /task/<id>/result 算进来
    page.on("request", (request) => {
      if (/\/api\/generate_handwriting\/task\/[^/]+$/.test(request.url())) {
        polledTaskStatus.push(request.url());
      }
    });

    await openHome(page);
    await useSmallCanvas(page);
    await fillText(page, "推送测试");
    await page.getByTestId("preview-btn").click();
    await expectPreviewImageLoaded(page);

    // 没连上 WS 就是降级了（比如 dev server 的 /api 代理漏了 ws: true）
    expect(socketUrls, "生成任务没有建立 WebSocket 连接，说明走了轮询降级").not.toHaveLength(0);
    expect(polledTaskStatus, "出现了轮询请求，说明 WebSocket 降级了").toHaveLength(0);

    // 帧事件经 CDP 异步投递，可能比预览渲染晚一步才到，所以轮询等它稳定，
    // 不要在这之后立刻读一次 frames —— 那会偶发地「没收到 completed 帧」
    await expect
      .poll(() => frames.filter((frame) => frame.task_status === "completed").length, {
        message: `没收到 completed 帧，收到的状态：${JSON.stringify(frames)}`,
      })
      .toBeGreaterThan(0);
    const completed = frames.filter((frame) => frame.task_status === "completed");

    // 状态帧是前端排队文案的全部来源，字段缺了界面上就会少提示
    for (const field of ["task_id", "task_stage", "task_message", "task_progress"]) {
      expect(completed[0]).toHaveProperty(field);
    }
  });
});
