import { createRouter, createWebHistory } from "vue-router";
import Home from "../views/HomeView.vue";
import Login from "../views/UserLogin.vue";
import Register from "../views/UserRegister.vue";
import UserFeedback from "@/components/UserFeedback"; // 导入Feedback组件
import IntroduceComponent from "@/components/Introduce"; // 导入Introduce组件

const routes = [
  {
    path: "/",
    name: "Home",
    component: Home,
  },
  {
    path: "/About",
    name: "About",
    // route level code-splitting
    // this generates a separate chunk (about.[hash].js) for this route
    // which is lazy-loaded when the route is visited.
    component: () =>
      import(/* webpackChunkName: "about" */ "../views/AboutView.vue"),
  },
  {
    path: "/Login",
    name: "Login",
    component: Login,
  },
  {
    path: "/Register",
    name: "Register",
    component: Register,
  },
  {
    path: "/Feedback",
    name: "Feedback",
    component: UserFeedback,
  },
  {
    path: "/Introduce",
    name: "Introduce",
    component: IntroduceComponent,
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
