# 手写文字生成

把一段文字渲染成看起来像手写的图片 —— 选字体、调参数、排好版，导出 PNG 打包或 PDF。

- 在线使用：<https://handwrite.sixiangjia.de>
- 视频介绍：<https://www.bilibili.com/video/BV1DM4y1W7fp/>
- 电报讨论群：<https://t.me/+zFImOziSNullOTE1>

![生成效果](https://raw.githubusercontent.com/14790897/handwriting-web/main/image-generate.png)

## 能做什么

<div class="grid cards" markdown>

- **自定义字体**

    上传自己的 `.ttf` 字体，或者从服务器已安装的字体里选一个。

- **背景图片**

    上传自己的背景图；不带背景时，只要给出宽高就会自动生成一张带横线的稿纸。

- **参数可调**

    字号、行距、四边边距、下划线，加上字距/字号/行距的浮动、笔画的横向与纵向偏移、
    旋转角度、墨迹深度、涂改痕迹 —— 都可以逐个调。

- **排版标记**

    正文里用 `---` 强制分页，行首的 `>>>` 把这一行靠右（署名、日期用得上）。

- **中文书信排版**

    一键把文字整理成紧凑的中文书信：段落空两格、去掉段间空行、落款自动靠右。

- **导入文档**

    直接上传 `.docx` / `.pdf` / `.txt` / `.rtf`，自动提取正文，不用手打。

- **预览与导出**

    先在右侧预览，满意后再导出整页 PNG（打包成 zip）或合并成 PDF。

- **内置预设**

    「小字加下划线（云烟体）」一键套用一组调好的参数。

</div>

## 从这里开始

- 第一次用 → [快速上手](guide/getting-started.md)
- 想调出特定效果 → [参数详解](guide/parameters.md)
- 要用分页和右对齐 → [排版标记](guide/layout-markers.md)
- 想自己搭一个 → [Docker 部署](self-hosting/docker.md)
- 想改代码 → [本地开发](development.md)
