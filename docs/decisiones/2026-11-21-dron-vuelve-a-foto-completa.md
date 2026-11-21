# 2026-11-21 — El dron vuelve a revisar la foto completa, como en la primera sesión

## Contexto

En las pruebas con el iPad, la revisión por cuadros casi nunca dio Sigatoka. El equipo notó que
en la primera sesión de fotos (17 de noviembre) sí salía.

## Qué cambió entre la primera sesión y ahora

- El modelo (sigatoka_cls_v2) es el mismo.
- En la primera sesión, el resultado que se veía en el video, en la foto y en el EXIF era el de
  la **foto completa** (`MODO_EN_VIVO = "imagen"`). La revisión por cuadros también corría, pero
  como segundo resultado.
- El 18 de noviembre se dejó un solo resultado por foto y se eligió el de los **cuadros**
  (`2026-11-18-un-solo-resultado-por-foto.md`). Desde ahí se ve la segmentación.
- La revisión por cuadros ya daba "otra condición" en las fotos de cerca desde antes: en el
  archivo del 17 de noviembre, por cuadros ninguna de las 71 fotos salió Sigatoka y con la foto
  completa salieron 38. Con el código del 17 de noviembre, las 6 fotos del iPad del 20 de
  noviembre salen "otra condición" por cuadros; la foto completa da lo mismo que hoy.

## Decisión

`MODO_ANALISIS = "imagen"` en `jetson/zed_right.py`: el video en vivo y las fotos se revisan con
la foto completa, como en la primera sesión. Los cuadros se pueden volver a usar con
`SIGATOKA_MODO=parches bash jetson/zed_control.sh reiniciar`.

## Consecuencias

- Revisar una foto tarda ~10 ms en la prueba (antes 1-3 s en la Jetson), así que el video se
  revisa más seguido.
- Desde el aire (hojas chicas en la foto), la foto completa no ve las manchas: en 25 fotos aéreas
  con Sigatoka, 0 contra 15 por cuadros. Para vuelos altos conviene `SIGATOKA_MODO=parches`.
- No hay cuadros dibujados en la foto ni lectura por hoja.
- Las fotos del iPad siguen siendo difíciles también con la foto completa (borrosas, con la
  interfaz de la galería): de 6, ninguna sale Sigatoka. El arreglo de fondo es reentrenar con fotos
  de la ZED.
