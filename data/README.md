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
| (pendiente — registrar aquí cada dataset al descargarlo) | | | |
[6:10 p.m., 29/9/2026] Hero: E Arman, Shifat; Baki Bhuiyan, Md Abdullahil; Abdullah, Hasan Muhammad; Islam, Shariful; Chowdhury, Tahsin Tanha; Hossain, Md. Arban (2023), “Banana Leaf Spot Diseases (BananaLSD) Dataset for Classification of Banana Leaf Diseases Using Machine Learning”, Mendeley Data, V1, doi: 10.17632/9tb7k297ff.1
[6:10 p.m., 29/9/2026] Hero: Azam, Showrov ; Das, Utsab; Kafi, Md Abdullah Al (2026), “Banana and Banana Leaf Dataset for Classification and Disease Detection”, Mendeley Data, V3, doi: 10.17632/5nfjzntwd8.3
[6:10 p.m., 29/9/2026] Hero: Mishra, Vikash Kumar; Shekhar, Raaj; Mishra, Amit; Singh , Upendra Pratap  (2026), “BLADE: Banana Leaf Agricultural Disease Evaluation”, Mendeley Data, V2, doi: 10.17632/w7ytz3twjv.2
[6:10 p.m., 29/9/2026] Hero: hailu, yordanos (2021), “Banana Leaf Disease Images”, Mendeley Data, V1, doi: 10.17632/rjykr62kdh.1
[6:10 p.m., 29/9/2026] Hero: Islam, Syeda Asrafa; Wen, Ng Giap; Mridha, Firoz; Abdullah-Al-Jubair, Md.; Alam, Touhid (2026), “Banana Leaf Disease Dataset of Bangladesh”, Mendeley Data, V1, doi: 10.17632/wzshm7ky49.1
[6:10 p.m., 29/9/2026] Hero: E Arman, Shifat; Baki Bhuiyan, Md Abdullahil; Abdullah, Hasan Muhammad; Islam, Shariful; Chowdhury, Tahsin Tanha; Hossain, Md. Arban (2023), “Banana Leaf Spot Diseases (BananaLSD) Dataset for Classification of Banana Leaf Diseases Using Machine Learning”, Mendeley Data, V1, doi: 10.17632/9tb7k297ff.1