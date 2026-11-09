# data/

Las imágenes **no se versionan en git** (ver `.gitignore`); viven en el NVMe de la Jetson / PC de trabajo con doble respaldo (disco externo + nube) tras cada visita de campo. Git versiona manifiestos, splits y exports de etiquetas. Estructura y reglas completas: [docs/05-datos-dataset.md](../docs/05-datos-dataset.md).

```
data/
├── manifests/    # CSV por versión del dataset + splits (SÍ en git)
├── labeled/      # exports de Label Studio (SÍ en git)
├── raw/          # imágenes públicas y de vuelos (NO en git)
└── flights/      # sesiones de captura de la Jetson (NO en git)
```

## Registro de fuentes públicas

| Fuente | Licencia | Fecha de descarga | Uso permitido |
|---|---|---|---|
| NM-AIST Bananas, Tanzania — doi:10.7910/DVN/LQUWXW | CC0 1.0 | al bajar | entrenar (sana, sigatoka, Fusarium) |
| Sigatoka/Cordana/sana, San Martín, Perú — 10.17632/hzttvh774g.3 | CC BY 4.0 | al bajar | entrenar |
| BananaLSD — 10.17632/9tb7k297ff.1 (solo OriginalSet) | CC BY 4.0 | al bajar | entrenar |
| Banana Disease Recognition — 10.17632/79w2n6b4kf.1 (solo originales) | CC BY 4.0 | al bajar | entrenar |
| Azam et al., Banana and Banana Leaf — 10.17632/5nfjzntwd8.3 (RAW) | CC BY 4.0 | al bajar | entrenar; frutos -> sin_hoja |
| Banana Leaf Disease Dataset Bangladesh — 10.17632/wfzpdmc5vx.1 | CC BY 4.0 | al bajar | entrenar |
| Banana Leaf Disease Images (Hailu) — 10.17632/rjykr62kdh.1 | CC BY 4.0 | al bajar | entrenar |
| BLADE — 10.17632/w7ytz3twjv.2 | CC BY 4.0 | al bajar | solo train |
| Deficiencias de nutrientes — 10.17632/7vpdrbdkd4.2 (sin Sulphur) | CC BY 4.0 | al bajar | entrenar (otra condición) |
| UAV Black Sigatoka DS-v2, Colombia — 10.5281/zenodo.20945958 | CC BY 4.0 | al bajar | solo prueba externa |
| Banana Imagery Tanzania — 10.5281/zenodo.7670326 (opcional, 34 GB) | CC BY 4.0 | al bajar | entrenar |
| DeepWeeds — github.com/AlexOlsen/DeepWeeds | CC BY 4.0 | al bajar | sin_hoja |
| PlantDoc — github.com/pratikkayal/PlantDoc-Dataset | CC BY 4.0 | al bajar | sin_hoja |
| iBean — huggingface.co/datasets/AI-Lab-Makerere/beans | MIT | al bajar | sin_hoja |
| Hojas de café, San Martín, Perú — 10.17632/mfpxg4y65r.2 | CC BY 4.0 | al bajar | sin_hoja |
| COCO val2017 — cocodataset.org (sin fotos con plátano ni plantas en maceta) | anotaciones CC BY 4.0; imágenes con su licencia de Flickr | al bajar | sin_hoja |

Lista y descarga automática: `vision/train/fuentes_v2.json` y `vision/train/descargar_datos.py` (ver `vision/GUIA-NOCHE.md`). Cambiar "al bajar" por la fecha real.
[6:10 p.m., 29/9/2026] Hero: E Arman, Shifat; Baki Bhuiyan, Md Abdullahil; Abdullah, Hasan Muhammad; Islam, Shariful; Chowdhury, Tahsin Tanha; Hossain, Md. Arban (2023), “Banana Leaf Spot Diseases (BananaLSD) Dataset for Classification of Banana Leaf Diseases Using Machine Learning”, Mendeley Data, V1, doi: 10.17632/9tb7k297ff.1
[6:10 p.m., 29/9/2026] Hero: Azam, Showrov ; Das, Utsab; Kafi, Md Abdullah Al (2026), “Banana and Banana Leaf Dataset for Classification and Disease Detection”, Mendeley Data, V3, doi: 10.17632/5nfjzntwd8.3
[6:10 p.m., 29/9/2026] Hero: Mishra, Vikash Kumar; Shekhar, Raaj; Mishra, Amit; Singh , Upendra Pratap  (2026), “BLADE: Banana Leaf Agricultural Disease Evaluation”, Mendeley Data, V2, doi: 10.17632/w7ytz3twjv.2
[6:10 p.m., 29/9/2026] Hero: hailu, yordanos (2021), “Banana Leaf Disease Images”, Mendeley Data, V1, doi: 10.17632/rjykr62kdh.1
[6:10 p.m., 29/9/2026] Hero: Islam, Syeda Asrafa; Wen, Ng Giap; Mridha, Firoz; Abdullah-Al-Jubair, Md.; Alam, Touhid (2026), “Banana Leaf Disease Dataset of Bangladesh”, Mendeley Data, V1, doi: 10.17632/wzshm7ky49.1
[6:10 p.m., 29/9/2026] Hero: E Arman, Shifat; Baki Bhuiyan, Md Abdullahil; Abdullah, Hasan Muhammad; Islam, Shariful; Chowdhury, Tahsin Tanha; Hossain, Md. Arban (2023), “Banana Leaf Spot Diseases (BananaLSD) Dataset for Classification of Banana Leaf Diseases Using Machine Learning”, Mendeley Data, V1, doi: 10.17632/9tb7k297ff.1