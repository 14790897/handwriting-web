<template>
  <div>
    <nav class="navbar navbar-expand-lg navbar-light bg-light mb-3">
      <router-link class="navbar-brand" to="/">Home</router-link>
      <button class="navbar-toggler" type="button" @click="isNavOpen = !isNavOpen">
        <span class="navbar-toggler-icon"></span>
      </button>
      <div class="collapse navbar-collapse" :class="{ show: isNavOpen }" id="navbarNav">
        <ul class="navbar-nav mr-auto">
          <li class="nav-item">
            <router-link class="nav-link" to="/Login">Login</router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/Register">Register</router-link>
          </li>
        </ul>
        <ul class="navbar-nav">
          <li class="nav-item dropdown">
            <a class="nav-link dropdown-toggle" href="#" id="navbarDropdown" role="button" data-toggle="dropdown"
              aria-haspopup="true" aria-expanded="false">
              <i class="fa fa-user"></i> {{ getUsername }}
            </a>
            <div class="dropdown-menu" aria-labelledby="navbarDropdown">
              <a class="dropdown-item" href="#">Profile</a>
              <a class="dropdown-item" href="#">Logout</a>
            </div>
          </li>
        </ul>
        <select v-model="selectedLanguage" class="custom-select ml-3 mr-3">
          <option v-for="lang in languages" :key="lang.code" :value="lang.code">{{ lang.name }}</option>
        </select>
        <button class="btn btn-primary ml-auto" @click="isModalOpen = true">Register/Login</button>
      </div>
    </nav>
    <div v-if="isModalOpen" class="d-flex align-items-center justify-content-center vh-100">
      <!-- Add the following div as a modal overlay -->
      <div v-if="isModalOpen" class="modal-overlay" @click.self="isModalOpen = false">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">Modal</h5>
              <button type="button" class="close" @click="isModalOpen = false">
                <span aria-hidden="true">&times;</span>
              </button>
            </div>
            <div class="modal-body flex-grow-1">
              <ul class="nav nav-tabs">
                <li class="nav-item">
                  <a :class="{ 'nav-link': true, active: currentView === 'UserRegister' }" href="#"
                    @click.prevent="changeView('UserRegister')">Register</a>
                </li>
                <li class="nav-item">
                  <a :class="{ 'nav-link': true, active: currentView === 'UserLogin' }" href="#"
                    @click.prevent="changeView('UserLogin')">Login</a>
                </li>
              </ul>
              <component v-bind:is="currentView" class="h-100" @close="isModalOpen = false"></component>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="mt-3">
      <!-- 这里是插槽 -->
      <slot></slot>
      <div v-if="$slots.default === undefined">No content in slot</div>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex';
import UserRegister from './UserRegister.vue';
import UserLogin from "./UserLogin.vue";

export default {
  name: 'UserLayout',
  data() {
    return {
      isNavOpen: false,
      selectedLanguage: 'en',
      languages: [
        { code: 'en', name: 'English' },
        { code: 'cn', name: 'Chinese' },
        // ...
      ],
      currentView: 'UserLogin',  // 默认显示登录组件
      isModalOpen: false,
    };
  },
  computed: {
    ...mapGetters([
      'getUsername'
    ]),
  },
  watch: {
    selectedLanguage(newLang) {
      // 当用户选择一个新的语言时，你可以在这里改变你的语言设置
      // 例如，你可以调用 vue-i18n 的语言切换方法，或者更改你的页面上的文本等
      this.$i18n.locale = newLang;
    },
  },
  components: {
    UserRegister,
    UserLogin
  },
  methods: {
    changeView(view) {
      this.currentView = view;
    },
  },
};
</script>

<style>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  backdrop-filter: blur(5px);
  /* This will blur the background */
}
</style>


