# Jetson Orin Nano — ZED X Mini RIGHT + Pixhawk GPS

Este directorio contiene el script de captura probado en la Jetson Orin Nano del proyecto de detección de Sigatoka.

## Hardware y comportamiento
- ZED X Mini a través de ZED Link Duo: imagen **RIGHT** (HD1200, 30 FPS solicitado).
- Pixhawk 6C por USB MAVLink: puerto usual `/dev/ttyACM0`. Si no existe (por ejemplo, al
  reconectar el USB aparece como `ttyACM1`), el script la busca en `/dev/serial/by-id/` y
  `/dev/ttyACM*`, y reintenta cada 3 s sin detener la cámara.
- GPS HERE4 por DroneCAN al Pixhawk: únicamente se utiliza cuando `GPS_RAW_INT.fix_type >= 3` y la posición es reciente (menos de 3 s).
- Ventana con GPS o `GPS: SIN SENAL` y **sin contador FPS**.
- `S`: toma una fotografía JPEG con texto sobreimpreso y EXIF GPS cuando existe fix válido.
- `Q`: cierra la aplicación.
- **Identificación a bordo:** con `vision/models/sigatoka_cls_v1.onnx` presente, un hilo
  clasifica lo que ve la cámara (hasta 5 veces por segundo) y lo muestra en la ventana
  (`DIAG: SIGATOKA 87%`, `DIAG: NO SEGURO`...). Sin el modelo, todo lo demás funciona igual.
- **Página web en el puerto 8080:** video en vivo, GPS, diagnóstico y botón de foto. La
  estación de tierra la usa desde *Cargar > Cámara del dron*; también abre en un celular.
- Sin monitor (o con `--sin-ventana`) no abre ventana: se controla desde la página.
- Directorio configurado en el script: `/home/jetsonnanoorin/Prueba#1`.
- Nombre: `AA-MM-DD_HH-MM-SS-GPS.jpg`; si varias fotos coinciden en el mismo segundo, sufijos `_2`, `_3`, `_4` y siguientes.
- Fecha (`FECHA`), hora (`HORA`), GPS y diagnóstico (`DIAG`) visibles sobre el video y la
  fotografía JPEG (`TEXTO_EN_FOTO = True`).
- **Copia sin texto:** cada foto se guarda también, con el mismo nombre y EXIF, en
  `Prueba#1/sin_texto/`. El texto encima confunde al modelo, así que el dataset, el
  reentrenamiento y la estación de tierra usan esa copia (`COPIA_SIN_TEXTO = True`).

> El texto "GPS" en el nombre no implica que el JPEG contenga coordenadas. Sin fix válido, la foto se guarda sin datos EXIF GPS. La posición corresponde a la última lectura válida reciente, no a un disparo sincronizado por hardware.

## Metadatos EXIF escritos por el programa

Se tomó y verificó una fotografía en la Jetson con nombre `26-10-16_19-33-19-GPS.jpg`:

- Fecha y hora EXIF: `2026:10:16 19:33:19`.
- Microsegundos: `128640`.
- Software: `Dron Sigatoka - Jetson`.
- Descripción: `ZED X Mini RIGHT; GPS desde Pixhawk HERE4`.
- Comentario EXIF: `Proyecto=Dron Sigatoka; Camara=ZED X Mini RIGHT; FechaHora=2026-10-16T19:33:19.128640-06:00; GPS=SIN_SENAL; FuenteGPS=Pixhawk 6C HERE4; AnalisisYOLO=NO_REALIZADO`.
- Con el modelo cargado, `AnalisisYOLO` lleva la clase que vio el dron al tomar la foto, más
  `ConfianzaYOLO=0.873; ModeloYOLO=sigatoka_cls_v1 a bordo`.

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

Un estado `GPS=SIN_SENAL` implica que no se escriben campos de latitud/longitud/altitud EXIF. El GPS válido requiere fix 3D y dato con menos de 3 segundos de antigüedad. La prueba con coordenadas GPS reales sigue pendiente de hacer en exterior. `AnalisisYOLO=NO_REALIZADO` solo aparece si el modelo no está en la Jetson.

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
python -m pip install pymavlink piexif Pillow onnxruntime "numpy==1.26.4"
python -c "import numpy, cv2, pyzed.sl, piexif, pymavlink, onnxruntime; print('Dependencias OK')"
```

Se utilizó NumPy 1.26.4 porque el OpenCV 4.8.0 del sistema no cargaba con NumPy 2.5.3. Evitar reemplazar a ciegas OpenCV o bibliotecas NVIDIA.

## Modelo para la identificación a bordo

El script busca el repo en `~/Dron-9no-semestre` (o en la carpeta de arriba de `jetson/`) y
usa `vision/models/sigatoka_cls_v1.onnx` con el mismo preprocesado que la estación
(`vision/clasificador.py`). El modelo baseline (`sigatoka_cls_v1.onnx`, 5.5 MB) está en el
repo, así que basta con:

```bash
cd ~/Dron-9no-semestre && git pull
bash jetson/zed_control.sh reiniciar
```

Al arrancar debe imprimir `[MODELO] sigatoka_cls_v1.onnx cargado`. Corre en CPU con
onnxruntime; la página muestra cuántos milisegundos tarda cada identificación.

## Página web (video para la estación)

Al arrancar imprime la dirección, por ejemplo:

```
[WEB] http://192.168.1.50:8080  (en la estación: Cargar > Cámara del dron > 192.168.1.50)
```

| Ruta | Qué da |
| --- | --- |
| `/` | Página sencilla para celular: video, diagnóstico, GPS y botón de foto |
| `/video` | Video MJPEG (960 px de ancho, ~12 cuadros/s; solo se codifica si alguien lo ve) |
| `/estado` | JSON con GPS, modelo y la última identificación (`clase`, `confianza`, `probs`, `ms`) |
| `POST /foto` | Toma una foto como la tecla `S` y responde el nombre del archivo |
| `/fotos/<nombre>.jpg` | Descarga una foto de la carpeta de fotos |

La laptop y la Jetson deben estar en la misma red. Si no conecta, revisar que el puerto 8080
no esté bloqueado (`sudo ufw status`; si está activo: `sudo ufw allow 8080/tcp`).

## Permisos Pixhawk USB

```bash
lsusb
ls -l /dev/ttyACM0
sudo usermod -aG dialout "$USER"
```

Cerrar sesión y volver a entrar para aplicar el cambio permanentemente; `newgrp dialout` puede servir temporalmente en una terminal nueva.

## Detener, iniciar y actualizar (zed_control.sh)

El lanzador vuelve a abrir el programa cada vez que se cierra con error, así que para
cerrarlo de verdad (por ejemplo, para correrlo a mano o actualizarlo) se usa:

```bash
cd ~/Dron-9no-semestre
bash jetson/zed_control.sh detener    # cierra la cámara y no deja que se reabra (ni al reiniciar)
bash jetson/zed_control.sh iniciar    # la vuelve a abrir
bash jetson/zed_control.sh reiniciar  # después de un git pull, para usar la versión nueva
bash jetson/zed_control.sh estado     # qué corre, la dirección [WEB] y las últimas líneas del log
bash jetson/zed_control.sh instalar   # una vez: el lanzador pasa a usar jetson/zed_right.py del repo
```

`detener` crea `~/ZED_Pruebas/PAUSA`; mientras exista, ni el lanzador ni el autostart abren
la cámara. `iniciar` lo borra. Cerrar la ventana con `Q` también termina sin que se reabra.

## Ejecución manual

Detener primero lo que esté corriendo, para no tener dos programas peleando por la cámara:

```bash
cd ~/Dron-9no-semestre
bash jetson/zed_control.sh detener
source ~/ZED_Pruebas/.venv/bin/activate
python jetson/zed_right.py
# al terminar: bash jetson/zed_control.sh iniciar
```

No iniciar una segunda instancia mientras la cámara está ocupada. QGroundControl u otro lector del puerto serial puede interferir con MAVLink.

## Arranque automático gráfico

El arranque automático usado para la Jetson inicia después de que Ubuntu abre una sesión gráfica. El lanzador `iniciar_zed.sh` de esta carpeta espera 30 segundos, bloquea instancias duplicadas, reintenta la cámara tras errores de apertura, respeta el archivo `PAUSA` y corre **la versión del repo** (`~/Dron-9no-semestre/jetson/zed_right.py`), así que basta `git pull` + `reiniciar` para actualizar.

```bash
bash jetson/zed_control.sh instalar   # copia el lanzador (respalda el anterior)
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

Para pausar el autostart: `bash jetson/zed_control.sh detener`. Para quitarlo del todo, borrar `~/.config/autostart/zed-right.desktop`.

## Limitaciones por verificar en campo

Las pruebas interiores confirmaron el enlace MAVLink, pero el HERE4 no obtuvo fix GPS (0 satélites). Falta validar coordenadas EXIF reales en exterior. La búsqueda del puerto USB ya está; falta la sincronización precisa de fotografías con GNSS en una versión posterior.
