<!-- impeccable:product-schema 1 -->

# Estación de tierra — Sigatoka

## Platform

web

## Users

- **Operador del dron / estudiante del equipo** (Platanos Machos, MR3002B, Tec): importa
  vuelos en la laptop al regresar del campo, revisa diagnósticos y corre reentrenamientos.
- **Agrónomo o productor**: revisa fotos de menor confianza, corrige la etiqueta (sana,
  Sigatoka, otra condición) y consulta el mapa de la finca para decidir dónde aplicar.
- **Profesor / jurado del curso**: ve la estación en demos y presentaciones; necesita entender
  en segundos qué detecta el sistema y con qué confianza.

Uso típico: laptop Windows en una mesa de trabajo o bajo techo junto al cultivo, a veces sin
internet. Ocasionalmente desde un celular en la misma red WiFi (`--red`).

## Product Purpose

Convertir las fotos de un vuelo de dron sobre plantaciones de plátano en un mapa de zonas
con Sigatoka, con un humano en el ciclo: cada corrección se guarda, el modelo se reentrena
por lotes y solo se activa una versión nueva si mejora en un examen de campo que nunca se
entrena. Éxito = el agrónomo confía en el mapa porque puede ver la evidencia de cada punto.

## Positioning

Todo corre local en la laptop de tierra (sin nube, sin cuentas), y el aprendizaje es honesto:
el examen de campo separado y la activación humana del modelo evitan que el sistema "mejore"
solo en apariencia.

## Operating Context

- Flujo: volar → copiar carpeta (fotos + JSON del Pixhawk) → Importar → revisar → mapa →
  reentrenar → comparar → activar.
- Identificación puntual: subir o tomar una foto de una hoja y obtener el diagnóstico.
- Servidor Flask en `ui/estacion.py`, puerto 5050; datos en `data/estacion/`.

## Capabilities and Constraints

- Clasificador YOLOv8n-cls exportado a ONNX (onnxruntime), 384 px, umbral 0.65; clases
  `otra_condicion`, `sana`, `sigatoka`. Por debajo del umbral el resultado es "no
  diagnosticable".
- GPS sin RTK (±2–3 m): el mapa agrega por zonas, no por planta.
- Debe funcionar sin internet (Leaflet y fuentes locales; teselas satelitales solo con red).
- Interfaz en español. Sin emojis.
- Categorías nuevas solo desde la zona técnica, validadas por un agrónomo.

## Brand Commitments

- Nombre de trabajo: "Estación de tierra" / "Estación Sigatoka". Equipo: Platanos Machos.
- Colores de categoría fijados en datos: sana #2e9e44, sigatoka #d7263d, otra condición
  #f0a202 (editables, pero son el significado del mapa).

## Evidence on Hand

- Modelo v1: 91.8 % top-1 en test de fotos públicas cercanas (no aéreas). No hay aún
  validación con fotos reales del dron; no presentar el sistema como validado en campo.
- No hay logotipo, fotografía de marca ni testimonios.

## Product Principles

1. La evidencia antes que el veredicto: cada diagnóstico muestra la foto y su confianza.
2. El humano decide: el sistema propone, el agrónomo confirma, el equipo activa modelos.
3. Honestidad sobre la incertidumbre: baja confianza se dice, no se esconde.
4. Funciona en el campo: offline, una laptop, sin pasos técnicos para el agrónomo.

## Accessibility & Inclusion

Uso con luz intensa y pantallas de laptop modestas: contraste alto, objetivos táctiles
amplios, atajos de teclado en la revisión. El color de categoría nunca es la única señal
(siempre acompañado de texto).
