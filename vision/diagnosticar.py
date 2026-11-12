"""Explica por qué el modelo dio un resultado en una foto: cuadro por cuadro, foto completa y v1.

Sirve para revisar fotos donde el resultado parece mal (p. ej. una hoja con Sigatoka que sale
"sana"). No cambia nada; solo imprime.

Uso (desde la raíz del repo):
    python vision/diagnosticar.py foto1.jpg foto2.jpg
    python vision/diagnosticar.py --ultimas 3          # las 3 fotos más nuevas del dron
En la Jetson, con el Python del dron:
    ~/ZED_Pruebas/.venv/bin/python vision/diagnosticar.py --ultimas 3
"""
import argparse
import sys
from pathlib import Path

import cv2
import numpy as np

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
from vision import parches as P  # noqa: E402
from vision.clasificador import Clasificador, leer_imagen  # noqa: E402

FOTOS_DRON = Path.home() / "Prueba#1"


def ultimas(n: int) -> list[Path]:
    limpias = FOTOS_DRON / "sin_texto"
    carpeta = limpias if limpias.is_dir() and any(limpias.glob("*.jpg")) else FOTOS_DRON
    return sorted(carpeta.glob("*.jpg"), key=lambda f: f.stat().st_mtime)[-n:]


def fmt(probs: dict) -> str:
    return " ".join(f"{k} {v:.2f}" for k, v in probs.items())


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("fotos", nargs="*", type=Path)
    ap.add_argument("--ultimas", type=int, default=0, help=f"las N fotos más nuevas de {FOTOS_DRON}")
    args = ap.parse_args()
    fotos = list(args.fotos) + (ultimas(args.ultimas) if args.ultimas else [])
    if not fotos:
        sys.exit("Dime qué fotos revisar (rutas o --ultimas N).")

    v2 = Clasificador(RAIZ / "vision/models/sigatoka_cls_v2.onnx")
    v1_ruta = RAIZ / "vision/models/sigatoka_cls_v1.onnx"
    v1 = Clasificador(v1_ruta) if v1_ruta.exists() else None
    cl = v2.clases
    print(f"v2: umbral {v2.umbral}, temperatura {v2.temperatura}, filtro de hoja "
          f"{'sí' if v2.filtro is not None else 'no'}")

    for f in fotos:
        img = leer_imagen(f)
        print(f"\n=== {f.name}")
        if img is None:
            print("  no se pudo abrir")
            continue
        alto, ancho = img.shape[:2]
        r = v2.predecir_bgr(img, "parches")
        print(f"  tamaño {ancho} x {alto}; {r.get('n_cuadros')} cuadros, {r.get('n_parches')} de hoja"
              f"{'; el filtro quitó ' + str(r['n_filtrados']) if r.get('n_filtrados') else ''}")
        print(f"  v2 por cuadros (fotos del dron y página): {r['clase']} {r['confianza']:.2f}"
              f"{'' if r['confianza'] >= v2.umbral else ' (no seguro)'}")
        print(f"     puntajes: {fmt(r['probs'])}")
        print(f"     cuadros seguros por clase: {r.get('votos')}")
        lista = r.get("parches") or []
        if lista:
            # Probabilidades de cada cuadro otra vez, para ver los que más parecen Sigatoka.
            probs = v2.probabilidades([P.recortar(img, q) for q in lista], cv2.INTER_AREA)
            k = cl.index("sigatoka")
            orden = np.argsort(-probs[:, k])[:5]
            print("     cuadros con más Sigatoka (x, y, lado: probabilidades):")
            for i in orden:
                q = lista[i]
                print(f"       ({q['x']}, {q['y']}, {q['w']}): " + " ".join(f"{c} {p:.2f}" for c, p in zip(cl, probs[i])))
        rv = v2.predecir_bgr(img, "imagen")
        print(f"  v2 foto completa (video en vivo): {rv['clase']} {rv['confianza']:.2f} | {fmt(rv['probs'])}")
        if v1 is not None:
            r1 = v1.predecir_bgr(img, "imagen")
            print(f"  v1 foto completa (modelo anterior): {r1['clase']} {r1['confianza']:.2f} | {fmt(r1['probs'])}")


if __name__ == "__main__":
    main()
