"""Entrenamiento de una noche (~8 h) del modelo por parches, de principio a fin.

Pasos (cada uno se salta si ya está hecho, así que si algo se interrumpe se vuelve a
correr el mismo comando y sigue donde se quedó):

 1. data/dataset_v2: junta las fuentes públicas sin duplicados (preparar_datos.py). ~10-20 min
 2. data/parches_v2: parches de hoja + clase sin_hoja, equilibrados y alterados
    (hacer_parches.py, con el v1 como maestro).                                   ~30-60 min
 3. Modelo principal yolo11s-cls (más exacto), --horas-s horas.               3.5 h por defecto
 4. Modelo ligero yolo11n-cls (más rápido en la Jetson), --horas-n horas.    1.25 h por defecto
 5. Calibra y evalúa los dos con fotos completas (calibrar.py, hasta 500 fotos
    por clase en cada prueba).                                                      ~45-60 min
 Total: ~7-8 h.
 6. Resumen: el mejor se copia a vision/models/sigatoka_cls_v2.* y se anota en
    vision/train/experiments.md. Revisa el reporte antes de subirlo.

Uso (desde la raíz del repo, con el venv activo y la laptop conectada a la corriente):
    python vision/train/entrenar_noche.py
    python vision/train/entrenar_noche.py --horas-s 4 --horas-n 1.5 --batch-s 48
    python vision/train/entrenar_noche.py --solo-s            # solo el modelo principal

Todo queda en runs/noche/ (log: runs/noche/noche.log). Para empezar de cero, borra
runs/noche (y data/parches_v2 si cambiaste las fuentes). Ver vision/GUIA-PARCHES.md.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from datetime import date, datetime, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
TRAIN = RAIZ / "vision" / "train"
MODELOS = RAIZ / "vision" / "models"


class Registro:
    def __init__(self, ruta: Path):
        ruta.parent.mkdir(parents=True, exist_ok=True)
        self.f = open(ruta, "a", encoding="utf-8")

    def __call__(self, texto: str = "") -> None:
        linea = f"[{datetime.now():%H:%M:%S}] {texto}" if texto else ""
        print(linea, flush=True)
        self.f.write(linea + "\n")
        self.f.flush()


def correr(log: Registro, script: str, *args: str) -> None:
    """Corre un script de vision/train/ y copia su salida a la pantalla y al log."""
    cmd = [sys.executable, "-u", str(TRAIN / script), *args]
    log(f"$ {script} {' '.join(args)}")
    entorno = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")  # acentos en la consola de Windows
    with subprocess.Popen(cmd, cwd=RAIZ, env=entorno, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                          text=True, encoding="utf-8", errors="replace", bufsize=1) as proc:
        for linea in proc.stdout:
            linea = linea.rstrip()
            print(linea, flush=True)
            log.f.write(linea + "\n")
        proc.wait()
    log.f.flush()
    if proc.returncode != 0:
        raise SystemExit(f"{script} falló (código {proc.returncode}). Revisa {log.f.name}; "
                         "al corregirlo, vuelve a correr el mismo comando y sigue donde se quedó.")


def entrenamiento_completo(pt: Path) -> bool:
    """best.pt de una corrida que sí terminó: ultralytics le quita el optimizador al final."""
    if not pt.exists():
        return False
    try:
        import torch
        return torch.load(pt, map_location="cpu", weights_only=False).get("optimizer") is None
    except Exception:  # noqa: BLE001
        return False


def entrenar(log: Registro, carpeta: Path, nombre: str, base: str, horas: float, batch: int,
             workers: int, parches: Path) -> Path:
    destino = carpeta / nombre
    onnx = destino / "weights" / "best.onnx"
    if onnx.exists():
        log(f"{nombre}: ya entrenado ({onnx}); se salta.")
        return onnx
    if entrenamiento_completo(destino / "weights" / "best.pt"):
        # Terminó de entrenar pero falló después (la prueba en test o la exportación):
        # no se repiten horas de entrenamiento, solo se exporta.
        log(f"{nombre}: ya entrenado, falta el ONNX; exportando {destino / 'weights' / 'best.pt'}")
        from ultralytics import YOLO
        YOLO(str(destino / "weights" / "best.pt")).export(format="onnx", imgsz=384, opset=17, dynamic=True)
        if onnx.exists():
            return onnx
        raise SystemExit(f"No se pudo exportar {onnx}. Revisa el log.")
    if destino.exists():
        shutil.rmtree(destino)  # corrida a medias: se repite completa
    log(f"{nombre}: entrenando {base} por {horas} h (termina ~{datetime.now() + timedelta(hours=horas):%H:%M})")
    correr(log, "train_cls.py", "--data", str(parches), "--model", base, "--time", str(horas),
           "--epochs", "300", "--patience", "15", "--imgsz", "384", "--batch", str(batch),
           "--workers", str(workers), "--flipud", "0.5", "--erasing", "0.1",
           "--project", str(carpeta), "--name", nombre)
    if not onnx.exists():
        raise SystemExit(f"No apareció {onnx}. Revisa el log.")
    return onnx


def metrica(meta: dict, prueba: str = "test") -> dict:
    if prueba == "test":
        return (meta.get("prueba_fotos_test") or {}).get("v2_parches") or {}
    return ((meta.get("pruebas_externas") or {}).get(prueba) or {}).get("v2_parches") or {}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--carpeta", default="runs/noche")
    ap.add_argument("--datos", default="data/dataset_v2")
    ap.add_argument("--parches", default="data/parches_v2")
    ap.add_argument("--horas-s", type=float, default=3.5, help="horas para yolo11s-cls (modelo principal)")
    ap.add_argument("--horas-n", type=float, default=1.25, help="horas para yolo11n-cls (modelo ligero)")
    ap.add_argument("--limite", type=int, default=500,
                    help="fotos por clase en cada prueba de calibrar.py (0 = todas; más lento)")
    ap.add_argument("--batch-s", type=int, default=64, help="si sale 'CUDA out of memory', usa 32")
    ap.add_argument("--batch-n", type=int, default=128, help="si sale 'CUDA out of memory', usa 64")
    ap.add_argument("--workers", type=int, default=2,
                    help="procesos que cargan fotos (y otros tantos para validar). Con 16 GB de RAM, 2; "
                         "con 32 GB se puede subir a 6")
    ap.add_argument("--solo-s", action="store_true", help="no entrenar el modelo ligero")
    ap.add_argument("--meta", type=float, default=0.90)
    args = ap.parse_args()

    carpeta = (RAIZ / args.carpeta).resolve()
    datos, parches = RAIZ / args.datos, RAIZ / args.parches
    log = Registro(carpeta / "noche.log")
    t0 = time.time()
    log("=" * 60)
    log(f"Entrenamiento de una noche · {datetime.now():%Y-%m-%d %H:%M}")

    try:
        import torch
        gpu = torch.cuda.get_device_name(0) if torch.cuda.is_available() else None
    except Exception:  # noqa: BLE001
        gpu = None
    log(f"GPU: {gpu or 'NINGUNA: en CPU tardará muchísimo; revisa GUIA-MODELO.md (Habilitar la GPU)'}")
    total = args.horas_s + (0 if args.solo_s else args.horas_n) + 2.0
    log(f"Plan: datos y parches ~1 h, entrenar {args.horas_s} h"
        f"{'' if args.solo_s else f' + {args.horas_n} h'}, calibrar ~1 h. "
        f"Termina hacia las {datetime.now() + timedelta(hours=total):%H:%M} (aprox.).")

    # 1. Dataset
    if datos.exists():
        log(f"1. {args.datos} ya existe; se salta (bórralo para rehacerlo con fuentes nuevas).")
    else:
        log("1. Juntando las fuentes públicas")
        correr(log, "preparar_datos.py", "--out", str(datos))

    # 2. Parches
    if parches.exists():
        log(f"2. {args.parches} ya existe; se salta (bórralo para rehacerlo).")
    else:
        log("2. Cortando parches")
        maestro = MODELOS / "sigatoka_cls_v1.onnx"
        extra = ["--maestro", str(maestro)] if maestro.exists() else []
        correr(log, "hacer_parches.py", "--entrada", str(datos), "--salida", str(parches),
               "--equilibrar", *extra)

    # 3-4. Entrenar
    modelos = {"s": entrenar(log, carpeta, "s", "yolo11s-cls.pt", args.horas_s, args.batch_s, args.workers, parches)}
    if not args.solo_s:
        modelos["n"] = entrenar(log, carpeta, "n", "yolo11n-cls.pt", args.horas_n, args.batch_n, args.workers, parches)

    # 5. Calibrar y evaluar
    metas = {}
    for nombre, onnx in modelos.items():
        salida = carpeta / f"calibrado_{nombre}" / "sigatoka_cls_v2.onnx"
        if not salida.with_suffix(".json").exists():
            log(f"5. Calibrando y evaluando el modelo {nombre}")
            correr(log, "calibrar.py", "--onnx", str(onnx), "--parches", str(parches),
                   "--imagenes", str(datos), "--salida", str(salida), "--meta", str(args.meta),
                   "--limite", str(args.limite))
        metas[nombre] = (salida, json.loads(salida.with_suffix(".json").read_text(encoding="utf-8")))

    # 6. Resumen y elección
    log("")
    log("6. Resumen (fotos completas de test; el modelo decide por parches)")
    pruebas = ["test"] + sorted({k for _, m in metas.values() for k in (m.get("pruebas_externas") or {})})
    for nombre, (_, m) in metas.items():
        partes = []
        for p in pruebas:
            r = metrica(m, p)
            if r.get("n"):
                partes.append(f"{p} {r['exactitud']:.1%} ({r['n']})")
        f1 = metrica(m).get("f1_macro")
        log(f"   yolo11{nombre}-cls · F1 macro test {f1:.3f} · " + " · ".join(partes) if f1 is not None
            else f"   yolo11{nombre}-cls · sin datos de test")

    def puntaje(nombre):
        # F1 de las fotos de hoja y, si existe, el de las fotos aéreas del dron (pesan igual:
        # el dron es para lo que se usa)
        m = metas[nombre][1]
        f1s = [metrica(m).get("f1_macro") or 0.0]
        aereo = metrica(m, "test_colombia_uav").get("f1_macro")
        if aereo is not None:
            f1s.append(aereo)
        return sum(f1s) / len(f1s)

    elegido = max(metas, key=puntaje)
    if "n" in metas and elegido == "s" and puntaje("s") - puntaje("n") < 0.01:
        elegido = "n"  # casi igual de bueno y ~3 veces más rápido en la Jetson
    salida, meta = metas[elegido]
    r = metrica(meta)
    for ext in (".onnx", ".json"):
        shutil.copy2(salida.with_suffix(ext), MODELOS / f"sigatoka_cls_v2{ext}")
    shutil.copy2(salida.with_name(salida.stem + "_evaluacion.md"), MODELOS / "sigatoka_cls_v2_evaluacion.md")
    cumple = r.get("exactitud", 0) >= args.meta
    log(f"Elegido: yolo11{elegido}-cls -> vision/models/sigatoka_cls_v2.onnx "
        f"(exactitud test {r.get('exactitud', 0):.1%}, meta {args.meta:.0%}: {'CUMPLE' if cumple else 'NO CUMPLE'})")

    # Fila en experiments.md
    resumen = json.loads((datos / "resumen.json").read_text(encoding="utf-8")) if (datos / "resumen.json").exists() else {}
    tren = (resumen.get("conteo") or {}).get("train", {})
    fila = (f"| noche | {date.today().isoformat()} | v2_publico ({', '.join(f'{k} {v}' for k, v in tren.items())} fotos en train)"
            f" | yolo11{elegido}-cls por parches | 384 | {args.horas_s if elegido == 's' else args.horas_n} h | "
            f"{args.batch_s if elegido == 's' else args.batch_n} | **{r.get('exactitud', 0):.3f}** (fotos) | "
            f"{', '.join(f'{k}={v:.2f}' for k, v in (r.get('recall') or {}).items())} (recall) | {meta.get('umbral_confianza')} | "
            f"runs/noche/ | entrenar_noche.py; T={meta.get('temperatura')}; ver sigatoka_cls_v2_evaluacion.md |\n")
    with open(TRAIN / "experiments.md", "a", encoding="utf-8") as fh:
        fh.write(fila)
    log("Fila agregada a vision/train/experiments.md")

    horas = (time.time() - t0) / 3600
    log(f"Listo en {horas:.1f} h. Revisa vision/models/sigatoka_cls_v2_evaluacion.md y, si te convence:")
    log("  git add vision/models/sigatoka_cls_v2.* vision/train/experiments.md data/manifests/v2_publico.csv")
    log('  git commit -m "Modelo v2 por parches (entrenamiento de una noche)"')
    log("  git push")


if __name__ == "__main__":
    main()
