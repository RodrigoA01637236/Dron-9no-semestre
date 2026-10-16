r"""Captura de fotos en la Jetson (o en cualquier PC) con su archivo de ubicación.

Sirve con cualquier cámara, para no depender de ZED Explorer:
  --fuente usb    webcam USB / cámara integrada (OpenCV). Funciona sin drivers.
  --fuente argus  cámara CSI/GMSL por nvarguscamerasrc (la ZED X sin el ZED SDK;
                  necesita el OpenCV de la Jetson, que trae GStreamer).
  --fuente zed    ZED por el ZED SDK (pyzed), imagen izquierda.

Cada disparo deja dos archivos con el mismo nombre en data/flights/<vuelo>/:
HHMMSS_0001.jpg y HHMMSS_0001.json (formato de docs/04 §5: ts, seq, lat, lon,
alt_rel_m, gps_ok...). Sin Pixhawk o sin fix, la foto se guarda igual con
gps_ok: false. Arrastra la carpeta a la pestaña Cargar de la estación: lee los .json.

Uso:
    python vision/capture.py                          # Enter = foto, q + Enter = salir
    python vision/capture.py --intervalo 2            # una foto cada 2 s (Ctrl+C para parar)
    python vision/capture.py --intervalo 2 --cantidad 20
    python vision/capture.py --camara 1 --resolucion 1920x1080
    python vision/capture.py --fuente argus --sensor-id 0
    python vision/capture.py --mavlink /dev/ttyACM0   # agrega GPS (pip install pymavlink)
    python vision/capture.py --vuelo prueba-patio --operador SH
"""
import argparse
import json
import os
import re
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path

import cv2

SALIDA = Path("data/flights")
CALENTAR = 10  # cuadros que se tiran al abrir, para que se ajuste la exposición


# ---------- Cámaras ----------
class CamaraOpenCV:
    def __init__(self, fuente):
        self.cap = cv2.VideoCapture(*fuente)
        if not self.cap.isOpened():
            raise RuntimeError("No se pudo abrir la cámara. Prueba otro --camara (0, 1, 2...).")

    def leer(self):
        ok, img = self.cap.read()
        return img if ok else None

    def cerrar(self):
        self.cap.release()


def camara_usb(indice, w, h):
    cam = CamaraOpenCV((indice,))
    cam.cap.set(cv2.CAP_PROP_FRAME_WIDTH, w)
    cam.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, h)
    cam.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    return cam


def camara_argus(sensor, w, h):
    tubo = (f"nvarguscamerasrc sensor-id={sensor} ! "
            f"video/x-raw(memory:NVMM),width={w},height={h},framerate=30/1 ! "
            "nvvidconv ! video/x-raw,format=BGRx ! videoconvert ! video/x-raw,format=BGR ! "
            "appsink drop=1 max-buffers=1")
    if not re.search(r"GStreamer:\s+YES", cv2.getBuildInformation()):
        print("Aviso: este OpenCV podría no tener GStreamer. En la Jetson usa el de apt "
              "(sudo apt install python3-opencv), no el de pip.")
    return CamaraOpenCV((tubo, cv2.CAP_GSTREAMER))


class CamaraZED:
    def __init__(self):
        import pyzed.sl as sl
        self.sl = sl
        self.cam = sl.Camera()
        ini = sl.InitParameters()
        ini.camera_resolution = sl.RESOLUTION.HD1200
        ini.depth_mode = sl.DEPTH_MODE.NONE
        estado = self.cam.open(ini)
        if estado != sl.ERROR_CODE.SUCCESS:
            raise RuntimeError(f"El ZED SDK no abrió la cámara: {estado}")
        self.mat = sl.Mat()

    def leer(self):
        if self.cam.grab() != self.sl.ERROR_CODE.SUCCESS:
            return None
        self.cam.retrieve_image(self.mat, self.sl.VIEW.LEFT)
        return cv2.cvtColor(self.mat.get_data(), cv2.COLOR_BGRA2BGR)

    def cerrar(self):
        self.cam.close()


# ---------- Telemetría (opcional) ----------
class Telemetria:
    """Lee la Pixhawk en segundo plano y guarda la última posición conocida."""

    def __init__(self, conexion, baud):
        from pymavlink import mavutil
        self.m = mavutil.mavlink_connection(conexion, baud=baud)
        print(f"Esperando heartbeat de la Pixhawk en {conexion}...")
        if self.m.wait_heartbeat(timeout=15) is None:
            raise RuntimeError("No llegó heartbeat. Revisa el cable / puerto / baudios.")
        self.m.mav.request_data_stream_send(self.m.target_system, self.m.target_component,
                                            mavutil.mavlink.MAV_DATA_STREAM_ALL, 5, 1)
        self.ultimo = {}
        self.t_pos = 0.0
        threading.Thread(target=self._leer, daemon=True).start()

    def _leer(self):
        while True:
            msg = self.m.recv_match(type=["GLOBAL_POSITION_INT", "GPS_RAW_INT", "SYS_STATUS"],
                                    blocking=True, timeout=1)
            if msg is None:
                continue
            if msg.get_type() == "SYS_STATUS":
                if msg.battery_remaining >= 0:
                    self.ultimo["battery_pct"] = float(msg.battery_remaining)
            elif msg.get_type() == "GPS_RAW_INT":
                self.ultimo.update(fix_type=msg.fix_type, satelites=msg.satellites_visible,
                                   hdop=msg.eph / 100 if msg.eph != 65535 else None)
            else:
                self.ultimo.update(lat=msg.lat / 1e7, lon=msg.lon / 1e7, alt_rel_m=msg.relative_alt / 1000,
                                   heading_deg=msg.hdg / 100 if msg.hdg != 65535 else None)
                self.t_pos = time.time()

    def ahora(self):
        d = dict(self.ultimo)
        edad = time.time() - self.t_pos if self.t_pos else None
        d["edad_gps_s"] = round(edad, 2) if edad is not None else None
        # Solo cuenta como ubicación válida con fix 3D y un dato de menos de 2 s.
        d["gps_ok"] = bool(d.get("fix_type", 0) >= 3 and edad is not None and edad < 2)
        if not d["gps_ok"]:
            d["lat"] = d["lon"] = None
        return d


# ---------- Guardado ----------
def nitidez(img):
    """Varianza del laplaciano: valores bajos = foto movida o fuera de foco."""
    gris = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gris, cv2.CV_64F).var())


def escribir_atomico(ruta, texto):
    """Escribe y luego renombra: si se corta la energía no queda un JSON a medias."""
    tmp = ruta.with_suffix(ruta.suffix + ".tmp")
    tmp.write_text(texto, encoding="utf-8")
    os.replace(tmp, ruta)


def guardar(img, carpeta, seq, camara, vuelo, operador, tele):
    t = datetime.now().astimezone()
    carpeta.mkdir(parents=True, exist_ok=True)
    base = carpeta / f"{t:%H%M%S}_{seq:04d}"
    cv2.imwrite(str(base.with_suffix(".jpg")), img, [cv2.IMWRITE_JPEG_QUALITY, 92])
    meta = {
        "ts": t.isoformat(timespec="milliseconds"),
        "seq": seq,
        "lat": None, "lon": None, "alt_rel_m": None, "heading_deg": None,
        "gps_ok": False,
        "battery_pct": None,
        "camera": camara, "exposure": "auto",
        "flight_id": vuelo,
        "operator": operador,
        # Extras (no son parte del contrato, la estación los ignora):
        "ts_utc": t.astimezone(timezone.utc).isoformat(timespec="milliseconds"),
        "width": img.shape[1], "height": img.shape[0],
        "sharpness": round(nitidez(img), 1),
    }
    if tele:
        meta.update(tele.ahora())
    escribir_atomico(base.with_suffix(".json"), json.dumps(meta, indent=2))
    return base.with_suffix(".jpg"), meta


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--fuente", choices=["usb", "argus", "zed"], default="usb")
    ap.add_argument("--camara", type=int, default=0, help="índice de la cámara USB")
    ap.add_argument("--sensor-id", type=int, default=0, help="sensor de Argus (ZED X: 0 = izquierda)")
    ap.add_argument("--resolucion", default="1920x1080", help="ANCHOxALTO, p. ej. 1280x720")
    ap.add_argument("--intervalo", type=float, default=0, help="segundos entre fotos (0 = con Enter)")
    ap.add_argument("--cantidad", type=int, default=0, help="parar tras N fotos (0 = sin límite)")
    ap.add_argument("--salida", type=Path, default=SALIDA)
    ap.add_argument("--vuelo", default="", help="nombre de la sesión; por defecto la fecha de hoy")
    ap.add_argument("--operador", default="", help="iniciales de quien captura")
    ap.add_argument("--mavlink", help="conexión a la Pixhawk: /dev/ttyACM0, /dev/ttyTHS1 o udpin:0.0.0.0:14550")
    ap.add_argument("--baud", type=int, default=57600)
    args = ap.parse_args()
    w, h = (int(x) for x in args.resolucion.lower().split("x"))
    hoy = datetime.now().strftime("%Y-%m-%d")
    vuelo = re.sub(r"[^\w.-]+", "-", f"{hoy}_{args.vuelo}" if args.vuelo else hoy)
    carpeta = args.salida / vuelo
    camara = {"usb": f"usb-{args.camara}", "argus": f"argus-{args.sensor_id}", "zed": "zedx-left"}[args.fuente]

    tele = Telemetria(args.mavlink, args.baud) if args.mavlink else None
    if args.fuente == "usb":
        cam = camara_usb(args.camara, w, h)
    elif args.fuente == "argus":
        cam = camara_argus(args.sensor_id, w, h)
    else:
        cam = CamaraZED()

    for _ in range(CALENTAR):
        cam.leer()
    prueba = cam.leer()
    if prueba is None:
        cam.cerrar()
        sys.exit("La cámara abrió pero no entrega imagen.")
    print(f"Cámara lista: {prueba.shape[1]}x{prueba.shape[0]} ({args.fuente}). Fotos en {carpeta.resolve()}")

    n = 0
    try:
        while not args.cantidad or n < args.cantidad:
            if args.intervalo > 0:
                t0 = time.time()
            else:
                if input("Enter = foto, q = salir: ").strip().lower() == "q":
                    break
            img = cam.leer()
            if img is None:
                print("No llegó imagen; reintentando...")
                time.sleep(0.2)
                continue
            n += 1
            ruta, meta = guardar(img, carpeta, n, camara, vuelo, args.operador, tele)
            gps = f"{meta['lat']:.6f}, {meta['lon']:.6f}" if meta["gps_ok"] else "sin GPS"
            aviso = "  (posible foto movida)" if meta["sharpness"] < 50 else ""
            print(f"[{n}] {ruta.name}  nitidez {meta['sharpness']:.0f}  {gps}{aviso}")
            if args.intervalo > 0:
                time.sleep(max(0.0, args.intervalo - (time.time() - t0)))
    except KeyboardInterrupt:
        pass
    finally:
        cam.cerrar()
    print(f"Listo: {n} foto(s) guardadas.")


if __name__ == "__main__":
    main()
