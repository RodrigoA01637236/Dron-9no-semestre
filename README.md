# Proyecto Dron — Detección de Sigatoka (Mycosphaerella) en plátano

Sistema de inspección fitosanitaria basado en dron: un operador vuela manualmente un dron equipado con una computadora NVIDIA Jetson y una cámara, se acerca a las plantas de plátano, captura fotos georreferenciadas, y un modelo de visión por computadora identifica plantas afectadas por Sigatoka (Mycosphaerella fijiensis / musicola).

## Arquitectura del sistema

```
                 ┌──────────────────────── DRON ────────────────────────┐
                 │                                                      │
  Radio RC ──────►  Pixhawk 6C ◄──── USB/MAVLink ────  Jetson Orin Nano │
  (operador)     │  (control de vuelo,                 (visión, IA,     │
                 │   GPS, telemetría)                   lógica misión)  │
                 │                                        ▲             │
                 │                                        │ CSI/USB     │
                 │                                     Cámara           │
                 └──────────────────────────────────────────────────────┘
                                                          │
                                        WiFi hotspot de la Jetson
                                                          ▼
                                        Celular/laptop del operador
                                        (mapa web de plantas afectadas)
```

Flujo de datos: `Cámara → Captura georreferenciada (GPS de Pixhawk) → Inferencia (TensorRT en Jetson) → Mapa web (Flask + Leaflet) → Operador/Agrónomo`

## Hardware

| Componente | Modelo | Estado |
|---|---|---|
| Computadora de misión | NVIDIA Jetson Orin Nano 8 GB Developer Kit (P3767-0005 / carrier P3768-0000) | ✅ Operativa |
| Sistema operativo | JetPack 7.2.1 — Ubuntu 24.04.4, Jetson Linux R39.2.1, CUDA 13.2 | ✅ Instalado |
| Almacenamiento | Kingston NVMe 1 TB (sistema arranca desde NVMe) | ✅ Operativo |
| Controlador de vuelo | Pixhawk 6C | ✅ Disponible |
| Cámara | ZED (conexión CSI, CAM0/CAM1) | ⚠️ Compatibilidad con JetPack 7 pendiente de verificar |
| Batería | Tattu 4S 14.8 V 5200 mAh (~77 Wh) | ✅ Disponible |

## Documentación

Toda la documentación está en [`docs/`](docs/). Empieza por el plan maestro.

| Documento | Contenido |
|---|---|
| [00 — Visión general](docs/00-vision-general.md) | Qué hace el sistema, cómo funciona de punta a punta, decisiones de diseño |
| [01 — Plan maestro](docs/01-plan-maestro.md) | Todas las fases del proyecto, de la validación de hardware al producto comercial |
| [02 — Hardware y alimentación](docs/02-hardware.md) | Jetson, alimentación en banco y en dron, montaje |
| [03 — Cámara](docs/03-camara.md) | Verificación ZED/JetPack 7, planes B, protocolo de captura |
| [04 — Pixhawk y MAVLink](docs/04-pixhawk-mavlink.md) | Conexión Jetson↔Pixhawk, MAVSDK, telemetría y geoetiquetado |
| [05 — Datos y dataset](docs/05-datos-dataset.md) | Datasets públicos, recolección propia, etiquetado, versionado |
| [06 — Entrenamiento del modelo](docs/06-entrenamiento.md) | Transfer learning en Colab, métricas, export ONNX/TensorRT |
| [07 — Inferencia en la Jetson](docs/07-inferencia-jetson.md) | Despliegue TensorRT, pipeline de inferencia en vuelo |
| [08 — Interfaz del operador](docs/08-interfaz-operador.md) | Hotspot WiFi, servidor web con mapa, uso en campo |
| [09 — Validación en campo](docs/09-validacion-campo.md) | Protocolo de vuelos, escala Stover/Fouré, métricas contra experto |
| [10 — Regulación y seguridad](docs/10-regulacion-seguridad.md) | AFAC / NOM-107-SCT3-2019, seguridad operacional |
| [11 — Producto y negocio](docs/11-producto-negocio.md) | Camino a producto vendible, escenarios, escalamiento |

## Estructura del repositorio

```
proyecto-dron/
├── docs/          Documentación completa del proyecto
├── vision/        Código de captura, inferencia y modelo
├── mavlink/       Comunicación con Pixhawk (MAVSDK)
├── ui/            Interfaz web del operador (Flask + Leaflet)
├── scripts/       Instalación, verificación y utilidades
└── data/          Datos locales (no versionados; ver data/README.md)
```

## Estado y siguiente paso

**Siguiente paso inmediato:** verificar la compatibilidad de la cámara ZED con JetPack 7.2.1 — ver [docs/03-camara.md](docs/03-camara.md). Esta prueba decide la arquitectura de captura de todo el proyecto.

## Software (todo gratuito / open source)

Ubuntu, JetPack (CUDA, cuDNN, TensorRT), Python, MAVSDK, PX4/ArduPilot en Pixhawk, Ultralytics YOLO, PyTorch, ONNX, Label Studio, Google Colab (entrenamiento), Flask, Leaflet, QGroundControl.
