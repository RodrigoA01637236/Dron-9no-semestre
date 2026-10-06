# Estación de tierra — guía de uso

Aplicación web local que corre en la laptop del equipo y se usa desde el navegador.
Tiene cuatro pestañas en la barra de la izquierda (abajo, en el celular):

| Pestaña | Para qué |
|---|---|
| **Cargar** (la principal) | Subir una imagen, varias, o arrastrar una carpeta completa (con subcarpetas), o usar la cámara en vivo. El modelo dice al momento qué cree que tiene cada imagen (sana, Sigatoka u otra condición), con qué seguridad y qué hacer. Todo se guarda con la fecha de hoy. |
| **Revisar** | Elige la fecha arriba. *Una por una*: salen primero las imágenes en las que el modelo tiene más dudas y una persona confirma o corrige. *Todas las imágenes*: todas las de esa fecha, de la más dudosa a la más segura. |
| **Modelo** | Reentrenar con lo revisado, comparar contra el modelo actual y activar el nuevo solo si mejora. |
| **Mapa** | Opcional por ahora: muestra en el mapa las imágenes que traen ubicación (GPS). |

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

## Borrar imágenes

Cada imagen tiene una **X arriba a la derecha** (en Cargar y en Revisar, vista *Todas las
imágenes*). El primer clic cambia la X por **Borrar**; un segundo clic la borra (si no
confirmas en 3 segundos, vuelve a ser X). También hay un botón *Borrar esta imagen* junto a la
imagen abierta. Borrar quita la imagen de la estación y del disco: no se puede deshacer.

## Cómo se lee el resultado

- Cada imagen muestra el diagnóstico, su seguridad y una barra por condición. La línea
  blanca de cada barra es la **seguridad mínima (65 %)**: si ninguna condición la pasa, el
  resultado es **El modelo no está seguro** y la estación pide otra foto en vez de adivinar.
- Con la cámara (webcam de la laptop) el diagnóstico se actualiza cada 0.8 s sin guardar
  nada. *Capturar y guardar* guarda ese cuadro como una imagen más de hoy.
- Desde otro equipo (`--red`) el navegador no permite la cámara en vivo por no ser una
  conexión segura; en el celular, *Usar cámara* abre la cámara del teléfono para tomar una foto.

## El flujo de trabajo

1. **Cargar**: arrastra la carpeta con las fotos (o elige imágenes, o usa la cámara). Cada
   imagen muestra al instante lo que cree el modelo. Quedan guardadas en la fecha de hoy.
2. **Revisar**: elige la fecha y revisa *una por una*, empezando por las dudosas. El
   agrónomo escribe su nombre y etiqueta. Atajos: `1` `2` `3`… categorías, `0` la imagen
   no sirve, `S` saltar, `Z` deshacer.
3. **Modelo** (de vez en cuando): con unas 50 imágenes revisadas nuevas, *Reentrenar
   ahora*. Al terminar aparece la versión nueva con su resultado en el **examen de campo**;
   si mejora, *Usar este modelo* (todas las imágenes se vuelven a diagnosticar con él).

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
