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


def crear_exif(gps, instante):
    import piexif.helper

    fecha_exif = instante.strftime("%Y:%m:%d %H:%M:%S")
    fecha_iso = instante.isoformat(timespec="microseconds")

    comentario = (
        f"Proyecto=Dron Sigatoka; "
        f"Camara=ZED X Mini RIGHT; "
        f"FechaHora={fecha_iso}; "
        f"GPS={'VALIDO' if gps is not None else 'SIN_SENAL'}; "
        f"FuenteGPS=Pixhawk 6C HERE4; "
        f"AnalisisYOLO=NO_REALIZADO"
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
def guardar_foto(pantalla, gps, instante):
    from PIL import Image

    marca = instante.strftime("%y-%m-%d_%H-%M-%S")
    ruta = CARPETA / f"{marca}-GPS.jpg"

    # Numerar fotos tomadas en el mismo segundo
    numero = 2

    while ruta.exists():
        ruta = CARPETA / f"{marca}-GPS_{numero}.jpg"
        numero += 1

    exif = crear_exif(gps, instante)

    imagen_rgb = cv2.cvtColor(
        pantalla, cv2.COLOR_BGR2RGB
    )

    imagen = Image.fromarray(imagen_rgb)

    # xb impide sobrescribir un archivo existente
    with open(ruta, "xb") as archivo:
        imagen.save(
            archivo,
            format="JPEG",
            quality=95,
            exif=exif
        )

    print("[FOTO]", ruta.name)
    print("[FECHA]", instante.isoformat())

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

        instante = datetime.now().astimezone()
        fecha_visible = instante.strftime("%y-%m-%d")
        hora_visible = instante.strftime("%H:%M:%S")

        # Crear copia para mostrar datos en pantalla
        pantalla = frame.copy()

        if gps is None:
            textos = [
                "RIGHT CAMERA",
                f"FECHA: {fecha_visible}",
                f"HORA: {hora_visible}",
                "GPS: SIN SENAL"
            ]
            color = (0, 0, 255)
        else:
            textos = [
                "RIGHT CAMERA",
                f"FECHA: {fecha_visible}",
                f"HORA: {hora_visible}",
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
            guardar_foto(pantalla, gps, instante)

        elif tecla == ord("q"):
            break

except KeyboardInterrupt:
    print("Programa detenido")

finally:
    print("Cerrando ZED...")
    zed.close()
    cv2.destroyAllWindows()
