// Identifica una hoja en el navegador con onnxruntime-web: la foto nunca sale del dispositivo.
// Mismo preprocesado que vision/clasificador.py: estirar a 384x384, RGB, /255, CHW.
// onnxruntime-web vive en vendor/ (lo baja preparar.sh), así que funciona sin internet.
ort.env.wasm.wasmPaths = new URL("vendor/", location.href).href;
ort.env.wasm.numThreads = 1;   // sin aislamiento entre orígenes el navegador no da hilos

let cargando = null;   // promesa del modelo: { sesion, entrada, salida, clases, umbral, lado }
let urlFoto = null;

function cargarModelo() {
  cargando ??= (async () => {
    const meta = await (await fetch("modelo/sigatoka_cls_v1.json")).json();
    const r = await fetch("modelo/sigatoka_cls_v1.onnx");
    if (!r.ok) throw new Error(`No se pudo bajar el modelo (${r.status}).`);
    const sesion = await ort.InferenceSession.create(new Uint8Array(await r.arrayBuffer()), { executionProviders: ["wasm"] });
    return {
      sesion, entrada: sesion.inputNames[0], salida: sesion.outputNames[0],
      clases: meta.classes, umbral: meta.umbral_confianza ?? 0.65, lado: meta.input[meta.input.length - 1],
    };
  })();
  cargando.catch(() => { cargando = null; });   // si falla, el siguiente intento vuelve a bajarlo
  return cargando;
}

async function tensorDe(archivo, lado) {
  const imagen = await createImageBitmap(archivo);   // ya respeta la orientación de la foto
  const lienzo = document.createElement("canvas");
  lienzo.width = lienzo.height = lado;
  const ctx = lienzo.getContext("2d", { willReadFrequently: true });
  ctx.drawImage(imagen, 0, 0, lado, lado);
  imagen.close();
  const { data } = ctx.getImageData(0, 0, lado, lado);
  const n = lado * lado, x = new Float32Array(3 * n);
  for (let i = 0; i < n; i++) {
    x[i] = data[4 * i] / 255;
    x[n + i] = data[4 * i + 1] / 255;
    x[2 * n + i] = data[4 * i + 2] / 255;
  }
  return new ort.Tensor("float32", x, [1, 3, lado, lado]);
}

async function identificar(archivo) {
  if (!archivo) return;
  if (urlFoto) URL.revokeObjectURL(urlFoto);
  urlFoto = URL.createObjectURL(archivo);
  $("foto").src = urlFoto;
  $("foto").classList.remove("oculto");
  $("soltar").classList.add("oculto");
  $("btn-otra").classList.add("oculto");
  $("pie-foto").textContent = archivo.name || "Foto de la cámara";
  $("pie-tiempo").textContent = "";
  pintarAviso("Identificando…");

  try {
    const m = await cargarModelo();
    const inicio = performance.now();
    let p;
    try {
      const salida = await m.sesion.run({ [m.entrada]: await tensorDe(archivo, m.lado) });
      p = Array.from(salida[m.salida].data);
    } catch (e) {
      if (e instanceof DOMException || /decode|image/i.test(e.message)) throw new Error("No se pudo leer esa foto. Prueba con una foto JPG o PNG.");
      throw e;
    }
    const suma = p.reduce((a, b) => a + b, 0);
    if (!(suma >= .99 && suma <= 1.01)) {   // por si el export no trae softmax
      const max = Math.max(...p), e = p.map(v => Math.exp(v - max)), s = e.reduce((a, b) => a + b, 0);
      p = e.map(v => v / s);
    }
    const top = p.indexOf(Math.max(...p));
    pintarLectura({ clase: m.clases[top], confianza: p[top], probs: Object.fromEntries(m.clases.map((c, i) => [c, p[i]])) }, m.umbral);
    $("pie-tiempo").textContent = `identificada en tu navegador · ${Math.round(performance.now() - inicio)} ms`;
  } catch (e) {
    pintarAviso("Sin lectura", e.message || "No se pudo identificar la foto.", true);
  }
  $("btn-otra").classList.remove("oculto");
}

for (const id of ["archivo", "captura", "archivo-otra"]) {
  $(id).onchange = e => { identificar(e.target.files[0]); e.target.value = ""; };
}

const visor = $("visor");
visor.addEventListener("dragover", e => { e.preventDefault(); $("soltar").classList.add("encima"); });
visor.addEventListener("dragleave", () => $("soltar").classList.remove("encima"));
visor.addEventListener("drop", e => {
  e.preventDefault();
  $("soltar").classList.remove("encima");
  const archivo = [...e.dataTransfer.files].find(f => f.type.startsWith("image/"));
  if (archivo) identificar(archivo);
});

// El modelo se baja de una vez para que la primera foto no espere.
cargarModelo()
  .then(() => { if ($("pie-tiempo").textContent === "Cargando el modelo…") $("pie-tiempo").textContent = "Modelo listo"; })
  .catch(e => { $("pie-tiempo").textContent = "No se pudo cargar el modelo: " + e.message; });
