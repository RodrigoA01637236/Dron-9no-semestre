# 01 — Plan maestro del proyecto

Plan completo desde el estado actual (hardware funcionando, repo vacío) hasta un producto comercializable. Cada fase tiene objetivo, pasos, entregables y un **criterio de salida** verificable: no se pasa a la siguiente fase del mismo subsistema sin cumplirlo.

Las fases de plataforma/datos/modelo corren **en paralelo** (son las tres pistas del doc 00). La numeración indica dependencia lógica, no orden estrictamente secuencial.

```
PISTA PLATAFORMA:  F0 ──► F1 ──────────► F4 ──► F5 ─────► F6 ──► F7
PISTA DATOS:       F2 (arranca YA y nunca se detiene) ──┘
PISTA MODELO:              F3 (itera con cada lote de datos) ──┘
```

---

## Fase 0 — Validación de la plataforma de visión (1–2 semanas)

**Objetivo:** saber con certeza con qué cámara y qué versión de JetPack se construye todo lo demás.

**Por qué primero:** la cámara ZED conectada por CSI sobre JetPack 7.2.1 tiene compatibilidad no verificada, y son dos riesgos apilados (soporte del SDK para JetPack 7 + configuración CSI/GMSL no estándar). Cada semana sin esta respuesta es una semana de plan construido sobre arena.

**Pasos** (detalle completo en [doc 03](03-camara.md)):
1. Identificar el modelo exacto de la cámara ZED (¿ZED 2/2i USB? ¿ZED X GMSL con tarjeta de captura?). La conexión por flex a CAM0/CAM1 sugiere ZED X + ZED Link, que requiere drivers ligados a la versión exacta de Jetson Linux.
2. Consultar la matriz de compatibilidad de Stereolabs para JetPack 7.x / L4T R39.
3. Intentar la instalación del ZED SDK y la captura de un frame.
4. Si falla, ejecutar el árbol de decisión del doc 03 (reflashear a JetPack 6.x / captura sin SDK / cámara alternativa).

**Entregables:** cámara capturando imágenes en la Jetson; decisión documentada en `docs/decisiones/` con la configuración final.

**Criterio de salida:** un comando reproducible guarda una foto de la cámara en disco en la Jetson. ✔/✘ sin ambigüedad.

---

## Fase 1 — Comunicación y captura georreferenciada (1–2 semanas)

**Objetivo:** la Jetson conversa con la Pixhawk y cada foto queda etiquetada con posición GPS y actitud.

**Pasos** (detalle en [doc 04](04-pixhawk-mavlink.md)):
1. Configurar la Pixhawk 6C con PX4 o ArduPilot (el que el equipo domine; la doc asume PX4) usando QGroundControl.
2. Conectar Pixhawk↔Jetson por USB; verificar `/dev/ttyACM0`.
3. Instalar MAVSDK-Python en la Jetson; script de prueba: heartbeat, posición GPS, actitud, batería.
4. Escribir el servicio de captura: al disparar (por comando, por intervalo o por botón en la UI), guarda imagen + JSON sidecar con timestamp, lat/lon/alt, actitud y estado del dron.
5. Prueba integrada en tierra: caminar con el sistema encendido y verificar que las fotos quedan georreferenciadas.

**Entregables:** `mavlink/telemetry.py`, `vision/capture.py`, formato de metadata documentado.

**Criterio de salida:** sesión de captura en tierra produce N fotos con coordenadas correctas verificadas contra un mapa.

---

## Fase 2 — Datos y dataset (arranca ya; continúa todo el proyecto)

**Objetivo:** construir el activo central del proyecto: un dataset de Sigatoka en condiciones de campo mexicanas, etiquetado con validación experta y versionado.

**Pasos** (detalle en [doc 05](05-datos-dataset.md)):
1. Descargar y organizar datasets públicos (BananaLSD, PSFD-Banana, PlantVillage-banana) para el baseline.
2. Conseguir acceso: contactar fincas/productores de plátano y un fitopatólogo o agrónomo especialista (universidad, INIFAP, comités de sanidad vegetal). **Agendar visitas desde la semana 1** — la ventana de campo depende de la temporada.
3. Definir el protocolo de captura (distancia, ángulos, iluminación, resolución mínima por hoja) y probarlo en la primera visita.
4. Recolectar en cada visita: fotos con dron cuando esté listo Y con celular siempre (el celular nunca se bloquea por hardware).
5. Etiquetar en Label Studio; doble etiqueta en muestra para medir acuerdo; validación experta de las etiquetas dudosas y de la muestra de control.
6. Versionar: estructura de carpetas + manifiestos CSV/JSON con metadata (fecha, finca, GPS, variedad, severidad Stover, etiquetador).

**Entregables:** dataset v1 (baseline público reorganizado), dataset v2+ (campo propio), reporte de acuerdo inter-etiquetador.

**Criterios de salida por hito:** v1: ≥1,000 imágenes por clase listas para entrenar. v2: ≥500 imágenes propias de campo etiquetadas y validadas. Meta de proyecto: ≥2,000 imágenes propias.

---

## Fase 3 — Modelo de visión (itera con cada versión del dataset)

**Objetivo:** modelo que clasifica hoja sana / Sigatoka (y opcionalmente severidad) con métricas honestas medidas en datos de campo propios.

**Pasos** (detalle en [doc 06](06-entrenamiento.md)):
1. Baseline: clasificador (YOLOv8n-cls o EfficientNet-B0) con transfer learning sobre el dataset público, en Google Colab.
2. Definir particiones sin fuga: el test set se separa **por planta/visita**, nunca por imagen.
3. Iterar con datos propios; aumentar datos (iluminación, blur de movimiento, escala) simulando condiciones de vuelo.
4. Evolución opcional: detección (YOLOv8n) para localizar hojas/lesiones dentro de la imagen en vez de clasificar la imagen completa — necesario cuando la foto contiene varias plantas.
5. Exportar a ONNX; construir engine TensorRT en la Jetson; verificar que la precisión no se degrada (comparar FP16 vs FP32) y medir FPS.
6. Registro de experimentos (tabla en el repo o Weights & Biases gratuito).

**Entregables:** `vision/train/` (notebooks/scripts), modelos versionados, tabla de experimentos.

**Criterio de salida:** ≥85 % F1 (por clase) en test set de campo propio, y ≥10 FPS de inferencia en la Jetson.

---

## Fase 4 — Integración a bordo (2–3 semanas tras F1+F3)

**Objetivo:** pipeline completo corriendo en la Jetson durante el vuelo: captura → inferencia → resultados en el mapa en vivo.

**Pasos** (detalle en docs [07](07-inferencia-jetson.md) y [08](08-interfaz-operador.md)):
1. Servicio de inferencia: consume las capturas, corre el engine TensorRT, produce eventos `{foto, gps, clase, confianza}`.
2. Hotspot WiFi en la Jetson (NetworkManager) + servidor Flask.
3. UI web con Leaflet: mapa con marcadores por planta (verde/rojo/amarillo según diagnóstico y confianza), galería de fotos, botón de captura manual, estado del sistema (GPS, batería, FPS).
4. Arranque automático de todos los servicios al encender la Jetson (systemd) — en campo nadie va a abrir una terminal.
5. Modo degradado: si la inferencia falla, la captura sigue funcionando (los datos son sagrados).
6. Pruebas de banco: sesión completa simulada en tierra, medir consumo (tegrastats) y temperatura.

**Entregables:** sistema integrado con arranque automático; manual de operación de una página.

**Criterio de salida:** demo en tierra de punta a punta sin tocar teclado: encender → conectarse al hotspot → capturar → ver diagnóstico en el mapa.

---

## Fase 5 — Validación en campo (3+ vuelos reales)

**Objetivo:** medir el desempeño real del sistema contra el diagnóstico de un experto, con protocolo formal. Esta métrica ES la tesis y ES el argumento comercial.

**Pasos** (detalle en [doc 09](09-validacion-campo.md)):
1. Pre-vuelo: checklist de seguridad, permiso del dueño de la finca, plan de vuelo manual (qué hileras, qué plantas).
2. El experto evalúa en tierra N plantas con escala Stover (ground truth), sin ver los resultados del sistema.
3. El dron inspecciona las mismas plantas; el sistema emite su diagnóstico.
4. Comparar: matriz de confusión, sensibilidad/especificidad por planta, concordancia con el experto.
5. Repetir en ≥2 fincas o zonas distintas para medir generalización.
6. Documentar todo con video — es la demo comercial y académica.

**Entregables:** reporte de validación con métricas, video demo, lecciones del protocolo de captura.

**Criterio de salida:** ≥3 vuelos documentados; sensibilidad y especificidad reportadas con intervalos; análisis honesto de fallos.

---

## Fase 6 — Endurecimiento hacia producto (posterior al prototipo académico)

**Objetivo:** convertir el prototipo en una unidad operable por alguien que no es el equipo de desarrollo.

**Pasos:**
1. **Alimentación de vuelo:** regulador DC-DC (14.8 V → 12 V o directo dentro del rango 9–20 V con filtrado LC/protección contra transitorios de ESC) para alimentar la Jetson desde la batería del dron; medir consumo real y autonomía (batería ~77 Wh ⇒ presupuestar 15–20 min de vuelo).
2. **Montaje físico:** carcasa/soporte antivibración para Jetson y cámara (las vibraciones arruinan las fotos y las soldaduras).
3. **Robustez de software:** watchdogs, logs, recuperación ante pérdida de GPS/cámara, apagado seguro.
4. **Regulación:** registro del dron ante AFAC, requisitos NOM-107-SCT3-2019 para operación, seguro de responsabilidad civil ([doc 10](10-regulacion-seguridad.md)).
5. **Reporte automático:** PDF/HTML post-vuelo con mapa de incidencia, conteos y fotos de evidencia — esto es lo que el cliente compra.
6. Pruebas con un usuario ajeno al equipo operando el sistema solo con el manual.

**Criterio de salida:** una persona externa completa una inspección con el manual, sin asistencia, y recibe su reporte.

---

## Fase 7 — Evolución del producto (hoja de ruta futura)

En orden de valor/esfuerzo; ninguna es prerequisito de vender el servicio v1:

1. **Vuelo semiautónomo:** misiones de escaneo por waypoints (MAVSDK ya lo soporta) con retorno seguro; el operador supervisa. Multiplica hectáreas/hora y es el diferenciador definitivo contra "un celular".
2. **App móvil / modo celular:** el mismo modelo ONNX corriendo en Android para agrónomos a pie — segundo producto con el mismo activo, mercado mayor, sin barrera regulatoria.
3. **Severidad y conteo:** pasar de sano/enfermo a estimar escala Stover por planta y % de incidencia por lote.
4. **Multi-enfermedad y multi-cultivo:** misma plataforma para Fusarium R4T (prioridad fitosanitaria nacional), y después otros cultivos (HLB en cítricos, roya en café). Cada una exige su dataset validado — el pipeline de datos ya construido es la ventaja.
5. **Cámara multiespectral:** para detección presintomática (NDVI y bandas red-edge); inversión de hardware significativa, justificarla con clientes reales.
6. **Servicio de datos (SaaS):** mapas de incidencia históricos por región para exportadoras, aseguradoras, comités de sanidad; requiere escala y credibilidad — es la visión, no el MVP.

Modelo de negocio y escenarios completos: [doc 11](11-producto-negocio.md).

---

## Gestión del proyecto

- **Repositorio:** todo el código y la documentación viven aquí; commits pequeños y descriptivos; el dataset se versiona por manifiestos (las imágenes van en disco/Drive, no en git).
- **Decisiones:** cada decisión técnica importante se registra en `docs/decisiones/AAAA-MM-DD-titulo.md` (qué se decidió, alternativas, por qué).
- **Registro de vuelos:** cada vuelo/visita de campo genera una entrada en `docs/bitacora/` (fecha, lugar, condiciones, resultados, fallos).
- **Riesgos principales y mitigación:**

| Riesgo | Prob. | Impacto | Mitigación |
|---|---|---|---|
| ZED SDK incompatible con JetPack 7 | Alta | Alto | Fase 0 inmediata; árbol de decisión con 3 planes B (doc 03) |
| Sin acceso a finca infectada / experto | Media | Crítico | Contactar 3+ fincas y 2+ expertos desde la semana 1; datasets públicos como colchón |
| Etiquetas sin valor diagnóstico (confusión con deficiencias nutricionales) | Media | Alto | Validación por fitopatólogo; doble etiquetado con medición de acuerdo |
| Fotos aéreas no diagnósticas (blur, distancia, oclusión) | Media | Alto | Protocolo de captura probado en visita 1 con celular Y dron; estabilización/ajuste de exposición |
| Modelo no generaliza fuera de la finca de entrenamiento | Media | Medio | Test por planta/visita; validar en ≥2 sitios; aumentado de datos |
| Crash del dron | Media | Alto | Checklist de vuelo, piloto practicado en simulador/campo abierto, montaje protegido de la Jetson |
| Regulación bloquea uso comercial | Baja (académico) / Alta (comercial) | Medio | Doc 10; registro AFAC antes de la fase comercial |
