# ValueWise design language

The design language for every ValueWise product: decks, demos, films, review decks, dashboards and apps. It is not specific to any one product.

- **Part 1** is the ValueWise SI house style, v3, as written: the palette, the data scale, type, surfaces and words, with slides in mind.
- **Part 2** carries it onto a screen, for any app or dashboard: themes, the wordmark, a screen type scale, colour on controls, contrast, charts and hover, and the reference tokens.
- **Part 3** records how each product applies it, and where its implementation lives.

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

## Part 2. On screen: apps and dashboards

Part 1 is written for slides. These rules carry it onto a screen, for any ValueWise app, dashboard or demo. They were worked out while building the first product to apply them (SeedFactory, Part 3), and each holds for every product.

### Themes

- **Dark is the default.** A first visit opens dark, whatever the operating system prefers. A toggle switches to light and remembers the choice. Light is for print and bright rooms.
- Both themes use the same hues; only the ground changes (Part 1, sections 2 and 4).

### The wordmark

- A product's title reads **ValueWise™ <Product>**, for example "ValueWise™ Seed Factory". The word **Value** is gold, as section 1 asks; the rest is primary text.
- On screen the wordmark is at least 20 px bold. That makes it large text, the only size at which the light theme's gold passes contrast (see Contrast below).
- Elsewhere a product may keep its short name in running text, logs and generated files.

### Type

- **IBM Plex Sans** for every word and figure, with its tabular numerals so figures line up in columns. **IBM Plex Mono** only where the text is code: logs and consoles, source editors, code in a preview. Nothing else.
- Fonts are bundled with the product when it must work offline. Decks and web demos may load them from Google Fonts (section 6).
- One size per role, on every page (the screen type scale below). Emphasis by weight, never by a new size. Nothing sets a size outside the scale's tokens.

### Screen type scale

The slide scale (section 6) is too large for a dense screen. A screen keeps its ratios at this scale. Nothing is smaller than 12 px, and only uppercase labels, chips and footnotes are under 14 px.

| Role | Token | Size, weight | Use |
|---|---|---|---|
| Page title | `--text-2xl` | 28 px, 600 | The `h1` of each page |
| Headline figure | `--text-figure` | 36 px, 700, gold | The one figure the room reads first, at most once per screen |
| KPI figure | `--text-xl` | 24 px, 600 | Every other KPI tile |
| Panel or section title | `--text-lg` | 20 px, 600 | Dashboard panels, report titles, page sections, modal titles, cards; the wordmark (20 px, 700) |
| Sub-heading | `--text-md` | 15 px, 600 | Sections inside a panel or report |
| Body | `--text-md` | 15 px, 400, line height 1.35 | Running text, lists, markdown |
| Tile label | 16 px | 16 px | Treemap and score tiles (section 3's dashboard minimum) |
| Supporting | `--text-sm` | 14 px | Tables, notes, captions, buttons, chart text (axes, legends, tooltips), consoles |
| Label | `--text-xs` | 12 px, 600, uppercase, letter-spaced, muted | Kickers, table heads, facts, chips, small controls, footnotes |

### Colour on screen

| Rule | On screen |
|---|---|
| Colour has a job | Band colours only for a status that comes from the data: a verdict or result chip, a measured value against its target, a class or grade the data assigns, a test outcome in a log. Everything else is navy, white and grey |
| Neutral controls | Primary button: white fill, navy label (dark); navy fill, white label (light). Secondary: panel navy with the panel border. A pressed control (a segmented choice, a filter, a speed) is a neutral inversion. The current step in a journey, the active item and the focus ring use the control colour (white in dark, navy in light) |
| Gold | The one headline figure per screen, and the Value lens in charts (cost, savings, value). Never headings, borders or emphasis |
| Link blue | Links and link-like actions only: drill-downs, "open", "show", disclosure toggles, downloads, retry |
| Counts are not statuses | A plain count or total that is not measured against anything takes white and greys, never a band colour |
| Surfaces | Square corners (radius 0), no shadows, no gradients, no transparency fades. Panels are flat with a 1 px border. The one scrim allowed is a modal's backdrop |

### Contrast

WCAG 2.1 AA wins over a hex value. Three values in Part 1 fail it on the guide's own panel colour, so each product uses the nearest value in its own hue that passes:

| Value | Guide | Fails | Use instead | Passes |
|---|---|---|---|---|
| Muted text, dark | #8A93A8 | 4.11:1 on panel #15335C | #949DB1 | 4.6:1 on the panel |
| Muted text, light | #6B778C | 4.14:1 on panel #F2F5FA | #626F84 | 4.7:1 on the panel |
| Gold, light | #B8962E | 2.58:1 on panel #F2F5FA, under 3:1 even for large text | #A68728 | 3.1:1, large text only |

#8A93A8 stays usable as a chart grey (a mark needs 3:1, which it has). Two further rules follow:

- **A status is a fill, with a tested label.** Most band colours cannot be read as text: no red reaches 4.5:1 on navy, and no green or orange does on white. So a status shows as a filled chip, dot or bar, its label in the colour tested on that fill: navy on green, orange and gold; white on red, dark green and navy. Where a status must also be words (a form error, a stopped step), the words take a tested colour (bright green or orange on dark, dark green or red on light, otherwise primary text) and a 3 px bar of the status fill. In a log, a failure is white text with its level on a red fill.
- **Tile labels follow the light theme's rule in both themes.** Section 3 puts white labels on every band in dark, but white on green or orange is under 3:1. Use navy on green and orange, white on red and dark green, in both themes.

### Charts

- **The data scale for anything measured against a target**, by how bad it is (section 3). A class or grade the data assigns maps to the band of its severity; the deepest red is kept for faults. The **Value lens** (cost, savings) is gold. Everything else (counts, totals, series) is a white, navy and grey ramp.
- **Flat on the panel.** Marks sit apart by a 1 px gap in the panel colour, never a white outline. A treemap's group levels are the panel itself. Legend swatches have no edge. Nothing in a chart is white unless it is data.
- **Labels.** Tiles read "Name (count)" at 16 px, in the label colour tested on their fill. Axes are named, with units.
- **Contrast of marks.** Navy and grey marks need 3:1 against the panel. The data scale and gold keep their exact hues even where they fall under 3:1 (red on navy, green, orange and gold on white). That is allowed only because every figure they draw is also given in text: tile labels with counts, a legend with figures, tooltips, a table.
- **Hover never covers what it points at.** A bar chart's hover band is a solid palette colour (#244A7A dark, #D5DCE8 light), with no transparency, drawn **behind** the bars, so the hovered bars and their labels stay on top. A line chart's pointer is a thin dashed line in the strong border colour. A hovered tile takes an edge in the primary text colour. Tooltips are panel navy (or the light panel) with a 1 px border and primary text. Any new chart follows the same rule: highlight behind or around the data, never a solid layer over it.

### What does not apply on a screen

Slide furniture: the kicker, action title and "n of N" footer row of section 7, the 22 px slide minimum, split slides, the gold demo-insert frame, and the deck score-tile thresholds. Gold bracket placeholders apply only where a product has text for a team to fill.

### Tokens

The reference values, as CSS custom properties. A product implements them under these names (Part 3 says where); each is checked in both themes.

| Token | Light | Dark | Role |
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
| `--text-muted` | `#626f84` | `#949db1` | Muted labels, adjusted for contrast |
| `--text-inverse` | `#ffffff` | `#020921` | A label on a control fill |
| `--accent` | `#0b1f3a` | `#ffffff` | The control colour: navy or white |
| `--accent-subtle` | `#ffffff` | `#020921` | A selected row: the ground |
| `--link` | `#0b5fd6` | `#4da3ff` | Link blue |
| `--gold` | `#a68728` | `#f2d27a` | Gold, light adjusted for contrast |
| `--status-positive` | `#17ae42` | `#17ae42` | Green, 20 to 50 |
| `--status-warning` | `#e9973a` | `#e9973a` | Orange, 70 to 100 |
| `--status-negative` | `#b50e05` | `#b50e05` | Red, 100 and above |
| `--chart-positive` | `#17ae42` | `#17ae42` | Data scale: good |
| `--chart-warning` | `#e9973a` | `#e9973a` | Data scale: caution, 70 to 100 |
| `--chart-anomaly` | `#b50e05` | `#b50e05` | Data scale: bad, 100 and above |
| `--chart-negative` | `#7a0a02` | `#7a0a02` | Data scale: a fault, 150 and above |
| `--chart-value` | `#a68728` | `#f2d27a` | The Value lens: gold |
| `--chart-baseline` | `#626f84` | `#8a93a8` | A baseline or total: grey |
| `--chart-muted` | `#d5dce8` | `#244a7a` | A background class: the panel border |
| `--chart-series-1` | `#0b1f3a` | `#ffffff` | First series: primary text |
| `--chart-series-2` | `#44516b` | `#b8c0d4` | Second series: secondary text |
| `--chart-series-3` | `#626f84` | `#8a93a8` | Third series: muted grey |
| `--chart-outline` | `#f2f5fa` | `#15335c` | The gap between marks: the panel |
| `--console-surface` | `#020921` | `#020921` | A log or console: background, both themes |
| `--console-surface-raised` | `#15335c` | `#15335c` | A log or console: panel, both themes |

The data scale's six values are tokens too (`--band-under-20` to `--band-150`), identical in both themes. `--chart-series-4` to `--chart-series-8` continue the navy and grey ramp for charts with more series. Radii are 0, shadows `none`.

---

## Part 3. Products

### SeedFactory (ValueWise™ Seed Factory)

The first product to apply this language (change request CR-3 and its follow-ups, 2026-10-05 and 2026-10-06, decisions D-96 to D-105 in `decisions.md`).

- **Where it lives.** `frontend/src/styles/tokens.css` holds the Part 2 tokens; `frontend/tests/contrast.spec.ts` reads the Part 2 table and checks every value and contrast pair in both themes; the dashboard validator's contrast test (T-20, `backend/seedfoundry/validators/visual.py`) applies the chart rules. Fonts are bundled from npm (`@fontsource-variable/ibm-plex-sans`, `@fontsource/ibm-plex-mono`), as the product runs offline.
- **Title.** The wordmark and the browser tab read "ValueWise™ Seed Factory" (D-103). The launcher, the Seed files and the docs keep the short name SeedFactory.
- **Mono.** IBM Plex Mono in the build console, the markdown source editor and code in a preview.
- **Statuses in colour.** Verdict and result chips (Passed, Completed with findings, Resolved, Within budget, the findings' severity), the build stepper's results, the console's PASS, WARN and FAIL, the Start Build checklist's complete files.
- **Dashboard (License Optimization).** Utilisation classes on the data scale: Active green, Underused orange, Unused red, Leaver the deepest red (the fault), Unassigned panel-border navy. Entitled, Assigned and In use are grey and white counts. Recoverable cost by product is gold, the Value lens, and Recoverable a year is the screen's one gold headline figure (D-99).
- **Link blue.** Drill crumbs and product names, "show on the dashboard", disclosure toggles, the download links, retry.
- **Footnote.** "* Assuming default 10 cycles", asked for in very small text, is the scale's smallest step: 12 px, muted.
- **Checked.** The rehearsal (`npm run rehearse`) takes screenshots of every page in both themes and hovers each chart in both themes.
