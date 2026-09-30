r"""Transmisión en vivo del diagnóstico por WiFi (el modo "dron" de la demo).

Corre la cámara + el clasificador y sirve una página web con el video anotado
en tiempo real. Cualquier laptop o celular EN LA MISMA RED la ve abriendo el
navegador — sin instalar nada. Es la arquitectura real del dron (doc 08):
la Jetson infiere a bordo y el operador solo mira una página web.

Uso (desde la raíz del repo, con el venv activo):
    pip install flask                   # solo la primera vez
    python vision/stream_live.py
    # En esta máquina:   http://localhost:5000
    # Desde otro equipo: http://<IP-de-esta-máquina>:5000   (la imprime al arrancar)

En la Jetson se corre igual (con la cámara del dron); el operador se conecta
al hotspot WiFi de la Jetson y abre la misma dirección.
"""
import argparse
import json
import socket
import time
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort

MODELO = Path("vision/models/sigatoka_cls_v1.onnx")

COLORES = {"sana": (80, 200, 80), "sigatoka": (60, 60, 230), "otra_condicion": (60, 200, 230)}

META = json.loads(MODELO.with_suffix(".json").read_text(encoding="utf-8"))
CLASES, UMBRAL, LADO = META["classes"], META["umbral_confianza"], META["input"][-1]
SESS = ort.InferenceSession(str(MODELO))
ENTRADA = SESS.get_inputs()[0].name

PAGINA = """<!doctype html><html><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dron Sigatoka — en vivo</title>
<style>body{margin:0;background:#111;color:#eee;font-family:sans-serif;text-align:center}
h1{font-size:1.1rem;padding:.6rem;margin:0}img{width:100%;max-width:960px}</style></head>
<body><h1>🚁 Detección de Sigatoka — video en vivo desde el sistema de visión</h1>
<img src="/video"></body></html>"""


def anotar(frame: np.ndarray) -> np.ndarray:
    x = cv2.resize(frame, (LADO, LADO))[:, :, ::-1]
    x = (x.astype(np.float32) / 255.0).transpose(2, 0, 1)[None]
    probs = SESS.run(None, {ENTRADA: x})[0][0]
    if not 0.99 <= probs.sum() <= 1.01:
        e = np.exp(probs - probs.max())
        probs = e / e.sum()
    top = int(probs.argmax())
    clase, conf = CLASES[top], float(probs[top])
    if conf < UMBRAL:
        texto, color = f"no diagnosticable ({conf:.0%})", (160, 160, 160)
    else:
        texto, color = f"{clase} {conf:.0%}", COLORES.get(clase, (255, 255, 255))
    cv2.rectangle(frame, (0, 0), (frame.shape[1], 56), (0, 0, 0), -1)
    cv2.putText(frame, texto, (12, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, color, 3)
    return frame


def main() -> None:
    from flask import Flask, Response

    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--camara", type=int, default=0)
    ap.add_argument("--puerto", type=int, default=5000)
    args = ap.parse_args()

    cam = cv2.VideoCapture(args.camara)
    if not cam.isOpened():
        raise SystemExit(f"No pude abrir la cámara {args.camara}. Prueba --camara 1.")

    app = Flask(__name__)

    @app.route("/")
    def inicio():
        return PAGINA

    @app.route("/video")
    def video():
        def frames():
            while True:
                ok, frame = cam.read()
                if not ok:
                    break
                ok, jpg = cv2.imencode(".jpg", anotar(frame), [cv2.IMWRITE_JPEG_QUALITY, 80])
                if ok:
                    yield (b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + jpg.tobytes() + b"\r\n")
                time.sleep(0.03)
        return Response(frames(), mimetype="multipart/x-mixed-replace; boundary=frame")

    try:
        ip = socket.gethostbyname(socket.gethostname())
    except OSError:
        ip = "<tu-IP>"
    print("\n================================================")
    print(f"  En esta máquina:    http://localhost:{args.puerto}")
    print(f"  Desde otro equipo:  http://{ip}:{args.puerto}")
    print("  (mismo WiFi; Ctrl+C para detener)")
    print("================================================\n")
    app.run(host="0.0.0.0", port=args.puerto, threaded=True)


if __name__ == "__main__":
    main()
