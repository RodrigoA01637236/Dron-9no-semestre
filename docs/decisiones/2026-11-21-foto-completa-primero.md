# 2026-11-21 — Foto completa primero; los cuadros, de apoyo

## Contexto

Con la cámara del dron, el equipo vio que una foto de una sola hoja de cerca se partía en muchos
cuadros, y que eso complicaba el resultado y lo llevaba a "otra condición" en lugar de Sigatoka. El
análisis por cuadros se pensó para fotos desde el aire, donde caben muchas hojas y las manchas son
chicas; en una hoja de cerca, la foto completa ya ve la hoja entera.

## Decisión

`completa_primero: true` en el JSON del modelo (`Clasificador._completa_primero` y
`completaPrimero` en `web/motor.js`, la misma regla):

1. Se revisa la foto completa y por cuadros (dos tamaños, con sus reglas).
2. Si los cuadros encuentran Sigatoka con seguridad, gana Sigatoka (lo que se busca; así se conserva
   la detección desde el aire, donde la foto completa no ve las manchas).
3. Si no, y la foto completa está segura (≥ 0.70), decide la foto completa y no se dibujan cuadros.
4. Si la foto completa no está segura, deciden los cuadros.

Sigue siendo un solo resultado por foto, igual en el dron (en vivo y en la foto), la página y la
estación. El log del dron dice "decidió la foto completa" o el tamaño de cuadro.

## Resultado (`vision/models/escalas_evaluacion.md`, 787 fotos de prueba)

| | Solo cuadros | Foto completa primero |
|---|---|---|
| Fotos tal cual | 93.4 % | 95.5 % |
| A 1920 px (de cerca) | 95.5 % (Sigatoka 110 de 112) | 95.5 % (Sigatoka 111 de 112) |
| Toma abierta | 97.0 % | 95.8 % |
| Fotos aéreas con Sigatoka | 15 de 25 | 15 de 25 |

Sanas y "sin hoja" mejoran o quedan igual en todas; Sigatoka nunca baja. Lo que baja es "otra
condición" en tomas abiertas (de 82 % a 74 %), casi siempre hacia Sigatoka.

Fotos del iPad del 20 de noviembre: las sanas salen sanas; las cuatro con Sigatoka salen "sin hoja"
u "otra condición": están borrosas y ninguna regla ve la mancha. Página y Python: misma clase en 36
de 36 fotos. Probado en el dron con la cámara simulada: en vivo "sana 79 %, decidió la foto completa".
