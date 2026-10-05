# FAQ

## Uploading a document says "doc文件暂不支持"

`.doc` is the old Word format and the backend does not handle it. **Save it as `.docx`** and
upload that.

The supported formats are `.docx`, `.pdf`, `.txt` and `.rtf`. `.doc` is offered by the file picker
but rejected by the server.

## I uploaded my own font but the output still uses the old one

Uploading the file is not enough — you also have to **select it in the font dropdown**. The file
is only sent to the backend when the selected name matches the uploaded filename.

Also make sure you uploaded a `.ttf`.

## Generation seems stuck

Most likely it is queued. Check two places:

- **Below the text area** — is there a "generating" message?
- **Top bar** — a wait countdown appears when the queue is full.

The backend handles a limited number of jobs at a time, so busy periods mean waiting. It could also
be the 3-second cooldown right after a previous run.

## Output got truncated partway

On `handwrite.14790897.xyz` a single run is capped at 10 pages and the rest is dropped. Split the
text into several runs, or [self-host](../self-hosting/docker.md) — a self-hosted instance has no cap.

## Width/height and background image can't both be set

They are mutually exclusive: give a width and height and you get generated paper; upload a background
image and it is used as the base. To switch, clear the other one first (the background image has an
✕ in its top-right corner).

## There are rules on the generated paper and I don't want them

Uncheck **"Add underline"**. Auto-generated paper obeys the same toggle — turn it off for plain white.

## Characters collide, or it looks too messy

See the "Tuning tips" section of [Parameters](parameters.md). The two most common cases:

- Characters overlapping → raise **Line Spacing** (it must exceed the font size).
- Too chaotic → lower **Perturb Theta Sigma**; it affects the impression the most.

## Letter layout deleted all my blank lines

That is by design — it removes every blank line and re-indents by two spaces per line.
"Undo layout" restores the previous state. Details in
[Chinese Letter Layout](chinese-letter.md).

## Can I use this commercially?

The **code** is MIT licensed — see [LICENSE](https://github.com/14790897/handwriting-web/blob/main/LICENSE).

**Fonts are a separate matter.** The fonts bundled in the repository and any fonts you upload each
carry their own licence, and whether you may use them commercially depends on that licence. Check the
licences of the files in `ttf_files/` yourself — do not assume they are MIT along with the code.

## Where do I ask questions?

- GitHub Issues: <https://github.com/14790897/handwriting-web/issues> — including error logs gets you
  a much faster answer.
- Telegram group: <https://t.me/+zFImOziSNullOTE1>
- There is also a feedback form on the site itself.
