# 项目名称

这是一个使用 Flask 开发的 API 服务，提供了一个手写生成和用户认证的后端服务器。用户可以输入文本并生成看起来像手写的图像。图像保存在数据库中，并可以通过一个 .zip 文件下载。

## 安装

1. 克隆项目到本地
```bash
git clone https://github.com/<username>/<repository>.git
```
2. 安装 Python 依赖库
```bash
pip install -r requirements.txt
```
3. 创建一个 `.env` 文件，包含如下内容（替换为你的实际值）：
```bash
HOST=<Your MySQL Host>
USERNAME=<Your MySQL Username>
PASSWORD=<Your MySQL Password>
DATABASE=<Your MySQL Database Name>
```

## 使用

1. 运行 Flask 应用程序
```bash
python app.py
```
2. 访问 `http://localhost:5000/api/generate_handwriting`，你可以提交一个 POST 请求生成手写字体图片。JSON 请求体应包含：
    - text: 要转化为手写的文本
    - preview: 如果为 `True`，则只生成预览版（400 字以内）的图片；如果为 `False`，则生成完整文本的图片
    - 其他参数请参考代码中 `generate_handwriting` 方法的定义
3. 访问 `http://localhost:5000/api/login`，你可以提交一个 POST 请求来登录。JSON 请求体应包含：
    - username: 用户名
    - password: 密码
4. 访问 `http://localhost:5000/api/register`，你可以提交一个 POST 请求来注册新用户。JSON 请求体应包含：
    - username: 用户名
    - password: 密码

注意：这个应用只提供 API，你需要自己创建前端页面来调用这些 API。

## 依赖

这个项目依赖于以下库：

- Flask
- Pillow
- handright
- MySQLdb
- python-dotenv

## 项目结构

- `app.py`: 应用程序的入口和主要代码文件
- `.env`: 存储环境变量的文件（例如，数据库凭证）。这个文件不应该包含在源代码管理中，你需要自己创建它。
- `requirements.txt`: 存储项目依赖的 Python 库

## 贡献

欢迎所有形式的贡献。如果你有任何问题或建议，请创建一个 issue。

## 许可证

该项目使用 MIT 许可证。