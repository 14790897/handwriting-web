<template>
  <div class="container">
      <div class="row justify-content-center">
          <div class="col-md-6">
              <div class="card border-primary my-5">
                <h2 class="mb-3">{{ $t('message.login') }}</h2>
                <div class="card-body">
                      <form @submit.prevent="submitForm">
                          <div class="form-group">
                              <label for="username">Username</label>
                              <input id="username" v-model="username" type="text" class="form-control" placeholder="Username">
                          </div>
                          <div class="form-group">
                              <label for="password">Password</label>
                              <input id="password" v-model="password" type="password" class="form-control" placeholder="Password">
                          </div>
                          <button type="submit" class="btn btn-primary w-100">{{ $t('message.login') }}</button>
                      </form>
                  </div>
              </div>
          </div>
      </div>
  </div>
</template>

<script>
import { mapMutations } from 'vuex';

export default {
  data() {
      return {
          username: '',
          password: ''
      }
  },
  methods: {
      ...mapMutations(['setUsername']),
      async submitForm() {
          let response = await this.$http.post('/api/login', {
              username: this.username,
              password: this.password
          });
          if (response.data.status === 'success') {
              // 使用 mutation 设置全局的 username
              this.setUsername(this.username);
              this.$router.push({name: 'Home'});
          } else {
              alert(this.$t('message.loginFailed'));
          }
      }
  }
}
</script>

<style scoped>
.container {
  margin-top: 100px;
}
</style>
