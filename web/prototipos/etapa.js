// Controla el escenario (la historia ilustrada, el mapa del lote o el dron en vivo) y el panel de
// la hoja. Cada mundo dibuja su propia historia; esto conecta los botones con el motor.
"use strict";
const Etapa = (() => {
  const M = Motor, P = Piezas;
  const $ = id => document.getElementById(id);

  function iniciar({ alModo = () => {}, relleno = () => [70, 290, 90, 24], compacto = true, posicionZoom = "topleft" } = {}) {
    let modo = "historia", mapa = null, hayLote = false;
    document.querySelectorAll("[data-ico]").forEach(el => { el.innerHTML = M.icono(el.dataset.ico); });
    $("qr") && ($("qr").innerHTML = M.qr());

    // ---------------------------------------- modos del escenario
    function ir(nuevo) {
      modo = nuevo;
      $("etapa").dataset.modo = nuevo;
      document.querySelectorAll("[data-modo]").forEach(el => el.classList.toggle("oculto", el.dataset.modo !== nuevo));
      document.querySelectorAll("[data-solo]").forEach(el => el.classList.toggle("oculto", !el.dataset.solo.split(" ").includes(nuevo)));
      if (nuevo === "lote") { $("vacio").classList.toggle("oculto", hayLote); mapa?.invalidar(); }
      if (nuevo !== "dron" && dron.conectado()) dron.desconectar();
      alModo(nuevo);
      if (matchMedia("(max-width: 900px)").matches && nuevo !== "historia") $("etapa").scrollIntoView({ block: "start", behavior: "smooth" });
    }
    document.addEventListener("click", e => {
      const b = e.target.closest("[data-ir]");
      if (b) { ir(b.dataset.ir); if (b.dataset.ir === "lote" && b.dataset.ejemplo !== undefined) verLote(M.ejemplo(), true); }
    });

    // ---------------------------------------- la hoja
    let urlFoto = null;
    document.querySelectorAll("[data-camara]").forEach(b => b.addEventListener("click", () => $("in-camara").click()));
    document.querySelectorAll("[data-galeria]").forEach(b => b.addEventListener("click", () => $("in-galeria").click()));
    ["in-camara", "in-galeria"].forEach(id => $(id).onchange = e => { revisar(e.target.files[0]); e.target.value = ""; });
    P.soltarFoto($("zona-foto"), revisar);
    $("voz").checked = M.vozActiva.get();
    $("voz").onchange = e => { M.vozActiva.set(e.target.checked); if (!e.target.checked) M.callar(); };
    async function revisar(archivo) {
      if (!archivo) return;
      if (urlFoto) URL.revokeObjectURL(urlFoto);
      urlFoto = URL.createObjectURL(archivo);
      $("foto").src = urlFoto; $("foto").classList.remove("oculto");
      document.querySelectorAll("[data-sin-foto]").forEach(el => el.classList.add("oculto"));
      await P.revisar(archivo, $("salida"), { otra: () => $("in-camara").click(), compacto });
      if (matchMedia("(max-width: 900px)").matches) $("salida").scrollIntoView({ block: "nearest", behavior: "smooth" });
    }

    // ---------------------------------------- lote
    async function verLote(fotos, ejemplo) {
      hayLote = true;
      $("vacio").classList.add("oculto");
      mapa ??= await M.crearMapa($("mapa"), { posicionZoom });
      const res = mapa.mostrar(fotos, { conSatelite: !ejemplo, relleno: relleno() });
      $("etiqueta-ejemplo").classList.toggle("oculto", !ejemplo);
      $("leyenda").innerHTML = P.leyenda(res);
      $("leyenda-flota").classList.remove("oculto");
    }
    document.querySelectorAll("[data-abrir-mapa]").forEach(b => b.addEventListener("click", () => $("in-mapa").click()));
    document.querySelectorAll("[data-ejemplo-mapa]").forEach(b => b.addEventListener("click", () => verLote(M.ejemplo(), true)));
    $("in-mapa").onchange = async e => {
      const f = e.target.files[0]; e.target.value = "";
      if (!f) return;
      ir("lote");
      try { await verLote(await P.leerArchivoMapa(f), false); $("error-mapa").classList.add("oculto"); }
      catch (err) { $("error-mapa").textContent = err.message; $("error-mapa").classList.remove("oculto"); }
    };
    document.querySelectorAll("[data-vista]").forEach(b => b.onclick = () => {
      document.querySelectorAll("[data-vista]").forEach(x => x.setAttribute("aria-pressed", String(x === b)));
      mapa?.vista(b.dataset.vista);
    });

    // ---------------------------------------- dron
    const dron = M.dron({
      aviso(a) { $("aviso-dron").innerHTML = P.avisoDron(a); },
      conectado({ video }) {
        $("video").src = video; $("aviso-dron").innerHTML = "";
        $("visor").classList.remove("oculto"); $("conectar").classList.add("oculto");
      },
      estado(e) {
        const L = e.lectura ? M.lectura(e.lectura) : null;
        $("lectura-dron").style.setProperty("--c", L ? L.color : "inherit");
        $("lectura-dron").innerHTML = e.sinModelo ? "Sin modelo en el dron" : L ? `<b>${M.esc(L.titulo)}</b><span class="nota">${M.esc(P.gps(e.gps))}</span>` : `<span class="estado"><span class="giro"></span>Esperando…</span>`;
      },
      desconectado() { $("video").removeAttribute("src"); $("visor").classList.add("oculto"); $("conectar").classList.remove("oculto"); },
    });
    $("dir-dron").value = dron.sugerida;
    $("form-dron").onsubmit = e => { e.preventDefault(); if ($("dir-dron").value.trim()) dron.conectar($("dir-dron").value); };
    $("b-desconectar").onclick = () => dron.desconectar();
    $("video").onerror = () => { if (dron.conectado()) setTimeout(() => { if (dron.conectado()) $("video").src = dron.video(); }, 2000); };
    if (dron.inicial) { ir("dron"); dron.conectar(dron.inicial); }

    ir("historia");
    M.precargar();
    return { ir, modo: () => modo };
  }
  return { iniciar };
})();
