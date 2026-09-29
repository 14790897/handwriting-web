<template>
  <div class="generation-status-wrapper">
    <div v-if="generating || cooldownSeconds > 0" class="generation-status" data-testid="generation-status">
      <div v-if="generating" class="status-generating" data-testid="status-generating">
        {{ $t('message.statusGenerating') }}
      </div>
      <div v-else class="status-cooldown" data-testid="status-cooldown">
        {{ $t('message.statusCooldown', { seconds: cooldownSeconds }) }}
      </div>
    </div>

    <!-- 页数提示：仅生产站点显示（pageCount 为 0 时隐藏） -->
    <div v-if="pageCount > 0" class="page-info-alert">
      <div class="alert alert-warning">
        <strong>{{ $t('message.pageHintTitle') }}</strong>
        {{ $t('message.pageHintEstimate', { pages: pageCount }) }}
        <span v-if="pageCount > maxPages" class="page-hint-truncated">{{ $t('message.pageHintTruncated') }}</span>
      </div>
    </div>
  </div>
</template>

<script>
// 生成状态与页数提示：新旧两版布局共用，避免只在新版里渲染（改造后旧版一度丢掉了这两块提示）
export default {
  name: 'GenerationStatus',
  props: {
    generating: {
      type: Boolean,
      default: false,
    },
    cooldownSeconds: {
      type: Number,
      default: 0,
    },
    pageCount: {
      type: Number,
      default: 0,
    },
  },
  data() {
    return {
      // 与 app.py 里的生产站点页数上限保持一致
      maxPages: 10,
    };
  },
};
</script>

<style scoped>
.generation-status {
  margin: 15px 0;
  padding: 10px;
  border-radius: 5px;
  text-align: center;
  font-weight: bold;
}

.status-generating {
  background-color: #e3f2fd;
  color: #1976d2;
  border: 1px solid #bbdefb;
}

.status-cooldown {
  background-color: #fff3e0;
  color: #f57c00;
  border: 1px solid #ffcc02;
}

.page-info-alert .alert {
  margin: 10px 0;
  font-size: 14px;
}

.page-hint-truncated {
  color: #d63384;
}
</style>
