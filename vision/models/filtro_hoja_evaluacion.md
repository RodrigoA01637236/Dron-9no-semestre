# Evaluación del filtro de hoja (sigatoka_cls_v2.onnx)

Generado por `vision/train/evaluar_filtro.py` el 2026-11-18. No cambia el modelo: entrena sondas de prueba con la misma receta que `filtro_hoja.py` (regresión logística, λ = 0.01).

- Fotos de hoja: 3866 de 9 fuentes: azam 1280, bananalsd 897, bangladesh2 424, bd_reconocimiento 408, dl_hailu 815, dl_nutr 3, dl_peru 6, dl_uav 25, samples 8.
- Fuentes excluidas: colombia_uav, v1_publico.
- Objetos para entrenar la sonda: 1200 imágenes. Objetos solo para medir: 760 (nunca se usaron para entrenar).

## Fotos de hoja que el filtro vuelve "sin hoja" (dejando fuera una fuente a la vez)

Regla final (fotos por cuadros): la foto cuenta como sin hoja solo si ningún cuadro de hoja pasa el umbral.

| Umbral | Fotos (por cuadros) | Video (foto completa) |
|---|---|---|
| -6 | 0 de 3866 | 0 de 3866 |
| -5 | 0 de 3866 | 1 de 3866 |
| -4 | 0 de 3866 | 3 de 3866 |
| -3 (elegido) | 5 de 3866 | 18 de 3866 |
| -2.5 | 13 de 3866 | 33 de 3866 |
| -2 | 25 de 3866 | 64 de 3866 |

Primera versión (cuadro por cuadro, umbral -4 si el cuadro tiene color de hoja y 0 si no), reentrenada con las mismas fuentes: cambia el veredicto de 39 de 3866 fotos.

Por fuente, con el umbral elegido (-3):

| Fuente | Fotos | Cambian (fotos) | Cambian (video) |
|---|---|---|---|
| azam | 1280 | 0 | 15 |
| bananalsd | 897 | 1 | 1 |
| bangladesh2 | 424 | 0 | 0 |
| bd_reconocimiento | 408 | 1 | 1 |
| dl_hailu | 815 | 3 | 1 |
| dl_nutr | 3 | 0 | 0 |
| dl_peru | 6 | 0 | 0 |
| dl_uav | 25 | 0 | 0 |
| samples | 8 | 0 | 0 |

## Objetos que el modelo sigue aceptando como hoja

Sin filtro: 130 de 760 por cuadros y 10 de 760 con la foto completa. De las 56 aceptadas por cuadros con poco color de hoja (menos de 15 %), cuántas quedan:

| Umbral | Fotos (por cuadros) | De ellas, con poco verde | Video (foto completa) |
|---|---|---|---|
| -6 | 127 | 55 | 9 |
| -5 | 118 | 48 | 8 |
| -4 | 108 | 42 | 8 |
| -3 (elegido) | 85 | 29 | 4 |
| -2.5 | 67 | 20 | 4 |
| -2 | 42 | 10 | 4 |

Primera versión (cuadro por cuadro): 61 de 760.

