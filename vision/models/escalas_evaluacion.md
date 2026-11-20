# Tamaño del cuadro (sigatoka_cls_v2.onnx)

Generado por `vision/train/evaluar_escalas.py` el 2026-11-20. Un tamaño: cuadro de 384 px (lado_min_rel 0.3). Dos tamaños: además uno de 0.5 del lado corto, con la regla de `elegir_escala` (vision/parches.py): manda el chico si encuentra Sigatoka con seguridad y el grande no dice "sin hoja"; si no, manda el grande. Umbral de seguridad 0.7.

- Fotos de prueba: 787 (carpeta `test`), fuentes excluidas: v1_publico.

## Fotos tal cual (224-1000 px)

| Regla | Exactitud | Acierto otra_condicion | Acierto sana | Acierto sigatoka | Acierto sin_hoja |
|---|---|---|---|---|---|
| Un tamaño (antes) | 93.4% | 78.3% | 97.0% | 94.6% | 96.5% |
| Dos tamaños (ahora) | 93.4% | 78.3% | 97.0% | 94.6% | 96.5% |

Fotos de Sigatoka: antes {'sigatoka': 106, 'no_seguro': 4, 'otra_condicion': 2}; ahora {'sigatoka': 106, 'no_seguro': 4, 'otra_condicion': 2}.

## Las mismas fotos a 1920 px (de cerca, como el dron)

| Regla | Exactitud | Acierto otra_condicion | Acierto sana | Acierto sigatoka | Acierto sin_hoja |
|---|---|---|---|---|---|
| Un tamaño (antes) | 80.4% | 93.0% | 86.4% | 75.0% | 74.1% |
| Dos tamaños (ahora) | 95.8% | 90.7% | 96.5% | 94.6% | 97.7% |

Fotos de Sigatoka: antes {'otra_condicion': 28, 'sigatoka': 84}; ahora {'sigatoka': 106, 'otra_condicion': 6}.

## Seis fotos por lienzo de 1920 x 1200 (hojas chicas, toma abierta)

| Regla | Exactitud | Acierto otra_condicion | Acierto sana | Acierto sigatoka | Acierto sin_hoja |
|---|---|---|---|---|---|
| Un tamaño (antes) | 98.0% | 96.9% | 97.5% | 100.0% | 98.0% |
| Dos tamaños (ahora) | 97.7% | 89.9% | 98.0% | 100.0% | 99.7% |

Fotos de Sigatoka: antes {'sigatoka': 112}; ahora {'sigatoka': 112}.

## Fotos aéreas con Sigatoka (sin etiqueta por foto)

25 fotos. Salen Sigatoka: antes 15, ahora 15.
