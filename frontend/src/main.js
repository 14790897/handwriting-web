import "bootstrap/dist/css/bootstrap.css";
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

import * as Sentry from "@sentry/vue";

import { isDesktop } from "./desktop";

// import Viewer from "v-viewer";H
// import "viewerjs/dist/viewer.css";

const app = createApp(App);
const head = createHead();

// 桌面版不加载第三方统计/客服/错误上报：离线环境下它们只会拖慢启动，
// 还会把用户本地产生的错误混进线上项目的报表里
const thirdPartyEnabled = !isDesktop();

// 异步加载Google Analytics的JavaScript库
function initAnalytics() {
  const script = document.createElement("script");
  script.async = true;
  script.src = "https://www.googletagmanager.com/gtag/js?id=G-GB1XG89B6Z";
  document.head.appendChild(script);

  // 当脚本加载完成后进行初始化
  script.onload = () => {
    // 初始化window.dataLayer数组
    window.dataLayer = window.dataLayer || [];

    // 定义gtag函数
    function gtag() {
      window.dataLayer.push(arguments);
    }

    // 调用gtag函数进行配置
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
}

function initChatwoot() {
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
}

function initSentry() {
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
    replaysSessionSampleRate: 0.1, // This sets the sample rate to 10%. You may want to change it to 100% while in development and then sample at a lower rate in production.
    replaysOnErrorSampleRate: 1.0, // If you're not already sampling the entire session, change the sample rate to 100% when sampling sessions where errors occur.
  });
}

// Sentry 必须在 app.mount() 之前初始化：SDK 在这一步接管 Vue 的 errorHandler、
// 装上路由 instrumentation 与 window 级错误监听，晚于挂载就丢掉启动阶段和首次渲染的报错
if (thirdPartyEnabled) {
  initSentry();
}

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

// 注销历史遗留的 /sw.js：现在的构建已经不注册 Service Worker，
// 这里只负责把老访客浏览器里那份清掉（unregister 本身不会触发 controllerchange）
const unregisterLegacyServiceWorker = async () => {
  try {
    const registrations = await navigator.serviceWorker.getRegistrations();
    for (const reg of registrations) {
      if (reg.active?.scriptURL?.includes("sw.js")) {
        await reg.unregister();
      }
    }
  } catch (error) {
    console.error("[SW] 注销旧版失败:", error);
  }
};

// GA / Clarity / Chatwoot 不参与首屏渲染，等 load 之后的空闲时段再加载
function initDeferredThirdParty() {
  initAnalytics();
  initChatwoot();
}

function onWindowLoad() {
  if (thirdPartyEnabled) {
    // timeout 兜底：页面一直繁忙时 requestIdleCallback 可能迟迟不触发
    if ("requestIdleCallback" in window) {
      window.requestIdleCallback(initDeferredThirdParty, { timeout: 3000 });
    } else {
      setTimeout(initDeferredThirdParty, 150);
    }
  }

  if ("serviceWorker" in navigator) {
    unregisterLegacyServiceWorker();
  }
}

// bundle 若在 load 之后才执行（异步注入、页面从 bfcache 恢复），load 事件不会再触发
if (document.readyState === "complete") {
  onWindowLoad();
} else {
  window.addEventListener("load", onWindowLoad);
}
