# Jetson Orin Nano — ZED X Mini RIGHT + Pixhawk GPS

Este directorio contiene el script de captura probado en la Jetson Orin Nano del proyecto de detección de Sigatoka.

## Hardware y comportamiento
- ZED X Mini a través de ZED Link Duo: imagen **RIGHT** (HD1200, 30 FPS solicitado).
- Pixhawk 6C por USB MAVLink: puerto usual `/dev/ttyACM0`.
- GPS HERE4 por DroneCAN al Pixhawk: únicamente se utiliza cuando `GPS_RAW_INT.fix_type >= 3` y la posición es reciente (menos de 3 s).
- Ventana con GPS o `GPS: SIN SENAL` y **sin contador FPS**.
- `S`: toma una fotografía JPEG con texto sobreimpreso y EXIF GPS cuando existe fix válido.
- `Q`: cierra la aplicación.
- Directorio configurado en el script: `/home/jetsonnanoorin/Prueba#1`.
- Nombre: `AA-MM-DD_HH-MM-SS-GPS.jpg`; si varias fotos coinciden en el mismo segundo, sufijos `_2`, `_3`, `_4` y siguientes.
- Fecha (`FECHA`) y hora (`HORA`) visibles sobre el video y la fotografía JPEG.

> El texto "GPS" en el nombre no implica que el JPEG contenga coordenadas. Sin fix válido, la foto se guarda sin datos EXIF GPS. La posición corresponde a la última lectura válida reciente, no a un disparo sincronizado por hardware.

## Metadatos EXIF escritos por el programa

Se tomó y verificó una fotografía en la Jetson con nombre `26-10-16_19-33-19-GPS.jpg`:

- Fecha y hora EXIF: `2026:10:16 19:33:19`.
- Microsegundos: `128640`.
- Software: `Dron Sigatoka - Jetson`.
- Descripción: `ZED X Mini RIGHT; GPS desde Pixhawk HERE4`.
- Comentario EXIF: `Proyecto=Dron Sigatoka; Camara=ZED X Mini RIGHT; FechaHora=2026-10-16T19:33:19.128640-06:00; GPS=SIN_SENAL; FuenteGPS=Pixhawk 6C HERE4; AnalisisYOLO=NO_REALIZADO`.

### Mapeo de información a etiquetas

| Sección | Etiqueta EXIF | Valor |
| --- | --- | --- |
| 0th | `DateTime` | Fecha y hora del reloj de la Jetson: `YYYY:MM:DD HH:MM:SS` |
| 0th | `Software` | `Dron Sigatoka - Jetson` |
| 0th | `ImageDescription` | Identificación de la cámara y la fuente GPS |
| Exif | `DateTimeOriginal` | Misma fecha y hora de la captura |
| Exif | `DateTimeDigitized` | Misma fecha y hora de captura |
| Exif | `SubSecTimeOriginal` | Fracción de segundo en microsegundos |
| Exif | `UserComment` | Proyecto, cámara, fecha ISO 8601 con zona horaria, estado GPS, fuente de GPS, estado YOLO y, si aplica, ubicación y satélites |
| GPS | `GPSVersionID` | Versión de la estructura GPS |
| GPS | `GPSLatitudeRef`, `GPSLatitude` | Hemisferio y latitud en grados/minutos/segundos racionales, solo con fix válido |
| GPS | `GPSLongitudeRef`, `GPSLongitude` | Hemisferio y longitud, solo con fix válido |
| GPS | `GPSAltitudeRef`, `GPSAltitude` | Sentido y magnitud de la altitud, solo con fix válido |

El desplazamiento horario (`-06:00` en la foto probada) está escrito en `UserComment`, **no** en un tag EXIF `OffsetTimeOriginal` independiente. El texto de la pantalla y los metadatos se forman a partir del mismo `instante` del reloj del sistema; el instante corresponde al ciclo de captura del fotograma, no a un disparo sincronizado por hardware.

Un estado `GPS=SIN_SENAL` implica que no se escriben campos de latitud/longitud/altitud EXIF. El GPS válido requiere fix 3D y dato con menos de 3 segundos de antigüedad. La prueba con coordenadas GPS reales sigue pendiente de hacer en exterior. El campo `AnalisisYOLO=NO_REALIZADO` es un marcador; **no** hay todavía análisis ni porcentaje calculado por YOLO.

### Leer los metadatos de la fotografía más reciente

```bash
source ~/ZED_Pruebas/.venv/bin/activate
python3 - <<'PY'
from pathlib import Path
import piexif
import piexif.helper

foto = max((Path.home() / "Prueba#1").glob("*.jpg"),
           key=lambda archivo: archivo.stat().st_mtime)
datos = piexif.load(str(foto))
print("Archivo:", foto.name)
for seccion, etiqueta in [
    ("0th", piexif.ImageIFD.DateTime),
    ("Exif", piexif.ExifIFD.DateTimeOriginal),
    ("Exif", piexif.ExifIFD.DateTimeDigitized),
    ("Exif", piexif.ExifIFD.SubSecTimeOriginal)
]:
    print(piexif.TAGS[seccion][etiqueta]["name"], datos[seccion].get(etiqueta))
comentario = datos["Exif"].get(piexif.ExifIFD.UserComment)
if comentario:
    print("UserComment:", piexif.helper.UserComment.load(comentario))
print("GPS:", datos["GPS"] or "SIN_SENAL")
PY
```

El programa evita sobrescribir imágenes con apertura exclusiva (`xb`). Cuando una captura comparte el mismo segundo con otra, añade `_2`, `_3`, etc. El contador se reinicia con cada segundo; no hay un contador global de fotografías.

## Entorno Python

El proyecto se probó con Python 3.12 en un entorno virtual con acceso a paquetes del sistema. La instalación del SDK ZED (`pyzed.sl`) debe realizarse de forma compatible con JetPack y el SDK instalado en la Jetson.

```bash
sudo apt install -y python3-venv
mkdir -p ~/ZED_Pruebas
python3 -m venv ~/ZED_Pruebas/.venv --system-site-packages
source ~/ZED_Pruebas/.venv/bin/activate
python -m pip install pymavlink piexif Pillow "numpy==1.26.4"
python -c "import numpy, cv2, pyzed.sl, piexif, pymavlink; print('Dependencias OK')"
```

Se utilizó NumPy 1.26.4 porque el OpenCV 4.8.0 del sistema no cargaba con NumPy 2.5.3. Evitar reemplazar a ciegas OpenCV o bibliotecas NVIDIA.

## Permisos Pixhawk USB

```bash
lsusb
ls -l /dev/ttyACM0
sudo usermod -aG dialout "$USER"
```

Cerrar sesión y volver a entrar para aplicar el cambio permanentemente; `newgrp dialout` puede servir temporalmente en una terminal nueva.

## Ejecución manual

Copiar `zed_right.py` al directorio `~/ZED_Pruebas/`. Cerrar ZED Studio y otras instancias de `zed_right.py`.

```bash
source ~/ZED_Pruebas/.venv/bin/activate
python ~/ZED_Pruebas/zed_right.py
```

No iniciar una segunda instancia mientras la cámara está ocupada. QGroundControl u otro lector del puerto serial puede interferir con MAVLink.

## Arranque automático gráfico

El arranque automático usado para la Jetson inicia después de que Ubuntu abre una sesión gráfica. El lanzador de ejemplo `iniciar_zed.sh` está en esta carpeta; espera 30 segundos, bloquea instancias duplicadas y reintenta la cámara tras errores de apertura.

```bash
cp jetson/iniciar_zed.sh ~/ZED_Pruebas/iniciar_zed.sh
chmod +x ~/ZED_Pruebas/iniciar_zed.sh
mkdir -p ~/.config/autostart
cat > ~/.config/autostart/zed-right.desktop <<'EOF'
[Desktop Entry]
Type=Application
Name=ZED RIGHT + GPS
Exec=/home/jetsonnanoorin/ZED_Pruebas/iniciar_zed.sh
Path=/home/jetsonnanoorin/ZED_Pruebas
Terminal=false
X-GNOME-Autostart-enabled=true
EOF
```

No dejar simultáneamente habilitado el viejo autostart de ZED Studio. Si se utilizaba `zed-fotos-gps.service` para vigilar imágenes, deshabilitarlo mientras este programa accede directamente al Pixhawk.

Para revisar errores:
```bash
tail -n 80 ~/ZED_Pruebas/zed-right.log
pgrep -af 'zed_right.py|ZED_Studio'
```

Para detener el autostart, quitar `~/.config/autostart/zed-right.desktop`.

## Limitaciones por verificar en campo

Las pruebas interiores confirmaron el enlace MAVLink, pero el HERE4 no obtuvo fix GPS (0 satélites). Falta validar coordenadas EXIF reales en exterior. También conviene manejar la asignación dinámica del puerto USB y la sincronización precisa de fotografías con GNSS en una versión posterior.
