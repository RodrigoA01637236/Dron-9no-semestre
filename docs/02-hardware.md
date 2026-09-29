# 02 — Hardware y alimentación

## Inventario y estado

| Componente | Detalle | Notas |
|---|---|---|
| Jetson Orin Nano 8 GB Developer Kit | Módulo P3767-0005, carrier P3768-0000 | JetPack 7.2.1, arranca desde NVMe |
| Kingston NVMe 1 TB | `nvme0n1`, raíz en `nvme0n1p1` (~930 GB) | Sistema y datos de vuelo |
| Pixhawk 6C | Controlador de vuelo | Conexión a Jetson por USB (fase actual) |
| Cámara ZED | Conectada por flex a CAM0/CAM1 | Ver doc 03 — compatibilidad pendiente |
| Fuente de banco | 15 V / 2 A (30 W) | Solo para desarrollo en mesa |
| Batería de vuelo | Tattu 4S, 14.8 V nominal, 5200 mAh, 76.96 Wh, 35C | Alimenta motores + (a futuro) Jetson |

## Verificación del sistema (comandos de referencia)

```bash
cat /proc/device-tree/model        # modelo del hardware
cat /etc/nv_tegra_release          # versión de Jetson Linux (R39.2.1)
free -h                            # RAM (~7.4 GiB utilizables)
lsblk                              # raíz en nvme0n1p1
nvcc --version                     # CUDA 13.2
sudo tegrastats                    # uso de GPU/CPU, temperatura, potencia
```

`tegrastats` es la herramienta de referencia para medir consumo (`VDD_IN`) y temperatura durante las pruebas de carga. En reposo/carga ligera se han observado ~5.4–7.2 W y 49–52 °C.

## Modos de potencia de la Jetson

La Orin Nano tiene perfiles de potencia (7 W / 15 W / 25 W según versión de JetPack):

```bash
sudo nvpmodel -q            # perfil actual
sudo nvpmodel -m 0          # perfil máximo (ver tabla con -q --verbose)
sudo jetson_clocks          # fija relojes al máximo (para benchmarks)
```

Para el vuelo conviene caracterizar el pipeline en el perfil de menor consumo que mantenga los FPS objetivo — cada watt sale de la batería de vuelo.

## Alimentación

### En banco (desarrollo)

La carrier board acepta **9–20 V** por el jack DC. La fuente de 15 V / 2 A (30 W) es suficiente para desarrollo, pero está justa para carga máxima (Jetson a 25 W + cámara + NVMe + picos). Si durante pruebas de estrés hay reinicios o cuelgues, sospechar de la fuente antes que del software; ideal conseguir una de 19 V / 3 A+ para el banco.

### En el dron (fase 6)

**No conectar la Jetson directo a la batería de vuelo sin regulación/filtrado.** Aunque 4S (14.8 V nominal, 16.8 V cargada) cae dentro del rango 9–20 V, los ESC y motores inyectan ruido y transitorios que pueden reiniciar o dañar la Jetson.

Diseño recomendado:
1. **Regulador DC-DC dedicado** (BEC de calidad o convertidor buck ajustado a 12 V, ≥5 A de margen) alimentado de la batería, exclusivo para la Jetson + cámara.
2. **Filtrado:** capacitor de bulk (≥470 µF low-ESR) en la entrada del regulador + filtro LC si se observa ruido; cables cortos y trenzados.
3. **Protección:** fusible en la línea de la Jetson; diodo TVS contra picos.
4. **Medición previa:** con `tegrastats`, registrar el consumo real del pipeline completo (captura + inferencia + WiFi). Presupuesto de energía: la Tattu de ~77 Wh alimenta motores primero; la Jetson a ~15 W consume ~5 Wh en un vuelo de 20 min — el factor limitante son los motores, no la Jetson, pero planificar vuelos de **15–20 min máximo** y llevar baterías de repuesto.
5. **Apagado seguro:** la Jetson no tolera bien cortes de energía repetidos (corrupción de FS). Añadir al software un apagado ordenado por telemetría de batería baja, y considerar `Overlayroot` o sync agresivo de los datos de captura.

### Montaje físico (fase 6)

- Jetson y cámara sobre soportes con **amortiguación de vibración** (gomas/gel); las vibraciones del frame arruinan fotos (motion blur) y agrietan soldaduras/conectores flex.
- Los conectores flex de la cámara (CAM0/CAM1) son frágiles: fijar el cable con cinta kapton y evitar radios de curvatura pequeños.
- Flujo de aire para el disipador de la Jetson; en vuelo hay viento, pero en pruebas de banco largas vigilar temperatura (>70 °C sostenidos ⇒ throttling).
- Proteger el puerto USB de la conexión a Pixhawk contra desconexión por vibración (conector con seguro o fijación mecánica del cable).

## Pixhawk 6C — conexionado

- **Fase actual (banco y primeros vuelos):** Pixhawk ↔ Jetson por **USB** (aparece como `/dev/ttyACM0`). Simple y confiable en banco; en vuelo el USB es sensible a vibración.
- **Fase 6 (recomendado para producto):** UART dedicado — `TELEM2` de la Pixhawk ↔ pines UART del header J12 de la Jetson (con niveles 3.3 V, sin conversor). Requiere configurar `MAV_1_CONFIG`/`SER_TEL2_BAUD` en PX4. Más robusto mecánicamente y libera el USB.
- El GPS, la radio RC y los ESC se conectan a la Pixhawk según el manual estándar de PX4/Holybro; la Jetson nunca está en la ruta de control de vuelo (si la Jetson muere, el dron sigue volando).

## Regla de arquitectura de seguridad

**La Pixhawk vuela el dron; la Jetson solo observa y registra.** En la fase actual, la Jetson no envía comandos de movimiento — solo lee telemetría. Cuando en fase 7 se agregue vuelo semiautónomo, los comandos de la Jetson pasarán por los modos de misión de PX4 con la radio RC siempre lista para retomar control manual (kill switch configurado).
