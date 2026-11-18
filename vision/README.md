# vision/

Código de captura, entrenamiento e inferencia.

| Módulo | Rol | Doc |
|---|---|---|
| `capture.py` | Captura de fotos + sidecar JSON con GPS (lee `mavlink/telemetry.py`) | [04](../docs/04-pixhawk-mavlink.md) §5 |
| `clasificador.py` | Predice con el paquete ONNX + JSON; modo foto completa o por parches de hoja | [GUIA-PARCHES](GUIA-PARCHES.md) |
| `parches.py` | Filtro de hoja: cuadros a resolución nativa, máscara ExG y veredicto por parches | [GUIA-PARCHES](GUIA-PARCHES.md) |
| `rasgos.py`, `train/filtro_hoja.py`, `train/evaluar_filtro.py`, `train/figura_filtro.py` | Filtro "¿esto es hoja de plátano?": una sonda sobre los rasgos de cada cuadro para que fotos de objetos cotidianos (mesa, mano, pared) no salgan como hoja; entrenarla, evaluarla dejando fuera una fuente a la vez y graficarla | [GUIA-NOCHE](GUIA-NOCHE.md) paso 7, [evaluación](models/filtro_hoja_evaluacion.md), [decisión](../docs/decisiones/2026-11-12-filtro-de-hoja-por-foto.md) |
| `diagnosticar.py` | Explica el resultado de una foto: parches, foto completa (video en vivo) y v1, lado a lado | [jetson/README](../jetson/README.md) |
| `train/preparar_datos.py`, `train/hacer_parches.py`, `train/calibrar.py` | Dataset v2 sin duplicados, parches de entrenamiento, calibración y comparación contra v1 | [GUIA-PARCHES](GUIA-PARCHES.md) |
| `infer.py` | Servicio de inferencia TensorRT sobre las capturas | [07](../docs/07-inferencia-jetson.md) |
| `train/` | Notebooks/scripts de entrenamiento (se ejecutan en Colab) y registro de experimentos | [06](../docs/06-entrenamiento.md) |
| `models/` | Metadata JSON de cada modelo (los `.onnx`/`.engine` no se versionan) | [06](../docs/06-entrenamiento.md) §6 |

Reglas de arquitectura:
- La captura nunca depende de la inferencia ni de la Pixhawk (modo degradado siempre disponible).
- El preprocesado de `infer.py` debe ser idéntico al de entrenamiento.
