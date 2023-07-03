<template>
    <div id='text_file_select'>
        <label for="textArea">Text:</label>
        <textarea id="textArea" v-model="text_handwriting" placeholder="请输入要转换的文字"></textarea>

        <label for="textFileInput">Or upload a document file:</label>
        <button @click="triggerTextFileInput">Choose File</button>
        <span>{{ selectedTextFileName }}</span>
        <label>
            <input type="file" ref="textFileInput" @change="uploadFile" id="textFileInput"
                accept=".doc,.docx,.pdf,.txt,.rtf" style="display: none;" />
        </label>

        <div v-if="isLoading" class="loader">Loading...</div>
    </div>
</template>

<script>
export default {
    name: 'TextInput',

    data() {
        return {
            text_handwriting: '',
            isLoading: false,
            selectedTextFileName: '',
        }
    },
    created() {
        const localStorageItems = ['selectedTextFileName', 'text_handwriting']
        localStorageItems.forEach(item => {
            this[item] = JSON.parse(localStorage.getItem(item)) || this[item];
        });
    },
    methods: {
        uploadFile(e) {
            let file = e.target.files[0];
            // 当用户选择了一个新的文本文件时，更新 selectedTextFileName
            this.selectedTextFileName = e.target.files[0].name;
            // localStorage.setItem('textFile', JSON.stringify(this.textFile));
            localStorage.setItem('selectedTextFileName', JSON.stringify(this.selectedTextFileName));

            let formData = new FormData();

            formData.append('file', file);  // 'file' 是你在服务器端获取文件数据时的 key
            this.isLoading = true;
            this.$http.post(
                '/api/textfileprocess',
                formData, {

                headers: {
                    'Content-Type': 'multipart/form-data'
                }
            })
                .then(response => {
                    this.text_handwriting = response.data.text;
                    //通知HomeView更新text_handwriting 7.3
                    this.$emit('childEvent', this.text_handwriting);
                    localStorage.setItem('text_handwriting', JSON.stringify(this.text_handwriting));
                    this.isLoading = false;
                })
                .catch(error => {
                    console.error(error);
                    this.isLoading = false;
                });
        },
        triggerTextFileInput() {
            this.$refs.textFileInput.click();
        },
    },

}
</script>

<style scoped>
#text_file_select {
    position: relative;
    /* 设置父元素为相对定位 */
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
</style >