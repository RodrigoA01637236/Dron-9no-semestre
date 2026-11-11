# Evaluación de sigatoka_cls_v2

Generado por `vision/train/calibrar.py` el 2026-11-11 con `C:\dron\runs\noche\n\weights\best.onnx`.

- Temperatura: 1.05. Umbral: 0.7. Parches seguros para marcar una foto: 1.
- En las fotos de val diagnostica 96.9% y acierta 95.1% de esas; el resto va a revisión humana.
- Métricas sobre fotos completas, no sobre parches. Datasets públicos: no representan el campo hasta que se pruebe con test_campo.

**Meta de 90% de exactitud** (modelo por parches):

- `test`: 94.6% en 2000 fotos: cumple
- `test_colombia_uav`: 84.7% en 1000 fotos: **no cumple**

### test · todas

| Modelo | Fotos | Exactitud | F1 macro | Recall otra_condicion | Recall sana | Recall sigatoka | Recall sin_hoja | Cobertura | Exactitud en las que diagnostica |
|---|---|---|---|---|---|---|---|---|---|
| v2_parches | 2000 | 94.6 % | 94.6 % | 94.2 % | 92.6 % | 97.4 % | 94.2 % | 97.3 % | 96.0 % |
| v2_foto_completa | 2000 | 93.9 % | 93.9 % | 90.8 % | 94.4 % | 91.6 % | 98.8 % | 93.8 % | 96.3 % |
| v1_foto_completa | 1500 | 66.7 % | 63.6 % | 29.2 % | 98.4 % | 72.6 % | - | 91.3 % | 69.5 % |
| v2_parches_mismas_fotos | 1500 | 94.7 % | 94.8 % | 94.2 % | 92.6 % | 97.4 % | - | 97.3 % | 95.8 % |

Matriz de confusión v2 por parches (filas = real, columnas = predicho):

| real \ predicho | otra_condicion | sana | sigatoka | sin_hoja |
|---|---|---|---|---|
| otra_condicion | 471 | 8 | 20 | 1 |
| sana | 35 | 463 | 2 | 0 |
| sigatoka | 11 | 0 | 487 | 2 |
| sin_hoja | 10 | 10 | 9 | 471 |

### test · fuente azam

| Modelo | Fotos | Exactitud | F1 macro | Recall otra_condicion | Recall sana | Recall sigatoka | Recall sin_hoja | Cobertura | Exactitud en las que diagnostica |
|---|---|---|---|---|---|---|---|---|---|
| v2_parches | 57 | 96.5 % | 98.9 % | - | 100.0 % | - | 95.8 % | 98.2 % | 98.2 % |
| v2_foto_completa | 57 | 100.0 % | 100.0 % | - | 100.0 % | - | 100.0 % | 100.0 % | 100.0 % |
| v1_foto_completa | 9 | 100.0 % | 100.0 % | - | 100.0 % | - | - | 100.0 % | 100.0 % |
| v2_parches_mismas_fotos | 9 | 100.0 % | 100.0 % | - | 100.0 % | - | - | 100.0 % | 100.0 % |

Matriz de confusión v2 por parches (filas = real, columnas = predicho):

| real \ predicho | otra_condicion | sana | sigatoka | sin_hoja |
|---|---|---|---|---|
| sana | 0 | 9 | 0 | 0 |
| sin_hoja | 1 | 0 | 1 | 46 |

### test · fuente bananalsd

| Modelo | Fotos | Exactitud | F1 macro | Recall otra_condicion | Recall sana | Recall sigatoka | Recall sin_hoja | Cobertura | Exactitud en las que diagnostica |
|---|---|---|---|---|---|---|---|---|---|
| v2_parches | 61 | 96.7 % | 96.8 % | 100.0 % | 90.0 % | 97.1 % | - | 96.7 % | 100.0 % |
| v2_foto_completa | 61 | 96.7 % | 96.8 % | 100.0 % | 90.0 % | 97.1 % | - | 96.7 % | 98.3 % |
| v1_foto_completa | 61 | 100.0 % | 100.0 % | 100.0 % | 100.0 % | 100.0 % | - | 100.0 % | 100.0 % |

Matriz de confusión v2 por parches (filas = real, columnas = predicho):

| real \ predicho | otra_condicion | sana | sigatoka | sin_hoja |
|---|---|---|---|---|
| otra_condicion | 17 | 0 | 0 | 0 |
| sana | 1 | 9 | 0 | 0 |
| sigatoka | 0 | 0 | 33 | 1 |

### test · fuente bangladesh2

| Modelo | Fotos | Exactitud | F1 macro | Recall otra_condicion | Recall sana | Recall sigatoka | Recall sin_hoja | Cobertura | Exactitud en las que diagnostica |
|---|---|---|---|---|---|---|---|---|---|
| v2_parches | 13 | 84.6 % | 85.0 % | 66.7 % | 100.0 % | 100.0 % | - | 92.3 % | 83.3 % |
| v2_foto_completa | 13 | 76.9 % | 76.6 % | 66.7 % | 100.0 % | 66.7 % | - | 92.3 % | 83.3 % |
| v1_foto_completa | 13 | 53.8 % | 54.8 % | 16.7 % | 75.0 % | 100.0 % | - | 100.0 % | 53.8 % |

Matriz de confusión v2 por parches (filas = real, columnas = predicho):

| real \ predicho | otra_condicion | sana | sigatoka | sin_hoja |
|---|---|---|---|---|
| otra_condicion | 4 | 0 | 2 | 0 |
| sana | 0 | 4 | 0 | 0 |
| sigatoka | 0 | 0 | 3 | 0 |

### test · fuente bd_reconocimiento

| Modelo | Fotos | Exactitud | F1 macro | Recall otra_condicion | Recall sana | Recall sigatoka | Recall sin_hoja | Cobertura | Exactitud en las que diagnostica |
|---|---|---|---|---|---|---|---|---|---|
| v2_parches | 22 | 72.7 % | 75.6 % | 66.7 % | 100.0 % | 75.0 % | - | 100.0 % | 72.7 % |
| v2_foto_completa | 22 | 72.7 % | 75.6 % | 66.7 % | 100.0 % | 75.0 % | - | 68.2 % | 80.0 % |
| v1_foto_completa | 22 | 40.9 % | 47.3 % | 20.0 % | 100.0 % | 75.0 % | - | 95.5 % | 42.9 % |

Matriz de confusión v2 por parches (filas = real, columnas = predicho):

| real \ predicho | otra_condicion | sana | sigatoka | sin_hoja |
|---|---|---|---|---|
| otra_condicion | 10 | 0 | 5 | 0 |
| sana | 0 | 3 | 0 | 0 |
| sigatoka | 1 | 0 | 3 | 0 |

### test · fuente cafe_peru

| Modelo | Fotos | Exactitud | F1 macro | Recall otra_condicion | Recall sana | Recall sigatoka | Recall sin_hoja | Cobertura | Exactitud en las que diagnostica |
|---|---|---|---|---|---|---|---|---|---|
| v2_parches | 62 | 100.0 % | 100.0 % | - | - | - | 100.0 % | 100.0 % | 100.0 % |
| v2_foto_completa | 62 | 100.0 % | 100.0 % | - | - | - | 100.0 % | 100.0 % | 100.0 % |

Matriz de confusión v2 por parches (filas = real, columnas = predicho):

| real \ predicho | otra_condicion | sana | sigatoka | sin_hoja |
|---|---|---|---|---|
| sin_hoja | 0 | 0 | 0 | 62 |

### test · fuente coco

| Modelo | Fotos | Exactitud | F1 macro | Recall otra_condicion | Recall sana | Recall sigatoka | Recall sin_hoja | Cobertura | Exactitud en las que diagnostica |
|---|---|---|---|---|---|---|---|---|---|
| v2_parches | 90 | 95.6 % | 97.7 % | - | - | - | 95.6 % | 96.7 % | 98.9 % |
| v2_foto_completa | 90 | 96.7 % | 98.3 % | - | - | - | 96.7 % | 95.6 % | 98.8 % |

Matriz de confusión v2 por parches (filas = real, columnas = predicho):

| real \ predicho | otra_condicion | sana | sigatoka | sin_hoja |
|---|---|---|---|---|
| sin_hoja | 1 | 2 | 1 | 86 |

### test · fuente deepweeds

| Modelo | Fotos | Exactitud | F1 macro | Recall otra_condicion | Recall sana | Recall sigatoka | Recall sin_hoja | Cobertura | Exactitud en las que diagnostica |
|---|---|---|---|---|---|---|---|---|---|
| v2_parches | 150 | 100.0 % | 100.0 % | - | - | - | 100.0 % | 100.0 % | 100.0 % |
| v2_foto_completa | 150 | 100.0 % | 100.0 % | - | - | - | 100.0 % | 100.0 % | 100.0 % |

Matriz de confusión v2 por parches (filas = real, columnas = predicho):

| real \ predicho | otra_condicion | sana | sigatoka | sin_hoja |
|---|---|---|---|---|
| sin_hoja | 0 | 0 | 0 | 150 |

### test · fuente hailu

| Modelo | Fotos | Exactitud | F1 macro | Recall otra_condicion | Recall sana | Recall sigatoka | Recall sin_hoja | Cobertura | Exactitud en las que diagnostica |
|---|---|---|---|---|---|---|---|---|---|
| v2_parches | 46 | 95.7 % | 97.8 % | 95.7 % | - | - | - | 80.4 % | 100.0 % |
| v2_foto_completa | 46 | 82.6 % | 90.5 % | 82.6 % | - | - | - | 80.4 % | 89.2 % |
| v1_foto_completa | 46 | 0.0 % | 0.0 % | 0.0 % | - | - | - | 93.5 % | 0.0 % |

Matriz de confusión v2 por parches (filas = real, columnas = predicho):

| real \ predicho | otra_condicion | sana | sigatoka | sin_hoja |
|---|---|---|---|---|
| otra_condicion | 44 | 2 | 0 | 0 |

### test · fuente ibean

| Modelo | Fotos | Exactitud | F1 macro | Recall otra_condicion | Recall sana | Recall sigatoka | Recall sin_hoja | Cobertura | Exactitud en las que diagnostica |
|---|---|---|---|---|---|---|---|---|---|
| v2_parches | 52 | 100.0 % | 100.0 % | - | - | - | 100.0 % | 100.0 % | 100.0 % |
| v2_foto_completa | 52 | 100.0 % | 100.0 % | - | - | - | 100.0 % | 100.0 % | 100.0 % |

Matriz de confusión v2 por parches (filas = real, columnas = predicho):

| real \ predicho | otra_condicion | sana | sigatoka | sin_hoja |
|---|---|---|---|---|
| sin_hoja | 0 | 0 | 0 | 52 |

### test · fuente nmaist

| Modelo | Fotos | Exactitud | F1 macro | Recall otra_condicion | Recall sana | Recall sigatoka | Recall sin_hoja | Cobertura | Exactitud en las que diagnostica |
|---|---|---|---|---|---|---|---|---|---|
| v2_parches | 885 | 99.1 % | 99.1 % | 97.7 % | 99.4 % | 100.0 % | - | 100.0 % | 99.1 % |
| v2_foto_completa | 885 | 97.9 % | 97.8 % | 95.3 % | 99.7 % | 98.1 % | - | 96.7 % | 98.7 % |
| v1_foto_completa | 885 | 64.9 % | 59.9 % | 23.0 % | 97.7 % | 66.6 % | - | 88.8 % | 68.7 % |

Matriz de confusión v2 por parches (filas = real, columnas = predicho):

| real \ predicho | otra_condicion | sana | sigatoka | sin_hoja |
|---|---|---|---|---|
| otra_condicion | 251 | 2 | 4 | 0 |
| sana | 1 | 309 | 1 | 0 |
| sigatoka | 0 | 0 | 317 | 0 |

### test · fuente nutrientes

| Modelo | Fotos | Exactitud | F1 macro | Recall otra_condicion | Recall sana | Recall sigatoka | Recall sin_hoja | Cobertura | Exactitud en las que diagnostica |
|---|---|---|---|---|---|---|---|---|---|
| v2_parches | 94 | 78.7 % | 60.9 % | 93.2 % | 25.0 % | - | - | 93.6 % | 81.8 % |
| v2_foto_completa | 94 | 80.9 % | 62.9 % | 95.9 % | 25.0 % | - | - | 89.4 % | 83.3 % |
| v1_foto_completa | 94 | 41.5 % | 42.4 % | 25.7 % | 100.0 % | - | - | 95.7 % | 40.0 % |

Matriz de confusión v2 por parches (filas = real, columnas = predicho):

| real \ predicho | otra_condicion | sana | sigatoka | sin_hoja |
|---|---|---|---|---|
| otra_condicion | 69 | 4 | 0 | 1 |
| sana | 15 | 5 | 0 | 0 |

### test · fuente peru

| Modelo | Fotos | Exactitud | F1 macro | Recall otra_condicion | Recall sana | Recall sigatoka | Recall sin_hoja | Cobertura | Exactitud en las que diagnostica |
|---|---|---|---|---|---|---|---|---|---|
| v2_parches | 118 | 94.9 % | 94.8 % | 92.5 % | 90.6 % | 100.0 % | - | 100.0 % | 94.9 % |
| v2_foto_completa | 118 | 86.4 % | 86.8 % | 72.5 % | 100.0 % | 89.1 % | - | 83.1 % | 94.9 % |
| v1_foto_completa | 118 | 48.3 % | 50.0 % | 10.0 % | 100.0 % | 45.7 % | - | 88.1 % | 50.0 % |

Matriz de confusión v2 por parches (filas = real, columnas = predicho):

| real \ predicho | otra_condicion | sana | sigatoka | sin_hoja |
|---|---|---|---|---|
| otra_condicion | 37 | 0 | 3 | 0 |
| sana | 3 | 29 | 0 | 0 |
| sigatoka | 0 | 0 | 46 | 0 |

### test · fuente plantdoc

| Modelo | Fotos | Exactitud | F1 macro | Recall otra_condicion | Recall sana | Recall sigatoka | Recall sin_hoja | Cobertura | Exactitud en las que diagnostica |
|---|---|---|---|---|---|---|---|---|---|
| v2_parches | 98 | 76.5 % | 86.7 % | - | - | - | 76.5 % | 90.8 % | 84.3 % |
| v2_foto_completa | 98 | 96.9 % | 98.4 % | - | - | - | 96.9 % | 98.0 % | 99.0 % |

Matriz de confusión v2 por parches (filas = real, columnas = predicho):

| real \ predicho | otra_condicion | sana | sigatoka | sin_hoja |
|---|---|---|---|---|
| sin_hoja | 8 | 8 | 7 | 75 |

### test · fuente v1_publico

| Modelo | Fotos | Exactitud | F1 macro | Recall otra_condicion | Recall sana | Recall sigatoka | Recall sin_hoja | Cobertura | Exactitud en las que diagnostica |
|---|---|---|---|---|---|---|---|---|---|
| v2_parches | 252 | 86.9 % | 84.7 % | 86.7 % | 85.6 % | 88.5 % | - | 90.9 % | 90.0 % |
| v2_foto_completa | 252 | 82.5 % | 82.1 % | 88.9 % | 90.1 % | 70.8 % | - | 84.1 % | 86.8 % |
| v1_foto_completa | 252 | 97.2 % | 96.8 % | 95.6 % | 100.0 % | 94.8 % | - | 96.4 % | 97.9 % |

Matriz de confusión v2 por parches (filas = real, columnas = predicho):

| real \ predicho | otra_condicion | sana | sigatoka | sin_hoja |
|---|---|---|---|---|
| otra_condicion | 39 | 0 | 6 | 0 |
| sana | 15 | 95 | 1 | 0 |
| sigatoka | 10 | 0 | 85 | 1 |

### test_colombia_uav · todas

| Modelo | Fotos | Exactitud | F1 macro | Recall otra_condicion | Recall sana | Recall sigatoka | Recall sin_hoja | Cobertura | Exactitud en las que diagnostica |
|---|---|---|---|---|---|---|---|---|---|
| v2_parches | 1000 | 84.7 % | 84.6 % | - | 77.4 % | 92.0 % | - | 100.0 % | 84.7 % |
| v2_foto_completa | 1000 | 51.0 % | 35.7 % | - | 99.8 % | 2.2 % | - | 99.0 % | 51.0 % |
| v1_foto_completa | 1000 | 52.5 % | 54.2 % | - | 56.0 % | 49.0 % | - | 78.7 % | 55.8 % |

Matriz de confusión v2 por parches (filas = real, columnas = predicho):

| real \ predicho | otra_condicion | sana | sigatoka | sin_hoja |
|---|---|---|---|---|
| sana | 0 | 387 | 113 | 0 |
| sigatoka | 0 | 40 | 460 | 0 |

Lesiones marcadas en `test_colombia_uav` que caen en un parche 'sigatoka': 1738 de 1884.
