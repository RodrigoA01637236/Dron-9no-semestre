"""Datos de la estación de tierra: base SQLite, GPS de las fotos e importación.

Todo vive en data/estacion/ (fuera de git): la base de datos, las fotos
importadas, sus miniaturas, los modelos activados y los entrenamientos.
"""
import hashlib
import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

import cv2

RAIZ = Path(__file__).resolve().parent.parent
DIR = RAIZ / "data" / "estacion"
DB = DIR / "estacion.db"
FOTOS = DIR / "fotos"
MINIS = DIR / "miniaturas"
MODELOS = DIR / "modelos"
ENTRENAMIENTOS = DIR / "entrenamientos"
DATASET_BASE = RAIZ / "data" / "dataset"
MODELO_INICIAL = RAIZ / "vision" / "models" / "sigatoka_cls_v1.onnx"

EXT_IMG = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
DESCARTAR = "_descartar"  # etiqueta humana: la foto no sirve (borrosa, sin hoja...)

CATEGORIAS_INICIALES = [
    ("sana", "Sana", "#2e9e44"),
    ("sigatoka", "Sigatoka", "#d7263d"),
    ("otra_condicion", "Otra condición", "#f0a202"),
]

ESQUEMA = """
CREATE TABLE IF NOT EXISTS fotos (
    id INTEGER PRIMARY KEY,
    vuelo TEXT NOT NULL,
    archivo TEXT NOT NULL,
    lat REAL, lon REAL, alt REAL,
    fecha TEXT,
    pred TEXT, conf REAL, modelo_version INTEGER,
    etiqueta TEXT, revisor TEXT, fecha_etiqueta TEXT,
    holdout INTEGER NOT NULL DEFAULT 0,
    importada TEXT NOT NULL,
    UNIQUE (vuelo, archivo)
);
CREATE TABLE IF NOT EXISTS categorias (
    clave TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    color TEXT NOT NULL,
    orden INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS modelos (
    version INTEGER PRIMARY KEY,
    ruta TEXT NOT NULL,
    clases TEXT NOT NULL,
    creado TEXT NOT NULL,
    top1_test REAL,
    acc_campo REAL, n_campo INTEGER,
    acc_campo_anterior REAL,
    activo INTEGER NOT NULL DEFAULT 0,
    notas TEXT
);
CREATE TABLE IF NOT EXISTS entrenamientos (
    id INTEGER PRIMARY KEY,
    inicio TEXT NOT NULL, fin TEXT,
    estado TEXT NOT NULL,
    carpeta TEXT NOT NULL,
    epocas INTEGER,
    resumen TEXT,
    modelo_version INTEGER
);
"""


def conectar() -> sqlite3.Connection:
    DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB, timeout=30, check_same_thread=False)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA journal_mode=WAL")
    return con


def inicializar() -> None:
    for d in (FOTOS, MINIS, MODELOS, ENTRENAMIENTOS):
        d.mkdir(parents=True, exist_ok=True)
    with conectar() as con:
        con.executescript(ESQUEMA)
        if con.execute("SELECT COUNT(*) FROM categorias").fetchone()[0] == 0:
            con.executemany(
                "INSERT INTO categorias (clave, nombre, color, orden) VALUES (?, ?, ?, ?)",
                [(c, n, col, i) for i, (c, n, col) in enumerate(CATEGORIAS_INICIALES)],
            )
        # Un entrenamiento "en curso" al arrancar es uno que murió con la app.
        con.execute("UPDATE entrenamientos SET estado='interrumpido' WHERE estado='en_curso'")
        if con.execute("SELECT COUNT(*) FROM modelos").fetchone()[0] == 0 and MODELO_INICIAL.exists():
            registrar_modelo(con, MODELO_INICIAL, activo=True, notas="Modelo baseline (datos públicos)")


def registrar_modelo(con, ruta_onnx: Path, activo=False, notas="", top1=None,
                     acc_campo=None, n_campo=None, acc_anterior=None) -> int:
    """Copia ONNX + JSON a data/estacion/modelos/vN/ y lo registra."""
    version = (con.execute("SELECT MAX(version) FROM modelos").fetchone()[0] or 0) + 1
    destino = MODELOS / f"v{version}"
    destino.mkdir(parents=True, exist_ok=True)
    onnx = destino / f"modelo_v{version}.onnx"
    shutil.copy2(ruta_onnx, onnx)
    shutil.copy2(Path(ruta_onnx).with_suffix(".json"), onnx.with_suffix(".json"))
    meta = json.loads(onnx.with_suffix(".json").read_text(encoding="utf-8"))
    if top1 is None:
        top1 = meta.get("top1_test")
    if activo:
        con.execute("UPDATE modelos SET activo=0")
    con.execute(
        "INSERT INTO modelos (version, ruta, clases, creado, top1_test, acc_campo, n_campo,"
        " acc_campo_anterior, activo, notas) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (version, str(onnx.relative_to(RAIZ)), json.dumps(meta["classes"]),
         ahora(), top1, acc_campo, n_campo, acc_anterior, int(activo), notas),
    )
    return version


def ahora() -> str:
    return datetime.now().isoformat(timespec="seconds")


def es_holdout(vuelo: str, archivo: str) -> int:
    """~20 % de las fotos etiquetadas se apartan para medir el modelo en campo.
    Es determinista: la misma foto siempre cae del mismo lado, y nunca se entrena con ella."""
    h = hashlib.sha1(f"{vuelo}/{archivo}".encode("utf-8")).hexdigest()
    return int(int(h, 16) % 5 == 0)


# ---------------------------------------------------------------- GPS

def _a_grados(valor, ref) -> float | None:
    try:
        g, m, s = (float(x) for x in valor)
    except (TypeError, ValueError):
        return None
    dec = g + m / 60 + s / 3600
    return -dec if ref in ("S", "W") else dec


def gps_exif(ruta: Path) -> dict:
    """Coordenadas y fecha del EXIF (celular, GoPro, cámaras con GPS)."""
    try:
        from PIL import Image
        with Image.open(ruta) as im:
            exif = im.getexif()
            gps = exif.get_ifd(0x8825)
            fecha = exif.get_ifd(0x8769).get(0x9003) or exif.get(0x0132)
    except Exception:
        return {}
    out = {}
    if gps.get(2) and gps.get(4):
        lat, lon = _a_grados(gps[2], gps.get(1)), _a_grados(gps[4], gps.get(3))
        if lat is not None and lon is not None and not (lat == 0 and lon == 0):
            out.update(lat=lat, lon=lon)
            if gps.get(6) is not None:
                try:
                    out["alt"] = float(gps[6])
                except (TypeError, ValueError):
                    pass
    if fecha:
        out["fecha"] = str(fecha).replace(":", "-", 2).replace(" ", "T")
    return out


def gps_sidecar(ruta_img: Path) -> dict:
    """JSON gemelo que escribe la captura del dron (contrato de docs/04 §5)."""
    side = ruta_img.with_suffix(".json")
    if not side.exists():
        return {}
    try:
        d = json.loads(side.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    out = {"fecha": d.get("ts")}
    if d.get("gps_ok", True) and d.get("lat") is not None and d.get("lon") is not None:
        out.update(lat=float(d["lat"]), lon=float(d["lon"]))
        alt = d.get("alt_rel_m", d.get("alt"))
        if alt is not None:
            out["alt"] = float(alt)
    return out


def leer_gps(ruta_img: Path) -> dict:
    """Prioridad: sidecar del Pixhawk (preciso y con hora GPS) > EXIF."""
    return gps_sidecar(ruta_img) or gps_exif(ruta_img)


# ---------------------------------------------------------- importación

def carpeta_vuelo(vuelo: str) -> Path:
    return FOTOS / vuelo


def nombre_seguro(texto: str) -> str:
    limpio = "".join(c if c.isalnum() or c in "-_." else "_" for c in texto.strip())
    return limpio.strip("._") or "vuelo"


def crear_miniatura(origen: Path, destino: Path, lado=360) -> None:
    from vision.clasificador import leer_imagen
    img = leer_imagen(origen)
    if img is None:
        return
    h, w = img.shape[:2]
    escala = lado / max(h, w)
    if escala < 1:
        img = cv2.resize(img, (int(w * escala), int(h * escala)), interpolation=cv2.INTER_AREA)
    destino.parent.mkdir(parents=True, exist_ok=True)
    ok, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 82])
    if ok:
        buf.tofile(str(destino))


def procesar_vuelo(con, vuelo: str, clasificador, version) -> dict:
    """Registra en la base todas las fotos nuevas de la carpeta del vuelo:
    GPS, miniatura y predicción del modelo activo."""
    carpeta = carpeta_vuelo(vuelo)
    existentes = {r[0] for r in con.execute("SELECT archivo FROM fotos WHERE vuelo=?", (vuelo,))}
    nuevas = con_gps = 0
    ids = []
    for ruta in sorted(carpeta.iterdir()):
        if ruta.suffix.lower() not in EXT_IMG or ruta.name in existentes:
            continue
        g = leer_gps(ruta)
        crear_miniatura(ruta, MINIS / vuelo / (ruta.stem + ".jpg"))
        pred = clasificador.predecir(ruta) if clasificador else None
        cur = con.execute(
            "INSERT INTO fotos (vuelo, archivo, lat, lon, alt, fecha, pred, conf, modelo_version,"
            " holdout, importada) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (vuelo, ruta.name, g.get("lat"), g.get("lon"), g.get("alt"), g.get("fecha"),
             pred and pred["clase"], pred and pred["confianza"], version if pred else None,
             es_holdout(vuelo, ruta.name), ahora()),
        )
        nuevas += 1
        con_gps += "lat" in g
        ids.append(cur.lastrowid)
    con.commit()
    return {"nuevas": nuevas, "con_gps": con_gps, "ids": ids}
