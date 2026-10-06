---
version: 1
slug: "ui-templates-base-html"
primary_target: "ui/templates/base.html"
related_targets: ["ui/templates/mapa.html","ui/templates/identificar.html","ui/templates/revisar.html","ui/templates/vuelos.html","ui/templates/modelo.html","ui/static/estacion.css"]
---

# Estación de tierra — superficie de trabajo (Operate)

History: the first build ("carta de vuelo", light chart paper) and two rounds of re-skins
(radar, mesa de luz, señalética; conversación, carretera, parque, libreta) were rejected by the
user: they read as the same page in different colours. Four structurally different concepts
were then prototyped on a design canvas (map first, step by step, phone app, desk with sidebar);
the user chose A, "Mapa primero". Code-led build; no image generation.

## Direction contract

THESIS: The station is the drone's ground-control screen: the plantation map is always the
ground of the app and every task floats over it. It refuses the page-with-tabs dashboard.

OWN-WORLD: Satellite map full-bleed; solid near-black navy panels (#0f171d, #1a2833) with
14–22 px radii and soft drop shadows; one sky-blue action colour (#4da3ff) plus a light
"claro" button (#eaf0f4) for the main step; diagnosis inks (green, red, amber) only for data.
Manrope throughout, heavy 800 headings, tabular numbers.

STORY: The operator sees where the disease is, opens the evidence, confirms or corrects it,
and improves the model only when the field exam says the new one is better.

FIRST VIEWPORT: Top bar (brand pill, flight selector chip, blue "Identificar una hoja"),
left icon rail (Mapa, Vuelos, Revisar with pending badge, Modelo vN), map zones in the middle,
right summary panel ("Así está el lote", big Sigatoka count, stacked bar, red-zone sentence,
"Revisar N fotos pendientes"), bottom photo strip. On a phone the rail becomes a bottom tab bar
and the summary a bottom sheet.

FORM: Map-first ground control, chosen by the user from the four-concept canvas; seed key
28770a99 (round 3, user choice). Signature: the map never leaves; Identificar, Revisar, Vuelos
and Modelo are sheets over the dimmed map, closed back to it. Probability bars keep the white
line at the 65 % minimum. Motion: 160 ms press, 200 ms dim of the map; none on keyboard labelling.

FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
