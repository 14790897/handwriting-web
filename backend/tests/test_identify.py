import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

import numpy as np
from PIL import Image, ImageDraw

import identify as identify_module
from identify import _as_lines, identify_distance

# 与 e2e/fixtures/sample-page.png 同一套几何参数：那张图由下面这段逻辑生成，
# 改动这里时要同步重新生成，否则前后端两个用例盯的就不是同一份数据了。
PAGE_WIDTH, PAGE_HEIGHT = 800, 1000
MARGIN_LEFT = MARGIN_RIGHT = 60
MARGIN_TOP = MARGIN_BOTTOM = 80
STROKE_HEIGHT = 8
LINE_SPACING = 70
INK = (15, 15, 20)


# identify_distance 依赖 HoughLinesP 的直方图投票（threshold=100, minLineLength=100），
# 笔画必须连成足够长的水平线才会被认出来，所以合成图用整条通栏的长横，而不是零散的字块。
def synthetic_page(path):
    image = Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), "white")
    draw = ImageDraw.Draw(image)
    y = MARGIN_TOP
    while y + STROKE_HEIGHT < PAGE_HEIGHT - MARGIN_BOTTOM:
        draw.rectangle(
            [MARGIN_LEFT, y, PAGE_WIDTH - MARGIN_RIGHT, y + STROKE_HEIGHT],
            fill=INK,
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

    def test_degrades_to_zero_when_no_lines_are_detected(self):
        # 整页找不到直线时 HoughLinesP 返回 None，以前 sorted(None) 直接 TypeError，
        # /api/imagefileprocess 会变成 500 —— 用户传一张纯白图就会踩到。
        blank = os.path.join(self.workdir, "blank.png")
        Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), "white").save(blank)

        self.assertEqual(identify(blank), (0, 0, 0, 0, 0))

    def test_normalises_both_hough_lines_shapes(self):
        # opencv-python 4.x 返回 (N, 1, 4)，5.0 起返回 (N, 4)；下游只认后者
        ocv4 = np.array([[[10, 20, 30, 20]], [[10, 50, 30, 50]]])
        ocv5 = np.array([[10, 20, 30, 20], [10, 50, 30, 50]])

        for lines in (ocv4, ocv5):
            with self.subTest(shape=lines.shape):
                np.testing.assert_array_equal(_as_lines(lines), ocv5)

        self.assertEqual(_as_lines(None).shape, (0, 4))

    def test_reads_a_page_through_the_open_cv_5_line_shape(self):
        # 本机装的是 4.x，所以把真结果挤掉多出来的那一维，模拟 5.0 的形状。
        # 没有归一化的话，第一处 sorted(..., key=lambda x: x[0][1]) 就会
        # IndexError: invalid index to scalar variable，接口 500
        original = identify_module.cv2.HoughLinesP

        def flattened(*args, **kwargs):
            lines = original(*args, **kwargs)
            return None if lines is None else np.asarray(lines).reshape(-1, 4)

        with mock.patch.object(identify_module.cv2, "HoughLinesP", side_effect=flattened):
            left, right, top, _, _ = identify(self.page)

        self.assertAlmostEqual(left, MARGIN_LEFT, delta=4)
        self.assertAlmostEqual(right, MARGIN_RIGHT, delta=4)
        self.assertAlmostEqual(top, MARGIN_TOP, delta=4)


if __name__ == "__main__":
    unittest.main()
