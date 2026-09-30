# Brand spec for the workshops page

Extracted from **SR Brand Guidelines 2025** (client version, 11 June 2025), which is in this
folder as `S&R Brand Guidelines 2025 for client 20250611.pdf`. It is gitignored, so it exists
only on machines where someone has put it there. Page numbers refer to the PDF.

**The PDF governs (decided 2026-09-30).** This file is a summary. Where the two differ, the PDF
wins. Diverge only where the guide is silent or following it would cause a real problem, such
as readability, and record each divergence in `PROJECT_BRIEF.md` so it can go to Natalia.
Corrections from checking this file against the PDF on 2026-09-30 are marked **(corrected)**.

---

## Typography (guide p.18, given in px, so this is the web spec)

| Element | Font | Size |
|---|---|---|
| Heading 1 | Oswald **Bold** | 72px |
| Heading 2 | Oswald Regular | 36px |
| Heading 3 | Oswald Regular, ALL CAPS | 22px |
| Body | Roboto Regular | 18px |
| Body emphasis | Roboto Bold | 18px |
| Button text | Roboto **Bold** | 24px |

Both are Google Fonts, so they load cleanly:

```html
<link href="https://fonts.googleapis.com/css2?family=Oswald:wght@300;400;500;700&family=Roboto:wght@400;700&display=swap" rel="stylesheet">
```

Scale these down proportionally at phone width. 72px H1 needs to clamp.

## Color palette (guide p.12 to 13)

**Primary.** Usable freely in content, gradients and copy highlights.

| Name | Hex |
|---|---|
| Spring Green | `#C0D72F` |
| Cerulean | `#05ACBD` |
| Slate | `#58585A` |
| Key Lime | `#E2F46F` |
| Soft Cyan | `#8ADBE4` |

**Secondary.** Used sparingly, as accent.

| Name | Hex |
|---|---|
| Deep Teal | `#345C60` |
| Iron | `#39393D` |
| Violet (sic) | `#00A651` |
| New Leaf (sic) | `#0072BC` |

**(corrected)** The PDF names these two on p.13: the green `#00A651` is labelled "Violet" and
the blue `#0072BC` "New Leaf". The names look mislabelled. Worth raising with Natalia.

**Neutrals.** To balance the brights. The guide says these are the website shades.

| Name | Hex |
|---|---|
| Chalk | `#F9FAF0` |
| Powder Blue | `#EDFDFF` |
| Pastel Green | `#F8FFE2` |

## The workshop date gradient (guide p.21)

The guide specifies this for our exact use case:

> "Use this gradient to highlight date, time and place section in workshops, with text in white"

Horizontal, left to right, three stops, with **white text**.

**(corrected)** The stops, read from the gradient definition inside the PDF (page 21, a
three-stop axial shading in RGB), are:

```css
background: linear-gradient(90deg, #05AABC 0%, #008F23 50%, #BFD630 100%);
color: #FFFFFF;
```

This file used to give the middle stop as `#00A651`. It is `#008F23`, a darker green that is
not in the palette. The ends are within one step of Cerulean `#05ACBD` and Spring Green
`#C0D72F`.

Contrast of white text on it (WCAG):

| Point | Colour | White text |
|---|---|---|
| 0% | `#05AABC` | 2.8:1 |
| 50% | `#008F23` | 4.2:1 |
| 100% | `#BFD630` | 1.6:1 |

White clears 3:1 (the bar for large text) only from about 8% to 68% across, and never reaches
4.5:1 (the bar for body text).

**On the page (decided 2026-09-30):** the gradient trimmed to its 8%-68% span, with white
22px Roboto Bold text. A divergence from the guide, recorded in `PROJECT_BRIEF.md`:

```css
background: linear-gradient(90deg, #04A6A4 0%, #008F23 70%, #45A928 100%);
```

## Copy highlights (guide p.18)

Highlight phrases in body copy with a Key Lime `#E2F46F` background fill, or a Key Lime
underline. Use rarely.

## Logo (guide p.4 to 10)

- Full color on white. White version on dark backgrounds
- Minimum clear space is 50% of the logo's height on every side
- Never blur, add texture, add shadow, box it, or rearrange its elements

## Where the guide and the live site disagree

**Superseded 2026-09-30.** This used to say "match the live site". The rule is now that the
guide governs, so where they disagree the page follows the guide. The drift itself still goes
to Natalia.

| Element | Guide says | Live site does | Use |
|---|---|---|---|
| Buttons | Dark rectangle, white text (p.19 mockup) | Deep Teal `#345C60` pill, `border-radius: 300px`, white text | **Guide.** Iron `#39393D` rectangle, Roboto Bold 24px |
| Deep Teal role | Secondary, sparing accent | Main action color throughout | **Guide.** Sparing: links and button hover only |
| Body size | 18px | about 14px | **Guide.** 18px |

The p.19 mockup's button and heading colour is `#343131`, which is not a palette value. The
page uses the nearest palette colour, Iron `#39393D`.

The mockup also sets H1 in capitals (as does the p.18 sample), with dark headings on light
ground. The page follows both.

Other values sampled from the live site, for reference:

- Page background `#F9FAF0` (Chalk, which matches the guide's neutral)
- Button hover on the live site uses `#038A98`, close to but not exactly Cerulean `#05ACBD`.
  Prefer the brand value `#05ACBD`
- Headings Oswald, body Roboto, consistent with the guide

## Writing voice

From the S&R document style guide:

- Short, simple words. Anglo-Saxon roots preferred
- Short sentences. **Avoid em-dashes.** Use commas, or break into separate sentences
- Contractions are fine when natural
- Protected terms, keep as written: Lean, Agile, Outcomes, Sense & Respond, Assumptions,
  Hypotheses, AI Transformation, Transformation
- Headings do not use bold in long-form documents. On the web, follow the type scale above
