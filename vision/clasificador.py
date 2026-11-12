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
    from vision import rasgos as R
except ImportError:  # al correrlo desde dentro de vision/
    import parches as P
    import rasgos as R


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
        # Filtro "¿esto es hoja de plátano?" (vision/rasgos.py): necesita los rasgos de la
        # penúltima capa, así que se le agrega esa salida al modelo. Si algo falla, sin filtro.
        self.filtro = None
        self._sess = None
        if meta.get("filtro_hoja") and "sin_hoja" in self.clases:
            try:
                datos, _, W, _ = R.con_rasgos(self.ruta.read_bytes())
                self.filtro = R.FiltroHoja(meta, W.shape[1])
                self._sess = ort.InferenceSession(datos, providers=_proveedores())
            except Exception as e:  # noqa: BLE001
                print(f"[Clasificador] sin filtro de hoja: {e}")
                self.filtro = None
        if self._sess is None:
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
        return self._correr(imgs_bgr, interp)[0]

    def _correr(self, imgs_bgr: list[np.ndarray], interp: int, filtrar: str | None = None):
        """(probabilidades calibradas, ¿es hoja de plátano? o None si no se filtra).
        filtrar: "cuadros" (la sonda de cuadros) o "imagen" (la de la foto completa)."""
        filas, hojas = [], []
        if self.filtro is None or (filtrar == "imagen" and self.filtro.w_imagen is None):
            filtrar = None
        for i in range(0, len(imgs_bgr), self._lote):
            x = np.stack([self._tensor(im, interp) for im in imgs_bgr[i:i + self._lote]])
            salida = self._sess.run(None, {self._entrada: x})
            filas.append(salida[0].astype(np.float64))
            if filtrar == "imagen":
                hojas.append(self.filtro.es_hoja_imagen(salida[1]))
            elif filtrar:
                hojas.append(self.filtro.es_hoja(salida[1], [R.color_hoja(t) for t in x]))
        p = np.concatenate(filas) if filas else np.zeros((0, len(self.clases)))
        if len(p) and not np.allclose(p.sum(axis=1), 1.0, atol=0.01):
            p = _softmax(p)  # por si el export no trae softmax
        if self.temperatura != 1.0 and len(p):
            # log(p) = logits + constante, así que esto es escalar los logits por 1/T.
            p = _softmax(np.log(np.clip(p, 1e-12, 1.0)) / self.temperatura)
        if not filtrar:
            return p, None
        return p, (np.concatenate(hojas) if hojas else np.zeros(0, bool))

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
        p, es = self._correr([img_bgr], cv2.INTER_LINEAR, filtrar="imagen")
        r = self._resultado(p[0])
        if es is not None and not es[0] and r["clase"] != "sin_hoja":
            # El filtro de hoja dice que la imagen no es hoja de plátano (video en vivo).
            q = np.zeros_like(p[0])
            q[self.clases.index("sin_hoja")] = 1.0
            r = self._resultado(q)
            r["n_filtrados"] = 1
        r["modo"] = "imagen"
        return r

    def predecir_parches(self, img_bgr: np.ndarray) -> dict:
        """Veredicto por parches de hoja, con los cuadros y las hojas para dibujarlos."""
        cfg = self.cfg_parches
        alto, ancho = img_bgr.shape[:2]
        mascara = P.mascara_hoja(img_bgr)
        todos = P.cuadros(img_bgr, cfg, mascara)
        usar = [c for c in todos if c["hoja"] >= cfg["min_hoja"]]
        if not usar:
            # Nada parece vegetación (muy seca, de noche, cielo...): respaldo con la foto completa.
            r = self._resultado(self.probabilidades([img_bgr])[0])
            r.update(modo="imagen", n_parches=0, n_cuadros=len(todos), parches=[], hojas=[],
                     ancho=ancho, alto=alto, aviso="No encontré hoja en la foto; usé la foto completa.")
            return r

        probs, es = self._correr([P.recortar(img_bgr, c) for c in usar], cv2.INTER_AREA, filtrar="cuadros")
        n_filtrados = None
        if es is not None:
            probs, n_filtrados = self.filtro.aplicar(probs, es, self.clases.index("sin_hoja"))
        r = P.agregar(probs, self.clases, cfg, self.umbral)
        if n_filtrados is not None:
            r["n_filtrados"] = n_filtrados
        ignorar = set(cfg.get("ignorar") or [])
        lista = []
        for c, p in zip(usar, probs):
            i = int(p.argmax())
            lista.append({**c, "clase": self.clases[i], "confianza": round(float(p[i]), 3)})

        # Una lectura por hoja: los parches se reparten entre las hojas que encuentra.
        hojas = []
        if cfg.get("separar_hojas") and r.get("n_hoja", 1) > 0:
            etiquetas, hojas = P.separar_hojas(img_bgr, mascara, cfg)
            grupos: dict[int, list[int]] = {}
            for k, c in enumerate(lista):
                c["id_hoja"] = P.hoja_de_cuadro(c, etiquetas, alto, ancho)
                if c["id_hoja"] and c["clase"] not in ignorar:
                    grupos.setdefault(c["id_hoja"], []).append(k)
            leidas = []
            for h in hojas:
                ks = grupos.get(h["id"])
                if not ks:
                    continue  # región sin parches de hoja de plátano (maleza, sombra...)
                rh = P.agregar(probs[ks], self.clases, cfg, self.umbral)
                leidas.append({**h, "clase": rh["clase"], "confianza": round(rh["confianza"], 3),
                               "n_parches": len(ks)})
            hojas = leidas
        r.update(modo="parches", n_parches=r.get("n_hoja", len(usar)), n_cuadros=len(todos),
                 parches=lista, hojas=hojas, ancho=ancho, alto=alto)
        return r

    def predecir(self, ruta, modo: str | None = None) -> dict | None:
        img = leer_imagen(ruta)
        return None if img is None else self.predecir_bgr(img, modo)


def _softmax(z: np.ndarray) -> np.ndarray:
    e = np.exp(z - z.max(axis=1, keepdims=True))
    return e / e.sum(axis=1, keepdims=True)
