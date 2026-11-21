# Tamaño del cuadro (sigatoka_cls_v2.onnx)

Generado por `vision/train/evaluar_escalas.py` el 2026-11-21. Un tamaño: cuadro de 384 px (lado_min_rel 0.3). Dos tamaños: además uno de 0.5 del lado corto, con la regla de `elegir_escala` (vision/parches.py): manda el chico si encuentra Sigatoka con seguridad y el grande no dice "sin hoja"; si no, manda el grande. Foto completa primero (`completa_primero`): la foto completa decide si está segura, salvo que los cuadros encuentren Sigatoka con seguridad. Umbral de seguridad 0.7.

- Fotos de prueba: 787 (carpeta `test`), fuentes excluidas: v1_publico.

## Fotos tal cual (224-1000 px)

| Regla | Exactitud | Acierto otra_condicion | Acierto sana | Acierto sigatoka | Acierto sin_hoja |
|---|---|---|---|---|---|
| Un tamaño | 93.4% | 76.0% | 98.5% | 94.6% | 96.5% |
| Dos tamaños | 93.4% | 76.0% | 98.5% | 94.6% | 96.5% |
| Dos tamaños + foto completa primero (ahora) | 95.5% | 78.3% | 99.0% | 95.5% | 100.0% |

Fotos de Sigatoka: un tamaño {'sigatoka': 106, 'no_seguro': 4, 'otra_condicion': 2}; dos tamaños {'sigatoka': 106, 'no_seguro': 4, 'otra_condicion': 2}; con foto completa primero {'sigatoka': 107, 'no_seguro': 3, 'otra_condicion': 2}.

## Las mismas fotos a 1920 px (de cerca, como el dron)

| Regla | Exactitud | Acierto otra_condicion | Acierto sana | Acierto sigatoka | Acierto sin_hoja |
|---|---|---|---|---|---|
| Un tamaño | 82.7% | 81.4% | 98.5% | 83.0% | 74.1% |
| Dos tamaños | 95.5% | 82.2% | 99.0% | 98.2% | 97.7% |
| Dos tamaños + foto completa primero (ahora) | 95.5% | 76.7% | 99.5% | 99.1% | 99.1% |

Fotos de Sigatoka: un tamaño {'sigatoka': 93, 'otra_condicion': 18, 'sana': 1}; dos tamaños {'sigatoka': 110, 'otra_condicion': 2}; con foto completa primero {'sigatoka': 111, 'otra_condicion': 1}.

## Seis fotos por lienzo de 1920 x 1200 (hojas chicas, toma abierta)

| Regla | Exactitud | Acierto otra_condicion | Acierto sana | Acierto sigatoka | Acierto sin_hoja |
|---|---|---|---|---|---|
| Un tamaño | 97.7% | 91.5% | 100.0% | 100.0% | 98.0% |
| Dos tamaños | 97.0% | 82.2% | 100.0% | 100.0% | 99.7% |
| Dos tamaños + foto completa primero (ahora) | 95.8% | 74.4% | 100.0% | 100.0% | 100.0% |

Fotos de Sigatoka: un tamaño {'sigatoka': 112}; dos tamaños {'sigatoka': 112}; con foto completa primero {'sigatoka': 112}.

## Fotos aéreas con Sigatoka (sin etiqueta por foto)

25 fotos. Salen Sigatoka: un tamaño 15, dos tamaños 15, con foto completa primero 15.
