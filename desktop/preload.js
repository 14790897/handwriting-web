// 渲染进程与主进程之间唯一的桥。contextIsolation 开着，站点页面拿不到任何 Node/Electron
// API，只能调这里明确暴露的两个方法：
//   onDownloadFinished(cb) —— 主进程把「下载完成，文件在这个绝对路径」推给页面
//   revealLastDownload()   —— 让系统文件管理器打开最后那次下载（路径由主进程记着，
//                             不从页面传路径过来，免得给 shell 开了个任意路径的入口）
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("handwritingDesktop", {
  onDownloadFinished: (callback) => {
    ipcRenderer.on("download:finished", (event, payload) => callback(payload));
  },
  revealLastDownload: () => ipcRenderer.send("download:reveal"),
});
