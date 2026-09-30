"""Prueba de humo del paquete modelo (fase 5): corre el ONNX con onnxruntime.

Usa EXACTAMENTE el preprocesado del contrato (resize 384x384, BGR->RGB,
float32/255, CHW) y el JSON de metadata que acompaña al modelo. Es el mismo
preprocesado que infer.py deberá replicar en la Jetson; si esta prueba pasa
en la PC y las predicciones coinciden con lo que ves en las fotos, el
paquete está listo para desplegarse.

Uso (desde la raíz del repo, con el venv activo):
    python vision/verificar_onnx.py --imagen ruta\a\foto.jpg
    python vision/verificar_onnx.py --carpeta data\dataset\test\sigatoka
"""
import argparse
import json
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def preprocesar(path: Path, lado: int) -> np.ndarray:
    img = cv2.imread(str(path))
    if img is None:
        raise SystemExit(f"No pude leer la imagen: {path}")
    x = cv2.resize(img, (lado, lado))[:, :, ::-1]          # BGR -> RGB
    return (x.astype(np.float32) / 255.0).transpose(2, 0, 1)[None]  # CHW + batch


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--modelo", default="vision/models/sigatoka_cls_v1.onnx")
    ap.add_argument("--imagen", action="append", default=[], help="una o varias fotos")
    ap.add_argument("--carpeta", help="evalúa todas las imágenes de una carpeta")
    args = ap.parse_args()

    modelo = Path(args.modelo)
    meta = json.loads(modelo.with_suffix(".json").read_text(encoding="utf-8"))
    clases, umbral, lado = meta["classes"], meta["umbral_confianza"], meta["input"][-1]

    sess = ort.InferenceSession(str(modelo))
    entrada = sess.get_inputs()[0].name

    rutas = [Path(p) for p in args.imagen]
    if args.carpeta:
        rutas += [p for p in sorted(Path(args.carpeta).iterdir()) if p.suffix.lower() in IMG_EXTS]
    if not rutas:
        raise SystemExit("Dame --imagen o --carpeta. Ejemplo: --carpeta data\\dataset\\test\\sana")

    aciertos_carpeta = 0
    for ruta in rutas:
        probs = sess.run(None, {entrada: preprocesar(ruta, lado)})[0][0]
        if not 0.99 <= probs.sum() <= 1.01:          # por si el export no trae softmax
            e = np.exp(probs - probs.max())
            probs = e / e.sum()
        top = int(probs.argmax())
        conf = float(probs[top])
        marca = "" if conf >= umbral else "  [descartada: bajo umbral]"
        print(f"{ruta.name:45s} -> {clases[top]:15s} conf={conf:.2f}{marca}")
        if args.carpeta and clases[top] == Path(args.carpeta).name:
            aciertos_carpeta += 1

    if args.carpeta:
        print(f"\nCoinciden con el nombre de la carpeta: {aciertos_carpeta}/{len(rutas)}")


if __name__ == "__main__":
    main()
