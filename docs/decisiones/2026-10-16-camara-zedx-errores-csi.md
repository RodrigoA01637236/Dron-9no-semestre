# 2026-10-16 — ZED X Mini: errores CRC en CSI y driver de otra versión de L4T

## Contexto

ZED Explorer funcionó una vez y después dejó de abrir ("serial number not valid",
`Reboot has failed for CAM0`, `checkStreamStatus: stream reported capture failure`).
Reiniciar `nvargus-daemon` y `zed_x_daemon` no ayudó. Ya se revisó el flex
(cable de cinta) entre la ZED Link Duo y la Jetson, y cada tarjeta tiene su propia alimentación.

## Diagnóstico

Lo que **sí** funciona:
- `ZED_Diagnostic` detecta la cámara por GMSL: `ZED-XG Mini`, serie 55465567, `/dev/i2c-9`, estado *Available*.
- Módulos cargados: `sl_zedx`, `sl_max96712`, `sl_max9295`; `zed_x_daemon` corriendo.
- `nvarguscamerasrc` enumera los modos del sensor (1920×1200 @ 60, 960×600 @ 120, 1920×1080 @ 60).

Lo que falla: en cuanto empiezan a llegar cuadros, la entrada CSI de la Jetson reporta
`PD_CRC_ERR` (CRC del paquete), `SINGLE_BIT_ERR`, `PIX_SHORT`, `CSIMUX_FRAME` para los dos
sensores; el canal de captura no se recupera (`RESET timeout on VI ch: 1`) y
`nvargus-daemon` muere con `SEGV`. Ese crash es el "Connection reset by peer" que ven todas
las apps (ZED Explorer, ZED_Diagnostic, GStreamer).

Versiones instaladas (`/var/log/dpkg.log`):
- Jetson Linux **R39.2.1** (JetPack 7.2.1), instalado el 2026-09-29.
- `stereolabs-zedlink-duo 1.4.4-LI-MAX96712-`**`L4T39.2.0`**, instalado el 2026-10-09.

La página de drivers de Stereolabs solo publica la ZED Link Duo 1.4.4 para **L4T 39.2.0**
(JetPack 7.2.0); no hay paquete para 39.2.1. El driver incluye la configuración del puerto
CSI (overlay `tegra234-p3768-camera-zedlink-duo-sl-overlay.dtbo` y ajustes de NVCSI); una
diferencia entre 39.2.0 y 39.2.1 en esa capa produce justo errores de CRC con un cable bueno.
**Hipótesis principal: el driver no corresponde a la versión de L4T.**

## Opciones

1. **Preguntar a Stereolabs** si hay paquete para L4T 39.2.1 (o si 39.2.0 es compatible).
   Sin costo, pero depende de su tiempo de respuesta. → Mensaje listo abajo.
2. **Bajar a L4T 39.2.0 con apt, sin reflashear** (`scripts/jetson_bajar_l4t_39.2.0.sh`).
   El repo de NVIDIA (`jetson/som` y `jetson/common`, rama r39.2) conserva los paquetes
   39.2.0. Todos los `nvidia-l4t-*` dependen de `nvidia-l4t-core` con versión exacta, así que
   se bajan todos juntos, incluido el firmware de arranque. El script primero simula y se
   detiene si apt quiere quitar algún paquete. Peor caso: no arranca bien → se hace la 3.
3. **Reflashear la Jetson a JetPack 7.2.0 (L4T 39.2.0)**, la versión exacta del driver.
   Mismo Ubuntu 24.04 y misma familia CUDA 13, así que casi nada más cambia.
4. Reflashear a JetPack 6.2.x (L4T 36.5.x), que también tiene driver 1.4.4 y es la rama más
   probada. Solo si en 39.2.0 siguen los errores CRC (entonces no era la versión).
5. Mientras tanto: **webcam USB** con `vision/capture.py --fuente usb` (no depende de nada de esto).

## Decisión

Hacer 1 y 5 hoy. Probar la 2 (bajar con apt); si falla, la 3 (reflasheo).

---

## Opción 2 paso a paso: bajar con apt

```bash
git pull
bash scripts/jetson_bajar_l4t_39.2.0.sh             # simula y muestra qué cambiaría
bash scripts/jetson_bajar_l4t_39.2.0.sh --aplicar   # lo hace (pide escribir SI)
```
El script baja los `nvidia-l4t-*` a 39.2.0, los bloquea con `apt-mark hold`, reinstala el
driver de la ZED Link Duo y explica la verificación. Después: apagado completo, 30 s sin
corriente, y no desconectar durante el primer arranque (actualiza el firmware de arranque).

---

## Opción 3 paso a paso: reflashear a JetPack 7.2.0

**Antes de borrar nada:**
1. Respaldar todo lo que no está en git: `data/`, fotos, `~/venvs` (o al menos `pip freeze > reqs.txt`).
2. Ver desde dónde arranca la Jetson: `findmnt /` y `lsblk` (¿microSD `mmcblk0` o NVMe `nvme0n1`?).

**Flasheo** (con SDK Manager, que sirve para microSD y NVMe):
1. PC con Ubuntu x86 (22.04 o 24.04) y NVIDIA SDK Manager instalado.
2. Poner la Jetson en modo recuperación: apagada, puentear los pines **FC REC** y **GND**
   del header de botones J14 (ver la guía del Developer Kit), conectar el USB‑C a la PC y encender.
   En la PC, `lsusb` debe mostrar `NVIDIA Corp. APX`.
3. En SDK Manager elegir **Jetson Orin Nano Developer Kit**, **JetPack 7.2.0** (no 7.2.1)
   y el destino correcto (microSD o NVMe). Flashear.
4. Si NVIDIA publica imagen de microSD de JetPack 7.2.0 para la Orin Nano y la Jetson arranca
   de microSD, también se puede grabar con Balena Etcher desde Windows.

**Después del flasheo:**
```bash
cat /etc/nv_tegra_release            # debe decir R39 (release), REVISION: 2.0
# Que apt NO la vuelva a subir a 39.2.1:
sudo apt-mark hold $(dpkg -l 'nvidia-l4t-*' | awk '/^ii/{print $2}')

# Driver de la ZED Link Duo para 39.2.0
wget https://download.stereolabs.com/drivers/zedx/1.4.4/R39.2/stereolabs-zedlink-duo_1.4.4-LI-MAX96712-L4T39.2.0_arm64.deb
sudo dpkg -i stereolabs-zedlink-duo_1.4.4-LI-MAX96712-L4T39.2.0_arm64.deb
sudo shutdown -h now                 # apagado completo; desconectar 30 s; encender
```
Luego instalar el ZED SDK para JetPack 7.2 (el instalador `.run` de Stereolabs).

**Verificación** (en este orden):
```bash
gst-launch-1.0 nvarguscamerasrc sensor-id=0 num-buffers=60 ! fakesink   # sin "Correctable Error"
gst-launch-1.0 nvarguscamerasrc sensor-id=1 num-buffers=60 ! fakesink
sudo journalctl -u nvargus-daemon -b --no-pager | grep -c CRC           # debe dar 0
/usr/local/zed/tools/ZED_Explorer
python3 vision/capture.py --fuente argus --cantidad 5                   # o --fuente zed
```

**Regla a partir de ahora:** no correr `sudo apt upgrade` en la Jetson sin revisar antes
qué paquetes `nvidia-l4t-*` va a cambiar.

---

## Mensaje para Stereolabs (foro community.stereolabs.com o support@stereolabs.com)

> **Subject:** ZED Link Duo on JetPack 7.2.1 (L4T 39.2.1): CSI CRC errors, nvargus-daemon crash
>
> Hi, we have a ZED X Mini (serial 55465567) on a ZED Link Duo connected to a Jetson Orin Nano
> Developer Kit (8 GB, "super" DTB) running **JetPack 7.2.1 / L4T R39.2.1**, ZED SDK 5.5.0.
> The only Duo driver available is `stereolabs-zedlink-duo_1.4.4-LI-MAX96712-L4T39.2.0`,
> which we installed on 39.2.1. The card is externally powered.
>
> The camera worked once in ZED Explorer. Since then:
> - ZED_Diagnostic detects the camera over GMSL (`ZED-XG Mini`, `/dev/i2c-9`, state Available);
>   `sl_zedx`, `sl_max96712` and `sl_max9295` are loaded and `zed_x_daemon` is running.
> - `nvarguscamerasrc` lists the sensor modes, but as soon as capture starts nvargus reports
>   `PD_CRC_ERR: CRC error on packet payload`, `SINGLE_BIT_ERR`, `PIX_SHORT`,
>   `CSIMUX_FRAME 0x000002` for sensors 0 and 1, then `RESET timeout on VI ch: 1`, and
>   `nvargus-daemon` exits with SEGV. ZED Explorer shows
>   `[ZED-Argus][Critical] Reboot has failed for CAM0 with current state=4`.
> - We already checked and reseated the CSI flex cable between the card and the Jetson.
>
> Questions: (1) Is there a ZED Link Duo driver for L4T 39.2.1, or is the 39.2.0 package
> expected to work on 39.2.1? (2) If not, should we reflash to JetPack 7.2.0?
> We can attach the full ZED_Diagnostic JSON and `journalctl -u nvargus-daemon` output.
> Thanks!

Adjuntar: el JSON de `ZED_Diagnostic` (correrlo con `sudo` para que incluya `dmesg`) y
`sudo journalctl -u nvargus-daemon -b --no-pager > nvargus.log`.
