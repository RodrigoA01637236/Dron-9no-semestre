"""Figura de la evaluación del filtro de hoja, a partir de filtro_hoja_evaluacion.json.

(a) Fotos de hoja que el filtro vuelve "sin hoja" según el umbral, dejando fuera una fuente a la vez.
(b) Imágenes de objetos que siguen pasando como hoja según el umbral.
Las dos para las fotos por cuadros, que es lo que usan el dron y la página. Con --con-foto-completa
agrega la sonda de la foto completa reducida (modo "imagen", que el dron ya no usa desde el 18 de
noviembre). La línea punteada vertical marca el umbral elegido.

Uso (necesita matplotlib, que ya trae el entorno de entrenamiento):
    python vision/train/figura_filtro.py
    python vision/train/figura_filtro.py --entrada vision/models/filtro_hoja_evaluacion.json --salida figura.png
"""
import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

RAIZ = Path(__file__).resolve().parents[2]
AZUL, NARANJA, VERDE, GRIS = "#2a64a8", "#cc8a28", "#17806c", "#6b7280"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--entrada", type=Path, default=RAIZ / "vision/models/filtro_hoja_evaluacion.json")
    ap.add_argument("--salida", type=Path, default=RAIZ / "vision/models/filtro_hoja_evaluacion.png")
    ap.add_argument("--con-foto-completa", action="store_true", help="agrega la sonda de la foto completa (sin uso en el dron)")
    args = ap.parse_args()
    r = json.loads(args.entrada.read_text(encoding="utf-8"))
    umbrales = sorted(float(u) for u in r["loo_foto"])
    clave = {float(u): u for u in r["loo_foto"]}
    elegido = float(r["elegido"])
    n_hojas, n_obj = r["fotos_hoja"], r["objetos_prueba"]

    plt.rcParams.update({"font.size": 10.5, "axes.spines.top": False, "axes.spines.right": False})
    fig, ax = plt.subplots(1, 2, figsize=(10.5, 3.9))
    series = [
        (ax[0], [r["loo_foto"][clave[u]]["total"] for u in umbrales], [r["loo_imagen"][clave[u]]["total"] for u in umbrales],
         f"(a) Leaf photos made non-leaf (of {n_hojas:,})", "Photos, one source held out", None),
        (ax[1], [r["objetos"]["foto"][clave[u]] for u in umbrales], [r["objetos"]["video"][clave[u]] for u in umbrales],
         f"(b) Object images still read as leaf (of {n_obj:,})", "Images never used for training", r["objetos"]["sin_filtro"]),
    ]
    for eje, fotos, video, titulo, etiqueta, sin_filtro in series:
        eje.plot(umbrales, fotos, "o-", color=NARANJA if eje is ax[0] else AZUL, lw=2, label="Photos (patches)")
        if args.con_foto_completa:
            eje.plot(umbrales, video, "s--", color=GRIS, lw=1.5, label="Full image (not used on the drone)")
        for x, y in zip(umbrales, fotos):
            eje.annotate(str(y), (x, y), textcoords="offset points", xytext=(-9 if x == elegido else 0, 7),
                         ha="right" if x == elegido else "center", fontsize=9.5)
        eje.axvline(elegido, color=VERDE, ls=":", lw=1.6)
        eje.set_xticks(umbrales)
        eje.set_xticklabels([f"{u:g}".replace("-", "−") for u in umbrales])
        eje.set_xlabel("Threshold")
        eje.set_ylabel(etiqueta)
        eje.set_title(titulo)
        eje.yaxis.grid(True, color="#eeeeee")
        eje.set_axisbelow(True)
        if sin_filtro is not None:
            eje.axhline(sin_filtro, color=GRIS, ls=":", lw=1.2)
            eje.text((umbrales[1] + umbrales[2]) / 2, sin_filtro * 1.03, f"photos, no filter: {sin_filtro}",
                     color=GRIS, fontsize=9, ha="center")
            eje.set_ylim(0, sin_filtro * 1.15)
        else:
            eje.set_ylim(0, max(max(fotos), max(video) if args.con_foto_completa else 0) * 1.25 + 1)
        eje.legend(frameon=False, fontsize=9, loc="upper left" if eje is ax[0] else "center left")
    ax[0].text(elegido + 0.05, ax[0].get_ylim()[1] * 0.9, f"chosen: {elegido:g}".replace("-", "−"), color=VERDE)
    fig.tight_layout()
    args.salida.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.salida, dpi=200)
    print(f"Figura guardada en {args.salida}")


if __name__ == "__main__":
    main()
