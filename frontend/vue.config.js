const { defineConfig } = require("@vue/cli-service");

module.exports = defineConfig({
  transpileDependencies: true,
  devServer: {
    host: "localhost", // 或者使用 '0.0.0.0'
    port: 8080,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:5005",
        changeOrigin: true,
      },
    },
  },
  pages: {
    index: {
      // entry for the page
      entry: "src/main.js",
      // the source template
      template: "public/index.html",
      // output as dist/index.html
      filename: "index.html",
      // when using title option,
      // template title tag needs to be <title><%= htmlWebpackPlugin.options.title %></title>
      title: "handwrite 手写文字生成",
    },
  },
  filenameHashing: process.env.NODE_ENV === "production",
  pwa: {
    name: "handwrite 手写文字生成",
    themeColor: "#4fc08d",
    msTileColor: "#000000",
    workboxPluginMode: "GenerateSW",
    workboxOptions: {
      skipWaiting: true,
      clientsClaim: true,
      // 清理旧版 precache 缓存
      cleanupOutdatedCaches: true,
      // 静态资源（JS/CSS/字体/图片）由 precache 自动管理版本，不需要 runtimeCaching
      runtimeCaching: [
        // API - 网络优先，离线时回退缓存
        {
          urlPattern: /\/api\//,
          handler: "NetworkFirst",
          options: {
            cacheName: "api-cache",
            cacheableResponse: { statuses: [0, 200] },
            networkTimeoutSeconds: 10,
          },
        },
      ],
    },
  },
});
