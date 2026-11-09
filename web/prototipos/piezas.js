// Piezas comunes de las opciones basadas en Clásico: cómo se pinta un resultado, la carga del
// modelo, la leyenda del mapa y la lectura del dron. Cada opción decide dónde va cada cosa.
"use strict";
const Piezas = (() => {
  const M = Motor;

  function cargando() {
    return M.modeloListo() ? `<div class="estado"><span class="giro"></span>Revisando la hoja…</div>`
      : `<div class="resultado"><div class="estado"><span class="giro"></span>Preparando el modelo. Solo la primera vez baja unos 20 MB.</div>
         <div class="medidor carga" style="--c:var(--tinta); --v:0%" role="progressbar" aria-label="Descarga del modelo" aria-valuemin="0" aria-valuemax="100"><i></i></div></div>`;
  }

  function resultado(r, { otraTexto = "Otra hoja" } = {}) {
    const L = M.lectura(r);
    const sinHoja = !r.seguro && r.calidad?.sinHoja;   // sin hoja, el porcentaje del modelo no dice nada
    return `<div class="resultado nueva" style="--c:${L.color}">
      <span class="pastilla${L.clave === "dudoso" ? " dudosa" : ""}"><i></i>${M.esc(L.nombre)}</span>
      <h2 class="titulo-resultado">${M.esc(L.titulo)}</h2>
      <div>${sinHoja ? "" : `<div class="medidor" style="--v:${L.porcentaje}%; --m:${L.minimo}%" role="meter" aria-label="Seguridad del modelo" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${L.porcentaje}"><i></i><span class="minimo"><span>mínimo ${L.minimo} %</span></span></div>`}
        <p class="confianza">${M.esc(L.confianza)}</p></div>
      <ul class="hacer">${L.pasos.map(([i, t]) => `<li>${M.icono(i)}<span>${M.esc(t)}</span></li>`).join("")}</ul>
      <div class="acciones">
        ${M.puedeHablar ? `<button class="btn btn-borde" type="button" data-accion="voz">${M.icono("voz")}Escuchar</button>` : ""}
        <button class="btn btn-borde" type="button" data-accion="compartir">${M.icono("compartir")}Mandar al técnico</button>
        <button class="btn btn-primario" type="button" data-accion="otra">${M.icono("camara")}${M.esc(otraTexto)}</button></div></div>`;
  }

  // Revisa una foto y pinta en `cont`: primero la carga, luego el resultado con sus botones.
  async function revisar(archivo, cont, { otra, otraTexto } = {}) {
    M.callar();
    cont.innerHTML = cargando();
    try {
      const r = await M.diagnosticar(archivo, v => {
        const c = cont.querySelector(".carga"); if (!c) return;
        c.style.setProperty("--v", `${Math.round(v * 100)}%`); c.setAttribute("aria-valuenow", Math.round(v * 100));
      });
      cont.innerHTML = resultado(r, { otraTexto });
      const L = M.lectura(r);
      cont.querySelector('[data-accion="voz"]')?.addEventListener("click", () => M.hablar(L.voz));
      cont.querySelector('[data-accion="compartir"]').addEventListener("click", () => M.compartir(r, archivo));
      cont.querySelector('[data-accion="otra"]').addEventListener("click", () => otra?.());
      if (M.vozActiva.get()) M.hablar(L.voz);
      return r;
    } catch (e) {
      cont.innerHTML = `<div class="resultado"><p class="error">${M.esc(e.message || "No se pudo revisar la foto.")}</p>
        <div class="acciones"><button class="btn btn-borde" type="button" data-accion="otra">Probar otra foto</button></div></div>`;
      cont.querySelector('[data-accion="otra"]').addEventListener("click", () => otra?.());
      return null;
    }
  }

  function leyenda(res) {
    const filas = ["sigatoka", "otra_condicion", "sana"].map(k =>
      `<li><i style="background:${M.cat(k).color}"></i>${M.esc(M.cat(k).nombre)}<b>${res ? res.porClase[k] || 0 : "–"}</b></li>`);
    if (res?.dudosas) filas.push(`<li><i class="rayado"></i>No está seguro<b>${res.dudosas}</b></li>`);
    return filas.join("");
  }

  function lecturaDron({ lectura, ms, sinModelo, esperando }) {
    if (sinModelo) return `<p class="nota">El video funciona, pero el dron no tiene el modelo cargado.</p>`;
    if (esperando || !lectura) return `<p class="estado"><span class="giro"></span>Esperando lo que ve el dron…</p>`;
    const L = M.lectura(lectura);
    return `<div style="--c:${L.color}; display:grid; gap:4px"><span class="pastilla${L.clave === "dudoso" ? " dudosa" : ""}"><i></i>${M.esc(L.nombre)}</span>
      <b style="font-size:1.25rem; letter-spacing:-.02em">${M.esc(L.titulo)}</b>${ms ? `<span class="nota">${Math.round(ms)} ms por imagen</span>` : ""}</div>`;
  }

  function avisoDron({ titulo, texto, error, local }) {
    return `<p class="${error ? "error" : "estado"}">${error ? "" : '<span class="giro"></span>'}<span><b>${M.esc(titulo)}</b>${texto ? `<br><span class="nota">${M.esc(texto)}</span>` : ""}</span></p>` +
      (local ? `<a class="btn btn-borde btn-chico" href="${M.esc(local)}" target="_blank" rel="noopener" style="margin-top:8px">Abrir ${M.esc(local)}</a>` : "");
  }

  const gps = g => g ? `GPS ${g.lat.toFixed(5)}, ${g.lon.toFixed(5)} · ${g.satelites} sat.` : "GPS sin señal";

  // Arrastrar una foto encima de un elemento.
  function soltarFoto(el, alSoltar) {
    el.addEventListener("dragover", e => { e.preventDefault(); el.classList.add("encima"); });
    el.addEventListener("dragleave", () => el.classList.remove("encima"));
    el.addEventListener("drop", e => {
      e.preventDefault(); el.classList.remove("encima");
      const f = [...e.dataTransfer.files].find(f => f.type.startsWith("image/"));
      if (f) alSoltar(f);
    });
  }

  // Lee el archivo de la estación; devuelve las fotos o lanza un error con un mensaje claro.
  async function leerArchivoMapa(f) {
    try { return M.leerGeojson(await f.text()); }
    catch (e) { throw new Error("No pude leer ese archivo. Tiene que ser el .geojson que da la estación en Mapa > Descargar el mapa."); }
  }

  return { cargando, resultado, revisar, leyenda, lecturaDron, avisoDron, gps, soltarFoto, leerArchivoMapa };
})();
