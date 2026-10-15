// 桌面版（Electron）判定：前端只有一份构建产物，靠 UA 区分，
// 线上站点行为不受影响。用于关掉第三方统计/客服/上报等在离线环境下
// 只会拖慢启动的脚本。
export const isDesktop = () =>
  typeof navigator !== "undefined" && navigator.userAgent.includes("Electron");

// 主进程通过 preload 暴露的桥（见 desktop/preload.js）。桌面版的下载是 Electron 自己
// 落盘的，只有它能告诉我们文件存到了哪个绝对路径；网页版拿不到。
export const hasDesktopBridge = () =>
  typeof window !== "undefined" && Boolean(window.handwritingDesktop?.onDownloadFinished);

export default isDesktop;
