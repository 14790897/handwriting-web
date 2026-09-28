import unittest
from collections import defaultdict
from unittest.mock import call, patch

from PIL import Image
from handright import Template
import handright._core as handright_core

from app import apply_right_align, handwrite_with_page_breaks


class FakeFont:
    def __init__(self, size=20, glyph_width=20):
        self.size = size
        self.glyph_width = glyph_width

    def getbbox(self, char):
        width = self.size if char == "　" else self.glyph_width
        return (0, 0, width, self.size)


class FakeTemplate:
    def __init__(self, font=None):
        self.font = font or FakeFont()

    def get_font(self):
        return self.font

    def get_word_spacing(self):
        return 0

    def get_size(self):
        return (200, 300)

    def get_left_margin(self):
        return 20

    def get_right_margin(self):
        return 20


def draft_lines(text, template):
    positioned_chars = []

    def record_flow_layout(draw, x, y, char, tpl, rand):
        positioned_chars.append((round(y), char))
        left, _, right, _ = tpl.get_font().getbbox(char)
        return x + (right - left) + tpl.get_word_spacing()

    with patch.object(handright_core, "_flow_layout", record_flow_layout):
        list(handright_core._draft(text, (template,), seed=1))

    chars_by_line = defaultdict(list)
    for y, char in positioned_chars:
        chars_by_line[y].append(char)
    return ["".join(chars_by_line[y]) for y in sorted(chars_by_line)]


class TextLayoutTest(unittest.TestCase):
    def test_right_aligns_only_prefixed_lines_with_safety_margin(self):
        text = "正文\n>>> 签名\n正文里的 >>> 保持不变"

        self.assertEqual(
            apply_right_align(text, FakeTemplate()),
            "正文\n" + "　" * 5 + "签名\n正文里的 >>> 保持不变",
        )

    def test_right_align_strips_marker_when_content_is_too_wide(self):
        content = "这是明显超过可用宽度的一整行文字"

        self.assertEqual(
            apply_right_align(">>>" + content, FakeTemplate()),
            content,
        )

    def test_right_align_strips_marker_when_padding_has_no_advance(self):
        class ZeroSpaceFont(FakeFont):
            def getbbox(self, char):
                if char == "　":
                    return (0, 0, 0, 20)
                return super().getbbox(char)

        self.assertEqual(
            apply_right_align(">>> 签名", FakeTemplate(ZeroSpaceFont())),
            "签名",
        )

    def test_right_align_does_not_wrap_with_negative_word_spacing(self):
        font = FakeFont(size=50, glyph_width=20)
        template = Template(
            background=Image.new("RGB", (218, 160), "white"),
            font=font,
            line_spacing=60,
            left_margin=20,
            top_margin=10,
            right_margin=20,
            bottom_margin=10,
            word_spacing=-15,
            line_spacing_sigma=0,
            font_size_sigma=0,
            word_spacing_sigma=0,
            perturb_x_sigma=0,
            perturb_y_sigma=0,
            perturb_theta_sigma=0,
            ink_depth_sigma=0,
        )
        content = "July 27, 2026"

        lines = draft_lines(apply_right_align(">>>" + content, template), template)

        self.assertEqual([line.lstrip("　") for line in lines], [content])

    def test_right_align_handles_negative_character_advances(self):
        font = FakeFont(size=50, glyph_width=20)
        template = Template(
            background=Image.new("RGB", (218, 160), "white"),
            font=font,
            line_spacing=60,
            left_margin=20,
            top_margin=10,
            right_margin=20,
            bottom_margin=10,
            word_spacing=-24,
            line_spacing_sigma=0,
            font_size_sigma=0,
            word_spacing_sigma=0,
            perturb_x_sigma=0,
            perturb_y_sigma=0,
            perturb_theta_sigma=0,
            ink_depth_sigma=0,
        )
        content = "iiiiiiiiii"

        lines = draft_lines(apply_right_align(">>>" + content, template), template)

        self.assertEqual([line.lstrip("　") for line in lines], [content])

    @patch("app.handwrite")
    def test_manual_page_breaks_render_each_chunk(self, handwrite_mock):
        template = FakeTemplate()
        handwrite_mock.side_effect = lambda text, _: [text]

        pages = list(
            handwrite_with_page_breaks(
                "第一页\r\n \t--- \t\r\n第二页\r\n-----\r\n第三页",
                template,
            )
        )

        self.assertEqual(pages, ["第一页", "第二页", "第三页"])
        self.assertEqual(
            handwrite_mock.call_args_list,
            [
                call("第一页", template),
                call("第二页", template),
                call("第三页", template),
            ],
        )

    @patch("app.handwrite")
    def test_boundary_page_break_markers_are_not_rendered(self, handwrite_mock):
        template = FakeTemplate()
        handwrite_mock.side_effect = lambda text, _: [text]

        pages = list(handwrite_with_page_breaks("---\n正文\n---", template))

        self.assertEqual(pages, ["正文"])
        handwrite_mock.assert_called_once_with("正文", template)

    @patch("app.handwrite")
    def test_page_break_preserves_additional_blank_lines(self, handwrite_mock):
        template = FakeTemplate()
        handwrite_mock.side_effect = lambda text, _: [text]

        pages = list(
            handwrite_with_page_breaks(
                "第一页尾部\n\n---\n\n第二页顶部",
                template,
            )
        )

        self.assertEqual(pages, ["第一页尾部\n", "\n第二页顶部"])
        self.assertEqual(
            handwrite_mock.call_args_list,
            [
                call("第一页尾部\n", template),
                call("\n第二页顶部", template),
            ],
        )

    @patch("app.handwrite")
    def test_inline_dashes_remain_plain_text(self, handwrite_mock):
        template = FakeTemplate()
        rendered = object()
        handwrite_mock.return_value = rendered

        text = "正文---仍在本页\r\n--\r\n---后面有正文\r\n下一行"
        result = handwrite_with_page_breaks(text, template)

        self.assertIs(result, rendered)
        handwrite_mock.assert_called_once_with(
            "正文---仍在本页\n--\n---后面有正文\n下一行",
            template,
        )


if __name__ == "__main__":
    unittest.main()
