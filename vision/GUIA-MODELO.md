# Guía completa — Modelo de identificación de imágenes (Sigatoka)

Ruta de trabajo de la pista de **visión**: desde una PC vacía hasta un modelo corriendo
a bordo de la Jetson. **El entrenamiento se hace directamente en tu computadora**;
Google Drive se usa solo como respaldo del dataset y de los pesos. Cada fase termina en
un **entregable verificable**; no avances a la siguiente sin cumplirlo. Complementa (no
sustituye) los docs [05-datos-dataset](../docs/05-datos-dataset.md),
[06-entrenamiento](../docs/06-entrenamiento.md) y
[07-inferencia-jetson](../docs/07-inferencia-jetson.md).

**Idea clave del pipeline:** se entrena en tu PC, se exporta un solo archivo portable
(`.onnx`) y ese archivo es lo ÚNICO que viaja a la Jetson. En la Jetson se convierte una
vez a TensorRT (`.engine`) y el servicio `infer.py` lo consume. Si respetas los contratos
de cada fase (estructura de carpetas, JSON de metadata, preprocesado idéntico), "meter el
modelo al dron" es copiar un archivo y correr un comando.

```
[PC] datasets públicos + fotos propias
        │  organizar + etiquetar + splits
        ▼
[PC] entrenar (transfer learning) ─► evaluar en TEST ─► exportar      (respaldo → Drive)
        │
        ▼
  sigatoka_cls_vN.onnx  +  sigatoka_cls_vN.json   ◄── el "paquete modelo"
        │  (copiar por scp / USB)
        ▼
[Jetson] trtexec → .engine ─► verificar paridad ─► systemd → funciona al encender
```

---

## Fase 0 — Preparar tu computadora (1 tarde)

### Cuentas (todas gratis)
- **Google** con Drive (~5 GB libres): respaldo del dataset y de los pesos entrenados.
- **Kaggle**: para descargar datasets (crear token API en *Settings → API → Create New
  Token*, descarga `kaggle.json` y colócalo en `C:\Users\<tu-usuario>\.kaggle\kaggle.json`
  — en Linux/Mac: `~/.kaggle/kaggle.json`).
- **GitHub**: ya la tienes; trabaja en tu rama de visión.

### Instalación en Windows (PowerShell) — probada paso a paso

⚠️ Usar **Python 3.13**, no 3.14: varios paquetes (Label Studio en particular) aún no
tienen versión precompilada para 3.14 e intentan compilar desde código, lo que falla
sin un compilador de C instalado.

```powershell
# 1. Instalar Python 3.13 con el gestor de python.org
#    (si "py" no existe: instala Python desde python.org marcando "Add python.exe to PATH",
#     cierra la terminal y ábrela de nuevo)
py install 3.13

# 2. Crear el entorno virtual con 3.13
py -V:3.13 -m venv $env:USERPROFILE\venvs\dron-vision

# 3. Activarlo — la línea debe empezar con "(dron-vision)".
#    OJO: esto se repite en CADA terminal nueva antes de trabajar.
& $env:USERPROFILE\venvs\dron-vision\Scripts\Activate.ps1
python --version    # debe decir Python 3.13.x

# 4. Herramientas de datos y verificación
pip install kaggle label-studio pillow pandas scikit-learn onnxruntime opencv-python

# 5. Entrenamiento (instala PyTorch automáticamente; ~2 GB, tarda varios minutos)
pip install ultralytics
```

Notas de instalación:
- Si PowerShell rechaza el `Activate.ps1` por "execution policy": corre una vez
  `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser` y reintenta.
- En Linux/Mac los pasos 2–5 equivalen a `python3 -m venv ~/venvs/dron-vision` y
  `source ~/venvs/dron-vision/bin/activate`.

### Habilitar la GPU NVIDIA (si la tienes)

`pip install ultralytics` instala la versión de PyTorch **solo-CPU** en Windows. Si
`nvidia-smi` muestra tu GPU pero `python -c "import torch; print(torch.cuda.is_available())"`
imprime `False`, reinstala PyTorch con CUDA (con el venv activo):

```powershell
pip uninstall -y torch torchvision
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128
python -c "import torch; print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0))"
```

- La descarga es de ~2.8 GB y el paso de instalación puede quedarse callado 5–15 min
  (el antivirus escanea miles de archivos): no está trabado, déjalo terminar.
- Si `cu128` da "No matching distribution": copia el comando actual del selector de
  [pytorch.org/get-started](https://pytorch.org/get-started/locally/) (Windows + Pip + CUDA).
- La advertencia de conflicto con `setuptools` que imprime al final (por Label Studio)
  es inofensiva; ignórala.
- Con GPU, una corrida tarda 10–30 min. **Sin GPU NVIDIA** todo funciona igual pero en
  CPU (horas por corrida): usa `--batch 16 --workers 2`, deja las corridas de noche, y
  si se vuelve insoportable, la alternativa gratis es Kaggle Notebooks (GPU ~30 h/semana).

**Entregable fase 0:** `kaggle datasets list` responde sin error de autenticación,
`python -c "from ultralytics import YOLO; print('ok')"` imprime `ok`, y (con GPU)
`torch.cuda.is_available()` imprime `True`.

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
3. **Respaldo inmediato a Drive:** sube una copia de `data/raw/` a `MyDrive/dron/data/raw/`
   (o deja que Drive for Desktop sincronice la carpeta). Una fuente que desaparece de
   internet no puede tumbar tu proyecto.

**Entregable fase 1:** ≥1,000 imágenes en `data/raw/public/`, con su origen documentado
en `data/README.md`, y respaldadas en Drive.

---

## Fase 2 — Organizar el dataset y generar los splits (1–2 días)

El modelo se entrena con esta estructura estándar (la espera Ultralytics tal cual),
en tu disco local, p. ej. `data/dataset/`:

```
data/dataset/
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
   estructura `data/dataset/` (copiando o con enlaces).
   - Con datos públicos el split es por imagen; **cuando entren fotos propias, el split es
     por planta y por visita** (doc 05 §6) — dos fotos de la misma planta jamás quedan una
     en train y otra en test.
4. Respalda `data/dataset/` a Drive.

**Entregable fase 2:** `data/dataset/` con las 3 particiones y conteo por clase anotado
en el manifiesto. Ninguna clase con menos de ~100 imágenes en train (si pasa, junta clases
o consigue más datos antes de entrenar).

---

## Fase 3 — Entrenar en tu PC (10–30 min con GPU; horas en CPU)

El script ya está en el repo: [`vision/train/train_cls.py`](train/train_cls.py).
Desde la raíz del repo, con el venv activo:

```bash
python vision/train/train_cls.py --data data/dataset --epochs 50 --imgsz 384 --batch 32
# sin GPU: --batch 16 --workers 2 (y deja la corrida de noche)
```

El script hace, en orden (léelo, son ~60 líneas):
1. **Entrena** `yolov8n-cls` por transfer learning desde pesos ImageNet, con el aumentado
   del dominio dron (doc 06 §3): rotaciones leves, escala, volteo horizontal, brillo —
   y **sin** volteo vertical ni cambios fuertes de tono (el color de las lesiones es
   señal diagnóstica).
2. **Evalúa en TEST** (nunca reportes métricas de val como finales) e imprime el top-1;
   la matriz de confusión queda en `runs/classify/<run>/`.
3. **Exporta a ONNX** (`opset 17`, 384 px) — la entrada del pipeline de la Jetson.
4. Imprime `model.names` — el **orden exacto de clases** que necesitas en la fase 5.

Al terminar cada corrida:
- Copia `runs/classify/<run>/weights/best.pt` y `best.onnx` a Drive
  (`MyDrive/dron/pesos/<fecha>/`). `runs/` no va a git (ya está ignorado).
- **Registra la corrida en [`vision/train/experiments.md`](train/experiments.md)**
  (fecha, dataset, hiperparámetros, métricas, ruta de pesos). Sin registro no hay experimento.

Si el F1 sale bajo, la primera pregunta es *"¿qué imágenes faltan?"*, no *"¿qué
learning rate uso?"*. El modelo mejora por datos.

**Entregable fase 3:** `best.onnx` generado + fila nueva en `experiments.md` + matriz de
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
clases alfabéticamente por nombre de carpeta — usa el `model.names` que imprime
`train_cls.py` al final. Un orden equivocado = diagnósticos cruzados sin ningún error visible.

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
El `.json` se commitea en `vision/models/`; el `.onnx` se respalda en Drive (no a git).

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
   de "funciona en la PC pero no en la Jetson".
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
| Métricas de PC altas, en campo malas | Dataset público ≠ fotos aéreas; fuga train/test | Test = visita/finca nunca vista; split por planta |
| "Funciona en la PC, no en la Jetson" | Preprocesado distinto (resize, RGB/BGR, normalización) | El string `preprocesado` del JSON es el contrato; copiarlo, no reescribirlo |
| Diagnósticos cruzados (sana ↔ enferma) | Orden de `classes` no coincide con la salida | Verificar `model.names` en la fase 5 |
| Todo lo "feo" lo marca enfermo | Faltan negativos difíciles | Recolectar deficiencias K/Mg, daño sol/mecánico (doc 05 §4) |
| Entrenamiento eterno / PC se congela | CPU sin GPU, batch grande | `--batch 16 --workers 2`, corridas de noche; o Kaggle Notebooks (GPU gratis) |
| `torch.cuda.is_available()` = False con GPU NVIDIA | PyTorch instalado sin CUDA | Reinstalar desde el selector de pytorch.org |
| Engine no carga tras actualizar JetPack | El `.engine` es específico de la versión de TensorRT | Reconstruir con `trtexec`; el `.onnx` es la fuente de verdad |
