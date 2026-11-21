"""Explica por qué el modelo dio un resultado en una foto, cuadro por cuadro.

El resultado es el mismo que da el dron y la página web: el v2 por cuadros sobre la foto.
Sirve para revisar fotos donde el resultado parece mal (p. ej. una hoja con Sigatoka que sale
"sana"). No cambia nada; solo imprime. Con --comparar imprime también la foto completa
reducida y el modelo v1, solo como referencia: ni el dron ni la página los usan.

Uso (desde la raíz del repo):
    python vision/diagnosticar.py foto1.jpg foto2.jpg
    python vision/diagnosticar.py --ultimas 3          # las 3 fotos más nuevas del dron
    python vision/diagnosticar.py --comparar foto.jpg  # además, foto completa y v1
    python vision/diagnosticar.py --ultimas 6 --comparar --guardar ~/diagnostico   # y dibuja los cuadros
En la Jetson, con el Python del dron:
    ~/ZED_Pruebas/.venv/bin/python vision/diagnosticar.py --ultimas 3
"""
import argparse
import sys
from collections import Counter
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
    ap.add_argument("--comparar", action="store_true", help="también la foto completa y el v1 (solo referencia)")
    ap.add_argument("--guardar", metavar="CARPETA", help="guarda cada foto con sus cuadros dibujados (p. ej. ~/diagnostico)")
    args = ap.parse_args()
    fotos = list(args.fotos) + (ultimas(args.ultimas) if args.ultimas else [])
    if not fotos:
        sys.exit("Dime qué fotos revisar (rutas o --ultimas N).")

    v2 = Clasificador(RAIZ / "vision/models/sigatoka_cls_v2.onnx")
    v1_ruta = RAIZ / "vision/models/sigatoka_cls_v1.onnx"
    v1 = Clasificador(v1_ruta) if args.comparar and v1_ruta.exists() else None
    cl = v2.clases
    print(f"v2: umbral {v2.umbral}, temperatura {v2.temperatura}, filtro de hoja "
          f"{'sí' if v2.filtro is not None else 'no'}")

    cfg = v2.cfg_parches
    COLOR = {"sana": (60, 180, 60), "sigatoka": (40, 40, 230), "otra_condicion": (0, 190, 255), "sin_hoja": (160, 160, 160)}
    salida = Path(args.guardar).expanduser() if args.guardar else None
    if salida:
        salida.mkdir(parents=True, exist_ok=True)

    for f in fotos:
        img = leer_imagen(f)
        print(f"\n=== {f.name}")
        if img is None:
            print("  no se pudo abrir")
            continue
        alto, ancho = img.shape[:2]

        # Cómo viene la imagen: luz, color y enfoque (para comparar fotos que salen bien y mal)
        gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        sat = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)[..., 1]
        nitidez = cv2.Laplacian(cv2.resize(gris, (ancho // 2, alto // 2), interpolation=cv2.INTER_AREA), cv2.CV_64F).var()
        b, g, r_ = img.reshape(-1, 3).mean(0)
        quemado = float((gris > 245).mean())
        print(f"  tamaño {ancho} x {alto} · brillo {gris.mean():.0f}/255 · saturación {sat.mean():.0f}/255 · "
              f"nitidez {nitidez:.0f} · color medio R {r_:.0f} G {g:.0f} B {b:.0f} · quemado {quemado:.0%}")
        avisos = [x for x, si in (("muy oscura", gris.mean() < 60), ("muy clara o con reflejo", gris.mean() > 200 or quemado > 0.05),
                                  ("poco color (gris)", sat.mean() < 35)) if si]
        if avisos:
            print("  ojo: " + ", ".join(avisos))

        r = v2.predecir_bgr(img, "parches")
        print(f"  Resultado (el mismo del dron y la página): {r['clase']} {r['confianza']:.2f}"
              f"{'' if r['confianza'] >= v2.umbral or r['clase'] == 'sin_hoja' else ' (no seguro)'}"
              f" · manda el cuadro {'grande' if r.get('escala') == 'gruesa' else 'chico'} ({r.get('lado')} px)")

        # Lo que ve cada tamaño de cuadro, para saber cuál falla y dónde
        m = P.mascara_hoja(img)
        dibujo = img.copy() if salida else None
        for nombre, c in (("chico", cfg), ("grande", P.cfg_gruesa(cfg))):
            if c is None:
                continue
            lado = P.lado_cuadro(alto, ancho, c)
            if nombre == "grande" and lado <= P.lado_cuadro(alto, ancho, cfg):
                print("  cuadro grande: en esta foto mide lo mismo que el chico")
                continue
            rr, usar, probs, _ = v2._por_cuadros(img, c, m)
            if rr is None:
                print(f"  cuadro {nombre} ({lado} px): no encontró hoja")
                continue
            cuenta = dict(Counter(cl[i] for i in probs.argmax(1)).most_common())
            print(f"  cuadro {nombre} ({lado} px, {len(usar)} cuadros): {rr['clase']} {rr['confianza']:.2f}")
            print(f"     clase más probable por cuadro: {cuenta}; seguros (>= {v2.umbral:g}): {rr.get('votos')}")
            print(f"     puntajes: {fmt(rr['probs'])}")
            if dibujo is not None:
                grosor = 3 if nombre == "chico" else 6
                for q, p in zip(usar, probs):
                    i = int(p.argmax())
                    cv2.rectangle(dibujo, (q["x"] + grosor, q["y"] + grosor), (q["x"] + q["w"] - grosor, q["y"] + q["h"] - grosor),
                                  COLOR[cl[i]], grosor)
                    cv2.putText(dibujo, f"{cl[i][:4]} {p[i]:.2f}", (q["x"] + 10, q["y"] + (30 if nombre == "chico" else 70)),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.8, COLOR[cl[i]], 2)
        if dibujo is not None:
            destino = salida / (f.stem + "_cuadros.jpg")
            cv2.imwrite(str(destino), dibujo, [cv2.IMWRITE_JPEG_QUALITY, 85])
            print(f"  cuadros dibujados en {destino} (delgados: chico; gruesos: grande; verde sana, rojo Sigatoka, "
                  f"amarillo otra condición, gris sin hoja)")

        if not args.comparar:
            continue
        rv = v2.predecir_bgr(img, "imagen")
        print(f"  Solo referencia, no se usa: v2 foto completa {rv['clase']} {rv['confianza']:.2f} | {fmt(rv['probs'])}")
        if v1 is not None:
            r1 = v1.predecir_bgr(img, "imagen")
            print(f"  Solo referencia, no se usa: v1 foto completa {r1['clase']} {r1['confianza']:.2f} | {fmt(r1['probs'])}")


if __name__ == "__main__":
    main()
