# ValueWise SI house style (v3)

SeedFactory's screens, dashboard and charts follow this house style from change request CR-3 (2026-10-05, D-96 to D-102). Part 1 is the guide as the stakeholder gave it. Part 2 is how SeedFactory applies it, including the tokens `frontend/src/styles/tokens.css` must hold (read by `frontend/tests/contrast.spec.ts`) and the few places SeedFactory departs from it, each with its reason.

The mood board: [valuewise-mood-board.png](valuewise-mood-board.png).

---

## Part 1. The guide (verbatim)

ValueWise SI house style v3

### 1\. Colour has a job

* Red, amber and green are reserved for meaningful analytical messages: a measured value against its target, a status that comes out of the data, a verdict (Met, Partly, Not met; Keep, Fix, Cut), a score tile. If a reader cannot ask "measured against what?" and get an answer, the element does not get a band colour.
* Never on buttons, tabs, toggles, navigation, section markers, bullets, dividers or decoration. Controls are neutral: white outline, white fill with navy text, or navy fill with #244A7A border. A pressed control is a neutral inversion, never a band colour.
* Gold (#F2D27A dark, #B8962E light) is the extra special accent, used sparingly: the key number the room must read first (one per slide at most), the word "Value" in the wordmark, and bracket placeholders the bid team must fill (\[figure], \[Name]). Not for headings, not for emphasis in body text, not for lines or borders.
* Link blue (#4DA3FF dark, #0B5FD6 light) only on things that open or act.
* Everything else is navy, white and the two greys. If a slide needs more than that, the message is unclear, not the palette.

### 2\. Dark theme (default, matches the dashboard)

* Background: #020921 (near-black navy)
* Panel / tooltip: #15335C
* Panel border: #244A7A
* Primary text: #FFFFFF; secondary text: #B8C0D4; muted labels: #8A93A8
* Accent (gold, for headline figures like "WR"): #F2D27A (the dashboard's gold reads as #9D9F76 through video compression; use the brighter value on screen)
* Link / interactive: #4DA3FF

### 3\. Data scale: % of Target Time (time against target; above 100 is bad) - other measures follow the same principle. Green is good. Red is bad.

|Band|Hex|Meaning|
|-|-|-|
|under 20|#036715|dark green|
|20 to 50|#17AE42|green|
|50 to 70|#37EB67|bright green|
|70 to 100|#E9973A|orange|
|100 and above|#B50E05|red|
|Deeper red for extreme values (150 and above): #7A0A02. Tile labels white, 16px minimum, with the count in brackets as on the dashboard.|||
|Score tiles in decks follow the same logic: below 50 red, 50 to 70 orange, above 70 green.|||

### 4\. Light theme (same hues, inverted ground)

* Background: #FFFFFF; panel: #F2F5FA; panel border: #D5DCE8
* Primary text: #0B1F3A; secondary: #44516B; muted: #6B778C
* Data scale unchanged (the five band colours are legible on white); tile labels #0B1F3A on green and orange tiles, white on red and dark green
* Accent gold: #B8962E; link: #0B5FD6
* Light theme is for printing and bright rooms; dark is the presentation default.

### 5\. Surfaces

* No pastel versions of the bands, no transparency fades, no gradients, no shadows, no faint underlines, no rounded cards, no numbered progression cards, no "Part N of 4" bars.
* Panels are flat #15335C with a 1px #244A7A border and square corners. Touching boxes share one stroke or keep a gap.
* Charts and maps on slides use the five-band scale for anything measured against SLA, and the gold ramp only for the Value lens.

### 6\. Type

* IBM Plex Sans everywhere (Google Fonts in decks and demos). One scale: kicker 22px uppercase, letter-spaced, muted; action title 40px semibold, two lines at most; body 24px, line height 1.35; secondary 22px; headline figure 64px bold in gold; footer 24px muted.
* Nothing under 22px on a slide. When content does not fit, split the slide ("1 of 2", "2 of 2"); never shrink the type.
* Emphasis by weight or colour from the palette, never by a new size.

### 7\. Every slide

* Kicker with the part or section name, an action title that states the point, dense content with examples, a footer row at the bottom ("ValueWise SI Edition" or the deck name on the left, "n of N" on the right). Nothing crosses the slide edge.
* Diagrams as inline SVG in the palette: shapes outlined in #244A7A or white, fills only panel navy or white, dashes carry meaning (firmness fades as scope grows), labels 22px or larger, never a face, never clip art.
* Demo inserts in a gold 2px frame marked "Live demonstration at orals" with what it shows and the fallback recording.
* Placeholders in gold square brackets; a deck ships only when a search for "\[" finds nothing.

### 8\. Words

* ValueWise is one word, capital V and W; the presented version is ValueWise SI Edition.
* No slogans or taglines unless Alex writes them, no presenter names or titles, no em dashes, no AI or model names in anything that leaves the team.
* Numbers carry their assumptions; anything illustrative says so on the slide.

### 9\. Scope of the rules

Deck, demos, films, dashboards and review decks all follow this file. The mood board (ValueWise mood board.png) shows the rules in use.

---

## Part 2. How SeedFactory applies it

### Choices the stakeholder made (2026-10-05, D-96)

- **Screen scale, not slide scale.** The guide's sizes are for slides. SeedFactory's screens keep the guide's type, ratios and rules at a size a dense app can hold: 14 px minimum, 16 px body, 20 px panel headings, 28 px KPI figures, 32 px screen titles, a 40 px gold headline figure, and 16 px tile labels on the dashboard (the guide's dashboard minimum). Line height 1.35.
- **IBM Plex Mono for code only.** IBM Plex Sans for every word and figure, with its tabular numerals so figures line up. Its sibling IBM Plex Mono only where text is code: the build console, the markdown source editor, and code in a markdown preview. Both are bundled from npm (`@fontsource-variable/ibm-plex-sans`, `@fontsource/ibm-plex-mono`), never fetched (NFR-2), so "Google Fonts in decks and demos" does not apply.
- **Style only, no ValueWise branding.** The wordmark stays SeedFactory, so gold has no "Value" to mark. No footer row reads "ValueWise SI Edition".
- **Dark is the default.** A first visit is dark whatever the operating system prefers; the toggle (Shift+D) still switches to light and remembers it.

### What carries over, and where

| Rule | In SeedFactory |
|---|---|
| Colour has a job | Band colours only for a status from the data: the utilisation classes on the dashboard, verdict and result chips (Passed, Findings, Resolved, Within budget), the stepper's phase and step results, the console's PASS, WARN and FAIL, the Start Build checklist's complete files. Everything else is navy, white and grey |
| Neutral controls | Primary button: white fill, navy label (dark); navy fill, white label (light). Secondary: panel navy with the panel border. A pressed control (the demo speed, a console filter) is a neutral inversion. The current journey step, the active phase and the focus ring use the control colour (`--accent`: white in dark, navy in light) |
| Gold | One figure per dashboard: Recoverable a year, the KPI the room reads first, larger and in gold. Recoverable cost by product, the Value lens, draws its bars in gold |
| Link blue | Links and link-like actions only: drill crumbs and product names, "show on the dashboard", disclosure toggles, the download links, retry |
| Data scale | Active green (20 to 50), Underused orange (70 to 100), Unused red (100 and above), Leaver the deepest red (150 and above, the fault), Unassigned panel-border navy. Counts that are not a status (Entitled, Assigned, In use, the footprint's three files) take white and greys |
| Surfaces | Square corners everywhere (`--radius-*` are 0), no shadows (`--shadow-*` are `none`), no gradients, no transparency fades. Panels are flat with a 1 px border. The one scrim is the modal backdrop |
| Type | IBM Plex Sans, kickers (`.caps-label`) uppercase, letter-spaced and muted; emphasis by weight |
| Tile labels | Treemap cells read "Name (count)", 16 px |
| Words | No em dashes (already a SeedFactory rule, tested) |

### What does not apply

Slide furniture has no place on an app screen: the kicker, action title and "n of N" footer row of section 7, the 22 px slide minimum, split slides, the gold demo-insert frame, gold bracket placeholders (SeedFactory has none to fill), and the score-tile thresholds for decks.

### Where SeedFactory departs from the guide (D-97, D-98, D-100)

The binding contrast rule (NFR-6, WCAG 2.1 AA, `contrast.spec.ts`) wins over a hex value. Three guide values fail it on the guide's own panel colour, so each takes the nearest value in its own hue that passes:

| Token | Guide | Fails | SeedFactory | Passes |
|---|---|---|---|---|
| Muted text, dark | #8A93A8 | 4.11:1 on panel #15335C | #949DB1 | 4.6:1 on the panel |
| Muted text, light | #6B778C | 4.14:1 on panel #F2F5FA | #626F84 | 4.7:1 on the panel |
| Gold, light | #B8962E | 2.58:1 on panel #F2F5FA, under 3:1 even for large text | #A68728 | 3.1:1, large text only |

#8A93A8 is kept as a chart grey (a mark needs 3:1, which it has). Two further rules follow from the same test:

- **A status is a fill, with a tested label.** Most band colours cannot be read as text: no red reaches 4.5:1 on navy, and no green or orange does on white. So a status shows as a filled chip, dot or bar with its label in the colour tested on that fill (navy on green, orange and gold; white on red, dark green and navy). Where a status must also be words (a form error, a stopped step), the words are in a tested colour (`--status-*-text`: bright green or orange on dark, dark green or red on light, otherwise primary text) and marked with a 3 px bar of the status fill. The guide's dark tile labels are white on every band; white on green or orange is under 3:1, so the dashboard uses the light theme's rule (navy on green and orange) in both themes.
- **Every filled mark is outlined.** The red and deep red on navy, and the green, orange and gold on white, are under the 3:1 a chart mark needs against its card. Every bar, treemap cell, pie slice and line point carries a 1 px outline in `--chart-outline` (white in dark, navy in light), so each mark keeps a visible edge and the bands keep their exact hues. The guide's diagrams are outlined in white too (section 7).

### Tokens

`frontend/src/styles/tokens.css` holds these values; `contrast.spec.ts` checks each one, after following `var()`, in both themes.

| Token | Light | Dark | From the guide |
|---|---|---|---|
| `--surface-base` | `#ffffff` | `#020921` | Background |
| `--surface-raised` | `#f2f5fa` | `#15335c` | Panel |
| `--surface-sunken` | `#ffffff` | `#020921` | Inputs and wells: the ground |
| `--surface-overlay` | `#f2f5fa` | `#15335c` | Panel, tooltip |
| `--border-subtle` | `#d5dce8` | `#244a7a` | Panel border |
| `--border-default` | `#d5dce8` | `#244a7a` | Panel border |
| `--border-strong` | `#44516b` | `#b8c0d4` | Secondary text, as a control outline |
| `--text-primary` | `#0b1f3a` | `#ffffff` | Primary text |
| `--text-secondary` | `#44516b` | `#b8c0d4` | Secondary text |
| `--text-muted` | `#626f84` | `#949db1` | Muted labels, adjusted (D-97) |
| `--text-inverse` | `#ffffff` | `#020921` | A label on a control fill |
| `--accent` | `#0b1f3a` | `#ffffff` | The control colour: navy or white |
| `--accent-subtle` | `#ffffff` | `#020921` | A selected row: the ground |
| `--link` | `#0b5fd6` | `#4da3ff` | Link blue |
| `--gold` | `#a68728` | `#f2d27a` | Gold, light adjusted (D-97) |
| `--status-positive` | `#17ae42` | `#17ae42` | Green, 20 to 50 |
| `--status-warning` | `#e9973a` | `#e9973a` | Orange, 70 to 100 |
| `--status-negative` | `#b50e05` | `#b50e05` | Red, 100 and above |
| `--chart-positive` | `#17ae42` | `#17ae42` | Active |
| `--chart-warning` | `#e9973a` | `#e9973a` | Underused |
| `--chart-anomaly` | `#b50e05` | `#b50e05` | Unused |
| `--chart-negative` | `#7a0a02` | `#7a0a02` | Leaver, the fault: 150 and above |
| `--chart-value` | `#a68728` | `#f2d27a` | Cost, the Value lens |
| `--chart-baseline` | `#626f84` | `#8a93a8` | Entitled: grey |
| `--chart-muted` | `#d5dce8` | `#244a7a` | Unassigned: panel border |
| `--chart-series-1` | `#0b1f3a` | `#ffffff` | Assigned: primary text |
| `--chart-series-2` | `#44516b` | `#b8c0d4` | In use: secondary text |
| `--chart-series-3` | `#626f84` | `#8a93a8` | Muted grey |
| `--chart-outline` | `#0b1f3a` | `#ffffff` | Diagram outline: navy or white |
| `--console-surface` | `#020921` | `#020921` | Background, both themes |
| `--console-surface-raised` | `#15335c` | `#15335c` | Panel, both themes |

The data scale's six values are tokens too (`--band-under-20` to `--band-150`), identical in both themes; series-4 to series-8 continue the navy and grey ramp for a chart with more series (only iteration 1's planted pie draws them).
