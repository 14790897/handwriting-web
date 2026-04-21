<template>
  <div style="height: 20px;"></div>
  <div class="container">
    <!-- 错误消息以及提示信息 -->
    <div id="message">
      <div v-if="message" class="alert alert-info" role="alert">
        {{ message }}
      </div>
      <div v-if="uploadMessage" class="alert alert-info" role="alert">
        {{ uploadMessage }}
      </div>
    </div> 

    <div id="form">
      <div class="container_file row">

        <div class="col justify-content-between">
          <TextInput @childEvent="(eventData) => { this.text = eventData }"></TextInput>
        </div>

        <div class="col">
          <label>{{ $t('message.fontFile') }}:</label>
          <div class="d-flex flex-row justify-content-between">
            <div class="font-selection">
              <button @click="triggerFontFileInput">{{ $t('message.chooseFile') }}</button>
              <input type="file" ref="fontFileInput" @change="onFontChange" style="display: none;" />
            </div>
            <select v-model="selectedOption" class="styled-select" style="width: 60%;">
              <option v-for="option in options" :value="option.value" :key="option.value">
                {{ option.text }}
              </option>
            </select>
          </div>

          <div class="image-container">
            <label>{{ $t('message.backgroundImageFile') }}:</label>
            <div class="button-container">
              <!-- :disabled="isDimensionSpecified" -->
              <button @click="triggerImageFileInput" :class="{ 'button-disabled': isDimensionSpecified }"
                :title="isDimensionSpecified ? $t('message.widthAndHeightSpecified') : ''">
                {{ $t('message.chooseFile') }}
                <div>
                  <div v-if="selectedImageFileName" class="clear-button" @click.stop="clearImage">
                    <div class="clear-button-line"></div>
                    <div class="clear-button-line"></div>
                  </div>
                </div>
              </button>
              <span class="border p-2 fs-6 text-primary nowrap" v-if="selectedImageFileName">{{ selectedImageFileName
                }}</span>
              <input type="file" ref="imageFileInput" @change="onBackgroundImageChange" style="display: none;" />
              <div v-if="isLoading" class="loader">{{ $t('message.loading') }}...</div>
            </div>
          </div>
        </div>
      </div>

      <div c lass="label-container">
 
        <label>{{ $t('message.width') }}:
          <input type="number" v-model="width" :disabled="isBackgroundImageSpecified"
            :title="isBackgroundImageSpecified ? $t('message.backgroundImageSpecified') : ''" />
        </label>
      </div>


      <div class="label-container">

        <label>{{ $t('message.height') }}:
          <input type="number" v-model="height" :disabled="isBackgroundImageSpecified"
            :title="isBackgroundImageSpecified ? $t('message.backgroundImageSpecified') : ''" />
        </label>
        <button type="button" class="close" aria-label="Close" @click="clearDimensions">
          <span aria-hidden="true">&times;</span>
        </button>
      </div>

      <input class="optionUnderline" type="checkbox" id="optionUnderline" name="option2" value="value2"
        v-model="isUnderlined">
      <label for="optionUnderline" style="margin-right: 0px;">增加下划线</label>

      <input class="optionEnglishSpacing" type="checkbox" id="optionEnglishSpacing" name="optionEnglishSpacing" value="englishSpacing"
        v-model="enableEnglishSpacing">
      <label for="optionEnglishSpacing" style="margin-right: 0px;">{{ $t('message.enableEnglishSpacing') }}</label>

      <div class="label-container">

        <label>{{ $t('message.fontSize') }}:
          <input type="number" v-model="fontSize" placeholder="recommend > 100" />
        </label>
      </div>

      <div class="label-container">
        <label>{{ $t('message.lineSpacing') }}:
          <input type="number" v-model="lineSpacing" />
        </label>
      </div>

      <div class="label-container">
        <label>{{ $t('message.topMargin') }}:
          <input type="number" v-model="marginTop" />
        </label>
      </div>

      <div class="label-container">
        <label>{{ $t('message.bottomMargin') }}:
          <input type="number" v-model="marginBottom" />
        </label>
      </div>

      <div class="label-container">
        <label>{{ $t('message.leftMargin') }}:
          <input type="number" v-model="marginLeft" />
        </label>
      </div>

      <div class="label-container">
        <label>{{ $t('message.rightMargin') }}:
          <input type="number" v-model="marginRight" />
        </label>
      </div>
      <!-- 这是一个按钮，用户点击这个按钮时，会展开或折叠下面的内容区域 -->
      <button class="btn btn-primary" type="button" @click="toggleCollapse" style="width: 100px; font-size:0.9rem">
        {{ $t('message.expand') }}
      </button>

      <!-- 这是一个内容区域，它的 id 与上面的按钮的 data-target 相对应 -->
      <div v-if="isExpanded" id="collapseContent">
        <div class="card card-body">
          <div class="label-container">
            <label>{{ $t('message.lineSpacingSigma') }}:
              <input type="number" v-model="lineSpacingSigma" />
            </label>
          </div>

          <div class="label-container">
            <label>{{ $t('message.fontSizeSigma') }}:
              <input type="number" v-model="fontSizeSigma" />
            </label>
          </div>

          <div class="label-container">
            <label>{{ $t('message.wordSpacingSigma') }}:
              <input type="number" v-model="wordSpacingSigma" />
            </label>
          </div>

          <div class="label-container">
            <label>{{ $t('message.perturbXSigma') }}:
              <input type="number" v-model="perturbXSigma" />
            </label>
          </div>

          <div class="label-container">
            <label>{{ $t('message.perturbYSigma') }}:
              <input type="number" v-model="perturbYSigma" />
            </label>
          </div>

          <div class="label-container">
            <label>{{ $t('message.perturbThetaSigma') }}:
              <input type="number" v-model="perturbThetaSigma" />
            </label>
          </div>

          <div class="label-container">
            <label>{{ $t('message.wordSpacing') }}:
              <input type="number" v-model="wordSpacing" />
            </label>
          </div>



          <div class="label-container">
            <label>{{ $t('message.strikethrough_length_sigma') }}:
              <input type="text" v-model="strikethrough_length_sigma" />
            </label>
          </div>

          <div class='label-container'>
            <label>{{ $t('message.strikethrough_angle_sigma') }}:
              <input type="number" v-model="strikethrough_angle_sigma" />
            </label>
          </div>

          <div class='label-container'>
            <label>{{ $t('message.strikethrough_width_sigma') }}:
              <input type="number" v-model="strikethrough_width_sigma" />
            </label>
          </div>

          <div class='label-container'>
            <label>{{ $t('message.strikethrough_probability') }}:
              <input type="number" v-model="strikethrough_probability" />
            </label>
          </div>

          <div class='label-container'>
            <label>{{ $t('message.strikethrough_width') }}:
              <input type="number" v-model="strikethrough_width" />
            </label>
          </div>

          <div class='label-container'>
            <label>{{ $t('message.ink_depth_sigma') }}:
              <input type="number" v-model="ink_depth_sigma" />
            </label>
          </div>
        </div>
      </div>
    </div>

    <!-- 生成状态提示 -->
    <div v-if="isGenerating || isInCooldownPeriod" class="generation-status">
      <div v-if="isGenerating" class="status-generating">
        🔄 正在生成中，请稍候...
      </div>
      <div v-else-if="isInCooldownPeriod" class="status-cooldown">
        ⏳ 冷却中，还需等待 {{ remainingCooldown }} 秒
      </div>
    </div>

    <div class="buttons">
      <button @click="loadPreset">{{ $t('message.loadSettings') }}</button>
      <button @click="savePreset">{{ $t('message.saveSettings') }}</button>
      <button @click="resetSettings">{{ $t('message.resetSettings') }}</button>
      <button @click="generateHandwriting(preview = true)" :disabled="shouldDisableButtons">
        {{ buttonText || $t('message.preview') }}
      </button>
      <button v-if="isDevEnv" @click="toggleFullPreview" :disabled="shouldDisableButtons">
        本地全量预览：{{ enableFullPreview ? '开' : '关' }}
      </button>
      <button @click="generateHandwriting(preview = false)" :disabled="shouldDisableButtons">
        {{ buttonText || $t('message.generateFullHandwritingImage') }}
      </button>
      <button @click="generateHandwriting(preview = false, pdf_save = true)" :disabled="shouldDisableButtons">
        {{ buttonText || $t('message.generatePdf') }}
      </button>

      <router-link to="/Feedback" class="btn btn-info">{{ $t('message.feedback') }}</router-link>
    </div>

    <!-- 页数提示 -->
    <div v-if="isProductionSite() && text && text.length > 0" class="page-info-alert">
      <div class="alert alert-warning" style="margin: 10px 0; font-size: 14px;">
        <strong>📄 页数提示：</strong>
        预计生成 <strong>{{ estimatePageCount() }}</strong> 页
        <span v-if="estimatePageCount() > 10" style="color: #d63384;">
          （handwrite.14790897.xyz限制一次最多10页，超出部分将被截断）
        </span>
      </div>
    </div>
    <!-- 预览区 -->
    <div class="preview">
      <h2 v-if="!previewImages || previewImages.length === 0">{{ $t('message.preview') }}:</h2>

      <div class="preview-container text-center">
        <!-- 导航按钮 -->
        <div v-if="previewImages && previewImages.length > 1" class="mb-3 d-flex justify-content-center align-items-center gap-3">
          <button @click="prevPage" class="btn btn-outline-primary btn-sm" :disabled="currentPreviewIndex === 0">
            &larr; 上一页
          </button>
          <span class="mx-3 font-weight-bold">
            第 {{ currentPreviewIndex + 1 }} 页 / 共 {{ previewImages.length }} 页
          </span>
          <button @click="nextPage" class="btn btn-outline-primary btn-sm" :disabled="currentPreviewIndex === previewImages.length - 1">
            下一页 &rarr;
          </button>
        </div>

        <!-- 图片显示 -->
        <div v-if="previewImages && previewImages.length > 0">
          <img :src="previewImages[currentPreviewIndex]" 
               :alt="$t('message.previewImage') + ' ' + (currentPreviewIndex + 1)" 
               style="width: 600px; max-width: 100%; border: 1px solid #ddd; padding: 5px; border-radius: 4px;" />
        </div>
        <img v-else :src="previewImage" :alt="$t('message.previewImage')" style="width: 600px; max-width: 100%;" />
      </div>
    </div>
    <footer class=" footer mt-auto py-3 bg-white">
      <div class="container text-center">

        <!-- <a href="mailto:14790897abc@gmail.com" class="text-info">14790897abc@gmail.com</a> -->
        <span class="text-black">{{ $t('message.projectAddress') }}:</span>
        <a href="https://github.com/14790897/handwriting-web" class="text-info">GitHub</a>
      </div>
      <!-- 本网站是免费网站如果你是付费访问的请退款 -->
      <div class ='freeprompt'>{{ $t('message.freeprompt') }}</div>
    </footer>
  </div>
</template>

<script>
import { mapState } from 'vuex';
import TextInput from './TextInput.vue';
import Swal from 'sweetalert2';



export default {
  // props: {
  //   login_delete_message: {
  //     type: Boolean,
  //     default: false
  //   }
  // },
  components: {
    TextInput,

  },

  data() {
    return {
      text: "",
      fontFile: null,
      backgroundImage: null,
      fontSize: 124,
      lineSpacing: 200,
      fill: "(0, 0, 0, 255)",
      width: 2481,
      height: 3507,
      marginTop: 50,
      marginBottom: 50,
      marginLeft: 50,
      marginRight: 50,
      previewImage: "/default1.webp", // 添加一个新的数据属性来保存预览图片的 URL
      previewImages: [], // 用于存储多页预览图片的数组
      currentPreviewIndex: 0, // 当前预览的图片索引
      preview: false,
      lineSpacingSigma: 0,
      fontSizeSigma: 2,
      wordSpacingSigma: 2,
      perturbXSigma: 3,
      perturbYSigma: 3,
      perturbThetaSigma: 0.05,
      wordSpacing: 1,
      endChars: '',
      errorMessage: '',  // 错误消息
      message: '',  // 提示消息
      uploadMessage: '',  // 上传提示消息
      selectedFontFileName: '',
      selectedImageFileName: '',
      //字体下拉选框
      selectedOption: '1',  // 当前选中的选项
      options: '',  // 下拉选项
      isLoading: false, //7.6
      strikethrough_length_sigma: 2,
      strikethrough_angle_sigma: 2,
      strikethrough_width_sigma: 2,
      strikethrough_probability: 0.005,
      strikethrough_width: 8,
      ink_depth_sigma: 30,
      isUnderlined: true,
      enableEnglishSpacing: false,
      isExpanded: false,
      // 生成状态控制
      isGenerating: false,
      lastGenerateTime: 0,
      generateCooldown: 3000, // 3秒冷却时间
      cooldownTimer: null,
      remainingCooldown: 0,
      isInCooldownPeriod: false,
      // 队列满倒计时
      queueFullCountdown: 0,        // 当前剩余秒数，>0 时展示提示
      queueFullTotal: 0,            // 初始等待秒数，用于计算进度条
      queueFullTimer: null,         // setInterval 句柄
      enableFullPreview: false,
      localStorageItems: ['text', 'fontFile', 'fontSize', 'lineSpacing', 'fill', 'width', 'height', 'marginTop', 'marginBottom', 'marginLeft', 'marginRight', 'selectedFontFileName', 'selectedOption', 'lineSpacingSigma', 'fontSizeSigma', 'wordSpacingSigma', 'perturbXSigma', 'perturbYSigma', 'perturbThetaSigma', 'wordSpacing', 'strikethrough_length_sigma', 'strikethrough_angle_sigma', 'strikethrough_width_sigma', 'strikethrough_probability', 'strikethrough_width', 'ink_depth_sigma', 'isUnderlined', 'enableEnglishSpacing'],
    };
  },
  created() {

    // const localStorageItems = ['text', 'fontFile', 'fontSize', 'lineSpacing', 'fill', 'width', 'height', 'marginTop', 'marginBottom', 'marginLeft', 'marginRight', 'selectedFontFileName', 'selectedOption', 'lineSpacingSigma', 'fontSizeSigma', 'wordSpacingSigma', 'perturbXSigma', 'perturbYSigma', 'perturbThetaSigma', 'wordSpacing'];//, 'backgroundImage', 'selectedImageFileName'

    this.localStorageItems.forEach(item => {
      const value = localStorage.getItem(item);
      if (value !== null && value !== "undefined") {
        try {
          this[item] = JSON.parse(value);
          console.log('成功加载localStorage项目:', item, '值:', this[item]);
        } catch (error) {
          console.error('解析localStorage项目失败:', item, '原始值:', value, '错误:', error);
        }
      } else {
        console.log('localstorage缺失item:' + item)
      }
    });

    this.$http.get('/api/fonts_info').then(response => {
      this.options = response.data.map((font, index) => {
        return { value: String(index + 1), text: font };
      });
    }).catch(error => {
      if (error.response && error.response.data) {
        this.errorMessage = error.response.data.error;
        this.message = '';
        this.uploadMessage = '';
      } else {
        this.errorMessage = error;
        this.message = '';
        this.uploadMessage = '';
      }
    });
    console.log('options' + this.options)
  },
  computed: {
    isDimensionSpecified() {
      // 当宽度或高度有值时，返回 true，这会禁用背景图片输入框
      return !!(this.width || this.height);
    },
    isBackgroundImageSpecified() {
      // 当有背景图片时，返回 true，这会禁用宽度和高度输入框
      return !!this.backgroundImage;
    },

    // 按钮是否应该被禁用
    shouldDisableButtons() {
      return this.isGenerating || this.isInCooldownPeriod || this.queueFullCountdown > 0;
    },

    // 队列满进度条（从100%倒减到0%）
    queueFullBarPercent() {
      if (this.queueFullTotal <= 0) return 0;
      return Math.max(0, (this.queueFullCountdown / this.queueFullTotal) * 100);
    },

    // 按钮显示文本
    buttonText() {
      if (this.isGenerating) {
        return '生成中...';
      } else if (this.isInCooldownPeriod) {
        return `请等待 ${this.remainingCooldown}s`;
      }
      return null; // 使用默认文本
    },
    isDevEnv() {
      return process.env.NODE_ENV === 'development';
    },

    //vuex中的login_delete_message，下面使用watch监控这个值  7.13
    ...mapState(['login_delete_message']),
  },
  watch: {
    login_delete_message(newVal) {
      if (newVal) {
        // this.message = '';
        // this.uploadMessage = '';
        console.log('已进入watch，错误消息已经清空');
      }
    },
    errorMessage(newVal) {
      if (newVal) {
        this.$swal.fire({
          toast: true,
          position: 'top-end',
          icon: 'error',
          title: newVal,
          showConfirmButton: false,
          timer: 5000,
          timerProgressBar: true,
        });
      }
    },
    message(newVal) {
      if (newVal) {
        this.$swal.fire({
          toast: true,
          position: 'top-end',
          icon: 'success',
          title: newVal,
          showConfirmButton: false,
          timer: 3000,
          timerProgressBar: true,
        });
      }
    },
    uploadMessage(newVal) {
      if (newVal) {
        this.$swal.fire({
          toast: true,
          position: 'top-end',
          icon: 'info',
          title: newVal,
          showConfirmButton: false,
          timer: false, // 上传提示保持显示
          showClass: { popup: 'swal2-show' },
          hideClass: { popup: 'swal2-hide' },
        });
      }
    },
    queueFullCountdown(newVal) {
      if (newVal > 0) {
        this.$swal.fire({
          toast: true,
          position: 'top-end',
          icon: 'warning',
          title: `服务器繁忙，队列已满，预计 ${newVal} 秒后可重试`,
          showConfirmButton: false,
          timer: newVal * 1000,
          timerProgressBar: true,
          didOpen: (toast) => {
            const progressBar = toast.querySelector('.swal2-timer-progress-bar');
            if (progressBar && this.queueFullTotal > 0) {
              // 更新进度条
              const updateProgress = () => {
                if (this.queueFullCountdown > 0 && progressBar) {
                  const percent = (this.queueFullCountdown / this.queueFullTotal) * 100;
                  progressBar.style.width = percent + '%';
                  requestAnimationFrame(updateProgress);
                }
              };
              requestAnimationFrame(updateProgress);
            }
          },
        });
      }
    },
    text: {
      handler(newVal) {
        localStorage.setItem('text', JSON.stringify(newVal));
      },
      deep: true
    },
    fontFile: {
      handler(newVal) {
        localStorage.setItem('fontFile', JSON.stringify(newVal));
      },
      deep: true
    },
    // backgroundImage: {
    //   handler(newVal) {
    //     localStorage.setItem('backgroundImage', JSON.stringify(newVal));
    //   },
    //   deep: true
    // },
    fontSize: {
      handler(newVal) {
        localStorage.setItem('fontSize', JSON.stringify(newVal));
      },
      deep: true
    },
    lineSpacing: {
      handler(newVal) {
        localStorage.setItem('lineSpacing', JSON.stringify(newVal));
      },
      deep: true
    },
    fill: {
      handler(newVal) {
        localStorage.setItem('fill', JSON.stringify(newVal));
      },
      deep: true
    },
    width: {
      handler(newVal) {
        localStorage.setItem('width', JSON.stringify(newVal));
      },
      deep: true
    },
    height: {
      handler(newVal) {
        localStorage.setItem('height', JSON.stringify(newVal));
      },
      deep: true
    },
    marginTop: {
      handler(newVal) {
        localStorage.setItem('marginTop', JSON.stringify(newVal));
      },
      deep: true
    },
    marginBottom: {
      handler(newVal) {
        localStorage.setItem('marginBottom', JSON.stringify(newVal));
      },
      deep: true
    },
    marginLeft: {
      handler(newVal) {
        localStorage.setItem('marginLeft', JSON.stringify(newVal));
      },
      deep: true
    },
    marginRight: {
      handler(newVal) {
        localStorage.setItem('marginRight', JSON.stringify(newVal));
      },
      deep: true
    },
    selectedFontFileName: {
      handler(newVal) {
        localStorage.setItem('selectedFontFileName', JSON.stringify(newVal));
      },
      deep: true
    },
    selectedImageFileName: {
      handler(newVal) {
        localStorage.setItem('selectedImageFileName', JSON.stringify(newVal));
      },
      deep: true
    },
    selectedOption: {
      handler(newVal) {
        localStorage.setItem('selectedOption', JSON.stringify(newVal));
      },
      deep: true
    },
    lineSpacingSigma: {
      handler(newVal) {
        localStorage.setItem('lineSpacingSigma', JSON.stringify(newVal));
      },
      deep: true
    },
    fontSizeSigma: {
      handler(newVal) {
        localStorage.setItem('fontSizeSigma', JSON.stringify(newVal));
      },
      deep: true
    },
    wordSpacingSigma: {
      handler(newVal) {
        localStorage.setItem('wordSpacingSigma', JSON.stringify(newVal));
      },
      deep: true
    },
    perturbXSigma: {
      handler(newVal) {
        localStorage.setItem('perturbXSigma', JSON.stringify(newVal));
      },
      deep: true
    },
    perturbYSigma: {
      handler(newVal) {
        localStorage.setItem('perturbYSigma', JSON.stringify(newVal));
      },
      deep: true
    },
    perturbThetaSigma: {
      handler(newVal) {
        localStorage.setItem('perturbThetaSigma', JSON.stringify(newVal));
      },
      deep: true
    },
    wordSpacing: {
      handler(newVal) {
        localStorage.setItem('wordSpacing', JSON.stringify(newVal));
      },
      deep: true
    },
    strikethrough_length_sigma: {
      handler(newVal) {
        localStorage.setItem('strikethrough_length_sigma', JSON.stringify(newVal));
      },
      deep: true
    },
    strikethrough_angle_sigma: {
      handler(newVal) {
        localStorage.setItem('strikethrough_angle_sigma', JSON.stringify(newVal));
      },
      deep: true
    },
    strikethrough_width_sigma: {
      handler(newVal) {
        localStorage.setItem('strikethrough_width_sigma', JSON.stringify(newVal));
      },
      deep: true
    },
    strikethrough_probability: {
      handler(newVal) {
        localStorage.setItem('strikethrough_probability', JSON.stringify(newVal));
      },
      deep: true
    },
    strikethrough_width: {
      handler(newVal) {
        localStorage.setItem('strikethrough_width', JSON.stringify(newVal));
      },
      deep: true
    },
    ink_depth_sigma: {
      handler(newVal) {
        localStorage.setItem('ink_depth_sigma', JSON.stringify(newVal));
      },
      deep: true
    },
    isUnderlined: {
      handler(newVal) {
        localStorage.setItem('isUnderlined', JSON.stringify(newVal));
      },
      deep: true
    },
    enableEnglishSpacing: {
      handler(newVal) {
        localStorage.setItem('enableEnglishSpacing', JSON.stringify(newVal));
      },
      deep: true
    },
  },

  methods: {
    prevPage() {
      if (this.currentPreviewIndex > 0) {
        this.currentPreviewIndex--;
      }
    },
    nextPage() {
      if (this.currentPreviewIndex < this.previewImages.length - 1) {
        this.currentPreviewIndex++;
      }
    },
    toggleCollapse() {
      this.isExpanded = !this.isExpanded;
    },
    toggleFullPreview() {
      this.enableFullPreview = !this.enableFullPreview;
    },
    startQueueFullCountdown(seconds) {
      // 清掉旧计时器
      if (this.queueFullTimer) {
        clearInterval(this.queueFullTimer);
        this.queueFullTimer = null;
      }
      this.queueFullTotal = seconds;
      this.queueFullCountdown = seconds;
      this.queueFullTimer = setInterval(() => {
        this.queueFullCountdown -= 1;
        if (this.queueFullCountdown <= 0) {
          this.queueFullCountdown = 0;
          clearInterval(this.queueFullTimer);
          this.queueFullTimer = null;
        }
      }, 1000);
    },
    updateTaskUploadMessage(taskData, taskId) {
      const taskStatus = taskData?.task_status;
      const taskMessage = taskData?.task_message || '任务处理中';
      const taskProgress = taskData?.task_progress;
      const queuePendingCount = taskData?.queue_pending_count;
      const queueAheadCount = taskData?.queue_ahead_count;
      const processingCount = taskData?.processing_count;
      if (taskStatus === 'pending' && typeof queuePendingCount === 'number' && typeof queueAheadCount === 'number') {
        if (typeof processingCount === 'number') {
          this.uploadMessage = `${taskMessage}（前方排队 ${queueAheadCount} 人，当前排队 ${queuePendingCount} 人，处理中 ${processingCount} 人） Task ID: ${taskId}`;
        } else {
          this.uploadMessage = `${taskMessage}（前方排队 ${queueAheadCount} 人，当前排队 ${queuePendingCount} 人） Task ID: ${taskId}`;
        }
      } else if (typeof taskProgress === 'number') {
        this.uploadMessage = `${taskMessage}（${taskProgress}%） Task ID: ${taskId}`;
      } else {
        this.uploadMessage = `${taskMessage} Task ID: ${taskId}`;
      }
    },
    async waitForTaskViaWebSocket(taskId, timeoutMs = 5 * 60 * 1000) {
      return new Promise((resolve, reject) => {
        let isSettled = false;
        const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
        const wsUrl = `${protocol}://${window.location.host}/api/generate_handwriting/ws/${taskId}`;
        const socket = new WebSocket(wsUrl);

        const timeoutId = setTimeout(() => {
          if (isSettled) return;
          isSettled = true;
          try {
            socket.close();
          } catch (e) {
            // ignore close errors
          }
          reject(new Error('WebSocket任务等待超时'));
        }, timeoutMs);

        socket.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data?.status === 'error') {
              if (isSettled) return;
              isSettled = true;
              clearTimeout(timeoutId);
              socket.close();
              reject(new Error(data?.message || '任务不存在'));
              return;
            }

            this.updateTaskUploadMessage(data, taskId);
            if (data?.task_status === 'completed') {
              if (isSettled) return;
              isSettled = true;
              clearTimeout(timeoutId);
              socket.close();
              resolve();
            } else if (data?.task_status === 'failed') {
              if (isSettled) return;
              isSettled = true;
              clearTimeout(timeoutId);
              socket.close();
              reject(new Error(data?.error_message || '任务执行失败'));
            }
          } catch (e) {
            // ignore malformed payload
          }
        };

        socket.onerror = () => {
          if (isSettled) return;
          isSettled = true;
          clearTimeout(timeoutId);
          reject(new Error('WebSocket连接失败'));
        };

        socket.onclose = () => {
          if (isSettled) return;
          isSettled = true;
          clearTimeout(timeoutId);
          reject(new Error('WebSocket连接已关闭'));
        };
      });
    },
    async pollGenerationTask(taskId, timeoutMs = 5 * 60 * 1000, intervalMs = 1500) {
      const start = Date.now();
      while (Date.now() - start < timeoutMs) {
        const statusResponse = await this.$http.get(`/api/generate_handwriting/task/${taskId}`);
        const taskStatus = statusResponse.data?.task_status;
        this.updateTaskUploadMessage(statusResponse.data, taskId);
        if (taskStatus === 'completed') {
          return;
        }
        if (taskStatus === 'failed') {
          throw new Error(statusResponse.data?.error_message || '任务执行失败');
        }
        await new Promise(resolve => setTimeout(resolve, intervalMs));
      }
      throw new Error('任务处理超时，请重试');
    },
    handleGenerationResultResponse(response) {
      const contentType = response.headers['content-type'] || '';
      if (contentType.includes('application/json')) {
        // 处理多页预览图像 (JSON)
        if (response.data && response.data.status === 'success') {
          this.previewImages = response.data.images.map(img => 'data:image/png;base64,' + img);
          this.currentPreviewIndex = 0; // 重置为第一页
          if (this.previewImages.length > 0) {
            this.previewImage = this.previewImages[0]; // 兼容显示第一页
          }
          this.message = '预览图像已加载。';
          this.uploadMessage = '';
          this.errorMessage = '';
        }
      } else if (contentType.includes('image/png')) {
        // 兼容旧的单张图片返回逻辑
        const blobUrl = URL.createObjectURL(response.data);
        // 将预览图像的 URL 保存到数据属性中
        this.previewImage = blobUrl;
        this.previewImages = [blobUrl];
        // 设置提示信息
        this.message = '预览图像已加载。';//显示message时，隐藏其他提示信息
        this.uploadMessage = '';
        this.errorMessage = '';

      } else if (contentType.includes('application/zip')) {
        // 处理.zip文件
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'images.zip'); // 或任何其他文件名
        document.body.appendChild(link);
        link.click();
        // 下载完成后，将链接删除，7.5
        document.body.removeChild(link);
        // 设置提示信息
        this.message = '文件已下载。';
        this.uploadMessage = '';
        this.errorMessage = '';

      } else if (contentType.includes('application/pdf')) {
        // 处理.pdf文件
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', 'images.pdf'); // 或任何其他文件名
        document.body.appendChild(link);
        link.click();
        // 下载完成后，将链接删除
        document.body.removeChild(link);
        // 设置提示信息
        this.message = '文件已下载。';
        this.uploadMessage = '';
        this.errorMessage = '';
      } else {
        // console.log(text);
        console.error(`Unexpected response type: ${contentType}, ${response.data}`);
      }
    },
    async generateHandwriting(preview = false, pdf_save = false) {
      // console.log('pdf_save', pdf_save)

      // 检查是否正在生成
      if (this.isGenerating) {
        this.$swal.fire({
          icon: 'warning',
          title: '正在生成中，请稍候...',
          showConfirmButton: false,
          timer: 2000,
        });
        return;
      }

      // 检查冷却时间
      const currentTime = Date.now();
      const timeSinceLastGenerate = currentTime - this.lastGenerateTime;
      if (timeSinceLastGenerate < this.generateCooldown) {
        const remainingTime = Math.ceil((this.generateCooldown - timeSinceLastGenerate) / 1000);
        this.$swal.fire({
          icon: 'warning',
          title: `请等待 ${remainingTime} 秒后再次生成`,
          showConfirmButton: false,
          timer: 2000,
        });
        return;
      }

      // 设置生成状态
      this.isGenerating = true;
      this.lastGenerateTime = currentTime;

      // 启动冷却时间定时器
      this.startCooldownTimer();

      try {
        // 检查是否为生产环境并进行页数限制
        if (!preview && this.isProductionSite()) {
          const estimatedPages = this.estimatePageCount();
          if (estimatedPages > 15) {
            const confirmed = await this.showPageLimitDialog(estimatedPages);
            if (!confirmed) {
              return; // 用户取消生成
            }
            // 用户确认继续，在前端截断文本到前15页
            this.truncateTextToPages(15);
          }
        }

      // 验证输入
      const Items = ['text', 'backgroundImage', 'fontSize', 'lineSpacing', 'marginTop', 'marginBottom', 'marginLeft', 'marginRight', 'lineSpacingSigma', 'fontSizeSigma', 'wordSpacingSigma', 'perturbXSigma', 'perturbYSigma', 'perturbThetaSigma', 'wordSpacing', 'strikethrough_length_sigma', 'strikethrough_angle_sigma', 'strikethrough_width_sigma', 'strikethrough_probability', 'strikethrough_width', 'ink_depth_sigma'];
      Items.forEach(item => {
        let value = this[item];
        // if (!value) {
        //   console.error(`Missing value for ${item}`);
        //   return;
        // }
        // 对不同的输入进行不同的验证
        switch (item) {
          case 'text':
            // 验证 text 是否是字符串
            if (typeof value !== 'string') {
              console.error(`Invalid value for ${item}`);
              this.errorMessage = '请输入字符串';
            }
            // return;
            break;
          case 'fontSize':
          case 'lineSpacing':
          case 'marginTop':
          case 'marginBottom':
          case 'marginLeft':
          case 'marginRight':
          case 'lineSpacingSigma':
          case 'fontSizeSigma':
          case 'wordSpacingSigma':
          case 'perturbXSigma':
          case 'perturbYSigma':
          case 'perturbThetaSigma':
          case 'wordSpacing':
          case 'strikethrough_length_sigma':
          case 'strikethrough_angle_sigma':
          case 'strikethrough_width_sigma':
          case 'strikethrough_probability':
          case 'strikethrough_width':
          case 'ink_depth_sigma':
            // 验证这些值是否是数字
            if (isNaN(Number(value))) {
              console.error(`Invalid value for ${item}`);
              this.errorMessage = '请输入数字';
            }
            // return
            break;
          case 'backgroundImage':
            // 验证 backgroundImage 是否是有效的 URL 或者文件路径
            // 这可能需要更复杂的验证
            break;
          default:
            console.error(`Unknown item: ${item}`);
        }
      });

      if (this.height < this.marginTop + this.lineSpacing + this.marginBottom && this.isDimensionSpecified) {
        this.errorMessage = '上边距、下边距和行间距之和不能大于高度';
        this.message = '';
        this.uploadMessage = '';
        return;
      }
      if (this.fontSize > this.lineSpacing) {
        this.errorMessage = '字体大小不能大于行间距';
        this.message = '';
        this.uploadMessage = '';
        return;
      }

      this.preview = preview;
      // this.pdf_save = pdf_save;
      // 设置提示信息为“内容正在上传…”
      this.uploadMessage = '内容正在上传并处理…（如果长时间没有响应说明服务器崩溃）单次请求最多处理五分钟，超过这个时间则失败';//显示上传提示信息时，隐藏其他提示信息
      console.log('内容正在上传并处理…');
      this.message = '';
      this.errorMessage = '';
      const formData = new FormData();
      formData.append("text", this.text);
      // 只有当用户选择的字体文件名与字体下拉选项中的字体文件名相同时，才上传字体文件7.5
      if (this.options[this.selectedOption - 1].text == this.selectedFontFileName) {
        formData.append("font_file", this.fontFile);
      }
      formData.append("background_image", this.backgroundImage);
      formData.append("font_size", this.fontSize);
      formData.append("line_spacing", this.lineSpacing);
      formData.append("fill", this.fill);
      if (this.width) {
        formData.append("width", this.width);
      }
      if (this.height) {
        formData.append("height", this.height);
      }
      formData.append("top_margin", this.marginTop);
      formData.append("bottom_margin", this.marginBottom);
      formData.append("left_margin", this.marginLeft);
      formData.append("right_margin", this.marginRight);
      formData.append("line_spacing_sigma", this.lineSpacingSigma);
      formData.append("font_size_sigma", this.fontSizeSigma);
      formData.append("word_spacing_sigma", this.wordSpacingSigma);
      formData.append("end_chars", this.endChars);
      formData.append("perturb_x_sigma", this.perturbXSigma);
      formData.append("perturb_y_sigma", this.perturbYSigma);
      formData.append("perturb_theta_sigma", this.perturbThetaSigma);
      formData.append("word_spacing", this.wordSpacing);
      formData.append("preview", this.preview.toString());
      formData.append("font_option", this.options[this.selectedOption - 1].text);
      formData.append("strikethrough_length_sigma", this.strikethrough_length_sigma);
      formData.append("strikethrough_angle_sigma", this.strikethrough_angle_sigma);
      formData.append("strikethrough_width_sigma", this.strikethrough_width_sigma);
      formData.append("strikethrough_probability", this.strikethrough_probability);
      formData.append("strikethrough_width", this.strikethrough_width);
      formData.append("ink_depth_sigma", this.ink_depth_sigma);
      formData.append("pdf_save", pdf_save.toString());
      formData.append("isUnderlined", this.isUnderlined.toString());
      formData.append("enableEnglishSpacing", this.enableEnglishSpacing.toString());
      
      // 根据环境与按钮决定是否启用多页预览
      const isDevEnv = process.env.NODE_ENV === 'development';
      const allowFullPreview = isDevEnv && this.enableFullPreview && preview;
      formData.append("full_preview", allowFullPreview.toString());

      for (let pair of formData.entries()) {
        console.log(pair[0] + ', ' + pair[1]);
      }

      const taskCreateResponse = await this.$http.post(
        '/api/generate_handwriting',
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
          withCredentials: true, //在跨域的时候，需要添加这句话，才能发送cookie 6.30
        }
      );

      const taskId = taskCreateResponse.data?.task_id;
      if (!taskId) {
        throw new Error('未获取到任务ID');
      }

      this.uploadMessage = `任务已提交，正在生成中（Task ID: ${taskId}）…`;
      try {
        await this.waitForTaskViaWebSocket(taskId);
      } catch (wsError) {
        console.warn('WebSocket不可用，降级为轮询模式', wsError);
        await this.pollGenerationTask(taskId);
      }

      const resultResponse = await this.$http.get(
        `/api/generate_handwriting/task/${taskId}/result`,
        {
          // 预览模式下：开发环境使用json接收多页图片，生产环境使用blob接收单页图片
          responseType: preview ? (allowFullPreview ? 'json' : 'blob') : 'blob',
          withCredentials: true,
        }
      );
      this.handleGenerationResultResponse(resultResponse);
      } catch (error) {
        if (error.response) {
          // ── 队列已满：503 queue_full ────────────────────────────────
          const errData = error.response.data;
          if (
            error.response.status === 503 &&
            errData?.status === 'queue_full'
          ) {
            const waitSec = errData.estimated_wait_seconds || 30;
            this.startQueueFullCountdown(waitSec);
            this.message = '';
            this.uploadMessage = '';
            this.errorMessage = '';
            return; // 不走通用错误展示
          }
          // ────────────────────────────────────────────────────────────
          // console.log('已进入报错处理程序')
          // 如果服务器返回了一个JSON错误消息
          if (error.response.data instanceof Blob) {
            let reader = new FileReader();
            reader.onload = (e) => {
              try {
                let errorData = JSON.parse(e.target.result);
                this.errorMessage = errorData.message;
              } catch (parseError) {
                // 如果解析失败，直接显示原始信息
                this.errorMessage = e.target.result;
                console.log('非JSON格式的错误数据：', e.target.result);
              }
              this.message = '';
              this.uploadMessage = '';
              console.log('错误信息：', this.errorMessage);
              console.log(error);
            };//注意，这里只能使用箭头函数，不然this指向全局对象window，6.30
            reader.readAsText(error.response.data);
          } else {
            this.errorMessage = error.response.data?.message || '生成失败，请稍后重试';
            // this.errorMessage = error.response.data.message;
            this.message = '';
            this.uploadMessage = '';
          }
        } else {
          // 如果没有从服务器收到响应
          this.errorMessage = error.message || '网络错误，请稍后再试';
          this.message = '';
          this.uploadMessage = '';
        }
      } finally {
        // 重置生成状态，但保持冷却状态
        this.isGenerating = false;
        // 冷却定时器会自动处理冷却状态的重置
      }
    },
    savePreset() {
      try {
        let data = {};
        this.localStorageItems.forEach(item => {
          data[item] = this[item];
        });
        // 将对象转换为 JSON 格式的字符串
        let dataString = JSON.stringify(data);

        // 将字符串存储到 localStorage 中
        localStorage.setItem('myPreset', dataString);

        this.$swal.fire({
          icon: 'success',
          title: '预设设置保存成功！',
          timer: 2000,
          showConfirmButton: false,
        });
      } catch (error) {
        console.error('保存预设设置失败:', error);
        this.$swal.fire({
          icon: 'error',
          title: '保存预设设置失败',
        });
      }
    },
    resetSettings() {
      // this.text = '';13213不能删除，会导致文字为空，但是输入框没有清除
      this.fontFile = null;
      this.backgroundImage = null;
      this.fontSize = 124;
      this.lineSpacing = 200;
      this.fill = "(0, 0, 0, 255)";
      this.width = 2481;
      this.height = 3507;
      this.marginTop = 50;
      this.marginBottom = 50;
      this.marginLeft = 50;
      this.marginRight = 50;
      this.lineSpacingSigma = 0;
      this.fontSizeSigma = 2;
      this.wordSpacingSigma = 2;
      this.perturbXSigma = 3;
      this.perturbYSigma = 3;
      this.perturbThetaSigma = 0.05;
      this.wordSpacing = 1;
      this.strikethrough_length_sigma = 2;
      this.strikethrough_angle_sigma = 2;
      this.strikethrough_width_sigma = 2;
      this.strikethrough_probability = 0.005;
      this.strikethrough_width = 8;
      this.ink_depth_sigma = 30;
      this.isUnderlined = true;
      this.enableEnglishSpacing = false;
      this.errorMessage = '';
      this.message = '';
      this.uploadMessage = '';
      this.selectedFontFileName = '';
      this.selectedImageFileName = '';
      this.selectedOption = '1';
      this.previewImage = "/default1.webp";
    },
    loadPreset() {
      try {
        // 从 localStorage 中获取字符串
        let dataString = localStorage.getItem('myPreset');

        if (dataString === null || dataString === "undefined") {
          this.$swal.fire({
            icon: 'info',
            title: '没有找到保存的预设设置',
          });
          return;
        }

        // 将字符串转换回对象
        let data = JSON.parse(dataString);
        Object.keys(data).forEach(item => {
          this[item] = data[item];
        });

        this.$swal.fire({
          icon: 'success',
          title: '预设设置加载成功！',
          timer: 2000,
          showConfirmButton: false,
        });
      } catch (error) {
        console.error('加载预设设置失败:', error);
        this.$swal.fire({
          icon: 'error',
          title: '加载预设设置失败，请检查保存的数据是否有效',
        });
      }
    },
    onBackgroundImageChange(event) {
      // 当用户选择了一个新的背景图片文件时，更新 selectedImageFileName，由于这边直接触发函数了，所以localstorage可以在这里修改，
      //之前因为文字不能触发函数，所以要放在watch里面
      this.selectedImageFileName = event.target.files[0].name;
      this.backgroundImage = event.target.files[0];
      // 由于文件无法在浏览器存储，所以下面的代码无效 7.15
      // localStorage.setItem('backgroundImage', JSON.stringify(this.backgroundImage));
      // if (localStorage.getItem('backgroundImage')) {
      //   console.log('Data successfully saved to localStorage.');
      // } else {
      //   console.log('Failed to save to localStorage.');
      // }

      this.previewImage = URL.createObjectURL(event.target.files[0]);
      Swal.fire({
        title: '你希望自动识别页面的四周边距吗？（尽量不要上传带有alpha透明通道的图片）',
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: '确定',
        cancelButtonText: '取消'
      }).then((result) => {
        if (result.isConfirmed) {
          let formData = new FormData();
          formData.append('file', this.backgroundImage);  // 'file' 是你在服务器端获取文件数据时的 key
          this.isLoading = true;
          this.$http.post(
            '/api/imagefileprocess',
            formData, {
            headers: {
              'Content-Type': 'multipart/form-data'
            }
          })
            .then(response => {
              this.marginLeft = response.data.marginLeft;
              this.marginRight = response.data.marginRight;
              this.marginTop = response.data.marginTop - this.lineSpacing;
              this.marginBottom = response.data.marginBottom;
              this.lineSpacing = response.data.lineSpacing;
              this.message = '背景图片已加载。';
              this.errorMessage = '';
              this.uploadMessage = '';
              this.isLoading = false;
            })
            .catch(error => {
              console.error(error);
              this.errorMessage = error.response.data.error;
              this.message = '';
              this.uploadMessage = '';
              this.isLoading = false;
            });
        }
      })
    },
    onFontChange(event) {
      // 当用户选择了一个新的字体文件时，更新 selectedFontFileName
      this.selectedFontFileName = event.target.files[0].name;
      this.fontFile = event.target.files[0];
      // 创建一个新的 option 对象
      const newOption = {
        value: String(this.options.length + 1), // 使用 options 数组的长度 + 1 作为新选项的 value
        text: this.selectedFontFileName // 使用字体文件名作为新选项的 text
      };

      // 将新选项添加到 options 数组中
      this.options.push(newOption);

      // 将 selectedOption 设为新选项的 value，这样下拉菜单就会自动更新为新添加的字体
      this.selectedOption = newOption.value;

    },
    triggerImageFileInput() {
      if (!this.isDimensionSpecified) {
        this.$refs.imageFileInput.click();
      }
      else {
        Swal.fire({
          title: '需要先清空高度宽度才能选择图片',
          text: '选择图片后需要点击按钮左下角的X删除图片才能再输入宽度高度',
          icon: 'question',
          showCancelButton: true,
          confirmButtonText: '清空宽度高度',
          cancelButtonText: '取消'
        }).then((result) => {
          if (result.isConfirmed) {
            this.width = null
            this.height = null
            this.$refs.imageFileInput.click();
          }
        })
      }
    },
    triggerFontFileInput() {
      this.$refs.fontFileInput.click();
    },
    //清空图像按钮对应的函数
    clearImage() {
      // 清空存储图像信息的变量
      this.selectedImageFileName = null;
      this.backgroundImage = null;
      // 清空文件输入框
      this.$refs.imageFileInput.value = null;
    },
    clearDimensions() {
      console.log('清空图像尺寸');
      this.width = null
      this.height = null
    },

    // 检查是否为生产网站
    isProductionSite() { // localhost:8080 handwrite.14790897.xyz
      return window.location.hostname === 'handwrite.14790897.xyz';
    },

    // 估算页数
    estimatePageCount() {
      if (!this.text || this.text.length === 0) {
        return 0;
      }

      // 获取页面参数
      const pageWidth = this.width || (this.backgroundImage ? 2481 : 2481); // 默认宽度
      const pageHeight = this.height || (this.backgroundImage ? 3507 : 3507); // 默认高度
      const fontSize = parseInt(this.fontSize) || 20;
      const lineSpacing = parseInt(this.lineSpacing) || 30;
      const marginTop = parseInt(this.marginTop) || 50;
      const marginBottom = parseInt(this.marginBottom) || 50;
      const marginLeft = parseInt(this.marginLeft) || 50;
      const marginRight = parseInt(this.marginRight) || 50;

      // 计算可用区域
      const usableWidth = pageWidth - marginLeft - marginRight;
      const usableHeight = pageHeight - marginTop - marginBottom;

      // 估算每行字符数（粗略估算，中文字符按字体大小计算）
      const avgCharWidth = fontSize * 0.8; // 中文字符宽度约为字体大小的0.8倍
      const charsPerLine = Math.floor(usableWidth / avgCharWidth);

      // 估算每页行数
      const linesPerPage = Math.floor(usableHeight / lineSpacing);

      // 估算每页字符数
      const charsPerPage = charsPerLine * linesPerPage;

      // 计算页数
      const estimatedPages = Math.ceil(this.text.length / charsPerPage);

      console.log('页数估算:', {
        textLength: this.text.length,
        charsPerLine,
        linesPerPage,
        charsPerPage,
        estimatedPages
      });

      return estimatedPages;
    },

    // 显示页数限制对话框
    async showPageLimitDialog(estimatedPages) {
      try {
        const result = await this.$swal.fire({
          title: '页数限制提醒',
          html: `
            <div style="text-align: left; line-height: 1.6;">
              <p><strong>检测到您的文本预计会生成 ${estimatedPages} 页</strong></p>
              <p>由于服务器资源限制，在 <strong>handwrite.14790897.xyz</strong> 网站上单次最多只能生成 <strong>10页</strong>。</p>
              <p>如果您选择继续：</p>
              <ul style="margin: 10px 0; padding-left: 20px;">
                <li>系统将只生成前 10 页内容</li>
                <li>超出部分将被自动截断</li>
                <li>建议您分批处理长文本</li>
              </ul>
              <p style="color: #666; font-size: 14px;">
                💡 提示：您可以将长文本分成多个部分，分别生成，或者自行搭建本项目来处理更长的文本
              </p>
              <p style="color: #888; font-size: 12px; margin-top: 10px;">
                注：此限制仅适用于 handwrite.14790897.xyz 网站
              </p>
            </div>
          `,
          icon: 'warning',
          showCancelButton: true,
          confirmButtonText: '继续生成（前10页）',
          cancelButtonText: '取消',
          confirmButtonColor: '#f39c12',
          cancelButtonColor: '#d33',
          width: '500px'
        });

        return result.isConfirmed;
      } catch (error) {
        console.error('SweetAlert2 error:', error);
        // 降级到原生 confirm
        return confirm(`检测到您的文本预计会生成 ${estimatedPages} 页。\n\n由于服务器资源限制，在 handwrite.14790897.xyz 网站上单次最多只能生成 10页。\n\n是否继续生成前10页？`);
      }
    },

    // 截断文本到指定页数
    truncateTextToPages(maxPages) {
      if (!this.text || this.text.length === 0) {
        return;
      }

      // 获取页面参数
      const pageWidth = this.width || (this.backgroundImage ?2481 : 2481); // 默认宽度
      const pageHeight = this.height || (this.backgroundImage ? 3507 : 3507); // 默认高度
      const fontSize = parseInt(this.fontSize) || 20;
      const lineSpacing = parseInt(this.lineSpacing) || 30;
      const marginTop = parseInt(this.marginTop) || 50;
      const marginBottom = parseInt(this.marginBottom) || 50;
      const marginLeft = parseInt(this.marginLeft) || 50;
      const marginRight = parseInt(this.marginRight) || 50;

      // 计算可用区域
      const usableWidth = pageWidth - marginLeft - marginRight;
      const usableHeight = pageHeight - marginTop - marginBottom;

      // 估算每行字符数
      const avgCharWidth = fontSize * 0.8;
      const charsPerLine = Math.floor(usableWidth / avgCharWidth);

      // 估算每页行数
      const linesPerPage = Math.floor(usableHeight / lineSpacing);

      // 计算每页字符数
      const charsPerPage = charsPerLine * linesPerPage;

      // 计算最大字符数
      const maxChars = charsPerPage * maxPages;

      // 截断文本
      if (this.text.length > maxChars) {
        const originalLength = this.text.length;
        this.text = this.text.substring(0, maxChars);

        console.log('文本截断:', {
          originalLength,
          truncatedLength: this.text.length,
          maxPages,
          charsPerPage,
          maxChars
        });

      }
    },

    // 启动冷却时间定时器
    startCooldownTimer() {
      // 清除现有定时器
      if (this.cooldownTimer) {
        clearInterval(this.cooldownTimer);
      }

      // 设置初始冷却状态
      this.isInCooldownPeriod = true;
      this.remainingCooldown = Math.ceil(this.generateCooldown / 1000);

      // 启动新定时器，每1秒更新一次显示
      this.cooldownTimer = setInterval(() => {
        const currentTime = Date.now();
        const timeSinceLastGenerate = currentTime - this.lastGenerateTime;
        const remaining = this.generateCooldown - timeSinceLastGenerate;

        if (remaining <= 0) {
          // 冷却结束
          this.isInCooldownPeriod = false;
          this.remainingCooldown = 0;
          clearInterval(this.cooldownTimer);
          this.cooldownTimer = null;
        } else {
          // 更新剩余时间
          this.remainingCooldown = Math.ceil(remaining / 1000);
        }
      }, 1000);
    },

  },

  // 组件销毁时清理定时器
  beforeUnmount() {
    if (this.cooldownTimer) {
      clearInterval(this.cooldownTimer);
      this.cooldownTimer = null;
    }
  },

};
</script>


<style scoped>
.container {
  display: grid;
  grid-template-areas:
    "form image"
    "button image"
    "message image";
  grid-template-columns: 1fr 2fr;
}

#message {
  grid-area: message;
  padding: 20px;
  box-sizing: border-box;
  overflow: auto;
  /* box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1); */
}

#form {
  grid-area: form;
  flex: 1 0 300px;
  max-width: 650px;
  column-count: auto;
  column-width: 200px;
  column-gap: 1em;
  width: 80vw;
  padding: 20px;
  margin: 0 auto;
  box-sizing: border-box;
  overflow: auto;
  box-shadow: 0 -1px 5px rgba(0, 0, 0, 0.1);
}

#form label {
  margin-bottom: 10px;
}

#form input,
#form textarea {
  width: 50%;
  padding: 10px;
  border-radius: 5px;
  border: 1px solid #ddd;
  box-sizing: border-box;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}


/* 想让标签和输入在一行显示，但是没有用 7.14 */
.label-container {
  display: flex;
  /* justify-content: center; */
  align-items: center;
}
.buttons{
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}
.buttons button {
  grid-area: button;
  padding: 10px 10px;
  border-radius: 5px;
  border: none;
  background: #007BFF;
  color: white;
  cursor: pointer;
  transition: all 0.3s ease-in-out;
  font-weight: bold;
  /* 使文本更粗 */
  box-shadow: 2px 2px 4px rgba(0, 0, 0, 0.5);
  /* 添加阴影效果 */
  outline: none;
  /* 移除默认的焦点轮廓 */
  margin-right: 10px;
  /* 为每个按钮添加右边距 */
  margin-top: 10px;
}

.buttons button:last-child {
  margin-right: 0;
  /* 为最后一个按钮移除右边距，避免额外空间 */
}

.buttons button:hover {
  background: #0056b3;
  transform: scale(1.05);
  /* 悬停时按钮轻微放大 */
}

.buttons button:active {
  background: #003d73;
  /* 按下按钮时更改背景色 */
  transform: scale(0.95);
  /* 按下按钮时按钮轻微缩小 */
}

.buttons button:disabled {
  background: #cccccc;
  /* 禁用按钮时的背景色 */
  cursor: not-allowed;
  /* 禁用按钮时的鼠标样式 */
}


.preview {
  /* flex: 1; */
  padding: 20px;
  box-sizing: border-box;
  grid-area: image;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
  min-width: 100px;
  min-height: 200px;

}

.preview img {
  max-width: 100%;
  height: auto;
  object-fit: cover;
  position: sticky;
  top: 0;
}

input[type="number"],
input[type="text"],
input[type="file"] {
  transition: all 0.3s ease;
  /* 过渡效果 */
}

input[type="number"]:hover,
input[type="text"]:hover,
input[type="file"]:hover {
  transform: scale(1.05);
  /* 放大输入框 */
  box-shadow: 0px 0px 8px rgba(0, 0, 0, 0.3);
  /* 添加阴影效果 */
}

/* >>> .TextInput{ */
.container_file {
  display: flex;
  flex-direction: column;
  gap: 10px;
  max-width: 400px;
  margin: auto;
}

.container_file label {
  font-size: 1.2rem;
  font-weight: 500;
}

.container_file button {
  padding: 10px 5px;
  font-size: 0.9rem;
  color: white;
  background-color: #4285f4;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  margin: 0 auto;
}

.container_file button:disabled {
  background-color: grey;
}

.container_file span {
  /* display: block; */
  margin-top: 5px;
  font-size: 0.9rem;
  color: #444;
}

/* } */
.styled-select {
  padding: 10px;
  border: none;
  border-radius: 5px;
  color: white;
  background-color: #4285f4;
  font-size: 1rem;
  transition: all 0.3s ease-in-out;


}

.styled-select:hover {
  transform: scale(1.05);
  /* 放大输入框 */
  box-shadow: 0px 0px 8px rgba(0, 0, 0, 0.3);
}

.styled-select:focus {
  outline: none;
}

.button-container {
  display: flex;
  justify-content: space-around;
  position: relative;
}

.clear-button {
  position: relative;
  top: 5px;
  right: 5px;
  width: 12px;
  height: 12px;
  cursor: pointer;
}

.clear-button-line {
  position: absolute;
  left: 1px;
  width: 10px;
  height: 2px;
  background-color: #000;
}

.clear-button-line:first-child {
  top: 5px;
  transform: rotate(45deg);
}

.clear-button-line:last-child {
  top: 5px;
  transform: rotate(-45deg);
}

.font-selection {
  display: flex;
  justify-content: space-around;
}

.loader {
  border: 16px solid #f3f3f3;
  /* Light grey */
  border-top: 16px solid #3498db;
  /* Blue */
  border-radius: 50%;
  width: 120px;
  height: 120px;
  animation: spin 2s linear infinite;
  position: absolute;
  /* 设置动画为绝对定位 */
  top: 50%;
  /* 将动画定位在父元素的中心 */
  left: 50%;
  transform: translate(-50%, -50%);
  /* 用 transform 属性将动画元素的中心对准父元素的中心 */
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

.image-container {
  /* display: flex;
  justify-content: center;
  align-items: center; */
  position: relative;
  margin-bottom: 15px;
}

.close {
  border: none !important;
}

.button-disabled {
  background-color: #ccc !important;
  color: #666 !important;
  cursor: not-allowed !important;
}

.optionUnderline {
  margin: 0;
  padding: 0;
  width: 10px;
  padding: 0 !important;
  border-radius: 0 !important;
  border: none !important;
  box-shadow: none !important;
  box-sizing: content-box !important;
}

.optionEnglishSpacing {
  margin: 0;
  padding: 0;
  width: 10px;
  padding: 0 !important;
  border-radius: 0 !important;
  border: none !important;
  box-shadow: none !important;
  box-sizing: content-box !important;
}

.freeprompt {
  font-size: 0.8rem;
  color: #e70808;
  text-align: center;
  margin-top: 10px;
}
@media (max-width: 1000px) {
  .container {
    /* flex-direction: column; */
    grid-template-areas:
      "form"
      "button"
      "message"
      "image";
    grid-template-columns: 1fr;
  }

  #form,
  .preview {
    flex: 1 0 100%;
  }
}

/* 生成状态提示样式 */
.generation-status {
  margin: 15px 0;
  padding: 10px;
  border-radius: 5px;
  text-align: center;
  font-weight: bold;
  animation: pulse 2s infinite;
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

/* 队列已满提示 - 已迁移到 Swal Toast */

</style>
