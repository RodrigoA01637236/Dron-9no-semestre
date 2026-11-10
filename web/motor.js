// Motor del sitio (index.html): revisar una hoja con el modelo en el navegador, el mapa del lote y
// el dron en vivo. No pinta nada: index.html decide cómo se ve.
// Todo corre en el navegador: la foto y el archivo del mapa nunca salen del dispositivo.
"use strict";
const Motor = (() => {
  const RAIZ = new URL("./", document.currentScript.src).href;   // la carpeta web/
  const SITIO = "https://dron-sigatoka.netlify.app";
  const GRIS = "#7d8b96";

  const CAT = {
    sana: { nombre: "Sana", color: "#2e9e44" },
    sigatoka: { nombre: "Sigatoka", color: "#d7263d" },
    otra_condicion: { nombre: "Otro problema", color: "#f0a202" },
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
    otra_condicion: { palabra: "Otro problema", titulo: "Parece otro problema", pasos: [
      ["telefono", "No parece Sigatoka, pero algo tiene: pide que tu técnico la revise."],
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
    bajar: '<path d="M12 4v11M7.5 10.5 12 15l4.5-4.5"/><path d="M5 19.5h14"/>',
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

  // ------------------------------------------------------------------ rasgos y última capa
  // El modelo termina en: rasgos (1280 números) -> una capa lineal (3 x 1280) -> softmax.
  // Para mejorar esa última capa en el navegador, al cargarlo se le agrega una salida con los
  // rasgos (mismo modelo, mismos pesos; se edita el protobuf del .onnx aquí mismo) y se leen
  // los pesos de la capa. Si algo falla, el modelo funciona igual, solo sin poder mejorarse.
  const RASGOS = "/model.9/Flatten_output_0", PESO = "model.9.linear.weight", SESGO = "model.9.linear.bias";
  function varint(buf, p) { let x = 0, f = 1, b; do { b = buf[p++]; x += (b & 127) * f; f *= 128; } while (b & 128); return [x, p]; }
  function codificar(x) { const o = []; while (x > 127) { o.push((x % 128) | 128); x = Math.floor(x / 128); } o.push(x); return o; }
  function campos(buf, ini, fin) {
    const lista = [];
    for (let p = ini; p < fin;) {
      const k0 = p; let k, a, b, n;
      [k, p] = varint(buf, p);
      const campo = Math.floor(k / 8), tipo = k & 7;
      if (tipo === 0) { a = p; [, p] = varint(buf, p); b = p; }
      else if (tipo === 1) { a = p; p += 8; b = p; }
      else if (tipo === 5) { a = p; p += 4; b = p; }
      else if (tipo === 2) { [n, a] = varint(buf, p); b = a + n; p = b; }
      else throw new Error("protobuf con un tipo inesperado");
      lista.push({ campo, tipo, k0, a, b });
    }
    return lista;
  }
  const largo = (campo, bytes) => [...codificar(campo * 8 + 2), ...codificar(bytes.length), ...bytes];
  const entero = (campo, v) => [...codificar(campo * 8), ...codificar(v)];
  function conRasgos(bytes) {
    const grafo = campos(bytes, 0, bytes.length).find(c => c.campo === 7 && c.tipo === 2);
    const enGrafo = campos(bytes, grafo.a, grafo.b);
    const leer = (nombre) => {   // TensorProto float guardado en raw_data
      for (const c of enGrafo.filter(c => c.campo === 5)) {
        const t = campos(bytes, c.a, c.b), n = t.find(x => x.campo === 8);
        if (n && new TextDecoder().decode(bytes.subarray(n.a, n.b)) === nombre) {
          const r = t.find(x => x.campo === 9);
          return new Float32Array(bytes.slice(r.a, r.b).buffer);
        }
      }
      throw new Error("no encontré " + nombre);
    };
    const W0 = leer(PESO), b0 = leer(SESGO);
    const forma = largo(2, [...largo(1, entero(1, 1)), ...largo(1, entero(1, W0.length / b0.length))]);
    const salida = largo(12, largo(1, [...new TextEncoder().encode(RASGOS)]).concat(largo(2, largo(1, [...entero(1, 1), ...forma]))));
    const nuevoGrafo = new Uint8Array(grafo.b - grafo.a + salida.length);
    nuevoGrafo.set(bytes.subarray(grafo.a, grafo.b)); nuevoGrafo.set(salida, grafo.b - grafo.a);
    const cabeza = codificar(7 * 8 + 2).concat(codificar(nuevoGrafo.length));
    const todo = new Uint8Array(grafo.k0 + cabeza.length + nuevoGrafo.length + bytes.length - grafo.b);
    todo.set(bytes.subarray(0, grafo.k0)); todo.set(cabeza, grafo.k0);
    todo.set(nuevoGrafo, grafo.k0 + cabeza.length); todo.set(bytes.subarray(grafo.b), grafo.k0 + cabeza.length + nuevoGrafo.length);
    return { bytes: todo, W0, b0 };
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
      let sesion = null, ultima = null;
      try {
        const c = conRasgos(bytes);
        sesion = await ort.InferenceSession.create(c.bytes, { executionProviders: ["wasm"] });
        if (sesion.outputNames.includes(RASGOS)) ultima = { W0: c.W0, b0: c.b0 }; else sesion = null;
      } catch (e) { sesion = null; }
      sesion ??= await ort.InferenceSession.create(bytes, { executionProviders: ["wasm"] });
      avisarAvance(1);
      return { sesion, entrada: sesion.inputNames[0], salida: sesion.outputNames.find(n => n !== RASGOS), clases: meta.classes,
               umbral: meta.umbral_confianza ?? 0.65, lado: meta.input[meta.input.length - 1], acierto: meta.top1_test,
               nombre: meta.model || "sigatoka_cls_v1", rasgos: ultima ? RASGOS : null, ...(ultima || {}) };
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
  async function tensorDe(archivo, lado, espejo = false) {
    const imagen = await createImageBitmap(archivo);
    const lienzo = document.createElement("canvas");
    lienzo.width = lienzo.height = lado;
    const ctx = lienzo.getContext("2d", { willReadFrequently: true });
    if (espejo) { ctx.translate(lado, 0); ctx.scale(-1, 1); }
    ctx.drawImage(imagen, 0, 0, lado, lado);
    imagen.close();
    const { data } = ctx.getImageData(0, 0, lado, lado);
    const n = lado * lado, x = new Float32Array(3 * n);
    for (let i = 0; i < n; i++) {
      x[i] = data[4 * i] / 255; x[n + i] = data[4 * i + 1] / 255; x[2 * n + i] = data[4 * i + 2] / 255;
    }
    return new ort.Tensor("float32", x, [1, 3, lado, lado]);
  }

  // Devuelve { clase, confianza, seguro, umbral, probs, ms, mejorado, rasgos, rasgosEspejo }.
  // opciones.espejo: también los rasgos de la foto volteada (para mejorar el modelo).
  async function diagnosticar(archivo, alProgreso, opciones = {}) {
    const m = await modelo(alProgreso);
    const inicio = performance.now();
    let revision = null;
    try { revision = await calidad(archivo); } catch (e) {}
    let p, rasgos = null, rasgosEspejo = null, mejorado = false;
    try {
      const salida = await m.sesion.run({ [m.entrada]: await tensorDe(archivo, m.lado) });
      p = Array.from(salida[m.salida].data);
      if (m.rasgos) {
        rasgos = Float32Array.from(salida[m.rasgos].data);
        const c = cabeza.leer(m);
        if (c) { p = aplicarCabeza(c, rasgos); mejorado = true; }
        if (opciones.espejo) rasgosEspejo = Float32Array.from((await m.sesion.run({ [m.entrada]: await tensorDe(archivo, m.lado, true) }))[m.rasgos].data);
      }
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
             probs: Object.fromEntries(m.clases.map((c, i) => [c, p[i]])), ms: Math.round(performance.now() - inicio), calidad: revision,
             mejorado, rasgos, rasgosEspejo };
  }

  // ------------------------------------------------------------------ mejorar la última capa aquí mismo
  // Probabilidades de una cabeza { W (K x D, por filas), b (K) } para unos rasgos.
  function aplicarCabeza(c, f) {
    const K = c.b.length, D = f.length, z = new Float64Array(K);
    for (let k = 0; k < K; k++) { let s = c.b[k]; const o = k * D; for (let d = 0; d < D; d++) s += c.W[o + d] * f[d]; z[k] = s; }
    const mx = Math.max(...z); let t = 0;
    for (let k = 0; k < K; k++) { z[k] = Math.exp(z[k] - mx); t += z[k]; }
    return Array.from(z, v => v / t);
  }
  // La cabeza mejorada que usa este navegador (se guarda aquí, no sale de la computadora).
  const cabeza = {
    clave: "cabeza-mejorada",
    leer(m) {
      try {
        const c = JSON.parse(localStorage.getItem(this.clave) || "null");
        if (!c || (m && (c.modelo !== m.nombre || c.W.length !== m.W0.length))) return null;
        return { ...c, W: Float32Array.from(c.W), b: Float32Array.from(c.b) };
      } catch (e) { return null; }
    },
    guardar(c, m) {
      localStorage.setItem(this.clave, JSON.stringify({ ...c, W: Array.from(c.W), b: Array.from(c.b), modelo: m.nombre }));
    },
    quitar() { try { localStorage.removeItem(this.clave); } catch (e) {} },
  };
  // Entrena la última capa con [{ f: rasgos, y: índice de la clase }]. Empieza desde la del modelo
  // original y no se aleja mucho de ella (ancla), para no olvidar lo que ya sabe. Clases equilibradas.
  async function entrenarCabeza(muestras, { vueltas = 400, ancla = 0.1, alProgreso } = {}) {
    const m = await modelo();
    if (!m.rasgos) throw new Error("Este navegador no pudo preparar el modelo para mejorarlo.");
    const K = m.b0.length, D = m.W0.length / K, N = muestras.length;
    const W = Float32Array.from(m.W0), b = Float32Array.from(m.b0);
    const porClase = new Array(K).fill(0); muestras.forEach(s => porClase[s.y]++);
    const presentes = porClase.filter(Boolean).length;
    const peso = porClase.map(n => n ? N / (presentes * n) : 0);
    const norma2 = muestras.reduce((a, s) => a + s.f.reduce((x, v) => x + v * v, 0), 0) / N;
    const paso = 1 / (norma2 / 2 + ancla);   // descenso de gradiente estable para esta escala de rasgos
    const gW = new Float64Array(K * D), gb = new Float64Array(K);
    let antes = Infinity;
    for (let v = 0; v < vueltas; v++) {
      gW.fill(0); gb.fill(0);
      let perdida = 0;
      for (const s of muestras) {
        const p = aplicarCabeza({ W, b }, s.f), w = peso[s.y] / N;
        perdida -= w * Math.log(Math.max(p[s.y], 1e-12));
        for (let k = 0; k < K; k++) {
          const e = (p[k] - (k === s.y ? 1 : 0)) * w, o = k * D;
          gb[k] += e;
          for (let d = 0; d < D; d++) gW[o + d] += e * s.f[d];
        }
      }
      for (let i = 0; i < W.length; i++) { W[i] -= paso * (gW[i] + ancla * (W[i] - m.W0[i])); perdida += ancla / 2 * (W[i] - m.W0[i]) ** 2; }
      for (let k = 0; k < K; k++) b[k] -= paso * (gb[k] + ancla * (b[k] - m.b0[k]));
      if (v % 20 === 0) { alProgreso?.(v / vueltas); await new Promise(r => setTimeout(r)); }
      if (Math.abs(antes - perdida) < 1e-6) break;
      antes = perdida;
    }
    alProgreso?.(1);
    return { W, b };
  }
  // Aciertos de una cabeza (o del modelo original, si es null) con [{ f, y }].
  async function aciertos(c, muestras) {
    const m = await modelo();
    const usar = c || { W: m.W0, b: m.b0 };
    return muestras.reduce((a, s) => { const p = aplicarCabeza(usar, s.f); return a + (p.indexOf(Math.max(...p)) === s.y); }, 0);
  }

  // Lo que la interfaz dice de una lectura: palabra, título, color, pasos, frase de confianza y voz.
  function lectura(r) {
    const clave = r.seguro ? r.clase : "dudoso";
    const sinHoja = !r.seguro && r.calidad?.sinHoja;
    let L = LECTURAS[clave] || { palabra: cat(r.clase).nombre, titulo: `Parece ${cat(r.clase).nombre}`, pasos: LECTURAS.dudoso.pasos.slice(2) };
    if (sinHoja) L = { palabra: "No veo hoja", titulo: "No veo una hoja", pasos: [
      ["hoja", "Usa una foto donde una hoja de plátano llene el cuadro."], LECTURAS.dudoso.pasos[1]] };
    const luz = r.calidad?.oscura ? " La foto salió muy oscura." : r.calidad?.quemada ? " La foto salió con demasiada luz." : "";
    const n = Math.round(r.confianza * 100), minimo = Math.round(r.umbral * 100);
    const confianza = (sinHoja ? "Casi no hay verde en la foto, así que no la reviso."
      : r.seguro ? `Qué tan seguro: ${n} de 100. Necesita ${minimo} para dar un resultado.`
      : `Lo más parecido es ${cat(r.clase).nombre.toLowerCase()}, pero solo ${n} de 100: necesita ${minimo} para decirlo.`) + luz;
    const cerca = r.seguro && n - minimo < 10 ? "Está cerca del límite: que lo confirme tu técnico. " : "";
    // Sana pero casi en el límite: no decir "se ve sana" ni "no se ven manchas"; pedir que el técnico la vea.
    if (cerca && clave === "sana") L = { ...L, titulo: "Parece sana", pasos: [
      ["telefono", "Manda la foto a tu técnico para que lo confirme."], L.pasos[1]] };
    const voz = (r.seguro ? `${L.titulo}. Qué tan seguro: ${n} de 100. ${cerca}` : sinHoja ? "No veo una hoja en la foto. " : "No estoy seguro de lo que veo. ") +
      L.pasos.map(p => p[1]).join(" ");
    return { clave, ...L, color: r.seguro ? cat(r.clase).color : GRIS, nombre: r.seguro ? cat(r.clase).nombre : "Sin confirmar",
             porcentaje: n, minimo, confianza, voz, sinHoja: !!sinHoja, cercaDelLimite: !!cerca };
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

  // ------------------------------------------------------------------ compartir con el técnico
  function mensaje(r) {
    const L = lectura(r);
    return (r.seguro ? `Revisé una hoja de plátano con Dron Sigatoka: ${L.titulo.toLowerCase()} (qué tan seguro: ${L.porcentaje} de 100).` +
        (L.cercaDelLimite ? " Está casi en el límite." : "")
      : "Revisé una hoja de plátano con Dron Sigatoka y no está seguro de lo que ve.") + ` ¿La puedes revisar? ${SITIO}`;
  }
  // En el celular: la hoja de compartir del teléfono, con la foto. Devuelve "compartido", "cancelado" o "whatsapp".
  async function compartir(r, archivo) {
    const texto = mensaje(r);
    try {
      if (archivo && navigator.canShare?.({ files: [archivo] })) { await navigator.share({ files: [archivo], text: texto }); return "compartido"; }
      if (navigator.share) { await navigator.share({ text: texto }); return "compartido"; }
    } catch (e) {
      if (e.name === "AbortError") return "cancelado";
    }
    window.open("https://wa.me/?text=" + encodeURIComponent(texto), "_blank", "noopener");
    return "whatsapp";
  }

  // La foto con el resultado escrito abajo, para mandarla al técnico o guardarla. Devuelve un File JPG.
  async function fotoConResultado(r, archivo) {
    const L = lectura(r);
    const img = await createImageBitmap(archivo);
    const W = Math.min(1280, img.width), H = Math.round(img.height * W / img.width), s = W / 1080, banda = Math.round(214 * s);
    const c = document.createElement("canvas"); c.width = W; c.height = H + banda;
    const ctx = c.getContext("2d");
    ctx.drawImage(img, 0, 0, W, H); img.close();
    ctx.fillStyle = "#ffffff"; ctx.fillRect(0, H, W, banda);
    try { await Promise.all(["600 52px Geist", "400 30px Geist"].map(f => document.fonts.load(f))); } catch (e) {}
    const letra = (peso, px) => `${peso} ${Math.round(px * s)}px Geist, system-ui, sans-serif`;
    const color = r.seguro ? L.color : "#0a0a0a";
    ctx.fillStyle = r.seguro ? L.color : GRIS;
    ctx.beginPath(); ctx.arc(60 * s, H + 70 * s, 13 * s, 0, 2 * Math.PI); ctx.fill();
    ctx.fillStyle = color; ctx.font = letra(600, 52); ctx.textBaseline = "alphabetic";
    ctx.fillText(L.titulo, 92 * s, H + 88 * s);
    ctx.fillStyle = "#3d3d3d"; ctx.font = letra(400, 30);
    ctx.fillText(L.sinHoja ? "No veo una hoja en la foto" : `Qué tan seguro: ${L.porcentaje} de 100${L.cercaDelLimite ? " · casi en el límite" : ""}`, 46 * s, H + 140 * s);
    const hoy = new Date().toLocaleDateString("es-MX", { day: "numeric", month: "long", year: "numeric" });
    ctx.fillStyle = "#8a8a8a"; ctx.font = letra(400, 24);
    ctx.fillText(`Dron Sigatoka · ${hoy} · ${SITIO.replace("https://", "")}`, 46 * s, H + 184 * s);
    const blob = await new Promise(ok => c.toBlob(ok, "image/jpeg", .9));
    const fecha = new Date().toISOString().slice(0, 10);
    return new File([blob], `hoja-${L.clave === "otra_condicion" ? "otro-problema" : L.clave}-${fecha}.jpg`, { type: "image/jpeg" });
  }

  // ------------------------------------------------------------------ fotos de un vuelo
  // El dron (jetson/zed_right.py) guarda en el EXIF de cada foto el GPS, la hora y un comentario
  // con lo que vio a bordo ("AnalisisYOLO=sigatoka; ConfianzaYOLO=0.820; ..."), y una copia sin
  // letras encima en sin_texto/. La captura de vision/capture.py deja un .json gemelo con el GPS.
  async function leerExif(archivo) {
    const v = new DataView(await archivo.slice(0, 256 * 1024).arrayBuffer());
    if (v.byteLength < 4 || v.getUint16(0) !== 0xFFD8) return {};
    for (let p = 2; p + 10 <= v.byteLength;) {
      const marca = v.getUint16(p), largo = v.getUint16(p + 2);
      if (marca === 0xFFE1 && v.getUint32(p + 4) === 0x45786966) return exifTiff(v, p + 10);   // "Exif"
      if ((marca & 0xFF00) !== 0xFF00 || marca === 0xFFDA) break;
      p += 2 + largo;
    }
    return {};
  }
  function exifTiff(v, t) {
    const le = v.getUint16(t) === 0x4949, fin = v.byteLength - t;
    const u16 = o => v.getUint16(t + o, le), u32 = o => v.getUint32(t + o, le);
    const ifd = o => {
      const e = {};
      if (!o || o + 2 > fin) return e;
      for (let i = 0, n = u16(o); i < n && o + 2 + i * 12 + 12 <= fin; i++) { const b = o + 2 + i * 12; e[u16(b)] = { tipo: u16(b + 2), n: u32(b + 4), b }; }
      return e;
    };
    const TAM = { 1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 7: 1, 9: 4, 10: 8 };
    const bytes = x => { const o = x.n * (TAM[x.tipo] || 1) > 4 ? u32(x.b + 8) : x.b + 8; return new Uint8Array(v.buffer, v.byteOffset + t + o, Math.min(x.n * (TAM[x.tipo] || 1), fin - o)); };
    const texto = x => x ? new TextDecoder("latin1").decode(bytes(x)).replace(/\0+$/, "").trim() : "";
    const racionales = x => { const o = u32(x.b + 8); return Array.from({ length: x.n }, (_, i) => u32(o + 8 * i) / (u32(o + 8 * i + 4) || 1)); };
    const cero = ifd(u32(4)), exif = cero[0x8769] ? ifd(u32(cero[0x8769].b + 8)) : {}, gps = cero[0x8825] ? ifd(u32(cero[0x8825].b + 8)) : {};
    const out = {};
    if (gps[2] && gps[4]) {
      const grados = x => { const [g, m, s] = racionales(x); return g + (m || 0) / 60 + (s || 0) / 3600; };
      out.lat = grados(gps[2]) * (texto(gps[1]) === "S" ? -1 : 1);
      out.lon = grados(gps[4]) * (texto(gps[3]) === "W" ? -1 : 1);
      if (gps[6]) out.alt = racionales(gps[6])[0] * (gps[5] && bytes(gps[5])[0] === 1 ? -1 : 1);
    }
    const fecha = texto(exif[0x9003]) || texto(cero[0x0132]);
    if (/^\d{4}:\d\d:\d\d \d\d:\d\d:\d\d/.test(fecha)) out.fecha = fecha.slice(0, 10).replace(/:/g, "-") + "T" + fecha.slice(11, 19);
    if (exif[0x9286]) {   // UserComment: 8 bytes de juego de caracteres y luego el texto
      const b = bytes(exif[0x9286]), cab = new TextDecoder("latin1").decode(b.subarray(0, 8)), resto = b.subarray(8);
      let c = cab.startsWith("UNICODE") ? new TextDecoder("utf-16be").decode(resto) : new TextDecoder("utf-8").decode(resto);
      if (cab.startsWith("UNICODE") && !/[=;]/.test(c)) c = new TextDecoder("utf-16le").decode(resto);
      out.comentario = c.replace(/\0+$/, "");
      const d = Object.fromEntries(out.comentario.split(";").map(x => x.split("=")).filter(x => x.length >= 2).map(([k, ...r]) => [k.trim(), r.join("=").trim()]));
      if (d.AnalisisYOLO && d.AnalisisYOLO !== "NO_REALIZADO")
        out.abordo = { clase: d.AnalisisYOLO, confianza: d.ConfianzaYOLO != null ? +d.ConfianzaYOLO : null,
                       parches: d.AnalisisParches || null, hojas: d.Hojas != null ? +d.Hojas : null, hojasConSintomas: d.HojasConSintomas != null ? +d.HojasConSintomas : null };
    }
    return out;
  }

  // [{ archivo, ruta }] -> fotos a revisar, cada una con su .json gemelo si lo hay.
  // Si viene la copia limpia de sin_texto/, se usa esa en lugar de la que trae letras encima.
  function juntarVuelo(lista) {
    const dir = r => r.includes("/") ? r.slice(0, r.lastIndexOf("/")) : "";
    const base = r => r.slice(r.lastIndexOf("/") + 1).replace(/\.[^.]+$/, "").toLowerCase();
    const enSinTexto = r => /(^|\/)sin_texto\/[^/]+$/i.test(r);
    const jsons = new Map();
    lista.filter(x => /\.json$/i.test(x.ruta)).forEach(x => jsons.set(`${dir(x.ruta)}|${base(x.ruta)}`, x.archivo));
    const fotos = lista.filter(x => /\.(jpe?g|png|webp)$/i.test(x.ruta) || (x.archivo.type || "").startsWith("image/"));
    const limpias = new Set(fotos.filter(x => enSinTexto(x.ruta)).map(x => base(x.ruta)));
    return fotos.filter(x => enSinTexto(x.ruta) || !limpias.has(base(x.ruta))).map(x => {
      const d = dir(x.ruta), padre = d.replace(/(^|\/)?sin_texto$/i, "");
      return { archivo: x.archivo, nombre: x.ruta.slice(x.ruta.lastIndexOf("/") + 1),
               json: jsons.get(`${d}|${base(x.ruta)}`) || jsons.get(`${padre}|${base(x.ruta)}`) || null };
    }).sort((a, b) => a.nombre.localeCompare(b.nombre, "es", { numeric: true }));
  }

  async function miniatura(archivo, lado = 220) {
    const img = await createImageBitmap(archivo), k = lado / Math.max(img.width, img.height);
    const c = document.createElement("canvas"); c.width = Math.round(img.width * k); c.height = Math.round(img.height * k);
    c.getContext("2d").drawImage(img, 0, 0, c.width, c.height); img.close();
    return URL.createObjectURL(await new Promise(ok => c.toBlob(ok, "image/jpeg", .78)));
  }

  // Todo lo que se sabe de una foto del vuelo: dónde y cuándo, qué ve el modelo aquí y qué vio a bordo.
  async function analizarFotoDeVuelo(item, alProgreso) {
    let exif = {}, gemelo = null;
    try { exif = await leerExif(item.archivo); } catch (e) {}
    if (item.json) { try { gemelo = JSON.parse(await item.json.text()); } catch (e) {} }
    let lat = null, lon = null, alt = null;
    if (gemelo && gemelo.gps_ok !== false && gemelo.lat != null && gemelo.lon != null) { lat = +gemelo.lat; lon = +gemelo.lon; alt = gemelo.alt_rel_m ?? gemelo.alt ?? null; }
    else if (Number.isFinite(exif.lat) && Number.isFinite(exif.lon) && (exif.lat || exif.lon)) { lat = exif.lat; lon = exif.lon; alt = exif.alt ?? null; }
    const r = await diagnosticar(item.archivo, alProgreso), L = lectura(r);
    return { archivo: item.nombre, lat, lon, alt: alt != null ? +alt : null,
             fecha: gemelo?.ts || exif.fecha || new Date(item.archivo.lastModified).toISOString().slice(0, 19),
             clave: L.sinHoja ? "sin_hoja" : r.clase, dudoso: !r.seguro && !L.sinHoja, conf: r.confianza, probs: r.probs, umbral: r.umbral,
             calidad: r.calidad, mejorado: r.mejorado, abordo: exif.abordo || null, mini: await miniatura(item.archivo).catch(() => null), humano: false, revisor: "" };
  }

  // Para el técnico o la estación: el mismo .geojson que abre la página (Abrir otro > mapa)…
  function geojsonDeVuelo(registros, vuelo = "") {
    const r3 = x => x == null ? null : Math.round(x * 1000) / 1000;
    return JSON.stringify({ type: "FeatureCollection", features: registros.filter(f => f.lat != null).map(f => ({ type: "Feature",
      geometry: { type: "Point", coordinates: f.alt != null ? [f.lon, f.lat, r3(f.alt)] : [f.lon, f.lat] },
      properties: { archivo: f.archivo, fecha: f.fecha, vuelo, clave: f.clave, diagnostico: cat(f.clave).nombre, color: cat(f.clave).color,
                    dudoso: f.dudoso, confianza_modelo: r3(f.conf), umbral: f.umbral, fuente: f.mejorado ? "modelo mejorado en el navegador" : "modelo en el navegador",
                    prob_sana: r3(f.probs?.sana), prob_sigatoka: r3(f.probs?.sigatoka), prob_otra_condicion: r3(f.probs?.otra_condicion),
                    a_bordo: f.abordo?.clase ?? null, confianza_a_bordo: f.abordo?.confianza ?? null } })) });
  }
  // …y una tabla con todo, también las fotos sin GPS (se abre en Excel).
  function csvDeVuelo(registros) {
    const q = x => x == null ? "" : /[",\n]/.test(String(x)) ? `"${String(x).replace(/"/g, '""')}"` : String(x);
    const n = x => x == null ? "" : Math.round(x * 100);
    const filas = [["archivo", "fecha", "latitud", "longitud", "altitud_m", "diagnostico", "que_tan_seguro_de_100", "seguro", "sin_hoja",
                    "sana_de_100", "sigatoka_de_100", "otro_problema_de_100", "a_bordo", "a_bordo_de_100", "a_bordo_por_hojas", "hojas_con_sintomas", "modelo"]];
    registros.forEach(f => filas.push([f.archivo, f.fecha, f.lat?.toFixed(7), f.lon?.toFixed(7), f.alt?.toFixed(1), f.dudoso ? "Sin confirmar" : cat(f.clave).nombre,
      n(f.conf), f.dudoso ? "no" : "sí", f.clave === "sin_hoja" ? "sí" : "no", n(f.probs?.sana), n(f.probs?.sigatoka), n(f.probs?.otra_condicion),
      f.abordo?.clase ? cat(f.abordo.clase).nombre : "", n(f.abordo?.confianza), f.abordo?.parches ? cat(f.abordo.parches).nombre : "", f.abordo?.hojasConSintomas ?? "",
      f.mejorado ? "mejorado" : "original"]));
    return "\ufeff" + filas.map(r => r.map(q).join(",")).join("\r\n");
  }

  // ------------------------------------------------------------------ historial de vuelos
  // Cada vuelo analizado se guarda en este navegador (IndexedDB) para ver cómo va el lote con el tiempo.
  // Nada se sube. Solo se guarda lo necesario para las métricas y el mapa (sin fotos).
  const historial = (() => {
    let db = null;
    const abrir = () => (db ??= new Promise((ok, mal) => {
      const r = indexedDB.open("dron-sigatoka-historial", 1);
      r.onupgradeneeded = () => r.result.createObjectStore("vuelos", { keyPath: "id", autoIncrement: true });
      r.onsuccess = () => ok(r.result); r.onerror = () => mal(r.error);
    }));
    async function tx(modo, fn) {
      const t = (await abrir()).transaction("vuelos", modo), r = fn(t.objectStore("vuelos"));
      return new Promise((ok, mal) => { t.oncomplete = () => ok(r?.result); t.onerror = () => mal(t.error); });
    }
    const limpio = f => ({ lat: f.lat ?? null, lon: f.lon ?? null, alt: f.alt ?? null, clave: f.clave || null, dudoso: !!f.dudoso,
                           conf: f.conf ?? null, fecha: f.fecha || "", archivo: f.archivo || "" });
    return {
      async todos() { return (await tx("readonly", s => s.getAll())).sort((a, b) => String(a.fecha).localeCompare(String(b.fecha))); },
      // { nombre, fotos, origen }. Si ya hay uno con la misma firma (mismas fotos), lo reemplaza.
      async guardar({ nombre = "", fotos, origen = "analizado aquí" }) {
        const lista = fotos.map(limpio), fechas = lista.map(f => f.fecha).filter(Boolean).sort();
        const firma = [lista.length, fechas[0], fechas[fechas.length - 1], lista.map(f => f.archivo).sort().slice(0, 3).join("|")].join("·");
        const previo = (await this.todos()).find(v => v.firma === firma);
        const vuelo = { ...(previo ? { id: previo.id } : {}), nombre: nombre || `Vuelo del ${(fechas[0] || "").slice(0, 10)}`, fecha: fechas[0] || new Date().toISOString(),
                        creado: new Date().toISOString(), origen, firma, fotos: lista };
        const id = await tx("readwrite", s => s.put(vuelo));
        return { ...vuelo, id, reemplazado: !!previo };
      },
      borrar: id => tx("readwrite", s => s.delete(id)),
      borrarTodo: () => tx("readwrite", s => s.clear()),
    };
  })();

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
    return `${n} con ${clave === "otra_condicion" ? "otro problema" : cat(clave).nombre}`;
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
  async function crearMapa(el, { borde = "#ffffff", posicionZoom = "topright" } = {}) {
    const L = await leaflet();
    el.style.isolation = "isolate";   // que las capas de Leaflet no pinten encima de la barra de la página
    const tactil = matchMedia("(pointer: coarse)").matches;
    const mapa = L.map(el, { zoomControl: false, attributionControl: true, dragging: !tactil, zoomSnap: .25, scrollWheelZoom: !tactil }).setView([17.99, -92.95], 15);
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
    L.control.zoom({ position: posicionZoom }).addTo(mapa);
    L.control.scale({ imperial: false, position: "bottomleft" }).addTo(mapa);
    const satelite = L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
      { maxZoom: 20, maxNativeZoom: 19, attribution: "Imágenes © Esri" });
    const capa = L.layerGroup().addTo(mapa);
    let fotos = [], vista = "zonas", metros = 20;

    function ficha(f) {
      const c = f.dudoso ? { nombre: "Sin confirmar", color: GRIS } : cat(f.clave);
      const fuente = f.humano ? `Revisada${f.revisor ? " por " + esc(f.revisor) : ""}` : f.conf != null ? `Qué tan seguro: ${Math.round(f.conf * 100)} de 100` : "Sin revisar";
      const hora = f.fecha && f.fecha !== "Ejemplo" ? String(f.fecha).replace("T", " ").slice(0, 19) : "";
      const abordo = f.abordo?.clase ? `A bordo del dron: ${esc(cat(f.abordo.clase).nombre)}${f.abordo.confianza != null ? ` (${Math.round(f.abordo.confianza * 100)} de 100)` : ""}` : "";
      return `<div class="mapa-ficha">${f.mini ? `<img src="${f.mini}" alt="">` : ""}<b><i style="background:${c.color}"></i>${esc(c.nombre)}</b><span>${fuente}${f.archivo ? ` · ${esc(f.archivo)}` : ""}</span>` +
        `${hora ? `<span>${esc(hora)}${f.alt != null ? ` · ${Math.round(f.alt)} m de altura` : ""}</span>` : ""}${abordo ? `<span>${abordo}</span>` : ""}</div>`;
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
        }).bindTooltip(`<b>${esc(cat(z.dominante).nombre)}</b> · ${plural(z.n, "foto", "fotos")} en este cuadro<br>${detalle}`).addTo(capa);
      });
    }
    return {
      mapa,
      // relleno: [arriba, derecha, abajo, izquierda] en px que tapan otros paneles encima del mapa.
      mostrar(lista, { conSatelite = true, relleno = null, encuadrar = true } = {}) {
        fotos = lista;
        mapa.invalidateSize();   // por si el contenedor cambió de tamaño desde que se creó
        if (conSatelite) satelite.addTo(mapa); else satelite.remove();
        el.classList.toggle("sin-fondo", !conSatelite);
        dibujar();
        // Encuadra las zonas completas (no solo los puntos), para que ninguna quede cortada en el borde.
        const zs = zonas(fotos, metros);
        const esquinas = zs.length ? zs.flatMap(z => [[z.i * z.dLat, z.j * z.dLon], [(z.i + 1) * z.dLat, (z.j + 1) * z.dLon]]) : fotos.map(f => [f.lat, f.lon]);
        const [ar, de, ab, iz] = relleno || [20, 20, 20, 20];
        if (encuadrar && esquinas.length) mapa.fitBounds(L.latLngBounds(esquinas), { paddingTopLeft: [iz, ar], paddingBottomRight: [de, ab], maxZoom: 19 });
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
      catch (e) { return avisar.aviso?.({ titulo: "Ese enlace no se ve bien", texto: "Cópialo completo del mensaje que te mandaron; empieza con https://", error: true }); }
      desconectar();
      if (dir.local) return avisar.aviso?.({ titulo: "Ese enlace solo funciona en la WiFi del dron",
        texto: "Conéctate a esa WiFi y abre el enlace directo, o pide el enlace que empieza con https://", local: dir.local, error: true });
      try { localStorage.setItem("dron", texto.trim()); } catch (e) {}
      d = { base: dir.base, temporizador: null, fallas: 0 };
      const host = new URL(dir.base).host;
      avisar.aviso?.({ titulo: "Conectando con el dron…" });
      let est;
      try { est = await (await pedir("/estado")).json(); }
      catch (e) {
        d = null;
        return avisar.aviso?.({ titulo: "El dron no contestó", error: true,
          texto: "Pide a quien lo vuela que revise que esté encendido y que te mande el enlace otra vez." });
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

  // Precarga el modelo (unos 20 MB) cuando la página ya está quieta, para que la primera foto no espere.
  // En la computadora siempre; en el celular solo con WiFi, para no gastar sus datos: ahí empieza a
  // bajar cuando la persona toca para tomar la primera foto.
  function precargar() {
    const red = navigator.connection;
    if (red && (red.saveData || /(^|-)(2g|3g)$/.test(red.effectiveType || ""))) return;
    if (!matchMedia("(pointer: fine)").matches && !/^(wifi|ethernet)$/.test(red?.type || "")) return;
    const ir = () => modelo().catch(() => {});
    if ("requestIdleCallback" in window) requestIdleCallback(ir, { timeout: 2500 }); else setTimeout(ir, 1200);
  }

  return { CAT, cat, GRIS, LECTURAS, esc, plural, pct, icono, qr, SITIO, modelo, modeloListo, diagnosticar, lectura, precargar,
           hablar, callar, puedeHablar, mensaje, cabeza, entrenarCabeza, aciertos, aplicarCabeza, leerExif, juntarVuelo, analizarFotoDeVuelo, geojsonDeVuelo, csvDeVuelo, historial, leaflet, compartir, fotoConResultado, leerGeojson, ejemplo, crearMapa, resumen, zonas, cuantas, dron };
})();
