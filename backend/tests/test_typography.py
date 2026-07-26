import unittest
from collections import defaultdict
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageFont
from handright import Template
import handright._core as handright_core


def _draft_lines(text):
    font_path = Path(__file__).parents[1] / "font_assets" / "李国夫手写体.ttf"
    font = ImageFont.truetype(str(font_path), 24)
    positioned_chars = []
    original_flow_layout = handright_core._flow_layout

    def record_flow_layout(draw, x, y, char, template, rand):
        positioned_chars.append((round(y), char))
        return original_flow_layout(draw, x, y, char, template, rand)

    template = Template(
        background=Image.new("RGB", (60, 120), "white"),
        font=font,
        line_spacing=30,
        word_spacing=0,
        line_spacing_sigma=0,
        font_size_sigma=0,
        word_spacing_sigma=0,
        perturb_x_sigma=0,
        perturb_y_sigma=0,
        perturb_theta_sigma=0,
        ink_depth_sigma=0,
    )

    with patch.object(handright_core, "_flow_layout", record_flow_layout):
        list(handright_core._draft(text, (template,), seed=1))

    chars_by_line = defaultdict(list)
    for y, char in positioned_chars:
        chars_by_line[y].append(char)
    return ["".join(chars) for chars in chars_by_line.values()]


class TypographyTest(unittest.TestCase):
    def test_closing_punctuation_does_not_start_a_line(self):
        for punctuation in "，。！？；：、）》】’”,.>?;:]}!%)′″℃℉":
            with self.subTest(punctuation=punctuation):
                self.assertEqual(
                    _draft_lines(f"丁。{punctuation}后文"),
                    [f"丁。{punctuation}", "后文"],
                )
