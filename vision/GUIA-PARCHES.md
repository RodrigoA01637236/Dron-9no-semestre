# Guía: modelo por parches (v2), de datos públicos al dron

Esta guía lleva de los datasets públicos a un modelo `sigatoka_cls_v2` que revisa cada foto
por trozos de hoja, y después a la Jetson y a la estación. Sigue a
[GUIA-MODELO.md](GUIA-MODELO.md), que armó el v1; usa el mismo venv `dron-vision`.

**Dónde se corre cada paso:** `[PC]` laptop con la RTX 4060 (PowerShell, venv activo),
`[Jetson]` terminal de la Jetson, `[Estación]` laptop con la estación de tierra.

| Paso | Dónde | Tiempo aprox. |
|---|---|---|
| 1. Descargar datasets | PC | 1–2 h (descargas) |
| 2. Juntar sin duplicados | PC | 5–15 min |
| 3. Cortar parches | PC | 20–40 min |
| 4. Entrenar | PC (GPU) | 1–2 h por corrida |
| 5. Calibrar y comparar contra v1 | PC | 30–60 min |
| 6. Subir al repo | PC | 2 min |
| 7. Instalar en el dron | Jetson | 5 min |
| 8. Activar en la estación | Estación | 5 min + reprocesar |
| 9. Prueba de campo | Campo + estación | 1 visita |

---

## Por qué cambia el modelo

El v1 reduce la foto entera a 384x384. Para una foto de la ZED X Mini (1920x1200) eso
significa ver unas 5 veces menos detalle, y una estría de Sigatoka de 1–2 mm desaparece.

El v2 hace lo que hace un agrónomo: mira la hoja por partes.

1. **Filtro de hoja** ([vision/parches.py](parches.py)): recorre la foto en cuadros de 384 px
   **a resolución nativa**, con 20 % de solape (como SAHI, Akyon et al., ICIP 2022,
   doi:10.1109/ICIP46576.2022.9897990). Descarta los cuadros con poca hoja usando un índice
   de verdor (ExG) más un rango de tono amarillo. Las manchas necróticas encerradas por
   hoja se rellenan para no perderlas.
2. **Clasificador por parche**: el mismo tipo de red (YOLO-cls), pero entrenada con
   parches. Clasificar por región en lugar de por hoja completa subió 12 % en promedio la
   exactitud en Barbedo (Biosystems Engineering 180:96–107, 2019,
   doi:10.1016/j.biosystemseng.2019.02.002).
3. **Veredicto de la foto**: si al menos `min_parches` cuadros muestran con seguridad la
   misma enfermedad, la foto tiene esa enfermedad. Si no, la foto es sana solo cuando la
   hoja en promedio se ve sana. Si no alcanza la seguridad mínima, va a revisión humana.
4. **Calibración**: con temperatura (Guo et al., ICML 2017), "80 % seguro" significa
   acertar alrededor del 80 % de las veces. Así el umbral se elige con datos.

En la Jetson, el **video en vivo sigue con la foto completa**, porque es rápido. **Cada
foto** se analiza además por parches en segundo plano: tarda unos 1–3 s y el resultado
queda en el EXIF y en la página del dron. La estación usa el modo por parches para todas
las fotos y dibuja en la foto los cuadros con síntomas.

---

## Antes de volar: distancia a la hoja

La distancia a la que se toma la foto decide qué se puede ver. Para la ZED X Mini
(sensor AR0234, pixel de 3 µm):

**GSD (mm por pixel) = distancia (m) × 3 / focal (mm)**

| Distancia a la hoja | Lente 2.2 mm: mm/px | Lente 2.2 mm: un cuadro de 384 px cubre | Lente 4.6 mm: mm/px | Lente 4.6 mm: un cuadro de 384 px cubre |
|---|---|---|---|---|
| 0.75 m | 1.0 | 39 cm | 0.49 | 19 cm |
| 1.0 m | 1.4 | 52 cm | 0.65 | 25 cm |
| 1.5 m | 2.0 | 79 cm | 0.98 | 38 cm |
| 2.0 m | 2.7 | 105 cm | 1.3 | 50 cm |
| 3.0 m | 4.1 | 157 cm | 2.0 | 75 cm |

- **Estrías tempranas (estadios 1–2):** miden ~1–2 mm de ancho. Para verlas se necesitan
  3–5 px a lo ancho, o sea ≤0.5 mm/px. Con el lente de 4.6 mm eso es ≤0.75 m; con el de
  2.2 mm, ≤0.37 m, que no es práctico en vuelo. Además empiezan en el envés (ProMusa). Esto
  sigue siendo trabajo de foto de cerca con celular o del agrónomo.
- **Manchas y necrosis (estadios 3–6):** son de varios mm a cm. Se ven bien a 1–2 mm/px.
  **Recomendación:** lente de 4.6 mm a 1.5–2 m de la hoja. Con el de 2.2 mm, a 1 m o menos.
- **Movimiento:** el desenfoque en px es velocidad × exposición / GSD. A 1 m/s, con
  1/1000 s y 1 mm/px, es 1 px. Para las fotos, mejor quieto o a ≤1 m/s.
- Los parches de entrenamiento (paso 3) imitan este rango: cuadros de 30–100 % de una foto
  de cerca, degradados a 1.5–4 veces menos resolución.

**Saber qué lente tiene la cámara** `[Jetson]`:
```bash
grep -m2 -E "^fx" /usr/local/zed/settings/SN55465567.conf
# fx ≈ 730 px  -> lente 2.2 mm (110° x 80°)
# fx ≈ 1500 px -> lente 4.6 mm (73° x 45°)
```

---

## Paso 1 — Descargar los datasets públicos `[PC]`

Cada uno va en su carpeta dentro de `data\raw\public\`. Esa carpeta no se sube a git. Las
rutas están en [train/fuentes_v2.json](train/fuentes_v2.json); si usas otra, cámbiala ahí.

| Fuente | Dónde | Carpeta | Para qué |
|---|---|---|---|
| El dataset del v1 | ya lo tienes | `data\raw\public\banana` | Base; conserva el reparto del v1 |
| Tanzania (Mduma et al.), CC BY 4.0 | doi.org/10.5281/zenodo.7670326 | `data\raw\public\tanzania` | Sigatoka negra, sana, Fusarium |
| BananaLSD, CC BY 4.0 | doi.org/10.17632/9tb7k297ff.1 | `data\raw\public\bananalsd` | Solo el conjunto **original** |
| Banana Leaf Disease Images (Hailu) | doi.org/10.17632/rjykr62kdh.1 | `data\raw\public\hailu` | Más variedad de campo |
| BLADE | doi.org/10.17632/w7ytz3twjv.2 | `data\raw\public\blade` | Opcional |
| Banana Leaf Disease Dataset of Bangladesh | doi.org/10.17632/wzshm7ky49.1 | `data\raw\public\bangladesh` | Opcional |
| Sigatoka desde dron, Colombia (cajas YOLO), CC BY 4.0 | doi.org/10.5281/zenodo.20945958 | `data\raw\public\colombia_uav` | **Solo prueba**: fotos aéreas reales |

- Descarga el zip desde la página (Zenodo y Mendeley se descargan con el navegador) y
  descomprímelo en su carpeta. No importa cuántas subcarpetas traiga.
- Anota cada fuente en [data/README.md](../data/README.md): URL, licencia, fecha.
- No hace falta tener todas. Las que falten se saltan con un aviso.

---

## Paso 2 — Juntar todo sin duplicados ni fugas `[PC]`

```powershell
cd C:\ruta\a\Dron-9no-semestre
git pull
& $env:USERPROFILE\venvs\dron-vision\Scripts\Activate.ps1
python vision\train\preparar_datos.py
```

Qué hace ([train/preparar_datos.py](train/preparar_datos.py)):
- Pone la clase según el nombre de la carpeta (`healthy` → sana, `sigatoka` → sigatoka,
  `cordana`/`fusarium`/... → otra_condicion). Salta las carpetas de copias aumentadas.
- Encuentra copias exactas y casi exactas, también giradas o en espejo, y pone cada grupo
  completo en el mismo split. Así no se cuela en test una foto que ya está en train.
- **Conserva el reparto del v1**: lo que fue test del v1 sigue en test. Si no, la
  comparación del paso 5 favorecería al v1, que habría entrenado con fotos de test.
- Las fuentes "externas" (Colombia, campo) van completas a `test_<nombre>`.

**Revisa la salida:**
- `AVISO ... carpeta sin clase`: agrega esa carpeta al `mapa` de la fuente en
  `fuentes_v2.json` (o déjala fuera si no es hoja de plátano), borra `data\dataset_v2` y corre de nuevo.
- `grupos con etiquetas contradictorias`: abre `data\manifests\v2_conflictos.csv`. Son la
  misma foto con dos etiquetas. Quedan fuera del dataset; vale la pena verlas.
- La tabla final debe tener cientos de fotos por clase en train.

Sale `data\dataset_v2\` (enlaces, casi no ocupa espacio) y `data\manifests\v2_publico.csv`.
El CSV sí se sube a git.

---

## Paso 3 — Cortar los parches `[PC]`

```powershell
python vision\train\hacer_parches.py --maestro vision\models\sigatoka_cls_v1.onnx
```

Qué hace ([train/hacer_parches.py](train/hacer_parches.py)):
- Por foto saca hasta 6 cuadros a cuatro escalas (100, 60, 40 y 30 % del lado corto), solo
  donde hay hoja, y los guarda a 384x384.
- 40 % de los parches se degradan (menos resolución, desenfoque, JPEG) para parecerse a la
  foto del dron.
- **Limpieza de etiquetas con el v1 como maestro:** un trozo de una hoja con Sigatoka puede
  ser un trozo sano. Si el maestro no ve la enfermedad en ese trozo (P < 0.35), se
  descarta. Y si un trozo de una foto "sana" tiene manchas claras (P enfermedad ≥ 0.80),
  también se descarta. La corrida 1 de [experiments.md](train/experiments.md) encontró
  justo eso: "sanas" con manchas.

**Revisa:**
- Abre 20–30 parches de `data\parches_v2\train\sigatoka\`. Casi todos deben mostrar lesiones.
- Si sale `AVISO: en train hay pocos parches de sigatoka`, el maestro descartó demasiados.
  Borra `data\parches_v2` y corre con `--min-maestro 0.2`.
- `data\parches_v2\parches.csv` dice de qué foto salió cada parche y por qué se descartó.

---

## Paso 4 — Entrenar `[PC]`

```powershell
python vision\train\train_cls.py --data data\parches_v2 --model yolo11n-cls.pt --epochs 60 --erasing 0.1 --name parches_v2
```

- `yolo11n-cls.pt` es la versión más nueva del mismo tamaño que el v1. Para comparar, una
  segunda corrida con `--model yolov8n-cls.pt --name parches_v2_y8`.
- `--erasing 0.1`: el borrado aleatorio (0.4 por defecto) podría tapar la única lesión del
  parche.
- Exporta el ONNX con lote libre, para clasificar todos los parches de una foto de una vez.
- El "top1 (test)" que imprime es **por parche y con etiquetas débiles**: sirve de
  referencia, pero la comparación que cuenta es la del paso 5.
- Anota la corrida en [train/experiments.md](train/experiments.md), aunque salga mal.

Sale `runs\classify\parches_v2\weights\best.onnx` (+ `best.json`).

### Atajo: entrenar desde la estación

Los pasos 3, 4 y 5 también se pueden correr desde la página **Modelo** de la estación, en la
misma laptop: en *Qué modelo* elige **Foto completa (como el v1)**, **Por parches de hoja
(v2)** o **Los dos, uno después del otro**, y presiona *Reentrenar ahora*.

- Usa como fotos base `data\dataset_v2` si ya hiciste el paso 2 (si no, `data\dataset`), más
  las fotos que el agrónomo revisó en la estación. El ~20 % de esas fotos revisadas queda
  como examen de campo y nunca se entrena.
- Con "Los dos" entrena primero el de foto completa y luego el de parches. Cada uno queda
  como una versión nueva, sin activarse, con su resultado en el examen de campo.
- Todo queda en `data\estacion\entrenamientos\<fecha>\` (el log, los parches y el reporte
  `parches_calibrado\modelo_parches_evaluacion.md`).
- La calibración en la estación usa hasta 300 fotos por clase para no tardar de más. Para
  el reporte completo de la Expo, corre `calibrar.py` a mano (paso 5).
- Para subir un modelo entrenado así al dron, copia `modelo_parches.onnx` y su `.json` a
  `vision\models\sigatoka_cls_v2.onnx` / `.json` y sigue con el paso 6.

---

## Paso 5 — Calibrar y comparar contra v1 `[PC]`

```powershell
python vision\train\calibrar.py --onnx runs\classify\parches_v2\weights\best.onnx
# prueba rápida antes (200 fotos por clase): agrega --limite 200
```

Qué hace ([train/calibrar.py](train/calibrar.py)):
1. Ajusta la temperatura con los parches de val e imprime el error de calibración (ECE)
   antes y después.
2. En las **fotos** de val prueba umbrales de 0.50 a 0.95 y de 1 a 3 parches mínimos.
   Elige la combinación que diagnostica más fotos con ≥95 % de aciertos en las que sí
   diagnostica (`--objetivo`). Las demás van a revisión humana.
3. En las **fotos** de test compara v1 (foto completa), v2 (foto completa) y v2 (por
   parches), por clase y por fuente. Hace lo mismo en `test_colombia_uav` y cuenta cuántas
   lesiones marcadas por los autores caen en un parche que el modelo marcó como Sigatoka.
4. Escribe `vision\models\sigatoka_cls_v2.onnx`, su `.json` y
   `sigatoka_cls_v2_evaluacion.md` con todas las tablas.

**Regla para decidir si v2 se usa:**
- En `test`, el **recall de sigatoka** y el **F1 macro** de `v2_parches` son iguales o
  mejores que los de `v1_foto_completa`.
- En `test_colombia_uav` (aéreo), `v2_parches` encuentra más que `v1_foto_completa`.

Si no se cumple, no lo subas: revisa los parches (paso 3), prueba la otra corrida del paso 4
o ajusta `--min-maestro`. Anota el resultado en `experiments.md` de todos modos.

---

## Paso 6 — Subir al repo `[PC]`

```powershell
git add vision\models\sigatoka_cls_v2.onnx vision\models\sigatoka_cls_v2.json vision\models\sigatoka_cls_v2_evaluacion.md data\manifests\v2_publico.csv vision\train\experiments.md
git commit -m "Modelo v2 por parches de hoja"
git push
```

`.gitignore` ya deja pasar `sigatoka_cls_v2.onnx`; los datasets y parches no se suben.
Respalda `runs\classify\parches_v2\` en Drive.

---

## Paso 7 — Instalar en el dron `[Jetson]`

```bash
cd ~/Dron-9no-semestre
git pull
bash jetson/zed_control.sh reiniciar
bash jetson/zed_control.sh estado
```

En las últimas líneas del log debe salir:
```
[MODELO] sigatoka_cls_v2.onnx cargado; clases ['otra_condicion', 'sana', 'sigatoka']; fotos por parches: sí
```
El programa usa el modelo más nuevo que encuentre (`v2`, luego `v1`).

**Verifica con una foto:** desde la página del dron (`http://<ip-jetson>:8080`) o la
estación, toma una foto. En 1–3 s el log muestra:
```
[PARCHES] 26-11-20_10-31-02-GPS.jpg: sigatoka 87% · 3/18 trozos con síntomas · 1450 ms
```
- La página del dron muestra "Última foto: ... trozos de hoja, ... con síntomas".
- El EXIF de la foto suma `AnalisisParches=...; ParchesHoja=...; FraccionParches=...`.
- Los cuadros quedan en `~/Prueba#1/parches/<foto>.json`.
- **Anota los ms** que imprime: es el dato de rendimiento real en la Jetson.

**Volver al v1 para comparar en campo:**
```bash
SIGATOKA_MODELO=sigatoka_cls_v1.onnx bash jetson/zed_control.sh reiniciar
bash jetson/zed_control.sh reiniciar      # sin la variable: regresa al v2
```
Si el análisis por parches estorba (Jetson muy cargada), en `jetson/zed_right.py` pon
`ANALIZAR_FOTOS = False`. La estación seguirá revisando por parches al importar.

---

## Paso 8 — Activar en la estación `[Estación]`

```powershell
git pull
# cierra la estación (Ctrl+C) y ábrela de nuevo con Iniciar-Estacion.bat
```

Al arrancar, la estación registra `sigatoka_cls_v2` como una versión nueva, **sin
activarla**. En la página **Modelo** aparece con su prueba pública. Al activarlo, la
estación vuelve a diagnosticar todas las fotos (por parches tarda más: ~0.3–0.5 s por foto
en la laptop). Después, en **Cargar**, cada foto muestra:
- el veredicto,
- las barras por clase: con el v2 cada barra mide si eso aparece en algún trozo, así que
  no suman 100 %,
- los cuadros con síntomas dibujados sobre la foto: línea continua si el modelo está seguro,
  punteada si no,
- cuántos trozos de hoja revisó.

---

## Paso 9 — La prueba que cuenta: campo `[Campo + Estación]`

Las métricas de los pasos 4–5 son con fotos públicas de cerca, **no** con nuestro dron.
Antes de decir en la Expo "el modelo acierta X %":

1. Vuela con el protocolo de altura de arriba y toma 100+ fotos en una parcela con
   Sigatoka.
2. El agrónomo las etiqueta en **Revisar**.
3. Copia las etiquetadas a `data\raw\campo_validado\sana\`, `...\sigatoka\` y
   `...\otra_condicion\`.
4. Repite los pasos 2 y 5. Aparece `test_campo` en el reporte: **ese** es el número que se
   presenta, junto con cuántas fotos son.

La estación ya separa ~20 % de las fotos etiquetadas como examen de campo (holdout), y
"Modelo → Entrenar" las usa para comparar versiones.

---

## Siguiente fase (no incluida aquí)

- **Tamaño de cuadro según la distancia:** con el `fx` del lente y la profundidad de la ZED
  (`depth_mode` hoy es `NONE`), calcular el GSD de cada foto y ajustar `lado_px` para que
  un cuadro cubra siempre ~40 cm de hoja.
- **Segmentar hojas** en lugar de usar el índice de verdor: YOLOv8n-seg entrenado con
  máscaras hechas con SAM 2 en Label Studio (Kirillov et al., ICCV 2023). Separa hojas
  vecinas y evita maleza.
- **Detectar lesiones con cajas**, usando las cajas del dataset de Colombia para entrenar un
  detector y reportar severidad por área.

---

## Problemas comunes

| Síntoma | Causa | Qué hacer |
|---|---|---|
| `... ya existe: bórralo` | El script no sobrescribe | Borra `data\dataset_v2` o `data\parches_v2` y repite |
| Muchas `carpeta sin clase` | Nombres de carpeta distintos a los esperados | Agrégalas al `mapa` de esa fuente en `fuentes_v2.json` |
| Un grupo de duplicados de cientos de fotos | Fotos casi lisas (oscuras, borrosas) se parecen entre sí | `--distancia 12` en `preparar_datos.py` |
| `train_cls.py` falla al exportar con `dynamic` | Versión vieja de ultralytics | `pip install -U ultralytics` |
| `calibrar.py`: `ninguna combinación llega a 95%` | El modelo aún no es tan bueno | Mira el reporte; prueba `--objetivo 0.9` para ver dónde está, pero no lo subas sin cumplir la regla del paso 5 |
| La Jetson tarda >5 s por foto | Muchos cuadros o CPU ocupada | Normal la primera vez; si sigue, `ANALIZAR_FOTOS = False` |
| La estación no muestra cuadros | El modelo activo es el v1 (no trae `modo_defecto: parches`) | Activa el v2 en la página Modelo |
