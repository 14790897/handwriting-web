import unittest
from unittest.mock import call, patch

from app import apply_right_align, handwrite_with_page_breaks


class FakeFont:
    size = 20

    def getbbox(self, char):
        return (0, 0, 20, 20)


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
