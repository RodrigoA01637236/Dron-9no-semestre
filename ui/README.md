# ui/

Interfaz web del operador servida desde la Jetson (Flask + Leaflet, sin internet). Ver [docs/08-interfaz-operador.md](../docs/08-interfaz-operador.md).

| Componente | Rol |
|---|---|
| `app.py` | Servidor Flask: página, API de resultados/estado, disparo manual |
| `static/` | Leaflet descargado localmente (sin CDN — en campo no hay internet) + JS/CSS propios |

El operador se conecta al hotspot WiFi de la Jetson y abre `http://10.42.0.1`. Cero instalación.
