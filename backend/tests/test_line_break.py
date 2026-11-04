import random
import unittest
from collections import defaultdict
from pathlib import Path
from unittest.mock import patch

from PIL import Image, ImageChops, ImageFont
import handright._core as handright_core
from handright import Template

from app import apply_word_wrap, handwrite_with_page_breaks
from linebreak import CLOSING_PUNCTUATION, break_lines


FONT_PATH = Path(__file__).resolve().parents[1] / "font_assets" / "青叶手写体.ttf"

PAGE_WIDTH = 600
PAGE_HEIGHT = 400
FONT_SIZE = 40
MARGIN = 20


def fixed_advance(char):
    return 10


def latin_template():
    return Template(
        background=Image.new("RGB", (PAGE_WIDTH, PAGE_HEIGHT), "white"),
        font=ImageFont.truetype(str(FONT_PATH), size=FONT_SIZE),
        line_spacing=60,
        left_margin=MARGIN,
        top_margin=MARGIN,
        right_margin=MARGIN,
        bottom_margin=MARGIN,
        word_spacing=0,
        line_spacing_sigma=0,
        font_size_sigma=0,
        word_spacing_sigma=0,
        perturb_x_sigma=0,
        perturb_y_sigma=0,
        perturb_theta_sigma=0,
        ink_depth_sigma=0,
    )


def font_advance(template):
    font = template.get_font()

    def advance(char):
        left, _, right, _ = font.getbbox(char)
        return (right - left) + template.get_word_spacing()

    return advance


def rendered_lines(text, template):
    """Line contents as handright lays them out, without rendering pixels."""
    positioned = []

    def record_flow_layout(draw, x, y, char, tpl, rand):
        positioned.append((round(y), char))
        left, _, right, _ = tpl.get_font().getbbox(char)
        return x + (right - left) + tpl.get_word_spacing()

    with patch.object(handright_core, "_flow_layout", record_flow_layout):
        list(handright_core._draft(text, (template,), seed=1))

    chars_by_line = defaultdict(list)
    for y, char in positioned:
        chars_by_line[y].append(char)
    return ["".join(chars_by_line[y]) for y in sorted(chars_by_line)]


def words_of(lines):
    return [word for line in lines for word in line.split()]


def drawn_lines(text, template, seed):
    """2026-10-31：按 handright 实际绘制口径分行，排除涂改功能随机插入的错字。"""
    positioned = []
    real_draw_char = handright_core._draw_char
    real_draw_strikethrough = handright_core._draw_strikethrough

    def record_draw_char(draw, char, xy, font):
        positioned.append([round(xy[1]), char])
        return real_draw_char(draw, char, xy, font)

    def record_strikethrough(draw, x, y, tpl, rand):
        # 2026-10-31：划线前画的那个字是 handright 随机抽中的“错字”，不属于正文
        if positioned:
            positioned[-1][1] = None
        return real_draw_strikethrough(draw, x, y, tpl, rand)

    # 2026-10-31：handright 的涂改位置用的是全局 random，不是 _draft 的 seed，
    # 单独钉住
    random.seed(seed)
    with (
        patch.object(handright_core, "_draw_char", record_draw_char),
        patch.object(handright_core, "_draw_strikethrough", record_strikethrough),
    ):
        list(handright_core._draft(text, (template,), seed=seed))

    chars_by_line = defaultdict(list)
    for y, char in positioned:
        if char is not None:
            chars_by_line[y].append(char)
    return ["".join(chars_by_line[y]) for y in sorted(chars_by_line)]


class WordBreakTest(unittest.TestCase):
    def test_english_words_are_not_split(self):
        text = "The quick brown fox jumps over the lazy dog"

        lines = break_lines(text, fixed_advance, 100).split("\n")

        self.assertGreater(len(lines), 1)
        self.assertEqual(words_of(lines), text.split())

    def test_closing_punctuation_never_starts_a_line(self):
        text = (
            "Hello, world. This is a test of the emergency broadcast system; "
            "it should wrap nicely! Also (this) part [works] fine, right?"
        )

        lines = break_lines(text, fixed_advance, 100).split("\n")

        self.assertGreater(len(lines), 1)
        for line in lines:
            self.assertNotIn(line[:1], CLOSING_PUNCTUATION)

    def test_punctuation_separated_by_a_space_stays_on_the_previous_line(self):
        text = "aaaaaaaaa , c"

        lines = break_lines(text, fixed_advance, 100).split("\n")

        self.assertEqual(lines[0], "aaaaaaaaa ,")
        for line in lines:
            self.assertFalse(line.startswith(","))

    def test_overlong_word_is_still_broken(self):
        text = "start " + "z" * 30 + " end"

        lines = break_lines(text, fixed_advance, 100).split("\n")

        self.assertEqual(
            lines,
            ["start", "z" * 11, "z" * 11, "z" * 8, "end"],
        )

    def test_cjk_punctuation_hangs_instead_of_starting_a_line(self):
        text = "中" * 10 + "，" + " tail"

        lines = break_lines(text, fixed_advance, 100).split("\n")

        self.assertEqual(lines, ["中" * 10 + "，", "tail"])

    def test_cjk_only_text_is_left_untouched(self):
        text = "这是一段用来测试换行的中文文字，标点符号不应该出现在行首，比如逗号。"

        self.assertEqual(break_lines(text, fixed_advance, 100), text)

    def test_existing_newlines_and_blank_lines_are_preserved(self):
        text = "hello world\n\nsecond paragraph here"

        lines = break_lines(text, fixed_advance, 100).split("\n")

        self.assertEqual(lines[0], "hello")
        self.assertEqual(lines[1], "world")
        self.assertEqual(lines[2], "")
        self.assertEqual(lines[3], "second")
        self.assertEqual(words_of(lines), text.split())

    def test_breaks_do_not_leave_leading_or_trailing_spaces(self):
        text = "aaaa bbbb cccc dddd eeee ffff"

        lines = break_lines(text, fixed_advance, 100).split("\n")

        for line in lines:
            self.assertEqual(line, line.strip())

    def test_leading_indentation_is_kept(self):
        text = "    中文 内容"

        self.assertEqual(break_lines(text, fixed_advance, 100), text)

    def test_first_line_indentation_survives_an_overflowing_first_word(self):
        text = "     aaaaaaaa b"

        lines = break_lines(text, fixed_advance, 100).split("\n")

        self.assertTrue(lines[0].startswith("     "))
        self.assertNotEqual(lines[0].strip(), "")

    def test_closing_punctuation_after_an_overflowing_space_stays_put(self):
        text = "aaaaaaaaa  , tail"

        lines = break_lines(text, fixed_advance, 100).split("\n")

        self.assertTrue(lines[0].endswith(","))
        for line in lines:
            self.assertFalse(line.startswith(","))

    def test_words_starting_with_punctuation_are_not_split(self):
        for text in (
            "alpha beta gamma delta .NET framework",
            "alpha beta gamma !important flag",
            "alpha beta gamma delta %s placeholder",
        ):
            lines = break_lines(text, fixed_advance, 100).split("\n")

            self.assertEqual(words_of(lines), text.split())

    def test_overlong_token_does_not_start_line_with_punctuation(self):
        text = "start " + "z" * 20 + ",z tail"

        lines = break_lines(text, fixed_advance, 100).split("\n")

        for line in lines:
            self.assertNotIn(line[:1], CLOSING_PUNCTUATION)

    def test_full_width_indent_before_an_overflowing_word_is_kept(self):
        text = "　　supercalifragilisticexpialidocious tail"

        lines = break_lines(text, fixed_advance, 100).split("\n")

        self.assertTrue(lines[0].startswith("　　"))
        self.assertNotEqual(lines[0].strip(), "")

    def test_overwide_indentation_keeps_the_following_word_whole(self):
        # 2026-11-01：缩进本身超过行宽时，先把缩进整行落下，优先保住整个词。
        lines = break_lines(" " * 40 + "word tail", fixed_advance, 100).split("\n")

        self.assertEqual(words_of(lines), ["word", "tail"])


class HandrightAgreementTest(unittest.TestCase):
    def test_cjk_breaks_inside_a_mixed_paragraph_match_handright(self):
        template = latin_template()
        text = (
            "这是一段用来测试换行的中文文字， "
            "The quick brown fox jumps over the lazy dog."
        )

        old_lines = rendered_lines(text, template)
        new_lines = break_lines(
            text,
            font_advance(template),
            PAGE_WIDTH - 2 * MARGIN - FONT_SIZE,
        ).split("\n")

        def cjk_only(lines):
            return [line for line in lines if not any(ord(c) < 128 for c in line)]

        self.assertEqual(cjk_only(new_lines), ["这是一段用来测试换行的中文文字，"])
        self.assertEqual(cjk_only(new_lines), cjk_only(old_lines))
        self.assertEqual(
            words_of(new_lines[1:]), "The quick brown fox jumps over the lazy dog.".split()
        )

    def test_rendered_lines_are_the_computed_lines(self):
        template = latin_template()
        text = (
            "The quick brown fox jumps over the lazy dog and keeps running "
            "through the field."
        )
        wrapped = apply_word_wrap(text, template)

        self.assertEqual(rendered_lines(wrapped, template), wrapped.split("\n"))
        for line in wrapped.split("\n"):
            self.assertNotIn(line[:1], CLOSING_PUNCTUATION)

    def test_mixed_cjk_layout_survives_default_randomness(self):
        # 2026-10-31：前端默认的随机扰动会逐字累积，宽字符断点必须留出余量，
        # 否则 handright 会把最后一字挪到下一行，再撞上这里插入的硬换行。
        template = Template(
            background=Image.new("RGB", (2481, 3507), "white"),
            font=ImageFont.truetype(str(FONT_PATH), size=124),
            line_spacing=200,
            left_margin=50,
            top_margin=50,
            right_margin=48,
            bottom_margin=50,
            word_spacing=1,
            line_spacing_sigma=0,
            font_size_sigma=2,
            word_spacing_sigma=2,
            perturb_x_sigma=0,
            perturb_y_sigma=0,
            perturb_theta_sigma=0,
            ink_depth_sigma=0,
            strikethrough_probability=0.005,
        )
        text = (
            "最近在整理一些手写字体相关的资料，发现英文单词在排版时经常被从中间截断，"
            "比如 handwriting 这个词会被拆成 hand 和 writing 两部分，看起来非常奇怪。"
        )
        wrapped = apply_word_wrap(text, template)
        expected = wrapped.split("\n")

        for seed in range(20):
            lines = drawn_lines(wrapped, template, seed)
            self.assertEqual(lines, expected)
            for line in lines:
                self.assertGreater(len(line.strip()), 1)


class ApplyWordWrapTest(unittest.TestCase):
    def test_cjk_text_is_left_untouched(self):
        template = latin_template()
        text = "这是一段用来测试换行的中文文字，标点符号不应该出现在行首，比如逗号。"

        self.assertEqual(apply_word_wrap(text, template), text)

    @patch("app.handwrite")
    def test_right_aligned_line_is_not_re_wrapped(self, handwrite_mock):
        # 2026-10-31：右对齐补的全角空格只保证最后一个字的起点在上限内，
        # 按词断行会把签名最后的 "W" 推到下一行，右对齐失效。
        handwrite_mock.side_effect = lambda text, _: [text]
        template = latin_template()

        list(handwrite_with_page_breaks("正文\n>>>Mary W", template))

        rendered = handwrite_mock.call_args.args[0]
        lines = rendered.split("\n")
        self.assertEqual(len(lines), 2)
        self.assertTrue(lines[1].startswith("　"))
        self.assertTrue(lines[1].endswith("Mary W"))

    @patch("app.handwrite")
    def test_page_breaks_are_applied_after_wrapping(self, handwrite_mock):
        handwrite_mock.side_effect = lambda text, _: [text]
        template = latin_template()
        text = "The quick brown fox jumps over the lazy dog\n---\nsecond page"

        list(handwrite_with_page_breaks(text, template))

        first_chunk = handwrite_mock.call_args_list[0].args[0]
        self.assertIn("\n", first_chunk)
        self.assertEqual(
            words_of(first_chunk.split("\n")),
            "The quick brown fox jumps over the lazy dog".split(),
        )
        self.assertEqual(handwrite_mock.call_args_list[1].args[0], "second page")

    @patch("app.apply_word_wrap")
    @patch("app.handwrite")
    def test_a_wrapped_marker_does_not_create_a_page_break(
        self, handwrite_mock, word_wrap_mock
    ):
        # 2026-10-25：先断行可能把段落末尾的 "---" 挤到单独一行，误命中分页
        # 标记。这里让断行故意输出这种结果，验证分页是在断行之前切的。
        word_wrap_mock.side_effect = lambda text, _, log=True: text.replace(
            " --- ", "\n---\n"
        )
        handwrite_mock.side_effect = lambda text, _: [text]
        template = latin_template()

        list(handwrite_with_page_breaks("word --- second", template))

        self.assertEqual(handwrite_mock.call_count, 1)


class RenderTest(unittest.TestCase):
    def test_wrapped_latin_text_renders_inside_the_canvas(self):
        template = latin_template()
        text = (
            "The quick brown fox jumps over the lazy dog and keeps running "
            "through the field."
        )

        images = list(handwrite_with_page_breaks(text, template))

        self.assertEqual(len(images), 1)
        image = images[0]
        self.assertEqual(image.size, (PAGE_WIDTH, PAGE_HEIGHT))
        ink = ImageChops.difference(image, Image.new("RGB", image.size, "white"))
        bbox = ink.getbbox()
        self.assertIsNotNone(bbox)
        left, top, right, bottom = bbox
        self.assertGreaterEqual(left, MARGIN - 2)
        self.assertGreaterEqual(top, MARGIN - 2)
        self.assertLessEqual(right, PAGE_WIDTH - MARGIN)
        self.assertLessEqual(bottom, PAGE_HEIGHT - MARGIN)


if __name__ == "__main__":
    unittest.main()
