r"""Estación de tierra del dron Sigatoka: mapa, revisión de fotos y reentrenamiento.

Corre en la laptop del equipo y se usa desde el navegador. Flujo:
  1. Importar: subes la carpeta de un vuelo (fotos del dron con su JSON de GPS,
     o fotos de celular/GoPro con GPS en el EXIF). El modelo las diagnostica.
  2. Mapa: cada foto es un punto en el terreno; vista por zonas de % de Sigatoka.
  3. Revisar: un humano confirma o corrige el diagnóstico, empezando por las
     fotos donde el modelo tiene más dudas.
  4. Modelo: botón para reentrenar con esas correcciones y activar el modelo
     nuevo solo si mejora en el examen de campo.
  5. Identificar: subes o tomas la foto de una hoja (o usas la cámara en vivo)
     y el modelo dice si está sana, tiene Sigatoka u otra condición.

Uso (con el venv activo, desde la raíz del repo):
    python ui\estacion.py            # se abre sola en http://localhost:5050
    python ui\estacion.py --red      # para abrirla desde otro equipo del mismo WiFi
O doble clic en ui\Iniciar-Estacion.bat
"""
import argparse
import json
import sys
import threading
import time
import webbrowser
from pathlib import Path

from flask import Flask, abort, jsonify, render_template, request, send_file

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))  # para importar vision.clasificador

import datos  # noqa: E402
import entrenamiento  # noqa: E402
from datos import DESCARTAR, RAIZ, carpeta_vuelo, conectar  # noqa: E402

app = Flask(__name__, template_folder=str(AQUI / "templates"), static_folder=str(AQUI / "static"))
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024**3

_clf = {"version": None, "obj": None}
_reproceso = {"activo": False, "hechas": 0, "total": 0}
_lock = threading.Lock()


def clasificador():
    """Modelo activo (se recarga solo si cambió la versión)."""
    with conectar() as con:
        fila = con.execute("SELECT version, ruta FROM modelos WHERE activo=1").fetchone()
    if not fila:
        return None, None
    with _lock:
        if _clf["version"] != fila["version"]:
            from vision.clasificador import Clasificador
            _clf.update(version=fila["version"], obj=Clasificador(RAIZ / fila["ruta"]))
        return _clf["obj"], _clf["version"]


def foto_dict(f) -> dict:
    return {k: f[k] for k in f.keys()}


# ------------------------------------------------------------------ páginas

@app.get("/")
def inicio():
    return render_template("inicio.html", pagina="inicio")


@app.get("/<any(inicio, mapa, identificar, revisar, galeria, importar, modelo):pagina>")
def pagina(pagina):
    return render_template(f"{pagina}.html", pagina=pagina)


@app.get("/foto/<int:fid>")
def foto(fid):
    with conectar() as con:
        f = con.execute("SELECT vuelo, archivo FROM fotos WHERE id=?", (fid,)).fetchone()
    if not f:
        abort(404)
    return send_file(carpeta_vuelo(f["vuelo"]) / f["archivo"])


@app.get("/mini/<int:fid>")
def mini(fid):
    with conectar() as con:
        f = con.execute("SELECT vuelo, archivo FROM fotos WHERE id=?", (fid,)).fetchone()
    if not f:
        abort(404)
    ruta = datos.MINIS / f["vuelo"] / (Path(f["archivo"]).stem + ".jpg")
    return send_file(ruta if ruta.exists() else carpeta_vuelo(f["vuelo"]) / f["archivo"])


# --------------------------------------------------------------------- API

@app.get("/api/resumen")
def api_resumen():
    with conectar() as con:
        cats = [dict(r) for r in con.execute("SELECT clave, nombre, color FROM categorias ORDER BY orden")]
        vuelos = [dict(r) for r in con.execute(
            "SELECT vuelo, COUNT(*) AS fotos, SUM(lat IS NOT NULL) AS con_gps,"
            " SUM(etiqueta IS NOT NULL) AS revisadas, MAX(importada) AS importada"
            " FROM fotos GROUP BY vuelo ORDER BY importada DESC")]
        mod = con.execute("SELECT version, clases, top1_test, acc_campo, n_campo, creado"
                          " FROM modelos WHERE activo=1").fetchone()
        tot = con.execute("SELECT COUNT(*), SUM(etiqueta IS NOT NULL) FROM fotos").fetchone()
    clf, _ = (None, None)
    umbral = 0.65
    if mod:
        clf, _ = clasificador()
        umbral = clf.umbral if clf else umbral
    # Para la página de inicio: qué tan avanzado va cada paso del flujo.
    with conectar() as con:
        con_gps = con.execute("SELECT COUNT(*) FROM fotos WHERE lat IS NOT NULL").fetchone()[0]
        sigatoka_mapa = con.execute(
            "SELECT COUNT(*) FROM fotos WHERE lat IS NOT NULL AND (etiqueta='sigatoka'"
            " OR (etiqueta IS NULL AND pred='sigatoka' AND conf>=?))", (umbral,)).fetchone()[0]
        nuevas = con.execute("SELECT COUNT(*) FROM fotos WHERE etiqueta IS NOT NULL AND etiqueta!=?"
                             " AND fecha_etiqueta > ?", (DESCARTAR, mod["creado"] if mod else "")).fetchone()[0]
    return jsonify(categorias=cats, vuelos=vuelos, umbral=umbral,
                   modelo=dict(mod) if mod else None,
                   total_fotos=tot[0] or 0, total_revisadas=tot[1] or 0,
                   con_gps=con_gps, sigatoka_mapa=sigatoka_mapa, revisadas_desde_modelo=nuevas,
                   modelo_inicial=str(datos.MODELO_INICIAL.relative_to(RAIZ)))


@app.get("/api/fotos")
def api_fotos():
    vuelo, clase, filtro = request.args.get("vuelo"), request.args.get("clase"), request.args.get("filtro")
    pagina_n = max(int(request.args.get("pagina", 1)), 1)
    sql, args = "SELECT * FROM fotos WHERE 1=1", []
    if vuelo:
        sql += " AND vuelo=?"; args.append(vuelo)
    if clase:
        sql += " AND COALESCE(etiqueta, pred)=?"; args.append(clase)
    if filtro == "pendientes":
        sql += " AND etiqueta IS NULL"
    elif filtro == "revisadas":
        sql += " AND etiqueta IS NOT NULL"
    elif filtro == "sin_gps":
        sql += " AND lat IS NULL"
    with conectar() as con:
        total = con.execute(sql.replace("SELECT *", "SELECT COUNT(*)"), args).fetchone()[0]
        filas = con.execute(sql + " ORDER BY vuelo, archivo LIMIT 60 OFFSET ?",
                            args + [(pagina_n - 1) * 60]).fetchall()
    return jsonify(total=total, pagina=pagina_n, fotos=[foto_dict(f) for f in filas])


@app.get("/api/mapa")
def api_mapa():
    vuelo = request.args.get("vuelo")
    sql = ("SELECT id, vuelo, archivo, lat, lon, alt, fecha, pred, conf, etiqueta, revisor"
           " FROM fotos WHERE lat IS NOT NULL")
    args = []
    if vuelo:
        sql += " AND vuelo=?"; args.append(vuelo)
    with conectar() as con:
        filas = [foto_dict(f) for f in con.execute(sql, args)]
        sin_gps = con.execute("SELECT COUNT(*) FROM fotos WHERE lat IS NULL" +
                              (" AND vuelo=?" if vuelo else ""), args).fetchone()[0]
    return jsonify(fotos=filas, sin_gps=sin_gps)


@app.get("/api/geojson")
def api_geojson():
    vuelo = request.args.get("vuelo")
    with conectar() as con:
        cats = {r["clave"]: r["nombre"] for r in con.execute("SELECT clave, nombre FROM categorias")}
        sql = "SELECT * FROM fotos WHERE lat IS NOT NULL" + (" AND vuelo=?" if vuelo else "")
        filas = con.execute(sql, [vuelo] if vuelo else []).fetchall()
    feats = [{
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [f["lon"], f["lat"]]},
        "properties": {
            "vuelo": f["vuelo"], "archivo": f["archivo"], "fecha": f["fecha"],
            "diagnostico": cats.get(f["etiqueta"] or f["pred"], f["etiqueta"] or f["pred"]),
            "fuente": "revisión humana" if f["etiqueta"] else "modelo",
            "confianza_modelo": f["conf"], "revisor": f["revisor"],
        },
    } for f in filas if f["etiqueta"] != DESCARTAR]
    nombre = f"sigatoka_{vuelo or 'todos'}.geojson"
    resp = app.response_class(json.dumps({"type": "FeatureCollection", "features": feats},
                                         ensure_ascii=False, indent=1),
                              mimetype="application/geo+json")
    resp.headers["Content-Disposition"] = f'attachment; filename="{nombre}"'
    return resp


@app.get("/api/siguiente")
def api_siguiente():
    """Siguiente foto a revisar: sin etiqueta, la de MENOR confianza primero
    (las dudas del modelo son las correcciones que más le enseñan)."""
    vuelo = request.args.get("vuelo")
    excluir = [int(x) for x in request.args.get("excluir", "").split(",") if x.isdigit()]
    sql, args = "SELECT * FROM fotos WHERE etiqueta IS NULL", []
    if vuelo:
        sql += " AND vuelo=?"; args.append(vuelo)
    if excluir:
        sql += f" AND id NOT IN ({','.join('?' * len(excluir))})"; args += excluir
    with conectar() as con:
        f = con.execute(sql + " ORDER BY conf IS NOT NULL, conf ASC, id LIMIT 1", args).fetchone()
        pend = con.execute("SELECT COUNT(*) FROM fotos WHERE etiqueta IS NULL" +
                           (" AND vuelo=?" if vuelo else ""), [vuelo] if vuelo else []).fetchone()[0]
    return jsonify(foto=foto_dict(f) if f else None, pendientes=pend)


@app.get("/api/foto/<int:fid>")
def api_foto(fid):
    with conectar() as con:
        f = con.execute("SELECT * FROM fotos WHERE id=?", (fid,)).fetchone()
    if not f:
        abort(404)
    d = foto_dict(f)
    clf, _ = clasificador()
    if clf:
        pred = clf.predecir(carpeta_vuelo(f["vuelo"]) / f["archivo"])
        d["probs"] = pred["probs"] if pred else None
    return jsonify(foto=d)


@app.post("/api/identificar")
def api_identificar():
    """Diagnostica una sola imagen subida (no se guarda en la base de datos)."""
    import cv2
    import numpy as np

    arch = request.files.get("imagen")
    if not arch:
        return jsonify(ok=False, error="No llegó ninguna imagen."), 400
    clf, version = clasificador()
    if not clf:
        return jsonify(ok=False, error="No hay modelo cargado: copia sigatoka_cls_v1.onnx a "
                       f"{datos.MODELO_INICIAL.relative_to(RAIZ)} y reinicia la estación."), 503
    img = cv2.imdecode(np.frombuffer(arch.read(), np.uint8), cv2.IMREAD_COLOR)
    if img is None:
        return jsonify(ok=False, error="No se pudo leer la imagen. Usa una foto JPG o PNG."), 400
    t0 = time.perf_counter()
    pred = clf.predecir_bgr(img)
    ms = (time.perf_counter() - t0) * 1000
    return jsonify(ok=True, **pred, umbral=clf.umbral, diagnosticable=pred["confianza"] >= clf.umbral,
                   modelo_version=version, ms=ms, ancho=int(img.shape[1]), alto=int(img.shape[0]))


@app.post("/api/etiquetar")
def api_etiquetar():
    d = request.get_json(force=True)
    etiqueta = d.get("etiqueta")
    with conectar() as con:
        validas = {r[0] for r in con.execute("SELECT clave FROM categorias")} | {DESCARTAR}
        if etiqueta is not None and etiqueta not in validas:
            return jsonify(ok=False, error="Categoría desconocida"), 400
        con.execute("UPDATE fotos SET etiqueta=?, revisor=?, fecha_etiqueta=? WHERE id=?",
                    (etiqueta, (d.get("revisor") or "").strip()[:60] or None,
                     datos.ahora() if etiqueta else None, int(d["id"])))
    return jsonify(ok=True)


@app.post("/api/subir")
def api_subir():
    vuelo = datos.nombre_seguro(request.form.get("vuelo", ""))
    carpeta = carpeta_vuelo(vuelo)
    carpeta.mkdir(parents=True, exist_ok=True)
    guardados = 0
    for arch in request.files.getlist("archivos"):
        nombre = Path(arch.filename or "").name
        ext = Path(nombre).suffix.lower()
        if not nombre or (ext not in datos.EXT_IMG and ext != ".json"):
            continue
        arch.save(carpeta / datos.nombre_seguro(nombre))
        guardados += 1
    return jsonify(ok=True, vuelo=vuelo, guardados=guardados)


@app.post("/api/procesar")
def api_procesar():
    vuelo = datos.nombre_seguro(request.get_json(force=True).get("vuelo", ""))
    if not carpeta_vuelo(vuelo).is_dir():
        return jsonify(ok=False, error="No hay fotos para ese vuelo"), 400
    clf, version = clasificador()
    with conectar() as con:
        r = datos.procesar_vuelo(con, vuelo, clf, version)
    return jsonify(ok=True, vuelo=vuelo, sin_modelo=clf is None, **r)


@app.get("/api/entrenamiento")
def api_entrenamiento_estado():
    with conectar() as con:
        modelos = [dict(r) for r in con.execute("SELECT * FROM modelos ORDER BY version DESC")]
        historial = [dict(r) for r in con.execute(
            "SELECT id, inicio, fin, estado, epocas, modelo_version FROM entrenamientos ORDER BY id DESC LIMIT 10")]
        datos_cat = entrenamiento.resumen_datos(con)
    return jsonify(estado=entrenamiento.estado(), modelos=modelos, historial=historial,
                   datos=datos_cat, reproceso=dict(_reproceso),
                   dataset_base=datos.DATASET_BASE.is_dir(),
                   min_por_clase=entrenamiento.MIN_POR_CLASE)


@app.post("/api/entrenamiento")
def api_entrenar():
    epocas = int(request.get_json(force=True).get("epocas", 50))
    ok, msg = entrenamiento.iniciar(max(1, min(epocas, 300)))
    return jsonify(ok=ok, mensaje=msg), (200 if ok else 409)


@app.post("/api/modelo/activar")
def api_activar():
    version = int(request.get_json(force=True)["version"])
    if _reproceso["activo"]:
        return jsonify(ok=False, error="Espera a que termine el reprocesamiento."), 409
    with conectar() as con:
        if not con.execute("SELECT 1 FROM modelos WHERE version=?", (version,)).fetchone():
            return jsonify(ok=False, error="No existe ese modelo"), 404
        con.execute("UPDATE modelos SET activo=(version=?)", (version,))
    _reproceso.update(activo=True, hechas=0, total=0)  # antes del hilo: la página ya lo ve en curso
    threading.Thread(target=_reprocesar, daemon=True).start()
    return jsonify(ok=True)


def _reprocesar():
    """Con un modelo nuevo activo, vuelve a diagnosticar todas las fotos."""
    con = conectar()
    try:
        clf, version = clasificador()
        filas = con.execute("SELECT id, vuelo, archivo FROM fotos").fetchall()
        _reproceso.update(total=len(filas))
        for f in filas:
            pred = clf.predecir(carpeta_vuelo(f["vuelo"]) / f["archivo"]) if clf else None
            con.execute("UPDATE fotos SET pred=?, conf=?, modelo_version=? WHERE id=?",
                        (pred and pred["clase"], pred and pred["confianza"],
                         version if pred else None, f["id"]))
            _reproceso["hechas"] += 1
            if _reproceso["hechas"] % 50 == 0:
                con.commit()
        con.commit()
    finally:
        _reproceso["activo"] = False
        con.close()


@app.post("/api/categorias")
def api_categoria_nueva():
    d = request.get_json(force=True)
    nombre = (d.get("nombre") or "").strip()[:40]
    clave = datos.nombre_seguro(nombre.lower().replace(" ", "_"))
    color = d.get("color") or "#7b61ff"
    if not nombre or not clave:
        return jsonify(ok=False, error="Escribe un nombre"), 400
    with conectar() as con:
        if con.execute("SELECT 1 FROM categorias WHERE clave=?", (clave,)).fetchone():
            return jsonify(ok=False, error="Esa categoría ya existe"), 409
        orden = con.execute("SELECT COALESCE(MAX(orden), 0) + 1 FROM categorias").fetchone()[0]
        con.execute("INSERT INTO categorias (clave, nombre, color, orden) VALUES (?,?,?,?)",
                    (clave, nombre, color, orden))
    return jsonify(ok=True, clave=clave)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--puerto", type=int, default=5050)
    ap.add_argument("--red", action="store_true", help="permitir abrirla desde otros equipos del WiFi")
    ap.add_argument("--no-navegador", action="store_true")
    args = ap.parse_args()

    datos.inicializar()
    url = f"http://localhost:{args.puerto}"
    print("\n==============================================")
    print(f"  Estación de tierra lista:  {url}")
    print("  (deja esta ventana abierta; Ctrl+C para cerrar)")
    print("==============================================\n")
    if not args.no_navegador:
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    app.run(host="0.0.0.0" if args.red else "127.0.0.1", port=args.puerto, threaded=True)


if __name__ == "__main__":
    main()
