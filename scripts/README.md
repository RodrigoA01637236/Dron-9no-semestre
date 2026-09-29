# scripts/

Utilidades de instalación, verificación y datos.

| Script (planificado) | Rol | Doc |
|---|---|---|
| `check_system.sh` | Verificación de la Jetson: CUDA, TensorRT, cámara, puerto Pixhawk, disco | [02](../docs/02-hardware.md) |
| `make_splits.py` | Genera splits train/val/test por planta/visita desde los manifiestos (semilla fija) | [05](../docs/05-datos-dataset.md) §6 |
| `build_engine.sh` | ONNX → engine TensorRT en la Jetson (`trtexec`) | [07](../docs/07-inferencia-jetson.md) §2 |
| `flight_report.py` | Genera el reporte post-vuelo HTML/PDF | [08](../docs/08-interfaz-operador.md) §4 |
| `systemd/` | Unidades de arranque automático de los servicios | [07](../docs/07-inferencia-jetson.md) §5 |
