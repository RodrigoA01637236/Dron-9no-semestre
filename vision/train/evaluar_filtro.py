"""Evalúa el filtro "¿esto es hoja de plátano?" (vision/rasgos.py) sin tocar el modelo.

Responde dos preguntas, para la regla por cuadros (fotos) y para la de foto completa (video):
1. ¿Cuántas fotos de hoja vuelve "sin hoja"? Se deja fuera una fuente de fotos de hoja a la vez:
   la sonda se entrena con las demás y se prueba con la que quedó fuera. Imita fotos de un
   celular o de una plantación que el filtro nunca vio. Una foto "cambia" si sin filtro el
   modelo veía hoja de plátano y con el filtro ya no.
2. ¿Cuántas fotos de objetos sigue aceptando como hoja? Con una sonda entrenada con todas las
   fuentes de hoja y con --objetos, sobre fotos de --objetos-prueba que no se usaron para
   entrenar. "Aceptada" = el veredicto es una clase de hoja con confianza >= el umbral del modelo.

También compara la regla de la primera versión (quitar cuadro por cuadro, umbral distinto según
el color del cuadro), que quitaba los cuadros con manchas cafés.

La fuente de cada foto de hoja es lo que va antes de "__" en su nombre (así nombra las fotos
preparar_datos.py) o, si no tiene, el nombre de la carpeta que se pasó en --hojas.
--objetos y --objetos-prueba agregan a cada foto un acercamiento simulado (como filtro_hoja.py);
--objetos-tal-cual se usan solo como están. Los rasgos se guardan en --cache.

Uso (desde la raíz del repo):
    python vision/train/evaluar_filtro.py --hojas data/dataset_v2 \\
        --objetos data/raw/objetos_coco/entrenar --objetos-prueba data/raw/objetos_coco/prueba

Escribe vision/models/filtro_hoja_evaluacion.md y .json (los usa figura_filtro.py).
"""
import argparse
import json
import random
import sys
from collections import Counter
from datetime import date
from pathlib import Path

import numpy as np

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from vision import parches as P  # noqa: E402
from vision.clasificador import _softmax, leer_imagen  # noqa: E402
from vision.train.filtro_hoja import Rasgos, acercamiento, con_cache, entrenar, fotos, fuente_de  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--modelo", type=Path, default=RAIZ / "vision/models/sigatoka_cls_v2.onnx")
    ap.add_argument("--hojas", type=Path, nargs="+", required=True)
    ap.add_argument("--objetos", type=Path, nargs="+", required=True, help="objetos para entrenar la sonda")
    ap.add_argument("--objetos-prueba", type=Path, nargs="*", default=[], help="objetos solo para medir")
    ap.add_argument("--objetos-tal-cual", type=Path, nargs="*", default=[], help="objetos solo para medir, sin acercamiento")
    ap.add_argument("--excluir-fuentes", default="", help="fuentes a dejar fuera, separadas por coma")
    ap.add_argument("--umbrales", default="-6,-5,-4,-3,-2.5,-2")
    ap.add_argument("--elegido", type=float, default=-3.0)
    ap.add_argument("--lam", type=float, default=1e-2)
    ap.add_argument("--cache", type=Path, default=RAIZ / "runs/evaluar_filtro_cache")
    ap.add_argument("--salida", type=Path, default=RAIZ / "vision/models/filtro_hoja_evaluacion.md")
    ap.add_argument("--seed", type=int, default=3)
    args = ap.parse_args()
    umbrales = [float(u) for u in args.umbrales.split(",")]
    args.cache.mkdir(parents=True, exist_ok=True)

    R = Rasgos(args.modelo)
    cl, umbral, T = R.c.clases, R.c.umbral, R.c.temperatura
    ks = cl.index("sin_hoja")
    saltar = set(R.cfg.get("ignorar") or [])

    def calibrar(p):
        return _softmax(np.log(np.clip(p.astype(np.float64), 1e-12, 1.0)) / T)

    def veredicto(probs):
        r = P.agregar(probs, cl, R.cfg, umbral)
        return r["clase"] if r["confianza"] >= umbral or r["clase"] == "sin_hoja" else "no_seguro"

    print("Leyendo fotos (los rasgos quedan en la cache)...", flush=True)
    hojas = []
    excluir = {x.strip() for x in args.excluir_fuentes.split(",") if x.strip()}
    for carpeta in args.hojas:
        for f in fotos([carpeta], saltar):
            if fuente_de(f, carpeta) in excluir:
                continue
            d = con_cache(R, args.cache, f, "tal", lambda f=f: leer_imagen(f))
            if d is not None:
                d.update(fuente=fuente_de(f, carpeta), nombre=f.name)
                hojas.append(d)
        print(f"  {carpeta}: {len(hojas)} fotos de hoja en total", flush=True)

    rnd = random.Random(args.seed)

    def objetos(carpetas, con_acerc):
        out = []
        for f in fotos(carpetas, set()):
            img = None

            def leer(f=f):
                nonlocal img
                img = leer_imagen(f)
                return img
            d = con_cache(R, args.cache, f, "tal", leer)
            if d is not None:
                out.append(d)
            if con_acerc:
                # El acercamiento se genera siempre (aunque esté en cache) para no mover la semilla.
                base = img if img is not None else leer_imagen(f)
                if base is None or base.ndim != 3:
                    continue
                cerca = acercamiento(base, rnd)
                d = con_cache(R, args.cache, f, f"cerca{args.seed}", lambda c=cerca: c)
                if d is not None:
                    out.append(d)
        return out

    O_tr = objetos(args.objetos, True)
    O_te = objetos(args.objetos_prueba, True) + objetos(args.objetos_tal_cual, False)
    fuentes = sorted({d["fuente"] for d in hojas})
    print(f"{len(hojas)} fotos de hoja de {len(fuentes)} fuentes; {len(O_tr)} imágenes de objetos para "
          f"entrenar y {len(O_te)} para medir", flush=True)

    for d in hojas + O_te:
        d["pc"] = calibrar(d["p"])
        d["hoja"] = d["p"].argmax(1) != ks
        d["base"] = veredicto(d["pc"])
        pi = calibrar(d["pi"][None])[0]
        d["base_i"] = cl[int(pi.argmax())] if pi.max() >= umbral or int(pi.argmax()) == ks else "no_seguro"
        d["hoja_i"] = int(d["pi"].argmax()) != ks

    def datos(hs, os_, imagen):
        if imagen:
            Xp = np.stack([d["fi"] for d in hs if d["hoja_i"]])
            Xn = np.stack([d["fi"] for d in os_])
        else:
            Xp = np.concatenate([d["f"][d["hoja"]] for d in hs])
            Xn = np.concatenate([d["f"] for d in os_])
        return np.concatenate([Xp, Xn]), np.concatenate([np.ones(len(Xp), np.float32), np.zeros(len(Xn), np.float32)])

    # ---- reglas
    def foto_cambia(d, s, t):            # regla final: la foto entera, si ningún cuadro de hoja pasa
        return bool(d["hoja"].any()) and not bool((d["hoja"] & (s >= t)).any())

    def foto_acepta(d, s, t):
        return d["base"] not in ("sin_hoja", "no_seguro") and bool((d["hoja"] & (s >= t)).any())

    def cuadro_veredicto(d, s, u_verde, u, verde_min=0.2):   # primera versión: cuadro por cuadro
        quita = s < np.where(d["col"] >= verde_min, u_verde, u)
        q = d["pc"].copy()
        q[quita] = 0.0
        q[quita, ks] = 1.0
        return veredicto(q)

    def imagen_cambia(d, s, t):
        return d["hoja_i"] and d["base_i"] != "sin_hoja" and s < t

    def imagen_acepta(d, s, t):
        return d["base_i"] not in ("sin_hoja", "no_seguro") and s >= t

    # ---- 1. dejando fuera una fuente
    print("Dejando fuera una fuente a la vez...", flush=True)
    loo = {"foto": {u: Counter() for u in umbrales}, "cuadro_primera": Counter(), "imagen": {u: Counter() for u in umbrales}}
    for s_fuera in fuentes:
        dentro = [d for d in hojas if d["fuente"] != s_fuera]
        fuera = [d for d in hojas if d["fuente"] == s_fuera]
        w, b = entrenar(*datos(dentro, O_tr, False), args.lam)
        wi, bi = entrenar(*datos(dentro, O_tr, True), args.lam)
        for d in fuera:
            s = d["f"] @ w + b
            si = float(d["fi"] @ wi + bi)
            for u in umbrales:
                loo["foto"][u][s_fuera] += foto_cambia(d, s, u)
                loo["imagen"][u][s_fuera] += imagen_cambia(d, si, u)
            loo["cuadro_primera"][s_fuera] += cuadro_veredicto(d, s, -4.0, 0.0) != d["base"]
        print(f"  sin {s_fuera} ({len(fuera)} fotos): cambian {loo['foto'][args.elegido][s_fuera]} (fotos, {args.elegido}), "
              f"{loo['imagen'][args.elegido][s_fuera]} (video)", flush=True)

    # ---- 2. objetos que no se usaron para entrenar
    w, b = entrenar(*datos(hojas, O_tr, False), args.lam)
    wi, bi = entrenar(*datos(hojas, O_tr, True), args.lam)
    obj = {"sin_filtro": sum(d["base"] not in ("sin_hoja", "no_seguro") for d in O_te),
           "sin_filtro_video": sum(d["base_i"] not in ("sin_hoja", "no_seguro") for d in O_te),
           "foto": {}, "video": {}, "poco_verde": {}}
    poco = [d for d in O_te if float(d["col"].mean()) < 0.15 and d["base"] not in ("sin_hoja", "no_seguro")]
    obj["poco_verde_sin_filtro"] = len(poco)
    for u in umbrales:
        obj["foto"][u] = sum(foto_acepta(d, d["f"] @ w + b, u) for d in O_te)
        obj["video"][u] = sum(imagen_acepta(d, float(d["fi"] @ wi + bi), u) for d in O_te)
        obj["poco_verde"][u] = sum(foto_acepta(d, d["f"] @ w + b, u) for d in poco)
    obj["cuadro_primera"] = sum(cuadro_veredicto(d, d["f"] @ w + b, -4.0, 0.0) not in ("sin_hoja", "no_seguro") for d in O_te)

    res = {
        "fecha": date.today().isoformat(), "modelo": args.modelo.name, "elegido": args.elegido,
        "fotos_hoja": len(hojas), "excluidas": sorted(excluir), "fuentes": {s: sum(d["fuente"] == s for d in hojas) for s in fuentes},
        "objetos_entrenar": len(O_tr), "objetos_prueba": len(O_te),
        "loo_foto": {str(u): dict(loo["foto"][u]) | {"total": sum(loo["foto"][u].values())} for u in umbrales},
        "loo_imagen": {str(u): dict(loo["imagen"][u]) | {"total": sum(loo["imagen"][u].values())} for u in umbrales},
        "loo_cuadro_primera": dict(loo["cuadro_primera"]) | {"total": sum(loo["cuadro_primera"].values())},
        "objetos": {k: ({str(u): x for u, x in v.items()} if isinstance(v, dict) else v) for k, v in obj.items()},
    }
    args.salida.with_suffix(".json").write_text(json.dumps(res, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # ---- reporte
    L = [f"# Evaluación del filtro de hoja ({args.modelo.name})", "",
         f"Generado por `vision/train/evaluar_filtro.py` el {res['fecha']}. No cambia el modelo: entrena sondas "
         "de prueba con la misma receta que `filtro_hoja.py` (regresión logística, λ = "
         f"{args.lam}).", "",
         f"- Fotos de hoja: {len(hojas)} de {len(fuentes)} fuentes: "
         + ", ".join(f"{s} {n}" for s, n in res["fuentes"].items()) + ".",
         (f"- Fuentes excluidas: {', '.join(sorted(excluir))}.\n" if excluir else "")
         + f"- Objetos para entrenar la sonda: {len(O_tr)} imágenes. Objetos solo para medir: {len(O_te)} "
         "(nunca se usaron para entrenar).", "",
         "## Fotos de hoja que el filtro vuelve \"sin hoja\" (dejando fuera una fuente a la vez)", "",
         "Regla final (fotos por cuadros): la foto cuenta como sin hoja solo si ningún cuadro de hoja pasa el umbral.", "",
         "| Umbral | Fotos (por cuadros) | Video (foto completa) |", "|---|---|---|"]
    for u in umbrales:
        marca = " (elegido)" if u == args.elegido else ""
        L.append(f"| {u:g}{marca} | {res['loo_foto'][str(u)]['total']} de {len(hojas)} | "
                 f"{res['loo_imagen'][str(u)]['total']} de {len(hojas)} |")
    L += ["", f"Primera versión (cuadro por cuadro, umbral -4 si el cuadro tiene color de hoja y 0 si no), "
          f"reentrenada con las mismas fuentes: cambia el veredicto de {res['loo_cuadro_primera']['total']} de {len(hojas)} fotos.", "",
          f"Por fuente, con el umbral elegido ({args.elegido:g}):", "", "| Fuente | Fotos | Cambian (fotos) | Cambian (video) |",
          "|---|---|---|---|"]
    for s in fuentes:
        L.append(f"| {s} | {res['fuentes'][s]} | {res['loo_foto'][str(args.elegido)].get(s, 0)} | {res['loo_imagen'][str(args.elegido)].get(s, 0)} |")
    L += ["", "## Objetos que el modelo sigue aceptando como hoja", "",
          f"Sin filtro: {obj['sin_filtro']} de {len(O_te)} por cuadros y {obj['sin_filtro_video']} de {len(O_te)} con la foto completa. "
          f"De las {obj['poco_verde_sin_filtro']} aceptadas por cuadros con poco color de hoja (menos de 15 %), cuántas quedan:", "",
          "| Umbral | Fotos (por cuadros) | De ellas, con poco verde | Video (foto completa) |", "|---|---|---|---|"]
    for u in umbrales:
        marca = " (elegido)" if u == args.elegido else ""
        L.append(f"| {u:g}{marca} | {obj['foto'][u]} | {obj['poco_verde'][u]} | {obj['video'][u]} |")
    L += ["", f"Primera versión (cuadro por cuadro): {obj['cuadro_primera']} de {len(O_te)}.", ""]
    args.salida.write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    print(f"\nGuardado en {args.salida} y {args.salida.with_suffix('.json')}")


if __name__ == "__main__":
    main()
