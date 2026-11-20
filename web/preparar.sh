#!/bin/bash
# Arma el sitio público: copia a web/ el modelo y Leaflet, que viven en otras carpetas del repo,
# y baja onnxruntime-web y MapLibre a web/vendor/ para que el sitio funcione también sin internet (hotspot).
# Netlify lo corre en cada despliegue (netlify.toml). En la Jetson se corre una vez con internet.
#   bash web/preparar.sh && python3 -m http.server 8090 --directory web
set -e
RAIZ="$(cd "$(dirname "$0")/.." && pwd)"
WEB="$RAIZ/web"

mkdir -p "$WEB/modelo" "$WEB/vendor/leaflet"
# Leaflet para el mapa (la misma copia que usa la estación, sin CDN)
cp -r "$RAIZ/ui/static/leaflet/." "$WEB/vendor/leaflet/"
# El v2 (por cuadros) es el que usa la página; el v1 queda para comparar con ?modelo=v1.
for m in sigatoka_cls_v1 sigatoka_cls_v2; do
    cp "$RAIZ/vision/models/$m.onnx" "$RAIZ/vision/models/$m.json" "$WEB/modelo/"
done

# Librerías de terceros, con versión fija. Se verifica el sha256 de cada archivo; si ya están, no se bajan.
# - onnxruntime-web 1.30.0, solo WebAssembly (el modelo en el navegador).
# - MapLibre GL JS 4.7.1 (el mapa 3D del lote); se carga solo al elegir 3D.
python3 - "$WEB/vendor" <<'PY'
import hashlib, sys, urllib.request
from pathlib import Path

GRUPOS = [
    ("https://cdn.jsdelivr.net/npm/onnxruntime-web@1.30.0/dist/", "", {
        "ort.wasm.min.js": "faece07e84faa9001f5104bbe4e5c70861d06cb2376a0dea1fa0ad33a67adc81",
        "ort-wasm-simd-threaded.mjs": "e13f7f94fc51b4ca72b12faeb1ee95f4ace6dfbc8939bc718aabdc0a27c4299b",
        "ort-wasm-simd-threaded.wasm": "3398c10d07d229bd91b364548e130e0e51a8e5704b88c7c083ebbeb78842dee2",
    }),
    ("https://cdn.jsdelivr.net/npm/maplibre-gl@4.7.1/dist/", "maplibre", {
        "maplibre-gl.js": "be9633c4d870e26fb37f1cfe5c5a77181667114003ea16207ac7850d8da8add1",
        "maplibre-gl.css": "576b085fdd9487a65a19215328c1e086c07ce5bf6da09b666b3806d3d008dae9",
    }),
]
for base, carpeta, archivos in GRUPOS:
    destino = Path(sys.argv[1]) / carpeta
    destino.mkdir(parents=True, exist_ok=True)
    for nombre, sha in archivos.items():
        ruta = destino / nombre
        if ruta.exists() and hashlib.sha256(ruta.read_bytes()).hexdigest() == sha:
            continue
        try:
            datos = urllib.request.urlopen(base + nombre, timeout=120).read()
        except OSError as e:
            sys.exit(f"No se pudo bajar {nombre} ({e}). Corre esto con internet una vez.")
        if hashlib.sha256(datos).hexdigest() != sha:
            sys.exit(f"{nombre} no coincide con el sha256 esperado; no se guardó.")
        ruta.write_bytes(datos)
        print("Bajado", carpeta + "/" + nombre if carpeta else nombre)
PY
echo "Sitio listo en $WEB"
