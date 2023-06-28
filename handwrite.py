from handright import Template, handwrite
from PIL import Image, ImageFont
import io

text = "Hello, World!"

# 创建一个字体对象，你可能需要选择正确的字体文件路径和大小
font = ImageFont.truetype("AdobeSongStd-Light.otf", 15)

template = Template(
    background=Image.new(mode="1", size=(100, 100), color=1),
    font=font,
    line_spacing=20,  # 行间距
    fill=(0),  # 填充颜色，黑色
    left_margin=10,  # 左边距
    top_margin=10,  # 上边距
    right_margin=10,  # 右边距
    bottom_margin=10,  # 下边距
    word_spacing=5,  # 字间距
    line_spacing_sigma=1,  # 行间距随机扰动
    font_size_sigma=1,  # 字体大小随机扰动
    word_spacing_sigma=1,  # 字间距随机扰动
    end_chars="，。",  # 防止特定字符因排版算法的自动换行而出现在行首
    perturb_x_sigma=1,  # 笔画横向偏移随机扰动
    perturb_y_sigma=1,  # 笔画纵向偏移随机扰动
    perturb_theta_sigma=0.1,  # 笔画旋转偏移随机扰动
)

images = handwrite(text, template)

for i, im in enumerate(images):
    assert isinstance(im, Image.Image)
    im.show()
    im.save(fp=io.BytesIO())
