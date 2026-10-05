# Preview & Export

## Preview

Click **"Preview Handwrite Image"** in the top bar and the result appears in the right column.

- **Preview renders only the first page** — the point is to check your parameters fast without
  waiting for the whole document.
- When the text runs to several pages, page controls appear below the preview: "Previous",
  "Next", and "Page x / y".
- After changing any parameter you must **click preview again**. The preview does not re-render
  on its own.

## Exporting images (zip)

Click **"Generate Full Handwriting Image"** and the backend renders every page to PNG and packages
them as `images.zip`.

- The archive contains one PNG per page, in order.
- This is the most direct way to get all the pages — useful if you want to lay them out yourself
  or drop them into another document.

## Exporting a PDF

Click **"Generate PDF"** and the backend merges every page into a single `images.pdf`. No more
pasting images into a document by hand.

!!! tip "Which one?"
    Inserting into Word, or controlling page order yourself → **zip**.
    A file you can print or send as-is → **PDF**.

## Page count and limits

- A **page estimate** appears below the text area, so you can see roughly how many pages you are
  heading for while you type.
- On `handwrite.14790897.xyz` a single run renders **at most 10 pages**; anything beyond that is
  truncated. Both the estimate and an over-limit dialog warn you in advance. A self-hosted instance
  has no such cap, but it is still subject to
  [resource limits](../self-hosting/fonts-and-limits.md).

## Queueing, cooldowns and failures

- **Cooldown** — 3 seconds between runs, with a countdown on the button.
- **Queueing** — the backend handles a limited number of jobs at once. When the queue is full a
  wait countdown appears, telling you roughly how long.
- **Progress** — generation state is pushed over a WebSocket; if that fails the client falls back
  to polling, and the interface looks the same.
- **Failures** — if rendering errors out, the task ends as failed with an error message.
  On a self-hosted instance the details are in the container logs:

  ```shell
  docker compose logs backend
  ```
