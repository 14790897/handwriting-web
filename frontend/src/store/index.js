// store.js
import { createStore } from "vuex";

export default createStore({
  state: {
    login_delete_message: false,
  },
  mutations: {
    login_delete_message_update(state) {
      state.login_delete_message = true;
    },
  },
  actions: {
    increment(context) {
      context.commit("increment");
    },
  },
  getters: {
    login_delete_message: (state) => state.login_delete_message,
  },
});
