# ui/

Interfaz web del operador servida desde la Jetson (Flask + Leaflet, sin internet). Ver [docs/08-interfaz-operador.md](../docs/08-interfaz-operador.md).

| Componente | Rol |
|---|---|
| `app.py` | Servidor Flask: página, API de resultados/estado, disparo manual |
| `static/` | Leaflet descargado localmente (sin CDN — en campo no hay internet) + JS/CSS propios |

El operador se conecta al hotspot WiFi de la Jetson y abre `http://10.42.0.1`. Cero instalación.

## Estación de tierra (laptop) — `estacion.py`

Aplicación local para el equipo y el agrónomo: importar vuelos, ver las fotos en el mapa
(puntos y zonas), identificar hojas sueltas con foto o cámara (sana / Sigatoka / otra condición),
revisar/etiquetar diagnósticos y reentrenar el modelo con esas revisiones. Sistema visual: [DESIGN.md](../DESIGN.md).
Doble clic en `Iniciar-Estacion.bat`. Guía completa: [ESTACION.md](ESTACION.md).
Decisión de arquitectura: [docs/decisiones/2026-10-02-estacion-de-tierra.md](../docs/decisiones/2026-10-02-estacion-de-tierra.md).
