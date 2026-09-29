# 09 — Validación en campo

La cifra que define el proyecto no es la del test set: es la **concordancia entre el sistema y un experto evaluando las mismas plantas en campo**. Esa cifra es la tesis, el paper y el argumento de venta. Merece protocolo formal.

## 1. Diseño del experimento

- **Unidad de análisis:** la planta (no la foto). El sistema y el experto emiten un veredicto por planta.
- **Muestra:** ≥30 plantas por vuelo (mezcla real de sanas/enfermas), marcadas físicamente (estaca/cinta numerada) y georreferenciadas.
- **Cegado:** el experto evalúa en tierra ANTES o de forma independiente del vuelo, sin ver las predicciones. El equipo no le comunica resultados hasta terminar.
- **Ground truth:** escala de **Stover modificada por Gauhl** (0–6) por planta (hoja más joven enferma + % de área afectada), registrada en hoja de campo. Para casos ambiguos, el estándar de oro sería confirmación de laboratorio; si no es viable, registrar la ambigüedad — no forzar la etiqueta.
- **Repetición:** el protocolo completo en **≥2 sitios distintos** (otra finca u otra zona) para medir generalización. Un solo sitio = una anécdota.

## 2. Protocolo de cada vuelo

**Pre-vuelo (checklist impresa):**
1. Permiso del dueño de la finca (por escrito, aunque sea mensaje).
2. Clima: sin lluvia, viento <20 km/h; horario 9:00–15:00.
3. Baterías cargadas (dron + repuestos), NVMe con espacio, hora de la Jetson sincronizada.
4. Zona despejada de personas; briefing de seguridad (doc 10).
5. Prueba en tierra de 2 min: telemetría OK, captura OK, UI OK.

**Durante:**
- El piloto vuela la ruta acordada acercándose a cada planta marcada (2–3 tomas por planta, ángulos distintos).
- Un segundo integrante monitorea la UI y anota incidencias (planta oculta, foto dudosa, viento).
- Regla dura de batería: aterrizar con ≥25 % restante, sin excepciones.

**Post-vuelo (mismo día):**
- Respaldar datos (doc 05 §7).
- Congelar las predicciones del sistema ANTES de mirar la hoja del experto.
- Llenar la bitácora (`docs/bitacora/AAAA-MM-DD.md`): condiciones, duración, fallos, sorpresas.

## 3. Análisis

Cruzar por `planta_id` el veredicto del sistema con el del experto:

- **Matriz de confusión** por planta (sana / enferma; y si el modelo da severidad, matriz completa).
- **Sensibilidad** (de las plantas enfermas según el experto, ¿cuántas detectó el sistema?) — la métrica que más le importa al agricultor.
- **Especificidad** (de las sanas, ¿cuántas marcó sanas?) — controla falsas alarmas y credibilidad.
- Intervalos de confianza (con n=30–100, binomial exacto o bootstrap — no reportar porcentajes pelones).
- **Análisis de fallos foto por foto:** ¿el error fue del modelo, de la captura (blur/distancia/oclusión), o del protocolo? Cada categoría alimenta una mejora distinta (docs 05, 03 y este, respectivamente).

## 4. Entregables de la fase

1. **Reporte de validación** (`docs/validacion/`): diseño, condiciones, métricas con intervalos, análisis de fallos, límites conocidos del sistema.
2. **Video demo** (3–5 min): despegue, aproximación, la UI detectando en vivo, comparación con el experto. Es la pieza central para evaluación académica, incubadoras y clientes.
3. Actualización del dataset con las imágenes del vuelo ya etiquetadas contra el ground truth del experto (el círculo virtuoso: cada validación agranda el dataset).

## 5. Criterios de honestidad

- Reportar TODOS los vuelos, incluidos los fallidos. Un reporte donde todo salió bien a la primera no es creíble ni útil.
- Distinguir siempre "precisión en test set" (foto) de "concordancia en campo" (planta): son números distintos y el segundo manda.
- Los límites conocidos (contraluz, copas muy altas, estadios muy tempranos, confusión con deficiencia de X) se documentan y se comunican — a un cliente y a un sínodo les inspira más confianza un sistema con límites conocidos que uno "perfecto".
