"""Corta data/dataset_v2 en parches de hoja para entrenar el clasificador por parches.

Por cada foto saca cuadros a varias escalas (100 %, 60 % y 40 % del lado corto), se queda
con los que tienen hoja (la misma máscara que usa el dron, vision/parches.py) y los guarda
a 384x384. Las escalas y la degradación (bajar resolución, desenfoque, JPEG) imitan lo que
ve la cámara del dron a 1.5-3 m, donde un cuadro de 384 px cubre 30-75 cm de hoja.

Etiquetas débiles: un parche hereda la clase de su foto, pero un parche de una hoja con
Sigatoka puede ser un trozo sano. Con --maestro (el modelo v1) se limpian:
- foto 'sana': el parche se descarta si el maestro ve enfermedad con >= 0.80 (la carpeta
  HEALTHY del dataset público trae hojas con manchas, ver experiments.md corrida 1);
- foto enferma: el parche se queda si el maestro le da a esa clase >= 0.35; la escala
  100 % (la foto completa) siempre se queda con su etiqueta original.
Los descartados se anotan en parches.csv para poder revisarlos.

Uso (desde la raíz del repo, con el venv activo):
    python vision/train/hacer_parches.py --maestro vision/models/sigatoka_cls_v1.onnx
    python vision/train/hacer_parches.py --entrada data/dataset_v2 --salida data/parches_v2 --por-foto 6

Sale: data/parches_v2/{train,val,test}/<clase>/*.jpg y data/parches_v2/parches.csv.
El test de parches es solo de referencia (etiquetas débiles); la prueba que cuenta es la
de fotos completas en vision/train/calibrar.py. Ver vision/GUIA-PARCHES.md, paso 3.
"""
import argparse
import csv
import random
import sys
from collections import Counter
from pathlib import Path

import cv2
import numpy as np

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ))
from vision import parches as P  # noqa: E402
from vision.clasificador import leer_imagen  # noqa: E402

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tif", ".tiff"}
LADO = 384


def degradar(img: np.ndarray, rng: random.Random) -> np.ndarray:
    """Imita una toma más lejana o movida: menos resolución, algo de desenfoque y JPEG."""
    f = rng.uniform(1.5, 4.0)
    chica = cv2.resize(img, (max(8, int(LADO / f)), max(8, int(LADO / f))), interpolation=cv2.INTER_AREA)
    img = cv2.resize(chica, (LADO, LADO), interpolation=cv2.INTER_LINEAR)
    s = rng.uniform(0.0, 1.2)
    if s > 0.3:
        img = cv2.GaussianBlur(img, (0, 0), s)
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, rng.randint(60, 90)])
    return cv2.imdecode(buf, cv2.IMREAD_COLOR) if ok else img


def cuadros_de_foto(img: np.ndarray, escalas: list[float], min_hoja: float, mascara: np.ndarray) -> list[dict]:
    alto, ancho = img.shape[:2]
    corto = min(alto, ancho)
    salida = []
    for e in escalas:
        lado = max(32, int(corto * e))
        cfg = P.config({"lado_px": lado, "lado_min_rel": 0.0, "solape": 0.25, "max_parches": 30})
        for c in P.cuadros(img, cfg, mascara):
            if e >= 0.999:
                # escala completa: el cuadrado centrado, sin importar la máscara
                c = {"x": (ancho - lado) // 2, "y": (alto - lado) // 2, "w": lado, "h": lado, "hoja": c["hoja"]}
                salida.append({**c, "escala": e})
                break
            if c["hoja"] >= min_hoja:
                salida.append({**c, "escala": e})
    return salida


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--entrada", default="data/dataset_v2")
    ap.add_argument("--salida", default="data/parches_v2")
    ap.add_argument("--maestro", default=None, help="ONNX para limpiar etiquetas (p. ej. sigatoka_cls_v1.onnx)")
    ap.add_argument("--escalas", default="1.0,0.6,0.4")
    ap.add_argument("--por-foto", type=int, default=6, help="máximo de parches por foto (equilibra fotos grandes)")
    ap.add_argument("--min-hoja", type=float, default=0.35)
    ap.add_argument("--degradar", type=float, default=0.4, help="fracción de parches degradados (0 = ninguno)")
    ap.add_argument("--min-maestro", type=float, default=0.35,
                    help="P mínima del maestro para que un trozo de hoja enferma conserve la etiqueta")
    ap.add_argument("--max-mancha-sana", type=float, default=0.80,
                    help="si el maestro ve enfermedad con al menos esto en un trozo 'sano', se descarta")
    ap.add_argument("--splits", default="train,val,test")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    entrada, salida = Path(args.entrada), Path(args.salida)
    if salida.exists():
        sys.exit(f"{salida} ya existe: bórralo (o usa otro --salida) para regenerar.")
    escalas = [float(e) for e in args.escalas.split(",")]
    rng = random.Random(args.seed)

    maestro = None
    if args.maestro:
        from vision.clasificador import Clasificador
        maestro = Clasificador(args.maestro)
        print(f"Maestro: {Path(args.maestro).name} {maestro.clases}")

    filas, conteo, motivos = [], Counter(), Counter()
    for split in args.splits.split(","):
        fotos = sorted(p for p in (entrada / split).rglob("*") if p.suffix.lower() in IMG_EXTS)
        print(f"\n{split}: {len(fotos)} fotos")
        for n, ruta in enumerate(fotos, 1):
            clase = ruta.parent.name
            img = leer_imagen(ruta)
            if img is None:
                motivos["no se pudo leer"] += 1
                continue
            mascara = P.mascara_hoja(img)
            cs = cuadros_de_foto(img, escalas, args.min_hoja, mascara)
            completos = [c for c in cs if c["escala"] >= 0.999]
            resto = [c for c in cs if c["escala"] < 0.999]
            rng.shuffle(resto)
            cs = completos + resto[:max(0, args.por_foto - len(completos))]
            recortes = [cv2.resize(P.recortar(img, c), (LADO, LADO), interpolation=cv2.INTER_AREA) for c in cs]
            probs = maestro.probabilidades(recortes) if maestro else None

            for i, (c, rec) in enumerate(zip(cs, recortes)):
                etiqueta, motivo, p_clase = clase, "", None
                if probs is not None:
                    pc = dict(zip(maestro.clases, probs[i]))
                    p_clase = pc.get(clase)
                    if c["escala"] < 0.999:
                        if clase == "sana" and max(v for k, v in pc.items() if k != "sana") >= args.max_mancha_sana:
                            etiqueta, motivo = None, "sana con mancha según el maestro"
                        elif clase != "sana" and (p_clase or 0) < args.min_maestro:
                            etiqueta, motivo = None, f"trozo sin {clase} según el maestro"
                degradado = rng.random() < args.degradar
                if degradado:
                    rec = degradar(rec, rng)
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
            if n % 500 == 0:
                print(f"  {n}/{len(fotos)}")

    salida.mkdir(parents=True, exist_ok=True)
    with open(salida / "parches.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(filas[0].keys()))
        w.writeheader()
        w.writerows(filas)

    clases = sorted({c for _, c in conteo})
    print(f"\n{'split':8s}" + "".join(f"{c:>16s}" for c in clases))
    for split in args.splits.split(","):
        print(f"{split:8s}" + "".join(f"{conteo[(split, c)]:16d}" for c in clases))
    for m, k in motivos.most_common():
        print(f"Descartados ({m}): {k}")
    for c in clases:
        if c != "sana" and conteo[("train", c)] < 0.25 * max(1, conteo[("train", "sana")]):
            print(f"AVISO: en train hay pocos parches de {c}. Si el maestro descartó muchos, prueba"
                  " --min-maestro 0.2 (o revisa parches.csv).")
    print(f"\nParches en {salida}. Siguiente paso:")
    print(f"  python vision/train/train_cls.py --data {salida} --model yolo11n-cls.pt --name parches_v2")


if __name__ == "__main__":
    main()
