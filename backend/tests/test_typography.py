import asyncio
import unittest
from unittest.mock import patch

from handright import Template as HandrightTemplate
from PIL import Image

from app import GenerateHandwritingParams, generate_handwriting_impl


class TemplateCaptured(Exception):
    pass


class FakeFont:
    size = 24


class TypographyTest(unittest.TestCase):
    def test_app_preserves_handright_default_end_chars(self):
        params = GenerateHandwritingParams(
            text="A.) B",
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
        captured_template = None

        def capture_template(*args, **kwargs):
            nonlocal captured_template
            captured_template = HandrightTemplate(*args, **kwargs)
            raise TemplateCaptured

        with (
            patch("app.psutil.cpu_percent", return_value=0),
            patch(
                "app.create_notebook_image",
                return_value=Image.new("RGB", (60, 120), "white"),
            ),
            patch("app.ImageFont.truetype", return_value=FakeFont()),
            patch("app.Template", side_effect=capture_template),
            self.assertRaises(TemplateCaptured),
        ):
            asyncio.run(
                generate_handwriting_impl(
                    "http://localhost/",
                    params,
                    font_file=b"test-font",
                )
            )

        expected_end_chars = "，。》？；：’”】｝、！％）,.>?;:]}!%)′″℃℉"  # noqa: RUF001
        self.assertTrue(
            set(expected_end_chars).issubset(captured_template.get_end_chars())
        )


if __name__ == "__main__":
    unittest.main()
