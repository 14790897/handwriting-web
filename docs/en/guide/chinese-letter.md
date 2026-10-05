# Chinese Letter Layout

A Chinese letter has a conventional shape: the salutation starts flush left, each paragraph is
indented two characters, there are no blank lines between paragraphs, and the signature and date
sit on the right. Doing that by hand is tedious — the "Letter Layout" button does it in one go.

## How to use it

1. Write the letter body into the text box.
2. Click the **"Letter Layout"** button above the text box.
3. A dialog shows a layout preview. If the app recognised a signature and date at the end of the
   body, it fills them into the corresponding fields.
4. Edit "Signature" and "Date" if you need to. Both are optional.
5. Click **"Apply layout"** to write the result back into the text box. "Undo layout" restores
   what you had before.

Applying really does change the contents of the text box, and you can keep editing afterwards.

## What it actually changes

| Action | Detail |
|---|---|
| Removes blank lines | Every blank line in the body is deleted; paragraphs no longer have a gap between them. |
| Indents each line | Two full-width spaces are prepended to each line. |
| Keeps the salutation flush | If the first line ends with `：` or `:`, it is left unindented. |
| Right-aligns the ending | The signature and date each get a `>>>` and are right-aligned when rendered. |
| Preserves other markers | Existing `>>>` lines stay right-aligned; `---` page breaks are kept as-is. |

!!! note "It works line by line"
    The formatter treats **one line as one paragraph**. If a paragraph in your text is split across
    several hard-wrapped lines, each of those lines gets its own indent. For a clean two-space
    indent, keep one paragraph per line.

## Recognising the ending automatically

Before applying, the app looks at the last two lines of the body and tries to pull the ending out:

- **Date** — the last line is treated as a date if it looks like one. Recognised shapes include
  `2026年7月26日`, `2026-07-26`, `2026/7/26`, `7月26日` and `二〇二六年七月二十六日`.
- **Signature** — up to two lines above the date. Two to four Han characters, an English name,
  a form like "爱你的…" or "儿子/女儿/父亲/母亲…", or anything ending in "敬上" / "谨上" / "谨启"
  counts as a signature. Lines ending in punctuation such as a full stop, exclamation mark or
  colon do not.

If it got it right, just apply. If not, "Move back to body" puts it back, or you can fill it in yourself.

## Example

Before:

```text
尊敬的老师：
　　您好！这学期多谢您的照顾。
　　此致
敬礼！
张三
2026年7月26日
```

Choosing "Letter Layout", the app recognises `张三` as the signature and `2026年7月26日` as the
date, fills them in, and applying produces the equivalent of:

```text
尊敬的老师：
　　您好！这学期多谢您的照顾。
　　此致
　　敬礼！
>>>张三
>>>2026年7月26日
```

The last two lines are right-aligned when rendered. For `>>>` itself, see
[Layout Markers](layout-markers.md).
