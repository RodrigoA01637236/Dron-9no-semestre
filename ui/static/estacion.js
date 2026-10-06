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

// Íconos de trazo (1.5 px, 24×24) dibujados para la estación.
const ICONOS = {
  aviso: '<path d="M12 4 21 19H3Z"/><path d="M12 10v4M12 16.5v.5"/>',
  subir: '<path d="M12 16V4M7 9l5-5 5 5"/><path d="M4 15v4h16v-4"/>',
  camara: '<path d="M4 8h3l1.5-2h7L17 8h3v11H4Z"/><circle cx="12" cy="13" r="3.5"/>',
  hoja: '<path d="M5 19c0-8 5-14 14-14 0 9-6 14-14 14Z"/><path d="M5 19 13 11"/>',
  carpeta: '<path d="M3 7h6l2 2h10v10H3Z"/>',
  descarga: '<path d="M12 4v12M7 11l5 5 5-5"/><path d="M4 20h16"/>',
  flecha: '<path d="M9 5l7 7-7 7"/>',
  guardar: '<path d="M5 4h11l3 3v13H5Z"/><path d="M8 4v5h7V4M8 20v-6h8v6"/>',
  pausa: '<path d="M9 6v12M15 6v12"/>',
  cerrar: '<path d="M6 6l12 12M18 6 6 18"/>',
};
const icono = (n, extra = "") =>
  `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true" ${extra}>${ICONOS[n]}</svg>`;

let RESUMEN = null;
async function cargarResumen() {
  RESUMEN = await api("/api/resumen");
  document.documentElement.style.setProperty("--umbral", `${RESUMEN.umbral * 100}%`);
  const aviso = document.getElementById("aviso-modelo");
  if (!RESUMEN.modelo) {
    aviso.innerHTML = `${icono("aviso")}<div><b>No hay modelo cargado.</b> Copia <code>sigatoka_cls_v1.onnx</code>
      (está en el Drive del equipo) a <code>${esc(RESUMEN.modelo_inicial)}</code> y reinicia la estación.
      Mientras tanto puedes importar y etiquetar fotos.</div>`;
    aviso.classList.remove("oculto");
  }
  const estado = document.getElementById("estado-modelo");
  estado.innerHTML = RESUMEN.modelo
    ? `<span><span class="palabra">Modelo </span><b>v${RESUMEN.modelo.version}</b></span><span title="El modelo solo da un diagnóstico si está al menos así de seguro"><span class="palabra">Seguridad mínima </span><b>${pct(RESUMEN.umbral)}</b></span>`
    : `<span class="sin">Sin modelo</span>`;
  const pend = RESUMEN.total_fotos - RESUMEN.total_revisadas;
  const nav = document.getElementById("pendientes-nav");
  nav.textContent = pend > 999 ? "999+" : pend;
  nav.classList.toggle("oculto", pend <= 0);
  nav.title = `${pend} fotos sin revisar`;
  return RESUMEN;
}

function categoria(clave) {
  if (clave === DESCARTAR) return { clave, nombre: "Foto no sirve", color: GRIS };
  return (RESUMEN?.categorias || []).find(c => c.clave === clave) || { clave, nombre: clave || "Sin diagnóstico", color: GRIS };
}

// Diagnóstico a mostrar: la revisión humana manda; si no hay, el modelo
// (marcado como dudoso si su confianza está bajo el umbral).
function diagnostico(f) {
  if (f.etiqueta) return { ...categoria(f.etiqueta), fuente: "humano" };
  if (!f.pred) return { clave: null, nombre: "Sin diagnóstico", color: GRIS, fuente: "ninguna" };
  const c = categoria(f.pred);
  const dudoso = f.conf < (RESUMEN?.umbral ?? 0.65);
  return { ...c, color: dudoso ? GRIS : c.color, fuente: "modelo", dudoso };
}

function textoConfianza(conf) {
  if (conf == null) return "";
  if (conf >= 0.9) return "muy seguro";
  if (conf >= (RESUMEN?.umbral ?? 0.65)) return "seguro";
  return "dudoso, revisar";
}

// Muestra de color + nombre: el color nunca va solo.
function ficha(c) {
  return `<span class="ficha${c.dudoso ? " dudosa" : ""}"><i class="muestra" style="background:${c.color}"></i>${esc(c.nombre)}</span>`;
}
const pildora = ficha;

// Escala de probabilidades con la línea del umbral (la firma de la estación).
function escala(probs, umbral = RESUMEN?.umbral ?? 0.65) {
  const filas = Object.entries(probs).sort((a, b) => b[1] - a[1]);
  return `<div class="escala">${filas.map(([k, p], i) => {
    const c = categoria(k);
    return `<div class="escala-fila${i === 0 ? " ganadora" : ""}">
      ${ficha(c)}<span class="lectura-valor">${(p * 100).toFixed(1)} %</span>
      <div class="pista" role="meter" aria-label="${esc(c.nombre)}" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Math.round(p * 100)}">
        <i style="background:${c.color}; transform:scaleX(${p.toFixed(4)})"></i></div></div>`;
  }).join("")}
    <div class="escala-umbral"><span>0 %</span><span class="marca-umbral">mínimo ${pct(umbral)}</span><span>100 %</span></div></div>`;
}

function llenarVuelos(select, conTodos = true) {
  select.innerHTML = (conTodos ? `<option value="">Todos los vuelos</option>` : "") +
    RESUMEN.vuelos.map(v => `<option value="${esc(v.vuelo)}">${esc(v.vuelo)} (${v.fotos} fotos)</option>`).join("");
}

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

function fecha(txt) { return txt ? esc(String(txt).replace("T", " ").slice(0, 16)) : "—"; }
