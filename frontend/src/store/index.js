// store.js
import { createStore } from "vuex";

export default createStore({
  state: {
    login_delete_message: false,
  },
  mutations: {
    login_delete_message_update(state, value) {
      state.login_delete_message = value;
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
