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
      runtimeCaching: [
        // StaleWhileRevalidate - 返回缓存同时更新（适用于静态资源）
        {
          urlPattern: /\.(js|css|woff2?)$/,
          handler: "StaleWhileRevalidate",
          options: {
            cacheName: "static-resources",
            cacheableResponse: { statuses: [0, 200] },
          },
        },
        // CacheFirst - 缓存优先（适用于图片等不常变更的资源）
        {
          urlPattern: /\.(png|jpg|jpeg|gif|svg|ico|webp)$/,
          handler: "CacheFirst",
          options: {
            cacheName: "image-cache",
            expiration: {
              maxEntries: 100,
              maxAgeSeconds: 30 * 24 * 60 * 60, // 30 天
            },
            cacheableResponse: { statuses: [0, 200] },
          },
        },
      ],
    },
  },
});
