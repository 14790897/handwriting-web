// 桌面版的跨站防护：本地后端监听 127.0.0.1，任何网页都能给它发请求，
// 同源策略只挡「读响应」不挡「发请求」，所以 Origin/Referer 校验必须真的生效
// （见 AGENTS.md「桌面版安全与编码」）。
const { test, expect } = require("./fixtures");
const { resetHome, httpRequest, websocketHandshake } = require("./launch");

const FOREIGN_ORIGIN = "http://evil.example";

test.describe("桌面版本地后端的跨站防护", () => {
  test("不带来源的请求（本机工具）放行，外站 Origin 被 403 拒绝", async ({ desktop }) => {
    const plain = await httpRequest({ port: desktop.port, reqPath: "/api/version" });
    expect(plain.status).toBe(200);

    const foreign = await httpRequest({
      port: desktop.port,
      reqPath: "/api/generate_handwriting",
      method: "POST",
      headers: { Origin: FOREIGN_ORIGIN },
    });
    expect(foreign.status).toBe(403);
    expect(JSON.parse(foreign.body.toString("utf8")).message).toBe("跨站请求被拒绝");
  });

  test("本站来源放行，伪造 Sec-Fetch-Site: cross-site 也被拒", async ({ desktop }) => {
    const sameOrigin = await httpRequest({
      port: desktop.port,
      reqPath: "/api/version",
      headers: { Origin: desktop.url },
    });
    expect(sameOrigin.status).toBe(200);

    // 浏览器发跨站请求时会带 Sec-Fetch-Site，伪造 Origin 也躲不过这条
    const crossSite = await httpRequest({
      port: desktop.port,
      reqPath: "/api/version",
      headers: { "Sec-Fetch-Site": "cross-site", Origin: FOREIGN_ORIGIN },
    });
    expect(crossSite.status).toBe(403);
  });

  test("WebSocket 不走中间件，同样按来源拒绝握手", async ({ desktop }) => {
    const wsPath = "/api/generate_handwriting/ws/not-a-real-task";

    const allowed = await websocketHandshake({
      port: desktop.port,
      reqPath: wsPath,
      origin: desktop.url,
    });
    expect(allowed.split("\r\n")[0]).toContain("101");

    // accept 之前 close → ASGI 约定回 403，绝不能给 101
    const foreign = await websocketHandshake({
      port: desktop.port,
      reqPath: wsPath,
      origin: FOREIGN_ORIGIN,
    });
    expect(foreign.split("\r\n")[0]).not.toContain("101");
    expect(foreign.split("\r\n")[0]).toContain("403");
  });

  test("页面本身能正常调接口（防护没有误伤同源请求）", async ({ desktop }) => {
    await resetHome(desktop);
    const result = await desktop.page.evaluate(async (url) => {
      const response = await fetch(`${url}/api/fonts_info`);
      return { status: response.status, count: (await response.json()).length };
    }, desktop.url);
    expect(result.status).toBe(200);
    expect(result.count).toBeGreaterThan(0);
  });
});
