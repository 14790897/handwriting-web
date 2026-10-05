# Getting Started

## The whole flow

1. **Enter text** — type into the middle text box, or click "Choose File" to upload a document.
2. **Pick a font** — choose one of the server's fonts, or upload your own `.ttf`.
3. **Set the paper** — either give a width and height (the app generates ruled paper), or upload a background image.
4. **Tune parameters** — the defaults are fine to start with; see [Parameters](parameters.md) to fine-tune.
5. **Click "Preview Handwrite Image"** — the result appears on the right, with page navigation if there is more than one page.
6. **Export** — "Generate Full Handwriting Image" gives you a zip of PNGs; "Generate PDF" gives you a merged PDF.

!!! tip "Preview before you export"
    Previewing renders only the first page, so you can iterate on parameters quickly.
    Exporting renders every page. With long text, preview first to save time.

## The interface is three columns

The current layout splits the workspace in three, left to right:

- **Left · Settings** — font, paper, font size, line spacing, margins, and the jitter options under "More".
- **Middle · Text** — the text box, document upload, and the letter-layout button.
- **Right · Preview** — the rendered result and its page controls.

The left and right columns are resizable: drag the divider, or double-click it to restore
the default width. Your widths are remembered between visits.

Prefer the old look? The **"Old layout"** button in the top bar switches back. Both layouts
edit the same content, so you can switch back and forth freely.

## Entering text

!!! warning "`.doc` is not supported"
    The supported upload formats are `.docx`, `.pdf`, `.txt` and `.rtf`. The old `.doc`
    format appears in the file picker, but the server rejects it with
    "doc文件暂不支持" (`.doc` files are not supported yet). Re-save as `.docx` first.

- The text box keeps its contents across page reloads, as does the uploaded document.
- Uploading a document only **fills the text box** — you can keep editing afterwards.
- A page estimate shows below the text area. On `handwrite.14790897.xyz` a single run is
  capped at 10 pages, and the estimate warns you before you hit the truncation.

## Choosing a font

Two options, pick one:

- **Use a server font** — select it from the dropdown. These are the fonts placed in `ttf_files/` at deploy time.
- **Upload your own** — click "Choose File" and pick a `.ttf`. The file is only sent to the backend
  when the uploaded filename matches the one selected in the dropdown, so **remember to select it
  in the dropdown** after uploading.

## Setting the paper

Width/height and background image are **mutually exclusive**:

- Width + height given → the backend generates ruled paper (ruled or plain depends on "Add underline").
- Background image uploaded → your image is used, and width/height are disabled.

After uploading a background image you are asked whether to auto-detect margins. Answering yes
analyses the lines in the image and fills in all four margins and the line spacing — very handy
with your own ruled paper.

## Remembering your parameters

The three buttons in the top bar manage parameter snapshots, stored in your browser:

- **Save Settings** — store the current parameters.
- **Load Settings** — bring them back.
- **Reset Settings** — restore the defaults.

The "Built-in Preset" dropdown is a different thing: a ready-made parameter set. There is
currently one, **"Small with underlines (Yunyan)"**. It requires the `云烟体.ttf` font and
requires that no background image is set — if either is missing it tells you instead of
failing silently.

## Queueing and waiting

The backend only renders a limited number of jobs at a time. When it is busy you will see:

- A "generating" message and a cooldown countdown under the text area.
- A wait countdown in the top bar when the queue is full, telling you roughly how long.

Progress is pushed over a WebSocket; if that connection cannot be established the client
falls back to polling, and the interface looks the same either way.
