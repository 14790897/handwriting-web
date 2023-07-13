<template>
  <div class="d-flex align-items-center justify-content-center" style="height: 100vh;">
    <div class="card p-4" style="width: 400px;">
      <h2 class="mb-3">{{ $t('message.login') }}</h2>
      <form @submit.prevent="submitForm">
        <div class="form-group">
          <label for="username">{{ $t('message.username') }}</label>
          <input id="username" v-model="username" type="text" class="form-control" placeholder="Username">
        </div>
        <div class="form-group">
          <label for="password">{{ $t('message.password') }}</label>
          <input id="password" v-model="password" type="password" class="form-control" placeholder="Password">
        </div>
        <button type="submit" class="btn btn-primary btn-block">{{ $t('message.login') }}</button>
      </form>
    </div>
  </div>
</template>

<script>
import Swal from 'sweetalert2'

export default {
  data() {
    return {
      username: '',
      password: ''
    }
  },
  methods: {
    // ...mapMutations(['setUsername']),
    submitForm() {
      this.$http.post('/api/login', {
        username: this.username,
        password: this.password
      })
        .then(response => {
          if (response.data.status === 'success') {
            // 使用 mutation 设置全局的 username
            // this.setUsername(this.username);
            // this.$router.push({name: 'Home'});

            //使得模态框消失
            this.$emit('update', false);
            //使得未登录消息消失
            this.$emit('login_delete', true)
          }
        })
        .catch(error => {
          console.log('login failed 应该显示sweet的报错信息' + error);
          console.log(this.$t('message.loginfailed'));
          this.showAlert();
        });
    },
    showAlert() {
      Swal.fire({
        title: 'Error!',
        text: this.$t('message.loginfailed'),
        icon: 'error',
        confirmButtonText: 'OK',
        customClass: {
          popup: 'swal2-popup-custom'
        }
      })
    }

  }
}
</script>

<style scoped>
.swal2-popup-custom {
  z-index: 2000 !important;
}
</style>
