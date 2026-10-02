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

let RESUMEN = null;
async function cargarResumen() {
  RESUMEN = await api("/api/resumen");
  const aviso = document.getElementById("aviso-modelo");
  if (!RESUMEN.modelo) {
    aviso.innerHTML = `⚠️ No hay modelo cargado: copia <b>sigatoka_cls_v1.onnx</b> (está en tu Drive) a
      <code>${RESUMEN.modelo_inicial}</code> y reinicia la estación. Mientras, puedes importar y etiquetar fotos.`;
    aviso.classList.remove("oculto");
  }
  return RESUMEN;
}

function categoria(clave) {
  if (clave === DESCARTAR) return { clave, nombre: "Foto no sirve", color: GRIS };
  return (RESUMEN?.categorias || []).find(c => c.clave === clave) || { clave, nombre: clave || "—", color: GRIS };
}

// Diagnóstico a mostrar: la revisión humana manda; si no hay, el modelo
// (en gris si su confianza está bajo el umbral).
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
  return "dudoso — revisar";
}

function pildora(c) {
  return `<span class="pildora" style="background:${c.color}">${c.nombre}</span>`;
}

function llenarVuelos(select, conTodos = true) {
  select.innerHTML = (conTodos ? `<option value="">Todos los vuelos</option>` : "") +
    RESUMEN.vuelos.map(v => `<option value="${v.vuelo}">${v.vuelo} (${v.fotos} fotos)</option>`).join("");
}

const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
