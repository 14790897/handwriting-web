// 桌面版（Electron）判定：前端只有一份构建产物，靠 UA 区分，
// 线上站点行为不受影响。用于关掉第三方统计/客服/上报等在离线环境下
// 只会拖慢启动的脚本。
export const isDesktop = () =>
  typeof navigator !== "undefined" && navigator.userAgent.includes("Electron");

export default isDesktop;
