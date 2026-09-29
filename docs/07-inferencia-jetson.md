# 07 — Inferencia en la Jetson (TensorRT)

Objetivo: el modelo ONNX entrenado en Colab corre a bordo a ≥10 FPS, integrado con la captura georreferenciada.

## 1. Preparar el entorno en la Jetson

JetPack 7.2.1 ya trae CUDA 13.2, cuDNN y TensorRT instalados. Verificar:

```bash
nvcc --version                     # CUDA 13.2
/usr/src/tensorrt/bin/trtexec --help | head -5   # TensorRT presente
python3 -c "import tensorrt; print(tensorrt.__version__)"
```

Dependencias de Python (en el venv del proyecto):

```bash
source ~/venvs/dron/bin/activate
pip install numpy opencv-python pillow pycuda onnx
```

Nota JetPack 7 / CUDA 13: los wheels de PyTorch para Jetson se publican por versión de JetPack (índice de NVIDIA / jetson-ai-lab). Si el wheel para JP7 aún no existe, **no bloquea nada**: el pipeline de inferencia usa TensorRT nativo (sin PyTorch a bordo); PyTorch solo vive en Colab. Es otra razón del diseño "entrena fuera, infiere dentro".

## 2. Convertir ONNX → engine TensorRT

El engine se construye **en la Jetson** (es específico del hardware y de la versión de TensorRT):

```bash
/usr/src/tensorrt/bin/trtexec \
  --onnx=models/sigatoka_cls_v3.onnx \
  --saveEngine=models/sigatoka_cls_v3_fp16.engine \
  --fp16 \
  --shapes=images:1x3x384x384
```

- `--fp16` duplica aproximadamente el rendimiento con pérdida de precisión normalmente despreciable — **verificarlo**: correr el set de test (o una muestra) contra el ONNX en PC y contra el engine FP16 en la Jetson y comparar predicciones; si divergen >1 %, usar FP32.
- `trtexec` reporta al final la latencia media → primera medición de FPS.
- Reconstruir el engine cada vez que cambie el modelo o se actualice JetPack.

## 3. Servicio de inferencia — `vision/infer.py`

Diseño: proceso que vigila el directorio de capturas (o recibe frames en memoria), corre el engine y emite eventos JSON. Boceto de la parte TensorRT:

```python
import tensorrt as trt, pycuda.driver as cuda, pycuda.autoinit
import numpy as np, cv2, json

class Engine:
    def __init__(self, path):
        logger = trt.Logger(trt.Logger.WARNING)
        with open(path, "rb") as f:
            self.engine = trt.Runtime(logger).deserialize_cuda_engine(f.read())
        self.ctx = self.engine.create_execution_context()
        # reservar buffers de entrada/salida según bindings...

    def infer(self, img_bgr: np.ndarray) -> np.ndarray:
        x = cv2.resize(img_bgr, (384, 384))[:, :, ::-1]      # BGR→RGB
        x = (x.astype(np.float32) / 255.0).transpose(2, 0, 1)[None]
        # copiar a GPU, execute_v2, copiar salida...
        return probs                                          # softmax por clase

def process(photo_path, sidecar_path, engine, classes, threshold):
    img = cv2.imread(str(photo_path))
    probs = engine.infer(img)
    top = int(probs.argmax())
    result = {
        "photo": photo_path.name,
        "clase": classes[top],
        "confianza": float(probs[top]),
        "descartada": float(probs[top]) < threshold,
        **json.loads(sidecar_path.read_text()),   # hereda GPS/ts del sidecar
    }
    out = photo_path.with_suffix(".result.json")
    out.write_text(json.dumps(result))            # la UI lee estos archivos
    return result
```

Reglas:
- El preprocesado (resize, normalización, orden de canales) debe ser **idéntico** al de entrenamiento — la causa #1 de "el modelo funciona en Colab pero no en la Jetson" es un preprocesado distinto.
- La inferencia **nunca bloquea la captura**: procesos separados; si la inferencia se cae, las fotos siguen guardándose y se procesan al reiniciar (cola por archivos pendientes de `.result.json`).
- Umbral de confianza del JSON de metadata del modelo (doc 06); por debajo → `descartada/no_diagnosticable`, que la UI muestra en gris, no en verde.

## 4. Rendimiento y energía

```bash
sudo tegrastats --interval 1000    # en paralelo a una sesión de inferencia
```

Medir y registrar en `docs/bitacora/`: FPS sostenidos, uso de GPU, temperatura y `VDD_IN` (potencia) en cada perfil de `nvpmodel`. Elegir para vuelo el **menor perfil que cumpla ≥10 FPS** — cada watt sale de la batería. Un YOLOv8n-cls a 384 px en una Orin Nano va sobrado incluso en perfiles bajos; si más adelante se pasa a detección/segmentación, repetir la medición.

Si hiciera falta más rendimiento (no se espera): DeepStream SDK acelera pipelines cámara→inferencia completos en GPU, a costa de bastante complejidad. No adoptarlo salvo necesidad medida.

## 5. Arranque automático (systemd)

En campo nadie abre una terminal. Cada servicio (telemetría, captura, inferencia, UI) es una unidad systemd:

```ini
# /etc/systemd/system/dron-infer.service
[Unit]
Description=Servicio de inferencia Sigatoka
After=network.target

[Service]
User=jetson
WorkingDirectory=/home/jetson/proyecto-dron
ExecStart=/home/jetson/venvs/dron/bin/python -m vision.infer
Restart=on-failure
RestartSec=3

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now dron-infer dron-telemetry dron-capture dron-ui
journalctl -u dron-infer -f        # logs en vivo
```

**Criterio de salida de la fase 4 (parte inferencia):** encender la Jetson → sin tocar nada, a los ~60 s el sistema captura, infiere y publica resultados; verificado dos veces desde arranque en frío.
