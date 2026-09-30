# Brand spec for the workshops page

Extracted from **SR Brand Guidelines 2025** (client version, 11 June 2025), cross-checked
against the live senseandrespond.co. Page numbers refer to the PDF.

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
| (green) | `#00A651` |
| (blue) | `#0072BC` |

**Neutrals.** To balance the brights. The guide says these are the website shades.

| Name | Hex |
|---|---|
| Chalk | `#F9FAF0` |
| Powder Blue | `#EDFDFF` |
| Pastel Green | `#F8FFE2` |

## The workshop date gradient (guide p.21)

The guide specifies this for our exact use case:

> "Use this gradient to highlight date, time and place section in workshops, with text in white"

Horizontal, left to right: Cerulean into green into Spring Green, with **white text**.

```css
background: linear-gradient(90deg, #05ACBD 0%, #00A651 50%, #C0D72F 100%);
color: #FFFFFF;
```

Use it for the date band on each workshop card. Check contrast at the lime end. White on
`#C0D72F` is weak, so consider stopping the gradient short of full Spring Green, or weighting
the text area toward the Cerulean side.

## Copy highlights (guide p.18)

Highlight phrases in body copy with a Key Lime `#E2F46F` background fill, or a Key Lime
underline. Use rarely.

## Logo (guide p.4 to 10)

- Full color on white. White version on dark backgrounds
- Minimum clear space is 50% of the logo's height on every side
- Never blur, add texture, add shadow, box it, or rearrange its elements

## Where the guide and the live site disagree

**Decision: match the live site.** Josh's call, so the new page doesn't read as a different
brand. Flag the drift to Natalia separately.

| Element | Guide says | Live site does | Use |
|---|---|---|---|
| Buttons | Iron `#39393D` rectangle | Deep Teal `#345C60` pill, `border-radius: 300px`, white text | **Live site** |
| Deep Teal role | Secondary, sparing accent | Main action color throughout | **Live site** |
| Body size | 18px | about 14px | **18px, per the guide** |

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
