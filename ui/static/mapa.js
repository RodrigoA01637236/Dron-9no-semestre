// El mapa del cultivo que vive de fondo en todas las páginas.
// En la página del mapa es interactivo; en las demás queda atenuado detrás.
const Mapa = (() => {
  let mapa = null, capa = null, fotos = [], sinGps = 0;
  // vista: "condicion" (cada zona con el color de lo que más hay), "zonas" (una condición) o "puntos".
  // ocultas: claves que el usuario apagó en la leyenda ("dudoso" = sin diagnóstico seguro).
  const op = { vista: "condicion", objetivo: "sigatoka", metros: 20, ocultas: new Set() };
  // Fotos que no dicen nada del cultivo: no cuentan para las zonas.
  const NO_DIAGNOSTICA = new Set(["sin_hoja"]);
  // En un empate, la zona toma el color de lo más grave.
  const PRIORIDAD = ["sigatoka", "otra_condicion", "sana"];
  const prioridad = k => (PRIORIDAD.indexOf(k) + 1) || 99;
  const coord = (v, pos, neg) => `${Math.abs(v).toFixed(5)}° ${v >= 0 ? pos : neg}`;

  function iniciar(interactivo) {
    mapa = L.map("mapa-base", {
      zoomControl: interactivo, dragging: interactivo, scrollWheelZoom: interactivo, doubleClickZoom: interactivo,
      boxZoom: interactivo, keyboard: interactivo, touchZoom: interactivo, attributionControl: true,
    }).setView([17.99, -92.95], 15);
    const fondos = {
      "Satélite (requiere internet)": L.tileLayer(
        "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
        { maxZoom: 20, maxNativeZoom: 19, attribution: "Imágenes © Esri" }),
      "Calles (requiere internet)": L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png",
        { maxZoom: 20, maxNativeZoom: 19, attribution: "© OpenStreetMap" }),
      "Sin fondo (sin internet)": L.layerGroup(),
    };
    fondos["Satélite (requiere internet)"].addTo(mapa);
    if (interactivo) {
      L.control.layers(fondos, null, { position: "topleft" }).addTo(mapa);
      L.control.scale({ imperial: false, position: "bottomright" }).addTo(mapa);
      mapa.on("mousemove", e => {
        const lectura = document.getElementById("lectura-pos");
        if (lectura) lectura.textContent = `${coord(e.latlng.lat, "N", "S")}  ${coord(e.latlng.lng, "E", "O")}`;
      });
    }
    capa = L.layerGroup().addTo(mapa);
    return mapa;
  }

  function fichaMapa(f) {
    const d = diagnostico(f);
    const fuente = d.fuente === "humano" ? `Revisada${f.revisor ? " por " + esc(f.revisor) : ""}`
      : d.fuente === "modelo" ? `Modelo: ${pct(f.conf)}, ${textoConfianza(f.conf)}` : "Sin diagnóstico";
    return `<div class="ficha-mapa"><img src="/mini/${f.id}" loading="lazy" alt="">
      ${ficha(d)}<div class="meta">${fuente}<br>${esc(f.fecha || "")}${f.alt != null ? ` · ${f.alt.toFixed(1)} m de altura` : ""}</div>
      <a href="/revisar?foto=${f.id}">Revisar esta foto</a></div>`;
  }

  // Clave con la que se prende o apaga cada foto desde la leyenda.
  function claveDe(f) {
    const d = diagnostico(f);
    return d.dudoso || !d.clave ? "dudoso" : d.clave;
  }
  const visible = f => !op.ocultas.has(claveDe(f));

  function dibujarPuntos() {
    fotos.filter(visible).forEach(f => {
      const d = diagnostico(f);
      const resalta = d.clave === op.objetivo && !d.dudoso;
      L.circleMarker([f.lat, f.lon], {
        radius: resalta ? 8 : 6.5, color: d.fuente === "humano" ? "#eaf0f4" : "#0f171d", weight: d.fuente === "humano" ? 2.5 : 1.5,
        fillColor: d.color, fillOpacity: resalta ? .95 : .7,
      }).bindPopup(fichaMapa(f)).addTo(capa);
    });
  }

  // Cuadros de N metros sobre el terreno (en grados, según la latitud del lote).
  function paso() {
    const lat0 = fotos.reduce((s, f) => s + f.lat, 0) / fotos.length;
    return { dLat: op.metros / 111320, dLon: op.metros / (111320 * Math.cos(lat0 * Math.PI / 180)) };
  }

  // Zonas por condición: cuántas fotos de cada condición hay en cada cuadro y cuál domina.
  function zonasCondicion() {
    if (!fotos.length) return [];
    const { dLat, dLon } = paso();
    const celdas = new Map();
    fotos.forEach(f => {
      const d = diagnostico(f);
      if (!d.clave || d.dudoso || d.clave === DESCARTAR || NO_DIAGNOSTICA.has(d.clave) || op.ocultas.has(d.clave)) return;
      const i = Math.floor(f.lat / dLat), j = Math.floor(f.lon / dLon), k = `${i}|${j}`;
      const c = celdas.get(k) || { i, j, n: 0, cuenta: {}, dLat, dLon };
      c.n++; c.cuenta[d.clave] = (c.cuenta[d.clave] || 0) + 1;
      celdas.set(k, c);
    });
    return [...celdas.values()].map(c => ({
      ...c, dominante: Object.keys(c.cuenta).sort((a, b) => c.cuenta[b] - c.cuenta[a] || prioridad(a) - prioridad(b))[0],
    }));
  }

  function dibujarCondicion() {
    zonasCondicion().forEach(c => {
      const color = categoria(c.dominante).color;
      // Borde punteado rojo: la zona no es mayormente Sigatoka, pero sí hay alguna foto con Sigatoka.
      const algoDeSigatoka = c.dominante !== "sigatoka" && c.cuenta.sigatoka;
      const detalle = Object.entries(c.cuenta).sort((a, b) => b[1] - a[1])
        .map(([k, n]) => `${esc(categoria(k).nombre)}: ${n}`).join(" · ");
      L.rectangle([[c.i * c.dLat, c.j * c.dLon], [(c.i + 1) * c.dLat, (c.j + 1) * c.dLon]], {
        color: algoDeSigatoka ? categoria("sigatoka").color : color, weight: algoDeSigatoka ? 2.5 : 1.5,
        dashArray: algoDeSigatoka ? "5 4" : null, fillColor: color, fillOpacity: .25 + .35 * Math.min(1, c.n / 10),
      }).bindTooltip(`<b>${esc(categoria(c.dominante).nombre)}</b> · ${plural(c.n, "foto", "fotos")}<br>${detalle}`).addTo(capa);
    });
  }

  // Zonas de una condición: cuadros de N metros con el % de fotos con la condición elegida.
  function zonas() {
    if (!fotos.length) return [];
    const { dLat, dLon } = paso();
    const celdas = new Map();
    fotos.forEach(f => {
      const d = diagnostico(f);
      if (!d.clave || d.dudoso || d.clave === DESCARTAR) return;  // solo diagnósticos confiables
      const i = Math.floor(f.lat / dLat), j = Math.floor(f.lon / dLon), k = `${i}|${j}`;
      const c = celdas.get(k) || { i, j, n: 0, pos: 0, dLat, dLon };
      c.n++; c.pos += d.clave === op.objetivo;
      celdas.set(k, c);
    });
    return [...celdas.values()];
  }

  function dibujarZonas() {
    const nombre = categoria(op.objetivo).nombre;
    zonas().forEach(c => {
      const p = c.pos / c.n;
      const color = p === 0 ? "#5fd27a" : p <= .25 ? "#ffc04d" : "#ff5a6e";
      L.rectangle([[c.i * c.dLat, c.j * c.dLon], [(c.i + 1) * c.dLat, (c.j + 1) * c.dLon]], {
        color, weight: 1.5, fillColor: color, fillOpacity: .18 + .3 * Math.min(1, c.n / 10),
      }).bindTooltip(`${c.n} fotos · ${c.pos} con ${esc(nombre)} (${Math.round(p * 100)} %)`).addTo(capa);
    });
  }

  function dibujar() {
    capa.clearLayers();
    if (!fotos.length) return;
    if (op.vista === "condicion") dibujarCondicion();
    else if (op.vista === "zonas") dibujarZonas();
    else dibujarPuntos();
  }

  async function cargar(vuelo, relleno = { tl: [110, 130], br: [390, 170] }) {
    const r = await api("/api/mapa" + (vuelo ? `?vuelo=${encodeURIComponent(vuelo)}` : ""));
    fotos = r.fotos; sinGps = r.sin_gps;
    dibujar();
    if (fotos.length) {
      const chico = innerWidth < 900;
      mapa.fitBounds(L.latLngBounds(fotos.map(f => [f.lat, f.lon])), {
        paddingTopLeft: chico ? [20, 120] : relleno.tl, paddingBottomRight: chico ? [20, innerHeight * .5] : relleno.br, maxZoom: 19,
      });
    }
    return r;
  }

  return {
    iniciar, cargar, dibujar, zonas, zonasCondicion, op, NO_DIAGNOSTICA,
    fotos: () => fotos, sinGps: () => sinGps, mapa: () => mapa,
  };
})();
