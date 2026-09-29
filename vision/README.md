# vision/

Código de captura, entrenamiento e inferencia.

| Módulo | Rol | Doc |
|---|---|---|
| `capture.py` | Captura de fotos + sidecar JSON con GPS (lee `mavlink/telemetry.py`) | [04](../docs/04-pixhawk-mavlink.md) §5 |
| `infer.py` | Servicio de inferencia TensorRT sobre las capturas | [07](../docs/07-inferencia-jetson.md) |
| `train/` | Notebooks/scripts de entrenamiento (se ejecutan en Colab) y registro de experimentos | [06](../docs/06-entrenamiento.md) |
| `models/` | Metadata JSON de cada modelo (los `.onnx`/`.engine` no se versionan) | [06](../docs/06-entrenamiento.md) §6 |

Reglas de arquitectura:
- La captura nunca depende de la inferencia ni de la Pixhawk (modo degradado siempre disponible).
- El preprocesado de `infer.py` debe ser idéntico al de entrenamiento.
