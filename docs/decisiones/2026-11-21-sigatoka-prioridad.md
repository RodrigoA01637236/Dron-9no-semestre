# 2026-11-21 — Sigatoka tiene prioridad sobre "otra condición"

## Contexto

El equipo pidió que Sigatoka gane siempre a "otra condición" y que "otra condición" sea la minoría:
el dron busca Sigatoka, y una hoja con Sigatoka marcada como otra cosa es el error más caro.

Antes, si una foto tenía cuadros seguros de las dos enfermedades, ganaba la que tuviera más.

## Opciones (787 fotos de prueba, dos tamaños de cuadro, con `mas_que_sana`)

| Sigatoka gana si tiene... | Sigatoka bien, a 1920 px | "Otra" que pasa a Sigatoka, a 1920 px | Ídem, toma abierta | Exactitud a 1920 px / abierta |
|---|---|---|---|---|
| más cuadros que la otra (antes) | 106 de 112 | 12 de 129 | 5 de 129 | 95.9 % / 99.1 % |
| 1 cuadro seguro | 111 | 50 | 88 | 91.7 % / 88.6 % |
| 2 cuadros | 109 | 32 | 61 | 93.8 % / 92.0 % |
| 3 cuadros | 109 | 24 | 42 | 94.8 % / 94.4 % |
| **la mitad de los de "otra" (elegida)** | **110** | **19** | **31** | **95.6 % / 95.8 %** |
| un tercio de los de "otra" | 110 | 22 | 38 | 95.2 % / 94.9 % |

Bajar la seguridad mínima de los cuadros de Sigatoka (0.4–0.6) no ganó ninguna foto de Sigatoka más
y sumó falsas alarmas. Las filas son de una prueba exploratoria con el cache de rasgos del 20 de
noviembre; la elegida está también en `vision/models/escalas_evaluacion.md`.

## Decisión

`prioridad: ["sigatoka"]`, `fraccion_prioridad: 0.5` en el JSON del modelo (`vision/parches.py` y
`web/motor.js`): Sigatoka gana a las demás enfermedades si tiene al menos la mitad de cuadros seguros
que la rival. Las hojas sanas no cambian (Sigatoka ya ganaba a "sana" con un cuadro seguro).

## Consecuencias

- Evaluación del repo (`vision/models/escalas_evaluacion.md`): a 1920 px, Sigatoka bien de 106 a
  110 de 112 y exactitud de 95.9 % a 95.5 %; en toma abierta, exactitud de 98.2 % a 97.0 %.
- Más falsas alarmas de Sigatoka en fotos de otras enfermedades: a 1920 px de 12 a 19 de 129 y en
  toma abierta de 13 a 23 de 129 (en la prueba exploratoria, con otros lienzos, de 5 a 31). Es el costo elegido: una falsa alarma la revisa una persona; una Sigatoka
  perdida no.
- No ayuda a fotos borrosas: en las fotos del iPad del 20 de noviembre ningún cuadro ve Sigatoka con
  seguridad, así que siguen "otra condición". Hace falta una foto nítida de la hoja.
- Página y Python: misma clase en 36 de 36 fotos.
