import cv2
import glob
import json
import os
import signal
import socket
import sys
import time
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote

# El lanzador manda la salida a un archivo (zed-right.log). Sin esto Python la guarda en memoria y
# el log no muestra las líneas [MODELO], [PARCHES]... hasta que el programa se cierra.
try:
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)
except AttributeError:
    pass

import pyzed.sl as sl
import piexif
from pymavlink import mavutil

# CONFIGURACION
CARPETA = Path("/home/jetsonnanoorin/Prueba#1")
PUERTO = "/dev/ttyACM0"   # si no existe, se busca la Pixhawk en /dev/serial/by-id y /dev/ttyACM*
PUERTO_WEB = 8080        # video y diagnóstico en http://<ip-de-la-jetson>:8080
ANCHO_WEB = 960          # ancho del video que se manda por WiFi (más chico = más fluido)
FPS_WEB = 12
# Detección en vivo: un hilo revisa por cuadros el último cuadro de la cámara una y otra vez (el
# mismo método y el mismo modelo que la página: dos tamaños de cuadro, filtro de hoja). Al tomar
# una foto, la foto guarda ESE cuadro con su resultado: lo que se veía en vivo es lo que queda en
# la foto, en el EXIF, en el log y en el mapa. Cada foto sigue teniendo un solo resultado.
ANALIZAR_EN_VIVO = True  # revisar el video sin parar (en la Jetson, una revisión cada 2-5 s)
PAUSA_EN_VIVO = 0.3      # segundos entre una revisión y la siguiente (deja procesador al video)
HILOS_MODELO = 4         # núcleos para el modelo; los demás quedan para la cámara, el video y el GPS
FOTO_DEL_CUADRO_ANALIZADO = True  # la foto es el cuadro revisado en vivo (puede ser de hace 2-5 s)
EDAD_MAX_VIVO = 10       # si la última revisión en vivo es más vieja (s), la foto se revisa aparte
ANALIZAR_FOTOS = True    # respaldo: sin revisión en vivo reciente, revisar la foto (~2-4 s)
# El modelo más nuevo que esté en vision/models; para volver a uno anterior:
#   SIGATOKA_MODELO=sigatoka_cls_v1.onnx bash jetson/zed_control.sh reiniciar
MODELOS = ("sigatoka_cls_v2.onnx", "sigatoka_cls_v1.onnx")
TEXTO_EN_FOTO = True     # la foto se guarda con FECHA/HORA/GPS y su resultado dibujados encima
COPIA_SIN_TEXTO = True   # y una copia limpia en <CARPETA>/sin_texto/ para el modelo y el dataset
# Sin monitor (en el dron) o con --sin-ventana: no abre ventana, solo la página.
CON_VENTANA = bool(os.environ.get("DISPLAY")) and "--sin-ventana" not in sys.argv

CARPETA.mkdir(parents=True, exist_ok=True)

gps_actual = None
gps_lock = threading.Lock()

# Último cuadro de la cámara (lo comparten la ventana, el modelo y la página)
ultimo = {"frame": None, "instante": None, "n": 0}
cuadro_lock = threading.Lock()

nombre_modelo = "sin modelo"

video = {"jpeg": None, "n": 0}
video_cond = threading.Condition()
clientes_video = 0
clientes_lock = threading.Lock()

foto_lock = threading.Lock()
fotos = {"ultima": None, "total": 0}

# Última revisión en vivo: el resultado y el cuadro, la hora y el GPS con que se revisó
vivo = {"r": None, "frame": None, "instante": None, "gps": None, "ms": None, "fin": None, "n": 0}
vivo_lock = threading.Lock()

NOMBRES = {"sana": "SANA", "sigatoka": "SIGATOKA", "otra_condicion": "OTRA CONDICION", "sin_hoja": "SIN HOJA"}
COLORES = {"sana": (80, 200, 80), "sigatoka": (60, 60, 230), "otra_condicion": (60, 200, 230),
           "sin_hoja": (170, 160, 150)}


# LEER GPS DEL PIXHAWK
def buscar_puerto():
    # El USB de la Pixhawk a veces aparece como ttyACM1 u otro nombre al reconectar
    if Path(PUERTO).exists():
        return PUERTO

    for patron in ("/dev/serial/by-id/*PX4*", "/dev/serial/by-id/*Pixhawk*",
                   "/dev/serial/by-id/*Holybro*", "/dev/ttyACM*"):
        encontrados = sorted(glob.glob(patron))
        if encontrados:
            return encontrados[0]

    return PUERTO


def leer_gps():
    global gps_actual
    ultimo_error = None

    while True:
        pixhawk = None

        try:
            puerto = buscar_puerto()
            pixhawk = mavutil.mavlink_connection(
                puerto, baud=115200
            )

            hb = pixhawk.wait_heartbeat(timeout=15)

            if hb is None:
                raise RuntimeError("Sin heartbeat")

            print(f"[GPS] Pixhawk conectado en {puerto}")
            ultimo_error = None

            pixhawk.mav.command_long_send(
                pixhawk.target_system,
                1,
                mavutil.mavlink.MAV_CMD_SET_MESSAGE_INTERVAL,
                0,
                mavutil.mavlink.MAVLINK_MSG_ID_GPS_RAW_INT,
                500000,
                0, 0, 0, 0, 0
            )

            while True:
                msg = pixhawk.recv_match(
                    type="GPS_RAW_INT",
                    blocking=True,
                    timeout=3
                )

                if msg is None:
                    continue

                with gps_lock:
                    if (
                        msg.fix_type >= 3
                        and -900000000 <= msg.lat <= 900000000
                        and -1800000000 <= msg.lon <= 1800000000
                        and (msg.lat != 0 or msg.lon != 0)
                    ):
                        gps_actual = {
                            "lat": msg.lat / 1e7,
                            "lon": msg.lon / 1e7,
                            "alt": msg.alt / 1000,
                            "satelites": msg.satellites_visible,
                            "tiempo": time.monotonic()
                        }
                    else:
                        gps_actual = None

        except Exception as e:
            # Sin Pixhawk el error se repite cada 3 s: se imprime solo cuando cambia
            if str(e) != ultimo_error:
                print("[GPS]", e, "(reintentando cada 3 s)")
                ultimo_error = str(e)

        finally:
            with gps_lock:
                gps_actual = None

            if pixhawk is not None:
                pixhawk.close()

        time.sleep(3)


def obtener_gps():
    with gps_lock:
        if gps_actual is None:
            return None

        if time.monotonic() - gps_actual["tiempo"] > 3:
            return None

        return gps_actual.copy()


# MODELO DE SIGATOKA (identificación a bordo)
def cargar_modelo():
    # El modelo vive en el repo: vision/models/sigatoka_cls_v2.onnx o v1 (+ .json)
    global nombre_modelo

    for repo in (Path(__file__).resolve().parent.parent,
                 Path.home() / "Dron-9no-semestre"):
        if (repo / "vision" / "clasificador.py").exists():
            break
    else:
        print("[MODELO] No encontré el repo Dron-9no-semestre; sigo sin identificar")
        return None

    carpeta = repo / "vision" / "models"
    elegido = os.environ.get("SIGATOKA_MODELO")
    candidatos = [elegido] if elegido else list(MODELOS)
    onnx = next((carpeta / c for c in candidatos if (carpeta / c).exists()), None)

    if onnx is None:
        print(f"[MODELO] No hay {' ni '.join(candidatos)} en {carpeta} (git pull); sigo sin identificar")
        return None

    sys.path.insert(0, str(repo))

    try:
        from vision.clasificador import Clasificador
        modelo = Clasificador(onnx, hilos=HILOS_MODELO)
    except Exception as e:
        print("[MODELO] No se pudo cargar:", e)
        return None

    nombre_modelo = onnx.stem

    print(f"[MODELO] {onnx.name} cargado; clases {modelo.clases}; en vivo por cuadros: "
          f"{'sí' if ANALIZAR_EN_VIVO else 'no'}; filtro de hoja: {'sí' if getattr(modelo, 'filtro', None) else 'no'}")
    return modelo


# CONVERTIR COORDENADAS A EXIF
def racional(numero):
    return (int(round(numero * 1000000)), 1000000)


def coordenada_exif(valor):
    valor = abs(valor)

    grados = int(valor)
    minutos_total = (valor - grados) * 60
    minutos = int(minutos_total)
    segundos = (minutos_total - minutos) * 60

    return (
        (grados, 1),
        (minutos, 1),
        racional(segundos)
    )


def crear_exif(gps, instante, r=None, en_vivo=False):
    """EXIF de la foto. r = resultado del análisis por parches (None mientras se analiza);
    en_vivo = el resultado es el de la revisión en vivo de ese mismo cuadro."""
    import piexif.helper

    fecha_exif = instante.strftime("%Y:%m:%d %H:%M:%S")
    fecha_iso = instante.isoformat(timespec="microseconds")

    if modelo is None or not (ANALIZAR_FOTOS or ANALIZAR_EN_VIVO):
        analisis = "AnalisisYOLO=NO_REALIZADO"
    elif r is None:
        analisis = "AnalisisYOLO=PENDIENTE"
    else:
        a = r
        analisis = (
            f"AnalisisYOLO={a['clase']}; "
            f"ConfianzaYOLO={a['confianza']:.3f}; "
            f"ModeloYOLO={nombre_modelo} a bordo, {'foto completa' if a.get('modo') == 'completa' else 'por parches'}{', en vivo' if en_vivo else ''}"
            f"; ParchesHoja={a.get('n_parches', 0)}"
            f"; Hojas={len(a.get('hojas') or [])}"
            f"; HojasConSintomas={sum(h['clase'] not in ('sana', 'sin_hoja') for h in a.get('hojas') or [])}"
            f"; FraccionParches=" + ",".join(f"{k}:{v:.2f}" for k, v in (a.get("fraccion") or {}).items())
        )

    comentario = (
        f"Proyecto=Dron Sigatoka; "
        f"Camara=ZED X Mini RIGHT; "
        f"FechaHora={fecha_iso}; "
        f"GPS={'VALIDO' if gps is not None else 'SIN_SENAL'}; "
        f"FuenteGPS=Pixhawk 6C HERE4; "
        f"{analisis}"
    )

    if gps is not None:
        comentario += (
            f"; Latitud={gps['lat']:.7f}"
            f"; Longitud={gps['lon']:.7f}"
            f"; Altitud_m={gps['alt']:.2f}"
            f"; Satelites={gps['satelites']}"
        )

    exif = {
        "0th": {
            piexif.ImageIFD.DateTime: fecha_exif,
            piexif.ImageIFD.Software: "Dron Sigatoka - Jetson",
            piexif.ImageIFD.ImageDescription:
                "ZED X Mini RIGHT; GPS desde Pixhawk HERE4"
        },
        "Exif": {
            piexif.ExifIFD.DateTimeOriginal: fecha_exif,
            piexif.ExifIFD.DateTimeDigitized: fecha_exif,
            piexif.ExifIFD.SubSecTimeOriginal:
                instante.strftime("%f"),
            piexif.ExifIFD.UserComment:
                piexif.helper.UserComment.dump(
                    comentario, encoding="unicode"
                )
        },
        "GPS": {},
        "1st": {},
        "thumbnail": None
    }

    if gps is not None:
        exif["GPS"] = {
            piexif.GPSIFD.GPSVersionID: (2, 3, 0, 0),
            piexif.GPSIFD.GPSLatitudeRef:
                b"N" if gps["lat"] >= 0 else b"S",
            piexif.GPSIFD.GPSLatitude:
                coordenada_exif(gps["lat"]),
            piexif.GPSIFD.GPSLongitudeRef:
                b"E" if gps["lon"] >= 0 else b"W",
            piexif.GPSIFD.GPSLongitude:
                coordenada_exif(gps["lon"]),
            piexif.GPSIFD.GPSAltitudeRef:
                0 if gps["alt"] >= 0 else 1,
            piexif.GPSIFD.GPSAltitude:
                racional(abs(gps["alt"]))
        }

    return piexif.dump(exif)


# GUARDAR FOTOGRAFIA
def texto_resultado(a, prefijo="DIAG", vacio="TOMA UNA FOTO"):
    """La línea de resultado (texto y color) para la pantalla o la foto."""
    gris = (200, 200, 200)
    if modelo is None:
        return f"{prefijo}: SIN MODELO", gris
    if not (ANALIZAR_FOTOS or ANALIZAR_EN_VIVO):
        return f"{prefijo}: SIN ANALISIS", gris
    if a is None:
        return f"{prefijo}: {vacio}", gris
    if a.get("pendiente"):
        return f"{prefijo}: ANALIZANDO...", gris
    if a.get("error"):
        return f"{prefijo}: NO SE PUDO ANALIZAR", gris
    if a["clase"] != "sin_hoja" and a["confianza"] < modelo.umbral:
        return f"{prefijo}: NO SEGURO ({a['confianza']:.0%})", gris
    return (f"{prefijo}: {NOMBRES.get(a['clase'], a['clase'])} {a['confianza']:.0%}",
            COLORES.get(a["clase"], (255, 255, 255)))


def dibujar_textos(frame, gps, instante, resultado):
    """Copia del cuadro con fecha, hora, GPS y la línea de resultado dibujados encima."""
    pantalla = frame.copy()
    fecha_visible = instante.strftime("%y-%m-%d")
    hora_visible = instante.strftime("%H:%M:%S")

    if gps is None:
        textos = ["RIGHT CAMERA", f"FECHA: {fecha_visible}", f"HORA: {hora_visible}", "GPS: SIN SENAL"]
        color = (0, 0, 255)
    else:
        textos = ["RIGHT CAMERA", f"FECHA: {fecha_visible}", f"HORA: {hora_visible}",
                  f"LAT: {gps['lat']:.7f}", f"LON: {gps['lon']:.7f}", f"ALT: {gps['alt']:.1f} m",
                  f"SAT: {gps['satelites']}"]
        color = (0, 255, 0)

    for i, texto in enumerate(textos):
        cv2.putText(pantalla, texto, (30, 50 + i * 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 0), 5)
        cv2.putText(pantalla, texto, (30, 50 + i * 40), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

    texto, color_r = resultado
    y = 50 + len(textos) * 40 + 10
    cv2.putText(pantalla, texto, (30, y), cv2.FONT_HERSHEY_SIMPLEX, 1.1, (0, 0, 0), 6)
    cv2.putText(pantalla, texto, (30, y), cv2.FONT_HERSHEY_SIMPLEX, 1.1, color_r, 2)
    return pantalla


def dibujar_cuadros(img, r, escala=1.0):
    """Marca sobre la imagen (en su lugar) los cuadros con síntomas de una revisión por cuadros."""
    if not r or modelo is None:
        return img
    for c in r.get("parches") or []:
        if c["clase"] in ("sana", "sin_hoja") or c["confianza"] < modelo.umbral:
            continue
        x, y = int(c["x"] * escala), int(c["y"] * escala)
        x1, y1 = int((c["x"] + c["w"]) * escala), int((c["y"] + c["h"]) * escala)
        cv2.rectangle(img, (x, y), (x1 - 1, y1 - 1), COLORES.get(c["clase"], (255, 255, 255)), max(2, int(4 * escala)))
    return img


def resumen_analisis(nombre, r, ms, en_vivo=False):
    """Lo que se guarda en fotos["analisis"] y se manda en /estado."""
    sintomas = [c for c in r.get("parches", []) if c["clase"] not in ("sana", "sin_hoja")]
    hojas = r.get("hojas") or []
    return {"archivo": nombre, "clase": r["clase"], "confianza": r["confianza"], "probs": r.get("probs"),
            "n_parches": r.get("n_parches", 0), "n_sintomas": len(sintomas), "n_hojas": len(hojas),
            "n_hojas_sintomas": sum(h["clase"] not in ("sana", "sin_hoja") for h in hojas),
            "fraccion": r.get("fraccion"), "ms": round(ms), "lado": r.get("lado"), "modo": r.get("modo"), "en_vivo": en_vivo}


def guardar_cuadros_json(ruta, r):
    """Los cuadros de la revisión en un JSON al lado, por si se quieren dibujar después."""
    (CARPETA / "parches").mkdir(exist_ok=True)
    (CARPETA / "parches" / (ruta.stem + ".json")).write_text(json.dumps({
        "archivo": ruta.name, "modelo": nombre_modelo, "clase": r["clase"],
        "confianza": r["confianza"], "probs": r["probs"], "modo": r.get("modo"),
        "escala": r.get("escala"), "lado": r.get("lado"),
        "fraccion": r.get("fraccion"), "ancho": r.get("ancho"), "alto": r.get("alto"),
        "hojas": r.get("hojas") or [], "parches": r.get("parches", [])
    }, indent=1), encoding="utf-8")


def linea_parches(nombre, a, detalle=""):
    como = "decidió la foto completa" if a.get("modo") == "completa" else f"cuadro de {a.get('lado') or '?'} px"
    print(f"[PARCHES] {nombre}: {a['clase']} {a['confianza']:.0%} · "
          f"{a['n_sintomas']}/{a['n_parches']} trozos con síntomas · "
          f"{a['n_hojas_sintomas']}/{a['n_hojas']} hojas con síntomas · {como} · "
          f"{a['ms']} ms{detalle}")


def ultimo_en_vivo():
    """La última revisión en vivo si es reciente (EDAD_MAX_VIVO), o None."""
    with vivo_lock:
        if vivo["r"] is None or vivo["fin"] is None or time.time() - vivo["fin"] > EDAD_MAX_VIVO:
            return None
        return dict(vivo)


def guardar_foto(frame, gps, instante):
    from PIL import Image

    # La foto se queda con la revisión en vivo: el cuadro que se revisó, con su hora, GPS y resultado.
    v = ultimo_en_vivo() if ANALIZAR_EN_VIVO else None
    if v is not None and FOTO_DEL_CUADRO_ANALIZADO:
        frame, gps, instante = v["frame"], v["gps"], v["instante"]
    r = v["r"] if v is not None else None

    marca = instante.strftime("%y-%m-%d_%H-%M-%S")
    exif = crear_exif(gps, instante, r, en_vivo=r is not None)
    analisis = resumen_analisis("", r, v["ms"], en_vivo=True) if r is not None else {"pendiente": True}

    # Con texto: el resultado en vivo, o "ANALIZANDO" si hay que revisar la foto aparte.
    con_texto = TEXTO_EN_FOTO
    pantalla = dibujar_textos(frame, gps, instante, texto_resultado(analisis)) if con_texto else None

    imagen = Image.fromarray(cv2.cvtColor(
        pantalla if con_texto else frame, cv2.COLOR_BGR2RGB
    ))

    # El candado evita choques si la tecla S y la página toman foto a la vez
    with foto_lock:
        ruta = CARPETA / f"{marca}-GPS.jpg"

        # Numerar fotos tomadas en el mismo segundo
        numero = 2

        while ruta.exists():
            ruta = CARPETA / f"{marca}-GPS_{numero}.jpg"
            numero += 1

        # xb impide sobrescribir un archivo existente
        with open(ruta, "xb") as archivo:
            imagen.save(
                archivo,
                format="JPEG",
                quality=95,
                exif=exif
            )

        # Copia sin texto con el mismo nombre y EXIF: el texto sobreimpreso
        # confunde al modelo, así que el dataset y la estación usan esta.
        if con_texto and COPIA_SIN_TEXTO:
            (CARPETA / "sin_texto").mkdir(exist_ok=True)
            Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)).save(
                CARPETA / "sin_texto" / ruta.name,
                format="JPEG",
                quality=95,
                exif=exif
            )

        fotos["ultima"] = ruta.name
        fotos["total"] += 1

    print("[FOTO]", ruta.name)
    print("[FECHA]", instante.isoformat())

    if gps is None:
        print("[FOTO] Sin coordenadas GPS")
    else:
        print("[FOTO] GPS:", gps["lat"], gps["lon"])

    if r is not None:
        analisis["archivo"] = ruta.name
        fotos["analisis"] = analisis
        try:
            guardar_cuadros_json(ruta, r)
        except OSError as e:
            print("[PARCHES] JSON:", e)
        edad = time.time() - v["fin"]
        linea_parches(ruta.name, analisis, f" · en vivo, revisado hace {edad:.1f} s")
    elif ANALIZAR_FOTOS and modelo is not None:
        fotos["analisis"] = {"archivo": ruta.name, "pendiente": True}
        threading.Thread(target=analizar_foto, args=(ruta, frame, gps, instante, con_texto),
                         daemon=True).start()

    return ruta


# ANALISIS POR PARCHES (en la Jetson, 2-5 s por revisión). Una revisión a la vez.
analisis_lock = threading.Lock()


def analizar_en_vivo():
    """Revisa por cuadros el último cuadro de la cámara, una y otra vez. El resultado se ve en la
    ventana, en el video, en /estado y en las páginas; la foto que se tome se queda con él."""
    visto = -1
    while True:
        with cuadro_lock:
            frame, instante, n = ultimo["frame"], ultimo["instante"], ultimo["n"]
        if frame is None or n == visto:
            time.sleep(0.05)
            continue
        visto = n
        gps = obtener_gps()
        inicio = time.perf_counter()
        try:
            with analisis_lock:
                r = modelo.predecir_bgr(frame, "parches")
        except Exception as e:
            print("[EN VIVO]", e)
            time.sleep(2)
            continue
        ms = (time.perf_counter() - inicio) * 1000
        with vivo_lock:
            vivo.update(r=r, frame=frame, instante=instante, gps=gps, ms=ms, fin=time.time(), n=vivo["n"] + 1)
        time.sleep(PAUSA_EN_VIVO)


def analizar_foto(ruta, frame, gps, instante, con_texto):
    """Respaldo cuando no hay revisión en vivo reciente: revisa la copia limpia ya guardada."""
    import piexif
    from PIL import Image

    limpia = CARPETA / "sin_texto" / ruta.name if con_texto and COPIA_SIN_TEXTO else ruta

    with analisis_lock:
        inicio = time.perf_counter()

        try:
            # La misma imagen que revisa la página: la copia limpia ya guardada en JPEG
            img = cv2.imread(str(limpia))
            r = modelo.predecir_bgr(frame if img is None else img, "parches")
        except Exception as e:
            print("[PARCHES]", e)
            fotos["analisis"] = {"archivo": ruta.name, "error": str(e)}
            if con_texto:
                Image.fromarray(cv2.cvtColor(dibujar_textos(frame, gps, instante, texto_resultado(fotos["analisis"])),
                                             cv2.COLOR_BGR2RGB)).save(ruta, format="JPEG", quality=95,
                                                                     exif=piexif.dump(piexif.load(str(ruta))))
            return

        ms = (time.perf_counter() - inicio) * 1000
        fotos_analisis = resumen_analisis(ruta.name, r, ms)

        # El resultado va en el EXIF de la foto y de su copia limpia, y dibujado en la foto con texto
        exif = crear_exif(gps, instante, r)
        if con_texto:
            try:
                Image.fromarray(cv2.cvtColor(dibujar_textos(frame, gps, instante, texto_resultado(fotos_analisis)),
                                             cv2.COLOR_BGR2RGB)).save(ruta, format="JPEG", quality=95, exif=exif)
            except Exception as e:
                print("[PARCHES] foto con texto:", e)
        for archivo in {ruta, limpia}:
            if archivo.is_file():
                try:
                    piexif.insert(exif, str(archivo))
                except Exception as e:
                    print("[PARCHES] EXIF:", e)

        guardar_cuadros_json(ruta, r)
        fotos["analisis"] = fotos_analisis

    linea_parches(ruta.name, fotos_analisis, " · revisada aparte (no había revisión en vivo reciente)")


def tomar_foto():
    with cuadro_lock:
        frame, instante = ultimo["frame"], ultimo["instante"]

    if frame is None:
        return None

    return guardar_foto(frame, obtener_gps(), instante)


# VIDEO PARA LA PAGINA (MJPEG): solo se codifica si alguien lo está viendo
def codificar_video():
    visto = -1

    while True:
        if clientes_video == 0:
            time.sleep(0.2)
            continue

        inicio = time.perf_counter()

        with cuadro_lock:
            frame, n = ultimo["frame"], ultimo["n"]

        if frame is None or n == visto:
            time.sleep(0.01)
            continue

        visto = n
        alto = int(frame.shape[0] * ANCHO_WEB / frame.shape[1])
        chico = cv2.resize(frame, (ANCHO_WEB, alto), interpolation=cv2.INTER_AREA)
        with vivo_lock:
            r_vivo = vivo["r"]
        dibujar_cuadros(chico, r_vivo, ANCHO_WEB / frame.shape[1])   # lo que se detecta en vivo
        ok, buf = cv2.imencode(".jpg", chico, [cv2.IMWRITE_JPEG_QUALITY, 75])

        if ok:
            with video_cond:
                video["jpeg"] = buf.tobytes()
                video["n"] += 1
                video_cond.notify_all()

        time.sleep(max(0.0, 1 / FPS_WEB - (time.perf_counter() - inicio)))


def resultado_ultima_foto(modelo):
    a = fotos.get("analisis")
    if modelo is None or not a or "clase" not in a:
        return None
    return {"clase": a["clase"], "confianza": a["confianza"], "probs": a.get("probs"), "ms": a.get("ms"),
            "foto": a["archivo"], "diagnosticable": a["confianza"] >= modelo.umbral or a["clase"] == "sin_hoja"}


def resultado_en_vivo(modelo):
    """La última revisión en vivo para /estado (sin el cuadro), con su edad en segundos."""
    with vivo_lock:
        r, ms, fin, n = vivo["r"], vivo["ms"], vivo["fin"], vivo["n"]
    if modelo is None or r is None:
        return None
    a = resumen_analisis(None, r, ms, en_vivo=True)
    a.update(edad_s=round(time.time() - fin, 1), n=n,
             diagnosticable=a["confianza"] >= modelo.umbral or a["clase"] == "sin_hoja")
    return a


def estado_actual(modelo):
    gps = obtener_gps()

    if gps is not None:
        gps.pop("tiempo", None)

    return {
        "camara": "ZED X Mini RIGHT",
        "hora": datetime.now().astimezone().isoformat(timespec="seconds"),
        "gps": gps,
        "modelo": None if modelo is None else {
            "archivo": modelo.ruta.name,
            "clases": modelo.clases,
            "umbral": modelo.umbral,
            "fotos_por_parches": ANALIZAR_FOTOS,
            "en_vivo": ANALIZAR_EN_VIVO,
            "filtro_hoja": getattr(modelo, "filtro", None) is not None
        },
        # La revisión en vivo (por cuadros) y la de la última foto, que es la en vivo del momento de la foto
        "en_vivo": resultado_en_vivo(modelo),
        "prediccion": resultado_en_vivo(modelo) or resultado_ultima_foto(modelo),
        "fotos": {k: v for k, v in fotos.items() if k != "analisis"},
        "analisis_foto": fotos.get("analisis")
    }


PAGINA = """<!doctype html><html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dron Sigatoka</title>
<style>
body{margin:0;background:#0b1217;color:#eaf0f4;font:16px system-ui,sans-serif}
main{max-width:960px;margin:auto;padding:12px;display:grid;gap:12px}
img{width:100%;border-radius:10px;background:#000}
#diag{font-size:1.6rem;font-weight:800} .nota{color:#9fb0bb;font-size:.9rem}
button{font:inherit;font-weight:700;padding:.8rem 1.2rem;border-radius:10px;border:0;background:#eaf0f4;color:#0b1217}
</style></head><body><main>
<img src="/video" alt="Video en vivo del dron">
<div id="diag">Conectando...</div>
<div class="nota" id="vivo"></div>
<div class="nota">En vivo, el dron revisa el video por cuadros, como la página; los cuadros con síntomas se marcan en el video. La foto se queda con ese resultado.</div>
<div class="nota" id="gps"></div>
<div><button id="foto">Tomar foto</button> <span class="nota" id="msg"></span></div>
<div class="nota" id="analisis"></div>
<p class="nota">Para revisar y guardar en el mapa, usa la estación de tierra: pestaña Cargar, botón Cámara del dron.</p>
</main><script>
const N={sana:"Sana",sigatoka:"Sigatoka",otra_condicion:"Otra condición",sin_hoja:"Sin hojas de plátano"};
const txt=(a,u)=>(a.confianza>=u||a.clase==="sin_hoja")?`${N[a.clase]||a.clase} · ${Math.round(a.confianza*100)} %`:`No está seguro (${N[a.clase]||a.clase} ${Math.round(a.confianza*100)} %)`;
async function estado(){try{const e=await (await fetch("/estado")).json();const a=e.analisis_foto,v=e.en_vivo;
document.getElementById("diag").textContent=!e.modelo?"Sin modelo en el dron":v?"En vivo: "+txt(v,e.modelo.umbral):"Revisando el video...";
document.getElementById("vivo").textContent=v?`${v.n_parches} trozos de hoja, ${v.n_sintomas} con síntomas · ${v.lado?`cuadro de ${v.lado} px`:"decidió la foto completa"} · revisado hace ${v.edad_s} s · tarda ${(v.ms/1000).toFixed(1)} s`:"";
document.getElementById("analisis").textContent=!a?"":a.pendiente?"Revisando la foto...":a.error?"No se pudo revisar la foto":`Última foto ${a.archivo}: ${txt(a,e.modelo.umbral)} · `+
`${a.n_hojas?`${a.n_hojas} hojas, ${a.n_hojas_sintomas} con síntomas · `:""}${a.n_parches} trozos de hoja, ${a.n_sintomas} con síntomas · ${(a.ms/1000).toFixed(1)} s`;
document.getElementById("gps").textContent=e.gps?`GPS ${e.gps.lat.toFixed(6)}, ${e.gps.lon.toFixed(6)} · ${e.gps.satelites} satélites`:"GPS: sin señal";
}catch(x){document.getElementById("diag").textContent="Sin conexión con el dron";}}
setInterval(estado,500);estado();
document.getElementById("foto").onclick=async()=>{const r=await (await fetch("/foto",{method:"POST"})).json();
document.getElementById("msg").textContent=r.ok?"Guardada: "+r.archivo:"No se pudo tomar";};
</script></body></html>"""


# PAGINA WEB EN LA JETSON (video, estado y fotos)
def crear_servidor(modelo):
    class Manejador(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def responder(self, codigo, tipo, cuerpo):
            self.send_response(codigo)
            self.send_header("Content-Type", tipo)
            self.send_header("Content-Length", str(len(cuerpo)))
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(cuerpo)

        def responder_json(self, datos, codigo=200):
            self.responder(codigo, "application/json; charset=utf-8",
                           json.dumps(datos).encode("utf-8"))

        def do_OPTIONS(self):
            self.send_response(204)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.send_header("Access-Control-Allow-Headers", "*")
            self.end_headers()

        def do_GET(self):
            ruta = self.path.split("?")[0]

            if ruta == "/":
                self.responder(200, "text/html; charset=utf-8", PAGINA.encode("utf-8"))
            elif ruta == "/video":
                self.enviar_video()
            elif ruta == "/estado":
                self.responder_json(estado_actual(modelo))
            elif ruta.startswith("/fotos/"):
                nombre = unquote(ruta[len("/fotos/"):])
                sub = ""

                if nombre.startswith("sin_texto/"):
                    sub, nombre = "sin_texto", nombre[len("sin_texto/"):]

                archivo = CARPETA / sub / nombre

                if "/" in nombre or not nombre.endswith(".jpg") or not archivo.is_file():
                    self.responder_json({"ok": False, "error": "No existe esa foto"}, 404)
                else:
                    self.responder(200, "image/jpeg", archivo.read_bytes())
            else:
                self.responder_json({"ok": False, "error": "No encontrado"}, 404)

        def do_POST(self):
            if self.path.split("?")[0] != "/foto":
                self.responder_json({"ok": False, "error": "No encontrado"}, 404)
                return

            try:
                ruta = tomar_foto()
            except Exception as e:
                self.responder_json({"ok": False, "error": str(e)}, 500)
                return

            if ruta is None:
                self.responder_json({"ok": False, "error": "Todavía no hay imagen de la cámara"}, 503)
            else:
                limpia = CARPETA / "sin_texto" / ruta.name
                self.responder_json({
                    "ok": True,
                    "archivo": ruta.name,
                    "url": f"/fotos/{ruta.name}",
                    "url_sin_texto": f"/fotos/sin_texto/{ruta.name}" if limpia.is_file() else None
                })

        def enviar_video(self):
            global clientes_video

            self.send_response(200)
            self.send_header("Content-Type", "multipart/x-mixed-replace; boundary=cuadro")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()

            with clientes_lock:
                clientes_video += 1

            visto = -1

            try:
                while True:
                    with video_cond:
                        video_cond.wait_for(lambda: video["n"] != visto, timeout=2)
                        jpeg, visto = video["jpeg"], video["n"]

                    if jpeg is None:
                        continue

                    self.wfile.write(b"--cuadro\r\nContent-Type: image/jpeg\r\n")
                    self.wfile.write(f"Content-Length: {len(jpeg)}\r\n\r\n".encode())
                    self.wfile.write(jpeg)
                    self.wfile.write(b"\r\n")

            except (BrokenPipeError, ConnectionResetError, TimeoutError):
                pass

            finally:
                with clientes_lock:
                    clientes_video -= 1

    servidor = ThreadingHTTPServer(("0.0.0.0", PUERTO_WEB), Manejador)
    servidor.daemon_threads = True
    return servidor


def direcciones_ip():
    ips = set()

    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ips.add(s.getsockname()[0])
        s.close()
    except OSError:
        pass

    try:
        ips.update(os.popen("hostname -I").read().split())
    except OSError:
        pass

    return sorted(ip for ip in ips if "." in ip and not ip.startswith("127."))


def salir(*args):
    raise KeyboardInterrupt


signal.signal(signal.SIGTERM, salir)


# INICIAR LECTURA GPS
hilo = threading.Thread(
    target=leer_gps,
    daemon=True
)
hilo.start()


# ABRIR CAMARA ZED RIGHT
print("Iniciando ZED X Mini...")

zed = sl.Camera()

config = sl.InitParameters()
config.camera_resolution = sl.RESOLUTION.HD1200
config.camera_fps = 30
config.depth_mode = sl.DEPTH_MODE.NONE

estado = zed.open(config)

if estado != sl.ERROR_CODE.SUCCESS:
    raise RuntimeError(f"Error ZED: {estado}")

print("Camara RIGHT conectada")


# INICIAR MODELO Y PAGINA WEB
modelo = cargar_modelo()

threading.Thread(target=codificar_video, daemon=True).start()
if modelo is not None and ANALIZAR_EN_VIVO:
    threading.Thread(target=analizar_en_vivo, daemon=True).start()

try:
    servidor = crear_servidor(modelo)
    threading.Thread(target=servidor.serve_forever, daemon=True).start()

    for ip in direcciones_ip() or ["<ip-de-la-jetson>"]:
        print(f"[WEB] http://{ip}:{PUERTO_WEB}  (en la estación: Cargar > Cámara del dron > {ip})")
except OSError as e:
    print(f"[WEB] No se pudo abrir el puerto {PUERTO_WEB}: {e}")

if CON_VENTANA:
    print("S = Fotografia | Q = Salir")
else:
    print("Sin ventana: fotos desde la página | Ctrl+C = Salir")

imagen_zed = sl.Mat()

try:
    while True:
        if zed.grab() != sl.ERROR_CODE.SUCCESS:
            if CON_VENTANA and cv2.waitKey(1) & 0xFF == ord("q"):
                break
            if not CON_VENTANA:
                time.sleep(0.01)
            continue

        # SENSOR DERECHO
        zed.retrieve_image(
            imagen_zed,
            sl.VIEW.RIGHT
        )

        frame = cv2.cvtColor(
            imagen_zed.get_data(),
            cv2.COLOR_BGRA2BGR
        )

        instante = datetime.now().astimezone()

        with cuadro_lock:
            ultimo["frame"] = frame
            ultimo["instante"] = instante
            ultimo["n"] += 1

        if not CON_VENTANA:
            continue

        # La ventana muestra fecha, hora, GPS y la detección en vivo (texto y cuadros con síntomas)
        gps = obtener_gps()
        if ANALIZAR_EN_VIVO and modelo is not None:
            with vivo_lock:
                r_vivo = vivo["r"]
            a_vivo = resumen_analisis(None, r_vivo, 0) if r_vivo is not None else None
            pantalla = dibujar_cuadros(dibujar_textos(frame, gps, instante, texto_resultado(a_vivo, "EN VIVO", "REVISANDO...")), r_vivo)
        else:
            pantalla = dibujar_textos(frame, gps, instante, texto_resultado(fotos.get("analisis"), "ULTIMA FOTO"))

        cv2.imshow(
            "ZED X Mini - RIGHT + GPS",
            pantalla
        )

        tecla = cv2.waitKey(1) & 0xFF

        if tecla == ord("s"):
            guardar_foto(frame, gps, instante)

        elif tecla == ord("q"):
            break

except KeyboardInterrupt:
    print("Programa detenido")

finally:
    print("Cerrando ZED...")
    zed.close()
    if CON_VENTANA:
        cv2.destroyAllWindows()
