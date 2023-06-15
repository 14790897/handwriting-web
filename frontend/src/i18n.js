import { createI18n } from 'vue-i18n'

const messages = {
  en: {
    message: {
      hello: 'Hello world',
      login: 'Login',
      loginfailed:'Login failed. Please check your username and password.',
      register: 'Register',
      registerfailed:'Username already exists. Choose a different one.',
      registersuccess:'Registration successful, redirecting to the main page...',
      login_required:'You need to login first.',
    },
  },
  cn: {
    message: {
      hello: '你好',
        login: '登录',
        loginfailed:'登录失败，请检查用户名和密码。',
        register: '注册',
        registerfailed:'用户名已存在，请选择其他用户名。',
        registersuccess:'注册成功，正在跳转到主页...',
        login_required:'请先登录。',
    },
  },
}

const i18n = createI18n({
  locale: 'en', // 默认显示的语言 
  messages,
})

export default i18n
