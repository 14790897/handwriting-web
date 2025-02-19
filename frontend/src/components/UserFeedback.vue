<template>
  <div id="feedBack" class="container mt-5">
    <!-- <h1 class="text-center">Send Feedback</h1> -->
    <form @submit.prevent="sendFeedback" class="mt-4">
      <div class="form-group">
        <label for="email">{{ $t("message.email") }}</label>
        <input
          type="email"
          id="email"
          v-model="email"
          class="form-control"
          required
        />
      </div>
      <div class="form-group">
        <label for="feedback">{{ $t("message.feedback") }}</label>
        <textarea
          id="feedback"
          v-model="feedback"
          class="form-control"
          rows="5"
          required
        ></textarea>
      </div>
      <button type="submit" class="btn btn-primary">Send</button>
    </form>
    <!-- 建议GitHub上提问 -->
    <div class="mt-4">
      <p>
        {{ $t("message.suggest") }}
        <a
          href="https://github.com/14790897/handwriting-web/issues"
          target="_blank"
          >GitHub issue</a
        >
      </p>
    </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  name: "UserFeedback",
  data() {
    return {
      email: "",
      feedback: "",
    };
  },
  methods: {
    async sendFeedback() {
      const emailToSend = this.email; // 保存当前 `email` 值，防止在请求之前被清空导致数据丢失
      const feedbackToSend = this.feedback; // 保存当前 `feedback` 值

      this.email = ""; // 提前清空
      this.feedback = ""; // 提前清空
      try {
        const res = await axios.post(
          "https://mail.14790897.xyz/api/sendEmail",
          {
            email: emailToSend,
            feedback: feedbackToSend,
          }
        );
        if (res.status === 200) {
          alert("Feedback sent successfully!");
        }
      } catch (error) {
        // 可在失败时重新设置 email 和 feedback 恢复到发送前状态
        this.email = emailToSend;
        this.feedback = feedbackToSend;
        console.error("Error:", error);
        alert("Failed to send feedback.");
      }
    },
  },
};
</script>
