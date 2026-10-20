#!/bin/bash
# Arma el sitio público: copia a web/ el modelo y la fuente, que viven en otras carpetas del repo.
# Netlify lo corre en cada despliegue (netlify.toml); también sirve para probar en local:
#   bash web/preparar.sh && python3 -m http.server 8090 --directory web
set -e
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
WEB="$RAIZ/web"

mkdir -p "$WEB/modelo" "$WEB/fuentes"
cp "$RAIZ/vision/models/sigatoka_cls_v1.onnx" "$RAIZ/vision/models/sigatoka_cls_v1.json" "$WEB/modelo/"
cp "$RAIZ/ui/static/fuentes/fuentes.css" "$RAIZ/ui/static/fuentes/manrope-0.woff2" "$RAIZ/ui/static/fuentes/LEEME.txt" "$WEB/fuentes/"
echo "Sitio listo en $WEB"
