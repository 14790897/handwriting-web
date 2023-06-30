import "bootstrap/dist/css/bootstrap.css";
import "bootstrap/dist/js/bootstrap.js";
import "bootstrap";
import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
import store from "./store";
import i18n from "./i18n";
import axios from "axios";

const app = createApp(App);

app.use(store);
app.use(router);
app.use(i18n);

app.config.globalProperties.$http = axios;
// const http = axios.create({
//   baseURL: "https://testhand.liuweiqing.top",
// });

// app.config.globalProperties.$http = http;

app.mount("#app");
