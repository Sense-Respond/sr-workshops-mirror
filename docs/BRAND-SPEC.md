# Brand spec for the workshops page

Extracted from **SR Brand Guidelines 2025** (client version, 11 June 2025), which is in this
folder as `S&R Brand Guidelines 2025 for client 20250611.pdf`. It is gitignored, so it exists
only on machines where someone has put it there. Page numbers refer to the PDF.

**The live site governs (decided 2026-10-01, design review with Natalia).** senseandrespond.co
is the design reference. Where it conflicts with the guide, follow the live site. The guide
still applies where the live site is silent. Natalia will update the guide to match the live
site. This reverses the 2026-09-30 rule that the PDF governs. The measured live values are in
"Live site values" at the top; the guide summary follows, for the gaps. Corrections from
checking this file against the PDF on 2026-09-30 are marked **(corrected)**.

Overall look: the three screenshots in `docs/reference/`. Exact values: the live CSS, below,
not the screenshots.

---

## Live site values (measured 2026-10-01)

Computed styles read in headless Chrome from senseandrespond.co (home and /individuals) at
390, 768, 1024 and 1440px wide. Squarespace scales type with the viewport: the root is 18px
from 1024px up and 16px below, and the theme sizes are rem multiples. The page uses
`clamp()`s fitted to the measured points.

**Type.** Oswald Regular (400) for every heading, sentence case, letter-spacing -0.02em.
Roboto for everything else, letter-spacing 0.01em.

| Element | Theme size | 1440px | 1024px | 390px | Line height |
|---|---|---|---|---|---|
| H1 | 4.5rem | 78.5px | 61.0px | 53.8px | 1.03 |
| H2 | 3.5rem | 61.2px | 48.7px | 43.0px | 1.08 |
| H3 | 2.5rem | 43.9px | | | 1.13 |
| H4 | 1.5rem | 26.6px | | | 1.18 |
| Body (Roboto 400) | 1.1rem | 19.7px | 19.2px | 17.1px | 1.6 |
| Small, nav, buttons | 0.9rem | 16.3px | 16.3px | 14.9px | |

The page uses the live H4 size for workshop titles, which are long.

**Colour.**

| Use | Value |
|---|---|
| Body and heading text | Black `#000000` |
| Eyebrow labels, secondary text | Slate `#58585A` |
| Primary buttons, links | Deep Teal `#345C60` (`hsl(185.45 29.73% 29.02%)`) |
| Some secondary buttons and links (e.g. "Meet Jeff and Josh") | `#038A98` |
| Text highlight | Key Lime `#E2F46F` (`hsl(68.24 86% 70%)`), marker style, 1em thick |
| Site background | Chalk `#F9FAF0`; most sections are white |

**Primary button** ("Explore Our Team Training"): background Deep Teal, white text, Roboto
600, 0.9rem, `text-transform: capitalize`, padding 18px 23.4px (16px 20.8px on phones),
`border-radius: 300px`, no border. Hover: `opacity: .8`, `transition: opacity .1s linear`.

**Text link** ("Upskill on your own →", Squarespace's tertiary button): Deep Teal, Roboto
600, 0.9rem, no underline, padding 3.6px 0. Hover: background Deep Teal, white text,
`transition: background-color .1s linear, color .1s linear`.

**Eyebrow** ("FLEXIBLE FORMATS", "INDIVIDUAL TRAINING"): Roboto Bold at body size, Slate,
typed in capitals.

**Header.** About 108px tall at 1440px. Logo 156x50px, left, at the 4vw gutter. Nav Roboto
400 0.9rem, black. Then a hero with a gradient background image.

**Cookie banner** (Squarespace's, measured for the page's own banner): fixed to the bottom,
full width, background Chalk `#F9FAF0`, padding 14px 20px, text and buttons spread apart.
Text Roboto 400, 14.5px (13.8px on phones), line height 1.6, black. Buttons Roboto 600
12px, padding 11px 15px: "Manage cookies" as a text button in `#038A98`, "Accept all" as a
Deep Teal pill, capitalized. On phones the buttons drop below the text. The page uses the
same styles with "Decline" in place of "Manage cookies".

**Layout.** Site max width 1400px. Gutter 4vw, 6vw on phones (under 768px).

**Not in the CSS.** The rounded cards on the live pages are Squarespace shape blocks, drawn as
SVG, so they have no radius to read. The page's 16px card radius is chosen to match ti.to's
cards (`srl_tito_reference.jpg`).

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

**Not used on the page since 2026-10-01.** The workshop date band is gone: date, time,
region and place are Slate text on white. Reason (Natalia): the courses use different
gradients. Kept as a record: from 2026-09-30 the page used the gradient trimmed to its 8%-68%
span, with white 22px Roboto Bold text:

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

**Since 2026-10-01: use the live site.** The full list, for Natalia's guide update, is the
"Brand divergences" table in `PROJECT_BRIEF.md`. The main ones:

| Element | Guide says | Live site does (and the page now does) |
|---|---|---|
| Buttons | Dark rectangle, Roboto Bold 24px (p.19 mockup) | Deep Teal `#345C60` pill, radius 300px, Roboto 600 0.9rem |
| Deep Teal role | Secondary, sparing accent | Main action colour throughout |
| H1 | Oswald Bold 72px, capitals | Oswald Regular 4.5rem (78.5px), sentence case |
| Body size | 18px | 1.1rem: 19.7px desktop, 17px phone. The "about 14px" noted in September was wrong |
| Text colour | `#343131` in the p.19 mockup | Black `#000000` |

History: 2026-09-18 said match the live site; 2026-09-30 said the guide governs; 2026-10-01
reverted to the live site.

## Writing voice

From the S&R document style guide:

- Short, simple words. Anglo-Saxon roots preferred
- Short sentences. **Avoid em-dashes.** Use commas, or break into separate sentences
- Contractions are fine when natural
- Protected terms, keep as written: Lean, Agile, Outcomes, Sense & Respond, Assumptions,
  Hypotheses, AI Transformation, Transformation
- Headings do not use bold in long-form documents. On the web, follow the type scale above
