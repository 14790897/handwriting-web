const { defineConfig } = require("@vue/cli-service");
module.exports = defineConfig({
  transpileDependencies: true,
});
// vue.config.js
module.exports = {
  devServer: {
    proxy: {
      '/api': {
        target: 'https://testhand.liuweiqing.top',//https://testhand.liuweiqing.top/http://127.0.0.1:5000
        changeOrigin: true,
      },
    },
  },
};
