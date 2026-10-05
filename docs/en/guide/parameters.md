# Parameters

There are two groups: the ones **visible in the left panel**, and the **jitter** settings
folded away under "More".

!!! info "What jitter is for"
    Handwriting looks handwritten because no two characters are identical. The backend adds a
    small random offset to every character, drawn from a normal distribution — the "sigma"
    parameters control the width of that distribution. **Bigger means messier; 0 means perfectly
    regular.** The defaults are already tuned to look natural, so don't change them all at once.

## Basic parameters

| Parameter | Default | Meaning |
|---|---:|---|
| Font Size | `124` | Character size in pixels. Bigger text means fewer characters per sheet. |
| Line Spacing | `200` | Baseline-to-baseline distance. Must exceed the font size or lines will overlap. |
| Top Margin | `50` | Distance from the text block to the top edge. |
| Bottom Margin | `50` | Distance to the bottom edge. |
| Left Margin | `50` | Distance to the left edge. |
| Right Margin | `50` | Distance to the right edge; `>>>` right-alignment measures from here too. |
| Word Spacing | `1` | Extra gap between characters. |
| Width | `2481` | Paper width. Mutually exclusive with a background image. |
| Height | `3507` | Paper height. Mutually exclusive with a background image. |

`2481 × 3507` is A4 at 300 DPI, and the defaults are sized around A4.

## Toggles

| Parameter | Default | Meaning |
|---|---|---|
| Add underline | on | Draws a rule under every line. Also decides whether auto-generated paper is ruled. |
| Auto-adjust English spacing | off | Widens the gaps between English words so they don't run together. Irrelevant for Chinese. |

## Jitter (under "More")

| Parameter | Default | Meaning |
|---|---:|---|
| Line Spacing Sigma | `0` | Variation in line spacing. Off by default. |
| Font Size Sigma | `2` | Variation in character size. |
| Word Spacing Sigma | `2` | Variation in the gap between characters. |
| Perturb X Sigma | `3` | Variation in each character's horizontal position. |
| Perturb Y Sigma | `3` | Variation in each character's vertical position. |
| Perturb Theta Sigma | `0.05` | Variation in each character's rotation, in radians. |
| Ink depth sigma | `30` | Variation in ink darkness, simulating heavier and lighter strokes. |

## Strikethroughs

Use these to leave a few "crossed out" marks on the page.

| Parameter | Default | Meaning |
|---|---:|---|
| Probability of a strikethrough occurring | `0.005` | Chance that any given character gets struck through. |
| Width of strikethrough | `8` | Thickness of the line. |
| Standard deviation of the strikethrough length | `2` | Variation in line length. |
| Standard deviation of the strikethrough width | `2` | Variation in line thickness. |
| Standard deviation of the strikethrough angle | `2` | Variation in line tilt. |

## Built-in preset

The "Built-in Preset" dropdown applies a complete tuned parameter set.

**Small with underlines (Yunyan)** — small text in the Yunyan font, generous line spacing and
margins, with underlines:

| Parameter | Preset | (Default for comparison) |
|---|---:|---|
| Font Size | `70` | 124 |
| Line Spacing | `100` | 200 |
| All four margins | `150` | 50 |
| Font Size Sigma | `1` | 2 |
| Line Spacing Sigma | `1` | 0 |
| Word Spacing | `2` | 1 |
| Perturb X Sigma | `1` | 3 |
| Perturb Y Sigma | `1` | 3 |
| Probability of a strikethrough occurring | `0` | 0.005 |
| Add underline | on | on |

The preset has two requirements: the `云烟体.ttf` font must be available, and there must be
**no background image** set. If either is unmet it tells you rather than failing quietly.

## Tuning tips

- **Characters are colliding** → raise Line Spacing or Word Spacing.
- **Looks too tidy to be handwriting** → raise Perturb X Sigma and Perturb Y Sigma.
- **Looks too chaotic** → lower Perturb Theta Sigma first; it affects the impression the most.
- **Want to fit more per page** → lower Font Size and Line Spacing, or shrink the paper.
- **Changed a parameter and nothing happened** → you have to click "Preview Handwrite Image"
  again. The preview does not re-render on its own.
