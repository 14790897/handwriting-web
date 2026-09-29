import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image

from pdf import PDF_JPEG_QUALITY, generate_pdf

# 写死期望值：跟着 PDF_JPEG_QUALITY 走的话，常量被改回高位时用例还是会过
EXPECTED_JPEG_QUALITY = 75


def _stroke_page(width=800, height=1100):
    """用细笔画模拟一页手写稿：线条走 JPEG 时不像纯色块那样一压就没。"""
    image = Image.new("RGB", (width, height), "white")
    pixels = image.load()
    for row in range(10, height - 10, 14):
        x = 20
        while x < width - 40:
            for offset in range(min(18, width - 40 - x)):
                for thickness in range(2):
                    pixels[x + offset, row + thickness] = (20, 20, 25)
            x += 24
    return image


class PdfExportTest(unittest.TestCase):
    def setUp(self):
        # generate_pdf 把临时文件写在当前工作目录的 ./temp 下
        self.original_cwd = os.getcwd()
        self.workdir = tempfile.mkdtemp()
        os.chdir(self.workdir)

    def tearDown(self):
        os.chdir(self.original_cwd)
        shutil.rmtree(self.workdir, ignore_errors=True)

    def test_pages_are_embedded_at_the_configured_quality(self):
        # 导出体积直接决定下载耗时，质量参数被调回高位时这条用例要拦住
        saved_qualities = []
        original_save = Image.Image.save

        def recording_save(self, fp, *args, **kwargs):
            saved_qualities.append(kwargs.get("quality"))
            return original_save(self, fp, *args, **kwargs)

        with patch.object(Image.Image, "save", recording_save):
            pdf_path = generate_pdf(images=[_stroke_page(), _stroke_page()])

        self.assertEqual(saved_qualities, [EXPECTED_JPEG_QUALITY] * 2)
        self.assertEqual(PDF_JPEG_QUALITY, EXPECTED_JPEG_QUALITY)

        with open(pdf_path, "rb") as handle:
            export = handle.read()
        self.assertTrue(export.startswith(b"%PDF-"))
        self.assertLess(len(export), 1_000_000)
