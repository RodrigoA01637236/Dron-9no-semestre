# 10 — Regulación y seguridad operacional

Punto ciego clásico de los proyectos de dron: el marco legal no importa para el prototipo en el laboratorio, pero **define si el producto puede venderse**. Conviene resolverlo temprano y barato, no tarde y caro.

> Aviso: esto es una guía de trabajo, no asesoría legal. Verificar la normativa vigente ante la AFAC antes de operar comercialmente — las reglas de RPAS se actualizan.

## 1. Marco mexicano — NOM-107-SCT3-2019 (AFAC)

La operación de RPAS (drones) en México la regula la Agencia Federal de Aviación Civil bajo la NOM-107-SCT3-2019. Puntos clave a verificar para este proyecto:

- **Clasificación por peso:** el dron del proyecto probablemente cae en RPAS pequeño (2–25 kg) — pesarlo con toda la carga (Jetson + cámara + batería) y confirmar categoría; los requisitos crecen con el peso.
- **Registro:** los RPAS por encima del umbral de juguete requieren **registro ante la AFAC**; el trámite es en línea y de bajo costo. Hacerlo aunque la operación actual sea académica.
- **Uso comercial vs. recreativo:** la operación con fines comerciales tiene requisitos adicionales (autorización de operador, y según peso/operación, licencia de piloto RPAS). El uso académico/experimental es más laxo, pero el plan de negocio debe presupuestar los trámites comerciales.
- **Reglas generales de operación** (aplican siempre): vuelo diurno y con línea de vista (VLOS); altura máxima general 120 m AGL (el proyecto vuela a <10 m — sin problema); no sobre personas no involucradas; lejos de aeródromos (verificar radio de exclusión de la zona de la finca); no en zonas restringidas.
- **Seguro de responsabilidad civil:** exigido para operación comercial; existen pólizas anuales de dron accesibles en México. Incluirlo en el modelo de costos del doc 11.
- **Propiedad privada:** volar sobre una finca requiere permiso del propietario (el protocolo del doc 09 ya lo exige por escrito).

Acción concreta de bajo costo (1 día): pesar el dron completo, registrarlo ante AFAC, y archivar en `docs/decisiones/` la categoría regulatoria y los requisitos que aplican hoy y los que aplicarían al vender el servicio.

## 2. Seguridad operacional

Reglas del equipo (imprimir con el checklist del doc 09):

1. **El piloto solo pilotea.** Nunca opera la UI ni discute resultados mientras el dron está en el aire; para eso está el segundo integrante.
2. **Kill switch configurado** en la radio RC y probado antes de cada sesión; failsafe de pérdida de RC = RTL/land configurado en PX4.
3. Distancia mínima a personas: 10 m; nadie debajo del dron, nunca.
4. Práctica previa: el piloto acumula vuelos en campo abierto (o simulador PX4) antes del primer vuelo entre plantas — volar cerca de vegetación a baja altura es lo más difícil que hará.
5. Hélices: inspección antes de cada vuelo; transportar el dron con las hélices desmontadas o protegidas.
6. Baterías LiPo: cargar con cargador balanceado bajo supervisión, transportar en bolsa ignífuga, nunca volar por debajo de 3.5 V/celda (regla del 25 % del doc 09).
7. Clima: no volar con lluvia (la electrónica no está sellada), ni viento >20 km/h a baja altura entre obstáculos.
8. **Registro de incidentes:** todo golpe, aterrizaje forzoso o comportamiento extraño va a la bitácora — los patrones de fallo se detectan por escrito, no de memoria.

## 3. Datos y privacidad

- Las fotos capturan la finca de un tercero: acordar con el propietario el uso de las imágenes (dataset, publicaciones, demo). Un acuerdo de una página firmado evita conflictos cuando el proyecto sea comercial.
- Evitar capturar personas; si aparecen incidentalmente, difuminar antes de publicar.
- El dataset con GPS revela ubicación de parcelas con enfermedad — información comercialmente sensible para el productor. Tratarla con confidencialidad; en publicaciones académicas, ofuscar coordenadas exactas.
