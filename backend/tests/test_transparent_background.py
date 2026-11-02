import asyncio
import unittest
from unittest.mock import patch

import numpy as np
from handright import Template as HandrightTemplate
from PIL import Image

from app import GenerateHandwritingParams, create_notebook_image, generate_handwriting_impl


class TemplateCaptured(Exception):
    pass


class FakeFont:
    size = 24


def build_params(**overrides):
    values = dict(
        text="AB",
        font_size="24",
        line_spacing="30",
        fill="(0, 0, 0, 255)",
        left_margin="0",
        top_margin="0",
        right_margin="0",
        bottom_margin="0",
        word_spacing="0",
        line_spacing_sigma="0",
        font_size_sigma="0",
        word_spacing_sigma="0",
        perturb_x_sigma="0",
        perturb_y_sigma="0",
        perturb_theta_sigma="0",
        preview="true",
        width="60",
        height="120",
    )
    values.update(overrides)
    return GenerateHandwritingParams(**values)


def capture_template(params):
    captured = {}

    def capture(*args, **kwargs):
        captured["template"] = HandrightTemplate(*args, **kwargs)
        raise TemplateCaptured

    with (
        patch("app.psutil.cpu_percent", return_value=0),
        patch("app.ImageFont.truetype", return_value=FakeFont()),
        patch("app.Template", side_effect=capture),
        unittest.TestCase().assertRaises(TemplateCaptured),
    ):
        asyncio.run(
            generate_handwriting_impl(
                "http://localhost/", params, font_file=b"test-font"
            )
        )
    return captured["template"]


class TransparentBackgroundTest(unittest.TestCase):
    def test_transparent_export_uses_empty_rgba_canvas_with_opaque_ink(self):
        template = capture_template(build_params(transparent_background="true"))
        background = template.get_background()

        self.assertEqual(background.mode, "RGBA")
        # 纸张和横线都不该出现：整张画布 alpha 为 0
        self.assertEqual(np.array(background)[..., 3].max(), 0)
        # handright 按通道数推出的默认 fill 是 (0, 0, 0, 0)，笔画会看不见
        self.assertEqual(template.get_fill(), (0, 0, 0, 255))

    def test_default_export_keeps_white_rgb_paper(self):
        template = capture_template(build_params())
        background = template.get_background()

        self.assertEqual(background.mode, "RGB")
        self.assertEqual(background.getpixel((0, 0)), (255, 255, 255))
        self.assertEqual(template.get_fill(), (0, 0, 0))

    def test_notebook_image_stays_opaque_without_the_flag(self):
        opaque = create_notebook_image(60, 120, 30, 0, 0, 0, 0, 24, "true")
        self.assertEqual(opaque.mode, "RGB")

        transparent = create_notebook_image(
            60, 120, 30, 0, 0, 0, 0, 24, "true", transparent=True
        )
        self.assertEqual(transparent.mode, "RGBA")
        self.assertEqual(np.array(transparent)[..., 3].max(), 0)


if __name__ == "__main__":
    unittest.main()
