"""Corta data/dataset_v2 en parches de hoja para entrenar el clasificador por parches.

Por cada foto saca cuadros a varias escalas (100, 60, 40 y 30 % del lado corto), se queda
con los que tienen hoja (la misma máscara que usa el dron, vision/parches.py) y los guarda
a 384x384. Las escalas y la degradación imitan lo que ve la cámara del dron a 1.5-3 m,
donde un cuadro de 384 px cubre 30-75 cm de hoja. El 30 % es el tamaño que usa la
inferencia en fotos grandes (lado_min_rel en vision/parches.py).

Robustez (--degradar): a una parte de los parches se les aplica una o varias de estas
alteraciones, para que el modelo no dependa de fotos perfectas: menos resolución, desenfoque,
movimiento, ruido de sensor, JPEG, sombra o luz desigual, neblina, tono de luz más cálido o
más frío y giros de 90 grados. No se cambia el tono de las lesiones (amarillo/café es la señal).

Clase "sin_hoja" (no se ve hoja de plátano):
- las fotos de la carpeta sin_hoja (otras plantas, maleza, frutos, escenas; ver
  fuentes_v2.json) dan cuadros amplios (60-100 %) al azar, con o sin verde;
- de las fotos 'sana' se toma a veces un cuadro casi sin vegetación (suelo, cielo, fondo).
  Solo de las sanas: de una foto enferma podría ser una hoja seca, que sí es plátano.

Etiquetas débiles: un parche hereda la clase de su foto, pero un parche de una hoja con
Sigatoka puede ser un trozo sano. Con --maestro (el modelo v1) se limpian:
- foto 'sana': el parche se descarta si el maestro ve enfermedad con >= 0.80;
- foto enferma: el parche se queda si el maestro le da a esa clase >= 0.35; la escala
  100 % (la foto completa) siempre se queda con su etiqueta original.
Los descartados se anotan en parches.csv para poder revisarlos.

--equilibrar saca más parches por foto de las clases con menos fotos (hasta 3 veces), así
el modelo no aprende a decir siempre la clase más común. Solo en train.

Uso (desde la raíz del repo, con el venv activo):
    python vision/train/hacer_parches.py --maestro vision/models/sigatoka_cls_v1.onnx --equilibrar
    python vision/train/hacer_parches.py --entrada data/dataset_v2 --salida data/parches_v2 --procesos 8

Sale: data/parches_v2/{train,val,test}/<clase>/*.jpg y data/parches_v2/parches.csv.
El test de parches es solo de referencia (etiquetas débiles); la prueba que cuenta es la
de fotos completas en vision/train/calibrar.py. Ver vision/GUIA-PARCHES.md.
"""
import argparse
import csv
import os
import random
import sys
from collections import Counter
from multiprocessing import Pool
from pathlib import Path

import cv2
import numpy as np

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from vision import parches as P  # noqa: E402
from vision.clasificador import leer_imagen  # noqa: E402

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
LADO = 384
SIN_HOJA = "sin_hoja"


# ------------------------------------------------------------------ alteraciones

def degradar(img: np.ndarray, rng: random.Random) -> np.ndarray:
    """Imita una toma más lejana, movida o con mala luz. Aplica 1-3 alteraciones."""
    opciones = ["resolucion", "desenfoque", "movimiento", "ruido", "sombra", "neblina", "luz"]
    for op in rng.sample(opciones, rng.randint(1, 3)):
        if op == "resolucion":
            f = rng.uniform(1.5, 4.0)
            chica = cv2.resize(img, (max(8, int(LADO / f)),) * 2, interpolation=cv2.INTER_AREA)
            img = cv2.resize(chica, (LADO, LADO), interpolation=cv2.INTER_LINEAR)
        elif op == "desenfoque":
            img = cv2.GaussianBlur(img, (0, 0), rng.uniform(0.5, 1.5))
        elif op == "movimiento":
            n = rng.choice([3, 5, 7, 9])
            k = np.zeros((n, n), np.float32)
            k[n // 2, :] = 1.0 / n
            k = cv2.warpAffine(k, cv2.getRotationMatrix2D((n / 2 - 0.5, n / 2 - 0.5), rng.uniform(0, 180), 1), (n, n))
            img = cv2.filter2D(img, -1, k / max(k.sum(), 1e-6))
        elif op == "ruido":
            ruido = np.random.default_rng(rng.randint(0, 2**31)).normal(0, rng.uniform(2, 8), img.shape)
            img = np.clip(img.astype(np.float32) + ruido, 0, 255).astype(np.uint8)
        elif op == "sombra":
            # luz desigual: un degradado de 0.55 a 1.15 en una dirección al azar
            a = rng.uniform(0, 2 * np.pi)
            yy, xx = np.mgrid[0:LADO, 0:LADO].astype(np.float32) / LADO - 0.5
            g = (np.cos(a) * xx + np.sin(a) * yy) + 0.5
            fac = rng.uniform(0.55, 0.8) + g * rng.uniform(0.2, 0.4)
            img = np.clip(img.astype(np.float32) * fac[..., None], 0, 255).astype(np.uint8)
        elif op == "neblina":
            gris = np.full_like(img, rng.randint(170, 230))
            img = cv2.addWeighted(img, 1 - (b := rng.uniform(0.1, 0.3)), gris, b, 0)
        elif op == "luz":
            # luz más cálida o más fría (azul/rojo ±8 %), sin tocar el verde
            f = rng.uniform(-0.08, 0.08)
            x = img.astype(np.float32)
            x[..., 0] *= 1 - f
            x[..., 2] *= 1 + f
            img = np.clip(x, 0, 255).astype(np.uint8)
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, rng.randint(60, 92)])
    return cv2.imdecode(buf, cv2.IMREAD_COLOR) if ok else img


# ------------------------------------------------------------------ cuadros

def cuadros_de_foto(img: np.ndarray, escalas: list[float], min_hoja: float, mascara: np.ndarray,
                    todos: bool = False) -> list[dict]:
    alto, ancho = img.shape[:2]
    corto = min(alto, ancho)
    salida = []
    for e in escalas:
        lado = max(32, int(corto * e))
        if e < 0.999 and lado < 160:
            continue  # en fotos chicas (224 px) un recorte de 60 px ampliado a 384 no aporta
        cfg = P.config({"lado_px": lado, "lado_min_rel": 0.0, "solape": 0.25, "max_parches": 30})
        for c in P.cuadros(img, cfg, mascara):
            if e >= 0.999:
                # escala completa: el cuadrado centrado, sin importar la máscara
                c = {"x": (ancho - lado) // 2, "y": (alto - lado) // 2, "w": lado, "h": lado, "hoja": c["hoja"]}
                salida.append({**c, "escala": e})
                break
            if todos or c["hoja"] >= min_hoja:
                salida.append({**c, "escala": e})
    return salida


# ------------------------------------------------------------------ un proceso por foto

_G: dict = {}


def _iniciar(args_dict: dict) -> None:
    """Cada proceso abre su propia copia del maestro (onnxruntime no se comparte)."""
    _G.update(args_dict)
    _G["maestro"] = None
    if args_dict.get("maestro"):
        from vision.clasificador import Clasificador
        _G["maestro"] = Clasificador(args_dict["maestro"])
        _G["maestro"]._sess.set_providers(["CPUExecutionProvider"])


def procesar_foto(tarea: tuple) -> tuple[list[dict], Counter, Counter]:
    ruta, split, clase, cuantos, semilla = tarea
    rng = random.Random(semilla)
    entrada, salida = Path(_G["entrada"]), Path(_G["salida"])
    maestro = _G["maestro"]
    filas, conteo, motivos = [], Counter(), Counter()
    img = leer_imagen(ruta)
    if img is None:
        motivos["no se pudo leer"] += 1
        return filas, conteo, motivos

    mascara = P.mascara_hoja(img)
    es_sin_hoja = clase == SIN_HOJA
    # De las fotos sin_hoja solo recortes amplios (60-100 %): de cerca, la cáscara de un plátano
    # con manchas o una hoja de otra planta se confunden con una hoja de plátano enferma o sana.
    escalas = [e for e in _G["escalas"] if e >= 0.6] if es_sin_hoja else _G["escalas"]
    cs = cuadros_de_foto(img, escalas, _G["min_hoja"], mascara, todos=es_sin_hoja)
    completos = [c for c in cs if c["escala"] >= 0.999]
    resto = [c for c in cs if c["escala"] < 0.999]
    rng.shuffle(resto)
    cs = completos + resto[:max(0, cuantos - len(completos))]
    etiquetas_fijas = [None] * len(cs)

    # Fondo de las fotos sanas -> sin_hoja (suelo, cielo, tela de fondo)
    if clase == "sana" and _G["fondo"] > 0 and rng.random() < _G["fondo"]:
        cfg = P.config({"lado_px": max(32, int(min(img.shape[:2]) * 0.3)), "lado_min_rel": 0.0,
                        "solape": 0.25, "max_parches": 30})
        vacios = [c for c in P.cuadros(img, cfg, mascara) if c["hoja"] < 0.03]
        if vacios:
            cs.append({**rng.choice(vacios), "escala": 0.3})
            etiquetas_fijas.append(SIN_HOJA)

    recortes = [cv2.resize(P.recortar(img, c), (LADO, LADO), interpolation=cv2.INTER_AREA) for c in cs]
    probs = maestro.probabilidades(recortes) if maestro is not None else None

    for i, (c, rec) in enumerate(zip(cs, recortes)):
        etiqueta, motivo, p_clase = etiquetas_fijas[i] or clase, "", None
        if probs is not None:
            pc = dict(zip(maestro.clases, probs[i]))
            enfermedad = max(v for k, v in pc.items() if k != "sana")
            if etiquetas_fijas[i] == SIN_HOJA:
                p_clase = pc.get("sana")
                if enfermedad >= 0.5:
                    etiqueta, motivo = None, "fondo con algo que parece lesión"
            elif clase in maestro.clases:  # una categoría nueva (o sin_hoja) no tiene maestro
                p_clase = pc.get(clase)
                if c["escala"] < 0.999:
                    if clase == "sana" and enfermedad >= _G["max_mancha_sana"]:
                        etiqueta, motivo = None, "sana con mancha según el maestro"
                    elif clase != "sana" and (p_clase or 0) < _G["min_maestro"]:
                        etiqueta, motivo = None, f"trozo sin {clase} según el maestro"
        degradado = rng.random() < _G["degradar"]
        if degradado:
            rec = degradar(rec, rng)
        if rng.random() < 0.3:
            rec = np.ascontiguousarray(np.rot90(rec, rng.choice([1, 2, 3])))
        nombre = f"{ruta.stem}_e{int(c['escala'] * 100)}_{i}{'_d' if degradado else ''}.jpg"
        if etiqueta:
            destino = salida / split / etiqueta / nombre
            destino.parent.mkdir(parents=True, exist_ok=True)
            ok, buf = cv2.imencode(".jpg", rec, [cv2.IMWRITE_JPEG_QUALITY, 92])
            if ok:
                buf.tofile(str(destino))
            conteo[(split, etiqueta)] += 1
        else:
            motivos[motivo] += 1
        filas.append({"parche": f"{split}/{etiqueta}/{nombre}" if etiqueta else "",
                      "foto": str(ruta.relative_to(entrada)).replace("\\", "/"),
                      "split": split, "clase_foto": clase, "etiqueta": etiqueta or "descartado",
                      "motivo": motivo, "escala": c["escala"], "x": c["x"], "y": c["y"],
                      "lado": c["w"], "hoja": c["hoja"], "degradado": int(degradado),
                      "p_maestro": "" if p_clase is None else round(float(p_clase), 3)})
    return filas, conteo, motivos


# ------------------------------------------------------------------ principal

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--entrada", default="data/dataset_v2")
    ap.add_argument("--salida", default="data/parches_v2")
    ap.add_argument("--maestro", default=None, help="ONNX para limpiar etiquetas (p. ej. sigatoka_cls_v1.onnx)")
    ap.add_argument("--escalas", default="1.0,0.6,0.4,0.3")
    ap.add_argument("--por-foto", type=int, default=6, help="parches por foto (equilibra fotos grandes)")
    ap.add_argument("--equilibrar", action="store_true",
                    help="en train, más parches por foto (hasta 3x) para las clases con menos fotos")
    ap.add_argument("--min-hoja", type=float, default=0.35)
    ap.add_argument("--degradar", type=float, default=0.5, help="fracción de parches alterados (0 = ninguno)")
    ap.add_argument("--fondo", type=float, default=0.3,
                    help="probabilidad de sacar un cuadro de fondo (sin_hoja) de cada foto sana")
    ap.add_argument("--min-maestro", type=float, default=0.35,
                    help="P mínima del maestro para que un trozo de hoja enferma conserve la etiqueta")
    ap.add_argument("--max-mancha-sana", type=float, default=0.80,
                    help="si el maestro ve enfermedad con al menos esto en un trozo 'sano', se descarta")
    ap.add_argument("--splits", default="train,val,test")
    ap.add_argument("--procesos", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    entrada, salida = Path(args.entrada), Path(args.salida)
    if salida.exists():
        sys.exit(f"{salida} ya existe: bórralo (o usa otro --salida) para regenerar.")
    splits = args.splits.split(",")

    # Tareas: (foto, split, clase, parches a sacar, semilla)
    tareas = []
    for split in splits:
        por_clase = {}
        for d in sorted(p for p in (entrada / split).iterdir() if p.is_dir()) if (entrada / split).is_dir() else []:
            por_clase[d.name] = sorted(p for p in d.rglob("*") if p.suffix.lower() in IMG_EXTS)
        # La meta la pone la clase de hoja más grande; sin_hoja tiene su propia cuota fija.
        mayor = max((len(v) for c, v in por_clase.items() if c != SIN_HOJA), default=1)
        for clase, fotos in por_clase.items():
            cuantos = args.por_foto
            if args.equilibrar and split == "train" and fotos:
                cuantos = int(min(3 * args.por_foto, max(args.por_foto, round(args.por_foto * mayor / len(fotos)))))
            if clase == SIN_HOJA:
                cuantos = max(2, args.por_foto // 2)  # muchas fuentes de negativos: menos por foto
            print(f"  {split:6s} {clase:16s} {len(fotos):6d} fotos x {cuantos} parches")
            tareas += [(r, split, clase, cuantos, args.seed + len(tareas) + k) for k, r in enumerate(fotos)]

    print(f"\n{len(tareas)} fotos, {args.procesos} procesos"
          f"{'; maestro ' + Path(args.maestro).name if args.maestro else ''}")
    config = {"entrada": str(entrada), "salida": str(salida), "maestro": args.maestro,
              "escalas": [float(e) for e in args.escalas.split(",")], "min_hoja": args.min_hoja,
              "degradar": args.degradar, "fondo": args.fondo, "min_maestro": args.min_maestro,
              "max_mancha_sana": args.max_mancha_sana}

    filas, conteo, motivos = [], Counter(), Counter()
    if args.procesos > 1:
        with Pool(args.procesos, initializer=_iniciar, initargs=(config,)) as pool:
            for n, (f, c, m) in enumerate(pool.imap_unordered(procesar_foto, tareas, chunksize=8), 1):
                filas += f
                conteo += c
                motivos += m
                if n % 1000 == 0:
                    print(f"  {n}/{len(tareas)}", flush=True)
    else:
        _iniciar(config)
        for n, t in enumerate(tareas, 1):
            f, c, m = procesar_foto(t)
            filas += f
            conteo += c
            motivos += m
            if n % 1000 == 0:
                print(f"  {n}/{len(tareas)}", flush=True)

    if not filas:
        sys.exit("No salió ningún parche. Revisa --entrada.")

    # Segundo equilibrio (solo train): las clases de hoja que quedaron cortas reciben copias
    # alteradas de sus propios parches hasta ~70 % de la clase más grande (máximo el doble).
    if args.equilibrar and "train" in splits:
        rng = random.Random(args.seed + 7)
        hoja = {c: n for (sp, c), n in conteo.items() if sp == "train" and c != SIN_HOJA}
        meta = int(0.7 * max(hoja.values(), default=0))
        for c, n in sorted(hoja.items()):
            faltan = min(meta - n, n)
            if faltan <= 0:
                continue
            fuentes = sorted((salida / "train" / c).glob("*.jpg"))
            for k in range(faltan):
                origen = rng.choice(fuentes)
                img = leer_imagen(origen)
                if img is None:
                    continue
                img = degradar(img, rng) if rng.random() < 0.7 else img
                img = np.ascontiguousarray(np.rot90(img, rng.choice([0, 1, 2, 3])))
                if rng.random() < 0.5:
                    img = np.ascontiguousarray(img[:, ::-1])
                ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 92])
                if ok:
                    buf.tofile(str(origen.with_name(f"{origen.stem}_eq{k}.jpg")))
                    conteo[("train", c)] += 1
            print(f"  equilibrio: {c} {n} -> {n + faltan} parches (copias alteradas)")
    salida.mkdir(parents=True, exist_ok=True)
    with open(salida / "parches.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(sorted(filas, key=lambda r: (r["split"], r["foto"])))

    clases = sorted({c for _, c in conteo})
    print(f"\n{'split':8s}" + "".join(f"{c:>16s}" for c in clases))
    for split in splits:
        print(f"{split:8s}" + "".join(f"{conteo[(split, c)]:16d}" for c in clases))
    for m, k in motivos.most_common():
        print(f"Descartados ({m}): {k}")
    tren = {c: conteo[("train", c)] for c in clases}
    for c in clases:
        if c != "sana" and tren[c] < 0.25 * max(tren.values()):
            print(f"AVISO: en train hay pocos parches de {c}. Si el maestro descartó muchos, prueba"
                  " --min-maestro 0.2 (o revisa parches.csv); si faltan fotos, agrega fuentes.")
    print(f"\nParches en {salida}. Siguiente paso:")
    print(f"  python vision/train/train_cls.py --data {salida} --model yolo11s-cls.pt --flipud 0.5 --erasing 0.1 --name parches_v2")


if __name__ == "__main__":
    main()
