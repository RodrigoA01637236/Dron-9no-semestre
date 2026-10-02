r"""Demo en TIEMPO REAL: la cámara diagnostica continuamente lo que ve.

Abre una ventana de video con la webcam y corre el clasificador sobre cada
frame, mostrando la clase, la confianza y los FPS sobre la imagen. Es el
mismo paquete ONNX y el mismo preprocesado que correrá la Jetson en vuelo
— esta demo es el pipeline del dron con tu webcam como cámara.

Uso (desde la raíz del repo, con el venv activo):
    python vision/demo_live.py
    python vision/demo_live.py --camara 1      # si tienes más de una cámara

Teclas dentro de la ventana:  q = salir,  g = guardar captura en runs/live/
Tip de demo: apunta la cámara a fotos de hojas en la pantalla de tu celular.
"""
import argparse
import json
import time
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort

MODELO = Path("vision/models/sigatoka_cls_v1.onnx")

COLORES = {  # BGR
    "sana": (80, 200, 80),
    "sigatoka": (60, 60, 230),
    "otra_condicion": (60, 200, 230),
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--camara", type=int, default=0, help="índice de la cámara (0 = la integrada)")
    args = ap.parse_args()

    meta = json.loads(MODELO.with_suffix(".json").read_text(encoding="utf-8"))
    clases, umbral, lado = meta["classes"], meta["umbral_confianza"], meta["input"][-1]
    sess = ort.InferenceSession(str(MODELO))
    entrada = sess.get_inputs()[0].name

    cam = cv2.VideoCapture(args.camara)
    if not cam.isOpened():
        raise SystemExit(f"No pude abrir la cámara {args.camara}. Prueba --camara 1 (o 2).")

    print("Corriendo. Teclas: q = salir, g = guardar captura.")
    t_prev = time.time()
    while True:
        ok, frame = cam.read()
        if not ok:
            break

        # Contrato de la Jetson: resize, BGR->RGB, float32/255, CHW
        x = cv2.resize(frame, (lado, lado))[:, :, ::-1]
        x = (x.astype(np.float32) / 255.0).transpose(2, 0, 1)[None]
        probs = sess.run(None, {entrada: x})[0][0]
        if not 0.99 <= probs.sum() <= 1.01:
            e = np.exp(probs - probs.max())
            probs = e / e.sum()
        top = int(probs.argmax())
        clase, conf = clases[top], float(probs[top])

        ahora = time.time()
        fps = 1.0 / max(ahora - t_prev, 1e-6)
        t_prev = ahora

        if conf < umbral:
            texto, color = f"no diagnosticable ({conf:.0%})", (160, 160, 160)
        else:
            texto, color = f"{clase} {conf:.0%}", COLORES.get(clase, (255, 255, 255))

        # Banda superior con el veredicto + barras por clase
        cv2.rectangle(frame, (0, 0), (frame.shape[1], 64), (0, 0, 0), -1)
        cv2.putText(frame, texto, (12, 42), cv2.FONT_HERSHEY_SIMPLEX, 1.1, color, 3)
        cv2.putText(frame, f"{fps:.0f} FPS", (frame.shape[1] - 130, 42),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        for i, (c, p) in enumerate(zip(clases, probs)):
            y = 84 + i * 26
            cv2.rectangle(frame, (12, y), (12 + int(180 * p), y + 14), COLORES.get(c, (200, 200, 200)), -1)
            cv2.putText(frame, f"{c} {p:.0%}", (200, y + 13),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        cv2.imshow("Sigatoka - deteccion en tiempo real (q=salir, g=guardar)", frame)
        tecla = cv2.waitKey(1) & 0xFF
        if tecla == ord("q"):
            break
        if tecla == ord("g"):
            destino = Path("runs/live")
            destino.mkdir(parents=True, exist_ok=True)
            nombre = destino / f"captura_{time.strftime('%Y%m%d_%H%M%S')}_{clase}.jpg"
            cv2.imwrite(str(nombre), frame)
            print(f"Guardada: {nombre}")

    cam.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
