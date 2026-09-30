# Registro de experimentos de entrenamiento

Regla: **cada corrida de entrenamiento agrega una fila aquí**, aunque haya salido mal
(los fracasos documentados ahorran repetirlos). Ver [GUIA-MODELO.md](../GUIA-MODELO.md) fase 3.

| # | Fecha | Dataset (versión) | Modelo base | imgsz | epochs | batch | top1 test | F1 por clase (test) | Umbral | Pesos (ruta en Drive) | Notas / análisis de errores |
|---|-------|-------------------|-------------|-------|--------|-------|-----------|---------------------|--------|-----------------------|------------------------------|
| 1 | 2026-09-30 | v1_public_baseline (11,228 imgs: sana 3,029 / sigatoka 3,226 / otra 4,973) | yolov8n-cls (ImageNet) | 384 | 47 (early stop; mejor: 37) | 32 | **0.918** | sigatoka≈0.95, otra≈0.92, sana≈0.89 (de la matriz de val; recalls: sig 0.97 / otra 0.95 / sana 0.83) | 0.65 (default, por afinar con datos de campo) | Drive: `dron/pesos/2026-09-30/` (`best.pt`, `best.onnx`) | Primera corrida. RTX 4060 Laptop, 0.585 h. val top1 0.927. `model.names`: {0: otra_condicion, 1: sana, 2: sigatoka}. Error dominante: 16 % de `sana` predicha como `otra_condicion` (falsa alarma benigna); solo 1 % de `sigatoka` real marcada `sana`. Pendiente: revisar imágenes sanas mal clasificadas. Métrica sobre dataset público — no representa campo. |

## Convenciones

- **Dataset (versión):** el nombre del manifiesto usado, ej. `v1_public_baseline`.
- **F1 por clase:** copiar de la matriz de confusión de `runs/classify/<run>/`, formato
  `sana=0.91, temprana=0.84, avanzada=0.88, otra=0.79`.
- **Pesos:** ruta en Drive de `best.pt` y `best.onnx` (no van a git).
- **Notas:** qué se cambió respecto a la corrida anterior y los 2–3 patrones de error
  principales vistos al revisar las imágenes mal clasificadas.
