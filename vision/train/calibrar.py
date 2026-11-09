"""Calibra, evalúa y empaqueta el modelo por parches (sigatoka_cls_v2).

1. Temperatura: ajusta T en los parches de val para que "80 % seguro" signifique acertar
   ~80 % de las veces (Guo et al., ICML 2017). Sin esto el umbral no significa nada.
2. Regla de la foto: prueba umbral (0.50-0.95) y min_parches (1-3) en las FOTOS de val y
   se queda con la que cubre más fotos con exactitud >= --objetivo entre las que sí
   diagnostica (el resto va a revisión humana).
3. Prueba final en las FOTOS de test (no en parches): v1 con la foto completa contra v2
   con la foto completa y v2 por parches, por clase y por fuente. Además, cada carpeta
   test_<externo> (dron de Colombia, fotos de campo) y, si trae cajas, cuántas lesiones
   marcadas caen en un parche que el modelo marcó.
4. Empaqueta: copia el ONNX a --salida y escribe el JSON (modo_defecto "parches",
   temperatura, umbral, configuración de parches y métricas) y un reporte .md al lado.

Uso (desde la raíz del repo, con el venv activo):
    python vision/train/calibrar.py --onnx runs/classify/parches_v2/weights/best.onnx
    python vision/train/calibrar.py --onnx ... --limite 200     # prueba rápida

Ver vision/GUIA-PARCHES.md, paso 5.
"""
import argparse
import ast
import json
import shutil
import sys
import time
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import cv2
import numpy as np

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from vision import parches as P  # noqa: E402
from vision.clasificador import Clasificador, leer_imagen  # noqa: E402

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}


def fotos_de(carpeta: Path, clases: list[str], limite: int, rng) -> list[tuple[Path, str]]:
    salida = []
    for c in clases:
        lista = sorted(p for p in (carpeta / c).glob("*") if p.suffix.lower() in IMG_EXTS)
        if limite and len(lista) > limite:
            lista = [lista[i] for i in sorted(rng.choice(len(lista), limite, replace=False))]
        salida += [(p, c) for p in lista]
    return salida


def preparar_meta(onnx: Path) -> dict:
    """JSON de train_cls.py al lado del ONNX; si no está, las clases salen del ONNX."""
    ruta = onnx.with_suffix(".json")
    if ruta.exists():
        return json.loads(ruta.read_text(encoding="utf-8"))
    import onnxruntime as ort
    s = ort.InferenceSession(str(onnx), providers=["CPUExecutionProvider"])
    nombres = ast.literal_eval(s.get_modelmeta().custom_metadata_map["names"])
    lado = s.get_inputs()[0].shape[-1]
    meta = {"model": onnx.name, "input": [1, 3, int(lado), int(lado)],
            "classes": [nombres[i] for i in sorted(nombres)], "umbral_confianza": 0.65}
    ruta.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
    return meta


# ------------------------------------------------------------------ métricas

def nll(p: np.ndarray, y: np.ndarray, t: float) -> float:
    z = np.log(np.clip(p, 1e-12, 1)) / t
    z -= z.max(axis=1, keepdims=True)
    logp = z - np.log(np.exp(z).sum(axis=1, keepdims=True))
    return float(-logp[np.arange(len(y)), y].mean())


def con_temperatura(p: np.ndarray, t: float) -> np.ndarray:
    z = np.log(np.clip(p, 1e-12, 1)) / t
    e = np.exp(z - z.max(axis=1, keepdims=True))
    return e / e.sum(axis=1, keepdims=True)


def ece(p: np.ndarray, y: np.ndarray, bins: int = 10) -> float:
    conf, pred = p.max(axis=1), p.argmax(axis=1)
    total = 0.0
    for a in range(bins):
        m = (conf > a / bins) & (conf <= (a + 1) / bins)
        if m.any():
            total += m.mean() * abs((pred[m] == y[m]).mean() - conf[m].mean())
    return float(total)


def resumen(etiquetas: list[str], preds: list[str], confs: list[float], umbral: float, clases: list[str]) -> dict:
    y, yp, cf = np.array(etiquetas), np.array(preds), np.array(confs)
    if len(y) == 0:
        return {"n": 0}
    f1s, recall = {}, {}
    for c in clases:
        tp = ((yp == c) & (y == c)).sum()
        if (y == c).sum():
            recall[c] = float(tp / (y == c).sum())
        prec = tp / max(1, (yp == c).sum())
        rec = tp / max(1, (y == c).sum())
        if (y == c).sum():
            f1s[c] = float(2 * prec * rec / max(1e-9, prec + rec))
    diag = cf >= umbral
    return {
        "n": int(len(y)),
        "exactitud": float((y == yp).mean()),
        "f1_macro": float(np.mean(list(f1s.values()))) if f1s else None,
        "recall": recall,
        "f1": f1s,
        "cobertura": float(diag.mean()),
        "exactitud_diagnosticadas": float((y[diag] == yp[diag]).mean()) if diag.any() else None,
        "matriz": {r: {c: int(((y == r) & (yp == c)).sum()) for c in clases} for r in clases if (y == r).any()},
    }


# ------------------------------------------------------------------ inferencia en fotos

def analizar_fotos(lista, clf: Clasificador, v1: Clasificador | None, cfg: dict) -> list[dict]:
    """Por foto: probabilidades de los parches de hoja (ya calibradas), de la foto completa y de v1."""
    datos = []
    t0 = time.time()
    for n, (ruta, clase) in enumerate(lista, 1):
        img = leer_imagen(ruta)
        if img is None:
            continue
        cs = [c for c in P.cuadros(img, cfg) if c["hoja"] >= cfg["min_hoja"]]
        pp = clf.probabilidades([P.recortar(img, c) for c in cs], cv2.INTER_AREA) if cs else np.zeros((0, len(clf.clases)))
        d = {"ruta": ruta, "clase": clase, "cuadros": cs, "pp": pp,
             "completa": clf.probabilidades([img])[0], "alto": img.shape[0], "ancho": img.shape[1]}
        if v1 is not None:
            d["v1"] = v1.predecir_bgr(img, "imagen")
        datos.append(d)
        if n % 100 == 0:
            print(f"    {n}/{len(lista)} ({(time.time() - t0) / n:.2f} s/foto)")
    return datos


def veredicto(d: dict, clases: list[str], cfg: dict, umbral: float) -> tuple[str, float]:
    if len(d["pp"]) == 0:
        i = int(d["completa"].argmax())
        return clases[i], float(d["completa"][i])
    r = P.agregar(d["pp"], clases, cfg, umbral)
    return r["clase"], r["confianza"]


def evaluar(datos, clases, cfg, umbral, umbral_v1) -> dict:
    y = [d["clase"] for d in datos]
    v2p = [veredicto(d, clases, cfg, umbral) for d in datos]
    v2i = [(clases[int(d["completa"].argmax())], float(d["completa"].max())) for d in datos]
    salida = {"v2_parches": resumen(y, [a for a, _ in v2p], [b for _, b in v2p], umbral, clases),
              "v2_foto_completa": resumen(y, [a for a, _ in v2i], [b for _, b in v2i], umbral, clases)}
    if datos and "v1" in datos[0]:
        salida["v1_foto_completa"] = resumen(y, [d["v1"]["clase"] for d in datos],
                                             [d["v1"]["confianza"] for d in datos], umbral_v1, clases)
    return salida


def recall_cajas(datos, cajas: dict, clases: list[str], umbral: float, clase="sigatoka") -> tuple[int, int]:
    """Cajas YOLO (cx, cy, w, h normalizados) cuyo centro cae en un parche marcado como `clase`."""
    vistas = total = 0
    for d in datos:
        lista = cajas.get(d["ruta"].name) or []
        marcados = [c for c, p in zip(d["cuadros"], d["pp"])
                    if clases[int(p.argmax())] == clase and p.max() >= umbral]
        for cx, cy, _, _ in lista:
            x, y = cx * d["ancho"], cy * d["alto"]
            total += 1
            vistas += any(c["x"] <= x < c["x"] + c["w"] and c["y"] <= y < c["y"] + c["h"] for c in marcados)
    return vistas, total


# ------------------------------------------------------------------ reporte

def tabla(nombre: str, ev: dict, clases: list[str]) -> list[str]:
    def pct(v):
        return "-" if v is None else f"{v * 100:.1f} %"
    lineas = [f"\n### {nombre}\n",
              "| Modelo | Fotos | Exactitud | F1 macro | " + " | ".join(f"Recall {c}" for c in clases) +
              " | Cobertura | Exactitud en las que diagnostica |",
              "|---" * (6 + len(clases)) + "|"]
    for m, r in ev.items():
        if not r.get("n"):
            continue
        lineas.append(f"| {m} | {r['n']} | {pct(r['exactitud'])} | {pct(r['f1_macro'])} | " +
                      " | ".join(pct(r["recall"].get(c)) for c in clases) +
                      f" | {pct(r['cobertura'])} | {pct(r['exactitud_diagnosticadas'])} |")
    r = ev.get("v2_parches", {})
    if r.get("matriz"):
        lineas += ["", "Matriz de confusión v2 por parches (filas = real, columnas = predicho):", "",
                   "| real \\ predicho | " + " | ".join(clases) + " |", "|---" * (len(clases) + 1) + "|"]
        for real, fila in r["matriz"].items():
            lineas.append(f"| {real} | " + " | ".join(str(fila[c]) for c in clases) + " |")
    return lineas


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--onnx", required=True, help="best.onnx de la corrida (runs/classify/<run>/weights/)")
    ap.add_argument("--parches", default="data/parches_v2", help="para la temperatura (usa val/)")
    ap.add_argument("--imagenes", default="data/dataset_v2", help="fotos completas: val/, test/ y test_*/")
    ap.add_argument("--comparar", default="vision/models/sigatoka_cls_v1.onnx")
    ap.add_argument("--salida", default="vision/models/sigatoka_cls_v2.onnx")
    ap.add_argument("--objetivo", type=float, default=0.95,
                    help="exactitud mínima en las fotos que sí diagnostica (val)")
    ap.add_argument("--limite", type=int, default=0, help="máximo de fotos por clase y carpeta (0 = todas)")
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    onnx = Path(args.onnx)
    meta = preparar_meta(onnx)
    clf = Clasificador(onnx)
    clases = clf.clases
    cfg = clf.cfg_parches
    print(f"Modelo {onnx} · clases {clases}")

    # 1. Temperatura con los parches de val
    lista = fotos_de(Path(args.parches) / "val", clases, args.limite * 4, rng)
    print(f"\n1. Temperatura con {len(lista)} parches de val")
    clf.temperatura = 1.0
    partes, yv = [], []
    for i in range(0, len(lista), 256):  # por tandas: miles de parches no caben juntos en memoria
        tanda = [(leer_imagen(r), c) for r, c in lista[i:i + 256]]
        tanda = [(im, c) for im, c in tanda if im is not None]
        partes.append(clf.probabilidades([im for im, _ in tanda]))
        yv += [clases.index(c) for _, c in tanda]
    p, yv = np.concatenate(partes), np.array(yv)
    temps = np.arange(0.3, 6.01, 0.05)
    t = float(temps[int(np.argmin([nll(p, yv, x) for x in temps]))])
    print(f"   T = {t:.2f} · ECE {ece(p, yv):.3f} -> {ece(con_temperatura(p, t), yv):.3f}"
          f" · exactitud parches val {(p.argmax(1) == yv).mean():.3f}")
    clf.temperatura = t

    v1 = Clasificador(args.comparar) if args.comparar and Path(args.comparar).exists() else None
    if v1 is not None and v1.clases != clases:
        print(f"   AVISO: v1 tiene otras clases {v1.clases}; no se compara.")
        v1 = None

    # 2. Regla de la foto con las fotos de val
    raiz = Path(args.imagenes)
    lista = fotos_de(raiz / "val", clases, args.limite, rng)
    print(f"\n2. Regla de la foto con {len(lista)} fotos de val")
    datos_val = analizar_fotos(lista, clf, None, cfg)
    y = [d["clase"] for d in datos_val]
    pruebas = []
    for m in (1, 2, 3):
        c = dict(cfg, min_parches=m)
        for u in np.arange(0.50, 0.951, 0.05):
            v = [veredicto(d, clases, c, u) for d in datos_val]
            r = resumen(y, [a for a, _ in v], [b for _, b in v], u, clases)
            pruebas.append((round(float(u), 2), m, r))
    buenas = [x for x in pruebas if (x[2]["exactitud_diagnosticadas"] or 0) >= args.objetivo]
    if buenas:
        umbral, min_p, r = max(buenas, key=lambda x: (x[2]["cobertura"], x[2]["f1_macro"]))
    else:
        umbral, min_p, r = max(pruebas, key=lambda x: (x[2]["exactitud_diagnosticadas"] or 0))
        print(f"   AVISO: ninguna combinación llega a {args.objetivo:.0%}; uso la más exacta.")
    cfg = dict(cfg, min_parches=min_p)
    print(f"   umbral {umbral} · min_parches {min_p} · cobertura {r['cobertura']:.1%}"
          f" · exactitud en las que diagnostica {r['exactitud_diagnosticadas']:.1%} · F1 macro {r['f1_macro']:.3f}")

    # 3. Prueba final
    evals = {}
    for carpeta in sorted(d for d in raiz.iterdir() if d.is_dir() and d.name.startswith("test")):
        lista = fotos_de(carpeta, clases, args.limite, rng)
        if not lista:
            continue
        print(f"\n3. Prueba en {carpeta.name}: {len(lista)} fotos")
        datos = analizar_fotos(lista, clf, v1, cfg)
        ev = {"todas": evaluar(datos, clases, cfg, umbral, v1.umbral if v1 else 0.65)}
        if carpeta.name == "test":
            por_fuente = defaultdict(list)
            for d in datos:
                por_fuente[d["ruta"].name.split("__")[0]].append(d)
            if len(por_fuente) > 1:
                for f, ds in sorted(por_fuente.items()):
                    ev[f"fuente {f}"] = evaluar(ds, clases, cfg, umbral, v1.umbral if v1 else 0.65)
        cajas_json = carpeta / "cajas_yolo.json"
        if cajas_json.exists():
            vistas, total = recall_cajas(datos, json.loads(cajas_json.read_text(encoding="utf-8")), clases, umbral)
            ev["cajas"] = {"vistas": vistas, "total": total}
            print(f"   lesiones marcadas que caen en un parche 'sigatoka': {vistas}/{total}")
        for nombre, e in ev.items():
            if nombre == "cajas":
                continue
            for m, rr in e.items():
                if rr.get("n"):
                    print(f"   {nombre:22s} {m:18s} exactitud {rr['exactitud']:.3f} · F1 {rr['f1_macro']:.3f}"
                          f" · recall {', '.join(f'{k} {v:.2f}' for k, v in rr['recall'].items())}")
        evals[carpeta.name] = ev

    # 4. Empaquetar
    salida = Path(args.salida)
    salida.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(onnx, salida)
    principal = evals.get("test", {}).get("todas", {})
    nuevo = {
        "model": salida.name,
        "input": meta["input"],
        "preprocesado": f"cuadros de hoja (vision/parches.py), cada uno resize {meta['input'][-1]}x"
                        f"{meta['input'][-1]}, BGR->RGB, float32 /255, CHW; temperatura sobre log-probabilidades",
        "classes": clases,
        "umbral_confianza": umbral,
        "temperatura": round(t, 3),
        "modo_defecto": "parches",
        "parches": {k: cfg[k] for k in P.CONFIG_DEFECTO},
        "dataset": str(raiz),
        "top1_test": principal.get("v2_parches", {}).get("exactitud"),
        "prueba_fotos_test": {m: {k: r.get(k) for k in ("n", "exactitud", "f1_macro", "recall", "cobertura",
                                                         "exactitud_diagnosticadas")}
                              for m, r in principal.items() if r.get("n")},
        "pruebas_externas": {k: {m: {"n": r["n"], "exactitud": r["exactitud"], "recall": r["recall"]}
                                 for m, r in v["todas"].items() if r.get("n")} | ({"cajas": v["cajas"]} if "cajas" in v else {})
                             for k, v in evals.items() if k != "test"},
        "calibrado": date.today().isoformat(),
        "base": meta.get("dataset"),
        "notas": "Generado por vision/train/calibrar.py. El orden de classes viene del entrenamiento y NO se cambia.",
    }
    salida.with_suffix(".json").write_text(json.dumps(nuevo, indent=2, ensure_ascii=False), encoding="utf-8")

    lineas = [f"# Evaluación de {salida.stem}", "",
              f"Generado por `vision/train/calibrar.py` el {date.today().isoformat()} con `{onnx}`.", "",
              f"- Temperatura: {t:.2f}. Umbral: {umbral}. Parches seguros para marcar una foto: {min_p}.",
              f"- En las fotos de val diagnostica {r['cobertura']:.1%} y acierta {r['exactitud_diagnosticadas']:.1%}"
              " de esas; el resto va a revisión humana.",
              "- Métricas sobre fotos completas, no sobre parches. Datasets públicos: no representan el campo"
              " hasta que se pruebe con test_campo."]
    for carpeta, ev in evals.items():
        for nombre, e in ev.items():
            if nombre == "cajas":
                lineas.append(f"\nLesiones marcadas en `{carpeta}` que caen en un parche 'sigatoka':"
                              f" {e['vistas']} de {e['total']}.")
            else:
                lineas += tabla(f"{carpeta} · {nombre}", e, clases)
    reporte = salida.with_name(salida.stem + "_evaluacion.md")
    reporte.write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print(f"\nListo: {salida} + {salida.with_suffix('.json').name} + {reporte.name}")
    print("Revisa el reporte; si v2 por parches gana a v1, sigue con el paso 6 de vision/GUIA-PARCHES.md.")


if __name__ == "__main__":
    main()
