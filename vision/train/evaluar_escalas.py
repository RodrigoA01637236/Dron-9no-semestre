"""Evalúa el tamaño del cuadro: un solo tamaño (384 px, lado_min_rel 0.3) contra dos tamaños
(el chico más uno de escala_gruesa del lado corto, con la regla de vision/parches.py:elegir_escala).

Por qué: en fotos de cerca a la resolución del dron (1920 x 1200), el cuadro de 384 px ve un
pedazo de hoja muy ampliado, que el modelo casi no vio al entrenar, y lo lee como "otro problema".

Cada foto de prueba se revisa de tres formas:
- tal cual: la foto del dataset como viene (224-1000 px);
- a 1920 px: la misma foto llevada a 1920 px de ancho, como la ZED X Mini (de cerca);
- mosaico: seis fotos de la misma clase y fuente en un lienzo de 1920 x 1200 (hojas chicas en
  la foto, como una toma más abierta).
Y, si se da --aereas, fotos aéreas de una plantación con Sigatoka (sin etiqueta por foto: se
cuenta cuántas salen Sigatoka, para ver que el cuadro grande no pierda las manchas chicas).

Uso (desde la raíz del repo):
    python vision/train/evaluar_escalas.py --test data/dataset_v2/test --excluir-fuentes v1_publico
    python vision/train/evaluar_escalas.py --test data/dataset_v2/test --aereas carpeta_aereas --gruesa 0.5
Sale vision/models/escalas_evaluacion.md (y .json).
"""
import argparse
import json
import random
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import cv2
import numpy as np

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from vision import parches as P  # noqa: E402
from vision.clasificador import Clasificador, leer_imagen  # noqa: E402

EXT = {".jpg", ".jpeg", ".png", ".webp"}


def a_1920(img: np.ndarray) -> np.ndarray:
    h, w = img.shape[:2]
    k = 1920 / w
    return cv2.resize(img, (1920, int(round(h * k))), interpolation=cv2.INTER_AREA if k < 1 else cv2.INTER_CUBIC)


def cubrir(img: np.ndarray, w: int, h: int) -> np.ndarray:
    ih, iw = img.shape[:2]
    k = max(w / iw, h / ih)
    z = cv2.resize(img, (max(w, round(iw * k)), max(h, round(ih * k))),
                   interpolation=cv2.INTER_AREA if k < 1 else cv2.INTER_CUBIC)
    y0, x0 = (z.shape[0] - h) // 2, (z.shape[1] - w) // 2
    return z[y0:y0 + h, x0:x0 + w]


def mosaico(fotos: list[np.ndarray]) -> np.ndarray:
    lienzo = np.zeros((1200, 1920, 3), np.uint8)
    for i in range(6):
        y, x = (i // 3) * 600, (i % 3) * 640
        lienzo[y:y + 600, x:x + 640] = cubrir(fotos[i % len(fotos)], 640, 600)
    return lienzo


def dos_lecturas(C: Clasificador, img: np.ndarray, gruesa: float):
    """(veredicto con el cuadro chico, veredicto con el grande o None si mide lo mismo)."""
    cfg = C.cfg_parches
    m = P.mascara_hoja(img)
    rf = C._por_cuadros(img, cfg, m)[0]
    cg = {**cfg, "lado_min_rel": gruesa}
    alto, ancho = img.shape[:2]
    rg = C._por_cuadros(img, cg, m)[0] if P.lado_cuadro(alto, ancho, cg) > P.lado_cuadro(alto, ancho, cfg) else None
    return rf, rg


def final(r: dict | None, umbral: float) -> str:
    if r is None:
        return "sin_cuadros"
    return r["clase"] if (r["clase"] == "sin_hoja" or r["confianza"] >= umbral) else "no_seguro"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--test", type=Path, default=RAIZ / "data/dataset_v2/test", help="carpeta con una subcarpeta por clase")
    ap.add_argument("--modelo", type=Path, default=RAIZ / "vision/models/sigatoka_cls_v2.onnx")
    ap.add_argument("--excluir-fuentes", nargs="*", default=[])
    ap.add_argument("--aereas", type=Path, default=None, help="fotos aéreas de una plantación con Sigatoka")
    ap.add_argument("--gruesa", type=float, default=0.5, help="escala_gruesa a evaluar")
    ap.add_argument("--salida", type=Path, default=RAIZ / "vision/models/escalas_evaluacion")
    args = ap.parse_args()

    C = Clasificador(args.modelo)
    U, cfg, cl = C.umbral, C.cfg_parches, C.clases
    fotos = []
    for carpeta in sorted(p for p in args.test.iterdir() if p.is_dir() and p.name in cl):
        for f in sorted(carpeta.iterdir()):
            fuente = f.name.split("__")[0] if "__" in f.name else carpeta.name
            if f.suffix.lower() in EXT and fuente not in args.excluir_fuentes:
                fotos.append((f, carpeta.name, fuente))
    grupos = defaultdict(list)
    for f, c, s in fotos:
        grupos[(c, s)].append(f)
    print(f"{len(fotos)} fotos de prueba", flush=True)

    conf = {b: {r: defaultdict(Counter) for r in ("un_tamano", "dos_tamanos")} for b in ("tal_cual", "a_1920", "mosaico")}
    usos = Counter()
    for n, (f, clase, fuente) in enumerate(fotos, 1):
        img = leer_imagen(f)
        if img is None:
            continue
        otras = [o for o in grupos[(clase, fuente)] if o != f]
        random.Random(str(f.name)).shuffle(otras)
        vecinas = [img] + [x for x in (leer_imagen(o) for o in otras[:5]) if x is not None]
        for base, im in (("tal_cual", img), ("a_1920", a_1920(img)), ("mosaico", mosaico(vecinas))):
            rf, rg = dos_lecturas(C, im, args.gruesa)
            escala = P.elegir_escala(rf, rg, cfg, U) if rf is not None and rg is not None else "fina"
            usos[(base, escala)] += 1
            conf[base]["un_tamano"][clase][final(rf, U)] += 1
            conf[base]["dos_tamanos"][clase][final(rg if escala == "gruesa" else rf, U)] += 1
        if n % 100 == 0:
            print(n, flush=True)

    aereas = None
    if args.aereas:
        cuenta = {"un_tamano": Counter(), "dos_tamanos": Counter()}
        for f in sorted(p for p in args.aereas.rglob("*") if p.suffix.lower() in EXT):
            img = leer_imagen(f)
            if img is None:
                continue
            rf, rg = dos_lecturas(C, img, args.gruesa)
            escala = P.elegir_escala(rf, rg, cfg, U) if rf is not None and rg is not None else "fina"
            cuenta["un_tamano"][final(rf, U)] += 1
            cuenta["dos_tamanos"][final(rg if escala == "gruesa" else rf, U)] += 1
        aereas = {k: dict(v) for k, v in cuenta.items()}

    def resumen(m):
        tot = sum(sum(v.values()) for v in m.values())
        ok = sum(m[c][c] for c in m)
        return {"fotos": tot, "exactitud": round(ok / max(1, tot), 4),
                "recall": {c: round(m[c][c] / max(1, sum(m[c].values())), 4) for c in cl if m.get(c)},
                "confusion": {c: dict(m[c]) for c in cl if m.get(c)}}

    salida = {"fecha": date.today().isoformat(), "modelo": args.modelo.name, "umbral": U, "gruesa": args.gruesa,
              "fuentes_excluidas": args.excluir_fuentes, "fotos": len(fotos),
              "resultados": {b: {r: resumen(conf[b][r]) for r in conf[b]} for b in conf},
              "escala_usada": {f"{b}|{e}": n for (b, e), n in usos.items()}, "aereas": aereas}
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    args.salida.with_suffix(".json").write_text(json.dumps(salida, indent=1, ensure_ascii=False), encoding="utf-8")

    nombres = {"tal_cual": "Fotos tal cual (224-1000 px)", "a_1920": "Las mismas fotos a 1920 px (de cerca, como el dron)",
               "mosaico": "Seis fotos por lienzo de 1920 x 1200 (hojas chicas, toma abierta)"}
    L = [f"# Tamaño del cuadro ({args.modelo.name})", "",
         f"Generado por `vision/train/evaluar_escalas.py` el {salida['fecha']}. Un tamaño: cuadro de 384 px "
         f"(lado_min_rel {cfg['lado_min_rel']}). Dos tamaños: además uno de {args.gruesa:g} del lado corto, con la regla "
         "de `elegir_escala` (vision/parches.py): manda el chico si encuentra Sigatoka con seguridad y el grande no dice "
         "\"sin hoja\"; si no, manda el grande. Umbral de seguridad " f"{U:g}.", "",
         f"- Fotos de prueba: {len(fotos)} (carpeta `{args.test.name}`), fuentes excluidas: {', '.join(args.excluir_fuentes) or 'ninguna'}.", ""]
    for b in ("tal_cual", "a_1920", "mosaico"):
        L += [f"## {nombres[b]}", "", "| Regla | Exactitud | " + " | ".join(f"Acierto {c}" for c in cl) + " |",
              "|---|---|" + "---|" * len(cl)]
        for r, etiqueta in (("un_tamano", "Un tamaño (antes)"), ("dos_tamanos", "Dos tamaños (ahora)")):
            s = salida["resultados"][b][r]
            L.append(f"| {etiqueta} | {s['exactitud']:.1%} | " + " | ".join(f"{s['recall'].get(c, 0):.1%}" for c in cl) + " |")
        a = salida["resultados"][b]["un_tamano"]["confusion"].get("sigatoka", {})
        d = salida["resultados"][b]["dos_tamanos"]["confusion"].get("sigatoka", {})
        L += ["", f"Fotos de Sigatoka: antes {a}; ahora {d}.", ""]
    if aereas:
        n = sum(aereas["un_tamano"].values())
        L += ["## Fotos aéreas con Sigatoka (sin etiqueta por foto)", "",
              f"{n} fotos. Salen Sigatoka: antes {aereas['un_tamano'].get('sigatoka', 0)}, "
              f"ahora {aereas['dos_tamanos'].get('sigatoka', 0)}.", ""]
    args.salida.with_suffix(".md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
