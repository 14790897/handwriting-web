import { createRouter, createWebHistory } from "vue-router";
import Home from "../views/HomeView.vue";
import Login from "../views/UserLogin.vue";
import Register from "../views/UserRegister.vue";

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
];

const router = createRouter({
  history: createWebHistory(process.env.BASE_URL),
  routes,
});

export default router;
