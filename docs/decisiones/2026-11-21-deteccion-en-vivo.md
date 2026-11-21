# 2026-11-21 — Detección en vivo; la foto se queda con ese resultado

## Contexto

Desde el 18 de noviembre el video no diagnosticaba: solo se revisaba cada foto después de tomarla
([decisión](2026-11-18-un-solo-resultado-por-foto.md)). El equipo pidió que el dron revise siempre
en vivo y que la foto se quede con el análisis que se estaba viendo.

El problema del 18 no era revisar en vivo, sino que el video usaba otro método (la foto completa
reducida a 384 x 384, donde las manchas no se ven) y la foto otro (por cuadros), así que una misma
foto tenía dos resultados.

## Decisión

- Un hilo revisa sin parar el último cuadro de la cámara **con el mismo método que la página**: por
  cuadros, con los dos tamaños de cuadro y el filtro de hoja (`modelo.predecir_bgr(..., "parches")`).
  El resultado se ve en la ventana (`EN VIVO: ...`), en el video (cuadros con síntomas marcados), en
  `/estado` (`en_vivo`) y en las páginas.
- Al tomar una foto se guarda **el cuadro que se revisó** (con su hora y su GPS) y su resultado: en el
  texto de la foto, en el EXIF de las dos copias (`ModeloYOLO=... por parches, en vivo`), en el log y
  en `Prueba#1/parches/`. La foto, su resultado y el mapa coinciden exactamente, y sigue habiendo un
  solo resultado por foto.
- Respaldo: si no hay revisión en vivo de los últimos 10 s, la foto se revisa aparte como antes.

## Costos

- En la Jetson cada revisión tarda 2–5 s, así que la detección en vivo se actualiza cada pocos
  segundos y la foto puede ser de 2–5 s antes de apretar el botón (si la cámara se movió, se
  guarda el cuadro anterior). Con `FOTO_DEL_CUADRO_ANALIZADO = False` se guarda el cuadro del
  momento, pero entonces el resultado sería el de otro cuadro.
- El procesador trabaja todo el tiempo. El modelo usa 4 núcleos (`HILOS_MODELO`) y descansa 0.3 s
  entre revisiones (`PAUSA_EN_VIVO`) para dejar procesador a la cámara, al video y al GPS. Falta
  medirlo en la Jetson.
- Los cuadros que se marcan en el video son los de la última revisión; si la cámara se mueve,
  quedan corridos hasta la siguiente.

## Verificación (cámara simulada con una foto de hoja con Sigatoka, 21 de noviembre)

Detección en vivo `sigatoka 88 %` (12 cuadros de 600 px); foto tomada desde la página: texto
`DIAG: SIGATOKA 88%`, EXIF de las dos copias `AnalisisYOLO=sigatoka; ConfianzaYOLO=0.883;
... por parches, en vivo`, log `[PARCHES] ... en vivo, revisado hace 0.6 s`. Con la detección en vivo
apagada, la foto se revisó aparte y dio lo mismo. La página web (Dron en vivo) dice
"En vivo: Parece Sigatoka". Falta probarlo en la Jetson con la cámara real.
