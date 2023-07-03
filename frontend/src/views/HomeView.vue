<template>
  <div class="container">
    <!-- 错误消息以及提示信息 -->
    <div v-if="errorMessage" class="alert alert-danger" role="alert">
      {{ errorMessage }}
    </div>
    <div v-if="message" class="alert alert-info" role="alert">
      {{ message }}
    </div>
    <div v-if="uploadMessage" class="alert alert-info" role="alert">
      {{ uploadMessage }}
    </div>

    <div id="form">
      <TextInput @childEvent="(eventData) => { this.text = eventData }"></TextInput>

      <label>Font File:
        <input type="file" @change="onFontChange" />
      </label>

      <label>Background Image File:
        <input type="file" @change="onBackgroundImageChange" :disabled="isDimensionSpecified"
          :title="isDimensionSpecified ? 'Width and height are already specified' : ''" />
      </label>

      <label>Width:
        <input type="number" v-model="width" :disabled="isBackgroundImageSpecified"
          :title="isBackgroundImageSpecified ? 'Background image is already specified' : ''" />
      </label>

      <label>Height:
        <input type="number" v-model="height" :disabled="isBackgroundImageSpecified"
          :title="isBackgroundImageSpecified ? 'Background image is already specified' : ''" />
      </label>

      <label>Font Size:
        <input type="number" v-model="fontSize" />
      </label>

      <label>Line Spacing:
        <input type="number" v-model="lineSpacing" />
      </label>

      <label>Fill Color (RGBA):
        <input type="text" v-model="fill" />
      </label>


      <label>Top Margin:
        <input type="number" v-model="marginTop" />
      </label>

      <label>Bottom Margin:
        <input type="number" v-model="marginBottom" />
      </label>

      <label>Left Margin:
        <input type="number" v-model="marginLeft" />
      </label>

      <label>Right Margin:
        <input type="number" v-model="marginRight" />
      </label>

    </div>
    <div class="buttons">
      <button @click="generateHandwriting(preview = true)">预览</button>
      <!-- <button @click="export_file">导出</button>
      <button @click="savePreset">保存</button>
      <button @click="loadPreset">载入预设</button> -->
      <button @click="generateHandwriting(preview = false)">生成手写图片</button>
    </div>
    <!-- 预览区 -->
    <div class="preview">
      <h2>预览：</h2>
      <img :src="previewImage" alt="预览图像" style="width: 600px;" />
    </div>
  </div>
</template>

<script>
// import mammoth from 'mammoth';
import TextInput from './TextInput.vue';
export default {
  props: {
    login_delete_message: {
      type: Boolean,
      default: false
    }
  },
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

    };
  },
  created() {
    const localStorageItems = ['text', 'fontFile', 'backgroundImage', 'fontSize', 'lineSpacing', 'fill', 'width', 'height', 'marginTop', 'marginBottom', 'marginLeft', 'marginRight'];

    localStorageItems.forEach(item => {
      this[item] = JSON.parse(localStorage.getItem(item)) || this[item];
    });
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
  },
  watch: {
    login_delete_message(newVal) {
      if (newVal) {
        this.errorMessage = '';
        // this.message = '';
        // this.uploadMessage = '';
        console.log('已进入watch');
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
  },
  methods: {
    async generateHandwriting(preview = false) {
      this.preview = preview;
      // 设置提示信息为“内容正在上传…”
      this.uploadMessage = '内容正在上传…';//显示上传提示信息时，隐藏其他提示信息
      console.log('内容正在上传…');
      this.message = '';
      this.errorMessage = '';
      const formData = new FormData();
      formData.append("text", this.text);
      formData.append("font_file", this.fontFile);
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
      this.backgroundImage = event.target.files[0];
    },
    onFontChange(event) {
      this.fontFile = event.target.files[0];
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
    "button image";
  grid-template-columns: 1fr 2fr;
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
  transition: background 0.3s;
}

.buttons button:hover {
  background: #0056b3;
}

.preview {
  /* flex: 1; */
  padding: 20px;
  box-sizing: border-box;
  grid-area: image;
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

.preview img {
  max-width: 100%;
  height: auto;
}

input[type="number"], input[type="text"], input[type="file"] {
  transition: all 0.3s ease; /* 过渡效果 */
}

input[type="number"]:hover, input[type="text"]:hover, input[type="file"]:hover {
  transform: scale(1.05);  /* 放大输入框 */
  box-shadow: 0px 0px 8px rgba(0, 0, 0, 0.3);  /* 添加阴影效果 */
}


@media (max-width: 800px) {
  .container {
    /* flex-direction: column; */
    grid-template-areas:
      "form"
      "button"
      "image";
    grid-template-columns: 1fr;
  }

  #form,
  .preview {
    flex: 1 0 100%;
  }
}</style>
