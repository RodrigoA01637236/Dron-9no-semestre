import cv2
import time
import threading
from pathlib import Path
from datetime import datetime

import pyzed.sl as sl
import piexif
from pymavlink import mavutil

# CONFIGURACION
CARPETA = Path("/home/jetsonnanoorin/Prueba#1")
PUERTO = "/dev/ttyACM0"

CARPETA.mkdir(parents=True, exist_ok=True)

gps_actual = None
gps_lock = threading.Lock()


# LEER GPS DEL PIXHAWK
def leer_gps():
    global gps_actual

    while True:
        pixhawk = None

        try:
            pixhawk = mavutil.mavlink_connection(
                PUERTO, baud=115200
            )

            hb = pixhawk.wait_heartbeat(timeout=15)

            if hb is None:
                raise RuntimeError("Sin heartbeat")

            print("[GPS] Pixhawk conectado")

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
            print("[GPS]", e)

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


def crear_exif(gps):
    exif = {
        "0th": {},
        "Exif": {},
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
def guardar_foto(pantalla, gps):
    fecha = datetime.now().strftime("%y-%m-%d")

    numero = 1

    while True:
        nombre = f"{fecha}-GPS_{numero:03d}.jpg"
        ruta = CARPETA / nombre

        if not ruta.exists():
            break

        numero += 1

    # Guardar imagen con los textos GPS visibles
    exif = crear_exif(gps)

    from PIL import Image

    imagen_rgb = cv2.cvtColor(
        pantalla, cv2.COLOR_BGR2RGB
    )

    imagen = Image.fromarray(imagen_rgb)

    imagen.save(
        str(ruta),
        format="JPEG",
        quality=95,
        exif=exif
    )

    print("[FOTO]", ruta.name)

    if gps is None:
        print("[FOTO] Sin coordenadas GPS")
    else:
        print("[FOTO] GPS:", gps["lat"], gps["lon"])


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
print("S = Fotografia | Q = Salir")

imagen_zed = sl.Mat()

try:
    while True:
        if zed.grab() != sl.ERROR_CODE.SUCCESS:
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
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

        gps = obtener_gps()

        # Crear copia para mostrar datos en pantalla
        pantalla = frame.copy()

        if gps is None:
            textos = [
                "RIGHT CAMERA",
                "GPS: SIN SENAL"
            ]
            color = (0, 0, 255)
        else:
            textos = [
                "RIGHT CAMERA",
                f"LAT: {gps['lat']:.7f}",
                f"LON: {gps['lon']:.7f}",
                f"ALT: {gps['alt']:.1f} m",
                f"SAT: {gps['satelites']}"
            ]
            color = (0, 255, 0)

        for i, texto in enumerate(textos):
            cv2.putText(
                pantalla,
                texto,
                (30, 50 + i * 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                (0, 0, 0),
                5
            )
            cv2.putText(
                pantalla,
                texto,
                (30, 50 + i * 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.9,
                color,
                2
            )

        cv2.imshow(
            "ZED X Mini - RIGHT + GPS",
            pantalla
        )

        tecla = cv2.waitKey(1) & 0xFF

        if tecla == ord("s"):
            guardar_foto(pantalla, gps)

        elif tecla == ord("q"):
            break

except KeyboardInterrupt:
    print("Programa detenido")

finally:
    print("Cerrando ZED...")
    zed.close()
    cv2.destroyAllWindows()
