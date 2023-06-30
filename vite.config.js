// vite.config.js
export default {
    server: {
      proxy: {
        '/api': {
          target: 'https://testhand.liuweiqing.top',
          changeOrigin: true,
        },
      }
    }
  }
  