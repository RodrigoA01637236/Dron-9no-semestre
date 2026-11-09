"""Reentrenamiento desde la estación de tierra.

Dos tipos de modelo, que se pueden entrenar por separado o uno después del otro:

- "foto": el de siempre (como el v1). Clasifica la foto completa reducida a 384 px.
- "parches": el v2 (vision/GUIA-PARCHES.md). Clasifica trozos de hoja a resolución
  completa y junta el veredicto de la foto.

Pasos:
1. Arma un dataset de fotos train/val/test = fotos públicas (data/dataset_v2 si existe,
   si no data/dataset) + las fotos etiquetadas por humanos. Las fotos marcadas como
   "holdout" (≈20 %) NUNCA entran a train/val: son el examen de campo.
2. "foto": corre vision/train/train_cls.py con esas fotos.
   "parches": corta parches (hacer_parches.py), entrena con ellos (train_cls.py) y calibra
   umbral y temperatura (calibrar.py). Cada paso es un proceso aparte y su salida va al
   mismo log, que la página va mostrando.
3. Al terminar, mide el modelo nuevo y el activo con el examen de campo y lo registra
   como candidato. Activarlo es una decisión humana (botón).
"""
import os
import random
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path

from datos import (DESCARTAR, ENTRENAMIENTOS, EXT_IMG, MODELO_INICIAL, RAIZ, ahora,
                   carpeta_vuelo, conectar, dataset_base, registrar_modelo)

MIN_POR_CLASE = 15  # una categoría nueva necesita al menos esto para entrenarse
TIPOS = {"foto": "Foto completa", "parches": "Por parches de hoja"}
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
    base_dir = dataset_base()
    filas = []
    for cat in con.execute("SELECT clave, nombre, color FROM categorias ORDER BY orden"):
        base = 0
        for split in ("train", "val", "test"):
            d = base_dir / split / cat["clave"]
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
    base_dir = dataset_base()
    clases = [f["clave"] for f in resumen_datos(con) if f["entrenable"]]
    conteo = {}
    for clase in clases:
        partes = {"train": [], "val": [], "test": []}
        for split in partes:
            d = base_dir / split / clase
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
    """Exactitud de un modelo sobre las fotos holdout etiquetadas por humanos.
    Cada modelo predice en su propio modo (foto completa o por parches)."""
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


def iniciar(epocas: int, tipo: str = "foto") -> tuple[bool, str]:
    tipos = list(TIPOS) if tipo == "ambos" else [tipo]
    if any(t not in TIPOS for t in tipos):
        return False, "Tipo de modelo desconocido."
    with _LOCK:
        if _ESTADO.get("activo"):
            return False, "Ya hay un entrenamiento en curso."
        _ESTADO.clear()
        _ESTADO.update(activo=True, fase="Preparando el dataset…", t0=time.time(), versiones=[])
    threading.Thread(target=_trabajo, args=(epocas, tipos), daemon=True).start()
    return True, "Entrenamiento iniciado."


def _fase(texto: str, **extra) -> None:
    with _LOCK:
        _ESTADO.update(fase=texto, **extra)


def _correr(script: str, args: list[str], log: Path) -> None:
    """Corre un script de vision/train/ en un proceso aparte; su salida se suma al log."""
    cmd = [sys.executable, str(RAIZ / "vision" / "train" / script), *args]
    entorno = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUNBUFFERED="1")
    with open(log, "a", encoding="utf-8") as salida:
        salida.write(f"\n===== {script} {' '.join(args)}\n")
        salida.flush()
        proc = subprocess.run(cmd, cwd=RAIZ, stdout=salida, stderr=subprocess.STDOUT, env=entorno)
    if proc.returncode != 0:
        raise RuntimeError(f"{script} falló; revisa el log de abajo.")


def _entrenar_foto(carpeta: Path, epocas: int, log: Path, prefijo: str) -> Path:
    _fase(f"{prefijo}Entrenando el modelo de foto completa… (la computadora debe quedarse encendida)")
    _correr("train_cls.py", ["--data", str(carpeta / "fotos"), "--epochs", str(epocas),
                             "--imgsz", "384", "--batch", "32", "--workers", "2",
                             "--project", str(carpeta), "--name", "foto"], log)
    return carpeta / "foto" / "weights" / "best.onnx"


def _entrenar_parches(carpeta: Path, epocas: int, log: Path, prefijo: str, comparar: Path | None) -> Path:
    _fase(f"{prefijo}Cortando las fotos en parches de hoja… (unos 20-40 minutos)")
    args = ["--entrada", str(carpeta / "fotos"), "--salida", str(carpeta / "parches")]
    if MODELO_INICIAL.exists():
        args += ["--maestro", str(MODELO_INICIAL)]  # el v1 limpia las etiquetas de los parches
    _correr("hacer_parches.py", args, log)

    _fase(f"{prefijo}Entrenando el modelo por parches… (la computadora debe quedarse encendida)")
    _correr("train_cls.py", ["--data", str(carpeta / "parches"), "--model", "yolo11n-cls.pt",
                             "--epochs", str(epocas), "--imgsz", "384", "--batch", "32", "--workers", "2",
                             "--erasing", "0.1", "--project", str(carpeta), "--name", "parches"], log)

    _fase(f"{prefijo}Calibrando el umbral y comparando con el modelo en uso…")
    salida = carpeta / "parches_calibrado" / "modelo_parches.onnx"
    args = ["--onnx", str(carpeta / "parches" / "weights" / "best.onnx"),
            "--parches", str(carpeta / "parches"), "--imagenes", str(carpeta / "fotos"),
            "--salida", str(salida), "--limite", "300"]
    args += ["--comparar", str(comparar)] if comparar else ["--comparar", ""]
    _correr("calibrar.py", args, log)
    return salida


def _trabajo(epocas: int, tipos: list[str]) -> None:
    con = conectar()
    sello = time.strftime("%Y%m%d_%H%M%S")
    carpeta = ENTRENAMIENTOS / sello
    cur = con.execute("INSERT INTO entrenamientos (inicio, estado, carpeta, epocas) VALUES (?,?,?,?)",
                      (ahora(), "en_curso", str(carpeta.relative_to(RAIZ)), epocas))
    ent_id = cur.lastrowid
    con.commit()
    versiones = []
    try:
        conteo = armar_dataset(con, carpeta / "fotos")
        if len(conteo) < 2:
            raise RuntimeError("Se necesitan al menos 2 categorías con datos para entrenar.")
        log = carpeta / "entrenamiento.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        log.write_text(f"Fotos para entrenar (base: {dataset_base().relative_to(RAIZ)}): {conteo}\n",
                       encoding="utf-8")
        _fase("Preparando…", log=str(log), conteo=conteo)

        for n, tipo in enumerate(tipos, 1):
            prefijo = f"{n} de {len(tipos)} · " if len(tipos) > 1 else ""
            activo = con.execute("SELECT version, ruta FROM modelos WHERE activo=1").fetchone()
            ruta_activo = RAIZ / activo["ruta"] if activo else None
            if tipo == "foto":
                onnx = _entrenar_foto(carpeta, epocas, log, prefijo)
            else:
                onnx = _entrenar_parches(carpeta, epocas, log, prefijo, ruta_activo)
            if not onnx.exists():
                raise RuntimeError(f"No apareció {onnx.name}; revisa el log de abajo.")

            _fase(f"{prefijo}Midiendo el modelo nuevo con el examen de campo…")
            acc_nuevo, n_campo = examen_de_campo(con, onnx)
            acc_actual = None
            if activo:
                acc_actual, n_actual = examen_de_campo(con, ruta_activo)
                con.execute("UPDATE modelos SET acc_campo=?, n_campo=? WHERE version=?",
                            (acc_actual, n_actual, activo["version"]))
            version = registrar_modelo(con, onnx, activo=False, acc_campo=acc_nuevo, n_campo=n_campo,
                                       acc_anterior=acc_actual,
                                       notas=f"{TIPOS[tipo]}: reentrenado {sello} ({epocas} épocas)")
            con.commit()
            versiones.append(version)
            with _LOCK:
                _ESTADO["versiones"] = list(versiones)

        con.execute("UPDATE entrenamientos SET fin=?, estado='terminado', modelo_version=?,"
                    " resumen=? WHERE id=?",
                    (ahora(), versiones[-1], f"{'+'.join(tipos)}: versiones {versiones}; {conteo}", ent_id))
        con.commit()
        _fase("Terminado", activo=False, version=versiones[-1])
    except Exception as exc:  # el error se muestra en la página
        con.execute("UPDATE entrenamientos SET fin=?, estado='fallido', resumen=? WHERE id=?",
                    (ahora(), f"{exc} (versiones creadas: {versiones})", ent_id))
        con.commit()
        _fase("Error", activo=False, error=str(exc))
    finally:
        con.close()
