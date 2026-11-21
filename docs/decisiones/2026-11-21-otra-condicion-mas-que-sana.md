# 2026-11-21 — "Otra condición" necesita más cuadros que "sana"

## Contexto

Con la cámara del dron apuntando a hojas sanas, la foto salía "otra condición" aunque la mayoría de
los cuadros dijera "sana" con seguridad (por ejemplo, 11 sanos contra 8 de otra condición). La regla
de la foto marca una enfermedad en cuanto hay `min_parches` (1) cuadro seguro de ella: está hecha
para no perder Sigatoka, pero con "otra condición" basta un borde, una sombra o algo que no es hoja
(en esas pruebas, la barra de la galería de un iPad fotografiado) para manchar la foto.

## Decisión

`mas_que_sana: ["otra_condicion"]` en el JSON del modelo (`vision/parches.py` y `web/motor.js`):
"otra condición" solo marca la foto si tiene más cuadros seguros que "sana". Si no, esos cuadros
cuentan como sanos (su probabilidad pasa a "sana", no a otra enfermedad) y se decide otra vez. La
primera versión repartía esa probabilidad entre todas las clases y hacía aparecer Sigatoka en hojas
sanas; se cambió antes de subirla. Sigatoka sigue con la regla de siempre.

## Resultado (787 fotos de prueba, dos tamaños de cuadro; `vision/models/escalas_evaluacion.md`)

| | Antes | Ahora |
|---|---|---|
| Fotos tal cual | 93.4 % | 93.5 % |
| A 1920 px (de cerca) | 95.8 % | 95.9 % |
| Toma abierta | 97.7 % | 98.2 % |

Sanas bien: tal cual de 193 a 196, a 1920 px de 192 a 197 y en toma abierta de 195 a 199 (de 199).
Sigatoka sin cambio (106 de 112 a 1920 px; 112 de 112 en toma abierta). "Otra condición" bien a
1920 px: de 117 a 113 de 129. Fotos aéreas con Sigatoka: 15 de 25, igual. En las fotos del iPad del 20 de noviembre, las dos
sanas pasan de "otra condición" a "sana"; las cuatro con Sigatoka siguen "otra condición" porque
salen borrosas (la cámara estaba muy cerca de la pantalla). Página y Python: misma clase en 35 de 36
fotos (la otra es un empate de cuadros).
