# vision/

Código de captura, entrenamiento e inferencia.

| Módulo | Rol | Doc |
|---|---|---|
| `capture.py` | Captura de fotos + sidecar JSON con GPS (lee `mavlink/telemetry.py`) | [04](../docs/04-pixhawk-mavlink.md) §5 |
| `clasificador.py` | Predice con el paquete ONNX + JSON; modo foto completa o por parches de hoja | [GUIA-PARCHES](GUIA-PARCHES.md) |
| `parches.py` | Filtro de hoja: cuadros a resolución nativa, máscara ExG y veredicto por parches | [GUIA-PARCHES](GUIA-PARCHES.md) |
| `rasgos.py`, `train/filtro_hoja.py` | Filtro "¿esto es hoja de plátano?": una sonda sobre los rasgos de cada cuadro para que fotos de objetos cotidianos (mesa, mano, pared) no salgan como hoja | [GUIA-NOCHE](GUIA-NOCHE.md) paso 7 |
| `train/preparar_datos.py`, `train/hacer_parches.py`, `train/calibrar.py` | Dataset v2 sin duplicados, parches de entrenamiento, calibración y comparación contra v1 | [GUIA-PARCHES](GUIA-PARCHES.md) |
| `infer.py` | Servicio de inferencia TensorRT sobre las capturas | [07](../docs/07-inferencia-jetson.md) |
| `train/` | Notebooks/scripts de entrenamiento (se ejecutan en Colab) y registro de experimentos | [06](../docs/06-entrenamiento.md) |
| `models/` | Metadata JSON de cada modelo (los `.onnx`/`.engine` no se versionan) | [06](../docs/06-entrenamiento.md) §6 |

Reglas de arquitectura:
- La captura nunca depende de la inferencia ni de la Pixhawk (modo degradado siempre disponible).
- El preprocesado de `infer.py` debe ser idéntico al de entrenamiento.
