import "bootstrap/dist/css/bootstrap.css";
import "bootstrap/dist/js/bootstrap.js";
import "bootstrap";
import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import store from "./store";
import i18n from "./i18n";
import axios from "axios";

import * as Sentry from "@sentry/vue";

const app = createApp(App);



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

app.use(store);
app.use(router);
app.use(i18n);

app.config.globalProperties.$http = axios;
// const http = axios.create({
//   baseURL: "https://testhand.liuweiqing.top",
// });

// app.config.globalProperties.$http = http;

app.mount("#app");
