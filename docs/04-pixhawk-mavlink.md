# 04 — Pixhawk 6C y MAVLink: telemetría y geoetiquetado

Objetivo de la fase 1: la Jetson lee de la Pixhawk posición GPS, actitud y estado, y cada captura de cámara queda etiquetada con esos datos.

## 1. Preparar la Pixhawk 6C

1. Instalar **QGroundControl** (gratuito) en una laptop.
2. Conectar la Pixhawk por USB y flashear el firmware estable de **PX4** (o ArduPilot si el equipo lo domina; esta guía asume PX4).
3. Calibraciones básicas en QGC: sensores (acelerómetro, compás), radio RC, modos de vuelo, failsafes (pérdida de RC → RTL o aterrizaje).
4. Verificar en QGC que hay fix de GPS al aire libre (en interiores no habrá posición — para pruebas de banco se puede simular o aceptar telemetría sin fix).

## 2. Conexión física Jetson ↔ Pixhawk

**Fase actual — USB:** cable USB-C/micro-USB de la Pixhawk a un puerto USB de la Jetson.

```bash
# En la Jetson, con la Pixhawk conectada y encendida:
ls -l /dev/ttyACM*        # debe aparecer /dev/ttyACM0
sudo usermod -aG dialout $USER   # permiso de puerto serie (relogin después)
```

**Futuro — UART (más robusto en vuelo):** `TELEM2` de la Pixhawk ↔ UART del header de 40 pines de la Jetson (3.3 V, TX↔RX cruzados, GND común). En PX4: `MAV_1_CONFIG = TELEM2`, baudrate 921600. En la Jetson el puerto será `/dev/ttyTHS*`.

## 3. Instalar MAVSDK-Python en la Jetson

```bash
python3 -m venv ~/venvs/dron && source ~/venvs/dron/bin/activate
pip install mavsdk
```

(Si el wheel de `mavsdk` no existiera para la combinación aarch64/versión de Python de Ubuntu 24.04, alternativa equivalente: `pip install pymavlink` — API más cruda pero sin dependencias binarias del servidor MAVSDK. El diseño del código abajo aísla esta elección en un solo módulo.)

## 4. Módulo de telemetría — `mavlink/telemetry.py`

Diseño: un servicio que mantiene en memoria el último estado conocido del dron y lo expone al resto del sistema. Nada más lo toca directamente.

```python
"""Servicio de telemetría: mantiene el último estado de la Pixhawk."""
import asyncio
from dataclasses import dataclass, field
from mavsdk import System

@dataclass
class DroneState:
    lat: float | None = None
    lon: float | None = None
    alt_rel: float | None = None      # m sobre el punto de despegue
    heading: float | None = None      # grados
    battery_pct: float | None = None
    gps_ok: bool = False
    armed: bool = False

STATE = DroneState()

async def run(address: str = "serial:///dev/ttyACM0:57600"):
    drone = System()
    await drone.connect(system_address=address)
    async for st in drone.core.connection_state():
        if st.is_connected:
            break
    asyncio.gather(_position(drone), _attitude(drone),
                   _battery(drone), _health(drone))

async def _position(drone):
    async for p in drone.telemetry.position():
        STATE.lat, STATE.lon = p.latitude_deg, p.longitude_deg
        STATE.alt_rel = p.relative_altitude_m

async def _attitude(drone):
    async for h in drone.telemetry.heading():
        STATE.heading = h.heading_deg

async def _battery(drone):
    async for b in drone.telemetry.battery():
        STATE.battery_pct = b.remaining_percent * 100

async def _health(drone):
    async for h in drone.telemetry.health():
        STATE.gps_ok = h.is_global_position_ok
```

Prueba de humo (primer hito de la fase 1):

```python
# mavlink/test_connection.py — imprimir 10 s de telemetría
import asyncio, mavlink.telemetry as t

async def main():
    asyncio.create_task(t.run())
    for _ in range(10):
        await asyncio.sleep(1)
        print(t.STATE)

asyncio.run(main())
```

Resultado esperado: heartbeat conecta, y con la Pixhawk al aire libre se ven lat/lon reales. Sin fix de GPS, `gps_ok=False` y posición `None` — el sistema debe seguir funcionando (ver "modo degradado").

## 5. Captura georreferenciada — `vision/capture.py`

Cada disparo produce **dos archivos con el mismo nombre base**:

```
data/flights/2026-10-15_finca-lopez/
├── 143502_0001.jpg
├── 143502_0001.json
└── ...
```

Formato del sidecar JSON (contrato estable — la UI, el etiquetado y el reporte dependen de él):

```json
{
  "ts": "2026-10-15T14:35:02.412-06:00",
  "seq": 1,
  "lat": 17.989123, "lon": -92.947456, "alt_rel_m": 4.2,
  "heading_deg": 213.0,
  "gps_ok": true,
  "battery_pct": 78.5,
  "camera": "zedx-left", "exposure": "auto",
  "flight_id": "2026-10-15_finca-lopez",
  "operator": "iniciales"
}
```

Reglas de implementación:
- El módulo de captura **lee** `telemetry.STATE`; jamás habla con la Pixhawk directamente.
- **Modo degradado:** sin GPS o sin Pixhawk, la captura sigue; el JSON registra `gps_ok: false`. Los datos son sagrados: una foto sin GPS sirve para el dataset; una foto no tomada no sirve para nada.
- Escribir el JSON con `os.replace()` (escritura atómica) para no corromper metadata si se corta la energía.
- Disparadores soportados: intervalo fijo (p. ej. cada 2 s), comando desde la UI web, y (futuro) botón físico/canal RC vía Pixhawk.

## 6. Verificación integrada de la fase 1

1. Jetson + Pixhawk + cámara encendidos al aire libre, sin volar.
2. Iniciar telemetría y captura por intervalo.
3. Caminar 50–100 m con el equipo.
4. Volcar los JSON sobre un mapa (script rápido con `folium`, o arrastrar un CSV a Google My Maps).
5. **Criterio de salida:** la traza de fotos en el mapa coincide con el recorrido real.

## 7. Problemas comunes

| Síntoma | Causa probable | Solución |
|---|---|---|
| No aparece `/dev/ttyACM0` | Cable solo de carga; Pixhawk sin encender | Cambiar cable; alimentar la Pixhawk |
| `Permission denied` en el puerto | Usuario fuera del grupo `dialout` | `sudo usermod -aG dialout $USER` + relogin |
| Conecta pero sin posición | Sin fix GPS (interior) | Probar al aire libre; verificar GPS en QGC |
| Telemetría se congela en vuelo | Vibración desconecta el USB | Fijar el cable; migrar a UART (TELEM2) |
| MAVSDK no instala en la Jetson | Sin wheel para la plataforma | Fallback a `pymavlink` (mismo módulo `telemetry.py`, otra implementación) |
