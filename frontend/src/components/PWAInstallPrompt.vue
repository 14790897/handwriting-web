<template>
  <div v-if="showInstallPrompt" class="pwa-install-prompt">
    <div class="prompt-content">
      <div class="prompt-icon">
        <img src="/icon.svg" alt="App Icon" width="48" height="48">
      </div>
      <div class="prompt-text">
        <h3>安装手写生成器</h3>
        <p>将此应用添加到主屏幕，获得更好的使用体验</p>
      </div>
      <div class="prompt-actions">
        <button @click="installApp" class="install-btn">安装</button>
        <button @click="dismissPrompt" class="dismiss-btn">稍后</button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PWAInstallPrompt',
  data() {
    return {
      showInstallPrompt: false,
      deferredPrompt: null
    }
  },
  mounted() {
    // 监听 beforeinstallprompt 事件
    window.addEventListener('beforeinstallprompt', (e) => {
      console.log('PWA: beforeinstallprompt event fired');
      // 阻止默认的安装提示
      e.preventDefault();
      // 保存事件，稍后使用
      this.deferredPrompt = e;
      // 显示自定义安装提示
      this.showInstallPrompt = true;
    });

    // 监听应用安装事件
    window.addEventListener('appinstalled', () => {
      console.log('PWA: App was installed');
      this.showInstallPrompt = false;
      this.deferredPrompt = null;
    });

    // 检查是否已经安装
    if (window.matchMedia('(display-mode: standalone)').matches) {
      console.log('PWA: App is running in standalone mode');
    }
  },
  methods: {
    async installApp() {
      if (!this.deferredPrompt) {
        return;
      }

      // 显示安装提示
      this.deferredPrompt.prompt();
      
      // 等待用户响应
      const { outcome } = await this.deferredPrompt.userChoice;
      console.log(`PWA: User response to the install prompt: ${outcome}`);
      
      // 清理
      this.deferredPrompt = null;
      this.showInstallPrompt = false;
    },
    dismissPrompt() {
      this.showInstallPrompt = false;
      // 24小时后再次显示
      localStorage.setItem('pwa-install-dismissed', Date.now().toString());
    }
  }
}
</script>

<style scoped>
.pwa-install-prompt {
  position: fixed;
  bottom: 20px;
  left: 20px;
  right: 20px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  z-index: 1000;
  animation: slideUp 0.3s ease-out;
}

@keyframes slideUp {
  from {
    transform: translateY(100%);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.prompt-content {
  display: flex;
  align-items: center;
  padding: 16px;
  gap: 12px;
}

.prompt-icon img {
  border-radius: 8px;
}

.prompt-text {
  flex: 1;
}

.prompt-text h3 {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 600;
  color: #333;
}

.prompt-text p {
  margin: 0;
  font-size: 14px;
  color: #666;
}

.prompt-actions {
  display: flex;
  gap: 8px;
}

.install-btn, .dismiss-btn {
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: background-color 0.2s;
}

.install-btn {
  background: #2196f3;
  color: white;
}

.install-btn:hover {
  background: #1976d2;
}

.dismiss-btn {
  background: #f5f5f5;
  color: #666;
}

.dismiss-btn:hover {
  background: #e0e0e0;
}

@media (max-width: 480px) {
  .pwa-install-prompt {
    left: 10px;
    right: 10px;
    bottom: 10px;
  }
  
  .prompt-content {
    flex-direction: column;
    text-align: center;
  }
  
  .prompt-actions {
    width: 100%;
    justify-content: center;
  }
}
</style>
