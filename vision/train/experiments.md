# Registro de experimentos de entrenamiento

Regla: **cada corrida de entrenamiento agrega una fila aquí**, aunque haya salido mal
(los fracasos documentados ahorran repetirlos). Ver [GUIA-MODELO.md](../GUIA-MODELO.md) fase 3.

| # | Fecha | Dataset (versión) | Modelo base | imgsz | epochs | batch | top1 test | F1 por clase (test) | Umbral | Pesos (ruta en Drive) | Notas / análisis de errores |
|---|-------|-------------------|-------------|-------|--------|-------|-----------|---------------------|--------|-----------------------|------------------------------|
| 1 |       |                   |             |       |        |       |           |                     |        |                       |                              |

## Convenciones

- **Dataset (versión):** el nombre del manifiesto usado, ej. `v1_public_baseline`.
- **F1 por clase:** copiar de la matriz de confusión de `runs/classify/<run>/`, formato
  `sana=0.91, temprana=0.84, avanzada=0.88, otra=0.79`.
- **Pesos:** ruta en Drive de `best.pt` y `best.onnx` (no van a git).
- **Notas:** qué se cambió respecto a la corrida anterior y los 2–3 patrones de error
  principales vistos al revisar las imágenes mal clasificadas.
