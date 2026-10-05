# Desktop App

If you would rather not use a browser, or want something that works offline, there is a desktop build.
It bundles the backend and frontend together — double-click and it runs, no network needed.

![Desktop app interface](../desktop-app-screenshot.png)

## Download

Go to the [Releases page](https://github.com/14790897/handwriting-web/releases), find the latest
version, and pick by system and chip:

| System | File |
|---|---|
| Windows | `.exe` installer (NSIS), or the portable exe |
| macOS (Apple Silicon) | `.dmg` |

!!! warning "Only Apple Silicon Mac builds are published"
    There is currently only an **arm64** macOS build; Intel Macs cannot install it.
    Windows builds are unaffected.

## macOS blocks it on first launch

The desktop build is **neither code-signed nor notarised** — there is no Apple Developer certificate in
the project. So macOS blocks it the first time you open it. On macOS 15 and later the warning may say the
file is **"damaged"** outright.

**That warning has two possible meanings — work out which one you are looking at:**

- Most of the time it is the **quarantine attribute**: macOS tags every downloaded file with it, and an
  unsigned app trips over it on first launch. The file itself is fine.
- It can also mean the file really is **corrupted, or has been tampered with**. Be especially wary of
  installers obtained from anywhere other than the official channel.

So **first confirm you downloaded the installer from this repository's
[Releases page](https://github.com/14790897/handwriting-web/releases)**. If the source checks out, use one
of the methods below to let it through. **If you cannot verify where it came from, do not bypass the
warning and do not open the app.**

Once confirmed, run this once in a terminal:

```shell
xattr -dr com.apple.quarantine /Applications/HandwritingWeb.app
```

Or go to System Settings → Privacy & Security and click **"Open Anyway"**.

Both of these tell macOS to stop blocking the app. They are necessary only because the project has no
Apple Developer certificate to sign and notarise the build — they do **not** mean the build is safe.
Hence the "verify the source first" step above is not boilerplate.

## How it differs from the web version

The features are identical; only these things differ:

- **No 10-page cap** — that limit applies only to `handwrite.14790897.xyz`. The desktop build runs on your
  own machine, so it is bounded by your hardware instead of an arbitrary page count.
- **No analytics** — Google Analytics, Microsoft Clarity, Sentry and the chat widget are not loaded.
- **No pandoc download** — `.docx` files are handled by `python-docx` when pandoc is absent.
- **No overload guard interference** — the CPU guard is relaxed so the app cannot rate-limit itself.

## Where your data lives

The task database, temporary files, logs and fonts live in the user data directory. Deleting it is
equivalent to a factory reset:

| System | Location |
|---|---|
| Windows | `%LOCALAPPDATA%\HandwritingWeb` |
| macOS | `~/Library/Application Support/HandwritingWeb` |

Roughly:

- `tasks.db` — the task queue (SQLite)
- `temp/` — rendered images
- `logs/` — logs
- fonts

## Building it yourself

The build must run **on the target platform** — PyInstaller cannot cross-compile, so Windows packages
can only be produced on Windows and macOS packages only on a Mac of the matching architecture.

```shell
bash desktop/build.sh                 # full build: frontend → backend executable → installer
bash desktop/build.sh --app-only      # Electron directory only, no installer
PYTHON=python bash desktop/build.sh   # pick the interpreter (used by CI)
```

Artifacts land in `desktop/build/`. For development, run `--app-only` first, then `npx electron .` from
`desktop/`.

Before changing anything desktop-related, read [`AGENTS.md`](https://github.com/14790897/handwriting-web/blob/main/AGENTS.md)
at the repository root — it documents the build-time encoding, signing and cross-site request protection
pitfalls that have already been hit. (It is written in Chinese.)
