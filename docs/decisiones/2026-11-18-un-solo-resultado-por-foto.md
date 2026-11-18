# 2026-11-18 — Un solo resultado por foto, el mismo que la página

## Contexto

En el dron, una foto tenía dos resultados distintos:

1. **Al tomarla:** la lectura del video en vivo (imagen completa reducida a 384 x 384), que se
   dibujaba en la foto (`DIAG`), se escribía en el EXIF (`AnalisisYOLO`) y en el log
   (`[FOTO] Modelo: ...`).
2. **Segundos después:** la revisión por cuadros (`[PARCHES]`), la misma que hace la página.

El modelo es el mismo; lo que cambia es la imagen que recibe. Reducida entera, las manchas de
Sigatoka desaparecen: en un cuadro aéreo de Colombia con Sigatoka, por cuadros sale Sigatoka
(11 de 16 cuadros) y la imagen completa sale sana. En el archivo de 71 fotos del 17 de
noviembre, las dos lecturas coincidían en 25. El equipo no quiere que una foto diga una cosa y
luego otra.

## Opciones

- Video en vivo por cuadros, a menos lecturas por segundo: ve las manchas, pero en la Jetson
  tarda 1–3 s por imagen y le quita procesador a las fotos.
- Video que solo diga "hoja / sin hoja": sigue siendo una segunda lectura que puede no
  coincidir.
- **El video no diagnostica; cada foto tiene un solo resultado** (elegida).

## Decisión

- Cada foto se revisa por cuadros sobre su **copia limpia ya guardada**: la misma imagen, el
  mismo modelo y el mismo código que la página web. Ese resultado se dibuja en la foto con
  texto, va en el EXIF de las dos copias, en el log y en `/estado`. Mientras se revisa, la foto
  dice `ANALIZANDO`.
- Se quitó la clasificación continua del video. La ventana, la página del dron, la página web
  (Dron en vivo) y la estación muestran el resultado de la **última foto**.
- `/estado` conserva el campo `prediccion` con el resultado de la última foto, para que las
  páginas viejas no se rompan.

## Verificación (cámara simulada con una foto aérea real, 18 de noviembre)

Una foto: texto `DIAG: SIGATOKA 100%`; EXIF de las dos copias `AnalisisYOLO=sigatoka;
ConfianzaYOLO=1.000 ... por parches`; log `[PARCHES] ... sigatoka 100% · 10/24`; la página web,
con esa misma copia limpia: Sigatoka 0.9996, 24 cuadros, 10 marcados. Falta probarlo en la Jetson
con la cámara real.

## Consecuencias

- La Jetson tiene más procesador libre para revisar fotos (ya no clasifica el video).
- La sonda del filtro de hoja para la imagen completa (`filtro_hoja.imagen`) queda sin uso en
  el dron; se conserva en el JSON por si se vuelve a usar.
- `vision/diagnosticar.py` imprime por defecto solo ese resultado; la foto completa y el v1
  salen únicamente con `--comparar`, marcados como referencia. La figura del filtro
  (`figura_filtro.py`) grafica por defecto solo las fotos por cuadros.
