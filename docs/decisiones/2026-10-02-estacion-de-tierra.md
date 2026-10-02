# 2026-10-02 — Estación de tierra: app web local en la laptop

## Contexto

Se quería un front-end para: ver las fotos recolectadas, que un humano las etiquete y el
modelo "aprenda en tiempo real", guardar el GPS de cada foto, un mapa de las hectáreas con
indicadores de Sigatoka, y una UI para que cualquiera agregue categorías y reentrene.
La decisión se pasó por un consejo de 5 perspectivas (contrarian, first principles,
expansionista, outsider, ejecutor) con revisión cruzada anónima.

## Opciones consideradas

- App de escritorio (Electron) vs. **sitio web local** vs. nube.
- UI servida desde la Jetson (doc 08) vs. **en la laptop de tierra**.
- Stacks: Streamlit, Gradio, Label Studio, FastAPI vs. **Flask** (ya en el repo).
- "Aprendizaje en tiempo real" (reentrenar con cada clic) vs. **reentrenamiento por lotes
  con examen de campo**.

## Decisión

- **Sitio web local en la laptop** (Flask + SQLite + Leaflet descargado al repo), un solo
  framework para un equipo pequeño. La Jetson captura (y luego infiere); la historia de la
  finca vive en la laptop, no en el dron (no hay que encender la aeronave para ver un mapa).
- **Aprendizaje honesto:** cada corrección se guarda al instante; la revisión muestra
  primero las fotos de menor confianza (active learning); un botón *Reentrenar* corre el
  `train_cls.py` de siempre. ≈20 % de las fotos revisadas forman un **examen de campo** que
  nunca se entrena; cada modelo nuevo se compara contra el actual y activarlo es decisión
  humana, con regreso a versiones anteriores.
- **GPS:** sidecar JSON del Pixhawk (`docs/04` §5) como fuente principal; EXIF de
  celular/GoPro como alternativa (permite trabajar sin dron).
- **Mapa por zonas, no por plantas:** GPS sin RTK (±2–3 m ≈ distancia entre plantas) y una
  foto aérea cubre varias plantas. Exportación GeoJSON.
- **Categorías nuevas:** solo desde la "zona técnica", con validación del agrónomo y mínimo
  de fotos; no es una función para cualquier usuario.

## Riesgos que el consejo marcó (pendientes, no de software)

1. **Nadie ha comprobado que la Sigatoka se vea desde el dron.** El 91.8 % es de fotos
   cercanas de internet. Primera acción: fotografiar con celular/GoPro plantas confirmadas
   por un agrónomo, a 3–4 alturas y en ángulo (la Sigatoka temprana aparece en el envés y
   en hojas tapadas por el follaje).
2. **La ZED X (~2 MP, estéreo de profundidad) puede ser el sensor equivocado** para rayas
   milimétricas; evaluar una cámara RGB de alta resolución antes de seguir depurándola.
3. **Verdad de campo:** plantas de referencia marcadas con GPS y diagnosticadas en sitio.
4. Logística: permisos de vuelo y del dueño del terreno, batería por hectárea, traslape.
5. A futuro: ortomosaicos (OpenDroneMap + QGIS) para ubicar plantas mejor que con el GPS
   de cada foto.

Implementación: `ui/estacion.py`, `ui/datos.py`, `ui/entrenamiento.py`, `ui/templates/`,
`vision/clasificador.py`. Guía de uso: `ui/ESTACION.md`.
