// Motor común de los prototipos de una sola página. Hace lo mismo que identificar.js, mapa.js y
// dron.js del sitio, pero no toca el DOM: cada variante pinta los resultados a su manera.
// Todo corre en el navegador: la foto y el archivo del mapa nunca salen del dispositivo.
"use strict";
const Motor = (() => {
  const RAIZ = new URL("../", document.currentScript.src).href;   // la carpeta web/
  const SITIO = "https://dron-sigatoka.netlify.app";
  const GRIS = "#7d8b96";

  const CAT = {
    sana: { nombre: "Sana", color: "#2e9e44" },
    sigatoka: { nombre: "Sigatoka", color: "#d7263d" },
    otra_condicion: { nombre: "Otra condición", color: "#f0a202" },
    sin_hoja: { nombre: "Sin hojas de plátano", color: "#8a94a6" },
  };
  const cat = k => CAT[k] || { nombre: k || "Sin diagnóstico", color: GRIS };

  // Qué decir y qué hacer con cada lectura. Sin dosis de químicos: eso lo decide el técnico.
  const LECTURAS = {
    sigatoka: { palabra: "Sigatoka", titulo: "Parece Sigatoka", pasos: [
      ["cinta", "Marca la planta para encontrarla después."],
      ["telefono", "Avisa al técnico o al agrónomo."],
      ["tijera", "Quitar las hojas muy dañadas ayuda a frenar el contagio."]] },
    sana: { palabra: "Sana", titulo: "Se ve sana", pasos: [
      ["ojo", "No se ven manchas de Sigatoka en esta hoja."],
      ["hoja", "Revisa también el envés y las hojas más jóvenes."]] },
    otra_condicion: { palabra: "Otra condición", titulo: "Parece otra condición", pasos: [
      ["telefono", "Tiene algo distinto a la Sigatoka: pide que un técnico la revise."],
      ["alerta", "Si la planta se marchita o se pone amarilla de golpe, avisa a Sanidad Vegetal (SENASICA)."]] },
    dudoso: { palabra: "No sé", titulo: "No estoy seguro", pasos: [
      ["camara", "Toma otra foto más cerca, con la hoja llenando el cuadro."],
      ["sol", "Evita sombras fuertes y que la foto salga borrosa."],
      ["telefono", "Si sigue la duda, pide que un técnico la revise."]] },
  };

  const esc = t => String(t ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const plural = (n, uno, varios) => `${n} ${n === 1 ? uno : varios}`;
  const pct = p => `${Math.round(p * 100)} %`;

  // ------------------------------------------------------------------ íconos (trazo, 24 px)
  const ICONOS = {
    camara: '<path d="M4 8h3l1.5-2h7L17 8h3v11H4Z"/><circle cx="12" cy="13" r="3.5"/>',
    imagen: '<rect x="3.5" y="5" width="17" height="14" rx="2"/><circle cx="9" cy="10" r="1.6"/><path d="m4 17 5-5 4 4 2.5-2.5L20 17"/>',
    cinta: '<path d="M12 11.5 4.5 7v9l7.5-4.5L19.5 16V7Z"/><path d="m11 12-2.5 8M13 12l2.5 8"/>',
    telefono: '<path d="M6.5 3.5h3l1.5 4-2 1.2a11 11 0 0 0 5.3 5.3l1.2-2 4 1.5v3a2 2 0 0 1-2 2A15.5 15.5 0 0 1 4.5 5.5a2 2 0 0 1 2-2Z"/>',
    tijera: '<circle cx="6" cy="7" r="2.5"/><circle cx="6" cy="17" r="2.5"/><path d="M8.2 8.4 20 17M8.2 15.6 20 7"/>',
    ojo: '<path d="M2.5 12S6 5.5 12 5.5 21.5 12 21.5 12 18 18.5 12 18.5 2.5 12 2.5 12Z"/><circle cx="12" cy="12" r="3"/>',
    hoja: '<path d="M4.5 19.5C4.5 11 10 4.5 19.5 4.5c0 9.5-6.5 15-15 15Z"/><path d="M4.5 19.5 14 10"/>',
    alerta: '<path d="M12 4 2.8 19.5h18.4Z"/><path d="M12 10v4.5M12 17.2v.1"/>',
    sol: '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M5.3 18.7l1.4-1.4M17.3 6.7l1.4-1.4"/>',
    voz: '<path d="M4 9.5h3.5L12 5.5v13l-4.5-4H4Z"/><path d="M15.5 9a4 4 0 0 1 0 6M18 6.5a7.5 7.5 0 0 1 0 11"/>',
    pausa: '<path d="M8.5 5.5v13M15.5 5.5v13"/>',
    compartir: '<path d="M12 3.5v11M7.5 8 12 3.5 16.5 8"/><path d="M5 12.5V19a1.5 1.5 0 0 0 1.5 1.5h11A1.5 1.5 0 0 0 19 19v-6.5"/>',
    mapa: '<path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2Z"/><path d="M9 4v14M15 6v14"/>',
    dron: '<circle cx="5.5" cy="5.5" r="2.5"/><circle cx="18.5" cy="5.5" r="2.5"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/><path d="M8 8l2.5 2.5M16 8l-2.5 2.5M8 16l2.5-2.5M16 16l-2.5-2.5"/><rect x="9.5" y="9.5" width="5" height="5" rx="1"/>',
    archivo: '<path d="M3 7h6l2 2h10v10H3Z"/>',
    otra: '<path d="M19.5 12a7.5 7.5 0 1 1-2.2-5.3L19.5 9"/><path d="M19.5 4v5h-5"/>',
    cerrar: '<path d="M6 6l12 12M18 6 6 18"/>',
    pregunta: '<circle cx="12" cy="12" r="9"/><path d="M9.6 9.4a2.5 2.5 0 1 1 3.4 2.4c-.6.3-1 .8-1 1.5v.7M12 17v.1"/>',
    flecha: '<path d="M5 12h14M13 6l6 6-6 6"/>',
    arriba: '<path d="M12 19V5M6 11l6-6 6 6"/>',
  };
  const icono = (nombre, clase = "") =>
    `<svg class="ico ${clase}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONOS[nombre] || ""}</svg>`;

  // Código QR de https://dron-sigatoka.netlify.app (29 x 29 módulos, corrección M).
  const QR_D = "M0 0.5h7m3 0h2m1 0h1m2 0h4m2 0h7m-29 1h1m5 0h1m4 0h1m1 0h3m2 0h1m3 0h1m5 0h1m-29 1h1m1 0h3m1 0h1m3 0h1m1 0h2m2 0h5m1 0h1m1 0h3m1 0h1m-29 1h1m1 0h3m1 0h1m6 0h3m2 0h1m3 0h1m1 0h3m1 0h1m-29 1h1m1 0h3m1 0h1m4 0h4m1 0h1m1 0h1m1 0h1m1 0h1m1 0h3m1 0h1m-29 1h1m5 0h1m1 0h1m1 0h5m3 0h2m2 0h1m5 0h1m-29 1h7m1 0h1m1 0h1m1 0h1m1 0h1m1 0h1m1 0h1m1 0h1m1 0h7m-17 1h1m1 0h1m2 0h2m-19 1h1m2 0h1m1 0h2m1 0h1m3 0h1m2 0h2m4 0h1m1 0h1m-24 1h2m1 0h3m1 0h2m1 0h2m2 0h2m1 0h2m1 0h4m1 0h1m2 0h1m-27 1h1m2 0h3m2 0h1m1 0h1m6 0h1m1 0h2m2 0h3m-27 1h1m1 0h1m4 0h5m1 0h2m4 0h1m2 0h2m1 0h2m-25 1h2m1 0h3m2 0h2m3 0h2m1 0h4m2 0h1m1 0h2m-29 1h3m2 0h1m3 0h2m4 0h2m2 0h2m-21 1h1m1 0h5m1 0h2m1 0h1m4 0h2m2 0h1m1 0h1m2 0h4m-25 1h2m1 0h1m1 0h2m1 0h4m1 0h1m2 0h1m1 0h1m1 0h2m1 0h1m-28 1h1m3 0h6m1 0h1m1 0h2m1 0h2m2 0h2m5 0h1m-27 1h1m5 0h2m2 0h2m3 0h2m3 0h3m1 0h1m2 0h1m-29 1h1m1 0h5m1 0h2m1 0h1m1 0h1m2 0h1m1 0h1m1 0h1m6 0h2m-27 1h1m2 0h1m1 0h2m2 0h3m1 0h4m1 0h1m1 0h2m3 0h2m-29 1h1m4 0h2m1 0h2m1 0h2m1 0h1m5 0h5m1 0h1m-19 1h2m1 0h1m1 0h1m2 0h2m2 0h1m3 0h1m1 0h3m-29 1h7m2 0h2m2 0h2m1 0h2m2 0h1m1 0h1m1 0h1m2 0h1m-28 1h1m5 0h1m1 0h4m1 0h1m1 0h1m4 0h1m3 0h3m-27 1h1m1 0h3m1 0h1m3 0h3m1 0h1m1 0h2m2 0h5m3 0h1m-29 1h1m1 0h3m1 0h1m1 0h1m1 0h2m2 0h1m3 0h2m2 0h1m1 0h4m-28 1h1m1 0h3m1 0h1m2 0h1m1 0h1m1 0h2m1 0h3m5 0h3m1 0h1m-29 1h1m5 0h1m3 0h5m1 0h5m2 0h1m3 0h1m-28 1h7m1 0h1m2 0h1m1 0h1m1 0h1m1 0h2m1 0h6m1 0h1";
  const qr = (clase = "") =>
    `<svg class="qr ${clase}" viewBox="-2 -2 33 33" role="img" aria-label="Código QR de ${SITIO.replace("https://", "")}" shape-rendering="crispEdges"><rect x="-2" y="-2" width="33" height="33" fill="#fff"/><path d="${QR_D}" stroke="#000" fill="none"/></svg>`;

  // ------------------------------------------------------------------ cargar scripts
  const cargados = {};
  function cargarScript(src) {
    cargados[src] ??= new Promise((ok, mal) => {
      const s = document.createElement("script");
      s.src = src; s.onload = ok; s.onerror = () => { delete cargados[src]; mal(new Error("No se pudo cargar " + src)); };
      document.head.append(s);
    });
    return cargados[src];
  }

  // ------------------------------------------------------------------ modelo en el navegador
  // La primera vez baja unos 20 MB (motor de WebAssembly + modelo). Se avisa el avance a quien
  // escuche con alProgreso(0..1), para mostrar una barra en vez de una espera muda.
  const TAMANOS = { wasm: 14239897, onnx: 5784396 };   // bytes sin comprimir, para estimar el avance
  let promesaModelo = null, avance = 0;
  const oyentes = new Set();
  const avisarAvance = v => { avance = v; oyentes.forEach(f => f(v)); };

  async function bajar(url, esperado, base, total) {
    const r = await fetch(url);
    if (!r.ok) throw new Error(`No se pudo bajar ${url.split("/").pop()} (${r.status}).`);
    if (!r.body?.getReader) return new Uint8Array(await r.arrayBuffer());
    const lector = r.body.getReader(), partes = [];
    let n = 0;
    for (;;) {
      const { done, value } = await lector.read();
      if (done) break;
      partes.push(value); n += value.length;
      avisarAvance(Math.min(.99, (base + Math.min(n, esperado)) / total));
    }
    const todo = new Uint8Array(n); let k = 0;
    partes.forEach(p => { todo.set(p, k); k += p.length; });
    return todo;
  }

  function modelo(alProgreso) {
    if (alProgreso) { oyentes.add(alProgreso); alProgreso(avance); }
    promesaModelo ??= (async () => {
      const total = TAMANOS.wasm + TAMANOS.onnx;
      if (!window.ort) await cargarScript(RAIZ + "vendor/ort.wasm.min.js");
      ort.env.wasm.wasmPaths = RAIZ + "vendor/";
      ort.env.wasm.numThreads = 1;   // sin aislamiento entre orígenes el navegador no da hilos
      ort.env.wasm.wasmBinary = (await bajar(RAIZ + "vendor/ort-wasm-simd-threaded.wasm", TAMANOS.wasm, 0, total)).buffer;
      const meta = await (await fetch(RAIZ + "modelo/sigatoka_cls_v1.json")).json();
      const bytes = await bajar(RAIZ + "modelo/sigatoka_cls_v1.onnx", TAMANOS.onnx, TAMANOS.wasm, total);
      const sesion = await ort.InferenceSession.create(bytes, { executionProviders: ["wasm"] });
      avisarAvance(1);
      return { sesion, entrada: sesion.inputNames[0], salida: sesion.outputNames[0], clases: meta.classes,
               umbral: meta.umbral_confianza ?? 0.65, lado: meta.input[meta.input.length - 1], acierto: meta.top1_test };
    })();
    promesaModelo.catch(() => { promesaModelo = null; avisarAvance(0); });   // si falla, el siguiente intento lo vuelve a bajar
    const quitar = () => { if (alProgreso) oyentes.delete(alProgreso); };
    promesaModelo.then(quitar, quitar);
    return promesaModelo;
  }
  const modeloListo = () => avance >= 1;

  // Revisión rápida de la foto antes del modelo: muy oscura, quemada, o sin nada verde.
  // Si no hay casi nada verde (una mano, el cielo, una pared), el resultado pasa a "no sé":
  // el modelo siempre elige una de sus tres clases y diría "sana" con mucha seguridad.
  async function calidad(archivo) {
    const img = await createImageBitmap(archivo);
    const c = document.createElement("canvas"); c.width = c.height = 64;
    const ctx = c.getContext("2d", { willReadFrequently: true });
    ctx.drawImage(img, 0, 0, 64, 64); img.close();
    const { data } = ctx.getImageData(0, 0, 64, 64);
    let luz = 0, verde = 0;
    for (let i = 0; i < data.length; i += 4) {
      const r = data[i], g = data[i + 1], b = data[i + 2];
      luz += .299 * r + .587 * g + .114 * b;
      if (g > 40 && g > r * 1.05 && g > b * 1.1) verde++;
    }
    const n = data.length / 4;
    luz /= n; verde /= n;
    return { oscura: luz < 45, quemada: luz > 225, sinHoja: verde < .05, verde };
  }

  // Mismo preprocesado que vision/clasificador.py: estirar a 384 x 384, RGB, /255, CHW.
  async function tensorDe(archivo, lado) {
    const imagen = await createImageBitmap(archivo);
    const lienzo = document.createElement("canvas");
    lienzo.width = lienzo.height = lado;
    const ctx = lienzo.getContext("2d", { willReadFrequently: true });
    ctx.drawImage(imagen, 0, 0, lado, lado);
    imagen.close();
    const { data } = ctx.getImageData(0, 0, lado, lado);
    const n = lado * lado, x = new Float32Array(3 * n);
    for (let i = 0; i < n; i++) {
      x[i] = data[4 * i] / 255; x[n + i] = data[4 * i + 1] / 255; x[2 * n + i] = data[4 * i + 2] / 255;
    }
    return new ort.Tensor("float32", x, [1, 3, lado, lado]);
  }

  // Devuelve { clase, confianza, seguro, umbral, probs, ms }.
  async function diagnosticar(archivo, alProgreso) {
    const m = await modelo(alProgreso);
    const inicio = performance.now();
    let revision = null;
    try { revision = await calidad(archivo); } catch (e) {}
    let p;
    try {
      const salida = await m.sesion.run({ [m.entrada]: await tensorDe(archivo, m.lado) });
      p = Array.from(salida[m.salida].data);
    } catch (e) {
      if (e instanceof DOMException || /decode|image|source/i.test(e.message)) throw new Error("No pude leer esa foto. Prueba con una foto JPG o PNG.");
      throw e;
    }
    const suma = p.reduce((a, b) => a + b, 0);
    if (!(suma >= .99 && suma <= 1.01)) {   // por si el export no trae softmax
      const max = Math.max(...p), e = p.map(v => Math.exp(v - max)), s = e.reduce((a, b) => a + b, 0);
      p = e.map(v => v / s);
    }
    const top = p.indexOf(Math.max(...p));
    return { clase: m.clases[top], confianza: p[top], seguro: p[top] >= m.umbral && !revision?.sinHoja, umbral: m.umbral,
             probs: Object.fromEntries(m.clases.map((c, i) => [c, p[i]])), ms: Math.round(performance.now() - inicio), calidad: revision };
  }

  // Lo que la interfaz dice de una lectura: palabra, título, color, pasos, frase de confianza y voz.
  function lectura(r) {
    const clave = r.seguro ? r.clase : "dudoso";
    const sinHoja = !r.seguro && r.calidad?.sinHoja;
    let L = LECTURAS[clave] || { palabra: cat(r.clase).nombre, titulo: `Parece ${cat(r.clase).nombre}`, pasos: LECTURAS.dudoso.pasos.slice(2) };
    if (sinHoja) L = { palabra: "No veo hoja", titulo: "No veo una hoja", pasos: [
      ["hoja", "Acerca la cámara a una hoja de plátano, que llene el cuadro."], LECTURAS.dudoso.pasos[1]] };
    const luz = r.calidad?.oscura ? " La foto salió muy oscura." : r.calidad?.quemada ? " La foto salió con demasiada luz." : "";
    const n = Math.round(r.confianza * 100), minimo = Math.round(r.umbral * 100);
    const confianza = (sinHoja ? "Casi no hay verde en la foto, así que no la diagnostico."
      : r.seguro ? `El modelo está ${n} % seguro. Necesita al menos ${minimo} % para decirlo.`
      : `Lo más parecido es ${cat(r.clase).nombre} (${n} %), pero necesita al menos ${minimo} % para decirlo.`) + luz;
    const voz = (r.seguro ? `${L.titulo}. El modelo está ${n} por ciento seguro. ` : sinHoja ? "No veo una hoja en la foto. " : "No estoy seguro de lo que veo. ") +
      L.pasos.map(p => p[1]).join(" ");
    return { clave, ...L, color: r.seguro ? cat(r.clase).color : GRIS, nombre: r.seguro ? cat(r.clase).nombre : "No estoy seguro",
             porcentaje: n, minimo, confianza, voz };
  }

  // ------------------------------------------------------------------ voz
  let voces = [];
  const puedeHablar = "speechSynthesis" in window;
  if (puedeHablar) {
    const cargar = () => { voces = speechSynthesis.getVoices(); };
    cargar(); speechSynthesis.addEventListener?.("voiceschanged", cargar);
  }
  function hablar(texto, alTerminar) {
    if (!puedeHablar) return false;
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(texto);
    const v = voces.find(v => /^es[-_]MX/i.test(v.lang)) || voces.find(v => /^es[-_](US|419)/i.test(v.lang)) || voces.find(v => /^es/i.test(v.lang));
    if (v) u.voice = v;
    u.lang = v?.lang || "es-MX";
    u.rate = .95;
    u.onend = u.onerror = () => alTerminar?.();
    speechSynthesis.speak(u);
    return true;
  }
  const callar = () => { if (puedeHablar) speechSynthesis.cancel(); };
  const vozActiva = {
    get() { try { return localStorage.getItem("voz") !== "no"; } catch (e) { return true; } },
    set(si) { try { localStorage.setItem("voz", si ? "si" : "no"); } catch (e) {} },
  };

  // ------------------------------------------------------------------ compartir con el técnico
  async function compartir(r, archivo) {
    const L = lectura(r);
    const texto = (r.seguro ? `Revisé una hoja de plátano: ${L.titulo.toLowerCase()} (el modelo está ${L.porcentaje} % seguro).`
      : "Revisé una hoja de plátano y el modelo no está seguro de lo que ve.") + ` ¿La puedes revisar? ${SITIO}`;
    try {
      if (archivo && navigator.canShare?.({ files: [archivo] })) { await navigator.share({ files: [archivo], text: texto }); return "compartido"; }
      if (navigator.share) { await navigator.share({ text: texto }); return "compartido"; }
    } catch (e) {
      if (e.name === "AbortError") return "cancelado";
    }
    window.open("https://wa.me/?text=" + encodeURIComponent(texto), "_blank", "noopener");
    return "whatsapp";
  }

  // ------------------------------------------------------------------ mapa del lote
  const NO_DIAGNOSTICA = new Set(["sin_hoja"]);
  const PRIORIDAD = ["sigatoka", "otra_condicion", "sana"];   // en un empate, la zona toma lo más grave
  const prioridad = k => (PRIORIDAD.indexOf(k) + 1) || 99;

  function claveDeNombre(nombre) {
    const n = String(nombre || "").trim().toLowerCase();
    const hallada = Object.entries(CAT).find(([k, c]) => c.nombre.toLowerCase() === n || k === n);
    return hallada ? hallada[0] : (n || null);
  }

  // Lee el .geojson que descarga la estación (Mapa > Descargar el mapa). También los archivos viejos.
  function leerGeojson(texto) {
    const datos = JSON.parse(texto);
    const fotos = (datos.features || [])
      .filter(f => f?.geometry?.type === "Point" && Array.isArray(f.geometry.coordinates))
      .map(f => {
        const p = f.properties || {};
        const [lon, lat] = f.geometry.coordinates;
        const clave = p.clave || claveDeNombre(p.diagnostico);
        const humano = p.fuente === "revisión humana";
        const conf = typeof p.confianza_modelo === "number" ? p.confianza_modelo : null;
        const dudoso = typeof p.dudoso === "boolean" ? p.dudoso : (!humano && conf != null && conf < (p.umbral ?? .65));
        return { lat: +lat, lon: +lon, clave, dudoso: !clave || dudoso, humano, conf, fecha: p.fecha || "",
                 archivo: p.archivo || "", revisor: p.revisor || "", vuelo: p.vuelo || "" };
      })
      .filter(f => Number.isFinite(f.lat) && Number.isFinite(f.lon));
    if (!fotos.length) throw new Error("no trae fotos con ubicación");
    return fotos;
  }

  // Lote de ejemplo con datos inventados (para mostrar el mapa sin la estación): un foco de
  // Sigatoka en una esquina que se va diluyendo, otra condición en la esquina contraria.
  function ejemplo() {
    let s = 11;
    const azar = () => { s = s + 0x6D2B79F5 | 0; let t = Math.imul(s ^ s >>> 15, 1 | s); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
    const dLat = 20 / 111320, dLon = 20 / (111320 * Math.cos(17.9 * Math.PI / 180));
    const lat0 = Math.floor(17.9 / dLat) * dLat, lon0 = Math.floor(-93 / dLon) * dLon;
    const fotos = [];
    for (let i = 0; i < 6; i++) for (let j = 0; j < 9; j++) {
      const n = 1 + Math.floor(azar() * 2.6);
      for (let k = 0; k < n; k++) {
        const foco = Math.hypot(i - 4.6, j - 1.2);
        let clave = azar() < Math.max(0, .98 - foco * .2) ? "sigatoka" : "sana";
        if (clave === "sana" && i <= 1 && j >= 6 && azar() < .6) clave = "otra_condicion";
        const dudoso = azar() < .07;
        const humano = !dudoso && azar() < .45;
        fotos.push({ lat: lat0 + (i + .1 + azar() * .8) * dLat, lon: lon0 + (j + .1 + azar() * .8) * dLon, clave, dudoso, humano,
                     conf: dudoso ? .5 + azar() * .13 : .7 + azar() * .29, fecha: "Ejemplo", archivo: `ejemplo_${String(fotos.length + 1).padStart(2, "0")}.jpg`,
                     revisor: humano ? "Agrónomo" : "", vuelo: "ejemplo" });
      }
    }
    return fotos;
  }

  async function leaflet() {
    if (!window.L) {
      const l = document.createElement("link");
      l.rel = "stylesheet"; l.href = RAIZ + "vendor/leaflet/leaflet.css";
      document.head.prepend(l);   // primero, para que el estilo de la variante gane
      await cargarScript(RAIZ + "vendor/leaflet/leaflet.js");
    }
    return window.L;
  }

  function zonas(fotos, metros) {
    const lat0 = fotos.reduce((s, f) => s + f.lat, 0) / fotos.length;
    const dLat = metros / 111320, dLon = metros / (111320 * Math.cos(lat0 * Math.PI / 180));
    const celdas = new Map();
    fotos.forEach(f => {
      if (f.dudoso || NO_DIAGNOSTICA.has(f.clave)) return;
      const i = Math.floor(f.lat / dLat), j = Math.floor(f.lon / dLon), k = `${i}|${j}`;
      const c = celdas.get(k) || { i, j, n: 0, cuenta: {}, dLat, dLon };
      c.n++; c.cuenta[f.clave] = (c.cuenta[f.clave] || 0) + 1;
      celdas.set(k, c);
    });
    return [...celdas.values()].map(c => ({ ...c,
      dominante: Object.keys(c.cuenta).sort((a, b) => c.cuenta[b] - c.cuenta[a] || prioridad(a) - prioridad(b))[0] }));
  }

  // "38 sanas", "10 con Sigatoka", "9 con otra condición".
  function cuantas(clave, n) {
    if (clave === "sana") return `${n} ${n === 1 ? "sana" : "sanas"}`;
    if (clave === "dudoso") return `${n} sin diagnóstico seguro`;
    return `${n} con ${clave === "otra_condicion" ? "otra condición" : cat(clave).nombre}`;
  }

  function resumen(fotos, metros) {
    const porClase = {}; let dudosas = 0;
    fotos.forEach(f => { if (f.dudoso) dudosas++; else porClase[f.clave] = (porClase[f.clave] || 0) + 1; });
    const zs = zonas(fotos, metros), zonasPor = {};
    zs.forEach(z => { zonasPor[z.dominante] = (zonasPor[z.dominante] || 0) + 1; });
    const conSig = zs.filter(z => z.cuenta.sigatoka).length;
    const partes = Object.entries(zonasPor).sort((a, b) => prioridad(a[0]) - prioridad(b[0])).map(([k, n]) => cuantas(k, n));
    const frase = zs.length
      ? `De ${plural(zs.length, "zona", "zonas")} de ${metros} m con fotos: ${partes.join(", ")}.` +
        (conSig ? ` ${plural(conSig, "zona tiene", "zonas tienen")} al menos una foto con Sigatoka: ahí conviene revisar primero.` : "")
      : "El archivo no trae fotos con un diagnóstico seguro.";
    return { total: fotos.length, porClase, dudosas, zonas: zs.length, zonasPor, conSig, frase, metros };
  }

  // Crea el mapa en un elemento. colores: { borde } para el contorno de las zonas sobre el fondo.
  async function crearMapa(el, { borde = "#ffffff" } = {}) {
    const L = await leaflet();
    el.style.isolation = "isolate";   // que las capas de Leaflet no pinten encima de la barra de la página
    const tactil = matchMedia("(pointer: coarse)").matches;
    const mapa = L.map(el, { zoomControl: false, scrollWheelZoom: false, attributionControl: true, dragging: !tactil, zoomSnap: .25 }).setView([17.99, -92.95], 15);
    if (tactil) {   // un dedo mueve la página, dos dedos mueven el mapa
      const aviso = document.createElement("div");
      aviso.className = "mapa-dos-dedos"; aviso.textContent = "Usa dos dedos para mover el mapa";
      Object.assign(aviso.style, { position: "absolute", inset: "0", zIndex: 1000, display: "grid", placeItems: "center", padding: "20px",
        background: "rgba(0,0,0,.45)", color: "#fff", font: "700 1.1rem/1.3 system-ui, sans-serif", textAlign: "center",
        opacity: 0, transition: "opacity 200ms ease", pointerEvents: "none" });
      el.append(aviso);
      let t = null;
      el.addEventListener("touchstart", e => { if (e.touches.length >= 2) mapa.dragging.enable(); }, { passive: true });
      el.addEventListener("touchend", e => { if (!e.touches.length) mapa.dragging.disable(); }, { passive: true });
      el.addEventListener("touchmove", e => {
        if (e.touches.length !== 1) return;
        aviso.style.opacity = 1; clearTimeout(t); t = setTimeout(() => { aviso.style.opacity = 0; }, 1200);
      }, { passive: true });
    }
    L.control.zoom({ position: "topright" }).addTo(mapa);
    L.control.scale({ imperial: false, position: "bottomleft" }).addTo(mapa);
    const satelite = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
      { maxZoom: 20, maxNativeZoom: 19, attribution: "Imágenes © Esri" });
    const capa = L.layerGroup().addTo(mapa);
    let fotos = [], vista = "zonas", metros = 20;

    function ficha(f) {
      const c = f.dudoso ? { nombre: "No está seguro", color: GRIS } : cat(f.clave);
      const fuente = f.humano ? `Revisada${f.revisor ? " por " + esc(f.revisor) : ""}` : f.conf != null ? `Modelo: ${pct(f.conf)}` : "Sin diagnóstico";
      return `<div class="mapa-ficha"><b><i style="background:${c.color}"></i>${esc(c.nombre)}</b><span>${fuente}${f.archivo ? ` · ${esc(f.archivo)}` : ""}</span></div>`;
    }
    function dibujar() {
      capa.clearLayers();
      if (!fotos.length) return;
      if (vista === "fotos") {
        fotos.forEach(f => L.circleMarker([f.lat, f.lon], {
          radius: 7, color: f.humano ? borde : "#0b1510", weight: f.humano ? 2.5 : 1.5,
          fillColor: f.dudoso ? GRIS : cat(f.clave).color, fillOpacity: .9,
        }).bindPopup(ficha(f)).addTo(capa));
        return;
      }
      zonas(fotos, metros).forEach(z => {
        const color = cat(z.dominante).color;
        const algo = z.dominante !== "sigatoka" && z.cuenta.sigatoka;
        const detalle = Object.entries(z.cuenta).sort((a, b) => b[1] - a[1]).map(([k, n]) => `${esc(cat(k).nombre)}: ${n}`).join(" · ");
        L.rectangle([[z.i * z.dLat, z.j * z.dLon], [(z.i + 1) * z.dLat, (z.j + 1) * z.dLon]], {
          color: algo ? CAT.sigatoka.color : color, weight: algo ? 2.5 : 1.2, dashArray: algo ? "5 4" : null,
          fillColor: color, fillOpacity: .35 + .35 * Math.min(1, z.n / 4),
        }).bindTooltip(`<b>${esc(cat(z.dominante).nombre)}</b> · ${plural(z.n, "foto", "fotos")}<br>${detalle}`).addTo(capa);
      });
    }
    return {
      mapa,
      mostrar(lista, { conSatelite = true } = {}) {
        fotos = lista;
        mapa.invalidateSize();   // por si el contenedor cambió de tamaño desde que se creó
        if (conSatelite) satelite.addTo(mapa); else satelite.remove();
        el.classList.toggle("sin-fondo", !conSatelite);
        dibujar();
        mapa.fitBounds(L.latLngBounds(fotos.map(f => [f.lat, f.lon])), { padding: [24, 24], maxZoom: 19 });
        return resumen(fotos, metros);
      },
      vista(v) { vista = v; dibujar(); },
      invalidar() { mapa.invalidateSize(); },
    };
  }

  // ------------------------------------------------------------------ dron en vivo
  // La Jetson (jetson/zed_right.py) da video, GPS y diagnóstico en su puerto 8080. Desde una página
  // https el navegador solo deja hablar con otra dirección https: la del túnel de la Jetson.
  const PRIVADA = /^(10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.|127\.|localhost$)/;
  function leerDireccion(texto) {
    texto = texto.trim();
    const u = new URL(/^https?:\/\//i.test(texto) ? texto : `https://${texto}`);
    if (PRIVADA.test(u.hostname)) {
      const local = `http://${u.hostname}:${u.port || 8080}`;
      return location.protocol === "https:" ? { local } : { base: local };
    }
    u.protocol = "https:";
    return { base: u.origin };
  }

  // Avisa a la variante con: aviso({ titulo, texto, error, local }), conectado({ host, video }),
  // estado({ lectura, gps, ms, sinModelo, esperando }), desconectado().
  function dron(avisar) {
    let d = null;
    async function pedir(ruta, opciones = {}, espera = 6000) {
      const control = new AbortController();
      const t = setTimeout(() => control.abort(), espera);
      try {
        const r = await fetch(d.base + ruta, { ...opciones, signal: control.signal, cache: "no-store" });
        if (!r.ok) { const j = await r.json().catch(() => ({})); throw new Error(j.error || `El dron respondió ${r.status}`); }
        return r;
      } finally { clearTimeout(t); }
    }
    function estado(est) {
      const p = est.prediccion;
      const umbral = est.modelo?.umbral ?? .65;
      avisar.estado?.({
        sinModelo: !est.modelo, esperando: !!est.modelo && !p, gps: est.gps || null, ms: p?.ms,
        lectura: p ? { clase: p.clase, confianza: p.confianza, seguro: p.confianza >= umbral, umbral, probs: p.probs } : null,
      });
    }
    async function ciclo() {
      if (!d) return;
      try { estado(await (await pedir("/estado", {}, 4000)).json()); d.fallas = 0; }
      catch (e) { if (d && ++d.fallas === 3) avisar.aviso?.({ titulo: "Se perdió la conexión", texto: "Sigo intentando…", error: true }); }
      if (d) d.temporizador = setTimeout(ciclo, 1000);
    }
    function desconectar() {
      if (d) clearTimeout(d.temporizador);
      const habia = !!d;
      d = null;
      if (habia) avisar.desconectado?.();
    }
    async function conectar(texto) {
      let dir;
      try { dir = leerDireccion(texto); }
      catch (e) { return avisar.aviso?.({ titulo: "Esa dirección no es válida", texto: "Escribe la que imprimió el túnel, algo como https://palabras.trycloudflare.com", error: true }); }
      desconectar();
      if (dir.local) return avisar.aviso?.({ titulo: "Esa dirección es de la red local",
        texto: "Esta página es pública y el navegador no la deja leer la red local. En la misma WiFi que el dron, abre su página directo.", local: dir.local });
      try { localStorage.setItem("dron", texto.trim()); } catch (e) {}
      d = { base: dir.base, temporizador: null, fallas: 0 };
      const host = new URL(dir.base).host;
      avisar.aviso?.({ titulo: "Conectando con el dron…", texto: host });
      let est;
      try { est = await (await pedir("/estado")).json(); }
      catch (e) {
        d = null;
        return avisar.aviso?.({ titulo: "No se pudo conectar", error: true,
          texto: `No contestó ${host}. Revisa que el dron esté encendido, con la cámara abierta y el túnel corriendo.` });
      }
      avisar.conectado?.({ host, video: `${dir.base}/video?t=${Date.now()}` });
      estado(est);
      d.temporizador = setTimeout(ciclo, 1000);
    }
    async function foto() {
      if (!d) throw new Error("No hay dron conectado");
      const r = await (await pedir("/foto", { method: "POST" }, 10000)).json();
      return { archivo: r.archivo, url: d.base + (r.url_sin_texto || r.url) };
    }
    const enJetson = PRIVADA.test(location.hostname) ? `${location.hostname}:8080` : null;
    let guardada = "";
    try { guardada = localStorage.getItem("dron") || ""; } catch (e) {}
    const inicial = new URLSearchParams(location.search).get("dron") || enJetson;
    return { conectar, desconectar, foto, conectado: () => !!d, video: () => d && `${d.base}/video?t=${Date.now()}`,
             inicial, sugerida: inicial || guardada };
  }

  // Precarga el modelo cuando la página ya está quieta, para que la primera foto no espere tanto.
  // Con datos limitados (ahorro de datos o red 2G/3G) espera a que la persona tome la primera foto.
  function precargar() {
    const red = navigator.connection;
    if (red && (red.saveData || /(^|-)(2g|3g)$/.test(red.effectiveType || ""))) return;
    const ir = () => modelo().catch(() => {});
    if ("requestIdleCallback" in window) requestIdleCallback(ir, { timeout: 2500 }); else setTimeout(ir, 1200);
  }

  return { CAT, cat, GRIS, LECTURAS, esc, plural, pct, icono, qr, SITIO, modelo, modeloListo, diagnosticar, lectura, precargar,
           hablar, callar, puedeHablar, vozActiva, compartir, leerGeojson, ejemplo, crearMapa, resumen, cuantas, dron };
})();
