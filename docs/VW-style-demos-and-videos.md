# ValueWise.SI style file: interactive demos and the two prototype videos

For whoever builds or re-shoots a demo or a prototype video so that it looks like the deck: the four HTML demos (Throughput Explorer, Microcluster Explorer, Emulated client and competition review, The Shrinking Window) and the two videos that play from the deck, Idea to Seed (Demo 3a, media/seed-factory.mp4) and Seed to Tree (Demo 3b, media/seed-to-tree.mp4).

It applies the ValueWise overall design guide 2.1.1 (Gold Standard, dark edition) to moving and interactive work and adds the conventions the deck already uses. Where this file and 2.1.1 differ, this file is the narrower rule for demos and video; Alex's direct decisions take precedence over both. Dark only: the demos and videos have no light edition.

## 1\. Character, in one paragraph

Calm, precise, human, quietly futuristic. Navy canvas, silver linework, white for what matters now, and one pale gold per screen for value, a benchmark, the champion or the human gate. The film supplies atmosphere; a demo or a prototype video supplies understanding: every frame shows a mechanism, a number with its unit, or a file with its name. Nothing sparkles, nothing glows, nothing is decorated. Space is generous, but never at the expense of the thing being explained.

## 2\. Tokens

|Role|Value|Use|
|-|-|-|
|Canvas|#020921|Every background, video included|
|Raised surface|#0D182E|Panels with a job: controls, a file, a caption band, a recorded window|
|Primary text|#F4F5F7|Titles, the current value, the latest series|
|Secondary text and linework|#C5CBD5|Body, contours, earlier series|
|Muted text|#9AA5B7|Labels, units, sources, speed tags|
|Structural line|#435168|Frames, connectors, axes|
|Subtle divider|#223049|Rules, grid lines|
|Value accent|#D8C397|One per screen: the key figure, the value note, the champion outline, the human gate, the seed core|
|Supporting blue|#7297BA|A named neutral series when silver and white are both taken|

Watermelon bands, analytical meaning only, never for buttons or decoration: under 20% #4F9875, 20 to 50% #79AA87, 50 to 70% #A2C4A1, 70 to 100% #C2A46C, 100 to 150% #BB7374, 150% and above #96545B. Resolution time as a share of the agreed SLA; 100% is the agreed time. An anomaly is a mellow red tile with an X; a valid exception an outlined square; the champion a thin gold outline. Legend and unit always on screen with the tiles.

Type: Arial, Helvetica, sans-serif. Regular and bold only. Monospace (Consolas, Menlo, Courier New) only for file contents, values that must align, and speed tags.

Vocabulary that is also style: "major AIs" and "maker", never "vendor"; "the SI orchestra", never "the formation"; roles Author, Reviewer, Challenger, Assurance; files identity.md, instrument.md, environment.md, value.md; the seed is core.md plus adaptation.md plus protection.md; "ValueWise" one word; no em dashes anywhere, not in captions, not in code comments on screen; ranges with "to"; the currency code EUR, never the symbol; "judgement"; "%" after the number. No maker or model names on screen, in a file name, a window title or a terminal prompt.

## 3\. Interactive demos (HTML)

Layout: one screen. A demo fits the viewport with no page scroll at 1366 x 700, 1440 x 780, 1600 x 860 and 1920 x 1016 (the deck opens demos in a frame of that height). Structure the page as a 100vh grid with three rows: header, main, footer. Header: the inline wordmark (Value in gold, Wise.SI in silver, 14 px bold), the title (26 to 40 px bold), one line of description. Main: controls on the left, results on the right, 5:7, the controls column a flex column that spreads its groups over the height it has; notes under sliders are the first thing to hide when the height is short, preset descriptions the second. Footer: sources on one line, 12 to 14 px muted, numbered, links underlined. Panels (#0D182E with a 1 px #435168 border, square corners) only where they have a function: the controls block, the formula block, a file. The canvas carries everything else.

Controls: real buttons, real labels, visible focus (2 px gold outline, 3 px offset). Neutral buttons: white text, 1.5 px silver border, transparent fill, panel fill on hover; pressed state is the panel fill with a white border. Sliders use the gold accent colour for the thumb and no other colour. Segmented choices (100k, 500k, 1M, 2M) as one bordered group. Colour alone never signals a state.

Results: the big figures first (36 to 80 px bold, tabular numerals), the unit under each in secondary, the derivation under that in muted monospace. The one gold figure is the one the demo is about (per setup, the champion, the SI-native bill), not the largest. Then one caveat line with a 3 px gold rule on its left ("Illustrative scenario. Reading capacity, not judgement, comprehension or business value."). Then the model with current values: the general formula in muted, the substituted formula with the result in gold, the inputs as three small steps.

No network at all: no fonts, scripts, analytics or images from elsewhere. Inline everything. Respect prefers-reduced-motion. The wordmark appears once per demo.

## 4\. Charts, in demos and in video

Every chart has a unit and a comparator. Comparisons share one scale. Bar charts start at zero. Earlier values in silver, the current or latest in white, the champion or the value line in gold; never gold on the biggest bar by default. Axis and band labels 22 px muted on slides and at 1920 x 1080 video, 14 to 16 px in demos. Illustrative curves are labelled illustrative, in the footer line or next to the chart, every time.

Animated charts follow the Shrinking Window conventions: one thin playhead line (1.5 px, white) with one dot per series and a small value tag beside each dot; static band labels that are revealed as the playhead passes them (Edge from context; Built into the weights; The model; Context work; SI-native company) and then stay; a faint ghost outline of the whole picture from the first frame, so the frame is never empty while it fills; no brackets, no labels that travel with the playhead, no second dot per series. Two charts side by side share the same header height and the same viewBox so their axes align to the pixel. The headline above an animated chart changes with the clock in one sentence ("context work against the model; SI-native pays 1/34 of that bill") and never wraps to a third line.

Tile grids (the watermelon): tiles of one size with a 1 px canvas gap, mellow band fills, the key under the grid (X error, outlined square valid exception, gold outline champion), the band legend under the key. A drill-down shows one service, then one queue, then one error beside one valid exception. The whole-estate view returns at the end.

## 5\. Motion

Routine interface transitions 160 to 220 ms; diagram changes 400 to 600 ms; growth and phase changes (the tree, the window filling) are the only long animations, and they run at the pace of the story, 20 to 40 s per phase, with ease-out. Motion explains selection, growth or a phase change; nothing moves on a text-heavy screen. Gold moves once per video: the moment a person opens the gate. No automatic audio in demos; a video carries narration or captions, never music under the mechanism.

## 6\. The seed and the tree: the drawing vocabulary

The seed (assets/seed-b.png, compact B, 528 x 890; assets/seed.png is the small C version): a frontal, symmetrical almond with exactly three structures and nothing else. Outer shell = protection.md, the guardrails generated around the seed. Inner layer = adaptation.md, instrument.md and environment.md folded into one. Gold core = core.md, from value.md: the value to create, its purpose and measure, the next build; short and versioned. The keyhole at the base is the human gate; nothing grows until a person opens it. Silver linework, one gold element (the core), the keyhole in silver until it opens. Never a crystal, a real seed, layered fabric, or roots passing through an intact shell: planting is approval followed by an opening.

The tree (assets/tree.png, 940 x 451, compact B; a fuller A version is coming from the design side): slender trunk, airy branches with primary, secondary and fine branching, geometric cube nodes at the tips, three of them gold (value outputs, sparse, at selected tips, never every branch), a small flat base with two end markers, the seed base under 8% of the tree's height. Never bark, leaves, fruit textures, tangled roots. The sapling between seed and tree is two leaves on a stem in the same line weight.

The window (the Planting and growing drawing): one thin rectangle (#435168, 1 px) is the context window; along its top a gauge bar from 0 to 100% of the window with two ticks, replan at 70% and hard reserve at 85%, the bar white up to the current use and structural grey beyond; a caption line above it reads "1M context window · Replan at 70% · Hard reserve at 85% · Auto-compression off". Inside, one ground line; on it, left to right, the seed, the sapling, the tree, with their labels Plant and Grow under the ground line in white bold. Between seed and sapling a gold arrow and the gold words "A person opens the gate" (the one gold line); between sapling and tree a white arrow and "the SI orchestra grows and tests it, one uninterrupted build".

The orchestra: humans with credible instruments, never robots or chips; four principal seats with their gold role labels at the players' feet; the conductor in white, labelled Human conductor, under the conductor; the bench small at the side. Use the approved artwork (assets/orchestra.png, assets/musician.png, assets/bench.png); do not redraw it.

## 7\. Video 1: Idea to Seed (Demo 3a, the Seed Factory)

File media/seed-factory.mp4. What it shows: an idea in a few sentences becomes a seed, composed and reviewed before anything is planted. The music example is deliberate: a seed is a definition of value, not a program.

Beats, with the running time as a guide (target 2:30 to 3:40; the deck button says 3:39 and is changed to match the delivered cut):

1. 0:00 Title card, 3 s: navy, the wordmark bottom left, "Demo 3a · Idea to Seed" in 44 px bold white, one line under it in 28 px secondary: "An idea becomes a seed: composed, then protected, then reviewed."
2. 0:03 The idea, 15 s: a single panel, "The idea, in a few sentences", the text typed at reading speed in 32 px white: a string quartet movement, in a given mood and length, for a given occasion. Caption: "Music on purpose: a seed is a definition of value, not a program."
3. 0:20 Composing core.md, 40 s: the gold core appears alone, drawn in one stroke, 600 ms; beside it the file core.md as a panel (label CORE.MD in 22 px uppercase muted, contents in 28 px monospace secondary): the value to create, its purpose, its measure, the next build; a version tag "v1" in the corner. The Author seat label sits in gold under the panel while it writes; the other three role labels wait in muted.
4. 1:00 Generating adaptation.md and protection.md, 50 s: the inner layer draws itself around the core (silver, 600 ms), then adaptation.md fills; the outer shell draws itself (silver, 600 ms), then protection.md fills. The keyhole appears last at the base, silver, shut. Speed tag "x12" top right in muted monospace while the files fill.
5. 1:50 Review by a different player, 30 s: the Reviewer, Challenger and Assurance labels light in turn; a small counter "Findings 7 → 2 → 0" in 28 px, the bar beside it shrinking to zero, silver then white; the version tag ticks to v2 and v3. Caption: "Reviewed by a different player before anything is planted."
6. 2:20 Hold, 10 s: the finished seed with its three leaders (protection.md: outer shell; adaptation.md: inner layer; core.md: core) and the shut keyhole. Caption: "The keyhole stays shut until a person opens the gate."
7. 2:30 End card, 5 s: "Handed to Demo 3b, where the same seed grows into working tools." Wordmark bottom left, no sound mark, no slogan.

If the video is a recording of the real Seed Factory screen rather than an animation, the recording sits inside a window frame (thin #435168 rectangle, 8 px radius, a 32 px navy margin around it) on the navy canvas, never full-bleed desktop; the recorded application's own chrome is cropped to the content; any maker, model or client name in the recording is masked with a #0D182E block. The seed drawing then runs beside or above the recording as the diagram that explains it, in the same beats.

## 8\. Video 2: Seed to Tree (Demo 3b)

File media/seed-to-tree.mp4. What it shows: three small files (how to think, how to adapt, what is allowed) grow into working tools in one approved session, inside one window, with a person at the gate. Two cuts exist: the full recording (4:31, the backup) and cut B with captions (2:32, the one played); the deck button names the cut it plays.

Beats (cut B as the guide):

1. 0:00 Title card, 3 s: "Demo 3b · Seed to Tree", one line: "One seed, one window, one approved session."
2. 0:03 The three files, 20 s: the seed from Demo 3a, with its three leaders; each file panel opens for a few seconds, caption "Three small files: how to think, how to adapt, what is allowed."
3. 0:23 The gate, 10 s: the gold arrow and the gold words "A person approves at the gate"; the keyhole turns from silver to gold and opens (the only gold motion in the film); caption "It only grows what is allowed."
4. 0:33 Growth inside the window, 70 to 90 s: the window rectangle with its gauge; the gauge fills white from the left as the session runs; the 70% tick is passed with a one-line caption "Replan at 70%", the 85% tick is never reached in the cut (if it is in the recording, the caption says "Hard reserve at 85%: the build stops and restarts from the seed"). The tree grows in the window: trunk first (one stroke, 2 s), primary branches (stroke-dashoffset along each path, 3 s), secondary branches, fine branches, then the cube nodes popping in (200 ms each, silver) as tools are built; the discovery count runs under the window in 28 px: "Discovery: 17 datasets across 5 systems", the two numbers counting up with the nodes. Each test pass is a thin white sweep across the window from left to right (600 ms) with a counter "Pass 3 · full re-read · 0 failures"; a failure found shows as one node outlined in mellow red for a moment, then silver again when fixed. Three selected tips turn gold at the end: the working tools. Speed tag "x20" during time-lapse.
5. 2:05 Working tools, 20 s: the grown tree held; beside it the three gold tips named as the tools that exist now (one line each, 28 px); caption "From three small files to working tools. Recorded demonstrator, sample data."
6. 2:27 End card, 5 s: "Build and tests stay with the seed; as models improve, the same seed is regrown and must pass the same tests."

Graphs in this video, all drawn in the chart conventions above: the window gauge (context use, %), the pass counter (passes, failures found and fixed), the discovery counter (datasets, systems), the time-lapse clock (elapsed session time in minutes, muted monospace, top right next to the speed tag). No other overlays.

If the film is a screen recording of the real session, the recording sits in a window frame as in Demo 3a, the tree and the gauge run as an animated diagram in a strip above or beside it, synchronised to the recording's own events (a tool completed = a node), and captions carry the beats; names in the recording masked as above.

## 9\. Captions and overlays in video

Caption band: a #0D182E band across the bottom third's lower edge, 96 px tall at 1920 x 1080, a 1 px #223049 line on top, text 36 px white, left aligned at x 96, at most two lines, one idea per caption, on screen at least 3 s. Speed tags: "x12" in 28 px muted monospace, top right at x 1824 right aligned, y 64, only while time-lapsed. File panels: #0D182E, 1 px #435168 border, label 22 px uppercase letter-spaced muted, contents 28 px monospace secondary, a version tag in muted at the top right. Role labels: 24 px bold, gold for the seat at work, muted for the others. Counters: 28 px, the number white, the words secondary. The wordmark: bottom left at x 96, y 1016, 24 px, Value gold and Wise.SI silver, on every frame except the title card's first second. No page numbers in video.

## 10\. Delivery

MP4, H.264 High profile, AAC audio (or no audio track if silent), 1920 x 1080, 25 or 30 fps constant, square pixels, a poster frame that is the title card at 0:02. Two files per video: the hosting copy (up to about 60 MB) and the deck-link copy (under 15 MB: 1280 x 720 at about 1 Mbps is enough for an animation). Names exactly media/seed-factory.mp4 and media/seed-to-tree.mp4; the deck picks them up with no other change. A three-second black opening belongs to the 60-second film only, not to these two. No maker or model names, no client names, sample data labelled sample.

## 11\. Checks before delivery

Open the file in a browser from the deck's media folder and play it from slide 31 and slide 32: it covers the slide, the controls appear, Esc returns. Scrub to every caption: two lines or fewer, no em dashes, numbers with units, "%" after the number. Pause on the seed: three structures, the gold core, the keyhole. Pause on the tree: slender, cube nodes, three gold tips, a base under 8% of its height. Check the window gauge's 70% and 85% ticks against the caption text. Check that gold appears once per frame at most, and moves once in the whole video. Check the title card, the end card and the wordmark position. Play at 1280 x 720 as well; the captions are still readable. Confirm there is no sound unless narration was recorded, and no music under the mechanism.

## Appendix A. CSS for a demo

```css
:root{color-scheme:dark;--bg:#020921;--panel:#0D182E;--line:#435168;--divider:#223049;--fg:#F4F5F7;--muted:#C5CBD5;--faint:#9AA5B7;--accent:#D8C397;--blue:#7297BA;--sans:Arial,Helvetica,sans-serif;--mono:Consolas,Menlo,"Courier New",monospace}
html,body{height:100%;background:var(--bg);color:var(--fg)}
body{font-family:var(--sans);font-size:clamp(14px,1vw,18px);line-height:1.45;overflow:hidden;box-sizing:border-box;padding:clamp(12px,1.6vw,22px) clamp(16px,2.6vw,48px)}
.wrap{height:100%;display:grid;grid-template-rows:auto minmax(0,1fr) auto;gap:clamp(10px,1.4vw,20px)}
.main{display:grid;grid-template-columns:minmax(0,5fr) minmax(0,7fr);gap:clamp(16px,2vw,36px);min-height:0}
.panel{background:var(--panel);border:1px solid var(--line)}
.btn{font:inherit;color:var(--fg);background:transparent;border:1.5px solid var(--muted);padding:10px 16px;cursor:pointer}
.btn:hover{background:var(--panel);border-color:var(--fg)}
.btn\[aria-pressed="true"]{background:var(--panel);border-color:var(--fg)}
:focus-visible{outline:2px solid var(--accent);outline-offset:3px}
.caveat{border-left:3px solid var(--accent);padding-left:14px}
.num{font-weight:700;letter-spacing:-0.02em;font-variant-numeric:tabular-nums}
.num.hero{color:var(--accent)}
@media (max-height:900px){.note{display:none}}
@media (prefers-reduced-motion:reduce){\*{transition:none!important;animation:none!important}}
```

## Appendix B. The playhead and value tag (SVG, 1000 x 700 viewBox)

```svg
<line class="playhead" x1="0" x2="0" y1="40" y2="640" stroke="#F4F5F7" stroke-width="1.5"/>
<circle class="dot" r="6" fill="#F4F5F7"/>            <!-- one per series; the gold series uses fill #D8C397 -->
<text class="tag" font-family="Arial" font-size="22" fill="#C5CBD5" dx="12" dy="-10">64</text>
<path class="ghost" d="…whole series…" fill="none" stroke="#435168" stroke-width="1" stroke-dasharray="4 6"/>
<text class="band" font-size="22" fill="#9AA5B7" opacity="0">Context work</text>  <!-- opacity 1 once the playhead passes its x -->
```

## Appendix C. The window gauge

Rectangle x 0, y 0, w 1200, h 300, stroke #435168 1 px, no fill. Gauge: y 44, from x 24 to x 1176, track 6 px #435168, fill #F4F5F7 from the left to the current use; ticks at 70% (x 830) and 85% (x 1003), 1 px #C5CBD5, 14 px tall, labels "70%" and "85%" 22 px muted under the ticks. Caption above the rectangle at y minus 16: "1M context window · Replan at 70% · Hard reserve at 85% · Auto-compression off", 22 px muted. Ground line y 262 from x 24 to x 1176, 1 px #C5CBD5. Seed at x 200 (height 150), sapling at x 540, tree at x 1020 (height 180, base on the ground line). Labels Plant and Grow 24 px bold white, 24 px under the ground line, centred under the seed and the tree.

## ValueWise.SI UI design style

### 2026-10-12

This file applied to the Seed Factory app (the screen Demo 3a records), style only: no script, template, visible text, route, file name or dependency changed. The decision is D-107 in `docs/decisions.md`. Four choices were made with the stakeholder before any edit. The file applies to the dark theme only, as the file is dark only; the light theme and its toggle are unchanged. The one-screen rule of section 3 is not applied, as it is written for the four HTML demos and the app's report, dashboard and console are longer than one screen; instead every page has no horizontal scroll and a whole top bar at the four sizes. One gold per screen: the dashboard's cost bars move to silver and Recoverable a year keeps gold; the wordmark's gold Value is treated as part of the wordmark, as in this file's own demo header. The wordmark stays at 20 px, as it is also the app's title.

Each entry gives the element or selector, the value before, the value after, and the section it follows. "Dark" means the `[data-theme='dark']` block; "both themes" means `:root`.

#### frontend/src/styles/tokens.css

Dark theme:

- `--surface-raised` and `--surface-overlay` (panels, menus, tooltips): #15335C to #0D182E. Section 2, raised surface.
- `--chart-outline` (the gap between chart marks): #15335C to #0D182E, so it stays the panel colour. Sections 2 and 4.
- `--border-default` (panel and card borders): #244A7A to #435168. Sections 2 and 3, structural line.
- `--border-subtle` (rules inside panels): #244A7A to #223049. Section 2, subtle divider.
- `--border-strong` (control outlines): #B8C0D4 to #C5CBD5. Section 3, the silver border of a neutral button.
- `--text-primary`: #FFFFFF to #F4F5F7. Section 2, primary text.
- `--text-secondary`: #B8C0D4 to #C5CBD5. Section 2, secondary text and linework.
- `--text-muted`: #949DB1 to #9AA5B7. Section 2, muted text.
- `--accent` (the control colour: primary button fill, current step, finding highlight): #FFFFFF to #F4F5F7. Section 2, primary text.
- `--link`: #4DA3FF to #7297BA. Section 2, supporting blue (this file names no link colour; the supporting blue is the only blue in its palette).
- `--gold`: #F2D27A to #D8C397. Section 2, value accent.
- `--band-under-20`: #036715 to #4F9875. Section 2, watermelon bands.
- `--band-20-50`: #17AE42 to #79AA87. Section 2.
- `--band-50-70`: #37EB67 to #A2C4A1. Section 2.
- `--band-70-100`: #E9973A to #C2A46C. Section 2.
- `--band-100`: #B50E05 to #BB7374. Section 2.
- `--band-150`: #7A0A02 to #96545B. Section 2.
- `--status-positive`, `--status-warning`, `--status-negative`, `--chart-positive`, `--chart-warning`, `--chart-anomaly`, `--chart-negative`, `--status-positive-text` and `--status-warning-text`: unchanged references to the bands, so they take the watermelon values above. Section 2.
- `--status-neutral`: #949DB1 to #9AA5B7. Section 2, muted text.
- `--on-status-negative` (a label on a red status chip): #FFFFFF to #020921, as white is 3.31:1 on #BB7374 and navy is 5.47:1. Section 2, with the contrast rule.
- `--status-negative-text`: #FFFFFF to #F4F5F7. Section 2.
- `--chart-series-1` (the current or latest series): #FFFFFF to #F4F5F7. Section 4, current in white.
- `--chart-series-2` (earlier values): #B8C0D4 to #C5CBD5. Section 4, earlier in silver.
- `--chart-series-3`: #8A93A8 to #7297BA. Section 2, supporting blue when silver and white are both taken.
- `--chart-value` (the dashboard's Recoverable cost by product bars): var(--gold), #F2D27A, to var(--text-secondary), #C5CBD5. Sections 1 and 2, one gold per screen; section 4, never gold on the biggest bar by default.
- `--chart-baseline`: #8A93A8 to #9AA5B7. Section 2, muted.
- `--chart-muted` (the Unassigned class): #244A7A to #435168. Section 2, structural line.
- `--chart-label-on-anomaly`: #FFFFFF to #020921, as white is 3.31:1 on #BB7374. Section 2, with the contrast rule.
- `--chart-label-on-negative`: #FFFFFF to #F4F5F7. Section 2.
- `--chart-label-on-muted`: #FFFFFF to #F4F5F7. Section 2.
- `--chart-grid` and `--chart-brush`: #244A7A to #223049. Section 2, grid lines.
- `--scrollbar-thumb`: #244A7A to #435168. Section 2, structural line.
- `--scrollbar-thumb-hover`: #8A93A8 to #9AA5B7. Section 2, muted.

Both themes (the console is dark in both themes, so it takes the dark values):

- `--console-surface-raised`: #15335C to #0D182E. Section 2.
- `--console-border`: #244A7A to #435168. Section 2.
- `--console-text`, `--console-llm` and `--console-fail`: #FFFFFF to #F4F5F7. Section 2.
- `--console-text-secondary` and `--console-api`: #B8C0D4 to #C5CBD5. Section 2.
- `--console-text-muted`: #949DB1 to #9AA5B7. Section 2.
- `--console-pass`: #37EB67 to #79AA87. Section 2, the 20 to 50% band.
- `--console-warn`: #E9973A to #C2A46C. Section 2, the 70 to 100% band.
- `--console-fail-mark` (the red mark behind a FAIL level): #B50E05 to #96545B, the 150% and above band, as white text is 3.31:1 on #BB7374 and 5.18:1 on #96545B. Section 2.
- `--font-sans`: 'IBM Plex Sans Variable', 'IBM Plex Sans', 'Segoe UI', system-ui, sans-serif to Arial, Helvetica, sans-serif. Section 2, type.
- `--font-mono`: 'IBM Plex Mono', Consolas, ui-monospace, monospace to Consolas, Menlo, 'Courier New', monospace. Section 2, type.
- `--duration-fast` (routine transitions: buttons, tooltips): 120 ms to 160 ms. Section 5, 160 to 220 ms.

#### frontend/src/styles/base.css

- `:focus-visible` outline: 2 px solid var(--accent) (white in dark) to 2 px solid var(--gold). Section 3 and Appendix A.
- `:focus-visible` outline-offset: 2 px to 3 px. Section 3 and Appendix A.
- `@media (prefers-reduced-motion: reduce)` on every element: animation-duration 0.01 ms, animation-iteration-count 1 and transition-duration 0.01 ms to animation: none and transition: none, both important. Section 5 and Appendix A.
- `.caps-label` font-weight: 600 to 700. Section 2, regular and bold only.

#### frontend/src/components/base/BaseButton.vue

- `.button` border: 1 px solid transparent to 1.5 px solid transparent. Section 3.
- `.button` font-weight: 600 to 700. Section 2.
- `.button--secondary` background: var(--surface-raised) to transparent. Section 3 and Appendix A, neutral button.
- `.button--secondary` border-color: var(--border-default) to var(--border-strong) (silver). Section 3.
- `.button--secondary:hover` background: var(--surface-sunken) to var(--surface-raised) (the panel fill). Section 3.
- `.button--secondary:hover` border-color: var(--border-strong) to var(--text-primary) (white). Section 3 and Appendix A.

#### frontend/src/components/shell/ThemeToggle.vue

- `.theme-toggle` border: 1 px solid var(--border-default) to 1.5 px solid var(--border-strong). Section 3, neutral button.
- `.theme-toggle` background: var(--surface-raised) to transparent. Section 3.
- `.theme-toggle` color: var(--text-secondary) to var(--text-primary). Section 3, white text.
- `.theme-toggle:hover` border-color: var(--border-strong) to var(--text-primary). Section 3.
- `.theme-toggle:hover` background: none set to var(--surface-raised). Section 3, panel fill on hover.

#### frontend/src/components/intake/MarkdownEditor.vue

- `.icon-button` (the editor's toolbar buttons) border: 1 px solid var(--border-default) to 1.5 px solid var(--border-strong). Section 3, neutral button.
- `.icon-button` background: var(--surface-raised) to transparent. Section 3.
- `.icon-button` color: var(--text-secondary) to var(--text-primary). Section 3.
- `.icon-button:hover` border-color: var(--border-strong) to var(--text-primary). Section 3.
- `.icon-button:hover` background: none set to var(--surface-raised). Section 3.
- `.segmented__option` font-weight: 500 to 400. Section 2.
- `.segmented__option[aria-pressed='true']` font-weight: 600 to 700. Section 2.

#### frontend/src/components/shell/TopBar.vue

- `.wordmark` color (the "Wise™ Seed Factory" part; "Value" stays gold): var(--text-primary) to var(--text-secondary). Section 3, Value in gold and the rest in silver.

#### frontend/src/components/build/BuildConsole.vue

- `.console__button:focus-visible` outline-color: var(--console-text) to var(--gold). Section 3. The offset stays -2 px, as the buttons sit in a clipped strip and a ring outside the edge would be cut off.
- `.console__body:focus-visible` outline-color: var(--console-text) to var(--gold). Section 3. The offset stays -2 px, as the body is the scroll container.
- `.console__button` font-weight: 600 to 700. Section 2.
- `.line--FAIL .line__tag` font-weight: 600 to 700. Section 2.

#### frontend/src/demo/DemoController.vue

- `.demo:focus-visible` outline-offset: 0 to 3 px. Section 3; the panel sits 16 px from the window edge, so the ring is not cut off.
- `.demo__title` font-weight: 600 to 700. Section 2.
- `.demo__speed[aria-pressed='true']` and its hover, font-weight: 600 to 700. Section 2.

#### Font weights in the other components

Every entry here follows section 2, regular and bold only: 600 to 700 and 500 to 400.

- `frontend/src/components/base/BaseCard.vue`: `.card__title` 600 to 700.
- `frontend/src/components/base/BaseChip.vue`: `.chip` 600 to 700.
- `frontend/src/components/base/BaseModal.vue`: `.modal__title` 600 to 700.
- `frontend/src/components/build/FeedbackRouting.vue`: `.tile__version`, `.tile__name` and `.tile__lines` 600 to 700.
- `frontend/src/components/build/PhaseStepper.vue`: `.phase--active .phase__row` with `.phase--stopped .phase__row`, `.step--active` and `.step--active .step__state` 600 to 700.
- `frontend/src/components/dashboard/ChartPanel.vue`: `.chart-panel__title` and `.chart-panel__legend-figure` 600 to 700.
- `frontend/src/components/dashboard/DashboardFrame.vue`: `.frame__back` with `.frame__findings`, `.frame__id` and `.frame__clear` 600 to 700.
- `frontend/src/components/dashboard/DashboardView.vue`: `.dashboard__title` 600 to 700.
- `frontend/src/components/dashboard/DrillBar.vue`: `.drill-bar__here` 600 to 700.
- `frontend/src/components/dashboard/KpiPanel.vue`: `.kpi__figure` 600 to 700.
- `frontend/src/components/dashboard/TablePanel.vue`: `.table-panel__title`, `thead th`, `tfoot th` with `tfoot td`, `.table-panel__figure` and `.table-panel__total` 600 to 700.
- `frontend/src/components/intake/EmptyState.vue`: `.empty__title` and `.empty__item dt` 600 to 700.
- `frontend/src/components/intake/FilePanel.vue`: `.checklist__item--complete`, `.group__title` and `.file--selected` 600 to 700.
- `frontend/src/components/intake/ImportDialog.vue`: `.row__note--warning` 600 to 700.
- `frontend/src/components/intake/MarkdownPreview.vue`: the headings `.markdown :deep(h1)` to `.markdown :deep(h6)`, `.markdown :deep(th)` and `.markdown :deep(.md-image-label)` 600 to 700.
- `frontend/src/components/intake/NewFileDialog.vue`: `.form__label` and `.form__warning` 600 to 700.
- `frontend/src/components/rebuild/RebuildModal.vue`: `.views__tab` 500 to 400; `.views__tab[aria-selected='true']` 600 to 700.
- `frontend/src/components/report/BuildReport.vue`: `.report__title`, `.report__fact dt`, `.report__heading`, `.report__group-title`, `.report__table thead th`, `.report__id`, `.context__budget-label` and `.context__total th` with `.context__total td` 600 to 700.
- `frontend/src/components/seed/SeedFiles.vue`: `.files__name`, `.files__download` and `.files__link` 600 to 700.
- `frontend/src/components/seed/SeedHistory.vue`: `.history__title` and `.history__toggle` 600 to 700.
- `frontend/src/components/shell/JourneyIndicator.vue`: `.journey__step` 500 to 400.
- `frontend/src/views/BuildView.vue`: `.build__empty h1`, `.build__link`, `.build__title` and `.build__show` 600 to 700.
- `frontend/src/views/KnowledgeView.vue`: `.banner__link` 600 to 700.
- `frontend/src/views/ReviewView.vue`: `h1` and `.review__link` 600 to 700.
- `frontend/src/views/SeedView.vue`: `h1`, `h2` and `.seed__link` with `.seed__inline-link` 600 to 700.

In all: 33 files, 140 style changes (48 token values in `tokens.css`, 4 in `base.css`, 88 in 31 components; 70 of them font weights).

#### Left as it was, and why

- The light theme's tokens: this file is dark only.
- `frontend/src/styles/defects.css`: iteration 1's planted defects (the off-grid cards, the serif title, the low-contrast grey) break the style on purpose, so the validators can find them.
- `.chart-panel__spinner` keeps its round shape: it is a loading indicator, not a panel. It stops under reduced motion.
- The dashboard's chart text sizes (14 px, tile labels 16 px) already sit in section 4's 14 to 16 px. They and the treemap's label weights (600 and 500) are constants in `frontend/src/dashboard/options.ts`, a script, so they are out of a style-only change; Arial draws 600 as bold and 500 as regular, so the result is the same.
- The Plex font packages are still imported by `frontend/src/main.ts`, a script and a dependency, so they are bundled but no longer used. They load from the bundle, never the network.

#### Copy issues not changed

No em dashes and no hyphenated ranges were found in the interface or the generated text.

- "vendor" (the file asks for "maker"): `backend/seedfoundry/dashboard/descriptor.py` line 95 ("Seats by vendor and product", the treemap title) and line 178 (the "Vendor" column); `backend/seedfoundry/dashboard/overlay.py` line 274; the dashboard API's error messages in `backend/seedfoundry/dashboard/query.py` lines 125, 139 and 144; the sample files `backend/seedfoundry/sample/environment.md` lines 20, 38, 55, 56, 61 and 115 and `backend/seedfoundry/sample/instrument-awareness.md` lines 8, 17 and 36, which flow into the generated Seed files.
- The currency symbol (the file asks for the code EUR): `frontend/src/dashboard/format.ts` lines 17, 23, 25 and 26 write money with the $ sign; `backend/seedfoundry/dashboard/descriptor.py` line 157 names the unit USD; `backend/seedfoundry/validators/visual.py` line 182 asks for "US dollars with the $ sign"; `backend/seedfoundry/sample/environment.md` lines 27, 87 and 105 describe US dollars and the $ sign.
- Maker names on screen: the sample estate in `backend/seedfoundry/data/estates.py` (from line 63) names software makers (Microsoft, Google, GitHub, Adobe, Salesforce and others), which show on the dashboard. The file's rule is about the major AIs' makers and models; listed in case it is meant more widely.
- Stale style words: `backend/seedfoundry/validators/visual.py` line 298 (T-19's message names "IBM Plex Sans or IBM Plex Mono"); `backend/seedfoundry/sample/environment.md` line 82 ("cost uses value (gold)", now silver in dark) and line 97 ("IBM Plex Sans for text").

#### Markup changes

None. Every change sits in a stylesheet or a component's style block.
