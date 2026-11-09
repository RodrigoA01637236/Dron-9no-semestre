"""Clasificador de hojas con el paquete modelo (ONNX + JSON de metadata).

Aplica el preprocesado del contrato (resize, BGR->RGB, float32/255, CHW) y
devuelve la clase, la confianza y las probabilidades por clase. Lo usan la
estación de tierra (ui/estacion.py), la Jetson (jetson/zed_right.py) y cualquier
script que necesite predecir.

Dos modos:
- "imagen": la foto completa reducida a la entrada del modelo (rápido; video en vivo).
- "parches": la foto se corta en cuadros de hoja a resolución nativa, se clasifica cada
  uno y se junta el veredicto (vision/parches.py). Es más lento, pero ve las lesiones
  pequeñas. Se usa en las fotos.
El modo por defecto viene del JSON ("modo_defecto"); si no lo trae, es "imagen", así
que sigatoka_cls_v1 se comporta igual que antes.
"""
import json
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort

try:
    from vision import parches as P
except ImportError:  # al correrlo desde dentro de vision/
    import parches as P


def leer_imagen(ruta) -> np.ndarray | None:
    """cv2.imread no abre rutas con acentos en Windows; imdecode sí."""
    try:
        datos = np.fromfile(str(ruta), dtype=np.uint8)
    except OSError:
        return None
    if datos.size == 0:
        return None
    return cv2.imdecode(datos, cv2.IMREAD_COLOR)


def _proveedores() -> list[str]:
    # GPU si el onnxruntime instalado la trae (onnxruntime-gpu); si no, CPU.
    disponibles = ort.get_available_providers()
    return [p for p in ("CUDAExecutionProvider", "CPUExecutionProvider") if p in disponibles]


class Clasificador:
    def __init__(self, ruta_onnx):
        self.ruta = Path(ruta_onnx)
        meta = json.loads(self.ruta.with_suffix(".json").read_text(encoding="utf-8"))
        self.clases: list[str] = meta["classes"]
        self.umbral: float = float(meta.get("umbral_confianza", 0.65))
        self.lado: int = int(meta["input"][-1])
        self.temperatura: float = float(meta.get("temperatura", 1.0))
        self.modo: str = meta.get("modo_defecto", "imagen")
        self.cfg_parches: dict = P.config(meta.get("parches"))
        self.meta = meta
        self._sess = ort.InferenceSession(str(self.ruta), providers=_proveedores())
        entrada = self._sess.get_inputs()[0]
        self._entrada = entrada.name
        # Exportado con dynamic=True el lote es libre; el de v1 es fijo en 1.
        self._lote = 16 if not isinstance(entrada.shape[0], int) else 1

    # -------------------------------------------------------------- inferencia

    def _tensor(self, img_bgr: np.ndarray, interp: int) -> np.ndarray:
        x = cv2.resize(img_bgr, (self.lado, self.lado), interpolation=interp)[:, :, ::-1]
        return (x.astype(np.float32) / 255.0).transpose(2, 0, 1)

    def probabilidades(self, imgs_bgr: list[np.ndarray], interp: int = cv2.INTER_LINEAR) -> np.ndarray:
        """Probabilidades (N x clases) de una lista de imágenes BGR, ya calibradas.
        La foto completa usa INTER_LINEAR (el resize verificado del v1); los parches usan
        INTER_AREA, igual que hacer_parches.py al guardarlos."""
        filas = []
        for i in range(0, len(imgs_bgr), self._lote):
            x = np.stack([self._tensor(im, interp) for im in imgs_bgr[i:i + self._lote]])
            filas.append(self._sess.run(None, {self._entrada: x})[0].astype(np.float64))
        p = np.concatenate(filas) if filas else np.zeros((0, len(self.clases)))
        if len(p) and not np.allclose(p.sum(axis=1), 1.0, atol=0.01):
            p = _softmax(p)  # por si el export no trae softmax
        if self.temperatura != 1.0 and len(p):
            # log(p) = logits + constante, así que esto es escalar los logits por 1/T.
            p = _softmax(np.log(np.clip(p, 1e-12, 1.0)) / self.temperatura)
        return p

    def _resultado(self, probs: np.ndarray) -> dict:
        top = int(probs.argmax())
        return {
            "clase": self.clases[top],
            "confianza": float(probs[top]),
            "probs": {c: float(p) for c, p in zip(self.clases, probs)},
        }

    # -------------------------------------------------------------- API

    def predecir_bgr(self, img_bgr: np.ndarray, modo: str | None = None) -> dict:
        modo = modo or self.modo
        if modo == "parches":
            return self.predecir_parches(img_bgr)
        r = self._resultado(self.probabilidades([img_bgr])[0])
        r["modo"] = "imagen"
        return r

    def predecir_parches(self, img_bgr: np.ndarray) -> dict:
        """Veredicto por parches de hoja, con la lista de cuadros para dibujarlos."""
        cfg = self.cfg_parches
        alto, ancho = img_bgr.shape[:2]
        todos = P.cuadros(img_bgr, cfg)
        hoja = [c for c in todos if c["hoja"] >= cfg["min_hoja"]]
        if not hoja:
            # Nada parece hoja (muy seca, de noche, cielo...): respaldo con la foto completa.
            r = self._resultado(self.probabilidades([img_bgr])[0])
            r.update(modo="imagen", n_parches=0, n_cuadros=len(todos), parches=[],
                     ancho=ancho, alto=alto, aviso="No encontré hoja en la foto; usé la foto completa.")
            return r

        probs = self.probabilidades([P.recortar(img_bgr, c) for c in hoja], cv2.INTER_AREA)
        r = P.agregar(probs, self.clases, cfg, self.umbral)
        lista = []
        for c, p in zip(hoja, probs):
            i = int(p.argmax())
            lista.append({**c, "clase": self.clases[i], "confianza": round(float(p[i]), 3)})
        r.update(modo="parches", n_parches=len(hoja), n_cuadros=len(todos), parches=lista,
                 ancho=ancho, alto=alto)
        return r

    def predecir(self, ruta, modo: str | None = None) -> dict | None:
        img = leer_imagen(ruta)
        return None if img is None else self.predecir_bgr(img, modo)


def _softmax(z: np.ndarray) -> np.ndarray:
    e = np.exp(z - z.max(axis=1, keepdims=True))
    return e / e.sum(axis=1, keepdims=True)
