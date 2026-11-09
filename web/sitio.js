// Piezas compartidas del sitio público: categorías y cómo se pinta un resultado.
// Mismas frases y colores que la estación de tierra (ui/static/estacion.js y ui/datos.py).
const $ = id => document.getElementById(id);

const CATEGORIAS = {
  sana: { nombre: "Sana", color: "#2e9e44" },
  sigatoka: { nombre: "Sigatoka", color: "#d7263d" },
  otra_condicion: { nombre: "Otra condición", color: "#f0a202" },
};
const categoria = clave => CATEGORIAS[clave] || { nombre: clave, color: "#9fb0bc" };

function esc(texto) {
  return String(texto ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
const pct = p => `${Math.round(p * 100)} %`;

function titular(clave) {
  if (clave === "sigatoka") return "Esta hoja tiene Sigatoka";
  if (clave === "sana") return "Esta hoja está sana";
  if (clave === "otra_condicion") return "Tiene otra condición";
  return `Parece: ${categoria(clave).nombre}`;
}

function queHacer(clave, seguro) {
  if (!seguro) return "Toma otra foto más cerca, con la hoja llenando el cuadro y sin sombra fuerte. Si la duda sigue, pide que un agrónomo la revise.";
  if (clave === "sigatoka") return "Avisa al agrónomo y marca la planta. Quitar las hojas muy dañadas ayuda a frenar el contagio.";
  if (clave === "sana") return "No se ven síntomas en esta hoja. Si sospechas, revisa también el envés y las hojas más jóvenes.";
  if (clave === "otra_condicion") return "Tiene algo distinto a la Sigatoka, como amarillamiento o daño. Pide que un agrónomo la revise.";
  return "Pide que un agrónomo la revise.";
}

// Barras de probabilidad con la línea de la seguridad mínima.
function escala(probs, umbral) {
  const filas = Object.entries(probs).sort((a, b) => b[1] - a[1]);
  return `<div class="escala" style="--umbral:${(umbral * 100).toFixed(1)}%">${filas.map(([k, p], i) => {
    const c = categoria(k);
    return `<div class="escala-fila${i === 0 ? " ganadora" : ""}">
      <span>${esc(c.nombre)}</span><span class="lectura-valor">${Math.round(p * 100)} %</span>
      <div class="pista" role="meter" aria-label="${esc(c.nombre)}" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${Math.round(p * 100)}">
        <i style="background:${c.color}; transform:scaleX(${p.toFixed(4)})"></i></div></div>`;
  }).join("")}
    <div class="escala-umbral">La línea blanca marca la seguridad mínima: ${pct(umbral)}.</div></div>`;
}

// Pinta una lectura {clase, confianza, probs} en los contenedores lectura / probs / que.
function pintarLectura(r, umbral) {
  const c = categoria(r.clase);
  const seguro = r.confianza >= umbral;
  $("lectura").innerHTML = seguro
    ? `<span class="chip-diagnostico"><i style="background:${c.color}"></i>${esc(c.nombre)}</span>
       <div class="veredicto">${esc(titular(r.clase))}</div>
       <p class="confianza">El modelo está <b>${pct(r.confianza)} seguro</b>. Necesita al menos ${pct(umbral)} para dar un diagnóstico.</p>`
    : `<span class="chip-diagnostico"><i class="muestra vacia" style="border-radius:50%"></i>No está seguro</span>
       <div class="veredicto">El modelo no está seguro</div>
       <p class="confianza">Lo más parecido es <b>${esc(c.nombre)}</b> (${pct(r.confianza)}), pero necesita al menos ${pct(umbral)} para dar un diagnóstico.</p>`;
  $("probs").innerHTML = r.probs ? escala(r.probs, umbral) : "";
  $("probs").classList.toggle("oculto", !r.probs);
  $("que").innerHTML = `<b>Qué hacer:</b> ${esc(queHacer(r.clase, seguro))}`;
  $("que").classList.remove("oculto");
}

function pintarAviso(titulo, texto, error = false) {
  $("lectura").innerHTML = `<h2>${esc(titulo)}</h2>` +
    (texto ? `<p class="${error ? "mensaje error" : "suave"}" style="margin:0">${esc(texto)}</p>` : "");
  ["probs", "que"].forEach(s => $(s).classList.add("oculto"));
}
