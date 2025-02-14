import "bootstrap/dist/css/bootstrap.css";
import "bootstrap/dist/js/bootstrap.js";
import "bootstrap";
import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import store from "./store";
import i18n from "./i18n";
import axios from "axios";
import Clarity from "@microsoft/clarity";

import * as Sentry from "@sentry/vue";

// import Viewer from "v-viewer";
// import "viewerjs/dist/viewer.css";

const app = createApp(App);

// 异步加载Google Analytics的JavaScript库
const script = document.createElement("script");
script.async = true;
script.src = "https://www.googletagmanager.com/gtag/js?id=G-GB1XG89B6Z";
document.head.appendChild(script);

// 当脚本加载完成后进行初始化
script.onload = () => {
  const projectId = "ounxp8da5s";
  Clarity.init(projectId);
  console.log("Clarity已经加载");
  // 初始化window.dataLayer数组
  window.dataLayer = window.dataLayer || [];

  // 定义gtag函数
  function gtag() {
    window.dataLayer.push(arguments);
  }

  // 调用gtag函数进行配置
  gtag("js", new Date());
  gtag("config", "G-GB1XG89B6Z");

  // (function (c, l, a, r, i, t, y) {
  //   c[a] =
  //     c[a] ||
  //     function () {
  //       (c[a].q = c[a].q || []).push(arguments);
  //     };
  //   t = l.createElement(r);
  //   t.async = 1;
  //   t.src = "https://www.clarity.ms/tag/" + i;
  //   y = l.getElementsByTagName(r)[0];
  //   y.parentNode.insertBefore(t, y);
  // })(window, document, "clarity", "script", "ounxp8da5s");
};

Sentry.init({
  app,
  dsn: "https://507b601bbd374cf58b7c5468cb434578@o4505255803551744.ingest.sentry.io/4505485557891072",
  integrations: [
    new Sentry.BrowserTracing({
      // Set `tracePropagationTargets` to control for which URLs distributed tracing should be enabled
      tracePropagationTargets: ["localhost", /^https:\/\/yourserver\.io\/api/],
      routingInstrumentation: Sentry.vueRouterInstrumentation(router),
    }),
    new Sentry.Replay(),
  ],
  // Performance Monitoring
  tracesSampleRate: 1.0, // Capture 100% of the transactions, reduce in production!
  // Session Replay
  replaysSessionSampleRate: 0.1, // This sets the sample rate at 10%. You may want to change it to 100% while in development and then sample at a lower rate in production.
  replaysOnErrorSampleRate: 1.0, // If you're not already sampling the entire session, change the sample rate to 100% when sampling sessions where errors occur.
});

// const DEFAULT_TITLE = "handwrite";

// router.afterEach((to) => {
//   app.nextTick(() => {
//     document.title = to.meta.title || DEFAULT_TITLE;
//   });
// });

app.use(store);
app.use(router);
app.use(i18n);

app.config.globalProperties.$http = axios;
// const http = axios.create({
//   baseURL: "https://testhand.liuweiqing.top",
// });

// app.config.globalProperties.$http = http;

// app.use(Viewer);

app.mount("#app");
