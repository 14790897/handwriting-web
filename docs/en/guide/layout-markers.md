# Layout Markers

You can insert two kinds of marker into the text to control the layout. They affect the page
only and are **never rendered into the output image**.

## `---` forces a page break

A line containing nothing but three or more dashes starts the **following content on a new page**.

- The dashes must be alone on their line; dashes inside a line don't count.
- Leading or trailing spaces are fine.
- Three, four, or more dashes all work.

```text
Content of the first page
---
The second page starts here
```

## `>>>` right-aligns a line

A `>>>` at the **start of a line** pushes that line to the right — most useful for signatures
and dates. One optional space right after the marker is swallowed and does not become part
of the text.

```text
First paragraph.
Second paragraph.
>>>Zhang San
>>>July 26, 2026
```

`>>>` only **pushes the whole line right**. To line up the starting position of a signature and
a date precisely, [Chinese Letter Layout](chinese-letter.md) does a better job.

## Using both

```text
Dear Teacher,
　　Thank you for everything this term.
　　Best regards,
>>>Zhang San
>>>July 26, 2026
---
Attachment: transcript
```

This renders two pages: the letter and its signature on the first, the attachment note on the second.

!!! tip "Let the app insert them for you"
    Writing `>>>` by hand is only for precise control. Most of the time, clicking the
    "Letter Layout" button and letting it right-align the signature is enough.
