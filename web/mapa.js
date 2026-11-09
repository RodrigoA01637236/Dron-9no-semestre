// Mapa del lote en el sitio público. Lee el GeoJSON que exporta la estación de tierra
// (ui/estacion.py, /api/geojson) y lo dibuja con la misma lógica de zonas que la estación
// (ui/static/mapa.js). Todo pasa en el navegador: el archivo no se sube a ningún lado.

const GRIS = "#7d8b96";
const NO_DIAGNOSTICA = new Set(["sin_hoja"]);          // no dicen nada del cultivo: no cuentan para zonas
const PRIORIDAD = ["sigatoka", "otra_condicion", "sana"]; // en un empate, la zona toma lo más grave
const prioridad = k => (PRIORIDAD.indexOf(k) + 1) || 99;
const op = { vista: "condicion", objetivo: "sigatoka", metros: 20, ocultas: new Set(), vuelo: "" };
const extra = {};  // categorías que trae el archivo y el sitio no conoce (las agregadas en la estación)
let mapa = null, capa = null, todas = [];

const cat = k => CATEGORIAS[k] || extra[k] || { nombre: k || "Sin diagnóstico", color: GRIS };
const plural = (n, uno, varios) => `${n} ${n === 1 ? uno : varios}`;
const coord = (v, pos, neg) => `${Math.abs(v).toFixed(5)}° ${v >= 0 ? pos : neg}`;

// "38 sanas", "10 con Sigatoka", "4 sin hojas de plátano".
function cuantas(clave, n) {
  const nombre = cat(clave).nombre;
  if (clave === "sana") return `${n} ${n === 1 ? "sana" : "sanas"}`;
  if (/^sin /i.test(nombre)) return `${n} ${nombre.charAt(0).toLowerCase()}${nombre.slice(1)}`;
  return `${n} con ${clave === "otra_condicion" ? "otra condición" : nombre}`;
}

// ------------------------------------------------------------------ leer el archivo

function claveDeNombre(nombre) {
  const n = String(nombre || "").trim().toLowerCase();
  const hallada = Object.entries(CATEGORIAS).find(([k, c]) => c.nombre.toLowerCase() === n || k === n);
  return hallada ? hallada[0] : (n || null);
}

function leerFoto(f) {
  const p = f.properties || {};
  const [lon, lat] = f.geometry.coordinates;
  const clave = p.clave || claveDeNombre(p.diagnostico);
  if (clave && !CATEGORIAS[clave] && !extra[clave]) extra[clave] = { nombre: p.diagnostico || clave, color: p.color || GRIS };
  const humano = p.fuente === "revisión humana";
  const conf = typeof p.confianza_modelo === "number" ? p.confianza_modelo : null;
  // Archivos nuevos traen "dudoso"; en los viejos se calcula con el umbral de 65 %.
  const dudoso = typeof p.dudoso === "boolean" ? p.dudoso : (!humano && conf != null && conf < (p.umbral ?? 0.65));
  return { lat: +lat, lon: +lon, clave, dudoso: !clave || dudoso, humano, conf,
           fecha: p.fecha, vuelo: p.vuelo || "", archivo: p.archivo, revisor: p.revisor };
}

async function abrir(archivo) {
  $("msg-archivo").textContent = "";
  try {
    const datos = JSON.parse(await archivo.text());
    const feats = (datos.features || []).filter(f => f?.geometry?.type === "Point" && Array.isArray(f.geometry.coordinates));
    const fotos = feats.map(leerFoto).filter(f => Number.isFinite(f.lat) && Number.isFinite(f.lon));
    if (!fotos.length) throw new Error("no trae fotos con ubicación");
    todas = fotos;
    $("pie-archivo").textContent = archivo.name;
    mostrar();
  } catch (e) {
    $("msg-archivo").textContent = `No pude leer ese archivo (${e.message}). Tiene que ser el .geojson que descarga la estación en Mapa.`;
  }
}

// ------------------------------------------------------------------ mapa

function iniciarMapa() {
  mapa = L.map("mapa", { zoomControl: false }).setView([17.99, -92.95], 15);
  const fondos = {
    "Satélite": L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
      { maxZoom: 20, maxNativeZoom: 19, attribution: "Imágenes © Esri" }),
    "Calles": L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png",
      { maxZoom: 20, maxNativeZoom: 19, attribution: "© OpenStreetMap" }),
    "Sin fondo": L.layerGroup(),
  };
  fondos["Satélite"].addTo(mapa);
  L.control.zoom({ position: "topright" }).addTo(mapa);
  L.control.layers(fondos, null, { position: "topright" }).addTo(mapa);
  L.control.scale({ imperial: false, position: "bottomleft" }).addTo(mapa);
  mapa.on("mousemove", e => { $("lectura-pos").textContent = `${coord(e.latlng.lat, "N", "S")}  ${coord(e.latlng.lng, "E", "O")}`; });
  capa = L.layerGroup().addTo(mapa);
}

const fotos = () => op.vuelo ? todas.filter(f => f.vuelo === op.vuelo) : todas;
const claveDe = f => f.dudoso ? "dudoso" : f.clave;
const visible = f => !op.ocultas.has(claveDe(f));

function paso(lista) {
  const lat0 = lista.reduce((s, f) => s + f.lat, 0) / lista.length;
  return { dLat: op.metros / 111320, dLon: op.metros / (111320 * Math.cos(lat0 * Math.PI / 180)) };
}

function ficha(f) {
  const c = f.dudoso ? { nombre: "No está seguro", color: GRIS } : cat(f.clave);
  const fuente = f.humano ? `Revisada${f.revisor ? " por " + esc(f.revisor) : ""}`
    : f.conf != null ? `Modelo: ${pct(f.conf)}${f.dudoso && f.clave ? ` (parece ${esc(cat(f.clave).nombre)})` : ""}` : "Sin diagnóstico";
  return `<div class="ficha-mapa"><span class="ficha"><i class="muestra" style="background:${c.color}"></i>${esc(c.nombre)}</span>
    <div class="meta">${fuente}<br>${esc(f.fecha || "")}${f.archivo ? `<br>${esc(f.archivo)}` : ""}</div></div>`;
}

function dibujarPuntos() {
  fotos().filter(visible).forEach(f => {
    const color = f.dudoso ? GRIS : cat(f.clave).color;
    const resalta = !f.dudoso && f.clave === op.objetivo;
    L.circleMarker([f.lat, f.lon], {
      radius: resalta ? 8 : 6.5, color: f.humano ? "#eaf0f4" : "#0f171d", weight: f.humano ? 2.5 : 1.5,
      fillColor: color, fillOpacity: resalta ? .95 : .7,
    }).bindPopup(ficha(f)).addTo(capa);
  });
}

function zonasCondicion() {
  const lista = fotos();
  if (!lista.length) return [];
  const { dLat, dLon } = paso(lista);
  const celdas = new Map();
  lista.forEach(f => {
    if (f.dudoso || NO_DIAGNOSTICA.has(f.clave) || op.ocultas.has(f.clave)) return;
    const i = Math.floor(f.lat / dLat), j = Math.floor(f.lon / dLon), k = `${i}|${j}`;
    const c = celdas.get(k) || { i, j, n: 0, cuenta: {}, dLat, dLon };
    c.n++; c.cuenta[f.clave] = (c.cuenta[f.clave] || 0) + 1;
    celdas.set(k, c);
  });
  return [...celdas.values()].map(c => ({
    ...c, dominante: Object.keys(c.cuenta).sort((a, b) => c.cuenta[b] - c.cuenta[a] || prioridad(a) - prioridad(b))[0],
  }));
}

function dibujarCondicion() {
  zonasCondicion().forEach(c => {
    const color = cat(c.dominante).color;
    const algoDeSigatoka = c.dominante !== "sigatoka" && c.cuenta.sigatoka;
    const detalle = Object.entries(c.cuenta).sort((a, b) => b[1] - a[1])
      .map(([k, n]) => `${esc(cat(k).nombre)}: ${n}`).join(" · ");
    L.rectangle([[c.i * c.dLat, c.j * c.dLon], [(c.i + 1) * c.dLat, (c.j + 1) * c.dLon]], {
      color: algoDeSigatoka ? cat("sigatoka").color : color, weight: algoDeSigatoka ? 2.5 : 1.5,
      dashArray: algoDeSigatoka ? "5 4" : null, fillColor: color, fillOpacity: .25 + .35 * Math.min(1, c.n / 10),
    }).bindTooltip(`<b>${esc(cat(c.dominante).nombre)}</b> · ${plural(c.n, "foto", "fotos")}<br>${detalle}`).addTo(capa);
  });
}

function zonasUna() {
  const lista = fotos();
  if (!lista.length) return [];
  const { dLat, dLon } = paso(lista);
  const celdas = new Map();
  lista.forEach(f => {
    if (f.dudoso || NO_DIAGNOSTICA.has(f.clave)) return;
    const i = Math.floor(f.lat / dLat), j = Math.floor(f.lon / dLon), k = `${i}|${j}`;
    const c = celdas.get(k) || { i, j, n: 0, pos: 0, dLat, dLon };
    c.n++; c.pos += f.clave === op.objetivo;
    celdas.set(k, c);
  });
  return [...celdas.values()];
}

function dibujarUna() {
  const nombre = cat(op.objetivo).nombre;
  zonasUna().forEach(c => {
    const p = c.pos / c.n;
    const color = p === 0 ? "#5fd27a" : p <= .25 ? "#ffc04d" : "#ff5a6e";
    L.rectangle([[c.i * c.dLat, c.j * c.dLon], [(c.i + 1) * c.dLat, (c.j + 1) * c.dLon]], {
      color, weight: 1.5, fillColor: color, fillOpacity: .18 + .3 * Math.min(1, c.n / 10),
    }).bindTooltip(`${plural(c.n, "foto", "fotos")} · ${c.pos} con ${esc(nombre)} (${Math.round(p * 100)} %)`).addTo(capa);
  });
}

function dibujar() {
  capa.clearLayers();
  if (op.vista === "condicion") dibujarCondicion();
  else if (op.vista === "zonas") dibujarUna();
  else dibujarPuntos();
}

// ------------------------------------------------------------------ leyenda y resumen

function chipCapa(clave, nombre, muestra) {
  const prendida = !op.ocultas.has(clave);
  return `<button type="button" class="chip-capa" data-clave="${esc(clave)}" aria-pressed="${prendida}"
    title="${prendida ? "Ocultar" : "Mostrar"} ${esc(nombre)}">${muestra}${esc(nombre)}</button>`;
}

function categoriasDelArchivo() {
  const claves = [...new Set(todas.map(f => f.clave).filter(Boolean))];
  return claves.sort((a, b) => prioridad(a) - prioridad(b)).map(k => ({ clave: k, ...cat(k) }));
}

function leyenda() {
  const cats = categoriasDelArchivo();
  let html;
  if (op.vista === "zonas") {
    const nombre = esc(cat(op.objetivo).nombre);
    html = `<span><i style="background:#5fd27a"></i>Sin ${nombre}</span><span><i style="background:#ffc04d"></i>Hasta 25 %</span><span><i style="background:#ff5a6e"></i>Más de 25 %</span>`;
  } else if (op.vista === "condicion") {
    html = cats.filter(c => !NO_DIAGNOSTICA.has(c.clave)).map(c => chipCapa(c.clave, c.nombre, `<i style="background:${c.color}"></i>`)).join("") +
      (cats.some(c => c.clave === "sigatoka") ? `<span><i style="border:2px dashed ${cat("sigatoka").color}; background:none"></i>Hay algo de Sigatoka</span>` : "");
  } else {
    html = cats.map(c => chipCapa(c.clave, c.nombre, `<i class="punto" style="background:${c.color}"></i>`)).join("") +
      chipCapa("dudoso", "No está seguro", `<i class="punto" style="background:${GRIS}"></i>`) +
      `<span><i class="punto" style="border:2px solid #eaf0f4"></i>Revisada</span>`;
  }
  $("leyenda").innerHTML = html;
  $("leyenda").querySelectorAll(".chip-capa").forEach(b => b.onclick = () => {
    const k = b.dataset.clave;
    op.ocultas.has(k) ? op.ocultas.delete(k) : op.ocultas.add(k);
    dibujar(); leyenda(); resumen();
  });
  $("caja-objetivo").classList.toggle("oculto", op.vista !== "zonas");
  $("caja-zona").classList.toggle("oculto", op.vista === "puntos");
}

function mensajePuntos() {
  return "Cada punto es una foto: tócalo para ver su diagnóstico. Los grises son fotos donde el modelo no está seguro; " +
    "los de borde blanco ya los revisó alguien del equipo.";
}

function mensajeCondicion() {
  const zonas = zonasCondicion();
  if (!zonas.length) return op.ocultas.size ? "No queda ninguna zona a la vista: prende alguna condición en la leyenda."
    : "El archivo no trae fotos con diagnóstico seguro.";
  const por = {};
  zonas.forEach(z => { por[z.dominante] = (por[z.dominante] || 0) + 1; });
  const conSig = zonas.filter(z => z.cuenta.sigatoka).length;
  const partes = Object.entries(por).sort((a, b) => b[1] - a[1]).map(([k, n]) => esc(cuantas(k, n)));
  return `De <b>${plural(zonas.length, "zona", "zonas")}</b> de ${op.metros} m con fotos: ${partes.join(", ")}.` +
    (conSig ? ` <b>${plural(conSig, "zona tiene", "zonas tienen")}</b> al menos una foto con Sigatoka: ahí conviene revisar primero.` : "");
}

function resumen() {
  const lista = fotos(), obj = op.objetivo, nombre = cat(obj).nombre;
  const vuelos = new Set(todas.map(f => f.vuelo).filter(Boolean));
  $("sub").textContent = `${op.vuelo || (vuelos.size > 1 ? "Todas las fechas" : [...vuelos][0] || "")} · ${plural(lista.length, "foto con ubicación", "fotos con ubicación")}`;
  const seguras = lista.filter(f => !f.dudoso);
  $("n-objetivo").textContent = seguras.filter(f => f.clave === obj).length;
  $("txt-objetivo").innerHTML = `fotos con ${esc(nombre)}<br>de ${plural(lista.length, "foto", "fotos")} con ubicación`;
  const cuenta = categoriasDelArchivo().map(c => ({ c, n: seguras.filter(f => f.clave === c.clave).length })).filter(x => x.n);
  const dudosas = lista.length - seguras.length, total = Math.max(lista.length, 1);
  $("barra-reparto").innerHTML = cuenta.map(x => `<i style="width:${x.n / total * 100}%; background:${x.c.color}"></i>`).join("") +
    (dudosas ? `<i style="width:${dudosas / total * 100}%; background:${GRIS}"></i>` : "");
  $("reparto").innerHTML = cuenta.map(x => `<span><i style="background:${x.c.color}"></i>${esc(cuantas(x.c.clave, x.n))}</span>`).join("") +
    (dudosas ? `<span><i style="background:${GRIS}"></i>${dudosas} sin diagnóstico seguro</span>` : "");
  const rojas = zonasUna().filter(z => z.pos / z.n > .25).length;
  $("msg-zonas").innerHTML = !lista.length ? "Esta fecha no tiene fotos con ubicación."
    : op.vista === "condicion" ? mensajeCondicion()
    : op.vista === "puntos" ? mensajePuntos()
    : rojas ? `<b>${plural(rojas, "zona en rojo tiene", "zonas en rojo tienen")}</b> más de una cuarta parte de fotos con ${esc(nombre)}. Ahí conviene revisar primero.`
    : `Ninguna zona pasa de 25 % de fotos con ${esc(nombre)}.`;
  $("nota-gps").textContent = "Ubicación aproximada (±3 m): cada punto es dónde estaba el dron al tomar la foto, no una planta exacta.";
}

function encuadrar() {
  const lista = fotos();
  if (lista.length) mapa.fitBounds(L.latLngBounds(lista.map(f => [f.lat, f.lon])), { padding: [40, 40], maxZoom: 19 });
}

function mostrar() {
  $("soltar").classList.add("oculto");
  ["mapa", "leyenda", "resumen"].forEach(id => $(id).classList.remove("oculto"));
  $("sin-archivo").classList.add("oculto");
  if (!mapa) iniciarMapa();
  mapa.invalidateSize();

  const vuelos = [...new Set(todas.map(f => f.vuelo).filter(Boolean))].sort().reverse();
  $("caja-vuelo").classList.toggle("oculto", vuelos.length < 2);
  $("vuelo").innerHTML = `<option value="">Todas las fechas</option>` + vuelos.map(v => `<option value="${esc(v)}">${esc(v)}</option>`).join("");
  op.vuelo = "";
  const cats = categoriasDelArchivo().filter(c => !NO_DIAGNOSTICA.has(c.clave));
  $("objetivo").innerHTML = cats.map(c => `<option value="${esc(c.clave)}">${esc(c.nombre)}</option>`).join("");
  op.objetivo = cats.some(c => c.clave === "sigatoka") ? "sigatoka" : cats[0]?.clave;
  $("objetivo").value = op.objetivo || "";
  op.ocultas.clear();

  dibujar(); leyenda(); resumen(); encuadrar();
}

// ------------------------------------------------------------------ eventos

["archivo", "archivo-2"].forEach(id => $(id).onchange = e => { if (e.target.files[0]) abrir(e.target.files[0]); e.target.value = ""; });
const marco = $("marco");
marco.addEventListener("dragover", e => { e.preventDefault(); $("soltar").classList.add("encima"); });
marco.addEventListener("dragleave", () => $("soltar").classList.remove("encima"));
marco.addEventListener("drop", e => {
  e.preventDefault();
  $("soltar").classList.remove("encima");
  if (e.dataTransfer.files[0]) abrir(e.dataTransfer.files[0]);
});
document.querySelectorAll("input[name=vista]").forEach(r => r.onchange = () => { op.vista = r.value; dibujar(); leyenda(); resumen(); });
$("tam-zona").onchange = e => { op.metros = +e.target.value; dibujar(); resumen(); };
$("objetivo").onchange = e => { op.objetivo = e.target.value; dibujar(); leyenda(); resumen(); };
$("vuelo").onchange = e => { op.vuelo = e.target.value; dibujar(); leyenda(); resumen(); encuadrar(); };
