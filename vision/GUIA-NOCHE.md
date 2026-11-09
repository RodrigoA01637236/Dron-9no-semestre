# Entrenamiento de una noche: el modelo más robusto posible

Un solo comando entrena, en unas 8 horas, el modelo por parches con:

- **más fuentes públicas** de hojas de plátano (lista abajo), sin duplicados ni fugas entre
  train y test;
- una categoría nueva, **"Sin hojas de plátano"** (`sin_hoja`): suelo, cielo, personas,
  objetos y otras plantas o maleza. Los trozos de la foto que el modelo ve así no cuentan
  para el diagnóstico; si ningún trozo es hoja de plátano, la respuesta es "No se ven hojas
  de plátano";
- **una lectura por hoja**: la foto se divide en hojas aproximadas (cada región verde se
  separa por sus bordes y cuellos) y cada hoja recibe su propio veredicto a partir de sus
  trozos. Funciona igual con una foto de cerca o con una foto amplia de varias plantas;
- **más robustez**: clases equilibradas, trozos a 4 escalas, y alteraciones de foto real
  (menos resolución, desenfoque, movimiento, ruido, sombra, neblina, luz cálida/fría, giros);
- **dos tamaños de modelo**: `yolo11s-cls` (más exacto) y `yolo11n-cls` (3 veces más rápido en
  la Jetson). Se calibran los dos, se comparan contra el v1 y se elige el mejor;
- **meta de 90 % de exactitud** revisada en cada prueba (`test`, dron de Colombia, campo).

Detalles de cada paso: [GUIA-PARCHES.md](GUIA-PARCHES.md).

**Sobre el 90 %:** el reporte dice, prueba por prueba, si se cumple. En fotos públicas es
probable; en fotos aéreas y en campo no se sabe hasta medirlo (paso 6). No se presenta un
número que no salga del reporte.

---

## 0. Preparar la laptop (una vez, 10 min) `[PC]`

```powershell
cd C:\ruta\a\Dron-9no-semestre
git pull
& $env:USERPROFILE\venvs\dron-vision\Scripts\Activate.ps1
pip install -U ultralytics
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

Debe imprimir `True NVIDIA GeForce RTX 4060 Laptop GPU`. Si dice `False`, sigue
"Habilitar la GPU NVIDIA" en [GUIA-MODELO.md](GUIA-MODELO.md) antes de seguir: en CPU
la noche no alcanza.

Espacio en disco: ~40 GB libres (fotos + parches). Energía: conectada a la corriente y con
la suspensión desactivada (Configuración → Sistema → Energía → "Nunca").

---

## 1. Descargar los datasets (1–3 h, casi todo esperar) `[PC]`

| Dataset | Enlace | Carpeta en `data\raw\public\` | Clases |
|---|---|---|---|
| El del v1 | ya lo tienes | `banana` | sana, sigatoka, otra |
| Tanzania (Mduma et al.), CC BY 4.0 | https://doi.org/10.5281/zenodo.7670326 | `tanzania` | sana, sigatoka, otra (Fusarium) |
| BananaLSD, CC BY 4.0 | https://doi.org/10.17632/9tb7k297ff.1 | `bananalsd` | sana, sigatoka, otra (solo el conjunto original) |
| Banana Leaf Disease Images (Hailu) | https://doi.org/10.17632/rjykr62kdh.1 | `hailu` | sana, sigatoka, otra |
| BLADE | https://doi.org/10.17632/w7ytz3twjv.2 | `blade` | varias |
| Banana Leaf Disease Dataset of Bangladesh | https://doi.org/10.17632/wzshm7ky49.1 | `bangladesh` | varias |
| Dron con Sigatoka, Colombia (solo prueba) | https://doi.org/10.5281/zenodo.20945958 | `colombia_uav` | sigatoka (cajas) |

(Lista provisional: se está verificando una lista más amplia, con fuentes para "sin hojas de plátano".)

- Cada uno se descomprime en su carpeta de `data\raw\public\`. No importa cuántas
  subcarpetas traiga; el script reconoce las clases por el nombre de la carpeta.
- Anota cada fuente en [data/README.md](../data/README.md) (enlace, licencia, fecha).
- No hace falta tener todas: las que falten se saltan. Las de "sin hojas" son importantes
  para la categoría nueva; sin ellas solo se aprende de suelo y cielo.

---

## 2. Revisar que el script reconozca las carpetas (10 min) `[PC]`

```powershell
python vision\train\preparar_datos.py --out data\prueba_carpetas
```

- Cada fuente debe salir con su número de fotos por clase.
- `AVISO ... carpeta sin clase 'X'`: abre `vision\train\fuentes_v2.json` y en el `"mapa"`
  de esa fuente agrega `"X": "sana"` (o `"sigatoka"`, `"otra_condicion"`, `"sin_hoja"`).
  Una carpeta de fruta, tallos o paisajes va a `"sin_hoja"`.
- Cuando todo salga bien, **borra la prueba**: `Remove-Item -Recurse data\prueba_carpetas`.

---

## 3. Lanzar la noche (~8 h) `[PC]`

```powershell
python vision\train\entrenar_noche.py
```

Lo que hace, en orden (cada paso se salta si ya está hecho):

| Paso | Qué | Tiempo aprox. |
|---|---|---|
| 1 | Junta las fuentes sin duplicados (`data\dataset_v2`) | 10–20 min |
| 2 | Corta parches equilibrados con alteraciones y la clase sin_hoja (`data\parches_v2`) | 30–60 min |
| 3 | Entrena `yolo11s-cls` | 3.5 h |
| 4 | Entrena `yolo11n-cls` | 1.25 h |
| 5 | Calibra y evalúa los dos contra el v1, con fotos completas | 45–60 min |
| 6 | Copia el mejor a `vision\models\sigatoka_cls_v2.*` y anota la corrida en `experiments.md` | — |

Al empezar imprime la hora aproximada en que termina. Todo queda en `runs\noche\`
(log completo: `runs\noche\noche.log`).

- **Si se interrumpe** (apagón, error): corrige lo que diga el log y vuelve a correr el
  mismo comando. Sigue donde se quedó.
- **`CUDA out of memory`**: `python vision\train\entrenar_noche.py --batch-s 32 --batch-n 64`.
- **Menos tiempo:** `--horas-s 2 --horas-n 1`, o solo el principal con `--solo-s`.
- **Empezar de cero** (por ejemplo, después de agregar fuentes): borra `runs\noche`,
  `data\dataset_v2` y `data\parches_v2`.

---

## 4. Leer el resultado (10 min) `[PC]`

Al final el log muestra:

```
Elegido: yolo11s-cls -> vision/models/sigatoka_cls_v2.onnx (exactitud test 93.4%, meta 90%: CUMPLE)
```

Abre `vision\models\sigatoka_cls_v2_evaluacion.md`:

- **Meta de 90 %**: dice para cada prueba si se cumple.
- **`v2_parches_mismas_fotos` contra `v1_foto_completa`**: la comparación justa con el
  v1 (mismas fotos; el v1 no conoce "sin hojas").
- **Recall de sigatoka**: de las fotos con Sigatoka, cuántas encuentra. Es lo que más
  importa para el productor; tiene que ser igual o mejor que el del v1.
- **`test_colombia_uav`**: fotos aéreas reales que nunca vio. Es la mejor pista de cómo le irá
  desde el dron.

Si no cumple: mira la matriz de confusión (qué confunde con qué), revisa 30 parches de esa
clase en `data\parches_v2\train\`, agrega fuentes de esa clase y vuelve a correr la noche.

---

## 5. Subirlo y usarlo `[PC] [Jetson] [Estación]`

```powershell
git add vision\models\sigatoka_cls_v2.* vision\train\experiments.md data\manifests\v2_publico.csv
git commit -m "Modelo v2 por parches (entrenamiento de una noche)"
git push
```

En la Jetson:
```bash
cd ~/Dron-9no-semestre && git pull
bash jetson/zed_control.sh reiniciar
bash jetson/zed_control.sh estado     # debe decir: sigatoka_cls_v2.onnx cargado; clases [..., 'sin_hoja']
```
Toma una foto: el log muestra `[PARCHES] ... · 1/3 hojas con síntomas · 1800 ms`. Si
con el modelo `s` tarda más de ~5 s por foto, usa el `n`, que ya quedó entrenado y
calibrado: copia `runs\noche\calibrado_n\sigatoka_cls_v2.*` a `vision\models\` y súbelo.

En la estación: `git pull`, reinicia `Iniciar-Estacion.bat`, página **Modelo** → la versión
nueva → **Usar este modelo**. En **Cargar**, cada foto muestra las hojas encontradas
("Hoja 1 · Sigatoka") y los trozos con síntomas. "Sin hojas de plátano" aparece también
como opción en **Revisar**.

---

## 6. La prueba de campo (lo que se presenta)

1. Vuela a 1.5–2 m de las hojas (lente de 4.6 mm; ver la tabla de distancia en
   [GUIA-PARCHES.md](GUIA-PARCHES.md)) y toma 100+ fotos, incluidas algunas sin plátano.
2. El agrónomo las etiqueta en **Revisar** (también "Sin hojas de plátano").
3. Cópialas a `data\dataset_v2\test_campo\<clase>\` (`sana`, `sigatoka`,
   `otra_condicion`, `sin_hoja`). Nunca a train: son el examen.
4. Corre solo la evaluación con el modelo elegido (`s` o `n`):
   ```powershell
   python vision\train\calibrar.py --onnx runs\noche\s\weights\best.onnx --salida runs\noche\campo\sigatoka_cls_v2.onnx
   ```
   El reporte (`runs\noche\campo\sigatoka_cls_v2_evaluacion.md`) trae `test_campo`: ese es
   el número que va a la Expo, con cuántas fotos.
