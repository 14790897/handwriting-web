<template>
  <div>
    <transition name="slide-fade">
      <nav class="navbar navbar-expand-lg navbar-light bg-light mb-3 justify-content-center" v-if="navbarVisible">
        <router-link class="navbar-brand " to="/">{{ $t('message.home') }}</router-link>
       

        <button @click="toggleNavbar" class="toggle-button btn btn-primary">
          {{ navbarVisible ? '隐藏导航栏' : '显示导航栏' }}
        </button>
        <button class="navbar-toggler" type="button" @click="isNavOpen = !isNavOpen">
          <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse justify-content-center" :class="{ show: isNavOpen }" id="navbarNav">
          <!-- <ul class="navbar-nav mr-auto">
          <li class="nav-item">
            <router-link class="nav-link" to="/Login">{{ $t('message.login') }}</router-link>
          </li>
          <li class="nav-item">
            <router-link class="nav-link" to="/Register">{{ $t('message.register') }}</router-link>
          </li>
        </ul> -->
          <!-- <ul class="navbar-nav">
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
        </ul> -->
          <select v-model="selectedLanguage" class="custom-select ml-3 mr-3">
            <option v-for="lang in languages" :key="lang.code" :value="lang.code">{{ lang.name }}</option>
          </select>

          <!-- 注册登录按钮 7.15 -->
          <!-- <button class="btn btn-light ml-auto" @click="isModalOpen = true" style="transition: all 0.3s ease;">
          {{ $t('message.reigisterlogin') }}
        </button> -->

        </div>
        <router-link to="/Introduce" class="text-info">{{ $t('message.introduce') }}</router-link>
      </nav>
      <button v-else @click="toggleNavbar" class="btn btn-outline-info btn-sm" style="opacity: 0.5;">
        {{ navbarVisible ? '隐藏导航栏' : '显示导航栏' }}
      </button>
    </transition>
    <!-- Add the following div as a modal overlay -->
    <div v-if="isModalOpen" class="d-flex align-items-center justify-content-center vh-100">
      <div v-if="isModalOpen" class="modal-overlay" @click.self="isModalOpen = false">
        <div class="modal-dialog">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title">{{ modalTitle }}</h5>
              <button type="button" class="close" @click="isModalOpen = false">
                <span aria-hidden="true">&times;</span>
              </button>
            </div>
            <div class="modal-body flex-grow-1">
              <ul class="nav nav-tabs">
                <li class="nav-item">
                  <a :class="{ 'nav-link': true, active: currentView === 'UserRegister' }" href="#"
                    @click.prevent="changeView('UserRegister')">{{ $t('message.register') }}</a>
                </li>
                <li class="nav-item">
                  <a :class="{ 'nav-link': true, active: currentView === 'UserLogin' }" href="#"
                    @click.prevent="changeView('UserLogin')">{{ $t('message.login') }}</a>
                </li>
              </ul>
              <!-- component代表组件 -->
              <component v-bind:is="currentView" class="h-100" @update="changeModalOpen"
                @login_delete="change_login_message"></component>
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
// import { mapGetters } from 'vuex';
import UserRegister from './UserRegister.vue';
import UserLogin from "./UserLogin.vue";
import { mapState, mapMutations } from 'vuex';

export default {
  name: 'UserLayout',
  computed: {
    ...mapState(['login_delete_message']),
    modalTitle() {
      return this.currentView === 'UserRegister' ? 'Register' : 'Login';
    },
  },
  data() {
    return {
      isNavOpen: false,
      selectedLanguage: 'cn',
      languages: [
        { code: 'cn', name: 'Chinese' },
        { code: 'en', name: 'English' },
        // ...
      ],
      currentView: 'UserLogin',  // 默认显示登录组件
      isModalOpen: false,
      navbarVisible: false,

    };
  },
  // computed: {
  //   ...mapGetters([
  //     'getUsername'
  //   ]),
  // },
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
    ...mapMutations(['login_delete_message_update']),
    changeView(view) {
      this.currentView = view;
    },
    changeModalOpen(newValue) {
      this.isModalOpen = newValue;
    },
    change_login_message(newValue) {
      //触发vuex中的mutations 7.12
      this.login_delete_message_update(newValue);
    },
    toggleNavbar() {
      this.navbarVisible = !this.navbarVisible;
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

.btn-light:hover {
  transform: scale(1.1);
  background-color: #ddd;
}

/* 下滑效果 */
.slide-down-enter-active,
.slide-down-leave-active {
  transition: all 0.3s ease;
}

.slide-down-enter,
.slide-down-leave-to {
  transform: translateY(-100%);
  opacity: 0;
}

/* 上滑效果 */
.slide-up-enter-active,
.slide-up-leave-active {
  transition: all 0.3s ease;
}

.slide-up-enter,
.slide-up-leave-to {
  transform: translateY(100%);
  opacity: 0;
}
</style>