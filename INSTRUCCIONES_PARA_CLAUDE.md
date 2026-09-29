# Instrucciones: subir esta documentación al repositorio

Este paquete contiene la documentación y estructura inicial del **Proyecto Dron — Detección de Sigatoka (Mycosphaerella) en plátano** (Jetson Orin Nano 8GB + Pixhawk 6C + cámara ZED), generada en una sesión anterior de Claude Code. Hay que subirla tal cual al repositorio de esta sesión.

## Pasos

1. Descomprimir/copiar **todo el contenido de este paquete** (respetando la estructura de carpetas) a la **raíz del repositorio**, EXCEPTO este archivo (`INSTRUCCIONES_PARA_CLAUDE.md`), que no debe subirse.
2. Si algún archivo ya existe en el repo (p. ej. `README.md` o `.gitignore`), fusionar el contenido en lugar de sobrescribir a ciegas: conservar lo que ya tenga el repo y añadir lo de este paquete.
3. Hacer commit con un mensaje como: `Agrega plan maestro y documentación completa del proyecto`.
4. Push a la rama de trabajo que corresponda en esa sesión.

## Contenido del paquete

```
README.md                        Portada: arquitectura, hardware, índice de docs
.gitignore                       Excluye imágenes/modelos pesados de git
docs/00-vision-general.md        Qué hace el sistema y decisiones de diseño
docs/01-plan-maestro.md          Fases 0–7 con pasos, entregables y criterios de salida
docs/02-hardware.md              Jetson, alimentación (banco y dron), montaje
docs/03-camara.md                Verificación ZED/JetPack 7, planes B, protocolo de captura
docs/04-pixhawk-mavlink.md       MAVSDK, telemetría, captura georreferenciada
docs/05-datos-dataset.md         Datasets públicos, recolección, etiquetado, versionado
docs/06-entrenamiento.md         Transfer learning en Colab, métricas, export ONNX
docs/07-inferencia-jetson.md     TensorRT, servicio de inferencia, systemd
docs/08-interfaz-operador.md     Hotspot WiFi + Flask + Leaflet (mapa en campo)
docs/09-validacion-campo.md      Protocolo de validación contra experto (escala Stover)
docs/10-regulacion-seguridad.md  AFAC / NOM-107-SCT3-2019, seguridad operacional
docs/11-producto-negocio.md      Modelos de negocio, escenarios A–D, expansión
docs/decisiones/README.md        Registro de decisiones técnicas
docs/bitacora/README.md          Bitácora de vuelos y visitas de campo
vision/README.md                 Rol y reglas del módulo de visión
mavlink/README.md                Rol y reglas del módulo MAVLink
ui/README.md                     Rol de la interfaz web del operador
scripts/README.md                Scripts planificados
data/README.md                   Reglas de datos (imágenes fuera de git) y registro de fuentes
```

## Contexto para la nueva sesión

- El plan completo y las prioridades están en `docs/01-plan-maestro.md`. La tarea más urgente del proyecto es la **Fase 0**: verificar la compatibilidad de la cámara ZED (conectada por CSI) con JetPack 7.2.1 — guía en `docs/03-camara.md`.
- El equipo ya tiene funcionando: Jetson Orin Nano 8GB con JetPack 7.2.1 (Ubuntu 24.04, CUDA 13.2) arrancando desde NVMe Kingston 1TB, y un script de detección con Ultralytics YOLO11n (`vision/detectar.py` en el repo del equipo).
- Si el repo destino ya contiene código (p. ej. `main.cpp`, `vision/detectar.py`), este paquete lo complementa: los README de `vision/`, `mavlink/`, etc. describen la arquitectura objetivo; integrar sin borrar el código existente.
