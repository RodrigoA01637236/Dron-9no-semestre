"""Genera el dataset train/val/test a partir de las carpetas de imágenes descargadas.

Mapea las carpetas del dataset público a las clases del proyecto, escribe el
manifiesto CSV (que SÍ va a git) y materializa la estructura que espera
Ultralytics. Split 70/15/15 por clase, con semilla fija para que sea
reproducible. Ver vision/GUIA-MODELO.md fase 2 y docs/05-datos-dataset.md.

Uso (desde la raíz del repo, con el venv activo):
    python scripts/make_splits.py --src data/raw/public/banana --out data/dataset

Windows:
    python scripts\\make_splits.py --src "data\\raw\\public\\banana" --out data\\dataset
"""
import argparse
import csv
import random
import shutil
from datetime import date
from pathlib import Path

# Carpeta del dataset descargado -> clase del proyecto.
# Con datos públicos no se distingue estadio de Sigatoka; la división
# temprana/avanzada llega con las fotos propias etiquetadas (doc 05).
# Las claves se comparan en mayúsculas y sin espacios extra.
CLASS_MAP = {
    "HEALTHY PICTURES": "sana",
    "SIGATOKA PICTURES": "sigatoka",
    "CORDANA PICTURES": "otra_condicion",
    "PESTALO PICTURES": "otra_condicion",
    "PANAMA DISEASE": "otra_condicion",
    "BANANA SKIPPER DAMAGE": "otra_condicion",
    "CHEWING INSECT DAMAGE": "otra_condicion",
}

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
SPLITS = (("train", 0.70), ("val", 0.15), ("test", 0.15))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", required=True, help="carpeta con las subcarpetas de clases descargadas")
    ap.add_argument("--out", default="data/dataset", help="carpeta destino train/val/test")
    ap.add_argument("--manifest", default="data/manifests/v1_public_baseline.csv")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    src, out = Path(args.src), Path(args.out)
    rng = random.Random(args.seed)

    if out.exists():
        raise SystemExit(f"{out} ya existe: bórralo (o usa otro --out) para regenerar desde cero.")

    # 1. Recolectar imágenes por clase del proyecto
    por_clase: dict[str, list[tuple[Path, str]]] = {}
    for carpeta in sorted(p for p in src.iterdir() if p.is_dir()):
        clase = CLASS_MAP.get(carpeta.name.strip().upper())
        if clase is None:
            print(f"AVISO: carpeta '{carpeta.name}' no está en CLASS_MAP; se omite.")
            continue
        imgs = [p for p in sorted(carpeta.rglob("*")) if p.suffix.lower() in IMG_EXTS]
        print(f"{carpeta.name:28s} -> {clase:15s} {len(imgs):5d} imágenes")
        por_clase.setdefault(clase, []).extend((p, carpeta.name) for p in imgs)

    if not por_clase:
        raise SystemExit("No se encontró ninguna carpeta mapeada. Revisa --src y CLASS_MAP.")

    # 2. Barajar y repartir 70/15/15 por clase; copiar al destino
    filas = []
    for clase, items in sorted(por_clase.items()):
        rng.shuffle(items)
        n = len(items)
        n_train = int(n * SPLITS[0][1])
        n_val = int(n * SPLITS[1][1])
        cortes = {"train": items[:n_train],
                  "val": items[n_train:n_train + n_val],
                  "test": items[n_train + n_val:]}
        for split, lote in cortes.items():
            destino = out / split / clase
            destino.mkdir(parents=True, exist_ok=True)
            for ruta, origen in lote:
                # prefijo con la carpeta de origen para evitar nombres repetidos
                nombre = f"{origen.replace(' ', '_').lower()}__{ruta.name}"
                shutil.copy2(ruta, destino / nombre)
                filas.append({
                    "path": f"{split}/{clase}/{nombre}",
                    "origen": origen,
                    "fecha": date.today().isoformat(),
                    "etiqueta": clase,
                    "split": split,
                })
        print(f"{clase:15s} total {n:5d} -> train {n_train}, val {n_val}, test {n - n_train - n_val}")

    # 3. Manifiesto CSV (este archivo SÍ se commitea)
    manifest = Path(args.manifest)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    with open(manifest, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["path", "origen", "fecha", "etiqueta", "split"])
        w.writeheader()
        w.writerows(filas)
    print(f"\nManifiesto: {manifest} ({len(filas)} filas)")
    print(f"Dataset listo en: {out}")
    print("Siguiente paso (fase 3): python vision/train/train_cls.py --data", out)


if __name__ == "__main__":
    main()
