// Dron en vivo: la Jetson (jetson/zed_right.py) da video, GPS y diagnóstico en su puerto 8080.
// Esta página es pública (https), así que el navegador solo la deja hablar con una dirección
// https: la del túnel de la Jetson. Las direcciones de la red local se abren directo.
let dron = null;   // { base, temporizador, fallas }
const PRIVADA = /^(10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.|127\.|localhost$)/;

// Devuelve { base } si se puede usar desde aquí, o { local } con la página propia de la Jetson.
function leerDireccion(texto) {
  texto = texto.trim();
  const u = new URL(/^https?:\/\//i.test(texto) ? texto : `https://${texto}`);
  if (PRIVADA.test(u.hostname)) {
    const local = `http://${u.hostname}:${u.port || 8080}`;
    return location.protocol === "https:" ? { local } : { base: local };
  }
  u.protocol = "https:";   // los túneles siempre dan https
  return { base: u.origin };
}

async function pedirDron(ruta, opciones = {}, espera = 6000) {
  const control = new AbortController();
  const t = setTimeout(() => control.abort(), espera);
  try {
    const r = await fetch(dron.base + ruta, { ...opciones, signal: control.signal, cache: "no-store" });
    if (!r.ok) {
      const d = await r.json().catch(() => ({}));
      throw new Error(d.error || `El dron respondió ${r.status}`);
    }
    return r;
  } finally { clearTimeout(t); }
}

async function conectar(texto) {
  let dir;
  try { dir = leerDireccion(texto); } catch (e) { return pintarAviso("Sin lectura", "Esa dirección no es válida. Escribe algo como https://ejemplo.trycloudflare.com", true); }
  desconectar();
  if (dir.local) {
    $("lectura").innerHTML = `<h2>Esa dirección es de la red local</h2>
      <p class="suave" style="margin:0">Esta página es pública y el navegador no la deja leer direcciones de la red
        local. Si estás en la misma WiFi que la Jetson, abre su página directo. Para verla desde aquí, abre el túnel
        de la Jetson (instrucciones abajo) y escribe la dirección <code>https://</code> que te dé.</p>
      <a class="boton claro" href="${esc(dir.local)}" target="_blank" rel="noopener" style="justify-self:start">Abrir ${esc(dir.local)}</a>`;
    ["probs", "que"].forEach(s => $(s).classList.add("oculto"));
    return;
  }

  try { localStorage.setItem("dron", texto.trim()); } catch (e) {}
  dron = { base: dir.base, temporizador: null, fallas: 0 };
  const host = new URL(dir.base).host;
  pintarAviso("Conectando con el dron…", host);
  let est;
  try { est = await (await pedirDron("/estado")).json(); }
  catch (e) {
    dron = null;
    return pintarAviso("Sin lectura", `No se pudo conectar con el dron en ${host}. Revisa que la Jetson esté encendida, que zed_right.py y el túnel sigan abiertos y que la dirección sea la que imprimió el túnel.`, true);
  }
  $("espera").classList.add("oculto");
  $("video").src = `${dir.base}/video?t=${Date.now()}`;
  ["video", "en-vivo", "dron-gps", "barra", "btn-desconectar"].forEach(id => $(id).classList.remove("oculto"));
  $("btn-conectar").textContent = "Cambiar";
  $("pie-foto").textContent = `Cámara del dron (${host})`;
  pintarDron(est);
  dron.temporizador = setTimeout(ciclo, 1000);
}

function pintarDron(est) {
  const p = est.prediccion;
  if (!est.modelo) {
    pintarAviso("El dron no tiene modelo", "El video funciona, pero para identificar hay que copiar sigatoka_cls_v1.onnx a vision/models/ en la Jetson y apagar y prender el dron.");
    $("pie-tiempo").textContent = "";
  } else if (!p) {
    pintarAviso("Esperando lectura del dron…");
  } else {
    pintarLectura(p, est.modelo.umbral);
    $("pie-tiempo").textContent = `identificada en el dron · ${Math.round(p.ms)} ms por imagen`;
  }
  const g = est.gps;
  $("dron-gps").textContent = g ? `GPS ${g.lat.toFixed(6)}, ${g.lon.toFixed(6)} · ${g.satelites} sat.` : "GPS: sin señal";
  $("dron-gps").classList.toggle("sin-senal", !g);
}

async function ciclo() {
  if (!dron) return;
  try {
    pintarDron(await (await pedirDron("/estado", {}, 4000)).json());
    dron.fallas = 0;
  } catch (e) {
    if (!dron) return;
    if (++dron.fallas === 3) pintarAviso("Sin lectura", "Se perdió la conexión con el dron. Sigo intentando…", true);
  }
  if (dron) dron.temporizador = setTimeout(ciclo, 1000);
}

async function fotoDron() {
  const b = $("btn-foto");
  b.disabled = true; b.textContent = "Tomando foto…";
  $("msg-foto").className = "mensaje"; $("msg-foto").textContent = "";
  try {
    const r = await (await pedirDron("/foto", { method: "POST" }, 10000)).json();
    const ruta = r.url_sin_texto || r.url;
    $("msg-foto").className = "mensaje bien";
    $("msg-foto").innerHTML = `Guardada en el dron: ${esc(r.archivo)}. <a href="${esc(dron.base + ruta)}" target="_blank" rel="noopener">Ver la foto</a>`;
  } catch (e) {
    $("msg-foto").className = "mensaje error";
    $("msg-foto").textContent = "No se pudo tomar la foto: " + e.message;
  } finally {
    b.disabled = false; b.textContent = "Tomar foto con el dron";
  }
}

function desconectar() {
  if (dron) clearTimeout(dron.temporizador);
  dron = null;
  $("video").removeAttribute("src");   // cierra la conexión del video
  ["video", "en-vivo", "dron-gps", "barra", "btn-desconectar"].forEach(id => $(id).classList.add("oculto"));
  $("espera").classList.remove("oculto");
  $("btn-conectar").textContent = "Conectar";
  $("pie-foto").textContent = "Sin conexión";
  $("pie-tiempo").textContent = "";
  $("msg-foto").textContent = "";
}

$("video").onerror = () => {
  if (!dron) return;
  const base = dron.base;
  setTimeout(() => { if (dron && dron.base === base) $("video").src = `${base}/video?t=${Date.now()}`; }, 2000);
};
$("form-dron").onsubmit = e => { e.preventDefault(); if ($("dron-dir").value.trim()) conectar($("dron-dir").value); };
$("btn-desconectar").onclick = () => {
  desconectar();
  pintarAviso("Sin lectura", "Te desconectaste del dron.");
};
$("btn-foto").onclick = fotoDron;
// Tecla S: toma la foto igual que la tecla S en la ventana de la Jetson (mismo guardado en el dron).
document.addEventListener("keydown", e => {
  if (!dron || e.repeat || e.ctrlKey || e.metaKey || e.altKey || e.key.toLowerCase() !== "s") return;
  if (e.target.closest("input, textarea, select")) return;
  e.preventDefault();
  if (!$("btn-foto").disabled) fotoDron();
});

// ?dron=https://... en el enlace conecta directo. Si la página la sirve la propia Jetson
// (hotspot, jetson/sitio_local.sh), el dron es esa misma máquina en el puerto 8080.
// Si no, se recuerda la última dirección.
const enJetson = PRIVADA.test(location.hostname) ? `${location.hostname}:8080` : null;
const inicial = new URLSearchParams(location.search).get("dron") || enJetson;
try { $("dron-dir").value = inicial || localStorage.getItem("dron") || ""; } catch (e) { $("dron-dir").value = inicial || ""; }
if (inicial) conectar(inicial);
