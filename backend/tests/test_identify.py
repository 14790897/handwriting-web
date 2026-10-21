import contextlib
import io
import os
import tempfile
import unittest

from PIL import Image, ImageDraw

from identify import ImageIdentificationError, identify_distance

# 与 e2e/fixtures/sample-page.png 同一套几何参数：那张图由下面这段逻辑生成，
# 改动这里时要同步重新生成，否则前后端两个用例盯的就不是同一份数据了。
PAGE_WIDTH, PAGE_HEIGHT = 800, 1000
MARGIN_LEFT = MARGIN_RIGHT = 60
MARGIN_TOP = MARGIN_BOTTOM = 80
STROKE_HEIGHT = 8
LINE_SPACING = 70
INK = (15, 15, 20)
# 浅色纸：纸比墨线亮，但两者都远高于原来的固定阈值 150
LIGHT_PAPER = (235, 235, 235)
LIGHT_INK = (200, 200, 200)


# identify_distance 依赖 HoughLinesP 的直方图投票（threshold=100, minLineLength=100），
# 笔画必须连成足够长的水平线才会被认出来，所以合成图用整条通栏的长横，而不是零散的字块。
def synthetic_page(path, paper="white", ink=INK):
    image = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), paper)
    draw = ImageDraw.Draw(image)
    y = MARGIN_TOP
    while y + STROKE_HEIGHT < PAGE_HEIGHT - MARGIN_BOTTOM:
        draw.rectangle(
            [MARGIN_LEFT, y, PAGE_WIDTH - MARGIN_RIGHT, y + STROKE_HEIGHT],
            fill=ink,
        )
        y += LINE_SPACING
    image.save(path)
    return path


def identify(path):
    # 函数里有一大堆调试 print（含中文），测试期间静音，免得淹掉断言失败信息
    with contextlib.redirect_stdout(io.StringIO()):
        return identify_distance(path)


class IdentifyDistanceTest(unittest.TestCase):
    def setUp(self):
        self.workdir = tempfile.mkdtemp()
        self.page = synthetic_page(os.path.join(self.workdir, "page.png"))

    def test_reads_back_the_margins_the_page_was_drawn_with(self):
        left, right, top, bottom, _ = identify(self.page)

        # opencv-python 在 requirements 里没有钉版本，CI 装到的可能和本地不是同一个，
        # 形态学与 HoughLinesP 的结果会差一两个像素，所以留出容差
        self.assertAlmostEqual(left, MARGIN_LEFT, delta=4)
        self.assertAlmostEqual(right, MARGIN_RIGHT, delta=4)
        self.assertAlmostEqual(top, MARGIN_TOP, delta=4)

        # 下边距量的是「最后一条线到页面底部」，不是绘制时的 MARGIN_BOTTOM：
        # 行距摆不整齐时底部会多留一截（这里最后一行停在 858，余下 142）
        self.assertAlmostEqual(bottom, 142, delta=4)

    def test_returns_plain_ints_for_every_margin(self):
        # 返回值直接进 JSON 响应（/api/imagefileprocess），numpy 标量不能被序列化
        for value in identify(self.page):
            self.assertIsInstance(value, int)
            self.assertGreaterEqual(value, 0)

    @unittest.expectedFailure
    def test_line_spacing_is_the_walk_distance_not_the_stroke_thickness(self):
        # 已知缺陷：一横画在 Canny 后是上下两条边缘，相距约等于笔画高度（这里 9px），
        # 而 DBSCAN 取的是「最常见」的簇 —— 笔画厚度，不是 LINE_SPACING。
        # 前端拿它当 line_spacing 用，所以这个返回值偏小得离谱。
        # 修好了就把这条 expectedFailure 去掉。
        *_, line_spacing = identify(self.page)
        self.assertAlmostEqual(line_spacing, LINE_SPACING, delta=4)

    def test_a_light_page_is_identified_too(self):
        # 二值化原来用固定阈值 150，会把亮于 150 的像素整片抹掉 —— 浅灰纸上的浅灰横线
        # 一条都留不下来，HoughLinesP 返回 None。而「上传一张浅色纸」是很朴素的用法。
        # 改用 Otsu 之后这类页面能识别出和深色页一样的边距。
        light = synthetic_page(
            os.path.join(self.workdir, "light.png"), paper=LIGHT_PAPER, ink=LIGHT_INK
        )

        left, right, top, _, _ = identify(light)
        self.assertAlmostEqual(left, MARGIN_LEFT, delta=4)
        self.assertAlmostEqual(right, MARGIN_RIGHT, delta=4)
        self.assertAlmostEqual(top, MARGIN_TOP, delta=4)

    def test_a_page_without_detectable_lines_asks_for_manual_input(self):
        # 整页找不到直线时 HoughLinesP 返回 None。这里不能返回全 0：前端会把 0 当成
        # 真实边距去覆盖用户填好的参数，再弹一个假的成功提示。要抛出让调用方
        # 转成「请手动填写」的提示，用户原来的参数原样保留。
        blank = os.path.join(self.workdir, "blank.png")
        Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), "white").save(blank)

        with self.assertRaises(ImageIdentificationError):
            identify(blank)

    def test_an_undecodable_file_is_reported_instead_of_raising_cv2_error(self):
        # 扩展名是 .png 但内容不是图片时 imread 返回 None，紧接着的 cvtColor 会抛
        # cv2.error 变成 500。这种情况同样要变成可读的提示。
        broken = os.path.join(self.workdir, "broken.png")
        with open(broken, "wb") as handle:
            handle.write(b"this is not a png")

        with self.assertRaises(ImageIdentificationError):
            identify(broken)

    def test_a_gradient_without_ruled_lines_asks_for_manual_input(self):
        # Otsu 之后，没有横线的背景（渐变、照片）也可能被 Hough 捡到一两条伪线，
        # 但四周空白和行距一个样本都算不出来。这种页面同样不能退回全 0，
        # 否则前端会拿 0 覆盖用户已经填好的参数。
        gradient = os.path.join(self.workdir, "gradient.png")
        Image.linear_gradient("L").resize((PAGE_WIDTH, PAGE_HEIGHT)).convert("RGB").save(
            gradient
        )

        with self.assertRaises(ImageIdentificationError):
            identify(gradient)

    def test_a_page_with_a_single_line_asks_for_manual_input(self):
        # 只有一条线时量不出行距：Canny 给出这条线上下两条边缘，间距只有几像素，
        # 会被 distance > 5 的过滤条件丢掉，distances 为空。此时不能把 lineSpacing
        # 报成 0，否则前端会拿 0 覆盖用户设置（随后还会被「字体大小不能大于行间距」拦住）。
        one_line = os.path.join(self.workdir, "one-line.png")
        image = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), "white")
        ImageDraw.Draw(image).rectangle(
            [MARGIN_LEFT, 400, PAGE_WIDTH - MARGIN_RIGHT, 402], fill=INK
        )
        image.save(one_line)

        with self.assertRaises(ImageIdentificationError):
            identify(one_line)


if __name__ == "__main__":
    unittest.main()
