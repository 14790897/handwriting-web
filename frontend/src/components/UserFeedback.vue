<template>
    <div id="feedBack" class="container mt-5">
        <!-- <h1 class="text-center">Send Feedback</h1> -->
        <form @submit.prevent="sendFeedback" class="mt-4">
            <div class="form-group">
                <label for="email">{{ $t('message.email')}}</label>
                <input type="email" id="email" v-model="email" class="form-control" required />
            </div>
            <div class="form-group">
                <label for="feedback">{{ $t('message.feedback')}}</label>
                <textarea id="feedback" v-model="feedback" class="form-control" rows="5" required></textarea>
            </div>
            <button type="submit" class="btn btn-primary">Send</button>
        </form>
    </div>
</template>  

<script>
import axios from 'axios';

export default {
    name: 'UserFeedback',
    data() {
        return {
            email: '',
            feedback: ''
        };
    },
    methods: {
        async sendFeedback() {
            try {
                const res = await axios.post('https://serverless.liuweiqing.top/api/sendEmail', {
                    email: this.email,
                    feedback: this.feedback
                });
                if (res.status === 200) {
                    alert('Feedback sent successfully!');
                    this.email = '';
                    this.feedback = '';
                }
            } catch (error) {
                alert('Failed to send feedback.');
                console.error('Error:', error);
            }
        }
    }
};
</script>
