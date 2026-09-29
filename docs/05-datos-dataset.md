# 05 — Datos y dataset: el activo central del proyecto

El modelo es reemplazable; **el dataset validado no**. No existe públicamente un dataset grande de Sigatoka en condiciones de campo mexicanas: construirlo bien es a la vez la mayor carga de trabajo (~80 %) y la ventaja competitiva del proyecto.

## 1. Estrategia en dos vías

- **Vía rápida (semana 1):** datasets públicos → baseline del modelo, pipeline de entrenamiento funcionando de inmediato.
- **Vía de valor (todo el proyecto):** recolección propia en campo con etiquetado validado por experto → métricas reales y activo comercial.

## 2. Datasets públicos de arranque

| Dataset | Dónde | Contenido aproximado | Uso |
|---|---|---|---|
| BananaLSD (Banana Leaf Spot Diseases) | Mendeley Data | Hojas de banano: sana, Sigatoka, cordana, pestalotiopsis | Baseline de clasificación |
| PSFD-Banana / datasets de "banana leaf disease" | Kaggle | Varias clases de enfermedades foliares | Aumento del baseline |
| PlantVillage (subconjuntos) | Kaggle/GitHub | Hojas en fondo controlado | Solo pre-entrenamiento; NO refleja campo |

Advertencias:
- Verificar **licencia** de cada dataset (la mayoría son CC BY — citar; algunas prohíben uso comercial: registrar cuál se usa para qué).
- Los datasets públicos suelen ser fotos de hoja individual, bien iluminada, a veces sobre fondo liso. Un modelo entrenado solo ahí **fallará en fotos aéreas de campo**. Sirven para validar el pipeline y como pre-entrenamiento, nunca como métrica final.
- Documentar en `data/README.md` el origen, licencia y fecha de descarga de cada fuente.

## 3. Acceso a campo y a expertos (empezar la semana 1)

Contactos a gestionar en paralelo (no esperar a tener el dron listo):

1. **Fincas/productores de plátano** — regiones productoras (Tabasco, Chiapas, Colima, Michoacán, Veracruz…): cooperativas locales, contactos de la universidad, asociaciones de productores. Pedir: permiso de acceso con dron y celular, y de preferencia una parcela con incidencia conocida de Sigatoka.
2. **Fitopatólogo o agrónomo especialista** — opciones: profesores de agronomía/fitopatología de la propia universidad o de una socia, INIFAP, Comités Estatales de Sanidad Vegetal, laboratorios de diagnóstico. Su rol: validar el protocolo de captura, etiquetar/verificar la muestra de control, y aplicar la escala Stover en las validaciones de campo.
3. Acordar desde el inicio qué recibe cada parte (reporte de su parcela, coautoría académica, acceso al sistema) — el acceso recurrente vale oro.

**Riesgo estacional:** la Sigatoka se dispara con lluvia y humedad. Confirmar con el experto la ventana de mayor incidencia en la región elegida y **agendar las visitas alrededor de esa ventana**.

## 4. Protocolo de recolección en campo

Cada visita produce datos de dos fuentes (redundancia deliberada):
- **Celular** (siempre): fotos de cerca de hojas individuales, envés y haz, con y sin síntomas. No depende de ningún hardware del proyecto.
- **Dron** (cuando la fase 1 esté lista): fotos con el protocolo de captura del doc 03, de las mismas plantas.

Por cada planta muestreada, registrar (hoja de campo o app de notas):

```
planta_id (etiqueta física o estaca numerada)
GPS (del celular o del dron)
variedad (si se conoce)
diagnóstico del experto: sana / sigatoka (severidad Stover 0–6) / otra cosa (cuál)
observaciones (deficiencias nutricionales visibles, plagas, daño mecánico)
```

**Crítico — clases negativas difíciles:** recolectar deliberadamente hojas con deficiencias nutricionales (K, Mg), daño por sol, daño mecánico y otras enfermedades. Los síntomas tempranos de Sigatoka se confunden con estas condiciones; sin negativos difíciles el modelo aprende "hoja fea = enferma" y no sirve para diagnosticar.

Meta de volumen (acumulada en 3+ visitas): **≥2,000 imágenes propias**, balanceadas ~40 % sanas / 40 % Sigatoka (en varios estadios) / 20 % otras condiciones.

## 5. Etiquetado con Label Studio

```bash
pip install label-studio
label-studio start   # UI web en http://localhost:8080
```

Configuración del proyecto de etiquetado:
- **Tarea de clasificación por imagen** (fase 1): `sana` / `sigatoka_temprana (Fouré 1–3)` / `sigatoka_avanzada (Fouré 4–6 / Stover ≥3)` / `otra_condicion` / `no_diagnosticable` (borrosa, lejana, oclusión).
- **Fase 2 (opcional, para detección):** cajas o polígonos sobre lesiones individuales.

Proceso de calidad:
1. Los dos integrantes etiquetan de forma independiente una **muestra común del 15–20 %**.
2. Medir acuerdo (porcentaje de coincidencia y kappa de Cohen; Label Studio lo reporta o se calcula con `sklearn.metrics.cohen_kappa_score`).
3. Las discrepancias y todo lo dudoso van al **experto**, cuya palabra es final.
4. El experto revisa además una muestra aleatoria del resto (control de calidad).
5. Registrar en el manifiesto quién etiquetó cada imagen y si fue validada por experto.

Si el acuerdo inter-etiquetador es bajo (<80 % / kappa <0.6), detenerse y recalibrar criterios con el experto antes de seguir etiquetando: etiquetas ruidosas = modelo ruidoso.

## 6. Estructura y versionado del dataset

Las imágenes **no van a git** (pesan GB); van a disco de la Jetson/PC + respaldo (Drive/disco externo). Git versiona los **manifiestos** y scripts.

```
data/
├── README.md                  # fuentes, licencias, fechas (SÍ va a git)
├── manifests/                 # SÍ van a git
│   ├── v1_public_baseline.csv
│   ├── v2_campo_2026-10.csv
│   └── splits/
│       ├── v2_train.csv  v2_val.csv  v2_test.csv
├── raw/                       # NO va a git
│   ├── public/bananalsd/ ...
│   └── flights/2026-10-15_finca-lopez/ ...
└── labeled/                   # exports de Label Studio (JSON — SÍ pueden ir a git)
```

Manifiesto CSV mínimo por imagen:

```
path,origen,fecha,finca,planta_id,lat,lon,etiqueta,severidad_stover,etiquetador,validado_experto
```

Reglas de particionado (previenen el error más común de estos proyectos):
- El split train/val/test se hace **por planta y por visita**, nunca por imagen: dos fotos de la misma planta jamás quedan una en train y otra en test (fuga de datos → métricas infladas).
- El test set ideal es **una finca o visita completa que el modelo nunca vio** — esa es la métrica que se reporta en la tesis y al cliente.
- Los splits se generan por script (`scripts/make_splits.py`) con semilla fija, y el resultado se versiona.

## 7. Respaldo

Después de cada visita de campo, el mismo día: copiar `data/raw/flights/` a dos destinos (disco externo + nube). Una visita de campo cuesta un día y dinero; perder sus datos por una SD/NVMe corrupta es el accidente más caro y más prevenible del proyecto.
