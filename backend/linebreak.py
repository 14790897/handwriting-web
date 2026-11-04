"""给 handright 渲染的文本做按词断行。

2026-10-25：handright 每次画字前判断笔位，逐字换行（``handright/_core.py``），
英文单词会被拆到两行；闭标点不在它的 ``end_chars`` 里时，还会落到行首。

这里的函数预先算好断行并插入显式换行，handright 会把换行当成硬换行。只处理
带空白的段落：没有空白的段落原样返回，纯中文继续交给 handright 自己换行，
行为不变。
"""

import unicodedata

# 2026-10-25：不能出现在行首的闭标点，与 handright 默认的 ``end_chars`` 一致。
CLOSING_PUNCTUATION = "，。》？；：’”】｝、！％）,.>?;:]}!%)′″℃℉"

_SPACES = " \t"


def is_wide(char):
    """判断是否为按单格排版的宽字符（中文及同类字符）。"""
    return unicodedata.east_asian_width(char) in ("W", "F")


def _tokenize(paragraph, advance):
    """把段落拆成 (类型, 文本, 宽度) 单元。

    宽字符各成一个单元，连续的窄字符（英文、数字、符号）合成整词，连续空格
    也自成一个单元。
    """
    tokens = []
    index = 0
    length = len(paragraph)
    while index < length:
        char = paragraph[index]
        if char in _SPACES:
            end = index
            while end < length and paragraph[end] in _SPACES:
                end += 1
            text = paragraph[index:end]
            tokens.append(("space", text, sum(advance(c) for c in text)))
            index = end
        elif is_wide(char):
            tokens.append(("char", char, advance(char)))
            index += 1
        else:
            end = index
            while (
                end < length
                and paragraph[end] not in _SPACES
                and not is_wide(paragraph[end])
            ):
                end += 1
            text = paragraph[index:end]
            tokens.append(("word", text, sum(advance(c) for c in text)))
            index = end
    return tokens


def _needs_wrapping(paragraph):
    """段落含空白时才需要按词断行。

    没有空白就没有需要保持完整的词，整段交给 handright，中文保持原来的断行。
    """
    return any(char in _SPACES for char in paragraph)


def _is_all_end_chars(text, end_chars):
    """整个 token 都是闭标点时才允许悬挂。

    2026-10-31：``.NET`` / ``!important`` / ``%s`` 这类词以闭标点开头但后面
    还有内容，不能把标点留在上一行、把剩下的字母扔到下一行。
    """
    return bool(text) and all(char in end_chars for char in text)


def _wrap_paragraph(
    paragraph,
    advance,
    max_width,
    end_chars,
    word_margin,
    drift_margin,
    stray_margin,
):
    if not _needs_wrapping(paragraph):
        return paragraph

    lines = []
    current = []
    x = 0.0
    glyph_count = 0
    after_break = False
    # 2026-10-25：空格超出边距时先不换行，等下一个词出现再决定，这样闭标点
    # 可以留在上一行，不会被空格挤到行首。
    pending_break = False

    def start_new_line():
        nonlocal x, glyph_count, after_break, pending_break
        while current and current[-1][0] == "space":
            current.pop()
        lines.append("".join(text for _, text in current))
        current.clear()
        x = 0.0
        glyph_count = 0
        after_break = True
        pending_break = False

    def shift(extra=0):
        # 2026-11-01：把待放单词自身的字数也算进漂移，否则大 sigma 下单词
        # 自己的字距扰动会把它推过上限。
        return (
            drift_margin(x, glyph_count + extra)
            if drift_margin is not None
            else 0.0
        )

    def line_limit():
        # 2026-10-31：stray_margin 留给 handright 随机涂改时多画的那个字。
        return max_width - shift() - stray_margin

    def keep_limit(extra=0):
        # 2026-10-31：留在当前行的单词也要给涂改留余量，否则涂改落在词里会把
        # 单词推过 handright 的上限、被拆开。
        return max_width - max(word_margin, shift(extra)) - stray_margin

    def word_limit(extra=0):
        # 2026-10-31：整词能否放在空行上；这里不扣 stray_margin，避免本来能
        # 独占一行的单词每次都被逐字拆开。
        return max_width - max(word_margin, shift(extra))

    def indent_only():
        return bool(current) and all(
            token_kind == "space" or chunk == "　"
            for token_kind, chunk in current
        )

    for kind, text, width in _tokenize(paragraph, advance):
        if kind == "space":
            if not current:
                # 2026-10-25：断行处产生的空格被断行本身吃掉，行首缩进保留。
                if after_break:
                    continue
                current.append((kind, text))
                x += width
                glyph_count += len(text)
                continue
            if x + width > line_limit():
                pending_break = True
                continue
            current.append((kind, text))
            x += width
            glyph_count += len(text)
            continue

        if kind == "word":
            if pending_break:
                # 2026-10-25：先看这个词是不是闭标点；是就悬挂在上一行，不是
                # 才真正换行。
                pending_break = False
                if _is_all_end_chars(text, end_chars):
                    current.append((kind, text))
                    x += width
                    glyph_count += len(text)
                    continue
                start_new_line()
            # 2026-10-25：单词必须整体放下，只有超长的单词才逐字拆开。
            if x + width <= keep_limit(len(text)):
                current.append((kind, text))
                x += width
                glyph_count += len(text)
                continue
            if current and not indent_only():
                # 2026-10-25：闭标点不能落到行首，即使悬挂到右边距外也留在
                # 当前行。
                if _is_all_end_chars(text, end_chars):
                    current.append((kind, text))
                    x += width
                    glyph_count += len(text)
                    continue
                start_new_line()
            if not indent_only() and width <= word_limit(len(text)):
                current.append((kind, text))
                x += width
                glyph_count += len(text)
                continue
            for char in text:
                # 2026-10-25：沿用 handright 对单个字的规则：笔位仍在上限内
                # 时才落字。2026-10-31：闭标点同样不提前断行，断点要算上
                # 随机扰动的累计漂移。2026-11-01：缩进本身超宽时先把它整行
                # 落下，保证后面的单词不被拆开（保整词优先于少一行缩进）。
                if current and x > line_limit() and char not in end_chars:
                    start_new_line()
                current.append(("char", char))
                x += advance(char)
                glyph_count += 1
            continue

        # 2026-10-25：宽字符在它前面断行；若它是可以悬挂到右边距外的闭标点，
        # 则不断行，避免落到行首。2026-10-31：留出随机扰动的漂移余量。
        if pending_break:
            pending_break = False
            if text in end_chars:
                current.append((kind, text))
                x += width
                glyph_count += 1
                continue
            start_new_line()
        if current and x > line_limit() and text not in end_chars:
            start_new_line()
        current.append((kind, text))
        x += width
        glyph_count += 1

    start_new_line()
    return "\n".join(lines)


def break_lines(
    text,
    advance,
    max_width,
    end_chars=CLOSING_PUNCTUATION,
    word_margin=0.0,
    drift_margin=None,
    stray_margin=0.0,
):
    """在 ``text`` 中插入显式换行。

    ``advance(char)`` 返回一个字的笔进宽度，``max_width`` 是可用宽度（页宽减
    去左右边距和一个字宽，与 handright 的上限一致）。``word_margin`` 用于在
    判断单词是否放得下时预留余量，供会扰动字距的调用方使用。
    ``drift_margin(x, count)`` 返回当前笔位和字数为 ``x`` / ``count`` 时应该
    预留的累计扰动余量。``stray_margin`` 是额外预留给 handright 随机涂改多画
    的那个字的宽度（2026-10-31 新增）。
    """
    if max_width <= 0:
        return text
    return "\n".join(
        _wrap_paragraph(
            paragraph,
            advance,
            max_width,
            end_chars,
            word_margin,
            drift_margin,
            stray_margin,
        )
        for paragraph in text.split("\n")
    )
