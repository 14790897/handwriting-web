# 项目名称：手写文本生成器

这是一个使用 Flask 开发的 API 服务，它可以将任意用户提供的文本转换为手写样式的图片。服务包括用户注册、登录以及生成手写图像的功能。

## 主要功能

### 1. 生成手写图像
- `text`：需要转换为手写样式的文本。
- `background_image`：用于生成手写图片的背景图片。
- `font`：用于生成手写图像的字体。
- `font_size`：生成的手写文字的字体大小。
- `line_spacing`：行间距。
- `red`, `green`, `blue`：用于设置手写文字的颜色。
- `left_margin`, `top_margin`, `right_margin`, `bottom_margin`：设置手写图像的边距。
- `word_spacing`：字间距。
- `line_spacing_sigma`, `font_size_sigma`, `word_spacing_sigma`：用于在行间距、字体大小和字间距上添加随机扰动。
- `end_chars`：指定哪些字符不应出现在行首。
- `perturb_x_sigma`, `perturb_y_sigma`, `perturb_theta_sigma`：用于在笔画的横向偏移、纵向偏移和旋转偏移上添加随机扰动。

### 2. 用户注册和登录
用户可以通过访问 `register` 和 `login` 页面来注册新用户和登录已有用户。

## 使用方法

1. 用户首先需要注册一个新的用户账户。这可以通过向 `/api/register` 端点发送一个包含 `username` 和 `password` 参数的 POST 请求来完成。
2. 用户登录，通过向 `/api/login` 端点发送一个包含 `username` 和 `password` 参数的 POST 请求。
3. 用户可以向 `/api/generate_handwriting` 端点发送 POST 请求，提交要转化为手写的文本，以及相关的配置参数。如果请求成功，服务器会返回一个包含多张手写图像的 `.zip` 文件。

以上就是这个项目的主要功能和使用方法。