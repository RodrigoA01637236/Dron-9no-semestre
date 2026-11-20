# 2026-11-20 — Dos tamaños de cuadro para revisar cada foto

## Contexto

Con el dron actualizado (un solo resultado por foto, el de la revisión por cuadros), el equipo
reportó que las fotos de hojas con Sigatoka salían casi siempre como "otra condición". En el
archivo del 17 de noviembre había pasado lo mismo: por cuadros, ninguna de las 71 fotos salió
Sigatoka, y con la foto completa salieron 38.

## Causa

El cuadro de 384 px a resolución nativa no se parece a lo que el modelo vio al entrenar cuando la
foto es de cerca:

- De las 548 fotos reales de Sigatoka de entrenamiento (copia local del dataset, armada con el
  mismo script y las mismas fuentes), 408 (74 %) son chicas: 337 de bananalsd a 224 x 224 y 71
  de bangladesh2 a 320 x 427. En ellas el único cuadro posible es la foto entera
  ampliada a 384. El modelo aprendió Sigatoka viendo la hoja completa y poco nítida.
- En `hacer_parches.py`, el maestro v1 descarta los acercamientos de una foto con Sigatoka
  donde él no ve la mancha, así que quedan aún menos acercamientos de Sigatoka.
- Las fotos nítidas y grandes del entrenamiento (azam, bd_reconocimiento) tienen más "otra
  condición" (249) que Sigatoka (140).

En una foto del dron de cerca (1920 x 1200), un cuadro de 384 px es un pedazo de hoja nítido y
ampliado unas 3 veces más de lo que el modelo vio en Sigatoka, y lo lee como "otra condición".
Desde el aire pasa lo contrario: la hoja es chica en la foto y el cuadro de 384 px es el que ve
las manchas (en 1000 fotos aéreas de Colombia, 92 % de Sigatoka por cuadros contra 2 % con la
foto completa).

Reproducido con las 787 fotos de prueba reales (`vision/train/evaluar_escalas.py`): llevadas a
1920 px de ancho, la revisión por cuadros baja de 93.4 % a 80.4 % de exactitud; 28 de 112 fotos
de Sigatoka pasan a "otra condición" y 25 de 199 sanas también. La foto completa casi no cambia.

## Opciones

| Opción | A 1920 px | Toma abierta (6 fotos por lienzo) | Fotos aéreas con Sigatoka |
|---|---|---|---|
| Cuadro de 384 px (antes) | 80.4 % | 98.0 % | 15 de 25 |
| Solo cuadro grande (50 % del lado corto) | 96.3 % | 98.9 % | 12 de 25 |
| Solo cuadro grande (70 %) | 97.7 % | 94.3 % | 7 de 25 |
| Foto completa | 92.2 % | 82.8 % | 0 de 25 |
| Elegir el tamaño por el tamaño de la hoja segmentada | 85–90 % | 97 % | 15 de 25 |
| Elegir el tamaño con más seguridad | 85 % | 98 % | 13 de 25 |
| **Dos tamaños, regla de abajo (elegida)** | **95.8 %** | **97.7 %** | **15 de 25** |

Las filas de "solo cuadro grande", "foto completa" y los dos selectores son de pruebas
exploratorias del 20 de noviembre con las mismas fotos (sus lienzos de toma abierta se armaron con otro orden de fotos, así que esa
columna puede variar un punto); la de antes y la elegida son de `vision/models/escalas_evaluacion.md`. Reentrenar es el arreglo de fondo, pero tarda una noche
en la PC del equipo y necesita fotos de cerca de la ZED; queda como siguiente paso.

## Decisión

Cada foto se revisa con dos tamaños de cuadro: el de siempre (384 px, `lado_min_rel` 0.3) y uno
de la mitad del lado corto (`escala_gruesa` 0.5 en el JSON del modelo; en la foto del dron,
600 px reducidos a 384). La regla (`elegir_escala` en `vision/parches.py`, copiada en
`web/motor.js`):

- si el cuadro chico encuentra Sigatoka con seguridad (≥ 0.70) y el grande no dice "sin hoja",
  manda el chico (no se pierden las manchas chicas vistas desde el aire);
- en todo lo demás, manda el grande.

Sigue siendo un solo resultado por foto. Los cuadros que se dibujan y la lectura por hoja son
los del tamaño que mandó. En fotos chicas (lado corto ≤ 768 px) los dos tamaños miden lo mismo
y se revisa una sola vez.

## Resultado (`vision/models/escalas_evaluacion.md`)

- Fotos de prueba tal cual: sin cambio (93.4 %).
- Las mismas a 1920 px: de 80.4 % a 95.8 %. Sigatoka de 84 a 106 de 112; sanas de 172 a 192 de
  199; sin hoja de 257 a 339 de 347.
- Toma abierta: de 98.0 % a 97.7 %. Las 112 de Sigatoka siguen bien, pero 9 fotos más de "otra
  condición" salen como Sigatoka (de 4 a 13 de 129): una falsa alarma que se revisa a mano.
- Fotos aéreas con Sigatoka: 15 de 25 antes y después.
- La página y Python dan la misma clase y el mismo tamaño en 30 de 30 fotos a 1920 px
  (diferencia máxima de confianza 0.014).

## Consecuencias

- Revisar cada foto tarda más: una foto de 1920 x 1200 pasa de 24 a 36 cuadros (12 grandes).
  En la página, unos 2 s por foto en la prueba; en la Jetson se ve en el log
  (`[PARCHES] ... cuadro de N px · ms`).
- El arreglo es de la inferencia. Para la siguiente corrida de entrenamiento: fotos propias de la
  ZED de hojas con Sigatoka, etiquetadas en la estación, y bajar o quitar el filtro del maestro
  en las escalas de 30–40 % (ver `vision/GUIA-PARCHES.md`, Siguiente fase).
- Falta probarlo con fotos reales del dron de cerca; las de prueba se llevaron a 1920 px
  ampliándolas, así que son menos nítidas que las de la ZED.
