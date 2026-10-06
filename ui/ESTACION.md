# Estación de tierra — guía de uso

Aplicación web local que corre en la laptop del equipo y se usa desde el navegador.
Sirve para cinco cosas:

| Página | Para qué |
|---|---|
| **Mapa** | Ver dónde se tomó cada foto y su diagnóstico; vista **por zonas** con el % de plantas enfermas. Descarga GeoJSON para Google Earth/QGIS. |
| **Identificar** | Subir o tomar la foto de una hoja (o usar la cámara en vivo) y ver al instante si está sana, tiene Sigatoka u otra condición, con la probabilidad de cada una. |
| **Revisar** | Un humano (idealmente el agrónomo) confirma o corrige cada diagnóstico. Empieza por las fotos donde el modelo tiene más dudas. |
| **Fotos** e **Importar** | Subir la carpeta de fotos de un vuelo (el modelo las diagnostica al instante) y explorarlas con filtros. |
| **Modelo** | Reentrenar con las correcciones, comparar contra el modelo actual y activar el nuevo solo si mejora. |

## Cómo abrirla

**Doble clic en `ui\Iniciar-Estacion.bat`.** Se abre sola en el navegador
(`http://localhost:5050`). Deja abierta la ventana negra mientras la usas.

Alternativa por PowerShell (con el venv activo, en la carpeta del repo):

```powershell
python ui\estacion.py
python ui\estacion.py --red     # para que otro equipo del mismo WiFi la abra (ej. el agrónomo en su laptop)
```

Requisitos: el entorno `dron-vision` de la guía del modelo, más `pip install flask`
(el `.bat` lo instala solo la primera vez), y el modelo `sigatoka_cls_v1.onnx`
(de tu Drive) copiado en `vision\models\`.

## Identificar una hoja

En **Identificar** arrastra una foto, elige un archivo o pulsa *Usar cámara*:

- Con una foto, la estación muestra el diagnóstico, su confianza y una barra por condición.
  La línea vertical de cada barra es el **umbral (65 %)**: si ninguna condición lo pasa, el
  resultado es **El modelo no está seguro** y la estación pide otra foto en vez de adivinar.
- Con la cámara (webcam de la laptop) el diagnóstico se actualiza cada 0.8 s. *Capturar y
  fijar* congela el cuadro para guardarlo.
- *Guardar para revisión* manda la foto al vuelo `identificaciones_<fecha>`: aparece en
  Revisar y Fotos, y una vez confirmada sirve para reentrenar.
- Desde otro equipo (`--red`) el navegador no permite la cámara en vivo por no ser una
  conexión segura; en el celular, *Usar cámara* abre la cámara del teléfono para tomar una foto.

## El flujo de trabajo

1. **Importar** la carpeta del vuelo (botón *Elegir carpeta*). Acepta:
   - Fotos del dron con su `.json` gemelo del Pixhawk (`docs/04` §5) — la fuente de GPS más precisa.
   - Fotos de celular o GoPro con ubicación activada (el GPS va en el EXIF de la foto).
     **Sirve para trabajar hoy, sin dron**: tomen fotos de hojas en una parcela con el celular.
2. **Mapa**: revisen el panorama. La vista *Zonas* agrupa las fotos en cuadros de 10–100 m.
3. **Revisar**: el agrónomo escribe su nombre y etiqueta. Atajos: `1` `2` `3`… categorías,
   `0` foto no sirve, `S` saltar, `Z` deshacer.
4. **Modelo**: cuando haya varias decenas de fotos revisadas, *Reentrenar ahora*. Al
   terminar aparece la versión nueva con su resultado en el **examen de campo**; si
   mejora, *Usar este modelo* (todas las fotos se vuelven a diagnosticar con él).

## Cómo "aprende" el modelo (honestamente)

El modelo **no cambia mientras etiquetas**: cada corrección se guarda al instante y
el aprendizaje ocurre al presionar *Reentrenar* (~10–35 min en la RTX 4060). Reentrenar
con unas pocas fotos a la vez lo haría olvidar lo que ya sabe; por eso se reentrena
con todo junto (dataset público + todas las revisiones).

**Examen de campo:** ≈20 % de las fotos revisadas se apartan automáticamente y **nunca**
se usan para entrenar. Con ellas se califica cada modelo nuevo contra el actual, en fotos
reales de campo. Así un modelo que empeora no se activa por accidente, y siempre se puede
regresar a una versión anterior.

## Límites que hay que decir en voz alta

- **El mapa marca zonas, no plantas.** Cada punto es la posición del dron al tomar la
  foto (GPS sin RTK: ±2–3 m, más o menos la distancia entre plantas), y una foto aérea
  cubre varias plantas. Por eso existe la vista por zonas.
- **El 91.8 % del modelo v1 se midió en fotos cercanas de internet.** La exactitud real
  en fotos del dron solo la dará el examen de campo con fotos propias.
- **Quién etiqueta importa:** si etiqueta alguien que no distingue Sigatoka de otras
  manchas, el modelo aprende sus errores. La estación guarda quién revisó cada foto.
- **Categorías nuevas** (zona técnica en *Modelo*): solo con validación del agrónomo y
  al menos 15 fotos revisadas antes de reentrenar.

## Dónde quedan los datos

Todo en `data\estacion\` (excluido de git): `estacion.db` (base de datos), `fotos\`,
`miniaturas\`, `modelos\` (cada versión activable) y `entrenamientos\` (log y dataset de
cada corrida). **Respáldenlo en Drive después de cada sesión de revisión**: las etiquetas
del agrónomo son el activo más valioso del proyecto.

## Antes de volar: la prueba que recomendó el consejo

Antes de invertir más en software, verifiquen que la Sigatoka **se ve** desde el aire:
con un celular o GoPro con GPS, fotografíen desde arriba plantas que un agrónomo confirme
enfermas, a 3–4 alturas y también en ángulo (la Sigatoka temprana aparece en el envés y
en hojas que el follaje tapa). Importen esas fotos aquí: el mapa y la revisión les dirán
a qué altura el modelo todavía acierta.
