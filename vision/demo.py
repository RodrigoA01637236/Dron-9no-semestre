r"""Demo interactiva del clasificador de Sigatoka (corre en tu PC, sin internet).

Abre una página web local donde puedes arrastrar fotos de hojas (o usar la
cámara/portapapeles) y el modelo las diagnostica en vivo con las probabilidades
por clase. Usa el paquete modelo (ONNX + JSON) con el MISMO preprocesado que
correrá en la Jetson, así que lo que ves aquí es lo que hará el dron.

Uso (desde la raíz del repo, con el venv activo):
    pip install gradio          # solo la primera vez
    python vision/demo.py
    # se abre solo en el navegador (http://127.0.0.1:7860)
"""
import json
from pathlib import Path

import cv2
import numpy as np
import onnxruntime as ort

MODELO = Path("vision/models/sigatoka_cls_v1.onnx")

META = json.loads(MODELO.with_suffix(".json").read_text(encoding="utf-8"))
CLASES, UMBRAL, LADO = META["classes"], META["umbral_confianza"], META["input"][-1]

BONITO = {"sana": "Sana", "sigatoka": "Sigatoka", "otra_condicion": "Otra condición"}

sess = ort.InferenceSession(str(MODELO))
ENTRADA = sess.get_inputs()[0].name


def diagnosticar(img_rgb: np.ndarray):
    if img_rgb is None:
        return None, "Sube una foto de una hoja."
    # Mismo contrato que la Jetson: resize LADOxLADO, RGB, float32/255, CHW.
    # (Gradio ya entrega RGB; en infer.py la cámara entrega BGR y se convierte.)
    x = cv2.resize(img_rgb, (LADO, LADO))
    x = (x.astype(np.float32) / 255.0).transpose(2, 0, 1)[None]
    probs = sess.run(None, {ENTRADA: x})[0][0]
    if not 0.99 <= probs.sum() <= 1.01:
        e = np.exp(probs - probs.max())
        probs = e / e.sum()

    etiquetas = {BONITO.get(c, c): float(p) for c, p in zip(CLASES, probs)}
    top = int(probs.argmax())
    conf = float(probs[top])
    if conf < UMBRAL:
        veredicto = (f"**No diagnosticable** — la confianza ({conf:.0%}) quedó debajo del "
                     f"umbral ({UMBRAL:.0%}). En el dron, esta foto se marcaría en gris "
                     f"para revisión del agrónomo.")
    else:
        veredicto = f"Diagnóstico: **{BONITO.get(CLASES[top], CLASES[top])}** con {conf:.0%} de confianza."
    return etiquetas, veredicto


def main() -> None:
    import gradio as gr

    demo = gr.Interface(
        fn=diagnosticar,
        inputs=gr.Image(type="numpy", sources=["upload", "webcam", "clipboard"],
                        label="Foto de la hoja"),
        outputs=[gr.Label(num_top_classes=3, label="Probabilidades"),
                 gr.Markdown(label="Veredicto")],
        title="Detección temprana de Sigatoka — demo del modelo v1",
        description=(
            "Arrastra una foto de una hoja de plátano (o usa la cámara). "
            "El modelo corre localmente con el mismo paquete ONNX que se "
            "desplegará en la Jetson del dron. Modelo baseline entrenado con "
            f"datos públicos ({META['dataset']}); las fotos de campo propias "
            "vienen en la siguiente iteración."
        ),
        flagging_mode="never",
    )
    demo.launch(inbrowser=True)


if __name__ == "__main__":
    main()
