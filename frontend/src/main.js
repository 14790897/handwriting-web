import "bootstrap/dist/css/bootstrap.css";
import "bootstrap";
import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import store from "./store";
import i18n from "./i18n";
import axios from "axios";
import axiosRetry from "axios-retry";
// eslint-disable-next-line no-unused-vars
import Swal from "sweetalert2";
import { createHead } from "@vueuse/head";

// import Viewer from "v-viewer";H
// import "viewerjs/dist/viewer.css";

const app = createApp(App);
const head = createHead();

const initThirdPartyServices = async () => {
  if (process.env.NODE_ENV !== "production") return;

  const script = document.createElement("script");
  script.async = true;
  script.src = "https://www.googletagmanager.com/gtag/js?id=G-GB1XG89B6Z";
  document.head.appendChild(script);

  script.onload = async () => {
    const { default: Clarity } = await import("@microsoft/clarity");
    Clarity.init("ounxp8da5s");
    window.dataLayer = window.dataLayer || [];

    function gtag() {
      window.dataLayer.push(arguments);
    }

    gtag("js", new Date());
    gtag("config", "G-GB1XG89B6Z");

    (function (c, l, a, r, i, t, y) {
      c[a] =
        c[a] ||
        function () {
          (c[a].q = c[a].q || []).push(arguments);
        };
      t = l.createElement(r);
      t.async = 1;
      t.src = "https://www.clarity.ms/tag/" + i;
      y = l.getElementsByTagName(r)[0];
      y.parentNode.insertBefore(t, y);
    })(window, document, "clarity", "script", "ounxp8da5s");
  };

  const chatwootScript = document.createElement("script");
  chatwootScript.async = true;
  chatwootScript.defer = true;
  chatwootScript.src = "https://chatwoot.14790897.xyz/packs/js/sdk.js";
  chatwootScript.onload = () => {
    if (window.chatwootSDK) {
      window.chatwootSDK.run({
        websiteToken: "LqgSJHw9boXsan69qwxSs8eg",
        baseUrl: "https://chatwoot.14790897.xyz",
      });
    }
  };
  document.head.appendChild(chatwootScript);

  const Sentry = await import("@sentry/vue");
  Sentry.init({
    app,
    dsn: "https://507b601bbd374cf58b7c5468cb434578@o4505255803551744.ingest.sentry.io/4505485557891072",
    integrations: [
      new Sentry.BrowserTracing({
        tracePropagationTargets: ["localhost", /^https:\/\/yourserver\.io\/api/],
        routingInstrumentation: Sentry.vueRouterInstrumentation(router),
      }),
      new Sentry.Replay(),
    ],
    tracesSampleRate: 1.0,
    replaysSessionSampleRate: 0.1,
    replaysOnErrorSampleRate: 1.0,
  });
};

// const DEFAULT_TITLE = "handwrite";

// router.afterEach((to) => {
//   app.nextTick(() => {
//     document.title = to.meta.title || DEFAULT_TITLE;
//   });
// });

app.use(store);
app.use(router);
app.use(i18n);
app.use(head);

// 配置自动重试：网络错误 或 5xx 响应自动重试，最多 3 次，指数退避
axiosRetry(axios, {
  retries: 3,
  retryDelay: axiosRetry.exponentialDelay, // 1s → 2s → 4s
  retryCondition: (error) => {
    // 503 queue_full 是业务状态，不需要重试
    if (
      error.response?.status === 503 &&
      error.response?.data?.status === "queue_full"
    ) {
      return false;
    }
    // 网络错误 或 5xx 服务端错误时重试
    return (
      axiosRetry.isNetworkError(error) ||
      axiosRetry.isRetryableError(error)
    );
  },
  onRetry: (retryCount, error) => {
    console.warn(`请求重试第 ${retryCount} 次，原因：${error.message}`);
  },
});

app.config.globalProperties.$http = axios;
app.config.globalProperties.$swal = Swal;
// const http = axios.create({
//   baseURL: "https://testhand.liuweiqing.top",
// });

// app.config.globalProperties.$http = http;

// app.use(Viewer);

app.mount("#app");

window.addEventListener("load", () => {
  if ("requestIdleCallback" in window) {
    window.requestIdleCallback(() => {
      void initThirdPartyServices();
    });
    return;
  }
  setTimeout(() => {
    void initThirdPartyServices();
  }, 0);
});

// Service Worker 版本更新提示
if ("serviceWorker" in navigator) {
  window.addEventListener("load", async () => {
    try {
      // 注销旧版 /sw.js
      const registrations = await navigator.serviceWorker.getRegistrations();
      for (const reg of registrations) {
        if (reg.active?.scriptURL?.includes("sw.js")) {
          await reg.unregister();
        }
      }

      // 监听新版本激活，提示用户刷新
      navigator.serviceWorker.addEventListener("controllerchange", () => {
        if (confirm("网站已更新到新版本，点击确定刷新页面以加载最新内容。")) {
          window.location.reload();
        }
      });
    } catch (error) {
      console.error("[SW] 初始化失败:", error);
    }
  });
}
