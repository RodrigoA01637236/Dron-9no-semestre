# mavlink/

Comunicación Jetson ↔ Pixhawk 6C. Ver [docs/04-pixhawk-mavlink.md](../docs/04-pixhawk-mavlink.md).

| Módulo | Rol |
|---|---|
| `telemetry.py` | Servicio que mantiene el último estado del dron (`STATE`): GPS, actitud, batería, salud |
| `test_connection.py` | Prueba de humo: imprime telemetría 10 s |

Regla de arquitectura: **este es el único módulo que habla con la Pixhawk.** El resto del sistema lee `telemetry.STATE`. En la fase actual la Jetson solo lee telemetría — no envía comandos de vuelo.
