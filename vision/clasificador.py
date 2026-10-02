"""Clasificador de hojas con el paquete modelo (ONNX + JSON de metadata).

Aplica el preprocesado del contrato (resize, BGR->RGB, float32/255, CHW) y
devuelve la clase, la confianza y las probabilidades por clase. Lo usan la
estación de tierra (ui/estacion.py) y cualquier script que necesite predecir.
"""
import json
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort


def leer_imagen(ruta) -> np.ndarray | None:
    """cv2.imread no abre rutas con acentos en Windows; imdecode sí."""
    try:
        datos = np.fromfile(str(ruta), dtype=np.uint8)
    except OSError:
        return None
    if datos.size == 0:
        return None
    return cv2.imdecode(datos, cv2.IMREAD_COLOR)


class Clasificador:
    def __init__(self, ruta_onnx):
        self.ruta = Path(ruta_onnx)
        meta = json.loads(self.ruta.with_suffix(".json").read_text(encoding="utf-8"))
        self.clases: list[str] = meta["classes"]
        self.umbral: float = float(meta.get("umbral_confianza", 0.65))
        self.lado: int = int(meta["input"][-1])
        self.meta = meta
        self._sess = ort.InferenceSession(str(self.ruta), providers=["CPUExecutionProvider"])
        self._entrada = self._sess.get_inputs()[0].name

    def predecir_bgr(self, img_bgr: np.ndarray) -> dict:
        x = cv2.resize(img_bgr, (self.lado, self.lado))[:, :, ::-1]
        x = (x.astype(np.float32) / 255.0).transpose(2, 0, 1)[None]
        probs = self._sess.run(None, {self._entrada: x})[0][0].astype(np.float64)
        if not 0.99 <= probs.sum() <= 1.01:  # por si el export no trae softmax
            e = np.exp(probs - probs.max())
            probs = e / e.sum()
        top = int(probs.argmax())
        return {
            "clase": self.clases[top],
            "confianza": float(probs[top]),
            "probs": {c: float(p) for c, p in zip(self.clases, probs)},
        }

    def predecir(self, ruta) -> dict | None:
        img = leer_imagen(ruta)
        return None if img is None else self.predecir_bgr(img)
