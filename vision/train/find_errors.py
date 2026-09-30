"""Encuentra las imágenes mal clasificadas y las copia a una carpeta para revisarlas.

Recorre un split del dataset (val por defecto), corre el modelo entrenado y copia
cada imagen mal clasificada a runs/errores/real_<X>__pred_<Y>/, con la confianza
en el nombre del archivo. Así el análisis de errores (fase 4 de la guía) se hace
viendo carpetas, no buscando a ciegas.

Uso (desde la raíz del repo, con el venv activo):
    python vision/train/find_errors.py
    python vision/train/find_errors.py --split test
"""
import argparse
import shutil
from collections import Counter
from pathlib import Path

from ultralytics import YOLO

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--weights", default="runs/classify/train/weights/best.pt")
    ap.add_argument("--data", default="data/dataset")
    ap.add_argument("--split", default="val", choices=["train", "val", "test"])
    ap.add_argument("--out", default="runs/errores")
    args = ap.parse_args()

    model = YOLO(args.weights)
    names = model.names
    out = Path(args.out) / args.split
    if out.exists():
        shutil.rmtree(out)

    errores: Counter[str] = Counter()
    total = 0
    for clase_dir in sorted((Path(args.data) / args.split).iterdir()):
        if not clase_dir.is_dir():
            continue
        real = clase_dir.name
        imgs = [p for p in sorted(clase_dir.iterdir()) if p.suffix.lower() in IMG_EXTS]
        total += len(imgs)
        for r in model.predict(source=imgs, stream=True, verbose=False):
            pred = names[int(r.probs.top1)]
            if pred == real:
                continue
            conf = float(r.probs.top1conf)
            destino = out / f"real_{real}__pred_{pred}"
            destino.mkdir(parents=True, exist_ok=True)
            origen = Path(r.path)
            shutil.copy2(origen, destino / f"{conf:.2f}_{origen.name}")
            errores[f"real {real} -> pred {pred}"] += 1

    print(f"\n{total} imágenes revisadas en '{args.split}'; {sum(errores.values())} mal clasificadas:")
    for combo, n in errores.most_common():
        print(f"  {combo}: {n}")
    print(f"\nCopias en {out}\\  (el número al inicio de cada archivo es la confianza).")
    print("Ábrelas con el Explorador y busca el patrón: ¿manchitas, contraluz, fondo, estilo de foto?")


if __name__ == "__main__":
    main()
