"""Reentrenamiento desde la estación de tierra.

1. Arma un dataset train/val/test = dataset base público (data/dataset) + las
   fotos etiquetadas por humanos. Las fotos marcadas como "holdout" (≈20 %)
   NUNCA entran a train/val: son el examen de campo.
2. Corre vision/train/train_cls.py en un proceso aparte (el mismo script de
   siempre), guardando su salida en un log que la página va mostrando.
3. Al terminar, mide el modelo nuevo y el activo sobre el examen de campo y
   lo registra como candidato. Activarlo es una decisión humana (botón).
"""
import os
import random
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

from datos import (DATASET_BASE, DESCARTAR, ENTRENAMIENTOS, EXT_IMG, RAIZ, ahora,
                   carpeta_vuelo, conectar, registrar_modelo)

MIN_POR_CLASE = 15  # una categoría nueva necesita al menos esto para entrenarse
_LOCK = threading.Lock()
_ESTADO = {"activo": False}


def _enlazar(origen: Path, destino: Path) -> None:
    """Hardlink (instantáneo, no ocupa espacio) y si no se puede, copia."""
    destino.parent.mkdir(parents=True, exist_ok=True)
    if destino.exists():
        return
    try:
        os.link(origen, destino)
    except OSError:
        shutil.copy2(origen, destino)


def resumen_datos(con) -> list[dict]:
    """Imágenes disponibles por categoría: base pública y etiquetas de campo."""
    filas = []
    for cat in con.execute("SELECT clave, nombre, color FROM categorias ORDER BY orden"):
        base = 0
        for split in ("train", "val", "test"):
            d = DATASET_BASE / split / cat["clave"]
            if d.is_dir():
                base += sum(1 for p in d.iterdir() if p.suffix.lower() in EXT_IMG)
        n = con.execute("SELECT SUM(holdout=0), SUM(holdout=1) FROM fotos WHERE etiqueta=?",
                        (cat["clave"],)).fetchone()
        campo, examen = n[0] or 0, n[1] or 0
        filas.append({"clave": cat["clave"], "nombre": cat["nombre"], "color": cat["color"],
                      "base": base, "campo": campo, "examen": examen,
                      "entrenable": base + campo + examen >= MIN_POR_CLASE})
    return filas


def armar_dataset(con, destino: Path, semilla=42) -> dict:
    rng = random.Random(semilla)
    clases = [f["clave"] for f in resumen_datos(con) if f["entrenable"]]
    conteo = {}
    for clase in clases:
        partes = {"train": [], "val": [], "test": []}
        for split in partes:
            d = DATASET_BASE / split / clase
            if d.is_dir():
                partes[split] += [p for p in sorted(d.iterdir()) if p.suffix.lower() in EXT_IMG]
        campo = [carpeta_vuelo(r["vuelo"]) / r["archivo"] for r in con.execute(
            "SELECT vuelo, archivo FROM fotos WHERE etiqueta=? AND holdout=0", (clase,))]
        examen = [carpeta_vuelo(r["vuelo"]) / r["archivo"] for r in con.execute(
            "SELECT vuelo, archivo FROM fotos WHERE etiqueta=? AND holdout=1", (clase,))]
        rng.shuffle(campo)
        corte = max(1, len(campo) // 5) if campo else 0
        partes["val"] += campo[:corte]
        partes["train"] += campo[corte:]
        partes["test"] += examen
        # Ultralytics necesita ejemplos de cada clase en los tres splits.
        for split in ("val", "test"):
            if not partes[split] and len(partes["train"]) > 2:
                partes[split].append(partes["train"].pop())
        for split, rutas in partes.items():
            for i, ruta in enumerate(rutas):
                if ruta.exists():
                    _enlazar(ruta, destino / split / clase / f"{i:05d}_{ruta.name}")
        conteo[clase] = {s: len(r) for s, r in partes.items()}
    return conteo


def examen_de_campo(con, ruta_onnx) -> tuple[float | None, int]:
    """Exactitud de un modelo sobre las fotos holdout etiquetadas por humanos."""
    from vision.clasificador import Clasificador
    filas = con.execute("SELECT vuelo, archivo, etiqueta FROM fotos WHERE holdout=1 AND"
                        " etiqueta IS NOT NULL AND etiqueta != ?", (DESCARTAR,)).fetchall()
    if not filas:
        return None, 0
    clf = Clasificador(ruta_onnx)
    aciertos = total = 0
    for f in filas:
        pred = clf.predecir(carpeta_vuelo(f["vuelo"]) / f["archivo"])
        if pred is None:
            continue
        total += 1
        aciertos += pred["clase"] == f["etiqueta"]
    return (aciertos / total if total else None), total


def estado() -> dict:
    with _LOCK:
        e = dict(_ESTADO)
    if e.get("log"):
        try:
            texto = Path(e["log"]).read_text(encoding="utf-8", errors="replace")[-6000:]
            lineas = [l.strip() for l in texto.replace("\r", "\n").split("\n") if l.strip()]
            e["ultimas"] = lineas[-14:]
        except OSError:
            e["ultimas"] = []
        e["transcurrido_s"] = int(time.time() - e["t0"])
    e.pop("proc", None)
    return e


def iniciar(epocas: int) -> tuple[bool, str]:
    with _LOCK:
        if _ESTADO.get("activo"):
            return False, "Ya hay un entrenamiento en curso."
        _ESTADO.clear()
        _ESTADO.update(activo=True, fase="Preparando el dataset…", t0=time.time())
    threading.Thread(target=_trabajo, args=(epocas,), daemon=True).start()
    return True, "Entrenamiento iniciado."


def _trabajo(epocas: int) -> None:
    con = conectar()
    sello = time.strftime("%Y%m%d_%H%M%S")
    carpeta = ENTRENAMIENTOS / sello
    cur = con.execute("INSERT INTO entrenamientos (inicio, estado, carpeta, epocas) VALUES (?,?,?,?)",
                      (ahora(), "en_curso", str(carpeta.relative_to(RAIZ)), epocas))
    ent_id = cur.lastrowid
    con.commit()
    try:
        conteo = armar_dataset(con, carpeta / "dataset")
        if len(conteo) < 2:
            raise RuntimeError("Se necesitan al menos 2 categorías con datos para entrenar.")
        log = carpeta / "entrenamiento.log"
        with _LOCK:
            _ESTADO.update(fase="Entrenando… (la computadora debe quedarse encendida)",
                           log=str(log), conteo=conteo)
        cmd = [sys.executable, str(RAIZ / "vision" / "train" / "train_cls.py"),
               "--data", str(carpeta / "dataset"), "--epochs", str(epocas),
               "--imgsz", "384", "--batch", "32", "--workers", "2",
               "--project", str(carpeta), "--name", "corrida"]
        entorno = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
        with open(log, "w", encoding="utf-8") as salida:
            proc = subprocess.run(cmd, cwd=RAIZ, stdout=salida, stderr=subprocess.STDOUT, env=entorno)
        onnx = carpeta / "corrida" / "weights" / "best.onnx"
        if proc.returncode != 0 or not onnx.exists():
            raise RuntimeError("El entrenamiento falló; revisa el log de abajo.")

        with _LOCK:
            _ESTADO.update(fase="Midiendo el modelo nuevo con el examen de campo…")
        acc_nuevo, n = examen_de_campo(con, onnx)
        activo = con.execute("SELECT version, ruta FROM modelos WHERE activo=1").fetchone()
        acc_actual = None
        if activo:
            acc_actual, n_actual = examen_de_campo(con, RAIZ / activo["ruta"])
            con.execute("UPDATE modelos SET acc_campo=?, n_campo=? WHERE version=?",
                        (acc_actual, n_actual, activo["version"]))
        version = registrar_modelo(con, onnx, activo=False, acc_campo=acc_nuevo, n_campo=n,
                                   acc_anterior=acc_actual,
                                   notas=f"Reentrenado {sello} ({epocas} épocas)")
        con.execute("UPDATE entrenamientos SET fin=?, estado='terminado', modelo_version=?,"
                    " resumen=? WHERE id=?", (ahora(), version, str(conteo), ent_id))
        con.commit()
        with _LOCK:
            _ESTADO.update(activo=False, fase="Terminado", version=version)
    except Exception as exc:  # el error se muestra en la página
        con.execute("UPDATE entrenamientos SET fin=?, estado='fallido', resumen=? WHERE id=?",
                    (ahora(), str(exc), ent_id))
        con.commit()
        with _LOCK:
            _ESTADO.update(activo=False, fase="Error", error=str(exc))
    finally:
        con.close()
