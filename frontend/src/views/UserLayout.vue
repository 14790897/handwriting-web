<template>
  <div>
    <nav class="navbar navbar-expand-lg navbar-light bg-light">
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
            <a class="nav-link dropdown-toggle" href="#" id="navbarDropdown" role="button" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
              <i class="fa fa-user"></i> {{ getUsername }}
            </a>
            <div class="dropdown-menu" aria-labelledby="navbarDropdown">
              <a class="dropdown-item" href="#">Profile</a>
              <a class="dropdown-item" href="#">Logout</a>
            </div>
          </li>
        </ul>
        <select v-model="selectedLanguage" class="custom-select ml-3">
          <option v-for="lang in languages" :key="lang.code" :value="lang.code">{{ lang.name }}</option>
        </select>
      </div>
    </nav>
    <div class="mt-3">
      <!-- 这里是插槽 -->
      <slot></slot>
      <div v-if="$slots.default === undefined">No content in slot</div>
    </div>
  </div>
</template>

<script>
import { mapGetters } from 'vuex';

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
};
</script>
