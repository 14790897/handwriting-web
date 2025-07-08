<template>
  <UserLayout>
      <router-view ref="myComponentRef"/>
      <!-- <HomeView /> -->
  </UserLayout>
  <PWAInstallPrompt />
</template>

<script>
import UserLayout from './views/UserLayout.vue';
import PWAInstallPrompt from './components/PWAInstallPrompt.vue';
// import HomeView from './views/HomeView.vue';

export default {
  name: 'App',
  components: {
    UserLayout,
    PWAInstallPrompt,
    // HomeView
  },
  // mounted() {
  //   // 请注意，$el 指向的是该组件最外层的 DOM 元素
  //   const contentElement = this.$refs.myComponentRef.$el;

  //   // 然后，你可以使用原生的 getBoundingClientRect 方法来获取元素的位置：
  //   if (contentElement) {
  //     const yPosition = contentElement.getBoundingClientRect().top;
  //     window.scrollTo(0, yPosition);
  //   }
  // },
};
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
}

nav {
  padding: 30px;
}

nav a {
  font-weight: bold;
  color: #2c3e50;
}

nav a.router-link-exact-active {
  color: #42b983;
}
button {
  transition: all 0.3s ease;
}

button:hover {
  cursor: pointer;
  transform: scale(1.1);
  box-shadow: 0px 0px 8px rgba(0, 0, 0, 0.3);
}

/* 文字不换行，溢出变为省略号 */
.nowrap {
  white-space: nowrap;
  text-overflow: ellipsis;
  overflow: hidden;
}

</style>
