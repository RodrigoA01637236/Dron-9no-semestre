# 2026-11-12 — Filtro de hoja: decidir por foto, con un solo umbral

## Contexto

Con el modelo v2 en la página pública, fotos de objetos cotidianos (mesa, mano, pared, taza)
salían como hoja enferma. La clase `sin_hoja` se entrenó con otras plantas, frutos y fondos del
cultivo; nunca vio objetos de la casa, y ante ellos el modelo elige una clase de hoja con mucha
seguridad (en 760 imágenes de COCO que nunca vio, 130 salen como hoja con confianza ≥ 0.70).

## Opciones consideradas

1. **Reglas de color** (fracción de pixeles verdes o amarillos). No separan paredes amarillas,
   pelo o madera de hojas con clorosis, y rechazan tejido necrótico café.
2. **Puntajes genéricos de "fuera de distribución"**: logit máximo y energía del modelo
   (Hendrycks y Gimpel 2017; Liu et al. 2020). Separan regular (área bajo la curva ROC 0.94 por
   cuadro) y dejan pasar muchos objetos con el umbral que no pierde hojas.
3. **Distancia al vecino más cercano** en los rasgos (Sun et al. 2022). Funciona con fuentes
   conocidas, pero al dejar fuera una fuente completa de fotos de hoja cae a 0.37–0.72: detecta
   "parece otra fuente", no "no es hoja".
4. **Sonda lineal** (regresión logística) sobre los 1280 rasgos de la penúltima capa, entrenada
   con fotos de hoja contra fotos de COCO y acercamientos simulados. Elegida.

Las opciones 1 a 3 fueron pruebas exploratorias del 11 y 12 de noviembre; no se repitieron.

## Dónde aplicar la sonda

- **Primera versión** (`dc9205c`): cuadro por cuadro, con umbral 0 para cuadros con poco color de
  hoja y −4 para los verdes. **Quitaba los cuadros con lesiones** (cafés, casi sin verde): de 112
  fotos reales con Sigatoka, 8 pasaron a "sin hoja" y 105 de 325 cuadros se quitaron. Reentrenada
  con las 9 fuentes y dejando fuera una a la vez, cambia el veredicto de 39 de 3866 fotos de hoja.
- **Versión elegida** (`6053626`): la foto cuenta como sin hoja **solo si ningún cuadro de hoja
  pasa** un umbral único de −3; si alguno pasa, el veredicto es el del modelo con todos sus
  cuadros, manchas incluidas. Nunca produce "sana": solo puede volver una foto "sin hoja".

## Resultado (`vision/models/filtro_hoja_evaluacion.md`, solo fotos reales)

| | Fotos de hoja que pasan a "sin hoja" (una fuente fuera a la vez) | Objetos que aún pasan como hoja |
|---|---|---|
| Sin filtro | — | 130 de 760 |
| Primera versión (por cuadro) | 39 de 3866 | 61 de 760 |
| Elegida (por foto, −3) | 5 de 3866 | 85 de 760 |
| Foto completa, −3 (la usaba el video en vivo; sin uso desde el 18 de noviembre) | 18 de 3866 (15 de una fuente de hojas recortadas sobre fondo negro; ninguna aérea) | 4 de 760 (10 sin filtro) |

La elegida atrapa menos objetos que la primera (45 de 130 contra 69), a cambio de no perder hojas
enfermas. Perder una hoja con Sigatoka es peor que aceptar un objeto, que quien revisa sí ve.

## Consecuencias

- Muchos objetos verdes (manzanas, pasto, plantas) siguen pasando. La solución de fondo es
  entrenar `sin_hoja` con fotos de objetos propias (`data/raw/propias/sin_hoja`).
- La sonda vive en el JSON del modelo (`filtro_hoja`): la página, la estación y el dron usan lo
  mismo. Se entrena con `vision/train/filtro_hoja.py` (paso 7 de la noche) y se evalúa con
  `vision/train/evaluar_filtro.py`.
- El 18 de noviembre se reentrenó sin dos fuentes locales que eran sustitutos generados para
  probar el código (`v1_publico` y `colombia_uav` de la copia local). En 50 fotos de prueba no
  cambió ningún veredicto respecto a la versión publicada el 12 de noviembre.
