# 11 — Camino a producto y escenarios de negocio

Este documento separa con honestidad lo que el semestre entrega (evidencia) de lo que el negocio necesita (clientes que pagan), y traza los escenarios.

## 1. Qué se vende (y qué no)

**No se vende un dron.** Un productor no quiere comprar hardware de miles de pesos, mantenerlo, asegurarlo y aprender a pilotearlo. Lo que compra es el resultado:

> "Sabemos qué plantas de tu parcela tienen Sigatoka, dónde están, y qué tan avanzadas — antes de que pierdas la hoja."

De ahí los modelos de negocio posibles, del más viable al más ambicioso:

| Modelo | Qué recibe el cliente | Quién opera | Barrera de entrada |
|---|---|---|---|
| **Servicio de inspección** (recomendado para empezar) | Reporte por visita: mapa de incidencia + evidencia fotográfica + conteos | El equipo (piloto propio) | Baja: un dron, trámites AFAC, primeros clientes |
| Suscripción de monitoreo | Inspecciones periódicas + historial de evolución por lote | El equipo | Media: requiere retención y logística |
| Licencia del sistema | Kit (o integración a su dron) + software + capacitación | El cliente grande (exportadora) | Alta: soporte, robustez fase 6 completa |
| App móvil de diagnóstico | Diagnóstico por foto de celular, freemium | El agricultor mismo | Media: el mismo modelo ONNX; mercado amplio, monetización difícil |
| Datos agregados (SaaS) | Mapas de incidencia regional para exportadoras/aseguradoras/comités | — | Muy alta: exige escala y credibilidad previas |

## 2. El cliente

Hipótesis a validar hablando con clientes reales (no en el pizarrón):

- **Productor mediano/grande de plátano** (≥10 ha): paga por reducir fungicida y pérdidas. Pregunta que hará: "¿cuánto me ahorra por hectárea vs. lo que me cuestas?"
- **Cooperativas y comités de sanidad vegetal:** inspeccionan muchas parcelas con pocos técnicos; el sistema multiplica a su personal.
- **Exportadoras/certificadoras:** necesitan trazabilidad fitosanitaria documentada de sus proveedores.

Tarea de descubrimiento (paralela a la técnica, sin código): **5 entrevistas** con productores/agrónomos de la región usando las fotos del prototipo. Preguntas: cómo manejan hoy la Sigatoka, cuánto gastan en fungicida y en inspección, qué harían con el mapa, cuánto pagarían por visita. Cinco conversaciones reales valen más que cualquier plan de negocio teórico.

## 3. Números de referencia (a validar en las entrevistas)

- Costo del control de Sigatoka en plantación comercial: comúnmente citado como 25–30 % del costo de producción — es el dolor que se ataca.
- Capacidad operativa realista del servicio v1: con vuelos de 15–20 min y baterías de repuesto, del orden de 2–4 ha inspeccionadas a detalle por jornada (vuelo manual planta a planta). **Este número mejora radicalmente con vuelo semiautónomo (fase 7)** — por eso esa fase es la inversión clave del negocio, no un lujo técnico.
- Costos del servicio: piloto (día), transporte, desgaste/baterías, seguro, trámites AFAC, tiempo de reporte. Ponerles cifra tras los primeros vuelos reales.

## 4. Escenarios

**Escenario A — El resultado técnico es bueno (F1 ≥ 0.85 y concordancia de campo alta):**
1. Con el reporte de validación + video demo: aplicar a incubadora universitaria y fondos de emprendimiento estudiantil / AgTech.
2. Ofrecer 3 inspecciones gratuitas a productores de la región a cambio de testimonio y acceso a datos → primeros casos de éxito → primer cliente de pago.
3. Priorizar fase 7.1 (vuelo semiautónomo) para multiplicar hectáreas/hora, que es lo que hace el negocio escalable.

**Escenario B — El modelo funciona pero el dron aporta poco (las fotos de celular diagnostican igual y más barato):**
- Pivote honesto: producto = app/servicio de diagnóstico por foto para agrónomos a pie; el dron queda para copas altas y para la versión autónoma futura. El activo (dataset + modelo) es el mismo — por diseño, nada se tira.

**Escenario C — El diagnóstico visual temprano resulta poco confiable con RGB:**
- Reposicionar como herramienta de severidad/monitoreo (estadios visibles, que es donde el mapa georreferenciado ya aporta valor de gestión), y evaluar cámara multiespectral para presintomático como línea futura con financiamiento.

**Escenario D — Sin acceso suficiente a campo este semestre:**
- El semestre se defiende con: plataforma completa funcionando + modelo baseline con datasets públicos + protocolo de validación listo. La validación de campo se ejecuta al inicio del siguiente ciclo. Es un resultado académico válido; retrasa, no mata, el negocio.

## 5. Expansión (visión, no compromiso)

La plataforma (captura georreferenciada + pipeline de datos + inferencia embarcada) es agnóstica de la enfermedad. Orden natural de expansión, cada una condicionada a tener su dataset validado:

1. **Fusarium R4T** — la amenaza existencial del banano en LATAM, con atención gubernamental (SENASICA) y de la industria. Detección visual aérea de síntomas (marchitez, amarillamiento) es plausible y el interés institucional es alto.
2. Otras del plátano (Moko, Erwinia).
3. Otros cultivos de la región: HLB en cítricos, roya del café, antracnosis en aguacate.

Cada expansión reutiliza: protocolo de captura, pipeline de etiquetado con experto, entrenamiento, plataforma de vuelo y UI. Eso — no el dron — es la empresa.

## 6. Reglas de honestidad comercial

- No prometer "detección temprana presintomática" sin evidencia; prometer lo validado en el doc 09, con sus intervalos.
- Presentar siempre el sistema como **apoyo al agrónomo**, no su reemplazo: el diagnóstico final y la decisión de tratamiento son humanos. (Además de honesto, reduce resistencia del canal: el agrónomo es aliado, no competencia.)
- Toda cifra del pitch debe poder rastrearse a un vuelo documentado en la bitácora o a una fuente citable.
