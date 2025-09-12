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
import { computed } from 'vue';
import { useRoute } from 'vue-router';
import { useHead } from '@vueuse/head';

export default {
  name: 'App',
  components: {
    UserLayout,
    PWAInstallPrompt,
    // HomeView
  },
  setup() {
    const route = useRoute();
    const site = 'https://handwrite.14790897.xyz';
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
        { property: 'og:image', content: '/default1.png' },
        { property: 'twitter:card', content: 'summary_large_image' },
        { property: 'twitter:url', content: canonical.value },
        { property: 'twitter:title', content: title.value },
        { property: 'twitter:description', content: description.value },
        { property: 'twitter:image', content: '/default1.png' },
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

