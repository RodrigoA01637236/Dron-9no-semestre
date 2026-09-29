# 00 — Visión general del sistema

## El problema

La Sigatoka (negra: *Mycosphaerella fijiensis* / *Pseudocercospora fijiensis*; amarilla: *M. musicola*) es la enfermedad foliar más costosa del cultivo de plátano y banano. Reduce el área fotosintética de la hoja, adelanta la maduración del fruto y obliga a aplicaciones intensivas de fungicida (en plantaciones comerciales puede representar 25–30 % del costo de producción). La detección temprana y localizada permite:

- Aplicar fungicida solo donde hace falta (ahorro directo).
- Deshojar/podar las plantas afectadas antes de que la infección se propague.
- Llevar un historial de incidencia por zona de la parcela.

El diagnóstico tradicional lo hace un agrónomo caminando la parcela y evaluando hojas con la escala de Stover modificada por Gauhl o el método de Fouré (estadios 1–6 de síntomas). Es confiable pero lento, costoso y no genera datos georreferenciados sistemáticos.

## La solución propuesta

Un dron operado manualmente que actúa como "los ojos" del agrónomo:

1. El operador vuela el dron por la plantación y se acerca a las plantas (las copas del platanar, difíciles de inspeccionar desde el suelo, quedan a la vista de la cámara).
2. La Jetson captura imágenes continuamente o bajo demanda, cada una etiquetada con la posición GPS que reporta la Pixhawk.
3. Un modelo de visión (clasificación/detección de hojas sanas vs. afectadas) corre a bordo en la Jetson con TensorRT.
4. Los resultados se muestran en tiempo real en un mapa web que la propia Jetson sirve por WiFi: el operador o el agrónomo lo abren desde un celular, sin instalar nada.
5. Al aterrizar, el sistema genera un reporte: mapa de incidencia, fotos de evidencia por planta, y severidad estimada.

### ¿Por qué un dron y no solo un celular?

Pregunta obligada que el proyecto debe poder responder (los compradores la harán):

- **Acceso a las copas.** Las hojas más jóvenes (donde la Sigatoka ataca primero, hojas 2–5) están a 3–6 m de altura. Desde el suelo se inspeccionan mal; el dron las ve de frente.
- **Cobertura y trazabilidad.** Cada observación queda georreferenciada automáticamente; caminar la parcela con celular no genera el mapa por sí solo.
- **Camino a la autonomía.** El vuelo manual es la fase 1. La arquitectura (Pixhawk + Jetson + MAVLink) permite evolucionar a rutas semiautónomas que escanean hectáreas — eso es lo que un celular nunca hará.

Honestidad técnica: para la *demostración de este semestre*, un celular tomaría fotos comparables. El valor diferencial del dron se materializa en la fase de autonomía. Por eso el plan trata al modelo de visión y al dataset como el activo central (funcionan en dron Y en celular), y al dron como la plataforma que escala.

## Decisiones de diseño y su justificación

| Decisión | Alternativa descartada | Razón |
|---|---|---|
| Inferencia a bordo (Jetson + TensorRT) | Procesar en la nube | Sin conectividad confiable en campo; latencia; costo de nube; la Jetson ya está comprada y funciona |
| Clasificación con cámara RGB mono | Aprovechar profundidad estéreo de la ZED | La profundidad no aporta al diagnóstico de manchas foliares; simplifica el pipeline; si la ZED falla, cualquier cámara sirve |
| Entrenar fuera de la Jetson (Colab) | Entrenar en la Jetson | 8 GB de RAM compartida es insuficiente para entrenar cómodo; Colab es gratis y con GPU mayor |
| Modelo exportado a ONNX | Formato nativo PyTorch | ONNX corre en Jetson (TensorRT), en PC y en Android — mantiene abierta la vía de app móvil |
| UI web servida desde la Jetson | App móvil nativa | Cero instalación para el usuario; se desarrolla una sola vez; accesible desde cualquier dispositivo |
| Vuelo manual (fase actual) | Vuelo autónomo desde el inicio | Reduce riesgo técnico y regulatorio; la autonomía es evolución, no requisito del MVP |
| MAVSDK-Python | pymavlink crudo / ROS 2 | API moderna y simple para telemetría/misiones; ROS 2 agrega complejidad que el proyecto aún no necesita |

## Los tres subsistemas (pistas de trabajo desacopladas)

El plan maestro (doc 01) organiza el trabajo en tres pistas que avanzan en paralelo y **ninguna bloquea a las otras**:

1. **Plataforma** — Jetson + cámara + Pixhawk + captura georreferenciada + UI. (Docs 02, 03, 04, 07, 08)
2. **Datos** — datasets públicos, protocolo de captura, recolección en campo, etiquetado validado por experto, versionado. Es el activo más valioso del proyecto. (Doc 05)
3. **Modelo** — entrenamiento por transfer learning, evaluación honesta, optimización para la Jetson. (Docs 06, 07)

Regla de oro: **el modelo y el dataset nunca deben depender de que el dron vuele**. Si el dron está en reparación, la recolección con celular y el entrenamiento continúan.

## Glosario mínimo

- **Sigatoka negra/amarilla**: enfermedades fúngicas foliares del plátano; la negra es la más agresiva.
- **Escala de Stover (mod. Gauhl)**: escala estándar de severidad 0–6 por porcentaje de área foliar afectada.
- **Estadios de Fouré**: 6 estadios de evolución del síntoma individual (pizca → estría → mancha con halo).
- **JetPack**: SDK de NVIDIA para Jetson (Ubuntu + CUDA + cuDNN + TensorRT + drivers).
- **MAVLink**: protocolo de comunicación con autopilotos (Pixhawk); **MAVSDK**: librería de alto nivel sobre MAVLink.
- **TensorRT**: motor de inferencia optimizada de NVIDIA; **ONNX**: formato portable de modelos.
- **GSD** (Ground Sample Distance): cm de terreno/objeto que representa cada píxel; define a qué distancia una foto sirve para diagnóstico.
