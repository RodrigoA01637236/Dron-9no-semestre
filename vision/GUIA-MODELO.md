# Guía completa — Modelo de identificación de imágenes (Sigatoka)

Ruta de trabajo de la pista de **visión**: desde una PC vacía hasta un modelo corriendo
a bordo de la Jetson. Cada fase termina en un **entregable verificable**; no avances a
la siguiente sin cumplirlo. Complementa (no sustituye) los docs
[05-datos-dataset](../docs/05-datos-dataset.md), [06-entrenamiento](../docs/06-entrenamiento.md)
y [07-inferencia-jetson](../docs/07-inferencia-jetson.md).

**Idea clave del pipeline:** se entrena en Google Colab (GPU gratis), se exporta un solo
archivo portable (`.onnx`) y ese archivo es lo ÚNICO que viaja a la Jetson. En la Jetson
se convierte una vez a TensorRT (`.engine`) y el servicio `infer.py` lo consume. Si
respetas los contratos de cada fase (estructura de carpetas, JSON de metadata,
preprocesado idéntico), "meter el modelo al dron" es copiar un archivo y correr un comando.

```
[PC] datasets públicos + fotos propias
        │  organizar + etiquetar + splits
        ▼
[Colab] entrenar (transfer learning) ─► evaluar en TEST ─► exportar
        │
        ▼
  sigatoka_cls_vN.onnx  +  sigatoka_cls_vN.json   ◄── el "paquete modelo"
        │  (copiar por scp / USB)
        ▼
[Jetson] trtexec → .engine ─► verificar paridad ─► systemd → funciona al encender
```

---

## Fase 0 — Qué necesitas antes de empezar (1 tarde)

### Cuentas (todas gratis)
- **Google** con Drive (~5 GB libres): ahí viven el dataset y los pesos. Colab se usa con la misma cuenta.
- **Kaggle**: para descargar datasets (crear token API en *Settings → API → Create New Token*, descarga `kaggle.json`).
- **GitHub**: ya la tienes; trabaja en tu rama de visión.

### En tu PC (no necesitas GPU)
```bash
# Python 3.10+ y un entorno virtual para el proyecto
python3 -m venv ~/venvs/dron-vision
source ~/venvs/dron-vision/bin/activate        # Windows: ~\venvs\dron-vision\Scripts\activate

pip install kaggle label-studio pillow pandas scikit-learn onnxruntime opencv-python
```
- `kaggle` → descarga de datasets; `label-studio` → etiquetado (fase 2 de campo);
  `onnxruntime` → probar el ONNX en tu PC antes de tocar la Jetson.
- **No instales PyTorch ni ultralytics en tu PC**: el entrenamiento vive en Colab.
  (Instalarlos localmente es opcional, solo si quieres depurar sin internet.)

**Entregable fase 0:** `kaggle datasets list` responde sin error de autenticación.

---

## Fase 1 — Descargar los datasets públicos (1 día)

Objetivo: tener un baseline entrenable **esta semana**, sin esperar fotos propias.

| Fuente | Cómo encontrarla | Qué bajar |
|---|---|---|
| **BananaLSD** (Banana Leaf Spot Diseases) | Buscar "BananaLSD" en `data.mendeley.com` | Las 4 clases: healthy, sigatoka, cordana, pestalotiopsis |
| Datasets "banana leaf disease" | Buscar en `kaggle.com/datasets` ("banana leaf disease", "banana sigatoka") | Los 2–3 mejor documentados y con licencia clara |
| PlantVillage (opcional) | Kaggle | Solo como pre-entrenamiento extra; fondo controlado, NO es campo |

```bash
# Ejemplo de descarga desde Kaggle (sustituye por el identificador real del dataset elegido)
kaggle datasets download -d <usuario>/<nombre-dataset> -p data/raw/public/ --unzip
```

Reglas al descargar (del doc 05, no opcionales):
1. **Anota en `data/README.md`** cada fuente: URL, licencia, fecha de descarga y para qué se usa.
   La mayoría son CC BY (hay que citar); algunas prohíben uso comercial — regístralo.
2. Todo cae en `data/raw/public/<nombre-dataset>/`. **Nada de esto se sube a git**
   (el `.gitignore` ya excluye imágenes); a git solo van manifiestos y scripts.
3. Respaldo inmediato: copia `data/raw/` a tu Drive (será además lo que monte Colab).

**Entregable fase 1:** ≥1,000 imágenes en `data/raw/public/`, con su origen documentado
en `data/README.md`, y copiadas a Drive en `MyDrive/dron/data/raw/`.

---

## Fase 2 — Organizar el dataset y generar los splits (1–2 días)

El modelo se entrena con esta estructura estándar (la espera Ultralytics tal cual):

```
dataset/
├── train/
│   ├── sana/                 *.jpg
│   ├── sigatoka_temprana/    *.jpg
│   ├── sigatoka_avanzada/    *.jpg
│   └── otra_condicion/       *.jpg
├── val/    (mismas 4 carpetas)
└── test/   (mismas 4 carpetas)
```

Pasos:
1. **Mapea las clases del dataset público a las nuestras.** Ej. BananaLSD: `healthy → sana`,
   `sigatoka → sigatoka_temprana` o `sigatoka_avanzada` (si el dataset no distingue estadio,
   usa una sola clase `sigatoka` por ahora y divide cuando haya fotos propias etiquetadas),
   `cordana`/`pestalotiopsis → otra_condicion`.
2. **Genera el manifiesto** `data/manifests/v1_public_baseline.csv` con una fila por imagen
   (`path,origen,fecha,...,etiqueta`) — este CSV **sí** va a git.
3. **Splits por script, nunca a mano:** `scripts/make_splits.py` reparte 70/15/15 con semilla
   fija y escribe `data/manifests/splits/v1_{train,val,test}.csv`, y de ahí materializa la
   estructura `dataset/` (copiando o con enlaces).
   - Con datos públicos el split es por imagen; **cuando entren fotos propias, el split es
     por planta y por visita** (doc 05 §6) — dos fotos de la misma planta jamás quedan una
     en train y otra en test.
4. Sube `dataset/` a Drive: `MyDrive/dron/dataset/`.

**Entregable fase 2:** `dataset/` en Drive con las 3 particiones y conteo por clase anotado
en el manifiesto. Ninguna clase con menos de ~100 imágenes en train (si pasa, junta clases
o consigue más datos antes de entrenar).

---

## Fase 3 — Entrenar en Google Colab (medio día por corrida)

1. Abre un notebook nuevo en `colab.research.google.com` y activa GPU:
   *Entorno de ejecución → Cambiar tipo → GPU (T4)*.
2. Guarda el notebook en el repo como `vision/train/train_cls.ipynb` (Archivo → Guardar copia en GitHub, o descárgalo y súbelo).
3. Celdas del notebook:

```python
# ── 1. Entorno ──────────────────────────────────────────────
!pip install ultralytics

# ── 2. Datos desde Drive ────────────────────────────────────
from google.colab import drive
drive.mount('/content/drive')
DATA = '/content/drive/MyDrive/dron/dataset'

# ── 3. Entrenar (transfer learning desde ImageNet) ──────────
from ultralytics import YOLO
model = YOLO('yolov8n-cls.pt')          # descarga los pesos base automáticamente
results = model.train(
    data=DATA,
    epochs=50, imgsz=384, batch=64, patience=10,
    augment=True,
    # aumentado del dominio dron (doc 06 §3):
    degrees=10, scale=0.5, fliplr=0.5, flipud=0.0,  # sin volteo vertical
    hsv_h=0.005, hsv_s=0.3, hsv_v=0.4,              # tono casi fijo: el color es diagnóstico
)

# ── 4. Evaluar SIEMPRE en test (nunca reportar val como final) ──
metrics = model.val(split='test')
print('top1:', metrics.top1)            # matriz de confusión en runs/classify/*/

# ── 5. Exportar el paquete modelo ───────────────────────────
model.export(format='onnx', imgsz=384, opset=17)
# El .onnx queda junto a los pesos en runs/classify/*/weights/
```

4. Descarga de `runs/classify/<run>/`: `weights/best.onnx`, la matriz de confusión y
   `results.csv`. Guarda también `best.pt` en Drive (para reanudar/afinar después).

Reglas:
- **Cada corrida se registra en [`vision/train/experiments.md`](train/experiments.md)**
  (fecha, dataset, hiperparámetros, métricas, ruta de pesos). Sin registro no hay experimento.
- Si el F1 sale bajo, la primera pregunta es *"¿qué imágenes faltan?"*, no *"¿qué
  learning rate uso?"*. El modelo mejora por datos.

**Entregable fase 3:** `best.onnx` descargado + fila nueva en `experiments.md` + matriz de
confusión revisada clase por clase.

---

## Fase 4 — Evaluación honesta (medio día)

Antes de declarar un modelo "listo para el dron":

1. **Métricas por clase** (precisión, recall, F1) desde la matriz de confusión — la exactitud
   global engaña con clases desbalanceadas.
2. **Criterio del proyecto:** F1 ≥ 0.85 por clase. Con datos públicos es solo referencia;
   la métrica que cuenta se mide sobre el **test de fotos propias de campo** cuando exista.
3. **Análisis de errores uno a uno:** abre las imágenes mal clasificadas. ¿Confunde
   deficiencia nutricional con Sigatoka? ¿Falla a contraluz o con blur? Cada patrón de error
   define qué fotos recolectar en la siguiente visita de campo.
4. **Elige el umbral de confianza** con el set de validación (curva ROC / barrido de umbral):
   para tamizaje conviene alta sensibilidad — que no se escape una planta enferma — aceptando
   falsos positivos que el agrónomo descarta viendo la foto. Documenta el umbral elegido:
   va dentro del JSON de metadata.

**Entregable fase 4:** tabla de métricas por clase + umbral decidido + lista de patrones de
error, todo en `experiments.md`.

---

## Fase 5 — Empaquetar el modelo (30 min)

El contrato con la Jetson son **dos archivos con el mismo nombre base**:

```
sigatoka_cls_v1.onnx        # el modelo
sigatoka_cls_v1.json        # su metadata (SÍ va a git, en vision/models/)
```

```json
{
  "model": "sigatoka_cls_v1.onnx",
  "input": [1, 3, 384, 384],
  "preprocesado": "resize 384x384, BGR->RGB, float32 /255, CHW",
  "classes": ["otra_condicion", "sana", "sigatoka_avanzada", "sigatoka_temprana"],
  "umbral_confianza": 0.65,
  "dataset": "v1_public_baseline",
  "f1_test": {"sana": 0.00, "sigatoka_temprana": 0.00, "sigatoka_avanzada": 0.00, "otra_condicion": 0.00}
}
```

⚠️ **`classes` debe ir en el orden exacto de salida del modelo.** Ultralytics ordena las
clases alfabéticamente por nombre de carpeta — verifica el orden en `model.names` antes de
escribir el JSON. Un orden equivocado = diagnósticos cruzados sin ningún error visible.

Prueba de humo en tu PC (sin Jetson):

```python
import onnxruntime as ort, cv2, numpy as np
sess = ort.InferenceSession('sigatoka_cls_v1.onnx')
img = cv2.resize(cv2.imread('foto_prueba.jpg'), (384, 384))[:, :, ::-1]
x = (img.astype(np.float32) / 255.0).transpose(2, 0, 1)[None]
probs = sess.run(None, {sess.get_inputs()[0].name: x})[0]
print(probs)   # ¿la clase más alta coincide con lo que ves en la foto?
```

**Entregable fase 5:** `.onnx` + `.json` verificados con 5–10 fotos conocidas en PC.
El `.json` se commitea en `vision/models/`; el `.onnx` se sube a Drive (no a git).

---

## Fase 6 — Meter el modelo a la Jetson (1 día la primera vez, 10 min las siguientes)

```bash
# 1. Copiar el paquete a la Jetson (o por USB)
scp sigatoka_cls_v1.onnx sigatoka_cls_v1.json jetson@<ip>:~/proyecto-dron/models/

# 2. En la Jetson: construir el engine TensorRT (UNA vez por modelo y por JetPack)
/usr/src/tensorrt/bin/trtexec \
  --onnx=models/sigatoka_cls_v1.onnx \
  --saveEngine=models/sigatoka_cls_v1_fp16.engine \
  --fp16 \
  --shapes=images:1x3x384x384
# trtexec reporta la latencia media al final → tu primera medición de FPS
```

3. **Verificar paridad FP16:** corre 20–50 fotos del test por el ONNX en PC y por el engine
   en la Jetson; si las predicciones divergen >1 %, reconstruye sin `--fp16`.
4. El servicio `vision/infer.py` (doc 07 §3) toma la ruta del engine y el `.json` de metadata.
   **El preprocesado de `infer.py` debe ser byte a byte el de la fase 5** — es la causa #1
   de "funciona en Colab pero no en la Jetson".
5. Medir con `sudo tegrastats`: FPS, temperatura, potencia. Elegir el menor `nvpmodel`
   que sostenga ≥10 FPS y anotarlo en `docs/bitacora/`.

**Entregable fase 6:** engine construido, paridad verificada, ≥10 FPS medidos y anotados.

---

## Fase 7 — Que funcione solo al encender (systemd)

Sigue el doc 07 §5 tal cual: unidad `dron-infer.service`, `systemctl enable --now`, y la
prueba de fuego **dos veces desde arranque en frío**: enchufar la Jetson → sin tocar nada,
a los ~60 s captura + inferencia + resultados publicándose.

Actualizar el modelo en el dron a partir de aquí es solo:
`scp` del nuevo `.onnx` + `.json` → `trtexec` → `sudo systemctl restart dron-infer`.

---

## Checklist de entrega del "paquete modelo" (imprimible)

- [ ] `experiments.md` tiene la corrida con dataset, hiperparámetros y métricas
- [ ] F1 por clase evaluado en TEST (no en val) y matriz de confusión revisada
- [ ] Umbral de confianza elegido y justificado
- [ ] `classes` del JSON verificado contra `model.names` (orden exacto)
- [ ] ONNX probado en PC con fotos conocidas (fase 5)
- [ ] Engine FP16 construido en la Jetson y paridad verificada
- [ ] ≥10 FPS sostenidos medidos con `tegrastats`, `nvpmodel` anotado
- [ ] Arranque en frío verificado 2 veces
- [ ] `.json` commiteado en `vision/models/`; `.onnx` y `.pt` respaldados en Drive

## Errores comunes (y su vacuna)

| Síntoma | Causa típica | Vacuna |
|---|---|---|
| Métricas de Colab altas, en campo malas | Dataset público ≠ fotos aéreas; fuga train/test | Test = visita/finca nunca vista; split por planta |
| "Funciona en Colab, no en la Jetson" | Preprocesado distinto (resize, RGB/BGR, normalización) | El string `preprocesado` del JSON es el contrato; copiarlo, no reescribirlo |
| Diagnósticos cruzados (sana ↔ enferma) | Orden de `classes` no coincide con la salida | Verificar `model.names` en la fase 5 |
| Todo lo "feo" lo marca enfermo | Faltan negativos difíciles | Recolectar deficiencias K/Mg, daño sol/mecánico (doc 05 §4) |
| Engine no carga tras actualizar JetPack | El `.engine` es específico de la versión de TensorRT | Reconstruir con `trtexec`; el `.onnx` es la fuente de verdad |
