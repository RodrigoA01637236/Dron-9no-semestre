---
name: Estación Sigatoka
description: Drone ground-control station for banana plantations; the satellite map is always the ground and every task floats over it.
colors:
  fondo-mapa: "#142019"
  panel: "#0f171d"
  panel-2: "#1a2833"
  panel-3: "#22323e"
  riel-activo: "#1f3346"
  borde: "#263844"
  borde-fuerte: "#36505f"
  visor: "#060a0d"
  texto: "#eaf0f4"
  texto-2: "#c9d5dd"
  texto-3: "#9fb0bc"
  acento: "#4da3ff"
  acento-hondo: "#7bbcff"
  acento-tenue: "rgba(77, 163, 255, .16)"
  sobre-acento: "#061423"
  claro: "#eaf0f4"
  sobre-claro: "#0f171d"
  rojo: "#ff5a6e"
  rojo-texto: "#ff8a98"
  verde: "#5fd27a"
  ambar: "#ffc04d"
  bien-texto: "#b9f0c6"
  aviso-fondo: "#3a2d0c"
  aviso-texto: "#ffe6ad"
  gris-dato: "#9aa3a0"
  categoria-sana: "#2e9e44"
  categoria-sigatoka: "#d7263d"
  categoria-otra: "#f0a202"
typography:
  figure:
    fontFamily: "Manrope, Segoe UI, system-ui, sans-serif"
    fontSize: "3.5rem"
    fontWeight: 800
    lineHeight: 1
    letterSpacing: "-0.03em"
    fontFeature: "\"tnum\""
  display:
    fontFamily: "Manrope, Segoe UI, system-ui, sans-serif"
    fontSize: "2.25rem"
    fontWeight: 800
    lineHeight: 1.12
    letterSpacing: "-0.03em"
  verdict:
    fontFamily: "Manrope, Segoe UI, system-ui, sans-serif"
    fontSize: "2.3rem"
    fontWeight: 800
    lineHeight: 1.05
    letterSpacing: "-0.03em"
  headline:
    fontFamily: "Manrope, Segoe UI, system-ui, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 800
    lineHeight: 1.12
    letterSpacing: "-0.02em"
  title:
    fontFamily: "Manrope, Segoe UI, system-ui, sans-serif"
    fontSize: "1.2rem"
    fontWeight: 700
    lineHeight: 1.12
    letterSpacing: "-0.02em"
  body:
    fontFamily: "Manrope, Segoe UI, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 500
    lineHeight: 1.5
  body-small:
    fontFamily: "Manrope, Segoe UI, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 500
    lineHeight: 1.5
  control:
    fontFamily: "Manrope, Segoe UI, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 700
    lineHeight: 1
  label:
    fontFamily: "Manrope, Segoe UI, system-ui, sans-serif"
    fontSize: "0.78rem"
    fontWeight: 700
    lineHeight: 1.4
  mono:
    fontFamily: "ui-monospace, Cascadia Mono, Consolas, monospace"
    fontSize: "0.78rem"
    fontWeight: 400
    lineHeight: 1.55
rounded:
  tag: "6px"
  thumb: "8px"
  s: "10px"
  md: "14px"
  l: "18px"
  xl: "22px"
  pill: "999px"
spacing:
  gutter: "16px"
  gutter-mobile: "10px"
  rail-gap: "12px"
  rail-width: "84px"
  panel-top: "80px"
  panel-pad: "22px"
  sheet-pad: "28px 32px 40px"
  control-height: "2.5rem"
  control-height-large: "3rem"
  topbar-height: "48px"
components:
  button-default:
    backgroundColor: "transparent"
    textColor: "{colors.texto}"
    typography: "{typography.control}"
    rounded: "{rounded.s}"
    padding: "0 1rem"
    height: "{spacing.control-height}"
  button-primario:
    backgroundColor: "{colors.acento}"
    textColor: "{colors.sobre-acento}"
    typography: "{typography.control}"
    rounded: "{rounded.s}"
    padding: "0 1rem"
    height: "{spacing.control-height}"
  button-primario-hover:
    backgroundColor: "{colors.acento-hondo}"
    textColor: "{colors.sobre-acento}"
  button-claro:
    backgroundColor: "{colors.claro}"
    textColor: "{colors.sobre-claro}"
    typography: "{typography.control}"
    rounded: "{rounded.s}"
    padding: "0 1rem"
    height: "{spacing.control-height}"
  button-claro-hover:
    backgroundColor: "#ffffff"
    textColor: "{colors.sobre-claro}"
  button-grande:
    rounded: "{rounded.md}"
    padding: "0 1.3rem"
    height: "{spacing.control-height-large}"
  button-confirmando:
    backgroundColor: "{colors.rojo}"
    textColor: "#ffffff"
  button-icono:
    backgroundColor: "{colors.panel-2}"
    textColor: "{colors.texto}"
    rounded: "{rounded.s}"
    size: "40px"
  button-icono-hover:
    backgroundColor: "{colors.panel-3}"
    textColor: "#ffffff"
  input-field:
    backgroundColor: "{colors.panel-2}"
    textColor: "{colors.texto}"
    rounded: "{rounded.s}"
    padding: "0 .75rem"
    height: "{spacing.control-height}"
  segmented:
    backgroundColor: "{colors.panel-2}"
    rounded: "{rounded.s}"
    padding: "4px"
  segmented-option-checked:
    backgroundColor: "{colors.claro}"
    textColor: "{colors.sobre-claro}"
    rounded: "{rounded.thumb}"
    padding: ".45rem .95rem"
  chip-diagnostico:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.texto}"
    rounded: "{rounded.pill}"
    padding: ".35rem .8rem"
  que-hacer:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.texto-2}"
    typography: "{typography.body-small}"
    rounded: "{rounded.md}"
    padding: ".9rem 1rem"
  topbar-pill:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.texto}"
    rounded: "{rounded.md}"
    padding: "0 16px"
    height: "{spacing.topbar-height}"
  rail:
    backgroundColor: "{colors.panel}"
    rounded: "{rounded.l}"
    padding: "8px"
    width: "{spacing.rail-width}"
  rail-item-active:
    backgroundColor: "{colors.riel-activo}"
    textColor: "{colors.texto}"
    rounded: "{rounded.s}"
  panel-resumen:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.texto}"
    rounded: "{rounded.l}"
    padding: "{spacing.panel-pad}"
    width: "350px"
  hoja-flotante:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.texto}"
    rounded: "{rounded.xl}"
    padding: "{spacing.sheet-pad}"
  tarjeta:
    backgroundColor: "{colors.panel-2}"
    rounded: "{rounded.l}"
    padding: "18px 20px"
  vuelo-row:
    backgroundColor: "{colors.panel-2}"
    rounded: "{rounded.md}"
    padding: "1rem 1.25rem"
  celda-foto:
    backgroundColor: "{colors.panel-2}"
    textColor: "{colors.texto}"
    rounded: "{rounded.md}"
  opcion-revisar:
    backgroundColor: "{colors.panel}"
    textColor: "{colors.texto}"
    rounded: "{rounded.s}"
    padding: ".6rem .9rem"
    height: "3.1rem"
  vacio:
    backgroundColor: "{colors.panel-2}"
    rounded: "{rounded.l}"
    padding: "2.5rem 1.5rem"
  aviso:
    backgroundColor: "{colors.aviso-fondo}"
    textColor: "{colors.aviso-texto}"
    rounded: "{rounded.md}"
    padding: ".85rem 1rem"
---

# Design System: Estación Sigatoka

## Overview

**Creative North Star: "Mapa primero" (the map comes first)**

The station is the drone's ground-control screen. The satellite map of the plantation is the full-screen ground of every page, and every task floats over it on solid near-black navy panels: a dark top bar of separate floating pills, an icon rail on the left, a summary panel on the right and a photo strip along the bottom. Identificar, Revisar, Vuelos and Modelo are not pages that replace the map; they are floating sheets laid over a dimmed map and closed back to it. The system refuses the page-with-tabs dashboard.

The world is dark because the imagery is the colour. Panels are opaque, flat inside and lifted from the map by one soft shadow. A single sky-blue carries the one global action; a light "claro" button marks the next step on whatever surface is open. The diagnosis inks (green, red, amber, and the categories' own hexes) are reserved for data: zones, points, swatches, bars. Type is Manrope throughout, heavy (800) for headings and figures, with tabular numbers wherever a count or percentage appears. Copy is plain-language Spanish written for an agronomist, not a data scientist: "El modelo no está seguro", "Revisar 12 fotos pendientes".

Density is moderate: a laptop on a work table, sometimes a phone on the same WiFi, often bright light. Controls are 40 px tall at minimum, focus rings are a 2 px blue outline, and colour is never the only signal (every swatch carries a name).

**Key Characteristics:**
- The map never leaves: full-bleed at z-index 0, interactive on Mapa, dimmed to 30 % and half-grey behind every sheet.
- Opaque navy panels (#0f171d over the map, #1a2833 inside panels) with 14 to 22 px radii.
- One shadow token, used only by panels that float over imagery.
- One blue action, one light "claro" step button; everything else is outlined.
- Diagnosis inks only for data; uncertain results are hatched grey, never a guessed colour.
- Manrope 500 body, 700 controls, 800 headings and figures; tabular numerals.
- Probability bars always show the white line at the 65 % minimum.

## Colors

A near-black navy panel family over a satellite photograph, lit by one sky-blue and one off-white, with saturated diagnosis inks held back for data.

### Primary
- **Sky Signal Blue** (`acento`): the one action colour. Fills the top-bar "Identificar una hoja" button and form commits ("Guardar para revisión", "Subir y diagnosticar"); also the focus outline, caret, checkbox accent, upload progress fill and the selected border of a history thumbnail. Text on it is `sobre-acento` (deep navy), never white.
- **Lifted Blue** (`acento-hondo`): hover state of the blue button and the colour of links, "Más opciones" summaries and the small "la propuesta" tag in Revisar.
- **Blue Wash** (`acento-tenue`): the only tint of blue, used as the drag-over fill of the upload drop zone.

### Secondary
- **Claro** (`claro`, same value as `texto`): the light button for the main step of the current surface ("Revisar N fotos pendientes", "Subir un vuelo", "Elegir foto", "Reentrenar ahora", "Revisar N" on a flight row) and the checked segment in a segmented control. Text on it is `sobre-claro`. Hover goes to pure white.

### Neutral
- **Map Ground** (`fondo-mapa`): a dark leaf-green that shows before tiles load and when the "Sin fondo" base layer is chosen offline. It is the body background too.
- **Panel** (`panel`): every surface that floats over the map: top-bar pills, rail, summary panel, photo strip, sheets, legend, Leaflet controls, popups, tooltips. Also the track of bars and the que-hacer box inside panels.
- **Panel 2** (`panel-2`): the layer inside a panel: cards (tarjeta), flight rows, photo cells, tables, the photo-and-reading table (mesa), fields, segmented track, icon buttons, empty states.
- **Panel 3** (`panel-3`): hover of icon buttons and review options; placeholder behind cell images.
- **Rail Active** (`riel-activo`): background of the current rail item.
- **Rule** (`borde`) and **Strong Rule** (`borde-fuerte`): table and fact-list dividers use `borde`; outlined buttons, fields, review options, the dashed drop zone and scrollbars use `borde-fuerte`.
- **Viewer Black** (`visor`): behind photos and video in the mesa, and behind the training log.
- **Text scale**: `texto` for headings, values and primary labels; `texto-2` for body prose and secondary values; `texto-3` for notes, field labels, table headers, inactive rail items and placeholders. Pure white is used only for emphasis inside dark copy (`b` in que-hacer and confidence lines) and for hover text.

### Diagnosis inks (data only)
- **Zone ramp** (`verde`, `ambar`, `rojo`): fill and stroke of map zones: no cases, up to 25 %, more than 25 % of photos with the selected condition. Repeated in the legend. `verde` and `rojo-texto` also colour "N pts mejor / peor" in the model table, which is data.
- **Category inks** (`categoria-sana`, `categoria-sigatoka`, `categoria-otra`): defined in data (ui/datos.py), editable by the technical team, and drawn wherever a single photo's diagnosis appears: swatches, map points, probability bars, the stacked bar, the diagnosis chip dot.
- **Data Grey** (`gris-dato`): "No está seguro", "Sin diagnóstico" and "La foto no sirve" in points, bars and the stacked bar.

### Alert and message colours
- **Alert Red** (`rojo`) doubles as the attention colour: the pending-count badge on the rail, the armed state of a two-step button and the "En vivo" camera tag. **Error Text** (`rojo-texto`) is the readable red for error messages on dark panels.
- **Success Text** (`bien-texto`): text of success messages. It is deliberately not `verde`.
- **Warning** (`aviso-fondo` / `aviso-texto`): the floating "No hay modelo cargado" notice.

### Named Rules
**The Data Ink Rule.** Green, amber and the category inks mean a diagnosis and nothing else. Do not use them for buttons, success states, progress or navigation. Red is the single shared hue: it marks Sigatoka-heavy zones in data and "needs attention now" in the chrome (badge, armed confirm, live camera), and it gets no third meaning.

**The One Blue Rule.** Sky blue is the action and the focus ring. One blue button per surface at most; the next step on a surface is the claro button, not a second blue one.

**The Colour Never Alone Rule.** Every swatch, dot and bar is paired with its category name or a sentence; the map legend names every colour.

## Typography

**Display Font:** Manrope (with Segoe UI, system-ui, sans-serif), self-hosted woff2 so the station works offline.
**Body Font:** Manrope, the same family.
**Label/Mono Font:** ui-monospace, Cascadia Mono, Consolas, for code, file paths, keyboard keys and the training log only.

**Character:** One geometric-humanist sans in weights 500 to 800. Headings and figures go heavy and slightly tight (-0.02 to -0.03 em) so they read across a room at a demo; body stays at 500 for legibility on modest, sunlit laptop screens.

### Hierarchy
- **Figure** (800, 3.5rem, line-height 1, -0.03em, tabular): the big Sigatoka count in the summary panel, coloured with the zone red because it is data.
- **Verdict** (800, 2.3rem, 1.05, -0.03em; 1.9rem below 560 px): the plain sentence result in Identificar and Revisar ("Esta hoja tiene Sigatoka", "El modelo no está seguro").
- **Display** (800, 2.25rem, 1.12, -0.03em; 1.8rem below 560 px): the h1 of each sheet. The summary panel's "Así está el lote" and "Empieza aquí" use it at 1.6rem.
- **Headline** (800, 1.5rem, 1.12, -0.02em): h2, empty-state titles, drop-zone titles. Section h2 inside sheets drop to 1.2rem.
- **Title** (700, 1.2rem): h3; flight names in rows use it at 1rem.
- **Body** (500, 1rem, 1.5): prose; sheet intros cap at 64ch, empty-state copy at 52ch.
- **Body small** (500, 0.875rem): notes, legends, table cells, que-hacer, messages.
- **Control** (700, 0.875rem, line-height 1): buttons and the flight chip; primario and claro buttons go to 800.
- **Label** (700, 0.78rem, sentence case): rail item names, field labels above inputs, table headers, photo-strip captions. Never uppercase, never letter-spaced.

### Named Rules
**The Tabular Count Rule.** Every number that can change (counts, percentages, coordinates, times) uses tabular numerals, so values do not jitter as they update.

**The Sentence Case Rule.** Labels are short Spanish sentence-case phrases. No uppercase tracking, no category labels above headings.

## Layout

A fixed overlay layout over a full-bleed map; nothing scrolls at the body level (`overflow: hidden`), and each floating panel scrolls internally.

- **Map**: `#mapa-base` fixed at inset 0. A vignette (`rgba(8, 14, 18, .55)` fading to clear at 16 % and from 72 %) sits above it so the top bar and photo strip stay legible. On sheet pages the body gets `con-hoja`: the map drops to 30 % opacity with 50 % greyscale and stops taking pointer events, and the vignette becomes a flat `rgba(8, 14, 18, .35)` dim. The map still loads the current flight's points behind the sheet.
- **Top bar**: fixed 16 px from the top, left and right; 12 px gaps; the bar itself is transparent and only its pieces catch the pointer. Pieces are 48 px tall: the brand pill (mark plus "Estación Sigatoka"), the flight selector chip (a select styled as a panel pill, max 46vw), a flexible spacer, and the blue "Identificar una hoja" button.
- **Rail**: fixed at left 16 px, top 80 px, 84 px wide, 8 px padding, 4 px between items. Items are icon (22 px) over label, with a red count badge on Revisar and the live model version ("Modelo v3") as the last label.
- **Map legend**: a small panel at top 80 px, just right of the rail (16 + 84 + 12 px), with the zone or category key and a live coordinate readout.
- **Summary panel**: fixed right 16 px, top 80 px, 350 px wide (310 px below 1100 px), 22 px padding, 18 px gaps, max height viewport minus 96 px. Order: flight line, "Así está el lote", the big figure, stacked bar with counts, que-hacer sentence about red zones, Zonas/Fotos segmented control, "Más opciones", the claro "Revisar N fotos pendientes", the outlined download button, the GPS accuracy note. On first run it holds three numbered steps instead.
- **Photo strip**: fixed 16 px from the bottom, spanning from the rail's right edge to the summary panel's left edge; 12 px padding, 10 px gaps, horizontal scroll; 128 x 84 px thumbnails with a swatch caption, ending in "Ver las N".
- **Sheets**: fixed from top 80 px to bottom 16 px, from the rail's right edge to right 16 px; content centred at max 1240 px with 28/32/40 px padding. A header row holds the h1 and intro on the left and actions plus the close icon button on the right; sections follow at 32 px intervals.
- **Breakpoints**: 1100 px narrows the summary panel. Below 900 px the rail width becomes 0 and the rail turns into a bottom tab bar (10 px from the bottom and sides, items flexed evenly); gutters shrink to 10 px; top-bar pieces shrink to 44 px and lose the brand name and the long button text; the summary panel becomes a bottom sheet above the tab bar (bottom 86 px, max height 42dvh, 18 px padding); the photo strip and the sheet close buttons are hidden (the tab bar is the way back); sheets run from top 64 px to bottom 86 px. Below 560 px photo grids drop to two columns, toolbars stack and fact lists go single-column.

### Named Rules
**The Map Never Leaves Rule.** No surface is opaque edge to edge. Sheets stop 16 px short of the viewport (10 px on phones) and the rail's column, so the map is always visible around them.

## Elevation & Depth

Hybrid: one drop shadow for anything floating over the map, tonal layering for everything inside a panel. Depth inside a panel comes from stepping `panel` to `panel-2` to `panel-3`, never from another shadow.

### Shadow Vocabulary
- **Float** (`box-shadow: 0 14px 34px -14px rgba(0, 0, 0, .7)`): top-bar pills and button, rail, legend, summary panel, photo strip, sheets, the warning notice, and the restyled Leaflet bars, layer control, popups and tooltips.

### Named Rules
**The Imagery-Only Shadow Rule.** Shadows exist because these panels sit over a photograph. A card, row, cell or table inside a panel is flat.

## Shapes

Soft, generous corners that grow with the size of the surface: 22 px sheets, 18 px rail, summary panel, photo strip, cards and empty states, 14 px top-bar pills, large buttons, rows, cells, popups and que-hacer, 10 px controls, fields and rail items, 8 px thumbnails, segment options and tooltips, 6 px code and key caps, fully round chips and badges. Swatches are 0.7rem squares with 3 px corners; map points and diagnosis-chip dots are circles. Borders are 1 px and used only on outlined controls and dividers; dashed borders mark the drop zone and the "La foto no sirve" option.

## Components

### Buttons
Tactile and plain: label first, an 18 px stroke icon when it helps.
- **Shape:** 10 px corners (`rounded.s`), 2.5rem tall; the large size is 3rem with 14 px corners and 1rem text.
- **Default:** transparent with a `borde-fuerte` outline and `texto` label; hover lightens the outline to `texto-3` and the label to white (only on hover-capable pointers).
- **Primario:** sky blue fill, navy label, weight 800. One per surface.
- **Claro:** off-white fill, navy label, weight 800; the main step of the surface.
- **Icon:** 40 px square, `panel-2` fill, no border; hover `panel-3`. Used for the sheet close button.
- **Two-step confirm:** for serious actions (start training, activate a model). The first click arms the button: it turns `rojo` with a white label and reads "Confirmar: …". The second click runs the action; it disarms by itself after 4 s.
- **Press:** every button scales on press (0.97, icon buttons 0.95) over 160 ms; disabled is 45 % opacity with a not-allowed cursor.

### Inputs / Fields
- **Style:** `panel-2` fill, 1 px `borde-fuerte` stroke, 10 px corners, 2.5rem tall, 600 weight 0.875rem text, `texto-3` placeholder. A field is a small 700 label stacked 0.35rem above its control.
- **Select:** native select with appearance removed and a two-gradient chevron in `texto-2`. In the top bar the flight select becomes a 48 px panel pill with a shadow and no stroke.
- **Focus:** 2 px `acento` outline at 0 offset and the border turns blue.

### Segmented control
A `panel-2` track with 4 px padding and gaps; options are hidden radios over 8 px-cornered labels in `texto-2`. The checked option fills claro with a navy label. Keyboard focus outlines the option in blue.

### Diagnosis chip and swatch ficha
- **Diagnosis chip:** a fully round `panel` pill, 800 weight, with a 10 px dot in the category ink before the name. Heads the reading in Identificar and Revisar.
- **Ficha:** a 0.7rem swatch with 3 px corners followed by the name in 700. It is the only way a diagnosis appears inline (cells, popups, the photo strip, fact lists).
- **Uncertain state:** when confidence is below the minimum the swatch is hatched (45° stripes of `texto-3`, 1.5 px on 4 px, with a 1 px inset ring) and the name turns `texto-3` and reads "No está seguro". The colour of the guessed class is never shown.

### Probability bars
One row per class, highest first: name and tabular percentage above a 10 px `panel` track with 5 px corners, filled in the class ink by a left-anchored scale. A 2 px white (`texto`) vertical line crosses every track at the minimum confidence (65 %, set from the live threshold), and a note under the bars says "La línea blanca marca la seguridad mínima: 65 %". Non-winning rows drop to `texto-2`.

### Que-hacer box
A `panel` box with 14 px corners and 0.9rem/1rem padding, 0.875rem text at 1.55 line height in `texto-2`, opening with a bold white "Qué hacer:". It turns a result into one practical instruction. The summary panel reuses it for the red-zones sentence.

### Flight rows
A `panel-2` row with 14 px corners in four columns: name and upload date, photo and GPS counts, a "N de M revisadas" note over an 8 px blue progress bar, and actions (claro "Revisar N" when work is pending, otherwise outlined "Revisado"; "Ver fotos"; "Mapa"). Two columns below 900 px, one below 560 px.

### Photo cells
Grid of 11rem-minimum cells: `panel-2`, 14 px corners, 4:3 cover image, then a ficha and a small note line. A 2 px transparent border turns `borde-fuerte` on hover; press scales to 0.98. History thumbnails in Identificar use the same shape with a blue border when selected.

### Review options
Full-width rows on `panel`, 1 px `borde-fuerte`, 10 px corners, at least 3.1rem tall: swatch, category name (with "la propuesta" in lifted blue on the model's suggestion) and a key cap with the shortcut number. The discard option is dashed and lighter.

### Tables
Wrapped in a `panel-2` frame with 14 px corners and horizontal scroll. Cells 0.75rem/1rem padding, `borde` dividers, last row open; headers 0.78rem 700 in `texto-3`; numbers right-aligned and tabular. Fact lists (`dl`) use a 12rem term column with `borde` rules.

### Messages
Small (0.875rem) lines under the control they concern, hidden when empty. Errors are `rojo-texto` and successes `bien-texto`, each led by a 1rem masked stroke icon (warning triangle, check mark) in the text colour. The no-model notice is a floating warning panel with the same triangle icon at top 76 px.

### Empty states
A `panel-2` block with 18 px corners, centred, 2.5rem/1.5rem padding: a headline that states the situation ("No quedan fotos por revisar"), a 52ch sentence saying what to do next, and buttons with the claro one first. The first-run summary panel uses numbered 32 px circles for its three steps.

### Navigation
Rail items are 0.78rem 700 labels in `texto-3` under 22 px stroke icons; hover lifts to `texto` on `panel-2`; the current page fills `riel-activo` with `texto`. The pending badge is a red pill (11 px text) at the item's top right. Below 900 px the same items lie in a row as the bottom tab bar.

### Leaflet restyle
Leaflet is dressed as station chrome: Manrope 500 0.875rem, `fondo-mapa` behind tiles. Zoom and layer controls are 36 px `panel` buttons with `borde` separators, 10 px corners and the float shadow; the layer icon is inverted to white. Attribution and scale line sit on 75 % `panel`. Popups are `panel` with 14 px corners holding a 15rem photo card (4:3 image, ficha, meta, "Revisar esta foto"); tooltips are `panel` with 8 px corners. Points are circle markers filled with the diagnosis ink (radius 6.5, 8 when highlighted), stroked navy for model results and off-white 2.5 px for human-reviewed ones. Zones are rectangles in the zone ramp, 1.5 px stroke, fill opacity rising from 0.18 with the photo count.

### Motion
- **Press:** 160 ms `transform` on `cubic-bezier(.23, 1, .32, 1)` for buttons, icon buttons, review options, cells and history thumbnails.
- **Map dim:** 200 ms ease on the map's opacity and filter when a sheet is present.
- **Colour changes:** 150 ms ease on background, border and text colour; the technical-zone chevron rotates in 200 ms; upload progress moves linearly over 300 ms.
- **Keyboard labelling:** nothing animates. Pressing 1 to 3, 0, S or Z in Revisar swaps straight to the next photo so a reviewer can label at speed.
- **Reduced motion:** `prefers-reduced-motion: reduce` sets every transition to 0 ms.

## Do's and Don'ts

### Do:
- **Do** keep the satellite map visible on every page; open tasks as sheets over the dimmed map (30 % opacity, 50 % greyscale) and close them back to it.
- **Do** put every floating panel on `panel` (#0f171d) with the single float shadow, and layer inside it with `panel-2` and `panel-3`.
- **Do** use one blue primario button per surface and the claro button for the surface's main next step.
- **Do** draw diagnoses as a swatch plus a name, hatch anything below the 65 % minimum and keep the white minimum line on every probability bar.
- **Do** use Manrope 800 for headings and figures and tabular numerals for every count and percentage.
- **Do** write labels and messages in plain-language Spanish that says what to do next ("Toma otra foto más cerca…").
- **Do** arm serious actions with the two-step confirm instead of a modal.
- **Do** keep the 160 ms press and the 200 ms map dim, and keep keyboard labelling instant.

### Don't:
- **Don't** use emojis anywhere in the interface.
- **Don't** add eyebrow or kicker labels above headings; the line above "Así está el lote" is data (flight and photo count), not a label.
- **Don't** use diagnosis colours (green, amber, the category inks) as UI status for success, progress, navigation or buttons; red's only chrome role is "needs attention now".
- **Don't** hide or replace the map with a full-page opaque surface, and don't open a page that has no map behind it.
- **Don't** put shadows on cards, rows, cells or tables inside a panel.
- **Don't** show a guessed class colour for an uncertain result.
- **Don't** add a second accent colour or light-mode panels; the claro button is the only light surface.
- **Don't** use uppercase, letter-spaced labels or technical jargon in user-facing copy; technical terms stay in the "Zona del equipo técnico".
