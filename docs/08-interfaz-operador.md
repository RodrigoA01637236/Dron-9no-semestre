# 08 — Interfaz del operador

Requisito de accesibilidad: el usuario final (operador/agrónomo) no instala nada. La Jetson levanta su propio WiFi y sirve una página web; cualquier celular o laptop se conecta y la abre.

## 1. Hotspot WiFi en la Jetson

Con NetworkManager (incluido en Ubuntu):

```bash
sudo nmcli device wifi hotspot ifname wlan0 ssid DRON-SIGATOKA password "eleccion-del-equipo"
# Persistente entre reinicios:
sudo nmcli connection modify Hotspot connection.autoconnect yes
```

La Jetson queda típicamente en `10.42.0.1`. El operador se conecta a la red `DRON-SIGATOKA` y abre `http://10.42.0.1` en el navegador.

Notas:
- Si el kit no tiene WiFi integrado, un dongle USB WiFi con soporte AP resuelve (~$300 MXN).
- Alcance práctico de un hotspot: decenas de metros — suficiente para operar junto al punto de despegue. La UI debe tolerar desconexiones (el dron se aleja) y re-sincronizar al volver: por eso el estado vive en la Jetson, no en el navegador.

## 2. Servidor web — `ui/app.py` (Flask)

Responsabilidades:
- Servir la página (HTML + Leaflet, estáticos locales — **sin CDN**: en campo no hay internet; descargar `leaflet.js/css` al repo).
- API JSON: `GET /api/results` (lista de resultados de inferencia), `GET /api/status` (GPS, batería, FPS, disco), `POST /api/capture` (disparo manual), `GET /photos/<file>` (miniaturas).
- Leer los `.result.json` que produce la inferencia (doc 07) — el filesystem es la cola; simple y robusto.

```python
from flask import Flask, jsonify, send_from_directory
from pathlib import Path
import json

app = Flask(__name__, static_folder="static")
FLIGHT_DIR = Path("data/flights/actual")

@app.get("/api/results")
def results():
    out = [json.loads(p.read_text()) for p in sorted(FLIGHT_DIR.glob("*.result.json"))]
    return jsonify(out)

@app.get("/api/status")
def status():
    from mavlink.telemetry import STATE
    return jsonify(vars(STATE))

# POST /api/capture → señal al servicio de captura (archivo flag o socket local)
```

## 3. Página del mapa (Leaflet)

Elementos, en orden de importancia para el usuario en campo:

1. **Mapa** con la posición del dron y un marcador por foto procesada: verde (sana), rojo (Sigatoka), naranja (otra condición), gris (no diagnosticable/baja confianza). Tocar un marcador → miniatura de la foto + clase + confianza + hora.
2. **Barra de estado** siempre visible: fix GPS sí/no, batería del dron, fotos tomadas/procesadas, espacio en disco.
3. **Botón grande de captura manual** (además del modo por intervalo).
4. Lista/galería de detecciones rojas para revisión rápida al aterrizar.

Guías de diseño (usuario = operador con guantes, al sol, en un celular):
- Botones grandes, alto contraste, texto en español llano ("Planta enferma", no "sigatoka_temprana p=0.87").
- La confianza del modelo se comunica como categoría ("detección segura" / "revisar"), no como decimal.
- Polling simple (`fetch` cada 2 s) es suficiente; WebSockets no aportan a esta escala.
- Sin capas de mapa online: en campo no hay internet. Fondo blanco con la traza del vuelo basta; como mejora, teselas descargadas de la zona (OpenStreetMap permite uso offline de teselas generadas con herramientas libres).

## 4. Reporte post-vuelo (fase 6, pero diseñarlo desde ahora)

Al terminar la sesión, un script genera el entregable que el cliente realmente valora:

- Resumen: fecha, finca, duración, plantas inspeccionadas, % con detección.
- Mapa estático con los marcadores (folium → HTML/PNG).
- Tabla de detecciones con foto de evidencia, GPS y severidad.
- Formato: HTML autocontenido y/o PDF (weasyprint). Descargable desde la propia UI.

**Criterio de salida de la fase 4 (parte UI):** una persona ajena al equipo, con un celular y una instrucción de una línea ("conéctate al WiFi DRON-SIGATOKA y abre 10.42.0.1"), ve el mapa actualizarse durante una sesión de captura en tierra.
