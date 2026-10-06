// Utilidades compartidas de la estación de tierra.
const GRIS = "#9aa3a0";
const DESCARTAR = "_descartar";

async function api(url, opciones = {}) {
  const r = await fetch(url, opciones);
  const datos = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(datos.error || datos.mensaje || `Error ${r.status}`);
  return datos;
}
const post = (url, cuerpo) => api(url, {
  method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(cuerpo),
});

const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
const pct = x => x == null ? "—" : `${Math.round(x * 100)} %`;
const plural = (n, uno, varios) => `${n} ${n === 1 ? uno : varios}`;
function fecha(txt) { return txt ? esc(String(txt).replace("T", " ").slice(0, 16)) : "—"; }

// Vuelo elegido: se recuerda entre páginas (el mapa de fondo lo usa).
function vueloActual() {
  const p = new URLSearchParams(location.search).get("vuelo");
  if (p !== null) return p;
  try { return localStorage.getItem("vuelo") || ""; } catch (e) { return ""; }
}
function guardarVuelo(v) { try { localStorage.setItem("vuelo", v || ""); } catch (e) {} }

let RESUMEN = null;
async function cargarResumen() {
  RESUMEN = await api("/api/resumen");
  document.documentElement.style.setProperty("--umbral", `${RESUMEN.umbral * 100}%`);
  const aviso = document.getElementById("aviso-modelo");
  if (!RESUMEN.modelo) {
    aviso.innerHTML = `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 4 21 19H3Z"/><path d="M12 10v4M12 16.5v.5"/></svg>
      <div><b>No hay modelo cargado.</b> Copia <code>sigatoka_cls_v1.onnx</code> (está en el Drive del equipo) a
      <code>${esc(RESUMEN.modelo_inicial)}</code> y reinicia la estación. Mientras tanto puedes subir y revisar fotos.</div>`;
    aviso.classList.remove("oculto");
  }
  const pend = RESUMEN.total_fotos - RESUMEN.total_revisadas;
  const ins = document.getElementById("pendientes-nav");
  ins.textContent = pend > 999 ? "999+" : pend;
  ins.classList.toggle("oculto", pend <= 0);
  document.getElementById("version-nav").textContent = RESUMEN.modelo ? `Modelo v${RESUMEN.modelo.version}` : "Modelo";
  return RESUMEN;
}

function categoria(clave) {
  if (clave === DESCARTAR) return { clave, nombre: "Foto no sirve", color: GRIS };
  return (RESUMEN?.categorias || []).find(c => c.clave === clave) || { clave, nombre: clave || "Sin diagnóstico", color: GRIS };
}

// Diagnóstico a mostrar: la revisión humana manda; si no hay, el modelo
// (marcado como dudoso si su confianza está bajo la seguridad mínima).
function diagnostico(f) {
  if (f.etiqueta) return { ...categoria(f.etiqueta), fuente: "humano" };
  if (!f.pred) return { clave: null, nombre: "Sin diagnóstico", color: GRIS, fuente: "ninguna" };
  const c = categoria(f.pred);
  const dudoso = f.conf < (RESUMEN?.umbral ?? 0.65);
  return { ...c, color: dudoso ? GRIS : c.color, fuente: "modelo", dudoso, nombre: dudoso ? "No está seguro" : c.nombre };
}

function textoConfianza(conf) {
  if (conf == null) return "";
  if (conf >= 0.9) return "muy seguro";
  if (conf >= (RESUMEN?.umbral ?? 0.65)) return "seguro";
  return "no está seguro";
}

// Muestra de color + nombre: el color nunca va solo.
function ficha(c) {
  return `<span class="ficha${c.dudoso ? " dudosa" : ""}"><i class="muestra" style="background:${c.color}"></i>${esc(c.nombre)}</span>`;
}

// Frase clara para el resultado de una hoja.
function titular(clave) {
  if (clave === "sigatoka") return "Esta hoja tiene Sigatoka";
  if (clave === "sana") return "Esta hoja está sana";
  if (clave === "otra_condicion") return "Tiene otra condición";
  return `Parece: ${categoria(clave).nombre}`;
}
function queHacer(clave, seguro) {
  if (!seguro) return "Toma otra foto más cerca, con la hoja llenando el cuadro y sin sombra fuerte. Si la duda sigue, guárdala para que el agrónomo la revise.";
  if (clave === "sigatoka") return "Avisa al agrónomo y marca la planta. Quitar las hojas muy dañadas ayuda a frenar el contagio.";
  if (clave === "sana") return "No se ven síntomas en esta hoja. Si sospechas, revisa también el envés y las hojas más jóvenes.";
  if (clave === "otra_condicion") return "Tiene algo distinto a la Sigatoka, como amarillamiento o daño. Guárdala para que el agrónomo la revise.";
  return "Guárdala para que el agrónomo la revise.";
}

// Barras de probabilidad con la línea de la seguridad mínima.
function escala(probs, umbral = RESUMEN?.umbral ?? 0.65) {
  const filas = Object.entries(probs).sort((a, b) => b[1] - a[1]);
  return `<div class="escala">${filas.map(([k, p], i) => {
    const c = categoria(k);
    return `<div class="escala-fila${i === 0 ? " ganadora" : ""}">
      <span>${esc(c.nombre)}</span><span class="lectura-valor">${Math.round(p * 100)} %</span>
      <div class="pista" role="meter" aria-label="${esc(c.nombre)}" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Math.round(p * 100)}">
        <i style="background:${c.color}; transform:scaleX(${p.toFixed(4)})"></i></div></div>`;
  }).join("")}
    <div class="escala-umbral">La línea blanca marca la seguridad mínima: ${pct(umbral)}.</div></div>`;
}

// Las imágenes se agrupan por la fecha en que se cargaron ("2026-10-06").
const MESES = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"];
function hoy() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`;
}
function nombreFecha(clave) {
  const m = /^(\d{4})-(\d{2})-(\d{2})(?:_(.+))?$/.exec(clave || "");
  if (!m) return clave || "Sin fecha";
  const base = clave.slice(0, 10) === hoy() ? "Hoy" : `${+m[3]} ${MESES[+m[2] - 1]} ${m[1]}`;
  return m[4] ? `${base} · ${m[4].replaceAll("_", " ")}` : base;
}
function llenarFechas(select, conTodas = true) {
  select.innerHTML = (conTodas ? `<option value="">Todas las fechas</option>` : "") +
    RESUMEN.vuelos.map(v => `<option value="${esc(v.vuelo)}">${esc(nombreFecha(v.vuelo))} · ${plural(v.fotos, "imagen", "imágenes")}</option>`).join("");
}
const llenarVuelos = llenarFechas;

// Botón de dos pasos para acciones serias: el primer clic pide confirmación,
// el segundo ejecuta. Se desarma solo a los 4 s.
function dosPasos(boton, textoConfirmar, accion) {
  const original = boton.innerHTML;
  let armado = null;
  boton.addEventListener("click", async () => {
    if (!armado) {
      boton.classList.add("confirmando");
      boton.textContent = textoConfirmar;
      armado = setTimeout(() => { boton.classList.remove("confirmando"); boton.innerHTML = original; armado = null; }, 4000);
      return;
    }
    clearTimeout(armado); armado = null;
    boton.classList.remove("confirmando"); boton.innerHTML = original;
    await accion();
  });
}

// Tarjeta de imagen con una X arriba a la derecha para borrarla.
// El primer clic pide confirmar ("Borrar"); el segundo la borra. Se desarma a los 3 s.
const ICONO_X = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6 6 18"/></svg>';
function celdaImagen(f, pie) {
  return `<div class="celda-caja">
    <button class="celda" type="button" data-id="${f.id}" aria-pressed="false">
      <img src="/mini/${f.id}" loading="lazy" alt="">
      <span class="celda-pie">${pie}</span></button>
    <button class="borrar" type="button" data-borrar="${f.id}" aria-label="Borrar esta imagen" title="Borrar esta imagen">${ICONO_X}</button>
  </div>`;
}
const borrarImagen = id => api(`/api/foto/${id}`, { method: "DELETE" });
function activarBorrado(contenedor, alBorrar) {
  contenedor.querySelectorAll("[data-borrar]").forEach(b => b.onclick = async e => {
    e.stopPropagation();
    if (!b.classList.contains("confirmando")) {
      b.classList.add("confirmando");
      b.textContent = "Borrar";
      b.setAttribute("aria-label", "Confirmar: borrar esta imagen");
      b._t = setTimeout(() => { b.classList.remove("confirmando"); b.innerHTML = ICONO_X; b.setAttribute("aria-label", "Borrar esta imagen"); }, 3000);
      return;
    }
    clearTimeout(b._t);
    b.disabled = true;
    const id = +b.dataset.borrar;
    try {
      await borrarImagen(id);
      b.closest(".celda-caja").remove();
      await cargarResumen();
      if (alBorrar) await alBorrar(id);
    } catch (err) {
      b.disabled = false;
      b.textContent = "Error";
      b.title = err.message;
    }
  });
}
