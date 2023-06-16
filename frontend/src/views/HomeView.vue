<template>
  <div class="container">
  <div id="form">
    <div>
      <label>Text:
        <textarea v-model="text" placeholder="请输入要转换的文字"></textarea>
      </label>

      <label>Font File:
        <input type="file" @change="onFontChange" />
      </label>

      <label>Background Image File:
        <input type="file" @change="onBackgroundImageChange" />
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

      <label>Width:
        <input type="number" v-model="width" />
      </label>

      <label>Height:
        <input type="number" v-model="height" />
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

      <!-- More inputs for other parameters... -->
    </div>

  </div>
  <div class="buttons">
    <button @click="preview">预览</button>
    <button @click="export_file">导出</button>
    <button @click="save">保存</button>
    <button @click="loadPreset">载入预设</button>
    <button @click="generateHandwriting">生成手写图片</button>
  </div>
  <!-- 预览区 -->
      <div class="preview">
        <h2>预览：</h2>
        <img :src="previewImage" alt="预览图像" style="width: 600px;"/>
      </div>
  </div>
</template>

<script>
import axios from "axios";

export default {
  data() {
    return {
      text: "",
      fontPath: null,
      backgroundImage: null,
      font: null,
      fontSize: 24,
      lineSpacing: 100,
      fill: "(0, 0, 0, 255)",
      width: 600,
      height: 800,
      marginTop: 50,
      marginBottom: 50,
      marginLeft: 50,
      marginRight: 50,
      previewImage: "/default.png", // 添加一个新的数据属性来保存预览图片的 URL
      previeW: false,
      lineSpacingSigma: 0, // 默认值，可以根据实际需要更改
      fontSizeSigma: 0, // 默认值，可以根据实际需要更改
      wordSpacingSigma: 0, // 默认值，可以根据实际需要更改
      endChars: '', // 默认值，可以根据实际需要更改
      perturbXSigma: 0, // 默认值，可以根据实际需要更改
      perturbYSigma: 0, // 默认值，可以根据实际需要更改
      perturbThetaSigma: 0, // 默认值，可以根据实际需要更改
      wordSpacing: 0, // 默认值，可以根据实际需要更改

    };
  },
  methods: {
    selectFile(event) {
      this.fontPath = event.target.files[0];
    },
    async generateHandwriting() {
      try {
        const formData = new FormData();
        formData.append("text", this.text);
        formData.append("font_path", this.fontPath);
        formData.append("background_image", this.backgroundImage);
        formData.append("font_size", this.fontSize);
        formData.append("line_spacing", this.lineSpacing);
        formData.append("fill", this.fill);
        formData.append("width", this.width);
        formData.append("height", this.height);
        formData.append("top_margin", this.marginTop);
        formData.append("bottom_marginbottom", this.marginBottom);
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
        if (this.preview){
          formData.append("preview", this.preview);
        }

        const response = await axios.post(
          '/api/generate_handwriting',
          formData,
          {
            headers: {
              "Content-Type": "multipart/form-data",
            },
            responseType: 'blob', // 这里设置为'blob'
          }
        );

        if (response.headers['content-type'] === 'image/png') {
          // 处理预览图像
          const blobUrl = URL.createObjectURL(response.data);
          // 将预览图像的 URL 保存到数据属性中
          this.previewImage = blobUrl;

        } else if (response.headers['content-type'] === 'application/zip') {
          // 处理.zip文件
          const url = window.URL.createObjectURL(new Blob([response.data]));
          const link = document.createElement('a');
          link.href = url;
          link.setAttribute('download', 'images.zip'); // 或任何其他文件名
          document.body.appendChild(link);
          link.click();
        } else {
          console.error('Unexpected response type');
        }

      } catch (error) {
        console.error(error);
        // 处理出错情况，可能是显示一个错误消息给用户
      }
    },
    export_file() {
      // 实现你的导出逻辑...
    },
    save() {
      // 这个方法可以用来保存当前的参数设置
      // 这里我们将它们保存到 localStorage
      const settings = {
        text: this.text,
        // 注意，文件类型的参数（如 font 和 backgroundImage）不能保存
        fontSize: this.fontSize,
        lineSpacing: this.lineSpacing,
        fill: this.fill,
        width: this.width,
        height: this.height,
        marginTop: this.marginTop,
        marginBottom: this.marginBottom,
        marginLeft: this.marginLeft,
        marginRight: this.marginRight,
        backgroundImage: this.backgroundImage,
        font_path: this.font_path,
        // ...其他你希望保存的参数...
      };
       localStorage.setItem('handwriting-settings', JSON.stringify(settings));
    },
    loadPreset() {
      // 这个方法可以用来载入之前保存的参数设置
      const settingsJson = localStorage.getItem('handwriting-settings');
      if (settingsJson) {
        const settings = JSON.parse(settingsJson);
        this.text = settings.text;
        this.fontSize = settings.fontSize;
        this.lineSpacing = settings.lineSpacing;
         this.fill = settings.fill;
        this.width = settings.width;
        this.height = settings.height;
        this.marginTop = settings.marginTop;
        this.marginBottom = settings.marginBottom;
        this.marginLeft = settings.marginLeft;
        this.marginRight = settings.marginRight;
        this.backgroundImage = settings.backgroundImage;
        this.font_path = settings.font_path;
        // ...其他你希望载入的参数...
      } else {
        alert('没有找到保存的预设');
      }
    },
    onBackgroundImageChange(event) {
      this.backgroundImage = event.target.files[0];
    },
    onFontChange(event) {
      this.font = event.target.files[0];
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
}

.preview img {
  max-width: 100%;
  height: auto;
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
}
</style>
