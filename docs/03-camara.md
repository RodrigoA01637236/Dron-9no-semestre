# 03 — Cámara: verificación ZED, planes B y protocolo de captura

Este documento cubre la **tarea más urgente del proyecto** (Fase 0): decidir con evidencia qué cámara y qué configuración usará el sistema.

## Contexto del riesgo

La cámara ZED está conectada por **dos cables flex a CAM0/CAM1** de una placa adaptadora. Esto implica casi con certeza que NO es una ZED 2/2i estándar (esas son USB 3.0), sino una **ZED X / ZED X Mini con interfaz GMSL2** conectada a través de una tarjeta de captura (ZED Link Mono/Duo) sobre los conectores CSI de la Jetson. Riesgos apilados:

1. **El ZED SDK y los drivers GMSL de Stereolabs se publican por versión exacta de JetPack/L4T.** JetPack 7.2.1 (L4T R39.2.1) es muy reciente; el soporte puede no existir aún.
2. Aunque el SDK exista para JetPack 7, el **driver de la tarjeta ZED Link** debe coincidir con el kernel de L4T R39.2.1.

## Paso 1 — Identificar la cámara y la tarjeta exactas (30 min)

1. Revisar físicamente las etiquetas de la cámara y de la placa adaptadora (modelo y número de serie).
2. En la Jetson:

```bash
# ¿Se enumera algo en video?
ls -l /dev/video*

# ¿El kernel ve los sensores CSI?
sudo dmesg | grep -iE "imx|gmsl|zed|csi|max9296|max96712"

# ¿Aparece por USB? (si fuera ZED 2/2i USB)
lsusb | grep -i stereolabs
```

3. Anotar los hallazgos en `docs/decisiones/`. Con el modelo exacto se consulta la página de descargas de Stereolabs.

## Paso 2 — Verificar soporte oficial (30 min)

1. Ir a la página de descargas del ZED SDK de Stereolabs (sección "ZED SDK for JetPack") y a la de **ZED Link drivers**.
2. Buscar explícitamente una versión para **JetPack 7.x / L4T R39.x**.
3. Tres resultados posibles:
   - **Existe SDK + driver para JetPack 7.2.x** → instalar y continuar al paso 3.
   - **Existe solo para JetPack 6.x (L4T R36)** → decisión: reflashear (ver árbol abajo).
   - **La cámara es ZED 2/2i USB** (no GMSL) → el SDK USB tiene más probabilidades de funcionar; instalar la versión más cercana y probar.

## Paso 3 — Instalación y prueba del ZED SDK

```bash
# Descargar el instalador correspondiente (ejemplo genérico; usar el de la página oficial)
chmod +x ZED_SDK_*.run
./ZED_SDK_*.run

# Si es ZED X (GMSL): instalar además el driver ZED Link para la L4T exacta,
# siguiendo la guía "Install ZED Link driver" de Stereolabs, y reiniciar.

# Prueba mínima
/usr/local/zed/tools/ZED_Explorer     # debe mostrar video
/usr/local/zed/tools/ZED_Diagnostic   # reporte de salud de la instalación
```

Prueba desde Python (la API que usará el proyecto):

```bash
python3 -m pip install --user pyzed  # o el script get_python_api.py del SDK
python3 - <<'EOF'
import pyzed.sl as sl
cam = sl.Camera()
params = sl.InitParameters()
status = cam.open(params)
print("open:", status)
if status == sl.ERROR_CODE.SUCCESS:
    img = sl.Mat()
    if cam.grab() == sl.ERROR_CODE.SUCCESS:
        cam.retrieve_image(img, sl.VIEW.LEFT)
        img.write("/tmp/zed_test.png")
        print("Foto guardada en /tmp/zed_test.png")
    cam.close()
EOF
```

**Criterio de éxito de la Fase 0:** ese script (o su equivalente del plan B) guarda una foto.

## Árbol de decisión si el SDK NO soporta JetPack 7.2.1

```
¿Stereolabs publica SDK+driver para JetPack 6.x y la cámara es ZED X/2i?
│
├─ SÍ → OPCIÓN A (recomendada): reflashear la Jetson a JetPack 6.x
│        Costo: ~1 día (el proceso de flasheo ya está dominado por el equipo).
│        Beneficio: stack completo soportado oficialmente (ZED SDK 4.x y
│        ecosistema PyTorch/YOLO maduro en JetPack 6).
│        Nota: se pierde CUDA 13.2 → CUDA 12.x; nada del proyecto lo requiere.
│
├─ La cámara entrega video por V4L2 aunque el SDK no funcione
│  (ls /dev/video* muestra los sensores y GStreamer captura)
│  → OPCIÓN B: capturar SIN el SDK, solo el sensor izquierdo:
│        gst-launch-1.0 v4l2src device=/dev/video0 ! ... ! nvjpegenc ! filesink
│        Se pierde: calibración estéreo, profundidad, herramientas ZED.
│        Se conserva: imágenes RGB, que es lo único que el diagnóstico necesita.
│        (Con GMSL esto depende de que el driver de la tarjeta cargue, así que
│        en la práctica suele requerir igualmente la versión correcta de L4T.)
│
└─ Nada de lo anterior funciona en tiempo razonable (>1 semana atascados)
   → OPCIÓN C: cámara alternativa barata y soportada nativamente:
        - CSI: Raspberry Pi HQ Camera (IMX477, ~12 MP) — soportada por
          nvarguscamerasrc en Jetson, excelente calidad/precio.
        - USB: cualquier webcam UVC 1080p+ (funciona con V4L2 sin drivers).
        El proyecto NO necesita estéreo: es clasificación de hojas RGB.
        La ZED se reintegra cuando su soporte llegue, sin cambiar el pipeline.
```

**Regla:** máximo **3 días** de intentos con la ZED antes de ejecutar A o C. La cámara no puede bloquear el semestre.

## Captura con GStreamer (referencia para opciones B/C)

```bash
# Cámara CSI (IMX477 u otra soportada por Argus):
gst-launch-1.0 nvarguscamerasrc num-buffers=1 ! \
  'video/x-raw(memory:NVMM),width=4032,height=3040' ! \
  nvjpegenc ! filesink location=test.jpg

# Webcam USB:
gst-launch-1.0 v4l2src device=/dev/video0 num-buffers=1 ! \
  'image/jpeg,width=1920,height=1080' ! filesink location=test.jpg
```

En Python, OpenCV con backend GStreamer (`cv2.VideoCapture(pipeline, cv2.CAP_GSTREAMER)`) da el mismo resultado integrado al código del proyecto.

## Protocolo de captura para diagnóstico (aplica a cualquier cámara)

La foto solo sirve si un experto puede diagnosticar Sigatoka en ella. Definir y **validar con el fitopatólogo en la primera visita**:

| Parámetro | Valor inicial propuesto | Justificación |
|---|---|---|
| Distancia a la planta | 1.5–3 m | Compromiso entre seguridad de vuelo y resolución por hoja |
| Resolución mínima sobre la hoja | ≥3–5 px/mm (GSD ≤0.3 mm/px) | Las estrías tempranas de Sigatoka miden ~1–2 mm |
| Ángulo | Frontal a la copa + tomas laterales | La Sigatoka inicia en el envés y en hojas jóvenes (2–5) |
| Exposición | Automática con compensación −0.3 EV; velocidad ≥1/500 s | Evitar cielo quemado y motion blur del dron |
| Formato | JPEG máxima calidad (o RAW si la cámara lo da) | Balance almacenamiento/calidad |
| Horario | 9:00–15:00, evitar contraluz | Iluminación consistente para el modelo |

Validación del protocolo: en la visita 1, tomar el mismo set de plantas con el protocolo propuesto y pedir al experto que diagnostique **desde las fotos**. Si no puede, ajustar distancia/resolución antes de recolectar en masa. Registrar el protocolo final como decisión.

## Nota sobre el estéreo

La profundidad de la ZED no aporta al diagnóstico. Si el SDK funciona, puede usarse como extra (distancia a la planta para normalizar escala, odometría visual); si no, no se pierde nada esencial. **Ninguna parte del pipeline debe depender de la profundidad.**
