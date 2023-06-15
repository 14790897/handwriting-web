<template>
    <div class="d-flex align-items-center justify-content-center" style="height: 100vh;">
        <div class="card p-4" style="width: 400px;">
            <div v-if="notification.show" class="alert" :class="notification.type === 'success' ? 'alert-success' : 'alert-danger'">
                {{ notification.message }}// todo 修改多语言
            </div>
            <h2 class="mb-3">{{ $t('message.register') }}</h2>
            <form @submit.prevent="submitForm">
                <div class="form-group">
                    <label for="username">Username</label>
                    <input id="username" v-model="username" type="text" class="form-control" placeholder="Username">
                </div>
                <div class="form-group">
                    <label for="password">Password</label>
                    <input id="password" v-model="password" type="password" class="form-control" placeholder="Password">
                </div>
                <button type="submit" class="btn btn-primary btn-block">{{ $t('message.register') }}</button>
            </form>
        </div>
    </div>
</template>


<script>
export default {
    data() {
        return {
            username: '',
            password: '',
            csrfToken: '',
            notification: {
                show: false,
                message: '',
                type: '',
            }
        }
    },
    methods: {
        async submitForm() {
            // Get CSRF token from server
            // let csrfResponse = await this.$http.get('/api/csrf-token');
            // if (csrfResponse.status === 200) {
            //     this.csrfToken = csrfResponse.data.token;
            //     console.log('CSRF token: ' + this.csrfToken);
            // } else {
            //     // Handle error here
            //     console.error('Failed to get CSRF token');
            //     return;
            // }

            let response = await this.$http.post('/api/register', {
                username: this.username,
                password: this.password,
            }, {
                headers: {
                    'X-CSRFToken': this.csrfToken,
                    'Content-Type': 'application/json',
                }
            });
            if (response.data.status === 'success') {
                this.notification = {
                show: true,
                message: this.$t('message.registersuccess'),
                type: 'success',
                };
                this.$router.push({name: 'Home'});
            } else {
                this.notification = {
                show: true,
                message: this.$t('message.registerfailed'),
                type: 'error',
                };
            }
        }
    }
}
</script>

<style>
.notification {
  padding: 1em;
  margin-bottom: 1em;
}

.success {
  background-color: #dff0d8;
  color: #3c763d;
}

.error {
  background-color: #f2dede;
  color: #a94442;
}
</style>