# 06 — Entrenamiento del modelo

Principio: **entrenar fuera de la Jetson** (Google Colab, gratis, GPU T4), **inferir en la Jetson** (TensorRT). La Jetson con 8 GB de RAM compartida no es máquina de entrenamiento.

## 1. Elección del modelo

| Etapa | Modelo | Por qué |
|---|---|---|
| Baseline (fase 3 inicio) | **YOLOv8n-cls** (clasificación) o EfficientNet-B0 | Pequeño, transfer learning trivial, export ONNX de una línea, corre sobrado en la Orin Nano |
| Evolución (cuando la foto contiene varias plantas/hojas) | **YOLOv8n / YOLOv8s** (detección) | Localiza cada hoja/lesión con caja; permite contar y mapear por planta |
| Futuro (severidad fina) | Segmentación (YOLOv8-seg) para % de área foliar afectada | Estimación directa de escala Stover |

Empezar SIEMPRE por clasificación: valida el problema con la décima parte del esfuerzo de etiquetado.

Nota de licencia para la fase comercial: Ultralytics YOLOv8 es AGPL-3.0 (uso comercial exige liberar el código derivado o pagar licencia). Para el prototipo académico es irrelevante; para el producto, alternativas con licencia permisiva: EfficientNet/MobileNetV3 (timm/torchvision, Apache/BSD), YOLO-NAS, o RT-DETR. Registrar la decisión cuando llegue el momento.

## 2. Entrenamiento en Colab — receta completa

Notebook `vision/train/train_cls.ipynb` (mantenerlo en el repo):

```python
# 1. Entorno
!pip install ultralytics

# 2. Datos: subir el dataset (o montarlo de Drive) con estructura
#    dataset/train/<clase>/*.jpg, dataset/val/<clase>/*.jpg, dataset/test/<clase>/*.jpg
#    generada por scripts/make_splits.py a partir de los manifiestos (doc 05).
from google.colab import drive
drive.mount('/content/drive')

# 3. Entrenar (transfer learning desde pesos ImageNet)
from ultralytics import YOLO
model = YOLO('yolov8n-cls.pt')
results = model.train(
    data='/content/drive/MyDrive/dron/dataset',
    epochs=50, imgsz=384, batch=64, patience=10,
    augment=True,   # además: ver aumentado específico abajo
)

# 4. Evaluar en TEST (nunca reportar métricas de val como finales)
metrics = model.val(split='test')
print(metrics.top1)   # y matriz de confusión en runs/classify/

# 5. Exportar a ONNX (entrada del pipeline de la Jetson)
model.export(format='onnx', imgsz=384, opset=17)
```

## 3. Aumentado de datos específico del dominio

Simular en entrenamiento lo que el dron produce en vuelo (con Albumentations o los flags de Ultralytics):
- **Motion blur** direccional (vibración/movimiento del dron).
- Cambios de **brillo/contraste** fuertes y sombras (sol tropical, nubes).
- **Escala**: la distancia a la planta varía 1.5–3 m.
- Rotaciones leves y volteo horizontal.
- NO usar volteo vertical ni cambios de tono extremos (el color amarillo/marrón de las lesiones es señal diagnóstica).

## 4. Métricas y evaluación honesta

- Reportar por clase: **precisión, recall (sensibilidad), F1** y la matriz de confusión. La exactitud global engaña con clases desbalanceadas.
- La métrica de decisión del proyecto: **F1 ≥ 0.85 por clase en el test set de campo propio** (no en el dataset público).
- Sensibilidad vs. especificidad según el uso: para tamizaje conviene alta sensibilidad (que no se escape una planta enferma) aceptando algunos falsos positivos que el agrónomo descarta al revisar la foto. Ajustar el umbral de confianza con la curva ROC sobre el set de validación y documentarlo.
- Analizar los errores uno a uno (¿el modelo confunde deficiencia de potasio con Sigatoka? ¿falla con contraluz?) — cada patrón de error alimenta la siguiente ronda de recolección (doc 05).
- Registrar cada experimento en `vision/train/experiments.md`: fecha, dataset version, hiperparámetros, métricas, ruta de pesos.

## 5. Ciclo de iteración

```
dataset vN ─► entrenar en Colab ─► evaluar en test de campo ─► análisis de errores
    ▲                                                                │
    └── recolectar/etiquetar lo que falta (negativos difíciles) ◄────┘
```

Cada iteración completa debería tomar ≤1 semana. El modelo mejora por datos, no por hiperparámetros: ante F1 bajo, la primera pregunta es "¿qué imágenes faltan?", no "¿qué learning rate uso?".

## 6. Entrega hacia la Jetson

El artefacto de esta fase es el archivo **ONNX** + un JSON con su metadata:

```json
{
  "model": "sigatoka_cls_v3.onnx",
  "input": [1, 3, 384, 384],
  "classes": ["sana", "sigatoka_temprana", "sigatoka_avanzada", "otra_condicion"],
  "umbral_confianza": 0.65,
  "dataset": "v2_campo_2026-10",
  "f1_test": {"sana": 0.91, "sigatoka_temprana": 0.84, "...": "..."}
}
```

La conversión a TensorRT y el despliegue están en el [doc 07](07-inferencia-jetson.md).
