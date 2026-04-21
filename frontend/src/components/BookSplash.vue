<template>
  <transition name="splash-fade">
    <div v-if="visible" class="book-splash" @click="skipAnimation">

      <!-- 左半屏（内页，一直在） -->
      <div class="half half-left">
        <div class="page-content">
          <div class="ruled-lines">
            <div class="ruled-row" v-for="i in 20" :key="'l' + i">
              <span v-if="leftLines[i - 1]" class="handwriting-text">{{ leftLines[i - 1] }}</span>
              <div class="ruled-line"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右半屏（封面，向左翻转揭开） -->
      <div class="half half-right" :class="{ 'page-flip': bookOpen }">
        <!-- 正面：封面 -->
        <div class="page-face page-face-front">
          <div class="cover-content">
            <div class="cover-icon">
              <img src="/favicon-96x96.png" alt="logo" class="cover-img" />
            </div>
            <div class="cover-title">手写文字生成</div>
            <div class="cover-divider"></div>
            <div class="cover-sub">在线生成手写图片与 PDF</div>
          </div>
          <!-- 书脊阴影线 -->
          <div class="spine-shadow"></div>
        </div>
        <!-- 背面：翻过去后显示内页 -->
        <div class="page-face page-face-back">
          <div class="ruled-lines">
            <div class="ruled-row" v-for="i in 20" :key="'r' + i">
              <span v-if="rightLines[i - 1]" class="handwriting-text">{{ rightLines[i - 1] }}</span>
              <div class="ruled-line"></div>
            </div>
          </div>
        </div>
      </div>

      <!-- 翻开后出现的中缝阴影 -->
      <div class="spine-center" :class="{ 'spine-visible': bookOpen }"></div>

      <!-- 翻开后中央品牌文字 -->
      <transition name="brand-in">
        <div v-if="showBrand" class="brand-overlay">
          <div class="brand-icon">
            <img src="/favicon-96x96.png" alt="logo" class="brand-img" />
          </div>
          <div class="brand-name">手写文字生成</div>
          <div class="brand-sub">在线生成手写图片与 PDF</div>
        </div>
      </transition>

      <!-- 跳过提示 -->
      <div class="skip-hint">点击任意处跳过</div>
    </div>
  </transition>
</template>

<script>
export default {
  name: 'BookSplash',
  data() {
    return {
      visible: true,
      bookOpen: false,
      showBrand: false,
      leftLines: [],
      rightLines: [],
    };
  },
  /**
 * 组件挂载后执行的生命周期钩子
 * 初始化书本开启动画效果，包括：
 * - 生成左右两侧的装饰线条
 * - 延时触发书本打开动画
 * - 延时显示品牌标识
 * - 延时隐藏组件并触发完成事件
 * 同时在本地存储中记录已显示标记，避免重复展示
 */
mounted() {
    this.leftLines = this.generateLines(6, 10);
    this.rightLines = this.generateLines(6, 10);
    setTimeout(() => { this.bookOpen = true; }, 400);
    setTimeout(() => { this.showBrand = true; }, 1000);
    setTimeout(() => {
      localStorage.setItem('bookSplashShown', '1');
      this.visible = false;
      this.$emit('complete');
    }, 3200);
  },
  methods: {
    skipAnimation() {
      localStorage.setItem('bookSplashShown', '1');
      this.visible = false;
      this.$emit('complete');
    },
    generateLines(count, maxLen) {
      const pools = [
        '轻轻的我走了，正如我轻轻的来', '我挥一挥衣袖，不带走一片云彩',
        '面朝大海，春暖花开', '从明天起，做一个幸福的人',
        '喂马劈柴，周游世界', '关心粮食和蔬菜',
        '有一所房子，面朝大海', '给每一条河每一座山取一个温暖的名字',
        '陌生人我也为你祝福', '愿你有一个灿烂的前程',
        '愿你有情人终成眷属', '愿你在尘世获得幸福',
        '人生若只如初见', '何事秋风悲画扇',
        '山有木兮木有枝', '心悦君兮君不知',
        '入我相思门，知我相思苦', '长相思兮长相忆',
        '短相思兮无穷极', '早知如此绊人心',
        '何如当初莫相识', '云想衣裳花想容',
        '春风拂槛露华浓', '若非群玉山头见',
        '会向瑶台月下逢', '一枝红艳露凝香',
        '云雨巫山枉断肠', '借问汉宫谁得似',
      ];
      const lines = [];
      for (let i = 0; i < count; i++) {
        const text = pools[Math.floor(Math.random() * pools.length)];
        const max = Math.floor(Math.random() * maxLen) + 4;
        lines.push(text.substring(0, max));
      }
      return lines;
    },
  },
};
</script>

<style scoped>
/* ── 全屏容器 ── */
.book-splash {
  position: fixed;
  inset: 0;
  display: flex;
  z-index: 9999;
  cursor: pointer;
  overflow: hidden;
  background: #f8f9fa;
  perspective: 2000px;
}

/* ── 左右半屏 ── */
.half {
  width: 50%;
  height: 100%;
  position: relative;
}

/* ── 左侧内页 ── */
.half-left {
  background: #ffffff;
  border-right: 2px solid #e9ecef;
  box-shadow: inset -8px 0 20px rgba(0,0,0,0.06);
}

.page-content {
  width: 100%;
  height: 100%;
  padding: 60px 48px;
  box-sizing: border-box;
}

/* ── 稿纸横线 ── */
.ruled-lines {
  display: flex;
  flex-direction: column;
  gap: 0;
  height: 100%;
  justify-content: space-around;
}

.ruled-row {
  display: flex;
  align-items: flex-end;
  height: 100%;
  position: relative;
}

.ruled-line {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: #dee2e6;
}

.handwriting-text {
  position: absolute;
  left: 0;
  bottom: 4px;
  font-size: 15px;
  color: #868e96;
  letter-spacing: 3px;
  white-space: nowrap;
  font-family: 'KaiTi', 'STKaiti', 'FangSong', serif;
  line-height: 1.2;
}

/* ── 右侧翻页封面 ── */
.half-right {
  transform-style: preserve-3d;
  transform-origin: left center;
  transition: transform 1.1s cubic-bezier(0.645, 0.045, 0.355, 1.000);
  position: relative;
  z-index: 10;
}

.half-right.page-flip {
  transform: rotateY(-180deg);
}

/* ── 封面正面 / 背面 ── */
.page-face {
  position: absolute;
  inset: 0;
  backface-visibility: hidden;
  -webkit-backface-visibility: hidden;
}

.page-face-front {
  background: linear-gradient(160deg, #ffffff 0%, #eef3ff 60%, #dce8ff 100%);
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: inset -4px 0 12px rgba(0,123,255,0.08);
}

.page-face-back {
  background: #ffffff;
  transform: rotateY(180deg);
  padding: 60px 48px;
  box-sizing: border-box;
  box-shadow: inset 8px 0 20px rgba(0,0,0,0.06);
}

/* ── 封面内容 ── */
.cover-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 18px;
  text-align: center;
  animation: coverPulse 2s ease-in-out infinite;
}

@keyframes coverPulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.02); }
}

.cover-icon {
  filter: drop-shadow(0 4px 12px rgba(0,123,255,0.2));
}

.cover-img {
  width: 72px;
  height: 72px;
  object-fit: contain;
}

.cover-title {
  font-size: 32px;
  font-weight: 800;
  color: #2c3e50;
  letter-spacing: 6px;
}

.cover-divider {
  width: 60px;
  height: 3px;
  background: #007bff;
  border-radius: 2px;
}

.cover-sub {
  font-size: 14px;
  color: #6c757d;
  letter-spacing: 2px;
}

/* 封面左侧书脊 */
.spine-shadow {
  position: absolute;
  left: 0;
  top: 0;
  width: 24px;
  height: 100%;
  background: linear-gradient(90deg, rgba(0,0,0,0.10) 0%, transparent 100%);
  pointer-events: none;
}

/* ── 中缝阴影 ── */
.spine-center {
  position: absolute;
  left: 50%;
  top: 0;
  width: 0;
  height: 100%;
  transform: translateX(-50%);
  background: linear-gradient(90deg,
    transparent 0%,
    rgba(0,0,0,0.06) 30%,
    rgba(0,0,0,0.10) 50%,
    rgba(0,0,0,0.06) 70%,
    transparent 100%
  );
  transition: width 0.6s ease 0.8s;
  z-index: 5;
  pointer-events: none;
}

.spine-center.spine-visible {
  width: 48px;
}

/* ── 翻开后品牌文字 ── */
.brand-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 16px;
  z-index: 20;
  pointer-events: none;
  background: rgba(248, 249, 250, 0.55);
  backdrop-filter: blur(2px);
}

.brand-icon {
  filter: drop-shadow(0 6px 20px rgba(0,123,255,0.25));
}

.brand-img {
  width: 80px;
  height: 80px;
  object-fit: contain;
}

.brand-name {
  font-size: 40px;
  font-weight: 800;
  color: #2c3e50;
  letter-spacing: 8px;
  text-shadow: 0 2px 12px rgba(0,0,0,0.08);
}

.brand-sub {
  font-size: 15px;
  color: #6c757d;
  letter-spacing: 3px;
}

/* ── 跳过提示 ── */
.skip-hint {
  position: fixed;
  bottom: 28px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 13px;
  color: #adb5bd;
  z-index: 30;
  pointer-events: none;
}

/* ── 淡入淡出 ── */
.splash-fade-leave-active {
  transition: opacity 0.5s ease;
}
.splash-fade-leave-to {
  opacity: 0;
}

.brand-in-enter-active {
  transition: opacity 0.6s ease, transform 0.6s ease;
}
.brand-in-enter-from {
  opacity: 0;
  transform: scale(0.94);
}
</style>
