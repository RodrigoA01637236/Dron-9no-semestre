#!/bin/bash
# Sirve el sitio web/ (Proyecto, Identificar una hoja, Dron en vivo) desde la Jetson, sin internet.
# Con el hotspot DRON-SIGATOKA: http://10.42.0.1:8000  (Dron en vivo se conecta solo al puerto 8080).
# Es un servidor aparte: no abre ni toca la cámara; zed_right.py sigue igual.
#   bash jetson/sitio_local.sh            puerto 8000
#   PUERTO=8001 bash jetson/sitio_local.sh
REPO="$(cd "$(dirname "$0")/.." && pwd)"
WEB="$REPO/web"
PUERTO="${PUERTO:-8000}"

# Modelo, fuente y onnxruntime-web: la primera vez hace falta internet para bajar onnxruntime-web.
if ! bash "$WEB/preparar.sh"; then
    echo "Aviso: falta onnxruntime-web en web/vendor; Identificar no funcionará hasta correr esto con internet."
fi

echo "Sitio en http://$(hostname -I | awk '{print $1}'):$PUERTO  (Ctrl+C para cerrar)"
exec python3 - "$WEB" "$PUERTO" <<'PY'
import http.server, sys

class Sitio(http.server.SimpleHTTPRequestHandler):
    # .mjs y .wasm necesitan su tipo exacto o el navegador no los carga
    extensions_map = {**http.server.SimpleHTTPRequestHandler.extensions_map,
                      ".mjs": "text/javascript", ".wasm": "application/wasm"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=sys.argv[1], **kwargs)

    def log_message(self, *args):
        pass

http.server.ThreadingHTTPServer(("0.0.0.0", int(sys.argv[2])), Sitio).serve_forever()
PY
