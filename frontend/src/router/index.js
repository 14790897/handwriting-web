import { createRouter, createWebHistory } from "vue-router";
import Home from "../views/HomeView.vue";
import Login from "../views/UserLogin.vue";
import Register from "../views/UserRegister.vue";
import UserFeedback from "@/components/UserFeedback";
import IntroduceComponent from "@/components/Introduce";

const routes = [
  {
    path: "/",
    name: "Home",
    component: Home,
    meta: {
      title: "手写文字生成网站 - 在线生成手写图片与 PDF",
      description:
        "手写文字生成网站，支持多种字体和背景，在线生成高质量手写文字图片与 PDF。适合作业、论文、信件等场景，支持自定义字体、背景与参数调节。",
      robots: "index, follow",
    },
  },
  {
    path: "/About",
    name: "About",
    component: () => import("../views/AboutView.vue"),
    meta: {
      title: "关于 - 手写文字生成网站",
      description: "关于本网站与功能介绍、使用方法及隐私说明。",
      robots: "index, follow",
    },
  },
  {
    path: "/Login",
    name: "Login",
    component: Login,
    meta: {
      title: "登录 - 手写文字生成网站",
      description: "登录您的账户以使用更多功能。",
      robots: "noindex, nofollow",
    },
  },
  {
    path: "/Register",
    name: "Register",
    component: Register,
    meta: {
      title: "注册 - 手写文字生成网站",
      description: "注册账户，开始生成个性化手写图片与 PDF。",
      robots: "noindex, nofollow",
    },
  },
  {
    path: "/Feedback",
    name: "Feedback",
    component: UserFeedback,
    meta: {
      title: "用户反馈 - 手写文字生成网站",
      description: "提交您的意见与建议，帮助我们改进产品。",
      robots: "index, follow",
    },
  },
  {
    path: "/Introduce",
    name: "Introduce",
    component: IntroduceComponent,
    meta: {
      title: "功能介绍 - 手写文字生成网站",
      description: "了解网站核心功能、参数配置与使用技巧。",
      robots: "index, follow",
    },
  },
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

router.afterEach(() => {
  const routerViewElement = document.querySelector("router-view");
  if (routerViewElement) {
    routerViewElement.scrollIntoView({ behavior: "smooth", block: "start" });
  }
});

export default router;

