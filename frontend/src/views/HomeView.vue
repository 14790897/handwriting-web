<template>
  <div class="container">
    <!-- 错误消息以及提示信息 -->
    <div id="message">
      <div v-if="errorMessage" class="alert alert-danger" role="alert">
        {{ errorMessage }}
      </div>
      <div v-if="message" class="alert alert-info" role="alert">
        {{ message }}
      </div>
      <div v-if="uploadMessage" class="alert alert-info" role="alert">
        {{ uploadMessage }}
      </div>
    </div>

    <div id="form">
      <div class="container_file row">

        <div class="col">
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

          <div>
            <label>{{ $t('message.backgroundImageFile') }}:</label>
            <div class="button-container">
              <button @click="triggerImageFileInput" :disabled="isDimensionSpecified"
                :title="isDimensionSpecified ? $t('message.widthAndHeightSpecified') : ''">
                {{ $t('message.chooseFile') }}
                <div v-if="selectedImageFileName" class="clear-button" @click.stop="clearImage">
                  <div class="clear-button-line"></div>
                  <div class="clear-button-line"></div>
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


      <label>{{ $t('message.width') }}:
        <input type="number" v-model="width" :disabled="isBackgroundImageSpecified"
          :title="isBackgroundImageSpecified ? $t('message.backgroundImageSpecified') : ''" />
      </label>

      <label>{{ $t('message.height') }}:
        <input type="number" v-model="height" :disabled="isBackgroundImageSpecified"
          :title="isBackgroundImageSpecified ? $t('message.backgroundImageSpecified') : ''" />
      </label>

      <label>{{ $t('message.fontSize') }}:
        <input type="number" v-model="fontSize" />
      </label>

      <label>{{ $t('message.lineSpacing') }}:
        <input type="number" v-model="lineSpacing" />
      </label>

      <label>{{ $t('message.topMargin') }}:
        <input type="number" v-model="marginTop" />
      </label>

      <label>{{ $t('message.bottomMargin') }}:
        <input type="number" v-model="marginBottom" />
      </label>

      <label>{{ $t('message.leftMargin') }}:
        <input type="number" v-model="marginLeft" />
      </label>

      <label>{{ $t('message.rightMargin') }}:
        <input type="number" v-model="marginRight" />
      </label>

    </div>
    <div class="buttons">
      <button @click="generateHandwriting(preview = true)">{{ $t('message.preview') }}</button>
      <!-- <button @click="loadPreset">{{ $t('message.loadSettings') }}</button>
      <button @click="savePreset">{{ $t('message.saveSettings') }}</button> -->
      <button @click="generateHandwriting(preview = false)">{{ $t('message.generateFullHandwritingImage') }}</button>
    </div>
    <!-- 预览区 -->
    <div class="preview">
      <h2>{{ $t('message.preview') }}：</h2>
      <img :src="previewImage" alt="{{ $t('message.previewImage') }}" style="width: 600px;" />
    </div>

    <footer class="footer mt-auto py-3 bg-white">
      <div class="container text-center">
        <span class="text-black">© 2023 Liuweiqing</span>
        <a href="mailto:14790897abc@gmail.com" class="text-info">14790897abc@gmail.com</a>
        <span class="text-black">{{ $t('message.projectAddress') }}：</span>
        <a href="https://github.com/14790897/handwriting-web" class="text-info">GitHub</a>
      </div>
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
    TextInput
  },

  data() {
    return {
      text: "",
      fontFile: null,
      backgroundImage: null,
      fontSize: 24,
      lineSpacing: 50,
      fill: "(0, 0, 0, 255)",
      width: 600,
      height: 800,
      marginTop: 50,
      marginBottom: 50,
      marginLeft: 50,
      marginRight: 50,
      previewImage: "/default.png", // 添加一个新的数据属性来保存预览图片的 URL
      preview: false,
      lineSpacingSigma: 0,
      fontSizeSigma: 0,
      wordSpacingSigma: 0,
      endChars: '',
      perturbXSigma: 0,
      perturbYSigma: 0,
      perturbThetaSigma: 0,
      wordSpacing: 0,
      errorMessage: '',  // 错误消息
      message: '',  // 提示消息
      uploadMessage: '',  // 上传提示消息
      selectedFontFileName: '',
      selectedImageFileName: '',
      //字体下拉选框
      selectedOption: '1',  // 当前选中的选项
      options: '',  // 下拉选项
      isLoading: false, //7.6
    };
  },
  created() {
    //
    const localStorageItems = ['text', 'fontFile', 'backgroundImage', 'fontSize', 'lineSpacing', 'fill', 'width', 'height', 'marginTop', 'marginBottom', 'marginLeft', 'marginRight', 'selectedFontFileName', 'selectedImageFileName', 'selectedOption'];

    localStorageItems.forEach(item => {
      const value = localStorage.getItem(item);
      if (value !== null && value !== "undefined") {
        this[item] = JSON.parse(value);
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
    //vuex中的login_delete_message，下面使用watch监控这个值  7.13
    ...mapState(['login_delete_message']),
  },
  watch: {
    login_delete_message(newVal) {
      if (newVal) {
        this.errorMessage = '';
        // this.message = '';
        // this.uploadMessage = '';
        console.log('已进入watch，错误消息已经清空');
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
    backgroundImage: {
      handler(newVal) {
        localStorage.setItem('backgroundImage', JSON.stringify(newVal));
      },
      deep: true
    },
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
  },
  methods: {
    async generateHandwriting(preview = false) {
      // 验证输入
      if (this.height < this.marginTop + this.lineSpacing + this.marginBottom) {
        this.errorMessage = '上边距、下边距和行间距之和不能大于高度';
        this.message = '';
        this.uploadMessage = '';
        return;
      }
      this.preview = preview;
      // 设置提示信息为“内容正在上传…”
      this.uploadMessage = '内容正在上传并处理…';//显示上传提示信息时，隐藏其他提示信息
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
      formData.append("width", this.width);
      formData.append("height", this.height);
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

      for (let pair of formData.entries()) {
        console.log(pair[0] + ', ' + pair[1]);
      }

      this.$http.post(
        '/api/generate_handwriting',
        formData,
        {
          headers: {
            "Content-Type": "multipart/form-data",
          },
          responseType: 'blob', // 这里设置为'blob'
          withCredentials: true, //在跨域的时候，需要添加这句话，才能发送cookie 6.30
        }

      ).then((response) => {
        if (response.headers['content-type'] === 'image/png') {
          // 处理预览图像
          const blobUrl = URL.createObjectURL(response.data);
          // 将预览图像的 URL 保存到数据属性中
          this.previewImage = blobUrl;
          // 设置提示信息
          this.message = '预览图像已加载。';//显示message时，隐藏其他提示信息
          this.uploadMessage = '';
          this.errorMessage = '';

        } else if (response.headers['content-type'] === 'application/zip') {
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

        } else {
          console.error('Unexpected response type');
          // 设置错误消息
          this.errorMessage = '意外的响应类型';
          this.message = '';
          this.uploadMessage = '';
        }
      }).catch(error => {
        // console.error(error);
        if (error.response) {
          // console.log('已进入报错处理程序')
          // 如果服务器返回了一个JSON错误消息
          let reader = new FileReader();
          reader.onload = (e) => {
            let errorData = JSON.parse(e.target.result);
            this.errorMessage = errorData.message;
            this.message = '';
            this.uploadMessage = '';
            console.log('错误信息：', errorData.message);

          };//注意，这里只能使用箭头函数，不然this指向全局对象window，6.30
          reader.readAsText(error.response.data); // 修改这里
          console.log(error.response.data);
          // this.errorMessage = error.response.data.message;

        } else {
          // 如果没有从服务器收到响应
          this.errorMessage = '网络错误，请稍后再试';
          this.message = '';
          this.uploadMessage = '';
        }
      });
    },

    onBackgroundImageChange(event) {
      // 当用户选择了一个新的背景图片文件时，更新 selectedImageFileName，由于这边直接触发函数了，所以localstorage可以在这里修改，
      //之前因为文字不能触发函数，所以要放在watch里面
      this.selectedImageFileName = event.target.files[0].name;
      this.backgroundImage = event.target.files[0];
      this.previewImage = URL.createObjectURL(event.target.files[0]);
      Swal.fire({
        title: '你希望自动识别页面的四周边距吗？',
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
              this.marginTop = response.data.marginTop;
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
      this.$refs.imageFileInput.click();
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
  },

};
</script>


<style scoped>
.container {
  /* display: flex; */
  /* flex-wrap: wrap; */
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
  max-width: 800px;
  column-count: auto;
  column-width: 200px;
  column-gap: 1em;
  width: 80vw;
  padding: 20px;
  margin: 0 auto;
  box-sizing: border-box;
  overflow: auto;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

#form label {
  display: block;
  margin-bottom: 10px;
}

#form input,
#form textarea {
  width: 100%;
  padding: 10px;
  border-radius: 5px;
  border: 1px solid #ddd;
  box-sizing: border-box;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.buttons button {
  grid-area: button;
  padding: 10px 20px;
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
  margin-right: 60px;
  /* 为每个按钮添加右边距 */
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

  object-fit: cover
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
  padding: 10px 20px;
  font-size: 1rem;
  color: white;
  background-color: #4285f4;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

.container_file button:disabled {
  background-color: grey;
}

.container_file span {
  display: block;
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
  position: absolute;
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

@media (max-width: 1000px) {
  .container {
    /* flex-direction: column; */
    grid-template-areas:
      "message"
      "form"
      "button"
      "image";
    grid-template-columns: 1fr;
  }

  #form,
  .preview {
    flex: 1 0 100%;
  }
}
</style>
