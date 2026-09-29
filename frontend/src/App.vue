<template>
  <transition name="splash-fade">
    <BookSplash v-if="showSplash" @complete="showSplash = false" />
  </transition>
  <!-- <UserLayout v-show="!showSplash"> -->
      <router-view ref="myComponentRef"/>
      <!-- <HomeView /> -->
  <!-- </UserLayout> -->
  <PWAInstallPrompt />
</template>

<script>
// import UserLayout from './views/UserLayout.vue';
import PWAInstallPrompt from './components/PWAInstallPrompt.vue';
import BookSplash from './components/BookSplash.vue';
// import HomeView from './views/HomeView.vue';
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { useHead } from '@vueuse/head';

export default {
  name: 'App',
  components: {
    // UserLayout,
    PWAInstallPrompt,
    BookSplash,
    // HomeView
  },
  data() {
    let splashShown = false;
    try {
      splashShown = !!localStorage.getItem('bookSplashShown');
    } catch (error) {
      // 存储被禁用（例如浏览器「阻止所有 Cookie」）时按“没看过”处理，
      // 不能让读取异常把整个挂载打断
      void error;
    }
    return {
      showSplash: !splashShown,
    };
  },
  setup() {
    const route = useRoute();
    const site = 'https://handwrite.sixiangjia.de';
    const defaultTitle = '手写文字生成网站 - 在线生成手写图片与 PDF';
    const defaultDesc = '手写文字生成网站，支持多种字体和背景，在线生成高质量手写文字图片与 PDF。适合作业、论文、信件等场景，支持自定义字体、背景与参数调节。';

    const title = computed(() => route.meta?.title || defaultTitle);
    const description = computed(() => route.meta?.description || defaultDesc);
    const robots = computed(() => route.meta?.robots || 'index, follow');
    const canonical = computed(() => site + route.fullPath);

    useHead(() => ({
      title: title.value,
      meta: [
        { name: 'description', content: description.value },
        { name: 'robots', content: robots.value },
        { property: 'og:type', content: 'website' },
        { property: 'og:url', content: canonical.value },
        { property: 'og:title', content: title.value },
        { property: 'og:description', content: description.value },
        { property: 'og:image', content: '/default1.webp' },
        { property: 'twitter:card', content: 'summary_large_image' },
        { property: 'twitter:url', content: canonical.value },
        { property: 'twitter:title', content: title.value },
        { property: 'twitter:description', content: description.value },
        { property: 'twitter:image', content: '/default1.webp' },
      ],
      link: [
        { rel: 'canonical', href: canonical.value },
      ],
    }));

    return {};
  },
};
</script>

<style>
/* 开屏遮罩的淡出。被过渡的是 BookSplash 的根节点，所以规则得写在这里：
   transition 与它的 CSS 放在同一个文件，避免以后有人把另一半当成多余样式删掉 */
.splash-fade-leave-active {
  transition: opacity 0.5s ease;
  /* 淡出期间表单已经露出来了，遮罩不能再吃掉点击 */
  pointer-events: none;
}

.splash-fade-leave-to {
  opacity: 0;
}

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

