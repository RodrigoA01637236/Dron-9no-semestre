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
