---
name: Estación Sigatoka
description: Ground station for a banana-plantation drone survey, drawn as an aerial-application flight chart.
colors:
  papel: "#f3f5f2"
  hoja: "#ffffff"
  margen: "#e8ecec"
  tinta: "#13202b"
  tinta-2: "#3f4d59"
  tinta-3: "#5d6a75"
  regla: "#cfd6da"
  regla-fuerte: "#9aa6ae"
  azul: "#1d5fa6"
  azul-hondo: "#154a84"
  azul-tenue: "#e4edf7"
  rojo: "#b3202f"
  rojo-tenue: "#fbe9eb"
  verde-tinta: "#1d6b30"
  noche: "#0f1922"
  gris-dato: "#9aa3a0"
  categoria-sana: "#2e9e44"
  categoria-sigatoka: "#d7263d"
  categoria-otra: "#f0a202"
typography:
  display:
    fontFamily: "Barlow Semi Condensed, Barlow, Segoe UI, system-ui, sans-serif"
    fontSize: "1.875rem"
    fontWeight: 600
    lineHeight: 1.15
    letterSpacing: "-0.01em"
  headline:
    fontFamily: "Barlow Semi Condensed, Barlow, Segoe UI, system-ui, sans-serif"
    fontSize: "1.2rem"
    fontWeight: 600
    lineHeight: 1.15
  title:
    fontFamily: "Barlow Semi Condensed, Barlow, Segoe UI, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 600
    lineHeight: 1.15
  figure:
    fontFamily: "Barlow Semi Condensed, Barlow, Segoe UI, system-ui, sans-serif"
    fontSize: "1.875rem"
    fontWeight: 600
    lineHeight: 1
    fontFeature: "\"tnum\", \"lnum\""
  body:
    fontFamily: "Barlow, Segoe UI, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.5
  body-small:
    fontFamily: "Barlow, Segoe UI, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.5
  control:
    fontFamily: "Barlow, Segoe UI, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 500
    lineHeight: 1
  label:
    fontFamily: "Barlow Semi Condensed, Barlow, Segoe UI, system-ui, sans-serif"
    fontSize: "0.78rem"
    fontWeight: 600
    letterSpacing: "0.08em"
  nav:
    fontFamily: "Barlow Semi Condensed, Barlow, Segoe UI, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 600
    letterSpacing: "0.07em"
  readout:
    fontFamily: "Barlow, Segoe UI, system-ui, sans-serif"
    fontSize: "0.78rem"
    fontWeight: 500
    lineHeight: 1.2
    letterSpacing: "0.02em"
    fontFeature: "\"tnum\", \"lnum\""
rounded:
  radio: "2px"
  muestra: "1px"
spacing:
  control: "2.25rem"
  control-grande: "2.75rem"
  barra: "3.5rem"
  panel-y: "1.1rem"
  panel-x: "1.25rem"
  gutter: "1.25rem"
  gutter-phone: "1rem"
  seccion: "2.5rem"
  contenido-max: "1240px"
  panel-mapa: "22rem"
  columna-lectura: "23rem"
components:
  button:
    backgroundColor: "{colors.hoja}"
    textColor: "{colors.tinta}"
    typography: "{typography.control}"
    rounded: "{rounded.radio}"
    height: "{spacing.control}"
    padding: "0 0.95rem"
  button-primary:
    backgroundColor: "{colors.azul}"
    textColor: "{colors.hoja}"
    typography: "{typography.control}"
    rounded: "{rounded.radio}"
    height: "{spacing.control}"
    padding: "0 0.95rem"
  button-primary-hover:
    backgroundColor: "{colors.azul-hondo}"
    textColor: "{colors.hoja}"
  button-danger:
    backgroundColor: "{colors.hoja}"
    textColor: "{colors.rojo}"
  button-danger-hover:
    backgroundColor: "{colors.rojo-tenue}"
    textColor: "{colors.rojo}"
  button-confirming:
    backgroundColor: "{colors.rojo}"
    textColor: "{colors.hoja}"
  button-disabled:
    backgroundColor: "{colors.margen}"
    textColor: "{colors.tinta-3}"
  button-large:
    height: "{spacing.control-grande}"
    padding: "0 1.25rem"
    typography: "{typography.body}"
  field:
    backgroundColor: "{colors.hoja}"
    textColor: "{colors.tinta}"
    typography: "{typography.body-small}"
    rounded: "{rounded.radio}"
    height: "{spacing.control}"
    padding: "0 0.65rem"
  segment:
    backgroundColor: "{colors.hoja}"
    textColor: "{colors.tinta-2}"
    padding: "0.45rem 0.9rem"
  segment-selected:
    backgroundColor: "{colors.tinta}"
    textColor: "{colors.hoja}"
  choice-option:
    backgroundColor: "{colors.hoja}"
    textColor: "{colors.tinta}"
    typography: "{typography.body}"
    rounded: "{rounded.radio}"
    height: "3rem"
    padding: "0.55rem 0.8rem"
  ficha-swatch:
    rounded: "{rounded.muestra}"
    size: "0.7rem"
  probability-track:
    backgroundColor: "{colors.margen}"
    rounded: "{rounded.muestra}"
    height: "0.6rem"
  table-header:
    backgroundColor: "{colors.papel}"
    textColor: "{colors.tinta-2}"
    typography: "{typography.label}"
    padding: "0.6rem 0.9rem"
  progress:
    backgroundColor: "{colors.margen}"
    height: "0.55rem"
  title-bar:
    backgroundColor: "{colors.hoja}"
    textColor: "{colors.tinta}"
    height: "{spacing.barra}"
  map-panel:
    backgroundColor: "{colors.hoja}"
    width: "{spacing.panel-mapa}"
    padding: "1.1rem 1.25rem"
  coordinate-readout:
    backgroundColor: "rgba(255, 255, 255, 0.92)"
    textColor: "{colors.tinta}"
    typography: "{typography.readout}"
    padding: "0.35rem 0.6rem"
  notice:
    backgroundColor: "{colors.azul-tenue}"
    textColor: "{colors.tinta}"
    typography: "{typography.body-small}"
    padding: "0.7rem 1rem"
  log:
    backgroundColor: "{colors.noche}"
    textColor: "#d3dde4"
    rounded: "{rounded.radio}"
    padding: "0.9rem 1rem"
---

# Design System: Estación Sigatoka

## Overview

**Creative North Star: "The Flight Chart"**

The station is the aerial-application crew's flight chart. A fumigation crew reads a chart to know where to fly and spray; the operator reads this one to know where Sigatoka is and how sure the system is about each point. Everything is drawn the way a chart is drawn: cool chart-white paper, navy chart ink, hairline 1px rules, square corners, tick marks in the margins, condensed caps labels and tabular figures. The map is full-bleed, the instruments sit in a ruled margin, and every probability carries its threshold line.

The system is dense and quiet. There is one action colour, an aeronautical blue, and it means "do this" or "this is selected". The three category inks (healthy, Sigatoka, other condition) are the meaning of the map and appear only on data: map points, zones, swatches and probability bars. Interface status speaks in ink, the dark alert red, the green ink and the blue, never in a category ink. Depth comes from rules and paper tone, not shadows. The scene is daylight: a Windows laptop on a work table or under a roof beside the crop, so the system is light-only and high-contrast.

It replaces the earlier green, emoji-heavy agritech dashboard entirely. It refuses both that dashboard of rounded cards and leaf icons and the neon drone HUD.

**Key Characteristics:**
- Cool chart-white paper with white sheets, navy ink, 1px hairline rules.
- One aeronautical blue for actions and selection; category inks reserved for data.
- Square corners (2px), corner-tick frames, a ruler of 8px ticks under the title bar.
- Barlow for reading, Barlow Semi Condensed for headings, caps labels and figures; tabular numerals everywhere numbers line up.
- Every probability scale shows the ruled threshold mark; below it the reading is "no diagnosticable".
- Motion is a 160ms press and nothing more; keyboard labelling never animates.

## Colors

A chart-paper palette: three paper tones, a navy ink scale, two rule weights, one blue, and data inks kept apart from the interface.

### Primary
- **Aeronautical Blue** (`azul`): the only action and selection colour. Primary buttons, links, the active nav item (3px inset underline), focus rings (2px outline), checkbox and radio accent, the progress fill, the caret, the selected history tile, the "En vivo" badge.
- **Deep Blue** (`azul-hondo`): hover for primary buttons and links.
- **Blue Wash** (`azul-tenue`): the system notice strip, the advice note under a verdict, and the drop zone while a file is dragged over it.

### Neutral
- **Chart Paper** (`papel`): the page ground, table header rows, the drop zone at rest, the hover fill of a choice option.
- **Sheet** (`hoja`): panels ("hojas"), the title bar, the map margin panel, controls and fields.
- **Margin** (`margen`): recessed tone. Empty probability tracks and progress tracks, disabled buttons, inline code, image placeholders.
- **Chart Ink** (`tinta`): text, headings, the title bar's bottom rule, the map panel's left rule, corner ticks, the threshold mark, the selected segment.
- **Ink 2** (`tinta-2`): secondary text, labels, intros, unselected segments and nav items.
- **Ink 3** (`tinta-3`): tertiary text, notes, placeholders, the hatch of a doubtful swatch, disabled text.
- **Rule** (`regla`): the default 1px hairline between rows, sections and panel edges.
- **Strong Rule** (`regla-fuerte`): control borders and the 8px tick ruler under the title bar.
- **Night** (`noche`): the photo viewer ground and the training log, where the image or the log is the light source.

### Status inks (interface, not data)
- **Alert Red** (`rojo`) with **Red Wash** (`rojo-tenue`): destructive actions, the armed two-step button, "Sin modelo", worse-than-current results in comparison tables. Danger buttons rest with a pale red border (#d9a3a9).
- **Green Ink** (`verde-tinta`): better-than-current results in comparison tables. It is an ink for text, never a fill.

### Data inks (category, map meaning)
- **Healthy** (`categoria-sana`), **Sigatoka** (`categoria-sigatoka`), **Other condition** (`categoria-otra`): defined in the station's data and editable from the technical zone; these defaults are the meaning of the map. They fill map points, zone rectangles, ficha swatches and probability bars, and nothing else.
- **Data Grey** (`gris-dato`): a model reading below threshold, no diagnosis, or "photo is no good". It is the data colour of doubt.

### Named Rules
**The One Blue Rule.** Aeronautical blue is the only colour that means "act" or "selected". No second accent, no gradient, no tinted variant beyond its deep hover and its wash.

**The Data Ink Rule.** Category inks belong to data only. A button, badge, alert, status chip or heading never borrows healthy green, Sigatoka red or other-condition amber; status is spoken in ink, alert red, green ink and blue.

**The Never Alone Rule.** A category colour is always paired with its name in text. A swatch without a label does not ship.

## Typography

**Body Font:** Barlow (400, 500, 600, 700), falling back to Segoe UI and system-ui.
**Display / Label Font:** Barlow Semi Condensed (500, 600, 700), falling back to Barlow.
**Mono:** ui-monospace, Cascadia Mono, Consolas, for code, keys and the training log.

Both families are self-hosted from `ui/static/fuentes/` (latin subset, `font-display: swap`) so the station works offline.

**Character:** a chart's lettering. Barlow is a plain grotesque with the even colour of highway and aviation signage; its semi-condensed cut sets headings, caps labels and big counts tightly, like the annotations on a flight chart.

### Hierarchy
The scale is in rem on a 16px root: 0.78rem (12.5px), 0.875rem (14px), 1rem (16px), 1.2rem (19px), 1.5rem (24px), 1.875rem (30px).
- **Display** (Semi Condensed 600, 1.875rem, 1.15, -0.01em): page titles (h1). Drops to 1.5rem under 560px. The verdict on Identify and Review uses this size too.
- **Headline** (Semi Condensed 600, 1.2rem, 1.15): section titles (h2). The map panel title sits at 1.5rem.
- **Title** (Semi Condensed 600, 1rem, 1.15): h3, the technical-zone summary.
- **Figure** (Semi Condensed 600, 1.875rem, line-height 1, tabular): the four counts in the map margin.
- **Body** (Barlow 400, 1rem, 1.5): running text; intros cap at 68ch, empty-state copy at 52ch.
- **Body small** (Barlow 400, 0.875rem): tables, fields, notes, legends, messages.
- **Control** (Barlow 500, 0.875rem, line-height 1): buttons and segments.
- **Label** (Semi Condensed 600, 0.78rem, 0.08em, UPPERCASE): the "rótulo" that names a group of controls or a readout ("Vista", "Leyenda", "Probabilidad por condición") and table headers (0.07em).
- **Nav** (Semi Condensed 600, 0.875rem, 0.07em, UPPERCASE): title-bar sections.
- **Readout** (Barlow 500, 0.78rem, 1.2, 0.02em, tabular): the live lat/lon readout.

Field labels are not caps: Barlow 500 at 0.78rem in Ink 2, sentence case.

### Named Rules
**The Tabular Figures Rule.** Every number that can sit above another number is set with tabular, lining figures: table cells, counts, percentages, probability values, coordinates, timers, the threshold label.

**The Caps Are Labels Rule.** Uppercase condensed type labels a control group, a table column or a nav item. It never sits above a heading as a kicker.

## Layout

The page is a ruled sheet with a sticky title bar. The title bar is 3.5rem tall, white, with a 1px ink rule beneath and a ruler of 1px ticks every 8px hanging 5px below it. It holds the mark, the nav and, on the right, the active model, threshold and field-exam score in a small hairline box.

Content pages centre at a 1240px maximum with 2rem top, 1.25rem side and 4rem bottom padding. A page header (title plus a 68ch intro, tools aligned to its baseline on the right) leads, then sections 2.5rem apart. Panels have 1.1rem by 1.25rem padding; panel sections are divided by 1px rules rather than gaps.

The map page is full-bleed: the map fills the viewport under the title bar and a 22rem margin panel sits on the right behind a 1px ink rule. The panel stacks flight selector, a 2x2 grid of counts ruled like a chart table, the view toggle, the legend and a sticky export button at the bottom. (The direction asked for a 320px margin; the build settled at 22rem, and the build is the record.)

The Identify and Review "work table" is a two-column grid: the photo frame on the left, a 23rem reading column on the right, 1.5rem apart.

### Responsive rules
- **At 1100px and below:** the reading column narrows to 20rem; the field-exam score in the title bar hides.
- **At 900px and below:** the title bar wraps; the nav moves to its own full-width 2.75rem row under a hairline, scrolls horizontally and fades out at the right edge. The map becomes a 62dvh map above the panel, which gains a top ink rule instead of a left one. Work tables and the import steps go to one column; the viewer height becomes automatic (16rem minimum, 72vh maximum). On Review, the human choice buttons move above the model's suggestion and probabilities.
- **At 560px and below:** page padding becomes 1.25rem top, 1rem sides, 3rem bottom; h1 drops to 1.5rem; the mark's subtitle and the words "Modelo" and "Umbral" in the status box hide (the figures stay); the gallery is two columns; tool rows stack full width; the model facts list goes single column; table cells stop wrapping and the table scrolls inside its sheet.
- Hover styles apply only under `(hover: hover) and (pointer: fine)`, so touch never sees a stuck hover.

## Elevation & Depth

The system is flat. Depth is told by paper tone (page `papel`, sheet `hoja`, recessed `margen`), by 1px rules, and by the weight of the rule: hairline `regla` between rows, strong rule around controls, full ink where a region must read as an edge (the title bar's bottom, the map panel's side, the coordinate readout, the empty-map card, the photo frame's corner ticks).

Box-shadow is used only as a ruling device: zero-blur 1px rings around swatches, map symbols and the selected history tile, and inset underlines on nav items. Leaflet's controls have their shadows removed and take a 1px ink border.

### Shadow Vocabulary
- **Map popup** (`box-shadow: 0 6px 20px -8px rgba(19, 32, 43, .45)`): the one soft shadow in the system, under the photo popup that floats over a satellite image, where a rule alone would be lost.

### Named Rules
**The Ruled, Not Raised Rule.** Surfaces never lift. If something must stand apart, give it a heavier rule or a different paper tone. The map popup is the only exception.

## Shapes

Square-cornered chart geometry. Panels, buttons, fields, segments, tables, tooltips and popups all use a 2px radius, enough to soften a pixel edge without reading as rounded. Swatches and probability tracks use 1px. The only round forms are data: map points are circles, and the pending-count badge in the nav is a pill.

Recurring marks: the 8px tick ruler under the title bar; corner ticks (16px arms, 2px thick, in ink, set 7px outside the frame) around the photo viewer and the drop zone; a ruled 2px threshold line crossing every probability track; a 45-degree hatch for doubtful data; a dashed border for the drop zone and for the discard option. Icons are drawn for the station as 24x24 strokes at 1.5px with round caps, never filled glyphs.

## Components

### Buttons
Plain, compact, chart-ruled.
- **Shape:** 2px corners, 1px border, 2.25rem tall (2.75rem for the large size), 0.95rem side padding, Barlow 500 at 0.875rem. An optional 1rem stroke icon leads the label.
- **Default:** white sheet, ink text, strong-rule border; on hover the border goes to full ink.
- **Primary:** aeronautical blue fill and border, white text; hover deepens to the deep blue.
- **Danger:** white with alert-red text and a pale red border; hover adds the red wash and a full red border.
- **Disabled:** margin fill, Ink 3 text, rule border, not-allowed cursor; no press.
- **Press:** `scale(.97)` over 160ms with `cubic-bezier(.23, 1, .32, 1)`; colour and border changes cross-fade in 150ms ease.
- **Focus:** 2px blue outline, 2px offset.
- **On dark (viewer):** transparent with white text and a #5f707d border, white border on hover; over the live camera they sit on translucent night.

### Two-step confirm button
For serious actions (start training, activate a model and re-diagnose everything). The first click arms it: the button fills alert red with white text and its label changes to "Confirmar: ..." stating what will happen. The second click runs the action. If not confirmed, it disarms itself after 4 seconds and restores its label. There is no modal dialog.

### Fields and selects
- **Style:** white, 1px strong-rule border, 2px corners, 2.25rem tall, 0.65rem side padding, Barlow 0.875rem. Selects drop the native chrome and draw a 1.4px ink chevron on the right.
- **Label:** above the control, Barlow 500 0.78rem in Ink 2, 0.3rem gap.
- **Focus:** 2px blue outline at zero offset plus a blue border.
- **Checkboxes and radios:** native, 1rem, accent in blue.

### Segmented control
The view toggle (Points / Zones). A single 1px strong-rule box with 2px corners; segments are 0.45rem by 0.9rem, Barlow 500 0.875rem in Ink 2, divided by hairlines. The selected segment fills with chart ink and white text; it is not blue, because it states a view, not an action. Focus draws the blue outline on the segment. The radios underneath stay real inputs.

### Ficha (category swatch)
The atom of data. A 0.7rem square swatch with 1px corners and a 1px ink ring at 35%, followed by the category name in Barlow 500. The colour never appears without the name.
- **Dudosa (doubtful):** when the model's confidence is below threshold, the swatch loses its category ink and becomes a 45-degree hatch of Ink 3 (1.5px lines every 4px) inside an Ink 3 ring, and the name drops to Ink 3. The same hatch marks an empty swatch.
- **Sizes:** 0.95rem inside choice options, 1.1rem beside a verdict.

### Probability scale (signature component)
Every reading shows its threshold. Each category row has its ficha on the left and the value (Barlow 600, 0.875rem, tabular, one decimal, "%") on the right; the winning row is full ink, the others recede to Ink 2. Under each row runs a 0.6rem track: margin fill, 1px rule border, 1px corners, with faint ink graduations every 10%. The bar fills from the left in the category ink (scaled with `scaleX`, no transition). A 2px ink line crosses every track at the threshold (65% by default, set live from the active model through the `--umbral` custom property), standing 5px above and below the track. A footer row labels "0 %", "umbral 65 %" (600, ink, centred on the line) and "100 %". Below the threshold the verdict reads "no diagnosticable" and the ficha turns doubtful. Each track is a `meter` with its category name for assistive technology.

### Choice options (Review)
Full-width buttons, 3rem minimum height, 1px strong-rule border, 2px corners: swatch, category name in Barlow 500 1rem, and its keyboard key on the right in a `kbd` cap (1px strong-rule border, 2px bottom). The model's suggestion carries a small caps "SUGERIDA" tag in Ink 3. Hover: ink border and paper fill. Pointer press scales to .98 in 160ms. The discard option ("Foto no sirve") sits apart with a dashed border and Ink 2 text.

### Tables
Inside a sheet, full width, Barlow 0.875rem. Header cells are caps labels (Semi Condensed 600, 0.78rem, 0.07em) in Ink 2 on chart paper. Cells pad 0.6rem by 0.9rem with a 1px hairline beneath, none under the last row. Numeric columns align right and use tabular figures. Comparison results use green ink for better and alert red for worse, both at 600. Tables scroll horizontally inside their sheet on narrow screens.

### Marco (corner-tick frame)
The frame around the photo viewer and the drop zone. Four L-shaped ink ticks, 16px arms and 2px thick, drawn 7px outside the frame's edge, like the registration marks of a chart sheet. It carries no border of its own; the viewer inside is night-ground with the photo contained.

### Progress bar
A 0.55rem track in margin tone with a 1px rule border and square ends; the fill is aeronautical blue, scaled from the left, moving in 300ms linear steps as real progress arrives. A tabular count or timer sits in a note above it. Long jobs also show a night-ground monospace log (0.78rem, 1.55 line height, 18rem maximum height).

### Messages
Inline, Barlow 0.875rem, under the action they report on; hidden when empty. A neutral message is Ink 2. Error and success messages switch to full ink and lead with a 1rem stroke icon (a triangle with a bang for error, a check for success) drawn in the text colour; the icon, not a colour, carries the meaning. System-wide notices (no model loaded) are a blue-wash strip under the title bar with a stroke icon and a hairline beneath.

### Empty states
A sheet with 3rem by 1.5rem padding, centred: a headline that states the situation plainly ("No quedan fotos por revisar"), one 52ch paragraph saying why and what to do next, then a row with the primary next action and, when useful, a secondary one. On the map the empty state is a white card with a 1px ink border floating over the map, 26rem maximum, with a single primary action. Before a photo is loaded, the viewer itself is the empty state: a stroke icon, a white headline and the upload and camera buttons on the night ground.

### Map panel and coordinate readout
- **Margin panel:** white, 22rem, 1px ink rule on its map side, sections divided by hairlines. The counts grid is a 2x2 table of figures ruled with hairlines; the count for the highlighted condition is set in red. The legend uses round symbols for points (white 1.5px edge, or a 2.5px ink edge when a person has reviewed it) and square ones for zones. The export button is sticky at the panel's foot.
- **Map grammar:** Leaflet controls, layer switcher and scale take 1px ink borders and 2px corners with no shadow; tooltips take ink borders; the popup is a 15rem photo ficha with its source and a link to review it. The map ground before tiles load is #dfe5e6.
- **Coordinate readout:** the live lat/lon in the map's lower-left margin, like a chart's position box: translucent white (92%), 1px ink border, square corners, Barlow 500 0.78rem with tabular figures, five decimals and a hemisphere letter ("17.99000° N   92.95000° O"). It follows the pointer on desktop and reports the map centre on touch. It never takes pointer events.

### Navigation
Condensed caps items in Ink 2 across the title bar's full height. Hover: ink text with a 2px strong-rule underline. Current page: blue text with a 3px blue inset underline. Review carries an ink pill with the pending count. Under 900px the nav becomes a horizontally scrolling row that fades at its right edge and centres the current item.

### Motion
One gesture: a press. Buttons, choice options, gallery cells and history tiles scale to .97 or .98 on `:active` over 160ms with `cubic-bezier(.23, 1, .32, 1)`. Hover and selection changes are 150ms colour cross-fades (a reading being recomputed dims to 45% in the same 150ms), the technical-zone chevron turns 90 degrees in 200ms on the same curve, and the progress fill steps in 300ms linear with real progress. Labelling by keyboard on Review (number keys, S to skip, Z to undo) acts immediately with no press, no transition and no animation. Under `prefers-reduced-motion: reduce` all transitions drop to 0ms.

## Do's and Don'ts

### Do:
- **Do** use aeronautical blue (`azul`) for the one action that matters on a view and for selection; keep every other control white with a strong-rule border.
- **Do** separate regions with 1px rules (`regla` between rows, full `tinta` at major edges) and paper tone, not shadows or gaps alone.
- **Do** show the threshold line on every probability scale, and say "no diagnosticable" below it; let the doubtful ficha hatch rather than show a category ink.
- **Do** pair every category colour with its name in text.
- **Do** set every comparable number in tabular, lining figures.
- **Do** keep corners at 2px (1px for swatches and tracks).
- **Do** put destructive or heavy actions behind the two-step confirm button: red when armed, self-disarming after 4 seconds.
- **Do** keep motion to the 160ms `cubic-bezier(.23, 1, .32, 1)` press, and leave keyboard labelling instant.
- **Do** draw icons as 24x24 strokes at 1.5px with round caps, in the text colour.

### Don't:
- **Don't** use emojis anywhere: not in labels, messages, empty states, buttons or data.
- **Don't** put an eyebrow or kicker label above a heading. Caps labels name a control group or a column; headings stand on their own.
- **Don't** use category inks (healthy green #2e9e44, Sigatoka red #d7263d, other amber #f0a202) for UI status, buttons, badges or alerts; status uses `rojo`, `verde-tinta`, `azul` and ink.
- **Don't** add drop shadows or elevation; the map popup's shadow is the only one. Box-shadow appears only as zero-blur rings and inset rules.
- **Don't** bring back the green agritech dashboard: no rounded cards, no leaf-icon decoration, no green brand fills.
- **Don't** drift toward a neon drone HUD: no dark theme, no glows, no decorative gradients. Night ground is for the photo viewer and the log only.
- **Don't** introduce a second accent colour or tint the blue for decoration.
- **Don't** animate on keyboard labelling, and don't animate the probability bars.
