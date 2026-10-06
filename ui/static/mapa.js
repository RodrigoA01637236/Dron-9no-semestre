// El mapa del cultivo que vive de fondo en todas las páginas.
// En la página del mapa es interactivo; en las demás queda atenuado detrás.
const Mapa = (() => {
  let mapa = null, capa = null, fotos = [], sinGps = 0;
  const op = { vista: "zonas", objetivo: "sigatoka", metros: 20 };
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

  function dibujarPuntos() {
    fotos.forEach(f => {
      const d = diagnostico(f);
      const resalta = d.clave === op.objetivo && !d.dudoso;
      L.circleMarker([f.lat, f.lon], {
        radius: resalta ? 8 : 6.5, color: d.fuente === "humano" ? "#eaf0f4" : "#0f171d", weight: d.fuente === "humano" ? 2.5 : 1.5,
        fillColor: d.color, fillOpacity: resalta ? .95 : .7,
      }).bindPopup(fichaMapa(f)).addTo(capa);
    });
  }

  // Zonas: cuadros de N metros con el % de fotos con la condición elegida.
  function zonas() {
    if (!fotos.length) return [];
    const lat0 = fotos.reduce((s, f) => s + f.lat, 0) / fotos.length;
    const dLat = op.metros / 111320, dLon = op.metros / (111320 * Math.cos(lat0 * Math.PI / 180));
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
    op.vista === "zonas" ? dibujarZonas() : dibujarPuntos();
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
    iniciar, cargar, dibujar, zonas, op,
    fotos: () => fotos, sinGps: () => sinGps, mapa: () => mapa,
  };
})();
